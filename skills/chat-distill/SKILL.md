---
name: chat-distill
description: Distill high-value knowledge and stable personal preferences from AI conversations into a user's own Obsidian vault, then safely create, consolidate, organize, or audit the resulting notes. Use when the user explicitly asks to save, record, archive, update, sync, merge, organize, audit, health-check, set up, configure, or troubleshoot ChatDistill for Obsidian. Trigger on requests such as "总结到 Obsidian", "记录到 Obsidian", "保存到知识库", "更新知识库", "整理 Obsidian", "检查知识库", "配置 ChatDistill", "Vault Audit", or "use $chat-distill".
license: MIT
---

# ChatDistill

## Purpose

Turn the current material into compact Chinese knowledge that has **future leverage for this user**. Future leverage means that finding the knowledge later can materially improve output quality, make a workflow clearer or faster, help recover from failure, reduce risk, improve human-AI collaboration or decisions, preserve a stable personal preference, or provide a reusable template/tool.

This skill is write-and-audit-oriented. Use it only after an explicit request to save, organize, or health-check knowledge. Do not invoke it merely to retrieve notes for an unrelated task.

**Core rule:** value is not the same as frequency or cross-project breadth. A rare recovery method can be worth saving; a named framework used only in one course can still be noise.

## Defaults

- Vault: resolve from `--vault`, `OBSIDIAN_VAULT_PATH`, private local config, or the current vault root; never guess or embed a creator path
- Folder: `AI Knowledge`, overridable through `--folder`, `OBSIDIAN_KNOWLEDGE_FOLDER`, or private local config
- Script: use `scripts/knowledge_note.py` relative to this `SKILL.md`; never assume a Codex, Claude, or home-directory installation path
- Private config: `~/.config/chat-distill/config.json` by default, overridable through `CHATDISTILL_CONFIG_PATH`
- Language: Chinese unless the user requests otherwise
- Style: compact actionable knowledge, not a transcript, diary, or broad recap
- Matching: update only when the future retrieval question and update direction match
- Organization: create and same-topic consolidate automatically; structural changes only when clearly safe
- User-habit classification: `用户习惯-领域-习惯对象.md`
- Write safety: per-note file locks, same-directory atomic replacement, private `0600` new files, and preserved permissions on updates
- Audit: read-only by default; report findings before any fix
- Runtime: macOS or Linux; deterministic locking uses `fcntl`

## Future-Leverage Gate

### Save when all essentials are present

A retained knowledge unit must have:

1. **Recognizable future trigger** — the user or agent can tell when it applies.
2. **Actionable guidance** — a method, criterion, preference, template, recovery path, or boundary changes what to do.
3. **Meaningful benefit** — at least one value lens below is material.

Use these value lenses during discovery:

| Value lens | Question |
| --- | --- |
| Quality improvement | Will this noticeably improve a future deliverable? |
| Process optimization | Will this make work clearer, faster, or less repetitive? |
| Failure recovery | Will this help diagnose, recover, verify, or stop safely? |
| Risk protection | Will this prevent loss, unsafe changes, privacy exposure, or uncontrolled action? |
| Collaboration gain | Will this improve roles, approval, feedback, acceptance, or closure? |
| Decision gain | Will this improve trade-offs, evidence use, or choice quality? |
| Personal preference | Is this a stable preference that should shape future work? |
| Reusable asset | Is this a useful template, checklist, prompt, or tool procedure? |

These are `价值类型`, not Obsidian storage categories.

### Tie-breakers, not hard gates

Use reuse frequency, cross-domain scope, cost of rediscovery, and ease of regeneration only after the essentials above. Do not reject a high-impact failure shield merely because it may be used rarely. Prefer exclusion when an item is low-impact, easy to regenerate, and unlikely to be retrieved.

### Exclude by default

- Course-specific theories, acronyms, or presentation structures with almost no use outside that course.
- One-off project versions, deliverables, timelines, participants, file paths, next actions, or conversation chronology.
- Common terms, textbook explanations, broad summaries, or facts that are easy to regenerate.
- Draft wording experiments and tool noise that teach no durable lesson.
- Duplicates already covered by an existing note.
- Speculative claims without a useful uncertainty-management rule.
- Private details, credentials, or raw sensitive content that are unnecessary for future use.

Generalize a project example only when the generalized rule independently passes the gate. Never manufacture a generic lesson just to justify a write.

### Uncertainty rule

- Ambiguous and ordinary value: discard.
- Ambiguous but potentially high-impact value: do not write; report it under `【排除】` and state that user confirmation is required.
- User explicitly asks to preserve a specific item: follow that request, but label uncertainty or time limits when relevant.

### User-habit evidence and privacy rule

Treat a user habit as an actionable preference about how the user works with outputs, collaboration, tools, organization, review, approval, or execution. Store it under the dedicated `用户习惯` classification when it should change future agent behavior.

Retain a habit only when at least one evidence path is present:

- the user explicitly states that the preference is general, persistent, or should be remembered;
- the same preference appears through repeated choices, corrections, or approvals in the complete source;
- a current signal corroborates an existing habit note with the same scope and direction.

An explicit persistent instruction may be recorded from one statement. An inferred habit requires repeated evidence. A one-off format request, temporary project constraint, isolated reaction, or absence of objection is not a habit.

Record only the minimum behavior-level rule needed for future action. Do not store raw quotes, speculative personality claims, inferred sensitive traits, private routines, identities, credentials, health, political, sexual, financial, or other sensitive attributes merely because they may explain a behavior. An explicit request to save or organize knowledge authorizes evaluating non-sensitive habits in the provided material; sensitive or materially private habits require separate user confirmation before writing.

When evidence conflicts, prefer the most recent explicit user statement, preserve genuinely contextual exceptions, and mark unresolved conflicts as `pending` rather than guessing.

## Progressive Disclosure

Read [references/naming.md](references/naming.md) before choosing or changing any note filename, YAML classification, title, alias, or date treatment.

Read [references/structural-operations.md](references/structural-operations.md) only before `rename`, `merge`, `split`, or `move-section`, or when proposing such cleanup. Ordinary create/update work does not require it.

Read [references/vault-audit.md](references/vault-audit.md) before running an Audit or interpreting its findings.

Read [references/setup.md](references/setup.md) when installing, configuring, diagnosing, or connecting ChatDistill through Codex, Claude Code, or the optional Claudian integration.

Run the script with `--help` for complete command syntax. The script finds candidates and performs file operations; it does **not** decide semantic value.

## Required Workflow

### 1. Preflight

Resolve `<skill-dir>` as the directory containing this `SKILL.md`. Do not require the user to edit this file with an installation path.

```bash
test -f "<skill-dir>/scripts/knowledge_note.py"
python3 "<skill-dir>/scripts/knowledge_note.py" doctor
```

`doctor` validates the configured Vault and knowledge folder without reading note contents. If no Vault is configured, ask the user for its absolute path and obtain permission before validating it. Configure it with:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" configure \
  --vault "<vault-path>" \
  --folder "AI Knowledge"
```

The user may instead set `OBSIDIAN_VAULT_PATH` and optionally `OBSIDIAN_KNOWLEDGE_FOLDER`, or pass `--vault` and `--folder` to an individual command. Never save personal paths in the Skill directory or repository.

Confirm every target stays inside the configured knowledge folder. For an update or structural operation, confirm every existing source and target exists.

All mutating script commands acquire deterministic per-note locks and replace each note atomically from a same-directory temporary file. Do not bypass the script with direct writes. A lock timeout or write failure means that note was not changed. Multi-note structural operations protect every affected path, but they are not a database transaction; if a later file fails after an earlier success, stop and report the partial result precisely.

### 2. Discover high-signal candidates

Scan the complete source before deciding what to save. Discovery is deliberately high-recall. Mark possible candidates when the material contains:

- repeated methods or explicit user approval;
- corrections, failures, fallback paths, verification, or stop conditions;
- permissions, review, approval, state transitions, or acceptance signals;
- explicit persistent preferences or repeated habits about output, collaboration, tools, organization, review, approval, or execution;
- a behavior that serves more than one purpose;
- reusable templates, checklists, criteria, or decision rules.

Do not write yet. A candidate is only an invitation to evaluate.

### 3. Apply the future-leverage gate

For every candidate, write a one-line future trigger, identify applicable value lenses, and ask what future action changes. Retain it only if the essentials pass.

Observed regression examples:

- **Word comments:** retain both `review changes before applying them` as risk protection and `use comments as an asynchronous collaboration and approval channel` as collaboration gain. They are separate knowledge units even when stored in one note.
- **Course-only STDP framework:** discard the course wrapper. Retain a generalized evidence principle only if it independently passes the gate and is not already covered elsewhere.
- **Browser timeout recovery:** retain finite retry, foreground/manual interaction fallback, verification, stop conditions, and permission boundaries. Low frequency does not cancel high recovery value.
- **User habit:** retain an explicit persistent preference such as a standing review boundary under `用户习惯`; discard a single request for a table or short answer unless the source shows that it is a stable cross-task preference.

### 4. Build the internal coverage ledger

Create an internal ledger before searching the vault. For each high-signal candidate include:

| Field | Required content |
| --- | --- |
| Candidate | One atomic knowledge unit |
| Future trigger | Observable situation in which it applies |
| Value type | One or more value lenses |
| Future retrieval question | The question a future search would ask |
| Proposed classification | Three semantic segments |
| Decision | `create`, `update`, `generalize`, `discard`, or `pending` |
| Reason | One concise sentence |
| Target | Proposed note or `none` |
| Habit evidence | For user-habit candidates only: explicit statement, repeated observations, or existing-note corroboration |

The ledger is internal working state. Do not save it to the vault and do not expose chain-of-thought. The final report gives only compact decisions and reasons.

### 5. Separate knowledge units from notes

An atomic knowledge unit is not automatically a separate note.

Keep multiple units in one note when they share the same object or scenario and future update direction. Make each unit retrievable through the title, aliases, headings, or keywords. Split notes only when future retrieval questions or update directions diverge.

For the Word-comments example, `controlled revision`, `collaboration channel`, and `approval/acceptance signal` may be three explicit sections in one note rather than three files.

Keep habits together only when they govern the same future usage context and will likely change together. Do not create one global profile note that mixes unrelated writing, tool, privacy, and collaboration preferences.

### 6. Classify, then search candidates

Choose the proposed three-segment classification before searching. Do not let the first lexical match determine meaning.

Use `用户习惯-领域-习惯对象.md` for a retained stable user habit. Keep methods, templates, sources, and ordinary knowledge in their existing classifications; `个人偏好` as a value lens does not by itself force the `用户习惯` note type.

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" candidates \
  --query "未来检索问题中的主题对象和方向" \
  --limit 8
```

Search independently for each retained cluster, using alternate terms when useful. Lexical scores are candidate hints only, never value or merge decisions.

### 7. Decide create, update, generalize, or discard

- Read a candidate note fully before updating it.
- Update only when topic object, future retrieval question, and future update direction match.
- Consolidate old and new knowledge into one better note; do not append a conversation dump.
- Preserve still-useful methods, preferences, boundaries, risks, and uncertainty.
- Remove stale wording, duplicates, and unnecessary project residue.
- If an existing note already covers the generalized lesson, report the new item as excluded due to duplication; do not create a narrower duplicate.
- A weak or ambiguous match is not permission to merge.
- For a habit update, distinguish a stable change from a contextual exception. Replace a superseded habit only when the newer evidence is explicit or clearly stronger.

### 8. Write for the knowledge type

Use only useful sections and omit empty headings.

**General method**

- 适用场景
- 核心原则
- 操作方法
- 判断标准
- 反例与边界

**Failure recovery**

- 触发症状
- 可能失效点
- 有限重试
- 回退路径
- 结果校验
- 停止条件
- 安全与权限边界

**Collaboration method**

- 适用场景
- 角色分工
- 权限与审批
- 反馈循环
- 验收信号
- 结束、清理与保留

**User habit**

- 适用场景
- 稳定习惯
- 默认执行方式
- 例外与边界
- 确认依据

Summarize `确认依据` as `用户明确说明`, `多次稳定选择`, or `既有习惯得到再次确认`; do not copy private raw conversation text into the note. Use `status: uncertain` only when the user explicitly asks to preserve a habit whose stability remains uncertain.

Prefer concise bullets. Use aliases and explicit headings to expose distinct value views without duplicating the note.

Write through the script:

```bash
# New note
python3 "<skill-dir>/scripts/knowledge_note.py" write \
  --title "方法-领域-方法名" \
  --content /path/to/note.md

# Existing note
python3 "<skill-dir>/scripts/knowledge_note.py" write \
  --title "方法-领域-方法名" \
  --target "<vault-path>/AI Knowledge/方法-领域-方法名.md" \
  --content /path/to/note.md
```

Treat `--title` as the complete filename classification. The script derives aligned YAML `type`, `domain`, and `topic` values from it while keeping the body heading concise.

### 9. Verify coverage and retrieval

After writing:

1. Re-read the saved note.
2. Map every retained unit to an explicit heading, alias, or keyword.
3. Search using at least one alternate phrasing for each important unit.
4. Confirm no duplicate note was introduced.
5. Confirm project-only and sensitive residue was removed.
6. Confirm the actual file path and operation result.
7. For each user habit, confirm the evidence threshold, scope, default action, and exceptions are explicit.

If alternate retrieval fails, improve headings or aliases in the same note. Do not create a duplicate merely to improve retrieval.

### 10. Audit only on request

Run Audit only when the user asks to inspect, check, clean up, or assess the knowledge base:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" audit
```

Treat Audit as read-only diagnosis. Report `error`, `review`, and `info` findings without exposing suspected secret values. Do not merge, rename, delete, or rewrite notes from an Audit result unless the user separately asks for fixes and the normal semantic and structural safety gates pass.

### 11. Organize conservatively

Same-note deduplication and consolidation are ordinary updates. Treat rename, merge, split, and section moves as structural operations. Read the structural reference and execute only with high confidence, low risk, no knowledge loss, and one clearly correct outcome. Otherwise report a suggestion without performing it.

## Failure Handling

- Preflight failure: make no changes and report the failed check.
- Candidate search failure: do not guess vault state or merge based on memory.
- Existing-note read failure: do not update or structurally modify that note.
- Write failure: do not claim the note was saved.
- Lock timeout: make no change to the locked note and report which operation could not start.
- Audit failure: do not claim the vault is healthy; report that the scan was incomplete.
- Structural failure: stop additional structural operations and report partial success precisely.
- Later failure after a successful change: identify what changed and what did not.

A no-op is a valid successful outcome when it prevents clutter.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| “Cross-project only” rejects rare but important recovery knowledge | Judge future leverage and impact first |
| A named framework sounds sophisticated, so it must be valuable | Test its future trigger and independent utility |
| One behavior gets one label | Check all value lenses and expose distinct units |
| One unit gets one file | Cluster by retrieval question and update direction |
| One request is treated as a stable habit | Require an explicit persistent instruction or repeated evidence |
| A habit note becomes a user profile | Store only the minimum actionable behavior rule and exclude sensitive inference |
| A duplicate warning becomes an automatic merge | Read both notes and reapply the semantic and structural gates |
| Audit silently rewrites the vault | Keep Audit read-only unless the user separately requests fixes |
| A direct file write bypasses the safety layer | Use the script so locks and atomic replacement remain active |
| Candidate score decides the destination | Classify first; use search only to find notes to read |
| New insight is appended to an old note | Rewrite a consolidated, cleaner note |
| Reporting exposes internal scoring or operation logs | Use only the compact added/updated/excluded brief |

## Required Final Brief

After every invocation, start with exactly:

`本次 ChatDistill 简报：`

Then use one line per knowledge cluster:

- `【新增】分类名｜新增：新知识简述｜理由：为什么建立新笔记`
- `【更新】分类名｜更新：合并、补充、简化或删除了什么｜理由：为什么修改`
- `【排除】分类名或知识主题｜排除：没有记录什么｜理由：为什么不记录`

Use these meanings consistently:

- `新增`: a new independent knowledge note was created.
- `更新`: an existing note changed. This includes adding knowledge to it, merging, simplifying, removing part of it, or deleting the entire note.
- `排除`: a high-signal candidate from this invocation was not written.

Always show all three labels. If a category is empty, write `【新增】无`, `【更新】无`, or `【排除】无`. Repeat a label on separate lines when it has multiple clusters.

Every non-empty line requires `理由：`. Render a three-segment classification inline with spaces, for example `方法 - 写作 - 批注驱动文档修订`.

The brief does not show internal value lenses, `价值类型`, `去向`, classification subheadings, operation-category blocks, or result-path lists. Do not list trivial noise or reveal private raw content.

Only when an operation actually fails, append `【失败】操作简述｜原因：失败原因`. Do not label a failed operation as `新增` or `更新`.

For an audit-only invocation, show the three empty labels first, then append the compact Audit summary and highest-value findings defined in `references/vault-audit.md`.

```markdown
本次 ChatDistill 简报：
【新增】无
【更新】工具 - Obsidian - 知识库规则｜更新：改用未来杠杆价值标准，并替换旧版汇报格式｜理由：减少误记和漏记
【更新】方法 - 写作 - 批注驱动文档修订｜更新：补充批注的协作与验收作用，并删除课程项目残留｜理由：让笔记更完整、纯净
【排除】方法 - 项目 - STDP证据化表达｜排除：课程限定的 STDP 框架｜理由：缺少独立未来用途，通用部分已有笔记覆盖
```

If no knowledge changes are made and no high-signal candidate is excluded:

```markdown
本次 ChatDistill 简报：
【新增】无
【更新】无
【排除】无
```
