"""Parse the "Phil's Recipes" Google Doc into structured recipes.

No network calls: this module takes the JSON returned by the Docs API
(`documents.get`) and returns recipes plus a problem report.

Text fields (ingredient items, steps, note text) are strings in which links are
written as Markdown, `[text](url)`. Cross-links to other recipes use the URL
scheme `recipe:<slug>`; build.py turns those into page links.
"""
import collections
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

# --- line model ------------------------------------------------------------

ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"), None)
MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


@dataclass
class Line:
    text: str            # rich text, links as [text](url)
    plain: str           # same text without link markup
    heading: int | None  # heading level, or None for normal text
    listed: bool         # first line of a paragraph that is in a Docs list

    @property
    def blank(self):
        return not any(ch.isalnum() for ch in self.plain)


def plain_text(rich):
    """Strip link markup from a rich-text string."""
    return MD_LINK.sub(lambda m: m.group(1), rich)


def clean_url(url, text):
    """Undo redirect wrappers (Mimecast, Google search) around a real link."""
    host = urlparse(url).netloc.lower()
    if host.endswith("mimecastprotect.com") and re.match(r"https?://", text.strip()):
        return text.strip()
    if host.endswith("google.com") and urlparse(url).path == "/search":
        q = parse_qs(urlparse(url).query).get("q", [""])[0]
        if re.match(r"https?://", q):
            return q
    return url


def _tidy(s):
    return re.sub(r"\s+", " ", s.translate(ZERO_WIDTH).replace("\xa0", " "))


def _body(doc):
    if "tabs" not in doc and "content" in doc:
        doc = doc["content"]
    if "tabs" in doc:
        return doc["tabs"][0]["documentTab"]["body"]["content"]
    return doc["body"]["content"]


def _heading_level(style):
    if style == "TITLE":
        return 0
    m = re.fullmatch(r"HEADING_(\d)", style or "")
    return int(m.group(1)) if m else None


def doc_to_lines(doc):
    """Flatten Docs API JSON into Lines, splitting paragraphs at soft line breaks."""
    lines = []
    for element in _body(doc):
        para = element.get("paragraph")
        if not para:
            continue
        heading = _heading_level(para.get("paragraphStyle", {}).get("namedStyleType"))
        # Collect (text, url) segments, merging neighbours that share a link.
        segs = []
        for el in para.get("elements", []):
            run = el.get("textRun")
            if not run:
                continue
            link = run.get("textStyle", {}).get("link", {}).get("url")
            text = run.get("content", "").replace("\n", "")
            if segs and segs[-1][1] == link:
                segs[-1][0] += text
            else:
                segs.append([text, link])
        # Split into lines at soft breaks (\v); build rich and plain text.
        pieces = [[]]
        for text, url in segs:
            parts = text.split("\x0b")
            for i, part in enumerate(parts):
                if i:
                    pieces.append([])
                if part:
                    pieces[-1].append((part, url))
        for i, piece in enumerate(pieces):
            rich, plain = "", ""
            for text, url in piece:
                if url and _tidy(text).strip():
                    lead = text[: len(text) - len(text.lstrip())]
                    trail = text[len(text.rstrip()):]
                    label = _tidy(text).strip()
                    rich += f"{lead}[{label}]({clean_url(url, label)}){trail}"
                else:
                    rich += text
                plain += text
            lines.append(Line(text=_tidy(rich).strip(), plain=_tidy(plain).strip(),
                              heading=heading, listed=("bullet" in para and i == 0)))
    return lines


# --- patterns --------------------------------------------------------------

STEP = re.compile(r"^(\d{1,2})(?:\.\s+|\s+\.\s*)(?=\S)")
STEP_TYPO = re.compile(r"^(\d{1,2})[,;:]\s+(?=[A-Za-z])")  # "3, Spoon…" typed for "3. Spoon…"
ING_LABEL = re.compile(r"^(?:(?P<prefix>(?:\S+\s+){0,5}?\S+)\s+ingredients\s*:|ingredients\s*:?)$", re.I)
DIR_LABEL = re.compile(r"^(?:(?P<prefix>(?:\S+\s+){0,5}?\S+)\s+(?:directions|instructions)\s*:"
                       r"|(?:directions|instructions)\s*:?)$", re.I)
SRC_LABEL = re.compile(r"^(?:(?:\S+\s+){0,3}?\S+\s+)?(?:sources?|recipe|based off of this)\s*:\s*(?P<rest>.*)$"
                       r"|^sources?$", re.I)
NOTE_LABEL = re.compile(r"^(?P<name>notes?|variations?|alternatives?)\s*(?::\s*(?P<rest>.*))?$", re.I)
TAGS_LABEL = re.compile(r"^tags?\s*:\s*(?P<rest>.*)$", re.I)
INLINE_NOTE = re.compile(r"^(?P<name>[A-Z][^:.]{0,40}):\s+(?P<rest>\S.*)$")
BARE_URL = re.compile(r"https?://[^\s<>\]\)]+")
VERBS = {"combine", "mix", "stir", "add", "toss", "place", "put", "heat", "bake", "cook", "whisk",
         "serve", "season", "saute", "sauté", "bring", "preheat", "pour", "let", "cut", "chop", "blend"}
UNITS = (r"cups?|tablespoons?|teaspoons?|tbsps?|tsps?|tbs|pounds?|lbs?|ounces?|oz|grams?|g|ml|"
         r"medium|large|small|cloves?|celery|ribs?|links?|cans?")
MERGED = re.compile(r"(?<=[A-Za-z)])\s*(?:\d+(?:[ -]\d+)?(?:/\d+)?|[½¼¾⅓⅔⅛])\s*(?:" + UNITS + r")\b")
OK_BEFORE_AMOUNT = {"about", "or", "and", "to", "plus", "approximately", "each", "of", "with",
                    "into", "than", "from", "for", "is", "per", "sub", "substitute", "divided",
                    "typically", "usually"}


def _rest_after_colon(rich):
    return rich.split(":", 1)[1].strip() if ":" in rich else ""


def is_name(plain):
    """A short line that could name a section, group or note."""
    s = plain.rstrip(":").strip()
    words = s.split()
    return (1 <= len(words) <= 7 and len(s) <= 60 and not s.endswith(".")
            and not STEP.match(plain))


def _is_ing_label(line):
    return line is not None and not line.blank and ING_LABEL.match(line.plain) is not None


def _looks_like_instruction(plain):
    words = plain.split()
    if len(words) < 8:
        return False
    first = re.sub(r"\W", "", words[0]).lower()
    return first in VERBS or re.search(r"[a-z]\.\s+[A-Z]", plain) is not None


def _links_only(rich):
    rest = BARE_URL.sub(" ", MD_LINK.sub(" ", rich))
    return rest != rich and not any(ch.isalnum() for ch in rest)


def _merged_ingredients(plain):
    """True if a second amount appears mid-line, e.g. "baking soda1 teaspoon garlic powder"."""
    while re.search(r"\([^()]*\)", plain):  # amounts in parentheses are asides, not ingredients
        plain = re.sub(r"\([^()]*\)", " ", plain)
    for m in MERGED.finditer(plain):
        before = plain[: m.start()].split()
        if before and before[-1].lower().strip(",;") not in OK_BEFORE_AMOUNT:
            return True
    return False


# --- slugs -----------------------------------------------------------------

def slugify(title):
    s = title.replace("'", "").replace("’", "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# --- recipe builder --------------------------------------------------------

ING, DIR, NOTE, SRC = "ingredients", "directions", "note", "sources"


class _RecipeBuilder:
    def __init__(self, title):
        self.title = title
        self.recipe = {"slug": slugify(title), "title": title, "sections": [],
                       "sources": [], "notes": [], "tags": []}
        self.problems = []
        self.meta = []          # per section: {"ing_label": bool, "dir_label": bool}
        self.mode = ING
        self.pending_name = None
        self.group = None
        self.group_break = False
        self.step_open = False
        self.last_number = None
        self.note = None
        self.ing_note = None
        self._new_section(None)

    # helpers
    @property
    def section(self):
        return self.recipe["sections"][-1]

    def guess(self, detail):
        self.problems.append({"recipe": self.title, "kind": "guess", "detail": detail})

    def _new_section(self, name):
        sec = {"ingredient_groups": [], "steps": [], "notes": []}
        if name:
            sec = {"name": name, **sec}
        self.recipe["sections"].append(sec)
        self.meta.append({"ing_label": False, "dir_label": False})
        self.group, self.group_break, self.step_open = None, False, False
        self.last_number, self.note, self.ing_note = None, None, None

    def _section_empty(self):
        s, m = self.section, self.meta[-1]
        return not (s["ingredient_groups"] or s["steps"] or s["notes"] or m["ing_label"] or m["dir_label"])

    def _has_items(self):
        return any(g["items"] for g in self.section["ingredient_groups"])

    def _start_group(self, name):
        self.group = {"name": name, "items": []} if name else {"items": []}
        self.section["ingredient_groups"].append(self.group)
        self.group_break = False

    def _start_note(self, name, text, target=None):
        self.note = {"name": name, "text": text} if name else {"text": text}
        (target if target is not None else self.section["notes"]).append(self.note)
        self.mode = NOTE

    def _append(self, existing, line):
        if not existing:
            return line.text
        joiner = " " if line.plain[:1].islower() else "\n"
        return existing + joiner + line.text

    def _add_sources(self, rich):
        pos = 0
        for m in list(MD_LINK.finditer(rich)) + [None]:
            chunk = rich[pos: m.start() if m else len(rich)]
            for i, part in enumerate(BARE_URL.split(chunk)):
                if i:
                    url = BARE_URL.findall(chunk)[i - 1].rstrip(".,;")
                    self.recipe["sources"].append({"text": url, "url": url})
                part = re.sub(r"^\s*(?:and|&)\s+|\s+(?:and|&)\s*$", "", part).strip(" ,;:–—-")
                if any(ch.isalnum() for ch in part):
                    self.recipe["sources"].append({"text": part})
            if m:
                self.recipe["sources"].append({"text": m.group(1) or m.group(2), "url": m.group(2)})
                pos = m.end()

    def _add_step(self, number, text):
        if number is not None:
            if self.last_number is not None and number != self.last_number + 1:
                self.guess(f"step numbers jump from {self.last_number} to {number}: “{plain_text(text)[:60]}”")
            self.last_number = number
        self.section["steps"].append(text)
        self.step_open = True

    # main dispatch
    def feed(self, line, next_line):
        p, t = line.plain, line.text
        if line.blank:
            if self.mode == ING and self.group and self.group["items"]:
                self.group_break = True
            return

        if m := TAGS_LABEL.match(p):
            self.recipe["tags"] += [x.strip() for x in m.group("rest").split(",") if x.strip()]
            return

        if m := ING_LABEL.match(p):
            prefix = m.group("prefix")
            after_dirs = self.section["steps"] or self.meta[-1]["dir_label"] or self.mode in (NOTE, SRC)
            if after_dirs or (prefix is None and self._has_items()):
                self._new_section(self.pending_name)
            elif self.pending_name:
                if self._section_empty():  # a name at the very start: rename, don't add
                    self.recipe["sections"].pop()
                    self.meta.pop()
                self._new_section(self.pending_name)
            self.pending_name = None
            self.mode = ING
            self.meta[-1]["ing_label"] = True
            self.group, self.ing_note = None, None
            if prefix:
                self._start_group(p.rstrip(":").strip())
            return

        if m := DIR_LABEL.match(p):
            if m.group("prefix") and self.section["steps"]:
                self._new_section(m.group("prefix"))
            self.mode = DIR
            self.meta[-1]["dir_label"] = True
            self.step_open, self.last_number = False, None
            return

        if m := SRC_LABEL.match(p):
            self.mode = SRC
            self._add_sources(_rest_after_colon(t))
            return

        if m := NOTE_LABEL.match(p):
            target = self.recipe["notes"] if self.mode == SRC else None
            self._start_note(m.group("name"), _rest_after_colon(t), target)
            return

        if is_name(p) and _is_ing_label(next_line) and (
                self.mode != ING or self._section_empty() or ING_LABEL.match(next_line.plain).group("prefix") is None):
            self.pending_name = p.rstrip(":").strip()
            return

        step = STEP.match(t)
        if not step and self.mode == DIR and (step := STEP_TYPO.match(t)):
            self.guess(f"step number looks mistyped (“{t[:step.end()].strip()}” instead of "
                       f"“{step.group(1)}.”); treated it as step {step.group(1)}")
        if step or line.listed:
            number = int(step.group(1)) if step else None
            text = t[step.end():] if step else t
            if self.mode == NOTE:
                note, self.note = self.note, None
                if not note["text"]:
                    for lst in (self.section["notes"], self.recipe["notes"]):
                        if note in lst:
                            lst.remove(note)
                self._new_section(note.get("name"))
            self.mode = DIR
            self._add_step(number, text)
            return

        colon_name = p.endswith(":") and is_name(p)
        if self.mode == ING:
            if colon_name:
                self._start_group(p.rstrip(":").strip())
            elif self.ing_note is not None and p[:1].islower():
                self.ing_note["text"] = self._append(self.ing_note["text"], line)
            elif _looks_like_instruction(p):
                self.ing_note = {"text": t}
                self.section["notes"].append(self.ing_note)
                self.guess(f"moved a sentence from the ingredients to notes: “{p[:70]}”")
            else:
                if self.group is None or self.group_break:
                    self._start_group(None)
                self.group["items"].append(t)
                self.ing_note = None
                if _merged_ingredients(p):
                    self.guess(f"this ingredient line may hold two ingredients: “{p}”")
        elif self.mode == DIR:
            inline = INLINE_NOTE.match(p) if self.step_open else None
            if colon_name:
                self._start_note(p.rstrip(":").strip(), "")
            elif inline and len(inline.group("name").split()) <= 4:
                self._start_note(inline.group("name").strip(), _rest_after_colon(t))
                self.guess(f"treated this line after the steps as a note named “{inline.group('name')}”: “{p[:60]}”")
            elif not self.step_open:
                self._add_step(None, t)
            else:
                self.section["steps"][-1] = self._append(self.section["steps"][-1], line)
        elif self.mode == NOTE:
            if self.note in self.recipe["notes"] and _links_only(t):
                # a note written among the sources, followed by more source links
                self.mode = SRC
                self._add_sources(t)
            elif colon_name:
                target = self.recipe["notes"] if self.note in self.recipe["notes"] else None
                self._start_note(p.rstrip(":").strip(), "", target)
            else:
                self.note["text"] = self._append(self.note["text"], line)
        elif self.mode == SRC:
            if colon_name:
                self._start_note(p.rstrip(":").strip(), "", self.recipe["notes"])
            else:
                self._add_sources(t)

    def finish(self):
        for lst in [s["notes"] for s in self.recipe["sections"]] + [self.recipe["notes"]]:
            lst[:] = [n for n in lst if n["text"]]
        for sec, meta in zip(self.recipe["sections"], self.meta):
            sec["ingredient_groups"] = [g for g in sec["ingredient_groups"] if g["items"]]
            where = f" (in “{sec['name']}”)" if sec.get("name") else ""
            if meta["ing_label"] and not sec["ingredient_groups"]:
                self.problems.append({"recipe": self.title, "kind": "empty-ingredients",
                                      "detail": f"the Ingredients section is empty{where}"})
            if meta["dir_label"] and not sec["steps"]:
                self.problems.append({"recipe": self.title, "kind": "empty-directions",
                                      "detail": f"the Directions section is empty{where}"})
        return self.recipe


# --- splitting the doc into recipes ----------------------------------------

def _title_level(lines):
    levels = collections.Counter(l.heading for l in lines if l.heading is not None and not l.blank)
    return levels.most_common(1)[0][0] if levels else None


def _split(lines):
    """Yield (title_line, body_lines) for each recipe, plus lines before the first title."""
    level = _title_level(lines)
    before, recipes = [], []
    for line in lines:
        if line.heading == level and level is not None:
            if not line.blank:
                recipes.append((line, []))
            continue
        (recipes[-1][1] if recipes else before).append(line)
    return before, recipes


def _parse(lines):
    _, chunks = _split(lines)
    recipes, problems = [], []
    seen = collections.Counter()
    for title_line, body in chunks:
        b = _RecipeBuilder(title_line.plain)
        for i, line in enumerate(body):
            nxt = next((l for l in body[i + 1:] if not l.blank), None)
            b.feed(line, nxt)
        recipe = b.finish()
        seen[recipe["slug"]] += 1
        if seen[recipe["slug"]] > 1:
            recipe["slug"] += f"-{seen[recipe['slug']]}"
            b.guess(f"another recipe has the same page address; this one became {recipe['slug']}")
        recipes.append(recipe)
        problems += b.problems
    return recipes, problems


def parse_lines(lines):
    return _parse(lines)[0]


# --- checks ----------------------------------------------------------------

SHORT_WORDS = 25


def _words(texts):
    return sum(len(plain_text(t).split()) for t in texts)


def check_recipes(recipes):
    problems = []
    step_owner = {}
    for r in recipes:
        items = [i for s in r["sections"] for g in s["ingredient_groups"] for i in g["items"]]
        steps = [st for s in r["sections"] for st in s["steps"]]
        if not steps:
            problems.append({"recipe": r["title"], "kind": "no-steps", "detail": "no steps"})
        n = _words(items + steps)
        if n < SHORT_WORDS:
            problems.append({"recipe": r["title"], "kind": "short",
                             "detail": f"unusually short ({n} words of ingredients and steps)"})
        for i, st in enumerate(steps, 1):
            key = " ".join(plain_text(st).lower().split())
            if len(key.split()) < 8:
                continue
            if key in step_owner and step_owner[key] != r["title"]:
                problems.append({"recipe": r["title"], "kind": "copied-step",
                                 "detail": f"step {i} is identical to a step in “{step_owner[key]}”"})
            step_owner.setdefault(key, r["title"])
    return problems


# --- cross-links -----------------------------------------------------------

# (recipe the link appears in, phrase to link, recipe it points to). The only
# cross-links on the site; Beef Stock and Pancakes are deliberately not linked.
CROSS_LINKS = [
    ("Pulled Pork", "Traditional “Sweet and Tangy” BBQ Sauce", "Traditional “Sweet and Tangy” BBQ Sauce"),
    ("Traditional “Sweet and Tangy” BBQ Sauce", "pulled pork", "Pulled Pork"),
    ("Basic Curry and Variations", "Tofu Stir Fry", "Tofu Stir Fry"),
    ("Quesadillas, Several Types", "Kale, Poblano, and Black Bean Tacos", "Kale, Poblano, and Black Bean Tacos"),
    ("Aunt Maria’s Buffalo Chicken Dip", "blue cheese dressing", "Blue Cheese Dressing"),
    ("Pasta Broccoli Bolognese", "Italian sausage", "Italian Sausage"),
    ("Korean Spicy Beef Soup", "chili oil", "Chili Oil"),
    ("Phil’s Chinese Cabbage", "chili oil", "Chili Oil"),
    ("Taiwanese Spicy Beef Soup", "chili oil", "Chili Oil"),
    ("Yucatan Shrimp", "chili oil", "Chili Oil"),
    ("Pumpkin Ravioli", "Fresh egg pasta dough", "Fresh Egg Pasta Dough"),
]


def _key(title):
    return re.sub(r"[\"'“”‘’]", "", title).casefold().strip()


def _link_phrase(rich, phrase, slug):
    pattern = re.compile(re.escape(phrase).replace(r"\ ", r"\s+"), re.I)
    out, pos = [], 0
    for m in list(MD_LINK.finditer(rich)) + [None]:
        chunk = rich[pos: m.start() if m else len(rich)]
        out.append(pattern.sub(lambda x: f"[{x.group(0)}](recipe:{slug})", chunk))
        if m:
            out.append(m.group(0))
            pos = m.end()
    return "".join(out)


def apply_cross_links(recipes):
    problems = []
    by_key = {_key(r["title"]): r for r in recipes}
    for src_title, phrase, dst_title in CROSS_LINKS:
        src, dst = by_key.get(_key(src_title)), by_key.get(_key(dst_title))
        if src is None:
            problems.append({"recipe": src_title, "kind": "cross-link",
                             "detail": f"recipe not found, so its link to “{dst_title}” was skipped"})
            continue
        if dst is None:
            problems.append({"recipe": src["title"], "kind": "cross-link",
                             "detail": f"link target “{dst_title}” not found"})
            continue
        linked = False

        def link(text):
            nonlocal linked
            new = _link_phrase(text, phrase, dst["slug"])
            linked |= new != text
            return new

        for sec in src["sections"]:
            for g in sec["ingredient_groups"]:
                g["items"] = [link(i) for i in g["items"]]
            sec["steps"] = [link(s) for s in sec["steps"]]
            for n in sec["notes"]:
                n["text"] = link(n["text"])
        for n in src["notes"]:
            n["text"] = link(n["text"])
        if not linked:
            problems.append({"recipe": src["title"], "kind": "cross-link",
                             "detail": f"the phrase “{phrase}” wasn't found, so there's no link to “{dst_title}”"})
    return problems


# --- nothing dropped -------------------------------------------------------

def _norm(s):
    return " ".join(plain_text(s).casefold().split())


def _corpus(recipe):
    texts = [recipe["title"]] + recipe["tags"]
    for s in recipe["sections"]:
        texts.append(s.get("name", ""))
        for g in s["ingredient_groups"]:
            texts += [g.get("name", "")] + g["items"]
        texts += s["steps"]
        texts += [n.get("name", "") + " " + n["text"] for n in s["notes"]]
    texts += [n.get("name", "") + " " + n["text"] for n in recipe["notes"]]
    texts += [src["text"] + " " + src.get("url", "") for src in recipe["sources"]]
    return " | ".join(_norm(t) for t in texts)


def _content_of(line):
    """The part of a line that should appear in the output, or '' for a bare label."""
    p = line.plain
    if m := STEP.match(p):
        p = p[m.end():]
    for pat in (ING_LABEL, DIR_LABEL):
        if pat.match(p):
            return p.rstrip(":") if pat.match(p).group("prefix") and pat is ING_LABEL else ""
    for pat in (SRC_LABEL, NOTE_LABEL, TAGS_LABEL):
        if pat.match(p):
            return _rest_after_colon(p)
    return p.rstrip(":")


def find_dropped(lines, recipes):
    problems = []
    before, chunks = _split(lines)
    for line in before:
        if not line.blank:
            problems.append({"recipe": "(before the first recipe)", "kind": "dropped",
                             "detail": f"line not placed anywhere: “{line.plain[:80]}”"})
    for (title_line, body), recipe in zip(chunks, recipes):
        corpus = _corpus(recipe)
        tokens = set(re.findall(r"\w+", corpus))
        for line in body:
            if line.blank:
                continue
            content = _norm(_content_of(line))
            if not content or content in corpus:
                continue
            missing = [w for w in re.findall(r"\w+", content) if w not in tokens]
            if missing:
                problems.append({"recipe": recipe["title"], "kind": "dropped",
                                 "detail": f"line not placed anywhere: “{line.plain[:80]}”"})
    return problems


# --- entry point and report ------------------------------------------------

@dataclass
class Result:
    recipes: list
    problems: list


def parse_document(doc):
    lines = doc_to_lines(doc)
    recipes, problems = _parse(lines)
    problems += check_recipes(recipes)
    problems += apply_cross_links(recipes)
    problems += find_dropped(lines, recipes)
    return Result(recipes, problems)


KIND_ORDER = ["dropped", "empty-ingredients", "empty-directions", "no-steps", "short",
              "copied-step", "cross-link", "guess"]


def format_report(result):
    by_recipe = collections.OrderedDict()
    for p in sorted(result.problems, key=lambda p: KIND_ORDER.index(p["kind"])):
        by_recipe.setdefault(p["recipe"], []).append(p)
    flagged = [t for t, ps in by_recipe.items() if any(p["kind"] not in ("guess", "cross-link") for p in ps)]
    n = len(result.recipes)
    out = [f"Parsed {n} recipe{'s' * (n != 1)}.",
           f"{len(flagged)} recipe{'s' * (len(flagged) != 1)} flagged (flagged recipes still publish)."]
    order = sorted(by_recipe, key=lambda t: (t not in flagged, t.casefold()))
    for title in order:
        out.append("")
        out.append(title)
        for p in by_recipe[title]:
            out.append(f"  - [{p['kind']}] {p['detail']}")
    return "\n".join(out)
