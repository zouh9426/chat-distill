#!/usr/bin/env python3
"""Fail when release files contain likely private paths or high-confidence secrets."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
TEXT_SUFFIXES = {
    "",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

CHECKS = {
    "macOS personal home path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "Linux personal home path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "Windows personal home path": re.compile(
        r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\", re.IGNORECASE
    ),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
}


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path == Path(__file__).resolve() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    findings: list[tuple[Path, int, str]] = []
    for path in iter_text_files():
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            for label, pattern in CHECKS.items():
                if pattern.search(line):
                    findings.append((path.relative_to(ROOT), line_number, label))

    if findings:
        print("Release hygiene check failed; matched values are intentionally redacted.")
        for path, line_number, label in findings:
            print(f"{path}:{line_number}: {label}")
        return 1

    print(f"Release hygiene check passed ({len(iter_text_files())} text files scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
