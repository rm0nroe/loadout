---
name: readme-banner
description: Design a memorable hero banner for a repository README as one self-contained SVG, with the wordmark converted to font outlines so it renders identically on GitHub, in dark and light themes, on every machine. Use whenever the user wants a README banner, header image, hero, or logo strip for a repo, is preparing to open-source or publish a repository, says "add a banner to the readme", or complains an existing README banner looks generic. Prefer this over general image or social-banner skills for anything that lives at the top of a README.
---

# README Banner

Produces `assets/banner.svg` (plus the font's license file) and wires it into the top of `README.md`. The worked example is this repository's own banner, `assets/example-loadout.svg`.

First drafts of README banners tend to land on the same thing: a dark card with monospace text and feature chips. It says "developer tool" and nobody remembers it. The banners that work turn the project's *name* into a picture. Most of this skill is about getting there on the first try.

## Workflow

### 1. Collect real facts (5 min)

Read the README, repo description, and main entry points. Note what the project literally does, its commands or surfaces, and any **real** numbers: counts from a run, file totals, supported platforms. Banner annotations use only these. A made-up "10x faster" erodes trust in an open-source repo, while a real measured number reads as confident.

### 2. Concept from the name, not the feature list (the step that matters)

Ask what the project's name literally means or evokes, then draw that. loadout is a kit you pack, and its skill names are inspired by Resident Evil, so its banner became a survival-horror attaché case: LOADOUT stenciled in blood on a stitched leather lid, and each skill a typed case file inside. The product idea lives inside the metaphor instead of being listed beside it.

Write three distinct concepts in one line each and pick the strongest. Reject any concept that comes down to "dark card + monospace + feature chips" or "gradient + logo + tagline". Those are the defaults every repo already has. If a concept could swap in another project's name without changing anything, it is not a concept yet.

If design or art-direction skills are installed, they can push the concept further. The output stays a vector SVG either way.

### 3. Palette and type

- **Background:** dark, so one file reads on both GitHub themes. Swapping files per theme with `<picture>` doubles the maintenance for little gain.
- **Colors:** three to five, derived from the concept (loadout: `#090707` night, `#B3141B` blood, `#C9A15B` brass, leather browns `#3A2618` to `#24170F`). Don't default to purple gradients.
- **Wordmark face:** a display font under SIL OFL 1.1 from `github.com/google/fonts/tree/main/ofl/`. Download the TTF and `OFL.txt` together:
  ```bash
  curl -sSfLO https://raw.githubusercontent.com/google/fonts/main/ofl/<family>/<File>-Regular.ttf
  curl -sSfLO https://raw.githubusercontent.com/google/fonts/main/ofl/<family>/OFL.txt
  ```
  Don't convert a system font like Impact or Helvetica. Outlining a short wordmark is common practice, but a public repo has no reason to leave the licensing question open.
- **Secondary text** (eyebrow, tagline, labels) can stay as `<text>` with a system stack like `'Helvetica Neue', Helvetica, 'Segoe UI', sans-serif`. Small text falls back gracefully; a wordmark does not.

### 4. Wordmark to outlines

```bash
uv run <skill-dir>/scripts/wordmark.py SairaStencilOne-Regular.ttf "LOADOUT" \
  --width 760 --x 92 --baseline 200 --fill "url(#blood)" --tracking 40
```

This prints one `<g transform="translate(..) scale(..)"><path/></g>` to paste in. Metrics go to stderr; use `top y` to place eyebrow lines above the mark. The scale is derived from `--width`, so changing fonts never needs hand-tuned numbers. `--tracking` adds letter spacing in font units, and `--fill` takes a color or a gradient reference.

Why outlines: GitHub renders README SVGs as images with no access to web fonts, and viewers miss local fonts. A `<text>` wordmark in a font stack falls back to some other face, which changes its width. `textLength` doesn't save it because librsvg ignores it.

If `uv` panics with `system-configuration ... NULL object` inside a sandbox, rerun outside the sandbox. It is uv's proxy lookup, not the script.

### 5. Compose the SVG

Canvas `viewBox="0 0 1600 520"`. Start from `assets/example-loadout.svg` for structure. Requirements, each with the reason it exists:

- `role="img"`, an `aria-label`, `<title>`, and a `<desc>` that states the concept, for screen readers.
- A comment naming the font and its license file, so the license travels with the art.
- Only plain geometry: `rect`, `line`, `path`, `circle`, `pattern`, `clipPath`, `mask`, gradients. No `filter` (rendering varies across viewers), no `<image>`, raster, `<foreignObject>`, `@import`, or external `href`. GitHub's image proxy drops external resources.
- Reuse one wordmark path under two `clipPath`s for split or cut effects instead of drawing it twice.
- Keep it diffable and small, ideally under 30 KB.
- Size every container from the text it holds (a card or capsule from its label, a plate from its longest row), never by eye. Fixed sizes are where overflows come from.
- For repeated elements (one card or slot per item), generate the SVG with a throwaway script rather than writing it by hand. Don't commit the script.

### 6. Render and actually look (iterate here)

```bash
rsvg-convert -w 1600 assets/banner.svg -o "$TMPDIR/banner.png"
rsvg-convert -w 420  assets/banner.svg -o "$TMPDIR/banner-phone.png"
```

Read both PNGs. Judge honestly:
- Does the wordmark sit inside the canvas, with nothing overflowing or clipped by accident?
- Does the concept read at phone width?
- Would a stranger remember it?

Fix and re-render until the answers are yes. rsvg is stricter than browsers, so passing here is a good proxy for GitHub.

**Theme from the project's own culture.** If the project's names come from somewhere, ask whether the banner should carry it. Subtle nods don't register; use the source's palette and two or three iconic, non-trademarked motifs (loadout uses a biohazard trefoil, a heart monitor reading FINE, typed case files). Never use logos, title text or copied art.

**When the user is unsure, show variants side by side.** Put them on one comparison page (each SVG as a base64 `<img>` so ids can't collide) with the current favorite on top for reference. Make the variants genuinely different: different concept, typeface and palette, as if from different designers. Save each favorite outside the repo before the next round, and delete them once the chosen banner is committed: the commit is the record.

### 7. Wire it in

Add this at the very top of `README.md`:
```html
<p align="center">
  <img src="assets/banner.svg" alt="<Name>: <one-line description>" width="100%">
</p>
```
Commit `assets/banner.svg`, `assets/<FONT>-OFL.txt`, and the README together, following the repo's own commit conventions. The commit body is a good place for the concept rationale, so the design can be recovered later. Don't commit the TTF or any build scripts, since the outlines are the artifact. Confirm with the user before committing or pushing.

## Done when

- `assets/banner.svg` renders cleanly in rsvg at 1600 and 420 px.
- Only real facts appear on it, and the wordmark has no `<text>`.
- The license file sits beside it, and the README shows it at the top.
