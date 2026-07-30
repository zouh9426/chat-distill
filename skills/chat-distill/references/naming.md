# Obsidian Knowledge Note Naming

Use this reference before choosing or changing filenames, YAML classification, titles, aliases, or date treatment.

## Contents

Core model · Decision order · Domains · Note types · Granularity · Dates · YAML · Aliases · Conflicts · Examples

## 1. Core model

Use three semantic segments for ordinary notes. Each segment should make the future retrieval target clearer.

Default:

`领域-主题对象-细分方向.md`

Functional patterns:

- `用户习惯-领域-习惯对象.md`
- `方法-领域-方法名.md`
- `模板-场景-用途.md`
- `资料-来源或对象-主题.md`

Structural exception: `索引-领域.md`

The three segments are storage classification. `质量提升`, `失败恢复`, `协作增益`, and other value lenses belong in internal evaluation or note content, not in the user-facing brief and not as new top-level filename types. `用户习惯` is a dedicated semantic note type for a stable actionable user preference; it is not another value lens.

In the user-facing brief, put the classification inline after `【新增】` or `【更新】`, with spaces for readability: `【更新】方法 - 写作 - 批注驱动文档修订｜...`. Use it after `【排除】` when the rejected candidate has a meaningful proposed classification. The actual filename remains `方法-写作-批注驱动文档修订.md`.

## 2. Naming decision order

Choose in this order:

1. Stable user preference or usage habit that should change future agent behavior → `用户习惯-领域-习惯对象.md`.
2. Reusable method, workflow, checklist, criterion, analysis logic, recovery path, collaboration method, or decision rule → `方法-领域-方法名.md`.
3. Reusable writing, email, report, resume, script, Q&A, complaint, or communication format → `模板-场景-用途.md`.
4. Source material whose source identity is itself useful and explicitly worth retaining → `资料-来源或对象-主题.md`.
5. Domain navigation or MOC → `索引-领域.md`.
6. Everything else → `领域-主题对象-细分方向.md`.

Do not choose `资料-` merely because a conversation mentioned a document. If the note stores the user's method or conclusion, choose `方法-` or the default form.

## 3. Domains and semantic segments

Preferred domains:

- `投资`
- `学业`
- `求职`
- `住房`
- `项目`
- `写作`
- `工具`
- `生活`

Add a new domain only when:

- none of the existing domains fits naturally; and
- the area is likely to accumulate multiple valuable notes.

Do not use a course code, company, project name, stock, participant, temporary deliverable, or version as the default domain.

Segment roles:

- `领域`: stable area of future use.
- `主题对象`: the object the user will search for.
- `细分方向`: the problem, method, decision, or outcome within that object.

For functional patterns, the prefix states note type and the remaining segments carry the same semantic job.

## 4. Note-type patterns

### User habit

`用户习惯-领域-习惯对象.md`

Use for a stable, actionable preference about how future work should be performed for this user. The second segment is the stable usage domain; the third is the habit object that a future agent will search for.

Require either an explicit persistent instruction or repeated evidence. Do not use this type for a one-off request, temporary project constraint, inferred personality, raw private routine, sensitive attribute, or speculative user profile.

Examples:

- `用户习惯-写作-表达与篇幅.md`
- `用户习惯-工具-Obsidian记录偏好.md`
- `用户习惯-项目-修改前确认.md`

Keep only the minimum actionable rule, its scope, exceptions, and a summarized evidence basis. Separate unrelated habits by domain and update direction instead of collecting them in one global profile note.

### Method

`方法-领域-方法名.md`

Use for:

- workflows and checklists;
- evaluation and decision criteria;
- failure recovery and verification;
- risk controls;
- collaboration, review, and approval methods;
- analysis frameworks with genuine future leverage.

Examples:

- `方法-写作-批注驱动文档修订.md`
- `方法-工具-浏览器超时回退.md`
- `方法-项目-需求澄清.md`
- `方法-投资-订单验证.md`

### Template

`模板-场景-用途.md`

Use for a reusable finished structure or wording pattern, not merely guidance about writing it.

Examples:

- `模板-邮件-课程申请.md`
- `模板-报告-自我反思.md`
- `模板-演讲-QA准备.md`

### Source or reference

`资料-来源或对象-主题.md`

Use sparingly. The source itself must be a reusable reference, or the user must explicitly ask to preserve it.

Examples:

- `资料-合同-风险条款.md`
- `资料-官方回复-申请流程.md`

Do not use `资料-课程-STDP.md` for a course-only framework merely because it came from course material. Apply the value gate first.

### Default knowledge note

`领域-主题对象-细分方向.md`

Use when the note is valuable knowledge but is not primarily a method, template, source, or index.

Examples:

- `写作-英文邮件-沟通表达.md`
- `住房-租房合同-风险条款.md`
- `求职-简历优化-产品经理.md`

### Index

`索引-领域.md`

Create only when enough related notes exist to require navigation. An index links and organizes; it does not replace specific notes.

## 5. Granularity and safety

- Prefer exactly three semantic segments for ordinary notes.
- Keep each segment concise and identifiable.
- Do not encode every metadata dimension in the filename.
- Avoid titles as broad as `投资.md`, `项目.md`, or `一些想法.md`.
- Avoid conversation-like titles and full-sentence filenames.
- Use half-width hyphens `-` as separators.
- Do not use `/ \ : * ? " < > |`.
- Avoid spaces unless part of an official English name.
- Keep official acronyms only when they materially improve retrieval.
- Generalize project-specific names unless the user explicitly requests archival detail.

Good granularity:

- `用户习惯-写作-表达与篇幅.md`
- `方法-写作-批注驱动文档修订.md`
- `工具-Obsidian-知识记录规则.md`

Too broad:

- `写作.md`
- `协作.md`

Overloaded:

- `方法-大学课程-COM5505-STDP-小组演讲-证据-最终版.md`

## 6. Dates

Do not add dates to long-term knowledge filenames by default.

Use a date only when the note is inherently a historical snapshot or the user explicitly asks for time-bound archival material, such as:

- daily or weekly review;
- meeting or event record;
- stage decision;
- final submission snapshot.

Prefer YAML fields for ordinary time information:

```yaml
created: YYYY-MM-DD
updated: YYYY-MM-DD
event_date:
source_date:
```

## 7. YAML alignment

Recommended base:

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: chat-distill
topic:
aliases: []
tags:
  - chat-distill
  - ai-knowledge
domain:
type:
status:
source_date:
related: []
---
```

Alignment rules:

- Default `领域-主题对象-细分方向`: `domain` = 领域; `topic` = 主题对象-细分方向.
- `用户习惯-领域-习惯对象`: `type` = 用户习惯; `domain` = 领域; `topic` = 习惯对象.
- `方法-领域-方法名`: `type` = 方法; `domain` = 领域; `topic` = 方法名.
- `模板-场景-用途`: `type` = 模板; `topic` = 场景-用途; add `domain` only when clear.
- `资料-来源或对象-主题`: `type` = 资料; `topic` = 来源或对象-主题; add `domain` only when clear.
- `索引-领域`: `type` = 索引; `domain` and `topic` = 领域.

Optional fields may be omitted when they add no value or cannot be inferred confidently. Never invent metadata to fill a schema.

Useful `type` values include `用户习惯`, `知识卡`, `方法`, `模板`, `资料`, `索引`, `判断标准`, `风险清单`, and `复用规则`.

Useful `status` values include `active`, `draft`, `archived`, `outdated`, and `uncertain`.

## 8. Titles and aliases

- Prefer a concise body title that names the topic, not a mechanical copy of every classification segment.
- Use aliases for old filenames, common user wording, alternate retrieval language, official English names, and important abbreviations.
- When multiple value views share one note, expose them with headings or aliases rather than duplicate files.
- Preserve the old title as an alias after a rename or merge.

Example:

```yaml
topic: 批注驱动文档修订
aliases:
  - Word批注协作
  - 修改前审批
  - 批注反馈循环
domain: 写作
type: 方法
```

## 9. Conflicts and maintenance

If the same filename exists:

- same retrieval question and update direction → update and consolidate it;
- different topic → make the topic object or direction more precise;
- ambiguous relationship → keep separate and do not rename or merge automatically.

Consider a rename only when the current name is vague, temporary, misleading, or materially harms retrieval. Do not rename for cosmetic consistency alone.

Consider a split only when independent future retrieval questions or update directions coexist. Multiple value lenses alone do not require multiple notes.

Consider a merge only when notes are true duplicates or one consolidated note clearly preserves and improves all useful knowledge.

## 10. Examples

| Knowledge | Filename | Inline brief classification |
| --- | --- | --- |
| Stable preference for concise writing | `用户习惯-写作-表达与篇幅.md` | `用户习惯 - 写作 - 表达与篇幅` |
| Obsidian recording preference | `用户习惯-工具-Obsidian记录偏好.md` | `用户习惯 - 工具 - Obsidian记录偏好` |
| Word comments for review and collaboration | `方法-写作-批注驱动文档修订.md` | `方法 - 写作 - 批注驱动文档修订` |
| Browser automation timeout recovery | `方法-工具-浏览器超时回退.md` | `方法 - 工具 - 浏览器超时回退` |
| Reusable application email body | `模板-邮件-课程申请.md` | `模板 - 邮件 - 课程申请` |
| Contract source clauses | `资料-合同-风险条款.md` | `资料 - 合同 - 风险条款` |

Classification never overrides the future-leverage gate. A well-formed filename is not evidence that the content deserves a note.
