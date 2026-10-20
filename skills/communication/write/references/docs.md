# Docs card (local, on the professional pass)

Sepia has no docs domain, so this card is written locally on `professional.md` (see `../PROVENANCE.md`); its article rules for numbers, code and sourcing apply. Read `professional.md` first, including its outline check for long pages. Covers documentation pages, READMEs, guides, API and runbook text. It writes text only; the user commits it.

## Baseline

The reader has a task and wants the shortest correct path to it. Docs are read by scanning, so structure earns its place here more than in an article. The repo's own docs (heading style, tone, how commands and warnings are shown) are the venue: read 2 or 3 neighboring pages and match them.

## Gather facts (read-only)

The code or config being documented, real commands and their real output, versions, defaults, and the neighboring docs. Read the code before describing behavior. Never document a flag, default or return value you did not see.

## Rules

1. Start with what the reader can do or must know, in the first lines. No history or marketing before the task.
2. Commands and code blocks are copy-pasteable, complete and real, with the version they apply to. A sketch is labeled as one. Keep them byte-exact; the runner protects them.
3. Say what the reader will see when a step worked, using the real output, when that output is known.
4. Warnings and prerequisites go before the step they guard, not after.
5. Distinguish "must", "should" and "may" only where the code or the user supports the distinction. An unknown default is a `[TODO: verify]`, not a guess.
6. Reference material (parameters, options, errors) is a table or list; explanation is prose. Do not mix them in one paragraph.
7. Do not restate the heading in the first sentence, and do not add a summary that repeats the page.
8. Uncertainty and known limits stay visible: "not supported on Windows" is documentation; silence is a bug report waiting to happen. An open question in the notes ("should X become the default? not decided") stays on the page as an open question or a `[TODO: ...]`; never drop it.
9. Follow the repo's docs conventions for headings, links and callouts over this card's defaults.
