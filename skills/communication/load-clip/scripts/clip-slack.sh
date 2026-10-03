#!/usr/bin/env bash
# Slack clipboard. Electron ignores clip.sh's AppleScript «class HTML».
# Writes an NSAttributedString (same as copying from TextEdit) so Slack
# gets public.rtf plus a plain-text fallback. Do not use clip.sh here.
# Usage: clip-slack.sh draft.md
set -e
[ -f "$1" ] || { echo "usage: clip-slack.sh <markdown file>" >&2; exit 2; }
HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d /tmp/clip-slack.XXXXXX)"
trap 'rm -rf "$T"' EXIT
python3 "$HERE/md2html.py" < "$1" > "$T/s.html"
textutil -convert rtf -format html -output "$T/s.rtf" "$T/s.html"
osascript -l JavaScript - "$T/s.html" "$T/s.rtf" <<'JS'
ObjC.import("AppKit")
ObjC.import("Foundation")
function run(argv) {
  var html = $.NSData.alloc.initWithContentsOfFile(argv[0])
  var rtf = $.NSData.alloc.initWithContentsOfFile(argv[1])
  var attr = $.NSAttributedString.alloc.initWithRTFDocumentAttributes(rtf, null)
  var pb = $.NSPasteboard.generalPasteboard
  pb.clearContents
  pb.writeObjects($.NSArray.arrayWithObject(attr))
  pb.setDataForType(html, $.NSPasteboardTypeHTML)
  pb.setDataForType(rtf, $.NSPasteboardTypeRTF)
}
JS
echo "clipboard: slack rich text from $1"
