# Provenance

Sources pinned 2026-09-24 (Sepia text first used 2026-09-25). Both revisions were the upstream `main` HEAD on that date.

| Source | Revision | License | Used for |
|---|---|---|---|
| https://github.com/mblode/agent-skills `skills/ghostwriter/` (SKILL.md, references/surfaces.md, strategy.md, tells.md) | `ec7f60811b30aa5eb0be58772cedbfc86454186f` | MIT, Copyright (c) 2026 Matthew Blode | `references/slack.md`, `references/email.md`, `references/pr-comment.md`, `references/tells.md`, `references/voice.md` |
| https://github.com/mblode/agent-skills `skills/pr-creator/` (SKILL.md) | `ec7f60811b30aa5eb0be58772cedbfc86454186f` | MIT, same | `references/pr.md` |
| https://github.com/Nanako0129/sepia | `06a5233395299ff78558b15568679c2c5c0fe942` | MIT, Copyright (c) 2026 Nanako Tsai | `references/professional.md` (professional-pass.md), `release-notes.md`, `postmortem.md`, `ticket.md`, `article.md` (domains/*). |

Ghostwriter's strategy reference credits Wes Kao's frameworks via kinantid/skills (MIT) and Alison Green; `references/slack.md` keeps the lead-with-the-point, ask and bad-news guidance derived from it.

## Local modifications

- **Ghostwriter to `slack.md`:** kept the chat surface, modes and precedence. Dropped the blanket refusal to draft emotionally weighted partner messages (not part of the approved design). Dropped the "shortest true version / cut it in half" default (no mandatory shortening). Dropped the non-chat surfaces. Voice profile slugs narrowed to `soul`, `slack`, `pr`.
- **Ghostwriter email and review/PR comment surfaces to `email.md` and `pr-comment.md`:** kept the shape defaults and the finding format (line, problem, cost, fix once). Dropped "reply shorter than what it answers" as a rule (no mandatory shortening). Added the `Subject:` output line and the reviewer-vs-author split. Send, post and submit actions removed.
- **Commit messages (`commit.md`):** no upstream source. Ghostwriter and pr-creator prescribe no commit style; the card only defines how to find the convention (rules, then history) and the output shape.
- **Sepia to `professional.md` and the domain cards:** kept the ten-check professional checklist, the venue-first rule, the whitelist, the domain tells and rules for release notes, postmortems, tickets and technical articles. Dropped everything fiction, journalism, model-fingerprint and language-specific, the detector-evidence framing and any "make it read as human" goal, the four-operation and model-identity protocol, the report format, unattended mode and protected-range syntax (the runner owns protection). Added the claims-list, research/citation rule (cite only what was read), outline check (first sentences of a long document), no-invented-dead-ends, and the output shapes (`Title` line, blank line, body for tickets). `docs.md` has no upstream domain file: it is a local card built on the professional pass and the article rules.
- **Ghostwriter tells to `tells.md`:** Slack, email and PR comments. Blanket punctuation bans (em dash, `--`, spaced hyphen) became per-user: the profile decides, and the runner enforces only the user's `rules.json`.
- **Ghostwriter profile writing to `voice.md`:** profile creation became propose-then-approve. Samples carry AI-assistance provenance; generated drafts are never promoted.
- **pr-creator to `pr.md`:** drafting only. Removed push, `gh pr create`/`gh pr edit`, draft/reviewer handling, and the whole commit-restructuring reference (`pr-polish.md`). Repo templates and the user's own format override the one-paragraph and no-Test-plan defaults. Removed upstream rule 8, which leaves the harness attribution footer in place: this skill strips all AI attribution instead.
- **Mechanical checks:** repeated words, double spaces and stray backticks are stdlib regexes in `finalize` (previously a scoped Vale config). The runner also checks attribution, PR title/body shape, Test plan and checkbox defaults, and the user's `rules.json` bans. No editorial tells.
