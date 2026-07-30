# ChatDistill

**Turn AI conversations into lasting Obsidian knowledge.**

ChatDistill is an agent Skill that distills useful methods, decisions, recovery
playbooks, reusable assets, and stable working preferences from the current AI
conversation into a personal Obsidian vault.

It is designed to build a high-value knowledge base, not a transcript archive.
ChatDistill writes only after an explicit request, searches for an appropriate
existing note before creating another one, and reports what it added, updated,
or excluded.

> ChatDistill is an independent community project. It is not affiliated with or
> endorsed by Obsidian, OpenAI, Anthropic, or the Claudian project.

## What it does

- Applies a future-value test before saving anything.
- Creates or consolidates topic-based Markdown notes.
- Keeps stable user preferences separate from ordinary knowledge.
- Uses per-note locks and atomic file replacement for safer writes.
- Audits the knowledge folder without changing it.
- Supports Codex and Claude Code.
- Optionally works with Claudian so the agent can run inside Obsidian.

## What it does not do

- It does not automatically read your chat history.
- It does not silently record every conversation.
- It does not infer and store sensitive personal traits.
- It does not require Obsidian to be open.
- It does not require Claudian.
- It is not a backup system; keep your own Vault backups.

## Requirements

- macOS or Linux
- Python 3.9 or newer
- a local Obsidian Vault containing a `.obsidian` directory
- Codex, Claude Code, or another compatible agent that can use Skills and access
  the Vault

Windows is not supported in the current release because the write-locking layer
uses POSIX `fcntl`.

## Install

### Codex

Ask Codex:

```text
Use $skill-installer to install:
https://github.com/zouh9426/chat-distill/tree/main/skills/chat-distill

Then follow the ChatDistill setup instructions. Before accessing anything,
ask me for the exact Obsidian Vault path. Configure it without reading any note
contents, run doctor, and report what was configured.
```

Restart Codex if the new Skill is not visible in the current session.

### Claude Code

Copy the `skills/chat-distill` directory to one of:

- personal installation: `~/.claude/skills/chat-distill`
- project installation: `.claude/skills/chat-distill`

Then ask Claude Code:

```text
Read the ChatDistill setup reference and configure this Skill for my Obsidian
Vault. Ask me for the exact Vault path first. Do not search my home directory,
read note contents, or change the Vault during setup. Run doctor and report the
result.
```

## Configure

Users do **not** edit `SKILL.md` or put personal paths in the repository.
ChatDistill stores the Vault choice in a private local configuration file.

Ask your agent to configure it, or run:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" configure \
  --vault "<vault-path>" \
  --folder "AI Knowledge"

python3 "<skill-dir>/scripts/knowledge_note.py" doctor
```

Replace:

- `<skill-dir>` with the installed `chat-distill` directory containing
  `SKILL.md`.
- `<vault-path>` with the Obsidian Vault root containing `.obsidian`.
- `AI Knowledge` with another relative folder inside the Vault if desired.

The default configuration file is
`~/.config/chat-distill/config.json` and is written with `0600` permissions.
Resolution order is:

1. command arguments: `--vault`, `--folder`
2. environment variables: `OBSIDIAN_VAULT_PATH`,
   `OBSIDIAN_KNOWLEDGE_FOLDER`
3. private local configuration
4. the current directory, when it is an Obsidian Vault root

Use `CHATDISTILL_CONFIG_PATH` or `--config` for a different configuration file,
including separate profiles for multiple Vaults.

`doctor` checks the selected directory and `.obsidian` marker. It reports
`notes_read: 0` and does not create, scan, or modify knowledge notes.

The canonical setup instructions for agents are in
[`skills/chat-distill/references/setup.md`](skills/chat-distill/references/setup.md).

## Use

ChatDistill responds to explicit requests such as:

```text
Use $chat-distill to save the reusable knowledge from this conversation to my
Obsidian vault.
```

```text
Use $chat-distill to update my knowledge base with the useful recovery method
we just discovered. Do not save the project-specific details.
```

```text
Use $chat-distill to run a read-only Vault Audit. Report findings first and do
not fix anything.
```

In Claude Code, use `/chat-distill` where its Skill invocation syntax requires
a slash command.

## Optional Claudian integration

[Claudian](https://github.com/YishenTu/claudian) is an Obsidian community plugin
that can run Codex, Claude Code, and other agents from inside Obsidian.
ChatDistill does not depend on it.

If you want this workflow:

1. Install and enable Claudian in Obsidian.
2. Install and authenticate the Codex or Claude Code CLI.
3. Let Claudian auto-detect the CLI.
4. If detection fails, run `command -v codex` or `command -v claude` and place
   the returned executable path in the matching Claudian provider setting.
5. Install and configure ChatDistill separately as described above.

The CLI executable path in Claudian and the Obsidian Vault path in ChatDistill
are different settings. Changing Obsidian or Claudian settings is not required
for standalone use.

## Privacy and safety

ChatDistill follows an explicit-action model:

- Setup asks for the exact Vault path instead of scanning the home directory.
- Setup validation reads zero note contents.
- Saving and auditing occur only after an explicit user request.
- Audit is read-only by default.
- Structural operations use stricter checks and report partial failures.
- Credentials and raw sensitive values are excluded from notes and reports.
- Personal paths live outside the repository.

See [SECURITY.md](SECURITY.md) for the complete security model and limitations.

## Development

Run the tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
```

Validate the Skill with the current `quick_validate.py` from OpenAI's
[skill-creator](https://github.com/openai/skills):

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skills/chat-distill
```

The test suite uses temporary example Vaults and does not require or access a
personal Vault.

## License

[MIT](LICENSE)
