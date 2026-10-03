# Worked example: review findings relayed to a plan's author

Context: the user asked for an adversarial review of an implementation plan written by a teammate, then asked for the results as a message they would relay. The teammate was not in the conversation. A late instruction changed the ask: make the document edits, but do not start work.

The message is reproduced below in condensed form, with annotations explaining why each part is shaped the way it is. Annotations are marked `>>`.

---

**To: PLAN-42 plan author**
**From: Claude (via Alex)**
**Re: Pre-implementation review results and required updates. Do not start work yet.**

>> The Re line carries the ask AND the boundary. A reader who reads nothing else still knows to hold. From: names both the author and the carrier, so the reader knows who to reply to and that the sender did not write it personally.

---

## Read this part first

Adversarial pass is done. Result: **the spec revision is good, the plan's task body was never swept to match it.**

>> The one-sentence diagnosis, in the first two lines, in bold. The reader can repeat this sentence to someone else. Everything after it is elaboration.

**What I am asking you to do: make the document edits below. Nothing else.**

**What I am asking you NOT to do, explicitly:**
- Do not start Task 0a. Do not stand up the webhook replay rig.
- Do not start Task 0b. Do not run the load spike, do not add `ioredis` anywhere.
- Do not start Task 1 or touch anything under `services/billing`.
- Do not commit or push.

>> The non-asks are enumerated, not implied. Note they are specific to plausible misreadings: this reader's most likely error is starting the phase the review just approved in principle. A generic "don't start yet" would not have closed that. Named items beat a general prohibition because the reader checks their intent against a list.

Alex wants the plan corrected and then held. Edits only, then stop and report back.

>> Attributes the decision to the person with authority. The reader needs to know this is the owner's call, not the reviewer's opinion, or they will negotiate.

Full detail: `docs/plans/PLAN-42/review/2026-09-01-SIGNOFF...md`. Everything below is verified against `origin/main` = `HEAD` = `3f9c2a1`, zero drift, so the line numbers are current.

>> Points at the durable artifact, and pre-empts the reader's first objection ("are these line numbers stale?") before they raise it.

---

## Credit where it is due

These are closed and I could not break them:

- **B4.** `npm install ioredis` correctly moved to Task 3 Step 4 (`plan:1128`), after the go/no-go. The committed contract test no longer asserts Redis key names, so the test lock-in that would have made an in-database verdict expensive is gone. That was the single best fix in the revision.
- **The schema change.** Substantially complete. All 6 migration steps, both index pairs, all 8 error codes in both API versions, the exact `Retry-After` value. The integration helper reads timestamps from the fixture clock rather than hardcoded values, so it survived the timezone change for free.

>> Specific enough that only someone who actually read the work could write it, and it cites lines the same way the criticism does. "I could not break them" signals the credit came from a real attempt to find fault, which is what makes it worth something. Naming a single best fix costs one clause and buys a lot of goodwill.

---

## Prior findings: where they stand

| ID | Status | Evidence |
|---|---|---|
| B1, B4, B5 | Closed | above |
| B2 | Partial | spec fixed at `spec:280`; step unchanged at `plan:2025` |
| M4 | Open | `releaseIdempotencyKey`: zero hits across 2,832 plan lines |

>> A table because the reader's real question is "which of my fixes actually landed", and that is a lookup, not a narrative. Partial is its own status: collapsing it into open or closed would misrepresent the work done.

---

## Three blockers

**BL-1. `markProcessed` still gets the retry term.** `plan:1951-1955` defines `shouldSkip` including `isRetry`; `plan:2025` passes it to the global dedupe guard. This contradicts your own `plan:34`. The guard is total: `WebhookRouter.ts:48-52` acknowledges the event and drops the payload. Nothing catches it: `webhook-dedupe.test.ts:135-144` retries without changing the payload.

>> Every sentence carries a citation. "Contradicts your own plan:34" is the strongest possible framing: the reader already agreed with the fix, they just did not propagate it, so there is nothing to argue about. Ending with why no test catches it answers the reader's next question before they ask it.

---

## Eight majors

6. **Task 4 has no reachable GREEN.** `plan:1715` requires `status` before `id` in the serialized event. I ran the repo's own serializer: output is `{"id":"evt_1","status":"paid","amount":1200}`. It always emits `id` first. Fix the assertion, do not reorder the fields to satisfy it.

>> "I ran it" plus the literal output. This claim would have cost the reader an hour to chase if wrong, so it was verified before sending. The trailing instruction blocks the tempting wrong fix, which is the kind of thing you can only add if you thought about what the reader will try first.

---

## Edits to make now

### Group A: four edits, roughly 20 minutes
1. Add Task 1 Step 0 after `plan:157`: three commands asserting both Phase 0 artifacts exist.
2. Make Task 0a executable. Note that **the repo's `queue-emulator` script has no `--replay` flag**.
...

### Group B: the Task 1-8 rewrite
Verbatim code for each is in the saved sign-off doc, section 7B. Summary: ...

>> Grouped by when, with an effort estimate on the near group. "Four edits, roughly 20 minutes" converts an intimidating list into something startable today. Group B summarizes and points at the artifact rather than inlining 17 code blocks, keeping the message readable.

---

## The structural change that matters most

`plan:146` scopes the revision to "candidate-specific code, constants, geometry, and tests with measured values." That wording covers the measurement items and nothing else, which is precisely why eight findings survived this revision untouched. Replace it with an explicit numbered debt checklist naming each open finding by ID. Otherwise the next revision loses them the same way.

>> The root cause, separated from the item list. Fixing the eight findings without this leaves the mechanism that produced them intact. This is usually the most valuable paragraph in the message and it is easy to bury inside the item list, where it reads as item nine.

---

## When you are done

Report back with the diff summary. Do not start Task 0a, Task 0b, or Task 1. Alex will give the go separately.

>> One action, then the boundary restated. The close and the open are the two places people actually read, so the hold appears in both.

---

## What this example does not show

The structure above suits a substantial review with a hold instruction. Most relay messages are far smaller. A three-line message with a header, one ask, and one citation is a correct relay message when the ask is small. The spine scales down; the ordering (boundary first, one action last) is what stays fixed.
