#!/usr/bin/env python3
"""Tiny GFM subset -> HTML: headings, bold, inline code, nested bullets, paragraphs.
No pandoc dependency; this covers exactly the subset SKILL.md allows."""
import html
import re
import sys


def inline(s):
    s = html.escape(s)  # quote=True: a " in a URL must not end the href attribute
    # pull inline code out first so bold/link syntax inside it stays literal
    codes = re.findall(r"`([^`]+)`", s)
    s = re.sub(r"`[^`]+`", "\0", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    # [text](url) -> anchor with custom text, so Jira pastes an inline link instead of a smart-link card.
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    for c in codes:
        s = s.replace("\0", f"<code>{c}</code>", 1)
    # Slack's RTF importer drops the font/bold reset when a run is empty, so a line
    # ending in </code> or </b> bleeds that style into the next paragraph. Pad it.
    if s.endswith(("</code>", "</b>")):
        s += "&nbsp;"
    return s


out = []
depth = 0


def close_to(n):
    global depth
    while depth > n:
        out.append("</li></ul>")
        depth -= 1


fence = None  # lines inside a ``` block
for line in sys.stdin.read().splitlines():
    if line.startswith("```"):
        if fence is None:
            close_to(0)
            fence = []
        else:
            out.append("<pre><code>" + html.escape("\n".join(fence), quote=False) + "</code></pre>")
            fence = None
        continue
    if fence is not None:
        fence.append(line)
        continue
    m = re.match(r"^( *)- (.*)$", line)
    if m:
        d = len(m.group(1)) // 2 + 1
        if d > depth:
            while depth < d:
                out.append("<ul><li>")
                depth += 1
            out[-1] += inline(m.group(2))
            continue
        close_to(d)
        out.append("</li><li>" + inline(m.group(2)))
        continue
    close_to(0)
    h = re.match(r"^(#+) (.*)$", line)
    if h:
        n = len(h.group(1))
        out.append(f"<h{n}>{inline(h.group(2))}</h{n}>")
    elif line.strip():
        out.append(f"<p>{inline(line)}</p>")
    else:
        out.append("<p>&nbsp;</p>")  # blank md line -> visible blank line; Slack collapses <p> margins
close_to(0)
if fence is not None:  # unclosed fence: keep its content rather than drop it
    out.append("<pre><code>" + html.escape("\n".join(fence), quote=False) + "</code></pre>")
print("<html><head><meta charset=\"utf-8\"></head><body>" + "\n".join(out) + "</body></html>")
