# Release notes card (Sepia rules)

Adapted from Sepia's release-notes domain (see `../PROVENANCE.md`). Read `professional.md` first. Covers changelogs, GitHub Releases, version announcements and short launch posts. It writes text only; the user publishes the release.

## Baseline

Terse, factual, user-impact-first. The reader is deciding whether to upgrade and what will break. The repo's own changelog format (Keep a Changelog categories, or its habit) is expected, not a tell; read 2 or 3 past entries and follow them.

## Gather facts (read-only)

The commit or PR range for this release, the version string and date the user gave, issue and PR numbers, breaking changes, benchmark numbers with their conditions. Never guess a version or date.

## Output

Whatever the repo's format is. With none: version and date on the first line, then breaking changes, then the rest ordered by user impact. No preamble about the journey, no closing about the road ahead.

## Rules

1. Breaking changes first, each with the exact migration step (the command, the config key, the renamed flag).
2. Every claim carries its artifact: issue or PR number, commit range, exact version string, a real number with its conditions. No artifact, no claim. "Improved performance" becomes the number or the change itself.
3. One line per change, verb first, no adjectives. Order by impact, not symmetry: breaking first, one-word fixes last.
4. Credit people plainly ("thanks @name for #398"). No gratitude paragraph.
5. Length follows the release. A patch release is a few lines; never inflate it.
6. No marketing inflation ("thrilled to announce", "powerful", "seamless", "supercharge"), no emoji headers or exclamation marks unless the repo's history has them. Never inject humor into a repo that has none.
7. A `Full Changelog` compare link is the user's; include it only when supplied.
