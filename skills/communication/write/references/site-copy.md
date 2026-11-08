# Site copy card (local, on the professional pass)

Sepia has no product-copy domain, so this card is written locally on `professional.md` (see `../PROVENANCE.md`); its rules for facts, numbers and sourcing apply. Read `professional.md` first, but skip its outline check: site copy is never long enough. Covers text a product or site shows its readers: labels, buttons, headings, empty and error states, tooltips, and short generated blurbs such as a card's summary or caveat. It writes text only; the user ships it.

## Baseline

The reader is looking at a screen and wants to know what this is, what it means, and what to do. Copy sits next to numbers, badges and controls that already say part of that, so every word has to add something the screen does not. The product's existing strings are the venue: read the neighboring labels and blurbs and match their grammar, case and length.

## Gather facts (read-only)

The rendered page or component around the string, the data the string describes, the product's existing strings for the same kind of element, and any fixed labels the product requires verbatim. Never describe a value, status or behavior you did not see in the data or code.

## Rules

1. Say the point first. A blurb leads with the claim the reader needs; a label names the thing; an empty state says what is missing and, when there is one, the next step.
2. Buttons and links are a verb first, in the imperative, with no "please" and no ending punctuation. Name the outcome ("Load in lab", "Read the case"), not the mechanism ("Click here", "Submit").
3. Never repeat what the surrounding UI already shows. If the card displays the price, the blurb does not restate it; it says what the price means or why it matters.
4. Numbers are exact and sourced from the data. No rounding, no invented figures, and no number at all when the data has none: say the value is missing.
5. Required labels the product defines (legal text, status labels, outcome names) are copied byte for byte. Wrap them in `[[keep]]...[[/keep]]` in the source so the runner protects them.
6. Claims stay as strong as the evidence and no stronger. A probability is not a promise, an estimate is labeled as one, and an unknown stays unknown.
7. No hype: no exclamation marks, superlatives or urgency words unless the venue's existing strings use them. No emoji unless the product already does.
8. One idea per string. A short blurb is a few plain sentences, not a list, and carries no bold or headings unless the component renders them.
9. Match the product's capitalization and punctuation habits (sentence case, title case, en dashes in ranges) over this card's defaults. The approved profile for this channel overrides both.
