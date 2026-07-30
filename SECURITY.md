# Security and privacy model

ChatDistill manages personal Markdown knowledge. Treat its access to an
Obsidian Vault with the same care as any local file-management tool.

## User-controlled actions

ChatDistill is designed to act only after an explicit request:

- Installation and setup do not authorize reading note contents.
- `doctor` validates the Vault path and `.obsidian` marker without reading
  notes.
- Saving authorizes evaluation of the material supplied in the current task and
  the minimum relevant candidate notes, not unrestricted collection of chat
  history.
- `audit` is read-only and runs only when explicitly requested.
- An audit result does not authorize automatic fixes.
- Rename, merge, split, and section moves require high semantic confidence and
  must stay inside the configured knowledge folder.

## Local data

The default local configuration is:

```text
~/.config/chat-distill/config.json
```

It contains the chosen Vault path and knowledge-folder name, and is created with
`0600` permissions. It contains no model credentials. Personal paths must not be
committed to this repository.

New notes are created with `0600` permissions. Existing note permissions are
preserved on replacement. Mutating commands use deterministic per-note locks
and same-directory atomic replacement.

## Data minimization

The Skill instructs the agent to:

- retain reusable knowledge instead of conversation transcripts;
- exclude credentials and unnecessary private details;
- avoid inferring sensitive user traits;
- store only the minimum actionable form of a stable preference;
- report suspected secrets without echoing their values.

The agent and model provider may have their own data-handling behavior.
ChatDistill does not override those products' settings or policies.

## Scope and limitations

- Supported platforms: macOS and Linux.
- Windows is not currently supported because locking uses POSIX `fcntl`.
- Multi-note operations protect every affected file but are not database
  transactions. A later failure can leave a precisely reported partial result.
- Atomic replacement reduces corruption risk but is not a backup.
- Sync tools and other editors can still create conflicts outside
  ChatDistill's process locks.
- A malicious or incorrectly configured agent may ignore Skill instructions.
  Review agent permissions and keep independent Vault backups.
- Claudian is optional and has its own security model.

## Reporting a vulnerability

Do not place credentials, private notes, or exploit details in a public issue.
Use GitHub's private vulnerability reporting for this repository when it is
enabled. If private reporting is not available, open a minimal issue requesting
a private contact channel without including sensitive details.
