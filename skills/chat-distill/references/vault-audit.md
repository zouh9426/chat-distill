# Obsidian Vault Audit

Read this reference before running or interpreting a Vault Audit.

## Purpose

Use Audit as a read-only health check for the configured knowledge folder. It finds mechanical risks and review candidates; it does not decide whether knowledge is valuable, whether two notes mean the same thing, or whether a structural change is safe.

Run Audit when the user explicitly asks to check, audit, clean up, inspect, or assess the health of the Obsidian knowledge base. Do not run it silently during ordinary saves.

## Command

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" audit
```

The command returns JSON and does not modify notes. `--max-issues` limits returned details while summary counts still cover the complete scan.

## What it checks

| Severity | Meaning | Examples |
| --- | --- | --- |
| `error` | A concrete integrity or privacy risk | malformed or unreadable note, credential-like field, private-key material |
| `review` | Human or semantic review is required | exact/near duplicate, dead link, empty section, naming mismatch, uncertain habit |
| `info` | A maintenance signal, not a defect | ambiguous wikilink, long note, large-vault comparison limit |

The lightweight checks cover:

- readable UTF-8 notes and complete frontmatter boundaries;
- managed fields and valid date order;
- filename/YAML classification alignment across `type`, `domain`, and `topic`;
- empty sections and dead or ambiguous wikilinks;
- alias collisions;
- exact duplicates and high lexical-overlap candidates;
- uncertain or outdated user habits;
- obvious credential-bearing fields without exposing their values;
- stale temporary files from interrupted writes.

Near-duplicate comparison is lexical, not semantic proof. It runs only for folders of at most 500 notes. Larger folders require targeted candidate search or a future optional retrieval index.

## Interpretation rules

1. Treat every Audit item as evidence, not permission to mutate.
2. Read every affected note fully before proposing a fix.
3. Never merge because Audit reports `exact_duplicate` or `near_duplicate` alone. Confirm the future retrieval question and update direction.
4. Never delete a stale habit or empty note without confirming that it has no intentional purpose.
5. Never reveal a suspected secret value. Report only the relative note path and issue code.
6. Read [structural-operations.md](structural-operations.md) before proposing or executing rename, merge, split, or section movement.
7. If the user asked only for an audit, do not auto-fix. Ask for a separate fix request after presenting the findings.

## Reporting

Lead with the summary:

`Vault Audit：扫描 N 篇｜错误 E｜需复核 R｜提示 I`

Then report the highest-value findings in plain Chinese, grouped by severity. Use relative note paths. Explain false-positive risk for duplicate and classification findings.

For an audit-only invocation, the required Obsidian brief still shows:

```markdown
本次 ChatDistill 简报：
【新增】无
【更新】无
【排除】无
```

Append the Audit summary and findings after the brief. Report an Audit execution failure under `【失败】`; do not present an incomplete scan as a clean result.
