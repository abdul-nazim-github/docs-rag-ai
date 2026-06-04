Commit hook: AI-Checked token

This repository includes a lightweight commit-msg hook that enforces a
convention: non-document commits must include the token `AI-Checked: yes`
in the commit message. The intent is to ensure contributors (or agents)
acknowledge they've read `AI/CONTEXT.md`, `AI/FILE_MAP.md`, and `AI/RULES.md`
before changing RAG-critical files.

Install locally (one-time):

```bash
cd /path/to/repo
mkdir -p .git/hooks
cp .githooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

Guidance:
- For doc-only commits (AI/*.md or .github templates), the hook allows commits
  without the token.
- For code changes touching fragile files (see `AI/FILE_MAP.md`), include in
  your commit message: `AI-Checked: yes` and mention what you validated.

Example commit message:

```
Fix: improve chunking edge-case handling

AI-Checked: yes
Reviewed AI/FILE_MAP.md and AI/RULES.md — change preserves metadata and added tests.
```
