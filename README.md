<p align="center">
  <img src="assets/banner.svg" alt="Loadout: three field kits of agent skills for Claude Code and Codex, built for the task" width="100%">
</p>

# loadout

Agent skills I use every day, cleaned up for other people. Small on purpose: each one does one job and was kept because it kept earning its place.

Works in Claude Code and Codex, and in other runtimes that read `SKILL.md`. `clip` needs macOS, and in Codex it needs approval to run outside the sandbox.

## Install

```bash
claude plugin marketplace add rm0nroe/loadout
claude plugin install rm0nroe-loadout@rm0nroe
```

Or install them as plain skill files for Claude Code, Codex and other agents with [skills.sh](https://skills.sh), picking the ones you want:

```bash
npx skills@latest add rm0nroe/loadout
```

Plugins from this marketplace don't auto-update by default. Turn it on in `/plugin` (Marketplaces tab, select `rm0nroe`, Enable auto-update), or update by hand with `claude plugin update rm0nroe-loadout@rm0nroe`. Copied skill files are yours to edit, and `npx skills update` pulls new versions. Pick one way: installing both leaves you with every skill twice.

Or copy a single skill folder into `~/.claude/skills/` for Claude Code or `~/.codex/skills/` for Codex.

Then, in any Claude Code session:

```
/rm0nroe-loadout:draft a Slack message: the deploy slipped to Friday
```

Installed as a plugin, skills are namespaced (`/rm0nroe-loadout:<skill>`). Copied into `~/.claude/skills/`, they run as `/<skill>`. Most also trigger on plain requests ("draft a PR description", "explain that simply").

In Codex, invoke a copied skill as `$draft`, `$relay`, or `$checkpoint-load`. Start a fresh session after updating installed skills so the new names are discovered.

## Renamed skills

After updating, use these names. The old commands and skill paths have no compatibility aliases.

For copied installations, remove the old Loadout folders listed below and install the matching new folders. Keep any separately installed Groundwork checkpoint skills. For Claude plugins, if updating still shows the old names, uninstall and reinstall `rm0nroe-loadout@rm0nroe`, then restart Claude Code.

| Previous name | New name |
|---|---|
| `ink-it` | `draft` |
| `intel-brief` | `relay` |
| `load-clip` | `clip` |
| `paint-it` | `simplify` |
| `prune-docs` | `docs-prune` |
| `pull-file` | `checkpoint-load` |
| `typewrite` | `checkpoint-save` |
| `file-cabinet` | `checkpoint-list` |

## Requirements

- `draft`: Python 3.9+ (standard library only). Voice profiles are optional and live in `~/.config/ghostwriter/` (override with `$GHOSTWRITER_HOME`), never in this repo.
- `clip`: macOS (`osascript`, `textutil`) and Python 3.
- `checkpoint-load`: sealed Send It checkpoints require Git, Python 3, and Groundwork's installed runtime; ordinary checkpoints need no extra tools.
- `exec-recap`: `git`, and the [GitHub CLI](https://cli.github.com/) (`gh`) for release lists and notes.
- `docs-prune`: classifying docs needs nothing extra. Writing `.graphifyignore` and rebuilding or verifying the graph needs [graphify](https://pypi.org/project/graphifyy/) (`uv tool install graphifyy`).
- `readme-banner`: [uv](https://docs.astral.sh/uv/) (runs the outline script and fetches `fonttools` itself) and `rsvg-convert` from librsvg (`brew install librsvg`) for render checks.
- Everything else: a runtime that reads `SKILL.md`.

## Communication

- **draft**: drafts Slack messages, emails, PR titles and bodies, review comments, commits, release notes, postmortems, tickets, articles and docs in your own voice. Keeps facts, code, identifiers and URLs byte-exact. Drafting only, never sends.
- **relay**: writes a message for someone who was not in the conversation, so you can forward it as a handoff.
- **break-it-down**: rewrites the last reply as a direct explanation. Blunt point, numbered facts, the mix-up named, one rule. No metaphors.
- **simplify**: explains the last reply with one everyday analogy and numbered roles.
- **clip**: puts formatted text on the clipboard so bold, bullets and links survive a paste into Slack or Jira. macOS only.
- **exec-recap**: turns a version range, a date range ("last two days") or a commit range into a one-screen, plain-language recap for executives who have never seen the project. Every line traces back to a release note, PR or commit.

## Sessions

Save where you are, clear context, pick up later. Ordinary state files live in `~/.claude_states/<repo-name>/`, outside every repo. Groundwork sealed checkpoints stay in the current worktree's Git directory.

- **checkpoint-save**: saves session progress to a named state file.
- **checkpoint-load**: loads a saved state file back into a fresh session. `sendit-<run-uuid>` reads a sealed Groundwork checkpoint through its installed runtime; validation failure blocks loading and never restarts work.
- **checkpoint-list**: lists the saved state files for the current project.

## Engineering

- **roundtable**: four parallel agents (product, tech lead, devil's advocate, QA) argue a decision against your actual code, then the positions are tallied into a consensus and an action plan.
- **slop-radar**: audits a screenshot, URL or source tree for generic, AI-template design choices.
- **docs-prune**: finds stale docs so code indexers and knowledge graphs only see live content.
- **readme-banner**: designs a README hero banner as one self-contained SVG, wordmark converted to font outlines so it renders the same on every machine. Made this repo's banner.

## License

MIT. `draft` includes third-party material under MIT; see its `THIRD_PARTY_NOTICES.md`.
