#!/usr/bin/env python3
"""Manage topic-based Obsidian AI knowledge notes."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterator


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
WORD = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
WIKILINK = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
SENSITIVE_KEY = re.compile(
    r"^\s*(api[_ -]?key|password|passwd|secret|access[_ -]?token|private[_ -]?key)"
    r"\s*[:=]\s*(.+?)\s*$",
    re.IGNORECASE,
)
LOCK_TIMEOUT_SECONDS = 10.0
LOCK_POLL_SECONDS = 0.05
NEAR_DUPLICATE_THRESHOLD = 0.85
NEAR_DUPLICATE_MIN_TOKENS = 12
SEVERITY_ORDER = {"error": 0, "review": 1, "info": 2}
KNOWN_TYPED_PREFIXES = {"用户习惯", "方法", "模板", "资料", "索引"}
DEFAULT_FOLDER = "AI Knowledge"
CONFIG_DIR_NAME = "chat-distill"
CONFIG_FILE_NAME = "config.json"
CONFIG_PATH_ENV = "CHATDISTILL_CONFIG_PATH"
VAULT_PATH_ENV = "OBSIDIAN_VAULT_PATH"
KNOWLEDGE_FOLDER_ENV = "OBSIDIAN_KNOWLEDGE_FOLDER"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage topic-based Markdown notes in an Obsidian vault."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    configure = subparsers.add_parser(
        "configure", help="Save a private local default vault configuration."
    )
    configure.add_argument(
        "--vault", required=True, help="Path to the Obsidian vault."
    )
    configure.add_argument(
        "--folder",
        default=DEFAULT_FOLDER,
        help=f"Folder inside the vault. Defaults to {DEFAULT_FOLDER}.",
    )
    add_config_arg(configure)

    doctor = subparsers.add_parser(
        "doctor", help="Validate configuration without reading note contents."
    )
    add_common_args(doctor)

    candidates = subparsers.add_parser(
        "candidates", help="Find related existing topic notes."
    )
    add_common_args(candidates)
    candidates.add_argument("--query", required=True, help="Topic or search query.")
    candidates.add_argument(
        "--limit", type=int, default=8, help="Maximum candidates to return."
    )

    audit = subparsers.add_parser(
        "audit", help="Run a read-only health check on the knowledge folder."
    )
    add_common_args(audit)
    audit.add_argument(
        "--max-issues",
        type=int,
        default=200,
        help="Maximum issues returned in JSON. Defaults to 200.",
    )

    write = subparsers.add_parser("write", help="Create or update a topic note.")
    add_common_args(write)
    add_date_arg(write)
    write.add_argument(
        "--title",
        required=True,
        help="Three-segment classification used for the filename and derived YAML.",
    )
    write.add_argument(
        "--content",
        required=True,
        help="Path to a Markdown file containing the note body, or '-' for stdin.",
    )
    write.add_argument(
        "--target",
        help="Existing topic note to overwrite after the caller confirms a match.",
    )

    rename = subparsers.add_parser(
        "rename", help="Rename a note and keep the old title as an alias."
    )
    add_common_args(rename)
    add_date_arg(rename)
    rename.add_argument("--target", required=True, help="Existing note to rename.")
    rename.add_argument(
        "--title", required=True, help="New three-segment filename classification."
    )

    merge = subparsers.add_parser(
        "merge", help="Merge source notes into a target note."
    )
    add_common_args(merge)
    add_date_arg(merge)
    merge.add_argument("--target", required=True, help="Target note to overwrite.")
    merge.add_argument(
        "--sources",
        nargs="+",
        required=True,
        help="Source notes to delete after the target is written.",
    )
    merge.add_argument(
        "--content",
        required=True,
        help="Path to an AI-consolidated Markdown note, or '-' for stdin.",
    )
    merge.add_argument("--title", help="Optional final body heading.")

    split = subparsers.add_parser("split", help="Split one note into topic notes.")
    add_common_args(split)
    add_date_arg(split)
    split.add_argument("--target", required=True, help="Broad note to split.")
    split.add_argument(
        "--outputs",
        nargs="+",
        required=True,
        metavar="TITLE=CONTENT_PATH",
        help="Output topic title and Markdown content path.",
    )

    move = subparsers.add_parser(
        "move-section", help="Move a section or rewrite source and target notes."
    )
    add_common_args(move)
    add_date_arg(move)
    move.add_argument("--source", required=True, help="Source note.")
    move.add_argument("--target", required=True, help="Target note.")
    move.add_argument(
        "--heading",
        help="Heading to remove from the source note when using --content.",
    )
    move.add_argument(
        "--content",
        help="Path to the final target Markdown content, or '-' for stdin.",
    )
    move.add_argument(
        "--source-content",
        help="Path to the final source Markdown content.",
    )
    move.add_argument(
        "--target-content",
        help="Path to the final target Markdown content.",
    )
    move.add_argument("--source-title", help="Optional final source body heading.")
    move.add_argument("--target-title", help="Optional final target body heading.")

    return parser.parse_args()


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--vault",
        help=(
            f"Path to the Obsidian vault. Overrides {VAULT_PATH_ENV} and local config."
        ),
    )
    parser.add_argument(
        "--folder",
        help=(
            "Folder inside the vault. Overrides "
            f"{KNOWLEDGE_FOLDER_ENV} and local config; defaults to {DEFAULT_FOLDER}."
        ),
    )
    add_config_arg(parser)


def add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        help=(
            "Optional config file path. Overrides "
            f"{CONFIG_PATH_ENV} and the default user config location."
        ),
    )


def add_date_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Date in YYYY-MM-DD format. Defaults to today.",
    )


def validate_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise SystemExit(f"Invalid --date {value!r}; expected YYYY-MM-DD.")


def default_config_path() -> Path:
    configured = os.environ.get(CONFIG_PATH_ENV)
    if configured:
        return Path(configured).expanduser()
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    config_home = (
        Path(xdg_config_home).expanduser()
        if xdg_config_home
        else Path.home() / ".config"
    )
    return config_home / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def config_path_from_args(args: argparse.Namespace) -> Path:
    configured = getattr(args, "config", None)
    return Path(configured).expanduser() if configured else default_config_path()


def read_runtime_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    if not path.is_file():
        raise SystemExit(f"Config path is not a file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"Could not read valid JSON config: {path}") from error
    if not isinstance(data, dict):
        raise SystemExit(f"Config must contain a JSON object: {path}")

    result: dict[str, str] = {}
    for key in ("vault", "folder"):
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            raise SystemExit(f"Config field {key!r} must be a string: {path}")
        if value:
            result[key] = value
    return result


def resolve_runtime_options(args: argparse.Namespace) -> tuple[Path, str, Path]:
    config_path = config_path_from_args(args)
    config = read_runtime_config(config_path)
    vault_arg = (
        getattr(args, "vault", None)
        or os.environ.get(VAULT_PATH_ENV)
        or config.get("vault")
    )
    if not vault_arg and (Path.cwd() / ".obsidian").is_dir():
        vault_arg = str(Path.cwd())
    if not vault_arg:
        raise SystemExit(
            "No Obsidian vault configured. Pass --vault, set "
            f"{VAULT_PATH_ENV}, run the configure command, or run from a vault root."
        )

    folder = (
        getattr(args, "folder", None)
        or os.environ.get(KNOWLEDGE_FOLDER_ENV)
        or config.get("folder")
        or DEFAULT_FOLDER
    )
    return validate_vault(vault_arg), folder, config_path


def safe_filename_part(value: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("", value)
    cleaned = WHITESPACE.sub(" ", cleaned).strip().strip(".")
    return cleaned or "Untitled"


def clean_display_title(value: str) -> str:
    return WHITESPACE.sub(" ", value).strip() or "Untitled"


def validate_vault(vault_arg: str) -> Path:
    vault = Path(vault_arg).expanduser().resolve()
    if not vault.exists():
        raise SystemExit(f"Vault does not exist: {vault}")
    if not vault.is_dir():
        raise SystemExit(f"Vault is not a directory: {vault}")
    if not (vault / ".obsidian").is_dir():
        raise SystemExit(f"Not an Obsidian vault; missing .obsidian directory: {vault}")
    return vault


def validate_folder(vault: Path, folder_arg: str) -> Path:
    folder = Path(folder_arg)
    if folder.is_absolute() or ".." in folder.parts:
        raise SystemExit("--folder must be a relative folder inside the vault.")
    folder_path = (vault / folder).resolve()
    try:
        folder_path.relative_to(vault)
    except ValueError:
        raise SystemExit("--folder must resolve inside the vault.")
    return folder_path


def validate_target(target_arg: str, folder_path: Path) -> Path:
    target = Path(target_arg).expanduser().resolve()
    try:
        target.relative_to(folder_path)
    except ValueError:
        raise SystemExit("--target must be inside the selected folder.")
    if target.suffix.lower() != ".md":
        raise SystemExit("--target must be a Markdown file.")
    if not target.exists():
        raise SystemExit(f"--target does not exist: {target}")
    if not target.is_file():
        raise SystemExit(f"--target is not a file: {target}")
    return target


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def lock_directory(folder_path: Path) -> Path:
    path = folder_path / ".knowledge-note-locks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def lock_path_for(target: Path, folder_path: Path) -> Path:
    digest = hashlib.sha256(str(target.resolve()).encode("utf-8")).hexdigest()
    return lock_directory(folder_path) / f"{digest}.lock"


@contextmanager
def locked_paths(
    paths: list[Path],
    folder_path: Path,
    *,
    timeout: float = LOCK_TIMEOUT_SECONDS,
) -> Iterator[None]:
    handles: list[object] = []
    unique_paths = sorted({path.resolve() for path in paths}, key=str)
    deadline = time.monotonic() + timeout
    try:
        for path in unique_paths:
            lock_path = lock_path_for(path, folder_path)
            handle = lock_path.open("a+", encoding="utf-8")
            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        handle.close()
                        raise SystemExit(
                            f"Timed out waiting for note lock: {path}"
                        )
                    time.sleep(LOCK_POLL_SECONDS)
            handles.append(handle)
        yield
    finally:
        for handle in reversed(handles):
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()


def sync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def atomic_write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = (target.stat().st_mode & 0o777) if target.exists() else None
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        if existing_mode is not None:
            os.fchmod(descriptor, existing_mode)
        handle = os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")
        descriptor = -1
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        sync_directory(target.parent)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise


def durable_unlink(path: Path) -> None:
    path.unlink()
    sync_directory(path.parent)


def read_content(content_arg: str) -> str:
    if content_arg == "-":
        content = sys.stdin.read()
    else:
        content = Path(content_arg).read_text(encoding="utf-8")
    return content.rstrip() + "\n"


def split_frontmatter(content: str) -> tuple[list[str], str]:
    match = FRONTMATTER.match(content)
    if not match:
        return [], content.lstrip()
    body = content[match.end() :]
    return match.group(1).splitlines(), body.lstrip()


def parse_frontmatter(content: str) -> dict[str, str]:
    lines, _body = split_frontmatter(content)
    data: dict[str, str] = {}
    for line in lines:
        if not is_top_level_key(line):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def is_top_level_key(line: str) -> bool:
    return bool(line) and not line.startswith((" ", "-")) and ":" in line


def key_name(line: str) -> str:
    return line.split(":", 1)[0].strip()


def first_heading(content: str) -> str:
    for line in content.splitlines():
        match = HEADING.match(line)
        if match and match.group(1) == "#":
            return match.group(2).strip()
    return ""


def all_headings(content: str) -> list[str]:
    headings: list[str] = []
    for line in content.splitlines():
        match = HEADING.match(line)
        if match:
            headings.append(match.group(2).strip())
    return headings


def title_for(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    metadata = parse_frontmatter(content)
    return metadata.get("topic") or first_heading(content) or path.stem


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return [strip_quotes(value)] if value else []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [strip_quotes(part.strip()) for part in inner.split(",") if part.strip()]


def list_field(lines: list[str], key: str) -> list[str]:
    values: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if is_top_level_key(line) and key_name(line) == key:
            _name, raw_value = line.split(":", 1)
            values.extend(parse_inline_list(raw_value))
            index += 1
            while index < len(lines) and not is_top_level_key(lines[index]):
                item = lines[index].strip()
                if item.startswith("-"):
                    values.append(strip_quotes(item[1:].strip()))
                index += 1
            break
        index += 1
    return [value for value in unique(values) if value]


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = WHITESPACE.sub(" ", value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def remove_keys(lines: list[str], keys: set[str]) -> list[str]:
    cleaned: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if is_top_level_key(line) and key_name(line) in keys:
            index += 1
            while index < len(lines) and not is_top_level_key(lines[index]):
                index += 1
            continue
        cleaned.append(line)
        index += 1
    return cleaned


def format_list_key(key: str, values: list[str]) -> list[str]:
    clean_values = unique(values)
    if not clean_values:
        return [f"{key}: []"]
    return [f"{key}:"] + [f"  - {value}" for value in clean_values]


def existing_created(target: Path | None, fallback: str) -> str:
    if target is None or not target.exists():
        return fallback
    data = parse_frontmatter(target.read_text(encoding="utf-8"))
    return data.get("created") or fallback


def replace_first_heading(body: str, title: str) -> str:
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            lines[index] = f"# {title}"
            return "\n".join(lines).rstrip() + "\n"
    return f"# {title}\n\n" + body.rstrip() + "\n"


def ensure_frontmatter(
    content: str,
    *,
    title: str,
    note_date: str,
    target: Path | None,
    aliases_to_add: list[str] | None = None,
    update_heading: bool = False,
    heading_title: str | None = None,
) -> str:
    lines, body = split_frontmatter(content)
    created = existing_created(target, note_date)
    aliases = list_field(lines, "aliases")
    if aliases_to_add:
        aliases = unique(aliases + aliases_to_add)
    existing_tags = list_field(lines, "tags")
    expected_type, expected_domain, expected_topic = expected_classification(title)
    topic = expected_topic or title
    managed_keys = {"created", "updated", "source", "topic", "aliases", "tags"}
    if expected_domain:
        managed_keys.add("domain")
    if expected_type:
        managed_keys.add("type")
    lines = remove_keys(lines, managed_keys)

    frontmatter = [
        f"created: {created}",
        f"updated: {note_date}",
        "source: chat-distill",
        f"topic: {topic}",
    ]
    frontmatter.extend(format_list_key("aliases", aliases))
    frontmatter.extend(
        format_list_key("tags", existing_tags or ["chat-distill", "ai-knowledge"])
    )
    if expected_domain:
        frontmatter.append(f"domain: {expected_domain}")
    if expected_type:
        frontmatter.append(f"type: {expected_type}")
    if lines:
        frontmatter.extend(lines)
    if update_heading:
        body = replace_first_heading(body, heading_title or topic)
    return "---\n" + "\n".join(frontmatter).rstrip() + "\n---\n\n" + body.rstrip() + "\n"


def tokenize(value: str) -> set[str]:
    tokens: set[str] = set()
    for match in WORD.findall(value.lower()):
        tokens.add(match)
        if re.fullmatch(r"[\u4e00-\u9fff]+", match):
            for size in (2, 3):
                if len(match) >= size:
                    tokens.update(match[i : i + size] for i in range(len(match) - size + 1))
    return tokens


def field_score(query: str, query_tokens: set[str], value: str, exact: int, term: int) -> int:
    if not value:
        return 0
    lowered = value.lower()
    score = exact if query.lower() in lowered else 0
    tokens = tokenize(value)
    score += len(query_tokens & tokens) * term
    return score


def candidate_for(path: Path, query: str, query_tokens: set[str]) -> dict[str, object] | None:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None

    metadata = parse_frontmatter(content)
    lines, _body = split_frontmatter(content)
    heading = first_heading(content)
    title = heading or path.stem
    topic = metadata.get("topic") or title
    aliases = " ".join(list_field(lines, "aliases"))
    headings = " ".join(all_headings(content))

    fields = {
        "topic": topic,
        "title": title,
        "filename": path.stem,
        "aliases": aliases,
        "headings": headings,
        "content": content,
    }
    weights = {
        "topic": (100, 14),
        "title": (90, 12),
        "filename": (70, 9),
        "aliases": (85, 12),
        "headings": (60, 8),
        "content": (20, 1),
    }

    score = 0
    matched_fields: list[str] = []
    for field, value in fields.items():
        field_match = field_score(query, query_tokens, value, *weights[field])
        if field_match:
            matched_fields.append(field)
            score += field_match

    if score <= 0:
        return None

    return {
        "path": str(path.resolve()),
        "title": title,
        "topic": topic,
        "score": score,
        "updated": metadata.get("updated") or metadata.get("created") or "",
        "matched_fields": matched_fields,
    }


def audit_path(path: Path, vault: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return path.name


def add_audit_issue(
    issues: list[dict[str, object]],
    *,
    severity: str,
    code: str,
    path: str,
    message: str,
    suggestion: str,
    related: list[str] | None = None,
) -> None:
    issue: dict[str, object] = {
        "severity": severity,
        "code": code,
        "path": path,
        "message": message,
        "suggestion": suggestion,
    }
    if related:
        issue["related"] = related
    issues.append(issue)


def parse_note_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalized_body(content: str) -> str:
    _lines, body = split_frontmatter(content)
    body = "\n".join(
        line for line in body.splitlines() if not HEADING.match(line)
    )
    return re.sub(r"[\W_]+", "", body.lower(), flags=re.UNICODE)


def empty_sections(content: str) -> list[str]:
    lines = content.splitlines()
    empty: list[str] = []
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if not match or len(match.group(1)) == 1:
            continue
        level = len(match.group(1))
        found_content = False
        for following in lines[index + 1 :]:
            next_heading = HEADING.match(following)
            if next_heading and len(next_heading.group(1)) <= level:
                break
            if following.strip():
                found_content = True
                break
        if not found_content:
            empty.append(match.group(2).strip())
    return empty


def looks_like_placeholder(value: str) -> bool:
    normalized = value.strip().strip("'\"").lower()
    return (
        not normalized
        or normalized in {"null", "none", "redacted", "placeholder", "changeme"}
        or normalized.startswith(("<", "${", "your-", "example"))
    )


def expected_classification(
    stem: str,
) -> tuple[str | None, str | None, str | None]:
    parts = stem.split("-")
    if not parts:
        return None, None, None
    prefix = parts[0]
    expected_type = prefix if prefix in KNOWN_TYPED_PREFIXES else None
    expected_domain: str | None = None
    expected_topic: str | None = None
    if prefix in {"用户习惯", "方法"} and len(parts) >= 2:
        expected_domain = parts[1]
        if len(parts) >= 3:
            expected_topic = "-".join(parts[2:])
    elif prefix in {"模板", "资料"} and len(parts) >= 2:
        expected_topic = "-".join(parts[1:])
    elif prefix == "索引" and len(parts) >= 2:
        expected_domain = "-".join(parts[1:])
        expected_topic = expected_domain
    elif len(parts) >= 3:
        expected_domain = parts[0]
        expected_topic = "-".join(parts[1:])
    return expected_type, expected_domain, expected_topic


def wikilink_status(
    target: str,
    *,
    vault_paths: set[str],
    stems: dict[str, list[str]],
) -> tuple[bool, bool]:
    cleaned = target.strip().replace("\\", "/")
    if cleaned.lower().endswith(".md"):
        cleaned = cleaned[:-3]
    normalized = cleaned.lstrip("./").lower()
    if "/" in normalized:
        return normalized in vault_paths, False
    matches = stems.get(normalized, [])
    return bool(matches), len(matches) > 1


def run_audit(args: argparse.Namespace) -> int:
    vault, folder, _config_path = resolve_runtime_options(args)
    folder_path = validate_folder(vault, folder)
    if args.max_issues < 1:
        raise SystemExit("--max-issues must be greater than 0.")
    if not folder_path.exists():
        print_json(
            {
                "summary": {
                    "notes_scanned": 0,
                    "issues": 0,
                    "errors": 0,
                    "review": 0,
                    "info": 0,
                },
                "issues": [],
                "truncated": False,
            }
        )
        return 0

    issues: list[dict[str, object]] = []
    note_records: list[dict[str, object]] = []
    aliases_by_value: dict[str, list[str]] = {}

    all_vault_notes = [
        path
        for path in vault.rglob("*.md")
        if path.is_file()
        and not path.is_symlink()
        and path_is_within(path, vault)
    ]
    vault_paths = {
        path.relative_to(vault).with_suffix("").as_posix().lower()
        for path in all_vault_notes
    }
    stems: dict[str, list[str]] = {}
    for path in all_vault_notes:
        stems.setdefault(path.stem.lower(), []).append(audit_path(path, vault))

    note_paths = sorted(folder_path.rglob("*.md"), key=lambda path: str(path))
    for path in note_paths:
        relative = audit_path(path, vault)
        if path.is_symlink() or not path_is_within(path, folder_path):
            add_audit_issue(
                issues,
                severity="error",
                code="symlink_note",
                path=relative,
                message="A knowledge note is a symlink or resolves outside the configured folder.",
                suggestion="Replace it with a real note contained inside the configured folder.",
            )
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            add_audit_issue(
                issues,
                severity="error",
                code="unreadable_note",
                path=relative,
                message="The note could not be read as UTF-8 text.",
                suggestion="Repair or restore the file before any update.",
            )
            continue

        frontmatter_match = FRONTMATTER.match(content)
        if content.startswith("---\n") and frontmatter_match is None:
            add_audit_issue(
                issues,
                severity="error",
                code="malformed_frontmatter",
                path=relative,
                message="The YAML frontmatter opening or closing boundary is incomplete.",
                suggestion="Repair the frontmatter boundaries before updating the note.",
            )
        elif frontmatter_match is None:
            add_audit_issue(
                issues,
                severity="review",
                code="missing_frontmatter",
                path=relative,
                message="The note has no managed YAML frontmatter.",
                suggestion="Add frontmatter only if this note belongs to the managed knowledge system.",
            )

        metadata = parse_frontmatter(content)
        frontmatter_lines, body = split_frontmatter(content)
        for field in ("created", "updated", "topic"):
            if not metadata.get(field):
                add_audit_issue(
                    issues,
                    severity="review",
                    code=f"missing_{field}",
                    path=relative,
                    message=f"The managed field '{field}' is missing.",
                    suggestion="Add the field during the next intentional note update.",
                )

        created = parse_note_date(metadata["created"]) if metadata.get("created") else None
        updated = parse_note_date(metadata["updated"]) if metadata.get("updated") else None
        for field, parsed in (("created", created), ("updated", updated)):
            if metadata.get(field) and parsed is None:
                add_audit_issue(
                    issues,
                    severity="review",
                    code="invalid_date",
                    path=relative,
                    message=f"The '{field}' value is not a YYYY-MM-DD date.",
                    suggestion="Correct the date during the next intentional update.",
                )
        if created and updated and updated < created:
            add_audit_issue(
                issues,
                severity="review",
                code="date_order",
                path=relative,
                message="The updated date is earlier than the created date.",
                suggestion="Verify both dates and correct the inaccurate value.",
            )

        parts = path.stem.split("-")
        if (parts[0] == "索引" and len(parts) < 2) or (
            parts[0] != "索引" and len(parts) < 3
        ):
            add_audit_issue(
                issues,
                severity="review",
                code="classification_shape",
                path=relative,
                message="The filename does not expose the expected semantic segments.",
                suggestion="Review the naming classification; do not rename for cosmetics alone.",
            )
        expected_type, expected_domain, expected_topic = expected_classification(
            path.stem
        )
        if expected_type and metadata.get("type") != expected_type:
            add_audit_issue(
                issues,
                severity="review",
                code="classification_type",
                path=relative,
                message="The filename classification and YAML type do not align.",
                suggestion="Confirm the note meaning before changing either field or filename.",
            )
        if expected_domain and metadata.get("domain") != expected_domain:
            add_audit_issue(
                issues,
                severity="review",
                code="classification_domain",
                path=relative,
                message="The filename domain and YAML domain do not align.",
                suggestion="Confirm the semantic domain before changing metadata.",
            )
        if expected_topic and metadata.get("topic") != expected_topic:
            add_audit_issue(
                issues,
                severity="review",
                code="classification_topic",
                path=relative,
                message="The filename classification and YAML topic do not align.",
                suggestion="Confirm the note meaning before changing either field or filename.",
            )

        aliases = list_field(frontmatter_lines, "aliases")
        for alias in aliases:
            aliases_by_value.setdefault(alias.casefold(), []).append(relative)

        for heading in empty_sections(content):
            add_audit_issue(
                issues,
                severity="review",
                code="empty_section",
                path=relative,
                message=f"The section '{heading}' has no content.",
                suggestion="Fill it with useful knowledge or remove the empty heading.",
            )

        for link_target in WIKILINK.findall(content):
            exists, ambiguous = wikilink_status(
                link_target, vault_paths=vault_paths, stems=stems
            )
            if not exists:
                add_audit_issue(
                    issues,
                    severity="review",
                    code="dead_wikilink",
                    path=relative,
                    message=f"The wikilink target '{link_target}' was not found.",
                    suggestion="Correct the link or remove it if it is no longer useful.",
                )
            elif ambiguous:
                add_audit_issue(
                    issues,
                    severity="info",
                    code="ambiguous_wikilink",
                    path=relative,
                    message=f"The wikilink target '{link_target}' matches multiple filenames.",
                    suggestion="Use a vault-relative path if Obsidian resolves the link ambiguously.",
                )

        for line in content.splitlines():
            match = SENSITIVE_KEY.match(line)
            if match and not looks_like_placeholder(match.group(2)):
                add_audit_issue(
                    issues,
                    severity="error",
                    code="sensitive_key",
                    path=relative,
                    message="A field that commonly contains a credential has a non-placeholder value.",
                    suggestion="Review and remove the secret without exposing its value in reports.",
                )
                break
            if "-----BEGIN PRIVATE KEY-----" in line:
                add_audit_issue(
                    issues,
                    severity="error",
                    code="private_key_material",
                    path=relative,
                    message="Possible private-key material is present.",
                    suggestion="Remove it from the vault and rotate the credential if necessary.",
                )
                break

        if path.stem.startswith("用户习惯-") and metadata.get("status") in {
            "uncertain",
            "outdated",
        }:
            add_audit_issue(
                issues,
                severity="review",
                code="habit_status_review",
                path=relative,
                message=f"The user habit is marked '{metadata['status']}'.",
                suggestion="Confirm whether it should remain active, be revised, or be archived.",
            )

        if len(content.splitlines()) > 300:
            add_audit_issue(
                issues,
                severity="info",
                code="long_note",
                path=relative,
                message="The note exceeds 300 lines and may contain divergent retrieval questions.",
                suggestion="Review its structure; do not split unless update directions truly diverge.",
            )

        normalized = normalized_body(content)
        note_records.append(
            {
                "path": relative,
                "normalized": normalized,
                "tokens": tokenize(body),
            }
        )

    for alias, paths in sorted(aliases_by_value.items()):
        unique_paths = unique(paths)
        if len(unique_paths) > 1:
            add_audit_issue(
                issues,
                severity="review",
                code="alias_collision",
                path=unique_paths[0],
                related=unique_paths[1:],
                message=f"The alias '{alias}' is shared by multiple notes.",
                suggestion="Keep the alias only where it resolves to one clear retrieval target.",
            )

    exact_groups: dict[str, list[str]] = {}
    for record in note_records:
        normalized = str(record["normalized"])
        if len(normalized) >= 60:
            exact_groups.setdefault(normalized, []).append(str(record["path"]))
    exact_pairs: set[tuple[str, str]] = set()
    for paths in exact_groups.values():
        if len(paths) > 1:
            first = paths[0]
            for related in paths[1:]:
                exact_pairs.add(tuple(sorted((first, related))))
            add_audit_issue(
                issues,
                severity="review",
                code="exact_duplicate",
                path=first,
                related=paths[1:],
                message="Multiple notes have the same normalized body.",
                suggestion="Read every note fully before deciding whether to merge.",
            )

    if len(note_records) <= 500:
        for index, left in enumerate(note_records):
            left_tokens = set(left["tokens"])
            if len(left_tokens) < NEAR_DUPLICATE_MIN_TOKENS:
                continue
            for right in note_records[index + 1 :]:
                pair = tuple(sorted((str(left["path"]), str(right["path"]))))
                if pair in exact_pairs:
                    continue
                right_tokens = set(right["tokens"])
                if len(right_tokens) < NEAR_DUPLICATE_MIN_TOKENS:
                    continue
                union = left_tokens | right_tokens
                similarity = len(left_tokens & right_tokens) / len(union) if union else 0
                if similarity >= NEAR_DUPLICATE_THRESHOLD:
                    add_audit_issue(
                        issues,
                        severity="review",
                        code="near_duplicate",
                        path=str(left["path"]),
                        related=[str(right["path"])],
                        message=f"The notes have high lexical overlap ({similarity:.0%}).",
                        suggestion="Treat this only as a candidate hint; read both before any merge.",
                    )
    else:
        add_audit_issue(
            issues,
            severity="info",
            code="near_duplicate_skipped",
            path=audit_path(folder_path, vault),
            message="Near-duplicate comparison was skipped because the folder exceeds 500 notes.",
            suggestion="Use targeted candidate searches or an optional retrieval index.",
        )

    now = time.time()
    for temporary in folder_path.rglob(".*.tmp"):
        try:
            age = now - temporary.stat().st_mtime
        except OSError:
            continue
        if age >= 60:
            add_audit_issue(
                issues,
                severity="review",
                code="temporary_write_residue",
                path=audit_path(temporary, vault),
                message="A stale temporary write file remains from an interrupted operation.",
                suggestion="Verify the corresponding note, then remove the temporary file.",
            )

    issues.sort(
        key=lambda issue: (
            SEVERITY_ORDER[str(issue["severity"])],
            str(issue["path"]),
            str(issue["code"]),
        )
    )
    counts = {
        severity: sum(1 for issue in issues if issue["severity"] == severity)
        for severity in ("error", "review", "info")
    }
    returned = issues[: args.max_issues]
    print_json(
        {
            "summary": {
                "notes_scanned": len(note_records),
                "issues": len(issues),
                "errors": counts["error"],
                "review": counts["review"],
                "info": counts["info"],
            },
            "issues": returned,
            "truncated": len(returned) < len(issues),
        }
    )
    return 0


def parse_output_pair(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise SystemExit("--outputs entries must use TITLE=CONTENT_PATH.")
    title, content_path = value.split("=", 1)
    title = safe_filename_part(title)
    if not title or not content_path:
        raise SystemExit("--outputs entries must include both title and content path.")
    return title, content_path


def remove_heading_section(content: str, heading: str) -> str:
    lines = content.splitlines()
    start: int | None = None
    level: int | None = None
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match and match.group(2).strip() == heading:
            start = index
            level = len(match.group(1))
            break
    if start is None or level is None:
        raise SystemExit(f"Heading not found in source note: {heading}")

    end = len(lines)
    for index in range(start + 1, len(lines)):
        match = HEADING.match(lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[:start] + lines[end:]).strip() + "\n"


def run_configure(args: argparse.Namespace) -> int:
    vault = validate_vault(args.vault)
    folder_path = validate_folder(vault, args.folder)
    config_path = config_path_from_args(args).resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    content = json.dumps(
        {"vault": str(vault), "folder": args.folder},
        ensure_ascii=False,
        indent=2,
    )
    atomic_write_text(config_path, content + "\n")
    config_path.chmod(0o600)
    print_json(
        {
            "configured": True,
            "config": str(config_path),
            "vault": str(vault),
            "folder": folder_path.relative_to(vault).as_posix(),
        }
    )
    return 0


def run_doctor(args: argparse.Namespace) -> int:
    vault, folder, config_path = resolve_runtime_options(args)
    folder_path = validate_folder(vault, folder)
    print_json(
        {
            "ok": True,
            "vault": str(vault),
            "folder": folder_path.relative_to(vault).as_posix(),
            "folder_exists": folder_path.is_dir(),
            "config": str(config_path) if config_path.is_file() else None,
            "notes_read": 0,
        }
    )
    return 0


def command_context(args: argparse.Namespace) -> tuple[str, Path]:
    note_date = validate_date(getattr(args, "date", date.today().isoformat()))
    vault, folder, _config_path = resolve_runtime_options(args)
    folder_path = validate_folder(vault, folder)
    return note_date, folder_path


def print_json(data: dict[str, object]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run_candidates(args: argparse.Namespace) -> int:
    vault, folder, _config_path = resolve_runtime_options(args)
    folder_path = validate_folder(vault, folder)
    if args.limit < 1:
        raise SystemExit("--limit must be greater than 0.")
    if not folder_path.exists():
        print("[]")
        return 0

    query_tokens = tokenize(args.query)
    candidates = [
        candidate
        for path in folder_path.rglob("*.md")
        if path.is_file()
        and not path.is_symlink()
        and path_is_within(path, folder_path)
        if (candidate := candidate_for(path, args.query, query_tokens)) is not None
    ]
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    print(json.dumps(candidates[: args.limit], ensure_ascii=False, indent=2))
    return 0


def run_write(args: argparse.Namespace) -> int:
    note_date, folder_path = command_context(args)
    folder_path.mkdir(parents=True, exist_ok=True)

    title = safe_filename_part(args.title)
    if args.target:
        target = validate_target(args.target, folder_path)
        if title != target.stem:
            raise SystemExit(
                "--title must match the existing target filename; use rename to change classification."
            )
    else:
        target = folder_path / f"{title}.md"

    with locked_paths([target], folder_path):
        confirmed_target: Path | None = None
        if args.target:
            confirmed_target = validate_target(args.target, folder_path)
            target = confirmed_target
        elif target.exists():
            raise SystemExit(
                f"Refusing to overwrite existing note without --target: {target}"
            )

        content = ensure_frontmatter(
            read_content(args.content),
            title=title,
            note_date=note_date,
            target=confirmed_target,
        )
        atomic_write_text(target, content)
    print(target.resolve())
    return 0


def run_rename(args: argparse.Namespace) -> int:
    note_date, folder_path = command_context(args)
    target = validate_target(args.target, folder_path)
    new_title = safe_filename_part(args.title)
    destination = target.with_name(f"{new_title}.md")
    with locked_paths([target, destination], folder_path):
        target = validate_target(args.target, folder_path)
        if destination.exists() and destination != target:
            raise SystemExit(f"Destination already exists: {destination}")

        original_content = target.read_text(encoding="utf-8")
        old_title = title_for(target)
        aliases = [old_title]
        if target.stem != old_title:
            aliases.append(target.stem)
        _new_type, _new_domain, new_topic = expected_classification(new_title)
        new_topic = new_topic or new_title
        content = ensure_frontmatter(
            original_content,
            title=new_title,
            note_date=note_date,
            target=target,
            aliases_to_add=[
                alias for alias in aliases if alias not in {new_title, new_topic}
            ],
            update_heading=True,
        )
        atomic_write_text(destination, content)
        if destination != target:
            durable_unlink(target)
    print_json(
        {
            "renamed": str(destination.resolve()),
            "from": str(target.resolve()),
            "aliases_added": [
                alias
                for alias in unique(aliases)
                if alias not in {new_title, new_topic}
            ],
        }
    )
    return 0


def run_merge(args: argparse.Namespace) -> int:
    note_date, folder_path = command_context(args)
    target = validate_target(args.target, folder_path)
    sources = [validate_target(source, folder_path) for source in args.sources]
    deleted: list[str] = []
    with locked_paths([target] + sources, folder_path):
        target = validate_target(args.target, folder_path)
        sources = [validate_target(source, folder_path) for source in args.sources]
        aliases: list[str] = []
        for path in [target] + sources:
            content = path.read_text(encoding="utf-8")
            lines, _body = split_frontmatter(content)
            aliases.extend(list_field(lines, "aliases"))
            aliases.extend([title_for(path), path.stem])

        merged_content = read_content(args.content)
        heading_title = clean_display_title(
            args.title or first_heading(merged_content) or title_for(target)
        )
        filename_title = target.stem
        _type, _domain, topic = expected_classification(filename_title)
        content = ensure_frontmatter(
            merged_content,
            title=filename_title,
            note_date=note_date,
            target=target,
            aliases_to_add=[
                alias
                for alias in aliases
                if alias not in {heading_title, topic, filename_title}
            ],
            update_heading=True,
            heading_title=heading_title,
        )
        atomic_write_text(target, content)
        for source in sources:
            if source != target and source.exists():
                durable_unlink(source)
                deleted.append(str(source.resolve()))
    print_json({"merged": str(target.resolve()), "deleted_sources": deleted})
    return 0


def run_split(args: argparse.Namespace) -> int:
    note_date, folder_path = command_context(args)
    target = validate_target(args.target, folder_path)
    outputs = [parse_output_pair(output) for output in args.outputs]
    destination_paths = [folder_path / f"{title}.md" for title, _path in outputs]
    if len({path.resolve() for path in destination_paths}) != len(destination_paths):
        raise SystemExit("Duplicate output titles are not allowed.")
    written: list[str] = []
    with locked_paths([target] + destination_paths, folder_path):
        target = validate_target(args.target, folder_path)
        for destination in destination_paths:
            if destination.exists() and destination != target:
                raise SystemExit(f"Output already exists: {destination}")

        prepared: list[tuple[Path, str]] = []
        for title, content_path in outputs:
            destination = folder_path / f"{title}.md"
            source_content = read_content(content_path)
            content = ensure_frontmatter(
                source_content,
                title=title,
                note_date=note_date,
                target=target if destination == target else None,
                update_heading=True,
                heading_title=first_heading(source_content) or None,
            )
            prepared.append((destination, content))
        for destination, content in prepared:
            atomic_write_text(destination, content)
            written.append(str(destination.resolve()))
        if target not in destination_paths and target.exists():
            durable_unlink(target)
    print_json({"split_from": str(target.resolve()), "written": written})
    return 0


def run_move_section(args: argparse.Namespace) -> int:
    note_date, folder_path = command_context(args)
    source = validate_target(args.source, folder_path)
    target = validate_target(args.target, folder_path)
    with locked_paths([source, target], folder_path):
        source = validate_target(args.source, folder_path)
        target = validate_target(args.target, folder_path)

        if args.source_content or args.target_content:
            if not (args.source_content and args.target_content):
                raise SystemExit(
                    "--source-content and --target-content must be used together."
                )
            source_content = read_content(args.source_content)
            target_content = read_content(args.target_content)
            source_title = clean_display_title(
                args.source_title or first_heading(source_content) or title_for(source)
            )
            target_title = clean_display_title(
                args.target_title or first_heading(target_content) or title_for(target)
            )
        else:
            if not (args.heading and args.content):
                raise SystemExit(
                    "Use either --source-content with --target-content, or --heading with --content."
                )
            source_content = remove_heading_section(
                source.read_text(encoding="utf-8"), args.heading
            )
            target_content = read_content(args.content)
            source_title = clean_display_title(
                args.source_title or first_heading(source_content) or title_for(source)
            )
            target_title = clean_display_title(
                args.target_title or first_heading(target_content) or title_for(target)
            )

        prepared_source = ensure_frontmatter(
            source_content,
            title=source.stem,
            note_date=note_date,
            target=source,
            update_heading=True,
            heading_title=source_title,
        )
        prepared_target = ensure_frontmatter(
            target_content,
            title=target.stem,
            note_date=note_date,
            target=target,
            update_heading=True,
            heading_title=target_title,
        )

        # Write the destination first. If removing content from the source later fails,
        # the safe partial state is duplication rather than knowledge loss.
        atomic_write_text(
            target,
            prepared_target,
        )
        atomic_write_text(source, prepared_source)
    print_json({"source": str(source.resolve()), "target": str(target.resolve())})
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "configure":
        return run_configure(args)
    if args.command == "doctor":
        return run_doctor(args)
    if args.command == "candidates":
        return run_candidates(args)
    if args.command == "audit":
        return run_audit(args)
    if args.command == "write":
        return run_write(args)
    if args.command == "rename":
        return run_rename(args)
    if args.command == "merge":
        return run_merge(args)
    if args.command == "split":
        return run_split(args)
    if args.command == "move-section":
        return run_move_section(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
