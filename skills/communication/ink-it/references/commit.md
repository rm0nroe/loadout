# Commit message card (repository conventions)

There is no universal commit style. The convention comes from the repository's own evidence and the user's explicit instructions; this card only says how to find it and what to produce. A commit message is text. This card never runs `git commit`, `git push`, amend or rebase; hand the message back and the user commits.

## Precedence

1. The user's explicit instructions for this commit.
2. The repository's stated rules: `commitlint` config, `CONTRIBUTING`, a `.gitmessage` template, a PR-title lint workflow under `.github/workflows/`.
3. The repository's actual history: the recent subjects and bodies on the branch and on the base.
4. The approved voice profile (`commit.md`, then `soul.md`, then the persona fallback), for wording only.
5. The defaults below.

## Gather facts (read-only)

- The change: `git diff --staged` for staged work, or the diff or commit the user names. Never guess at files that are not in it.
- The convention: `git log -n 30 --format='%s%n%b---'` on the current branch. Note the subject shape (`type(scope): action`, ticket prefix, plain sentence), case, tense, trailing period, typical body, trailer use, and the longest subject.
- The stated rules above. If the rules and the history disagree, follow the rules and say so in the delivery line.
- The reason: the branch name, ticket, user prompt and diff. If the why is not in any of them, leave it out.
- Ticket ID from the branch, prompt or history. Never guess one.

## Output format

Line 1 is the subject, then one blank line, then the body if there is one. No `Subject:` prefix, no fences inside the message. Trailers (`Fixes: #12`, human `Co-authored-by:`) go last, one per line, only when the user or the repo convention calls for them.

If the repo states a subject length limit, pass it as `finalize --subject-max <n>`. Never invent one.

## Subject

- Match the repo's shape exactly: same type vocabulary, scope naming, case and punctuation as its recent subjects.
- Imperative or whatever tense the history uses. Say what the commit does, not that it exists.
- With no repo evidence: a short plain imperative subject, no type prefix, no trailing period.

## Body

- Body only when the why is not obvious from the subject and diff. A one-line commit is normal.
- What and why, in the reason's own terms. The diff already says which files changed.
- No fake why. No test result unless it ran.
- Wrap only if the history wraps.
- One logical change per message. A diff mixing unrelated changes gets a one-line note to the user that it may want splitting; never split it yourself.

## Anti-patterns

- Narrating the artifact: "This commit adds...", "Updated files to improve..."
- A body that restates the diff line by line.
- A type or scope the repo never uses.
- Any footer that names a tool. The runner strips AI attribution and session links from the message.
