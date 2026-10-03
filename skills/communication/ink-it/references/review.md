# Review

Review finds problems; it does not rewrite. It happens twice: on the candidate before `finalize`, and on the exact final text after `finalize` whenever it changed bytes.

## Before finalize: every draft, three axes

1. **Meaning.** Check each required claim from the claims list against the draft. Nothing added, nothing dropped, no hedge hardened ("may" stays "may"), no open question closed, no commitment the user didn't make.
2. **Clarity.** Does the point land in the first sentence? Would the named reader know what to do next?
3. **Voice.** Compare against the approved profile or fallback, using this channel's card only (Slack, email, PR comment: its card plus `tells.md`; PR title/body: `pr.md`; commit: `commit.md`; release notes, postmortem, ticket, article, docs: `professional.md` checklist plus its document card).

Record each finding as place, problem, fix. No findings: the draft goes to `finalize` unchanged.

## Complex or consequential drafts: independent review

Use an independent reviewer when the message carries bad news, a decline, a commitment, money, security, or an external or upward reader; when the PR or commit touches migrations, billing, auth, permissions or irreversible writes; when an email goes to an external or upward reader; for any postmortem, and any article, doc or release note that will be published; or when the source is long enough that a claim could slip.

Give the reviewer only:

- the user's original request,
- the source and context files and `spans.json`,
- the required claims, uncertainty, commitments and missing-information list,
- voice examples (approved profile excerpts or the fallback),
- the candidate draft.

Never pass your reasoning, earlier candidates or your opinion of the draft. In Claude Code, spawn a fresh subagent with that packet. Where no subagent is available, start a fresh pass that reads only those files, and say in the delivery line that review was same-session.

Ask for findings only, each tagged meaning, clarity or voice, with place, problem and fix. An empty list means the draft is clean.

## After finalize: meaning recheck on the delivered bytes

When the report says `recheck_meaning: true`, `finalize` restored a span or stripped attribution. Read `final.md`, not the candidate, and recheck meaning against the claims list. A restored quote can change a sentence's sense, and a stripped credit can leave a dangling clause. Any problem is a finding: fix it in a new candidate and run `finalize` again, within the shared two-round budget. Deliver only after a `finalize` pass whose output you have rechecked, or whose report says `recheck_meaning: false`.

## Applying findings

- Targeted edits only, for the findings named.
- Each revision is a new `candidate-N.md`, with the round number passed to `finalize --round N`.
- Two revision rounds total, shared with lint repairs and post-finalize rechecks. After that, deliver the last verified draft or report what is still open.
- Deliver `final.md` as-is. No extra rewrite, no humanizer pass.
