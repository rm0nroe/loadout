# Security

## Reporting a vulnerability

Report it privately through GitHub's private vulnerability reporting: the **Security** tab of this repository, then **Report a vulnerability**. Please do not open a public issue for a security problem.

Include the skill, what you ran, and what happened. Expect a first reply within 7 days.

## What is in scope

- The scripts that ship with skills: `ink-it/scripts/write_runner.py`, `load-clip/scripts/` (`clip.sh`, `clip-slack.sh`, `md2html.py`) and `readme-banner/scripts/wordmark.py`.
- Skill instructions that could lead an agent to leak data, run something you did not ask for, or skip a safety step the skill promises (for example, `ink-it` sending or committing when it says it only drafts).

## What the skills do and don't do

- No script makes a network call. `write_runner.py` uses only the Python standard library and starts no other process. The `load-clip` scripts call the macOS tools `textutil` and `osascript` and write only to a temporary directory.
- Skills run with your agent's permissions. Text you give a skill goes to your model provider like any other prompt.
- `ink-it` reads voice profiles from `~/.config/ghostwriter/` (or `$GHOSTWRITER_HOME`). None ship with this repo.
- `roundtable` starts background agents in your session, and `slop-radar` can open a URL you give it. Both work only on what you point them at.
- `readme-banner` has `uv` download `fonttools` the first time its outline script runs, and can download an open-license font from Google Fonts. The script itself makes no network call.
- `exec-recap` runs `git fetch` and read-only `gh` queries (releases, release notes, merged PRs) on the repo you point it at. It changes nothing in the repo.

Review any skill before you install it, the same as any code you run.
