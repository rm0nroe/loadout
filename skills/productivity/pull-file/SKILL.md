---
name: pull-file
description: "Instantly loads a specific session checkpoint. Usage: /pull-file <session_name>"
---

# Load Session State

1. Identify the `<session_name>` provided immediately after the command.
2. Determine the current project: the basename of the git repository root (`git rev-parse --show-toplevel`), or of the working directory outside a repo, so subfolders of one repo share state.
3. Locate and read the file at `~/.claude_states/<project>/<session_name>.md`.
4. If the file does NOT exist, output: "Checkpoint not found. Run `/file-cabinet` (`/rm0nroe-loadout:file-cabinet` if installed as a plugin) to see available checkpoints for this project."
5. If the file DOES exist, silently read and absorb the entire document to prime your context. Do not summarize it back to me.
6. Reply with a short confirmation: "Session `<session_name>` loaded. Ready to execute next actions:" followed by the checkpoint's next actions as sub-bullets, one line each, in the checkpoint's own order. Keep each to a single line: the action itself, no rationale, no restated background, so the reply shows what is being worked on next without re-summarizing the checkpoint. If the checkpoint records no next actions, say so on one line instead.
