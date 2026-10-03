# ink-it skill

Drafts Slack messages, emails and PR comments (Ghostwriter rules), PR titles and bodies (pr-creator rules) commit messages (repository conventions), and release notes, postmortems, tickets, articles and docs (Sepia rules) in the user's voice. It is drafting only and never sends, posts, commits, pushes, rebases or edits PRs.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | The skill: routing, workflow, revision budget, attribution rules |
| `references/slack.md`, `email.md`, `pr-comment.md`, `tells.md` | Ghostwriter rule sets (adapted) |
| `references/commit.md` | Commit message card: convention comes from repo evidence |
| `references/professional.md`, `release-notes.md`, `postmortem.md`, `ticket.md`, `article.md`, `docs.md` | Professional-document rule set (Sepia, adapted; docs card is local) |
| `references/pr.md` | PR rule set (pr-creator, adapted, drafting only) |
| `references/review.md` | Pre-finalize review, independent review packet, post-finalize meaning recheck |
| `references/voice.md` | Voice data root, approval rules for profiles and `rules.json` |
| `scripts/write_runner.py` | `route`, `voice`, `snapshot`, `finalize` (stdlib only) |
| `PROVENANCE.md`, `THIRD_PARTY_NOTICES.md` | Pinned upstream revisions, local changes, MIT notices |
| `config/claude-settings.json` | Attribution source-off for Claude Code, passed per run with `--settings` |
| `tests/test_gates.py`, `tests/fixtures/` | Correctness gates; all fixtures are synthetic |

## Run the gates

```sh
python3 -m unittest discover -s tests -v
```

## Use without installing

Claude Code, project-scoped (no global install): symlink or copy this skill directory to `<project>/.claude/skills/ink-it`, then run `claude --settings <skill directory>/config/claude-settings.json`.

Codex: point it at `SKILL.md` in the prompt. Codex attribution is account/workspace policy with no verified local switch; it only applies to commits and PRs Codex creates, which this skill never does.

## Voice data

Lives in `$GHOSTWRITER_HOME` (default `~/.config/ghostwriter`), never in this repo. `rules.json` there holds the user's mechanical bans. With none, no punctuation is banned. Imports under `imports/` are unapproved candidate evidence.
