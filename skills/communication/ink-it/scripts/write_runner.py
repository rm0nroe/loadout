#!/usr/bin/env python3
"""Deterministic runner for the /ink-it skill (Builds 1-3: Slack, PR title/body,
PR comments, email, commit messages, release notes, postmortems, tickets,
articles, docs).

Commands:
  route     pick the rule set for a channel
  voice     resolve the voice data root and report what exists
  snapshot  record protected spans: --source material must survive in the
            draft, --context material is protected only where it is used
  finalize  restore changed protected spans, strip AI attribution, run
            mechanical checks on the exact final text, write it only on pass

Editorial rules (tells, tone, formatting taste) belong to the channel cards,
not here. Punctuation bans are per user, loaded from a rules file.

Stdlib only. It starts no child process and never calls git, gh, or the
network: drafting has no publishing side effects.

Exit codes: 0 pass, 1 fixable lint errors (revise), 2 rejected
(preservation or attribution conflict), 3 revision round limit,
4 channel not drafted in this build, 64 usage or ambiguous request.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
MAX_REVISION_ROUNDS = 2
SHIPPED_BUILD = 3   # channels whose build is <= this are drafted

# ---------------------------------------------------------------- routing

ROUTES = {
    "slack": {"ruleset": "ghostwriter", "card": "references/slack.md", "build": 1},
    "pr": {"ruleset": "pr-creator", "card": "references/pr.md", "build": 1},
    "pr-comment": {"ruleset": "ghostwriter", "card": "references/pr-comment.md", "build": 2},
    "email": {"ruleset": "ghostwriter", "card": "references/email.md", "build": 2},
    "commit": {"ruleset": "repo-conventions", "card": "references/commit.md", "build": 2},
    "release-notes": {"ruleset": "sepia", "card": "references/release-notes.md", "build": 3},
    "postmortem": {"ruleset": "sepia", "card": "references/postmortem.md", "build": 3},
    "ticket": {"ruleset": "sepia", "card": "references/ticket.md", "build": 3},
    "article": {"ruleset": "sepia", "card": "references/article.md", "build": 3},
    "docs": {"ruleset": "sepia", "card": "references/docs.md", "build": 3},
}

# Order matters: more specific patterns claim their words first.
REQUEST_PATTERNS = [
    ("pr-comment", r"\b(pr|pull request|review) comments?\b|\bcomment on (the|this|my|a) (pr|pull request)\b|\breview repl(y|ies)\b"),
    ("pr", r"\b(pr|pull request) (title|description|body|desc)s?\b|\bpr desc\b|\bdescribe (the|this|my) (pr|pull request)\b"),
    ("commit", r"\bcommit messages?\b"),
    ("release-notes", r"\brelease notes?\b|\bchangelog\b"),
    ("postmortem", r"\bpost-?mortem\b|\bincident (report|review)\b"),
    ("ticket", r"\b(ticket|jira|linear issue)\b"),
    ("email", r"\be-?mail\b"),
    ("slack", r"\bslack\b|\bdm\b|\bthread repl(y|ies)\b|\bstandup (update|post)\b"),
    ("article", r"\b(article|blog post|essay)\b"),
    ("docs", r"\b(docs|documentation|readme)\b"),
]


def route(channel=None, request=None):
    if channel:
        if channel not in ROUTES:
            return 64, {"error": f"unknown channel {channel!r}", "channels": sorted(ROUTES)}
        found = [channel]
    else:
        text = (request or "").lower()
        found, claimed = [], text
        for name, pat in REQUEST_PATTERNS:
            if re.search(pat, claimed):
                found.append(name)
                claimed = re.sub(pat, " ", claimed)
        if len(found) != 1:
            return 64, {"error": "ambiguous request" if found else "no channel found",
                        "matches": found, "action": "ask which channel"}
    name = found[0]
    r = ROUTES[name]
    out = {"channel": name, "ruleset": r["ruleset"], "build": r["build"],
           "supported": r["build"] <= SHIPPED_BUILD, "mechanical": "runner finalize"}
    if r["card"]:
        out["card"] = str(SKILL_DIR / r["card"])
    if not out["supported"]:
        out["error"] = f"{name} ships in build {r['build']}; this build does not draft it"
        return 4, out
    return 0, out


# ------------------------------------------------------------------ voice

def voice_root():
    return Path(os.environ.get("GHOSTWRITER_HOME") or "~/.config/ghostwriter").expanduser()


def voice(channel):
    root = voice_root()
    profile = f"{channel}.md"
    info = {"root": str(root), "exists": root.is_dir(),
            "soul": str(root / "soul.md") if (root / "soul.md").is_file() else None,
            "profile": str(root / profile) if (root / profile).is_file() else None,
            "rules": str(root / "rules.json") if (root / "rules.json").is_file() else None,
            "persona_fallback": None}
    # candidate corpora: unapproved evidence for a profile proposal, never read while drafting
    imports = root / "imports"
    info["candidate_corpora"] = sorted(str(d) for d in imports.iterdir() if d.is_dir()) if imports.is_dir() else []
    persona = Path(os.environ.get("GHOSTWRITER_PERSONA") or root / "persona.md").expanduser()
    if not info["profile"] and persona.is_file():
        info["persona_fallback"] = str(persona)
    if not info["profile"]:
        info["request"] = (f"No approved {channel} profile yet. Send 5-10 {channel} samples you wrote, "
                           "tagged with date and whether AI helped.")
    if not info["rules"]:
        info["rules_note"] = "no rules.json: finalize applies no punctuation bans"
    return 0, info


# ------------------------------------------------------------- snapshot

KEEP_RE = re.compile(r"\[\[keep\]\](.*?)\[\[/keep\]\]", re.S)
AUTO_PATTERNS = [
    ("code", re.compile(r"^[ \t]*(```|~~~)[^\r\n]*\r?\n(.*?)\r?\n[ \t]*\1[ \t]*\r?$", re.S | re.M), 2),
    ("inline-code", re.compile(r"(?<!`)`([^`\r\n]+)`(?!`)"), 1),
    ("url", re.compile(r"\bhttps?://[^\s<>\"'`]+[^\s<>\"'`.,;:!?)\]}]"), 0),
    ("quote", re.compile(r"\"([^\"\r\n]{3,})\"|“([^”\r\n]{3,})”"), None),
    ("identifier", re.compile(
        r"\b[A-Z][A-Z0-9]+-\d+\b"                      # ticket IDs
        r"|(?<![\w/.])(?:[\w.-]+/)+[\w.-]+\.\w+\b"     # paths with a directory
        r"|\b[a-z]+(?:_[a-z0-9]+)+\b"                  # snake_case
        r"|\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b"          # CONSTANT_CASE
        r"|\b[a-z]+[a-z0-9]*[A-Z][A-Za-z0-9]*\b"       # camelCase
        r"|(?<![\w#])#\d+\b"), 0),                      # PR / issue refs
]
# kinds whose count in the draft may not exceed their count in the source
BOUNDED = {"designated", "quote", "code"}


def read_text(path):
    data = Path(path).read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise SystemExit(_die(2, {"rejected": [f"{path} is not valid UTF-8: {e}"]}))


def _dedent(t):
    """A code block as its span reads it: the match region starts at the first character, so the
    first line has no indent, and later lines lose the first line's indent (its list nesting)."""
    first, *rest = t.split("\n")
    pref = first[:len(first) - len(first.lstrip(" \t"))]
    return "\n".join([first[len(pref):]] + [l[len(pref):] if l.startswith(pref) else l for l in rest])


def _prefix(draft, a):
    """Whitespace before position a on its line, when that is all there is (the block's nesting)."""
    pre = draft[draft.rfind("\n", 0, a) + 1:a]
    return "" if pre.strip(" \t") else pre


def _view(draft, a, b, kind):
    """The draft region as a span reads it: code blocks without their own nesting indent."""
    t = draft[a:b]
    if kind != "code" or "\n" not in t:
        return t
    pref = _prefix(draft, a)
    first, _, rest = t.partition("\n")
    return "\n".join([first] + [l[len(pref):] if l.startswith(pref) else l for l in rest.split("\n")])


def _reindent(text, kind, draft, a):
    if kind != "code" or "\n" not in text:
        return text
    pref = _prefix(draft, a)
    first, _, rest = text.partition("\n")
    return "\n".join([first] + [pref + l if l.strip("\r") else l for l in rest.split("\n")])


def _plain_word(t):
    return t.isalpha() and (t.islower() or t.isupper() or t.istitle())


def _extract(text):
    found = [("designated", m.group(1)) for m in KEEP_RE.finditer(text)]
    seen = {m.span(1) for m in KEEP_RE.finditer(text)}
    for kind, pat, grp in AUTO_PATTERNS:
        for m in pat.finditer(text):
            group = grp if grp is not None else next(i for i, g in enumerate(m.groups(), 1) if g)
            t = m.group(group)
            if kind == "code":
                t = _dedent(t)
            if m.span(group) not in seen and "[[keep]]" not in t and "[[/keep]]" not in t:
                seen.add(m.span(group))
                # a quoted single token is a literal or name, not someone's words
                found.append(("identifier" if kind == "quote" and not re.search(r"\s", t) else kind, t))
    return found


def snapshot(sources, contexts=()):
    """Spans from sources are required; spans only in context are protected if used.
    A [[keep]] span is required exactly as many times as it is marked."""
    hits = [(kind, t, True) for text in sources for kind, t in _extract(text)]
    hits += [(kind, t, False) for text in contexts for kind, t in _extract(text)]
    spans = {}
    for _, t, _ in hits:
        if t in spans:
            continue
        mine = [(k, src) for k, tt, src in hits if tt == t]
        kinds = [k for k, _ in mine]
        kind = "designated" if "designated" in kinds else kinds[0]
        required = kind == "designated" or any(src for _, src in mine)
        if kind == "designated":
            count = kinds.count("designated")
        else:
            count = sum(1 for _, src in mine if src == required)
        spans[t] = {"kind": kind, "text": t, "required": required, "count": count}
    vocab = sorted({w for text in (*sources, *contexts) for w in WORD.findall(text.lower())})
    return {"version": 2, "spans": list(spans.values()), "vocab": vocab}


# ---------------------------------------------------- normalized matching

_FOLD = {**{c: "'" for c in "‘’‚‛′"},
         **{c: '"' for c in "“”„‟″"},
         **{c: "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"}}


def normalize(s):
    """Folded text plus a map from each folded char to its source index."""
    out, idx, prev_space = [], [], False
    for i, ch in enumerate(s):
        if ch == "\r":
            continue
        ch = _FOLD.get(ch, ch)
        if ch.isspace() or unicodedata.category(ch) == "Zs":
            if prev_space:
                continue
            out.append(" ")
            idx.append(i)
            prev_space = True
            continue
        prev_space = False
        for c in ch.casefold():
            out.append(c)
            idx.append(i)
    return "".join(out), idx


_JOINERS = set("-/.@:#+~")


def _wordish(c):
    return c.isalnum() or c == "_"


def _find_candidates(draft, ndraft, nidx, span):
    nspan = normalize(span)[0].strip()
    if not nspan:
        return []
    res, start = [], 0
    while (k := ndraft.find(nspan, start)) >= 0:
        a, b = nidx[k], nidx[k + len(nspan) - 1] + 1
        glued = ((a > 0 and _wordish(draft[a - 1]) and _wordish(span[0]))
                 or (b < len(draft) and _wordish(draft[b]) and _wordish(span[-1])))
        if draft[a:b] != span and not glued:
            # a changed span must stand alone: not part of a branch name, path, URL or longer ID
            left = draft[a - 1] if a > 0 else " "
            right = draft[b] if b < len(draft) else " "
            after = draft[b + 1] if b + 1 < len(draft) else " "
            glued = (left in _JOINERS or _wordish(left)) and _wordish(span[0]) or \
                    (right in _JOINERS and not (right == "." and after.isspace())) and _wordish(span[-1])
        if not glued:
            res.append((a, b))
        start = k + 1
    return res


# ------------------------------------------------------------ attribution

AI_NAMES = (r"claude(?:[ -]code)?|codex|chatgpt|openai|anthropic|(?:github )?copilot|cursor|gemini|"
            r"gpt[\w.-]*|windsurf|aider|devin|jules|grok|opencode|amp|llm|an? ai|ai(?: assistant)?")
AI_RE = re.compile(r"\b(?:" + AI_NAMES + r")\b|\bbot\b|\[bot\]|\bagent\b|\bassistant\b|noreply@(?:anthropic|openai)\.com", re.I)
TRAILER_LINE = re.compile(r"^[^\S\r\n]*(co-authored-by|assisted-by|generated-by|ai-by|ai-assisted(?:-by)?)\s*:[^\r\n]*(?:\r?\n|$)",
                          re.I | re.M)
_PREP = (r"(?:with the (?:help|assistance|support) of|with (?:help|assistance|support) from|"
         r"with|by|using|via|in|through|thanks to)")
CREDIT = re.compile(r"(?:\U0001F916[ \t]*)?(?<![A-Za-z0-9])(?:generated|made|written|drafted|created|built|produced|authored|"
                    r"co-authored|assisted|powered|composed|prepared)[ \t]+(?:(?:entirely|partly|partially|mostly|"
                    r"fully|largely)[ \t]+)?" + _PREP + r"[ \t]+", re.I)
DISCLOSURE = re.compile(r"\b(?:ai|llm|gpt|machine|bot)[- ](?:generated|assisted|written|drafted|authored|"
                        r"produced|created)\b", re.I)
_TEXT_NOUN = (r"(?:message|draft|text|summary|description|post|reply|note|response|write-?up|content|body|pr|"
              r"update|comment)s?")
# a short sentence is a disclosure only when its other words name the text itself:
# "AI-generated draft" goes, "AI-generated images improve accessibility" stays
SHORT_DISCLOSURE = re.compile(r"(?:[\w-]+:[ \t]+)?(?:(?:this|the)[ \t]+)?(?:" + _TEXT_NOUN + r"[ \t]+)?" + DISCLOSURE.pattern +
                              r"(?:[ \t]+" + _TEXT_NOUN + r")?", re.I)
SELF_REF = re.compile(r"\b(?:this|these|the above|the following)[ \t]+(?:[\w-]+[ \t]+){0,2}?" + _TEXT_NOUN + r"\b"
                      r"[ \t]+(?:was|is|were|are|has been|have been)[ \t]+(?:(?:entirely|partly|partially|mostly|fully|"
                      r"largely)[ \t]+)?(?:[\w-]*generated|[\w-]*assisted|[\w-]*written|[\w-]*drafted|created|"
                      r"produced|composed|prepared|authored)\b", re.I)
SESSION_URL = re.compile(
    r"\(?<?https?://(?:www\.)?(?:claude\.ai/(?:code|chat|share)|chatgpt\.com/(?:codex|c|share|g)|"
    r"(?:www\.)?cursor\.com/(?:agents|background-agent))[^\s)>]*>?\)?", re.I)
# a credited tool: a known AI name, a markdown link, or a bare 1-3 token name ending the sentence
TOOL_TAIL = re.compile(r"\[[^\]\r\n]+\](?:\([^)\r\n]*\))?|[\w.+-]+(?: [\w.+-]+){0,2}")
_EMPH = "*_~"


def _sentence(text, i):
    """Bounds of the sentence around i, within its line. A ')' closes the
    sentence only when it closes a '(' opened before the sentence."""
    ls = text.rfind("\n", 0, i) + 1
    starts = [m.end() for m in re.finditer(r"[.!?|][ \t]+|\(", text[ls:i])]
    s0 = ls + (starts[-1] if starts else 0)
    le = text.find("\n", i)
    le = len(text) if le < 0 else le
    depth = 0
    for j in range(i, le):
        c = text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            if depth == 0:
                return s0, j
            depth -= 1
        elif c in ".!?" and depth == 0 and (j + 1 == le or text[j + 1] in " \t\r*_~)"):
            return s0, j + 1
    return s0, le


def _opens_sentence(text, a):
    before = text[text.rfind("\n", 0, a) + 1:a].rstrip(" \t" + _EMPH)
    return (not before.strip(" \t-*>\u2022") or before[-1] in ".!?:;|(" or
            unicodedata.category(before[-1]) == "So")


def _widen(text, a, b):
    """Take wrapping emphasis or parentheses with the hit."""
    while a > 0 and b < len(text) and text[a - 1] == text[b] and text[b] in _EMPH:
        a, b = a - 1, b + 1
    if a > 0 and text[a - 1] == "(" and b < len(text) and text[b] == ")":
        a, b = a - 1, b + 1
    return a, b


_PREP_TAIL = re.compile(_PREP + r"[ \t]+$", re.I)
_PREP_HEAD = re.compile(r"[ \t]+" + _PREP + r"[ \t]+", re.I)


WORD = re.compile(r"[\w+-]+(?:\.[\w+-]+)*")


def _credited(prep, tool, vocab=frozenset()):
    """Is this credit a tool byline? A known AI name always is. "by" also credits
    people, so an unknown name after "by" stays. After with/using/via, an unknown
    short name goes, unless the user's own source or context supplied it:
    "Generated with sqlc." from their notes is a fact, not a byline. Callers pass
    no vocab for robot-marked or self-referential credits, which are bylines."""
    if AI_RE.search(tool):
        return True
    if prep.lower() == "by" or not TOOL_TAIL.fullmatch(tool):
        return False
    words = WORD.findall(tool.lower())
    return not (words and all(w in vocab for w in words))


def _credit_hits(text, vocab=frozenset(), ambiguous=None):
    hits = []
    for m in CREDIT.finditer(text):
        a = m.start()
        if not _opens_sentence(text, a):
            continue
        _, stop = _sentence(text, m.end())
        tool = text[m.end():stop].rstrip(" .!?)" + _EMPH).strip()
        prep = _PREP_TAIL.search(m.group(0)).group(0).strip()
        while stop > m.end() and text[stop - 1] in _EMPH + " \t\r":
            stop -= 1
        span = _widen(text, a, stop)
        robot = m.group(0).startswith("\U0001F916")     # a robot-marked byline is never a fact
        if _credited(prep, tool, frozenset() if robot else vocab):
            hits.append((*span, "credit"))
        elif span != (a, stop) and _credited(prep, tool) and ambiguous is not None:
            # wrapped credit naming a supplied tool: fact or byline, the text cannot say
            ambiguous.append(a)
    for m in DISCLOSURE.finditer(text):
        s0, e = _sentence(text, m.start())
        unit = text[s0:e].strip(" .!?()" + _EMPH)
        if SHORT_DISCLOSURE.fullmatch(unit) or SELF_REF.search(text[s0:e]):
            hits.append((*_widen(text, s0, e), "disclosure"))
    for m in SELF_REF.finditer(text):
        s0, e = _sentence(text, m.start())
        if not DISCLOSURE.search(m.group(0)):          # "AI-written" says it outright
            p = _PREP_HEAD.match(text, m.end())
            if not p:
                continue                                 # "was written." credits no one
            tool = text[p.end():e].rstrip(" .!?)" + _EMPH).strip()
            if not _credited(p.group(0).strip(), tool):  # "this response was drafted with X" credits X even if supplied
                continue
        hits.append((*_widen(text, s0, e), "disclosure"))
    return hits


def attribution_hits(text, vocab=frozenset()):
    hits = [(m.start(), m.end(), "trailer") for m in TRAILER_LINE.finditer(text)
            if not m.group(1).lower() == "co-authored-by" or AI_RE.search(m.group(0).split(":", 1)[1])]
    for a, b, k in _credit_hits(text, vocab) + [(m.start(), m.end(), "session-url") for m in SESSION_URL.finditer(text)]:
        if not any(x < b and a < y for x, y, _ in hits):
            hits.append((a, b, k))
    return sorted(hits)


def strip_attribution(text, hits):
    # widen each hit: an inline hit that leaves its line empty takes the whole line
    cuts = []
    for a, b, kind in hits:
        whole = kind == "trailer"
        if not whole:
            ls = text.rfind("\n", 0, a) + 1
            le = text.find("\n", b)
            le = len(text) if le < 0 else le + 1
            if not (text[ls:a] + text[b:le]).strip(" \t\r\n-*_~>\u2022"):
                a, b, whole = ls, le, True
            elif a > 0 and text[a - 1] == " ":
                a -= 1
            elif b < len(text) and text[b] == " ":
                b += 1
        cuts.append([a, b, whole])
    # a removed line also takes the blank separator line above it, when what
    # follows is another blank line, another removed line, or the end
    starts = {c[0] for c in cuts if c[2]}
    for c in cuts:
        if c[2]:
            sep = re.search(r"\n(\r?\n)$", text[:c[0]])
            rest = text[c[1]:]
            if sep and (not rest.strip() or re.match(r"\r?\n", rest) or c[1] in starts):
                c[0] -= len(sep.group(1))
    out, pos = [], 0
    for a, b, _ in sorted(cuts):
        if a >= pos:
            out.append(text[pos:a])
        pos = max(pos, b)
    tail = text[pos:]
    result = "".join(out) + tail
    if not tail.strip():
        # footer removed from the end: drop the gap it leaves, keep the final newline style
        nl = re.search(r"\r?\n$", text)
        result = result.rstrip(" \t\r\n") + (nl.group(0) if nl else "")
    return result


# ------------------------------------------------------------- mechanical

def load_rules(path):
    """Per-user mechanical bans: {"forbid": [{"pattern", "message", "channels"?}]}."""
    if path is None:
        default = voice_root() / "rules.json"
        path = default if default.is_file() else None
    if path is None:
        return []
    rules = json.loads(Path(path).read_text(encoding="utf-8")).get("forbid", [])
    for r in rules:
        r["re"] = re.compile(r["pattern"], re.M)
    return rules


def mechanical(text, channel, protected, template, allow, rules, subject_max=None, vocab=frozenset()):
    errors, warnings = [], []

    def free(a, b):
        return not any(a < pb and pa < b for pa, pb in protected)

    def scan(pat, msg, bucket):
        for m in pat.finditer(text):
            if free(m.start(), m.end()):
                line = text.count("\n", 0, m.start()) + 1
                bucket.append(f"line {line}: {msg}: {m.group(0)!r}")

    for r in rules:
        if channel in r.get("channels", [channel]):
            scan(r["re"], r.get("message", r["pattern"]), errors)
    for a, _, kind in attribution_hits(text, vocab):
        errors.append(f"line {_line(text, a)}: attribution-survived ({kind})")
    ambiguous = []
    _credit_hits(text, vocab, ambiguous)
    for a in ambiguous:
        warnings.append(f"line {_line(text, a)}: possible-byline: a wrapped credit names a tool from the "
                        "source or context; ask the user whether it is a fact or a byline")
    scan(re.compile(r"\[(placeholder|todo|tbd)[^\]]*\]", re.I), "missing fact placeholder", warnings)
    # prose-only checks: skip code fences, inline code and table rows, where repeats and padding are normal
    markup = [m.span() for name, pat, _ in AUTO_PATTERNS if name == "code" for m in pat.finditer(text)]
    markup += [m.span() for pat in (INLINE_CODE, TABLE_ROW) for m in pat.finditer(text)]
    for pat, msg, is_error in PROSE_CHECKS:
        for m in pat.finditer(text):
            if free(m.start(), m.end()) and not any(m.start() < b and a < m.end() for a, b in markup):
                (errors if is_error else warnings).append(f"line {_line(text, m.start())}: {msg}: {m.group(0)!r}")
    if channel in ("pr", "commit", "email", "ticket"):
        title, _, body = text.partition("\n")
        what = {"pr": "PR title", "commit": "commit subject", "email": "email Subject line", "ticket": "ticket title"}[channel]
        if not title.strip():
            errors.append(f"line 1: {what} missing")
        if channel == "email" and title.strip() and not re.match(r"subject:[ \t]*\S", title, re.I):
            errors.append("line 1: email draft starts with 'Subject: <subject>'")
        if body and not re.match(r"\r?\n", body):
            errors.append(f"line 2: blank line required after the {what}")
        if channel == "commit" and subject_max and len(title.rstrip("\r")) > subject_max:
            errors.append(f"line 1: commit subject is {len(title.rstrip(chr(13)))} chars, repo limit {subject_max}")
    if channel == "pr":
        tpl = (template or "").lower()
        if "test plan" not in tpl and "test-plan" not in allow:
            scan(re.compile(r"^#{1,6}\s*test plan\b.*$", re.I | re.M), "Test plan section (template or --allow test-plan)", errors)
        if "[ ]" not in tpl and "checkboxes" not in allow:
            scan(re.compile(r"^\s*[-*] \[[ xX]\] .*$", re.M), "checkbox (template or --allow checkboxes)", errors)
    return errors, warnings


TABLE_ROW = re.compile(r"^[ \t]*\|.*$", re.M)
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)")   # any matching backtick run: `x`, ``x``
PROSE_CHECKS = [   # (pattern, message, is_error); mechanical only, never taste
    (re.compile(r"\b([A-Za-z]+)[ \t]+\1\b", re.I), "repeated word", True),   # same line only
    (re.compile(r"[^\s] {2,}[^\s]"), "two spaces between words", False),
    (re.compile(r"^[^`\n]*`[^`\n]*$", re.M), "stray backtick; inline code may be unclosed", True),
]


# ------------------------------------------------------------- finalize

def _line(text, i):
    return text.count("\n", 0, i) + 1


def _regions(text, spans):
    out = []
    nt, ni = normalize(text)
    for s in spans:
        if s["kind"] == "code" and "\n" in s["text"]:
            out += _find_candidates(text, nt, ni, s["text"])
            continue
        start = 0
        while (k := text.find(s["text"], start)) >= 0:
            out.append((k, k + len(s["text"])))
            start = k + 1
    return out


def finalize(draft, snap, channel, template=None, allow=(), omit=(), rules=(), subject_max=None):
    spans = snap["spans"]
    vocab = frozenset(snap.get("vocab", ()))
    known = {s["text"] for s in spans}
    unknown = [o for o in omit if o not in known]
    if unknown:
        return 64, {"error": "--omit names text that is not a snapshot span", "unknown": unknown}, None
    rejected = []
    ndraft, nidx = normalize(draft)

    cands = []  # (a, b, span_text, kind)
    for s in spans:
        if not s["required"] and len(normalize(s["text"])[0].strip()) < 6 and s["text"] not in draft:
            continue  # short context spans: too many innocent near-misses in prose
        for a, b in _find_candidates(draft, ndraft, nidx, s["text"]):
            if s["kind"] in ("inline-code", "identifier") and _plain_word(s["text"]) and draft[a:b] != s["text"]:
                continue  # an ordinary word in other case is prose, not a changed identifier
            cands.append((a, b, s["text"], s["kind"]))

    # an exact match settles its region: case-folded twins are not candidates there
    exact_at = {(a, b) for a, b, t, kd in cands if _view(draft, a, b, kd) == t}
    cands = [c for c in cands if _view(draft, c[0], c[1], c[3]) == c[2] or (c[0], c[1]) not in exact_at]

    # overlaps: same region for two texts is ambiguous; a container whose text
    # holds the inner text wins; any other overlap conflicts
    cands.sort(key=lambda c: (c[0], -(c[1] - c[0])))
    kept, dropped = [], []
    for c in cands:
        clash = [k for k in kept if c[0] < k[1] and k[0] < c[1]]
        if not clash:
            kept.append(c)
            continue
        for k in clash:
            if (k[0], k[1]) == (c[0], c[1]) and k[2] != c[2]:
                rejected.append(f"ambiguous restoration at {c[0]}: {draft[c[0]:c[1]]!r} matches "
                                f"{k[2]!r} and {c[2]!r}")
            elif k[0] <= c[0] and c[1] <= k[1] and c[2] in k[2]:
                pass
            elif (k[0] <= c[0] and c[1] <= k[1] and draft[c[0]:c[1]] != c[2]
                  and normalize(c[2])[0].strip() in normalize(k[2])[0]):
                dropped.append(c)   # a case-variant fragment inside a longer protected span, not a match of its own
            elif k[2] != c[2]:
                rejected.append(f"overlapping protected spans at {c[0]}: {k[2]!r} vs {c[2]!r}")

    cands = [c for c in cands if c not in dropped]

    for s in spans:
        text = s["text"]
        # Count nested matches too; only restoration uses the outermost spans.
        mine = [k for k in cands if k[2] == text]
        exact = sum(1 for k in mine if _view(draft, k[0], k[1], k[3]) == text)
        changed = len(mine) - exact
        hi = s["count"] if s["kind"] in BOUNDED else float("inf")
        lo = 0 if (text in omit or not s["required"]) else (s["count"] if s["kind"] == "designated" else 1)
        if exact + changed > hi:
            rejected.append(("ambiguous restoration" if changed else "duplicated protected span")
                            + f" ({s['kind']}): {text!r} allowed {hi}, found {exact} exact + {changed} changed")
        elif exact + changed < lo:
            rejected.append(f"missing protected span ({s['kind']}): {text!r} needs {lo}, found {exact + changed}"
                            " (restore it, or --omit it if dropping it was deliberate)")
    if rejected:
        return 2, {"rejected": sorted(set(rejected))}, None

    restored, parts, pos = [], [], 0
    for a, b, text, kind in sorted(kept):
        if a < pos:
            continue  # nested inside a restored container
        exact = _view(draft, a, b, kind) == text
        parts += [draft[pos:a], draft[a:b] if exact else _reindent(text, kind, draft, a)]
        if not exact:
            restored.append({"kind": kind, "from": draft[a:b], "to": text})
        pos = b
    final = "".join(parts) + draft[pos:]

    protected = _regions(final, spans)
    hits = attribution_hits(final, vocab)
    conflicts = [f"line {_line(final, a)}: attribution-in-protected-text ({kind})"
                 for a, b, kind in hits if any(a < pb and pa < b for pa, pb in protected)]
    if conflicts:
        return 2, {"rejected": conflicts}, None
    stripped = []
    if hits:
        before = {s["text"]: final.count(s["text"]) for s in spans}
        stripped = [{"line": _line(final, a), "code": kind} for a, b, kind in hits]
        final = strip_attribution(final, hits)
        moved = [t for t, n in before.items() if final.count(t) != n]
        if moved:
            return 2, {"rejected": [f"attribution-strip-disturbed-protected-span ({len(moved)})"]}, None
        protected = _regions(final, spans)

    errors, warnings = mechanical(final, channel, protected, template, allow, rules, subject_max, vocab)
    report = {"restored": restored, "stripped_attribution": stripped, "omitted": list(omit),
              "errors": errors, "warnings": warnings,
              "unchanged": final == draft,
              "recheck_meaning": final != draft}
    return (1 if errors else 0), report, final


# ------------------------------------------------------------------- CLI

# unanchored on purpose: diagnostics may hold repr'd text; over-redacting a report is fine
_LOOSE = re.compile(r"(?:co-authored-by|assisted-by|generated-by|ai-by|ai-assisted(?:-by)?)\s*:[^'\"\n]*"
                    r"|" + CREDIT.pattern + r"[^'\"\n.!?]*"
                    r"|" + DISCLOSURE.pattern + r"[^'\"\n.!?]*"
                    r"|" + SESSION_URL.pattern, re.I)


def _scrub(obj):
    """Backstop: no attribution text in any report, whatever field it reached."""
    if isinstance(obj, str):
        return _LOOSE.sub("<attribution>", obj)
    if isinstance(obj, list):
        return [_scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()}
    return obj


def _die(code, obj):
    print(json.dumps(_scrub(obj), indent=2, ensure_ascii=False))
    return code


def main(argv=None):
    p = argparse.ArgumentParser(prog="write_runner")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("route")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--channel")
    g.add_argument("--request")
    v = sub.add_parser("voice")
    v.add_argument("--channel", required=True, choices=sorted(n for n, r in ROUTES.items() if r["build"] <= SHIPPED_BUILD))
    s = sub.add_parser("snapshot")
    s.add_argument("--source", nargs="+", default=[], help="material the draft must carry")
    s.add_argument("--context", nargs="+", default=[], help="background; protected only where used")
    s.add_argument("--out", required=True)
    f = sub.add_parser("finalize")
    f.add_argument("--channel", required=True)
    f.add_argument("--spans", required=True)
    f.add_argument("--draft", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--round", type=int, default=0, help="0 = first draft, 1-2 = revisions")
    f.add_argument("--template")
    f.add_argument("--allow", action="append", default=[], choices=["test-plan", "checkboxes"],
                   help="the user explicitly asked for this PR section")
    f.add_argument("--omit", action="append", default=[], help="source span deliberately left out")
    f.add_argument("--rules", help="mechanical rules JSON (default: $GHOSTWRITER_HOME/rules.json)")
    f.add_argument("--subject-max", type=int, help="commit subject length limit found in the repo's own rules")
    a = p.parse_args(argv)

    if a.cmd == "route":
        return _die(*route(a.channel, a.request))
    if a.cmd == "voice":
        return _die(*voice(a.channel))
    if a.cmd == "snapshot":
        if not a.source and not a.context:
            return _die(64, {"error": "give --source and/or --context"})
        snap = snapshot([read_text(x) for x in a.source], [read_text(x) for x in a.context])
        Path(a.out).write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
        return _die(0, {"spans": len(snap["spans"]),
                        "required": sum(s["required"] for s in snap["spans"]), "out": a.out})
    if a.cmd == "finalize":
        code, info = route(a.channel)
        if code:
            return _die(code, info)
        if not 0 <= a.round <= MAX_REVISION_ROUNDS:
            return _die(3, {"error": f"round {a.round}: revision limit is {MAX_REVISION_ROUNDS}; "
                                     "deliver the last verified draft or report the open problems"})
        if os.path.abspath(a.out) == os.path.abspath(a.draft):
            return _die(64, {"error": "--out must differ from --draft; candidates stay separate"})
        snap = json.loads(Path(a.spans).read_text(encoding="utf-8"))
        if snap.get("version") != 2:
            return _die(64, {"error": "spans file is from an older runner; re-run snapshot"})
        template = read_text(a.template) if a.template else None
        code, report, final = finalize(read_text(a.draft), snap, a.channel, template,
                                       a.allow, a.omit, load_rules(a.rules), a.subject_max)
        report["round"] = a.round
        if code == 0:
            Path(a.out).write_bytes(final.encode("utf-8"))
            report["out"] = a.out
        return _die(code, report)


if __name__ == "__main__":
    sys.exit(main())
