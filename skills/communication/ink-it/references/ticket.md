# Ticket card (Sepia rules)

Adapted from Sepia's tickets domain (see `../PROVENANCE.md`). Read `professional.md` first. Covers issue tickets, tasks, work orders and bug reports the user files (a reply on someone else's issue is a PR comment, not this). It writes text only; the user files it in the tracker.

## Baseline

Imperative, minimal, complete enough that the assignee can start without a question and knows when they are done. The tracker's field template is a container, not a tell.

## Gather facts (read-only)

Versions, commands, inputs, pasted real output, frequency, related ticket ids, the design doc or alert to link. Never guess an id or an estimate.

## Output

Line 1 is the ticket title, then one blank line, then the description. No `Title:` prefix. If the tracker has fields, keep its headings and answer each in a sentence or leave it empty.

## Rules

1. Title is the outcome, not the activity ("Retry queue drops jobs on redeploy", not "Investigate queue issue").
2. The description starts where the title stops; it never restates it.
3. Bug: exact repro (versions, commands, input), expected versus actual with the real output pasted, and frequency. If it was not reproduced, say what was tried.
4. Acceptance criteria are testable or they are not criteria: the command and the output that means done. Vague ("works correctly") is a defect. But criteria, thresholds, scope boundaries, repro steps and investigation plans come only from what the user gave. When none were supplied, write `[TODO: acceptance]` or leave the field empty; never invent a command, exit code, threshold, "only" boundary or first step to make a ticket look complete.
5. Scope is a concrete boundary: which files or functions are in, which are explicitly out. No "refactor the module" or "clean up".
6. Context is only what the assignee does not already know. Link prior tickets, docs and alerts; do not repeat them.
7. Empty is a valid field value; "N/A" beats a paragraph of nothing. Priority and estimate are bare, with no justification paragraph, and only if the user gave them.
8. Do not enumerate obvious steps; give the non-obvious ones and the exact commands.
9. Keep every supplied value exactly as given, including anything that looks like a key or token. Never redact or reword it; if it looks sensitive, say so in the delivery line and let the user decide.
