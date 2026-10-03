# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools"]
# ///
"""Convert a wordmark to SVG outlines so it renders identically everywhere.

    uv run wordmark.py FONT.ttf "Groundwork" --width 1053 --x 92 --baseline 366 --fill "#EDE6DA"

Prints one <g transform="translate(x baseline) scale(s)"><path .../></g> to stdout,
ready to paste into the banner. Metrics go to stderr. Paths stay in font units with
y flipped; the group's scale maps them to pixels, so the scale is derived from the
target width instead of guessed.
"""
import argparse
import sys

from fontTools.misc.transform import Transform
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("font")
    p.add_argument("text")
    p.add_argument("--width", type=float, required=True, help="target wordmark width in px")
    p.add_argument("--x", type=float, default=0, help="left edge in px")
    p.add_argument("--baseline", type=float, default=0, help="baseline y in px")
    p.add_argument("--fill", default="#FFFFFF")
    p.add_argument("--tracking", type=float, default=0, help="extra space per glyph, font units")
    a = p.parse_args()

    font = TTFont(a.font)
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")

    # ponytail: no GPOS kerning; fine for display caps/tight faces, add a kern pass if pairs look loose
    x = 0.0
    for ch in a.text:
        if ord(ch) not in cmap:
            sys.exit(f"glyph for {ch!r} missing from {a.font}")
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, Transform(1, 0, 0, -1, x, 0)))
        x += hmtx[name][0] + a.tracking
    advance = x - a.tracking

    scale = a.width / advance
    upm = font["head"].unitsPerEm
    cap = getattr(font.get("OS/2"), "sCapHeight", 0) or 0
    print(
        f"upm {upm}  advance {advance:.0f}  scale {scale:.5f}  "
        f"cap height {cap * scale:.1f}px  top y {a.baseline - cap * scale:.1f}",
        file=sys.stderr,
    )
    print(
        f'<g transform="translate({a.x} {a.baseline}) scale({scale})">'
        f'<path d="{pen.getCommands()}" fill="{a.fill}"/></g>'
    )


if __name__ == "__main__":
    main()
