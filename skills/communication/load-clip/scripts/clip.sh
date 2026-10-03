#!/usr/bin/env bash
# Put a markdown file on the macOS clipboard as AppleScript HTML + RTF.
# Jira, Notes, and Docs paste this as native bold and bullets.
# Slack does not: use clip-slack.sh.
# Usage: clip.sh draft.md
set -e
[ -f "$1" ] || { echo "usage: clip.sh <markdown file>" >&2; exit 2; }
HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d /tmp/clip.XXXXXX)"
python3 "$HERE/md2html.py" < "$1" > "$T/s.html"
textutil -convert rtf -format html -output "$T/s.rtf" "$T/s.html"
osascript - "$T/s.html" "$T/s.rtf" <<'AS'
on run argv
  set h to read (POSIX file (item 1 of argv)) as «class HTML»
  set r to read (POSIX file (item 2 of argv)) as «class RTF »
  set the clipboard to {«class HTML»:h, «class RTF »:r}
end run
AS
rm -rf "$T"
echo "clipboard: jira/notes rich text from $1"
