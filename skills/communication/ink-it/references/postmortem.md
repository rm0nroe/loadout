# Postmortem card (Sepia rules)

Adapted from Sepia's postmortem domain (see `../PROVENANCE.md`). Read `professional.md` first, including its outline check. Covers incident reports, outage retrospectives and RCA documents. It writes text only; the user files or posts it. A postmortem is consequential: use independent review (`review.md`).

## Baseline

Blameless toward people, exact about mechanisms. A real postmortem has absolute timestamps, the failure mechanics (the query, the config line, the race window), honest dead ends and action items someone owns. The team's incident template is a fine container; the defect is filler inside it.

## Gather facts (read-only)

Timeline data, alerts, logs, the diff or config that changed, impact counts (duration, failed requests, users, money if known), the owners and dates for action items. Everything comes from the incident data the user supplies. The mechanism you do not know is a question for the team, not a gap to write over.

## Rules

1. Timeline with absolute times and timezone, including the wrong turns. The 40 minutes on the bad hypothesis is the most instructive part; keep it if the user supplied it, never invent one.
2. The failure mechanism at code or config level: the exact query, flag, limit or race. Unknown means marked unknown.
3. Contributing factors as a causal chain, each saying what it enabled. No bullet cloud.
4. Impact in numbers first, narrative second. Real durations and counts from the data, never estimated to sound complete.
5. Counterfactuals stated honestly: what would have caught it and why it did not exist. No "the system worked as designed".
6. Blameless is not agentless. Name systems and roles ("the deploy pipeline promoted the config before validation ran"), not "mistakes were made".
7. An action item is a change with an owner and a date, from the user's data. Generic lessons ("improve monitoring and communication") are filler; without owners or dates, leave `[TODO: owner]` rather than invent them.
8. Commit to the causal chain the evidence supports and mark the unknown part unknown. A hedged "a combination of factors may have contributed" fails. So does a postmortem that admits no wrong judgment anywhere, when the record shows one.
9. Sections earn their length; a section with nothing to say gets one honest line or is dropped. No self-praise adverbs ("swiftly"), no moralizing close. End at the action items.
