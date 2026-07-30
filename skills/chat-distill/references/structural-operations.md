# Obsidian Structural Operations

Use this reference before renaming, merging, splitting, moving sections, or proposing structural cleanup.

## Contents

1. Safety gate
2. Required preparation
3. Rename
4. Merge
5. Split
6. Move a section
7. When not to execute
8. Verification and reporting

## 1. Safety gate

`rename`, `merge`, `split`, and `move-section` are structural operations. Execute automatically only when all are true:

- relationship and intended structure are high-confidence;
- the change is low-risk and clearly improves retrieval;
- no useful method, preference, template, example, risk, or uncertainty will be lost;
- only one clearly correct destination or outcome exists;
- sources and targets are inside the configured knowledge folder;
- all affected notes have been read completely.

If any condition is false, do not execute. In the compact brief, report the proposed knowledge change under `【排除】` with the reason it was not safely performed.

## 2. Required preparation

Before an operation:

1. Confirm the vault, script, source, and target paths.
2. Read all affected notes.
3. Extract all still-useful knowledge and aliases.
4. Decide the final structure before changing files.
5. Prepare consolidated replacement content when required.
6. Confirm no external path or unsafe filename is involved.

The script performs file mechanics. The agent remains responsible for semantic preservation.

The script locks every affected path in deterministic order and atomically replaces each individual note. This prevents interleaved or half-written files. A multi-note operation is still not a database transaction: if a later replacement or deletion fails, earlier completed files remain changed. For `move-section`, the destination is written before content is removed from the source, so a partial failure favors recoverable duplication over knowledge loss. Stop immediately, re-read every affected path, and report the partial result.

## 3. Rename

Use when the existing name is vague, temporary, misleading, or materially harms retrieval, and one better name is obvious.

Do not rename only for cosmetic consistency.

Keep the old title as an alias:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" rename \
  --target "<vault-path>/AI Knowledge/旧标题.md" \
  --title "方法-领域-新标题"
```

Verify that the new file exists, the old path no longer exists as a separate note, and the alias was preserved.

## 4. Merge

Use when notes have the same future retrieval question and update direction, are true duplicates, and consolidation improves clarity.

Do not merge merely because filenames share words, notes belong to one project, or a search score is high.

Write a fully consolidated target body before running:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" merge \
  --target "<vault-path>/AI Knowledge/目标.md" \
  --sources "<vault-path>/AI Knowledge/来源一.md" "<vault-path>/AI Knowledge/来源二.md" \
  --content /path/to/consolidated.md
```

The final note must preserve useful conclusions, preferences, procedures, examples, risks, uncertainty, and old titles as aliases while removing duplicates.

## 5. Split

Use when one broad note contains independent future retrieval questions or update directions that will evolve separately.

Do not split merely because one method has several value lenses. Use headings and aliases when the units share the same scenario and maintenance direction.

Prepare every output note first:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" split \
  --target "<vault-path>/AI Knowledge/宽泛笔记.md" \
  --outputs "方法-领域-主题一=/path/to/one.md" "方法-领域-主题二=/path/to/two.md"
```

Verify that all useful source content is represented and that each output independently passes the future-leverage gate.

## 6. Move a section

Use only when a section clearly belongs to one existing target and removing it will not strip the source of its central meaning.

Prepare the final target content first:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" move-section \
  --source "<vault-path>/AI Knowledge/来源.md" \
  --target "<vault-path>/AI Knowledge/目标.md" \
  --heading "要迁移的小标题" \
  --content /path/to/target-after-move.md
```

Read both resulting notes after the operation.

## 7. When not to execute

Do not automatically run a structural operation when:

- similarity is lexical or superficial;
- multiple destinations or structures are plausible;
- meaning, context, or uncertainty may be hidden;
- the operation could remove a stable personal preference;
- a source contains project-specific and reusable material that has not been disentangled;
- the old topic would lose its core knowledge;
- a required note cannot be read;
- the final structure is not obviously better than no change.

Default to preservation and a cleanup suggestion when uncertainty is material.

## 8. Verification and reporting

After a successful structural operation:

- read every result;
- verify all expected paths;
- search by old and new terms;
- confirm aliases preserve old retrieval routes;
- confirm no valuable unit disappeared;
- confirm no unexpected duplicate remains.

Report completed structural changes under `【更新】`, describing what was renamed, merged, split, moved, or deleted and why. Do not add a separate path or operation-result block.

For deferred cleanup:

```markdown
本次 ChatDistill 简报：
【新增】无
【更新】无
【排除】方法 - 项目 - 研究证据整理｜排除：未合并两篇相近笔记｜理由：更新方向仍可能不同，尚无唯一安全结构
```

On failure, stop further structural operations. Report completed changes under `【更新】`, then append `【失败】操作简述｜原因：失败原因`; never imply an all-or-nothing success when the result was partial.
