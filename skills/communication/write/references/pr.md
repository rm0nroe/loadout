# PR title and body card (pr-creator rules)

Adapted from pr-creator (see `../PROVENANCE.md`), drafting half only. This card writes text. It never pushes, creates or edits a PR, commits, rebases or restructures history; hand the text back and the user runs the command.

## Precedence

1. The user's explicit instructions for this PR.
2. The repo's PR template, if one exists.
3. The approved voice profile (`pr.md`, then `soul.md`, then the persona fallback).
4. The defaults below.

A finished title and body the user supplies is the draft under review, not raw notes: keep it byte for byte unless a rule in this card is violated, and change only what a finding names. A profile default (format, tense, bullets, title style) never rewrites text the user wrote; it applies to drafts you write from notes.

Any of the first three overrides the one-paragraph default and the no-Test-plan default. Example: a profile that says "flat bullet list of lowercase gerund phrases, no headers" wins over the paragraph.

## Gather facts (read-only)

- Diff against the real PR base with three dots: `git diff <base>...HEAD`. Don't assume `main`; stacked PRs have other bases. `gh pr view --json baseRefName,title,body,state` tells you the base of an existing PR.
- `git log <base>..HEAD --format=%s%n%b` for the commits' stated reasons.
- Templates: first match of `pull_request_template.md` (case-insensitive) in `.github/`, the repo root or `docs/`, or a `PULL_REQUEST_TEMPLATE/` directory in any of those. Pass the file to `finalize --template`.
- Ticket ID from the branch, commits or prompt, uppercased (`mblode/abc-123-add-auth` gives `ABC-123`). Never guess one: a wrong ID links someone else's issue.

## Output format

Line 1 is the title, then one blank line, then the body. No `Title:` prefix.

## Title

- With a ticket ID: `ABC-123: Add auth flow`. Without: `Add auth flow`. No trailing period.
- If the repo lints PR titles (a `semantic-pull-request` or commitlint workflow under `.github/workflows/`), use its shape: `feat: add auth flow (ABC-123)`.
- The user's profile can set a different convention; follow it.
- Partial work: keep the ID out of the title and write `Part of ABC-123` in the body.

## Body defaults

- What changed and why it matters, in the first sentence. The diff already says what changed file by file.
- No fake why. If the reason isn't in the prompt, ticket, branch, commits or diff, leave it out.
- `Risk:` line only for migrations, billing, auth, permissions, irreversible writes, wide blast radius or subtle behavior change.
- `Input wanted:` line only when an open decision in the diff would change on the reviewer's answer; name the decision.
- Testing: say what ran only if it actually ran. No `Test plan` section or checkboxes unless the user asks for one (pass `finalize --allow test-plan` and/or `--allow checkboxes`) or the template has one (pass `--template`).
- Diff over 500 lines or five-plus files: one `Review path:` line saying where to start.
- With a template: keep its headings, answer each in a sentence or two, add nothing it or the user doesn't ask for.
- Stop after the useful content. No footer of any kind.

## Anti-patterns

- Openers that narrate the artifact: "This PR implements...", "This change ensures..."
- Changelog verbs with no reason: "Refactored X to improve Y"
- Lines that start with a filename, or a bullet list that restates the diff (unless that is the user's own format)
- The point arriving after the first sentence
