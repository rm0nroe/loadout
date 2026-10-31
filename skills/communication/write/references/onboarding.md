# Writing voice questionnaire

Build the user's own writing preferences through conversation. No author's persona, private examples, or historical ratings are bundled. This is optional setup; it is not a prerequisite for drafting.

## Start

Explain the outcome: a general `persona.md` and, where useful, channel profiles in `$GHOSTWRITER_HOME` (default `~/.config/ghostwriter`). They stay outside the repository. Answers and samples still enter the model conversation; ask users to redact sensitive material. Nothing is saved until they approve the proposed files.

Ask one question at a time, with short choices and a free-text option. Accept answers in any order, reuse what the user already supplied, and allow "skip", "not sure", or "finish here". Do not turn a skipped answer into a preference. Keep a short answered/remaining checklist in the conversation so setup can resume without repeating questions.

For an existing profile, read it first and ask what the user wants to refine. Check `voice --channel <channel>` for their selected channels and honor `$GHOSTWRITER_PERSONA` if set. Do not re-onboard someone merely because another channel has no profile.

## Shared questions

1. **Where do you write?** Which should we personalize first: Slack, email, PR descriptions, review comments, commits, release notes, postmortems, tickets, articles, or docs? Who usually reads them?
2. **Tone:** How should you sound to those readers: conversational, formal, direct, warm, or a mix? Does that change for colleagues, customers, or public readers?
3. **Length and detail:** Do you prefer a short answer first, context first, or a fuller explanation? When should the writer include technical detail or unpack unfamiliar terms?
4. **Structure:** Do you like paragraphs, bullets, headings, examples, links, or diagrams? Which formats or repository templates must be followed?
5. **Voice markers:** Any preferences for capitalization, contractions, greetings, closings, humor, emoji, punctuation, or phrases to avoid? Which are strict rules, and which depend on context?
6. **Disagreement and uncertainty:** When should feedback be a question, suggestion, or direct request? How should uncertainty, bad news, and acknowledgment sound?

Offer to move straight to a proposal after the shared questions, or ask the relevant channel questions below. Cover only the channels the user selected; don't require all ten.

## Channel questions

| Channel | Ask about |
|---|---|
| `slack` | Quick replies versus updates; how to open an ongoing conversation; bullets, mentions and acknowledgments. |
| `email` | Internal versus external tone; subject lines; when to state the ask; greetings, sign-offs and typical length. |
| `pr` | Title conventions; summary and body structure; test evidence; repository templates that take precedence. |
| `pr-comment` | Questions versus direct findings; severity and minor feedback; suggested fixes; brief approvals or replies. |
| `commit` | Repository conventions; subject style; when a body is useful; issue references. |
| `release-notes` | Audience; grouping changes; benefits versus technical details; breaking changes and required action. |
| `postmortem` | Summary, impact, timeline and causes; uncertainty; action items, owners and follow-up. |
| `ticket` | Problem and context; technical notes; acceptance criteria; links, blockers and how prescriptive to be. |
| `article` | Audience knowledge; opening style; narrative versus sections; examples, evidence and conclusions. |
| `docs` | Purpose and summary; navigation; explanations versus procedures; terminology, links and visuals. |

## Optional examples and calibration

Offer either route; neither is required to create a profile from explicit answers:

- **Their samples:** ask for 5-10 examples they wrote for the selected channel, with date and AI-assistance provenance (`yes`, `no`, `unknown`). Fewer are fine; describe the evidence as limited. Read only samples the user supplies or explicitly selects for setup, not unrelated files under `imports/` or `evals/`.
- **Paired drafts:** use one short synthetic scenario for a selected channel and show two alternatives with identical facts but different tone or structure. Ask which sounds closer, what they would edit, and whether either changes the meaning. Repeat only where a preference is still unclear and the user wants to continue. Label both drafts as generated examples; they never become samples of the user's own writing.

Keep direct answers, observed sample patterns and agent suggestions distinct. Never fill unanswered preferences or editing-effort ratings on the user's behalf. A preference inferred from examples remains a proposal until approved.

## Propose, approve, save

1. Summarize the agreed preferences and any unresolved questions. Explicit user instructions and repository requirements override general style preferences; factual preservation always applies.
2. Show the exact proposed content and destination for each file. Put shared preferences in `persona.md`; add `<channel>.md` only for channels with specific preferences. Each new channel profile must reference the shared persona's actual path, so those shared preferences are read even when `voice` selects a channel profile. Do not create `soul.md` just to duplicate the persona.
3. Mark the proposal's basis (interview answers, supplied samples, or approved comparison choices) and date. Leave unknown preferences out. The example below illustrates the shape only; never install it as the user's defaults.
4. Ask approval for the displayed content and paths. Answers to the questionnaire or a preference between two drafts are not approval to save. "Skip" means no writes; "finish here" means offer a proposal from the answers already given.
5. After approval, save only the approved files. Follow `voice.md` for preserving existing profiles. Resolve symlinks and custom persona paths before proposing changes, and include their actual targets in the approval. Do not replace a symlink or overwrite an external persona silently. If the configured location is inside a repository, propose a private location instead. Never put profiles, answers, samples or ratings into the skill package or commit them.
6. Run `python3 scripts/write_runner.py voice --channel <channel>` for each configured channel, confirm it resolves the intended files, and read back their contents. Report what was saved and which channels still use the general persona or editorial defaults. Offer one small trial draft; saving a profile alone does not establish that its voice matches the user.

### Example proposal (fictional, not a default)

```markdown
# Writing persona

Basis: interview answers, approved YYYY-MM-DD.

- Use a warm, professional tone for customer emails and a casual tone with teammates.
- Lead with the request, then give the context the reader needs.
- Prefer short paragraphs; use bullets for multiple actions.
- Keep greetings in external emails. Contractions are welcome.
- Avoid jokes in incident updates; retain uncertainty and factual detail.
```

A channel file can be as small as:

```markdown
# Email voice

Use `persona.md` beside this file for shared preferences.
For external emails, include a descriptive subject and a brief greeting.
```

These files guide the model's writing. `rules.json` is separate: only propose it for explicitly requested mechanical bans, show the exact patterns and their scope, and require approval. Do not turn a contextual style preference into a global regex ban.
