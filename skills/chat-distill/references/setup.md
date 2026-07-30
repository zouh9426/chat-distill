# ChatDistill Setup

Use this reference when installing, configuring, diagnosing, or connecting ChatDistill through Codex, Claude Code, or Claudian.

## Contents

1. Safety rules
2. Requirements
3. Install the Skill
4. Configure the Vault
5. Validate without reading notes
6. Use multiple Vaults
7. Optional Claudian integration
8. Setup report

## 1. Safety rules

- Ask the user for the intended Obsidian Vault path. Do not scan their home directory to discover Vaults.
- Do not overwrite an existing `chat-distill` Skill without explicit approval.
- Store personal paths only in local configuration, environment variables, or per-command arguments. Never write them into `SKILL.md`, examples, or a Git repository.
- During setup, validate only the directory and `.obsidian` marker. Do not read note contents or run `audit`.
- Do not display tokens, provider credentials, or environment-variable values.

## 2. Requirements

- macOS or Linux
- Python 3.9 or newer
- a local Obsidian Vault containing a `.obsidian` directory
- a compatible AI agent with permission to access that Vault

Obsidian does not need to remain open. Claudian is optional and is required only when the user wants to run the agent inside the Obsidian interface.

## 3. Install the Skill

The installed directory must be named `chat-distill` and must contain `SKILL.md`.

For Codex, prefer the built-in Skill installer with the repository subtree URL:

```text
$skill-installer install https://github.com/zouh9426/chat-distill/tree/main/skills/chat-distill
```

Restart Codex if the new Skill does not appear in the current session.

For Claude Code, install the `skills/chat-distill` directory at one of:

- personal: `~/.claude/skills/chat-distill`
- project: `.claude/skills/chat-distill`

Do not copy the repository-level README, tests, examples, or GitHub Actions files into the installed Skill directory.

## 4. Configure the Vault

Resolve `<skill-dir>` as the installed directory containing `SKILL.md`. Ask the user for the exact Vault path, then run:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" configure \
  --vault "<vault-path>" \
  --folder "AI Knowledge"
```

The default config path is:

```text
~/.config/chat-distill/config.json
```

The config file is written with `0600` permissions. Override its location with `CHATDISTILL_CONFIG_PATH` or `--config` when required.

## 5. Validate without reading notes

Run:

```bash
python3 "<skill-dir>/scripts/knowledge_note.py" doctor
```

Success reports `ok: true` and `notes_read: 0`. Do not create the knowledge folder or run a content scan during setup unless the user separately asks to save or audit knowledge.

## 6. Use multiple Vaults

Resolution order is:

1. `--vault` and `--folder`
2. `OBSIDIAN_VAULT_PATH` and `OBSIDIAN_KNOWLEDGE_FOLDER`
3. private local config
4. current directory when it is an Obsidian Vault root

Use per-command arguments for temporary overrides. Use separate config files through `CHATDISTILL_CONFIG_PATH` when the user wants several persistent profiles.

## 7. Optional Claudian integration

Claudian is an optional Obsidian community plugin that embeds Claude Code, Codex, and other agents in the Vault. It is not a ChatDistill runtime dependency.

When the user wants this integration:

1. Ask them to install and enable Claudian in Obsidian.
2. Ask which provider they want: Codex or Claude Code.
3. Confirm that provider's CLI is installed and authenticated.
4. Let Claudian auto-detect the CLI first.
5. If detection fails, locate it with `command -v codex` or `command -v claude`, then ask the user to place that exact executable path in the matching Claudian provider setting.
6. Keep the Claudian CLI path separate from the ChatDistill Vault path.
7. Verify that the provider can invoke `$chat-distill` in Codex or `/chat-distill` in Claude Code.

Changing Obsidian settings or operating its interface requires the user's approval. Never inspect or report Claudian environment-variable values or authentication data.

## 8. Setup report

Report:

- installed Skill directory;
- configured Vault and knowledge folder;
- private config path;
- `doctor` result;
- whether Claudian was configured or intentionally skipped;
- any remaining manual action.

State explicitly that setup read zero note contents and made no knowledge changes.
