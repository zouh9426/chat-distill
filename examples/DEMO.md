# ChatDistill demo

This demo uses only fictional content. It does not contain or require a personal
Vault.

## Scenario

During an AI-assisted browser task, an automation step repeatedly timed out.
The useful part of the conversation was not the specific website or project.
It was the reusable recovery rule:

- retry only a finite number of times;
- switch to a manual fallback when retries stop producing information;
- verify the final state;
- stop before an action could be duplicated or data could be overwritten.

ChatDistill would retain that method, remove project-specific residue, and
create or update the topic note shown in
[`demo-vault/AI Knowledge/方法-AI协作-有限重试与人工回退.md`](demo-vault/AI%20Knowledge/%E6%96%B9%E6%B3%95-AI%E5%8D%8F%E4%BD%9C-%E6%9C%89%E9%99%90%E9%87%8D%E8%AF%95%E4%B8%8E%E4%BA%BA%E5%B7%A5%E5%9B%9E%E9%80%80.md).

## Try the deterministic tools

From the repository root:

```bash
python3 skills/chat-distill/scripts/knowledge_note.py doctor \
  --vault examples/demo-vault

python3 skills/chat-distill/scripts/knowledge_note.py candidates \
  --vault examples/demo-vault \
  --query "自动化超时以后如何安全回退"

python3 skills/chat-distill/scripts/knowledge_note.py audit \
  --vault examples/demo-vault
```

These commands validate, search, and audit the included example. The semantic
distillation itself is performed by the AI agent following `SKILL.md`; the
Python script does not make knowledge-value decisions.

Do not configure the bundled demo as your permanent Vault. During real setup,
provide the root of your own Obsidian Vault to the agent.
