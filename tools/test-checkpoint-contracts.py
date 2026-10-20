#!/usr/bin/env python3
"""Pin source instructions only; this does not exercise native model compliance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
load = (ROOT / 'skills/productivity/checkpoint-load/SKILL.md').read_text()
save = (ROOT / 'skills/productivity/checkpoint-save/SKILL.md').read_text()
for clause in (
    'before any ordinary-file lookup',
    'reject malformed `sendit-` names',
    'exact requested run',
    'before reading the view or invoking the runtime',
    'Claude uses `CLAUDE_CONFIG_DIR` when set, otherwise `$HOME/.claude`',
    'Codex uses `CODEX_HOME` when set, otherwise `$HOME/.codex`',
    'as a separate command',
    'exit status and full JSON output',
    'all nine semantic fields and retained limits',
    'Never fall back to an ordinary file, another task, a source-checkout runtime, or a latest checkpoint',
    'stop without confirming a load',
):
    assert clause in load, clause
for clause in (
    'reject it for manual checkpoint names',
    'run, platform, snapshot sequence and sealed hash',
    'all nine semantic fields and retained limits',
    'label this manual document as session notes',
    'Do not overwrite the Git-local generated view',
):
    assert clause in save, clause
print('PASS: Loadout reserved routing, fail-closed readback and manual save authority contracts')
