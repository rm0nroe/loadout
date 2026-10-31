# Voice data

The voice data root is `$GHOSTWRITER_HOME`, default `~/.config/ghostwriter`. It lives outside every repository. Private samples, backups and logs stay there; only synthetic or redacted fixtures go into a repo.

No persona is bundled. For guided setup, follow [onboarding.md](onboarding.md): ask about shared and channel preferences, optionally calibrate with samples or paired drafts, and propose files for approval. Without setup or existing profiles, drafting uses the channel's general editorial rules.

## What the skill reads

- `soul.md`: what holds across channels.
- `<channel>.md`: one approved profile per channel, named after the channel: `slack.md`, `pr.md`, `pr-comment.md`, `email.md`, `commit.md`, `release-notes.md`, `postmortem.md`, `ticket.md`, `article.md`, `docs.md`. Any of them may be missing.
- `persona.md`: optional general writing persona, the fallback when a channel has no approved profile. `$GHOSTWRITER_PERSONA` points elsewhere if it lives outside the root. A channel profile may also reference this file for shared preferences; follow that reference when reading the profile.
- `rules.json`: the user's mechanical bans (for example em dashes, emoji), as `{"forbid": [{"pattern", "message", "channels"?}]}`. Written only with the user's approval, like a profile.
- Never read `imports/`, `corpus/`, `evals/`, `backups/` or other raw sample folders while drafting. Those are evidence for building a profile, not rules. `voice` lists `imports/*` as `candidate_corpora` so a profile proposal can find them.

`write_runner.py voice --channel <channel>` reports which of these exist and, when no approved profile exists, a fallback (`persona.md`, or `$GHOSTWRITER_PERSONA`) plus an optional questionnaire or sample request. It only inspects paths; it does not interview the user or save profiles.

## Samples and approval

- Samples may be any age. Each one carries provenance: where it came from, the date, and whether AI helped (`yes`, `no`, `unknown`).
- Samples marked `unknown` or `yes` for AI help are weak evidence. Flag any pattern that rests mostly on them.
- Building or changing `persona.md`, `soul.md`, a channel profile or `rules.json` is a proposal. Show the exact content, destination and evidence for each rule; write only after approval. Preserve an existing file in `backups/` before editing it. Follow onboarding's symlink and external-path checks when applicable.
- A wording correction the user makes deliberately and approves can teach voice, through the same approval step.
- Never promote a generated draft into the samples or the profile, and never change a voice rule on your own.
