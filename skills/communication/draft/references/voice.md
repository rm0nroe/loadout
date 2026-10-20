# Voice data

The voice data root is `$GHOSTWRITER_HOME`, default `~/.config/ghostwriter`. It lives outside every repository. Private samples, backups and logs stay there; only synthetic or redacted fixtures go into a repo.

## What the skill reads

- `soul.md`: what holds across channels.
- `<channel>.md`: one approved profile per channel, named after the channel: `slack.md`, `pr.md`, `pr-comment.md`, `email.md`, `commit.md`, `release-notes.md`, `postmortem.md`, `ticket.md`, `article.md`, `docs.md`. Any of them may be missing.
- `persona.md`: optional general writing persona, the fallback when a channel has no approved profile. `$GHOSTWRITER_PERSONA` points elsewhere if it lives outside the root.
- `rules.json`: the user's mechanical bans (for example em dashes, emoji), as `{"forbid": [{"pattern", "message", "channels"?}]}`. Written only with the user's approval, like a profile.
- Never read `imports/`, `corpus/`, `evals/`, `backups/` or other raw sample folders while drafting. Those are evidence for building a profile, not rules. `voice` lists `imports/*` as `candidate_corpora` so a profile proposal can find them.

`write_runner.py voice --channel <channel>` reports which of these exist and, when no approved profile exists, a fallback (`persona.md`, or `$GHOSTWRITER_PERSONA`) plus the sample request to relay.

## Samples and approval

- Samples may be any age. Each one carries provenance: where it came from, the date, and whether AI helped (`yes`, `no`, `unknown`).
- Samples marked `unknown` or `yes` for AI help are weak evidence. Flag any pattern that rests mostly on them.
- Building or changing a profile is a proposal. Show the user the proposed profile text and what evidence supports each rule; write `<channel>.md` only after they approve. Move an existing profile to `backups/` first.
- A wording correction the user makes deliberately and approves can teach voice, through the same approval step.
- Never promote a generated draft into the samples or the profile, and never change a voice rule on your own.
