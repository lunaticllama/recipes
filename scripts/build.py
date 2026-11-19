"""Build the site from data/recipes.json.

Usage (from the repo root):
  python scripts/build.py            # design test: only the DESIGN_TEST recipes
  python scripts/build.py --all      # every recipe (from step 9 on)

Writes index.html, assets/search-index.js and recipes/<slug>.html, and deletes
recipe pages for recipes that are no longer being built.
"""
import argparse
import html
import itertools
import json
import os
import re
import string
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser import MD_LINK, plain_text  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# The recipes on the site during the design test (plan step 5).
DESIGN_TEST = [
    "adana-kebab", "falafel", "jerk-chicken", "tofu-stir-fry",
    "general-tsos-stir-fry", "thai-noodle-bowls-with-tofu-and-veggies",
]
LETTERS = list(string.ascii_uppercase)


def esc(s):
    return html.escape(s, quote=True)


def select(recipes, slugs):
    by_slug = {r["slug"]: r for r in recipes}
    missing = [s for s in slugs if s not in by_slug]
    if missing:
        sys.exit(f"Design-test recipes not found in recipes.json: {', '.join(missing)}")
    return [r for r in recipes if r["slug"] in set(slugs)]


# --- search index ----------------------------------------------------------

def search_entries(recipes):
    return [{"title": r["title"], "slug": r["slug"],
             "ingredients": [plain_text(i) for s in r["sections"]
                             for g in s["ingredient_groups"] for i in g["items"]]}
            for r in recipes]


def search_index_js(recipes):
    data = json.dumps(search_entries(recipes), ensure_ascii=False, separators=(",", ":"))
    return f"window.RECIPES = {data};\n"


# --- index page ------------------------------------------------------------

def letter_of(title):
    folded = unicodedata.normalize("NFKD", title)
    for ch in folded:
        if ch.isalpha() and ch.isascii():
            return ch.upper()
        if ch.isdigit():
            return "#"
    return "#"


def _sort_key(title):
    return unicodedata.normalize("NFKD", re.sub(r"[\"'“”‘’]", "", title)).casefold()


def group_by_letter(recipes):
    groups = {}
    for r in sorted(recipes, key=lambda r: _sort_key(r["title"])):
        groups.setdefault(letter_of(r["title"]), []).append(r)
    return dict(sorted(groups.items(), key=lambda kv: (kv[0] == "#", kv[0])))


def render_index(recipes):
    groups = group_by_letter(recipes)
    letters = LETTERS + (["#"] if "#" in groups else [])
    buttons = []
    for letter in letters:
        if letter in groups:
            buttons.append(f'      <button type="button" class="az-letter" data-letter="{letter}" '
                           f'aria-pressed="false" aria-controls="letter-{letter}">{letter}</button>')
        else:
            buttons.append(f'      <button type="button" class="az-letter" data-letter="{letter}" '
                           f'disabled aria-label="{letter}: no recipes">{letter}</button>')
    lists = []
    for letter, rs in groups.items():
        items = "\n".join(f'        <li><a href="recipes/{esc(r["slug"])}.html">{esc(r["title"])}</a></li>'
                          for r in rs)
        lists.append(f'    <section class="az-list" id="letter-{letter}" aria-label="Recipes starting with {letter}">\n'
                     f'      <h2 class="az-heading">{letter}</h2>\n'
                     f'      <ul class="results-list">\n{items}\n      </ul>\n    </section>')
    with open(os.path.join(TEMPLATES, "index.html"), encoding="utf-8") as f:
        page = f.read()
    return page.replace("{{LETTERS}}", "\n".join(buttons)).replace("{{LISTS}}", "\n".join(lists))


# --- recipe pages ----------------------------------------------------------

def render_rich(text, built):
    """Escape a rich-text string and turn its [text](url) links into <a> tags.

    recipe:<slug> links become relative page links, but only to pages being built.
    """
    out, pos = [], 0
    for m in MD_LINK.finditer(text):
        out.append(esc(text[pos:m.start()]))
        label, url = m.group(1), m.group(2)
        if url.startswith("recipe:"):
            slug = url[len("recipe:"):]
            out.append(f'<a href="{esc(slug)}.html">{esc(label)}</a>' if slug in built else esc(label))
        elif re.match(r"https?://", url):
            out.append(f'<a href="{esc(url)}">{esc(label)}</a>')
        else:
            out.append(esc(label))
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out)


def paragraphs(text, built):
    return "".join(f"<p>{render_rich(p, built)}</p>" for p in text.split("\n") if p.strip())


def short_url(url):
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


def _notes_html(notes, built, indent):
    out = []
    for n in notes:
        title = esc(n.get("name") or "Note")
        out.append(f'{indent}<div class="note"><h4 class="group-title">{title}</h4>'
                   f'{paragraphs(n["text"], built)}</div>')
    return out


def _section_html(sec, built, counter):
    groups = [g for g in sec["ingredient_groups"] if g["items"]]
    if not (groups or sec["steps"] or sec["notes"]):
        return ""
    cols = []
    if groups:
        rows = ['        <section class="ingredients">',
                '          <h3 class="section-title">Ingredients</h3>']
        for g in groups:
            rows.append('          <div class="ingredient-group">')
            if g.get("name"):
                rows.append(f'            <h4 class="group-title">{esc(g["name"])}</h4>')
            for item in g["items"]:
                n = next(counter)
                rows.append(f'            <div class="check"><input id="ing-{n}" type="checkbox">'
                            f'<label for="ing-{n}">{render_rich(item, built)}</label></div>')
            rows.append("          </div>")
        rows.append("        </section>")
        cols += rows
    if sec["steps"] or sec["notes"]:
        rows = ['        <section class="directions">']
        if sec["steps"]:
            rows.append('          <h3 class="section-title">Directions</h3>')
            rows.append('          <ol class="steps">')
            rows += [f'            <li><div class="step-text">{paragraphs(s, built)}</div></li>'
                     for s in sec["steps"]]
            rows.append("          </ol>")
        rows += _notes_html(sec["notes"], built, "          ")
        rows.append("        </section>")
        cols += rows
    head = ['    <section class="recipe-section">']
    if sec.get("name"):
        head.append(f'      <h2 class="sub-title">{esc(sec["name"])}</h2>')
    return "\n".join(head + ['      <div class="recipe-body">'] + cols + ["      </div>", "    </section>"])


def _footer_html(recipe, built):
    parts = []
    if recipe["notes"]:
        parts += ['      <section class="recipe-notes">',
                  '        <h3 class="section-title">Notes</h3>']
        parts += _notes_html(recipe["notes"], built, "        ")
        parts.append("      </section>")
    if recipe["sources"]:
        heading = "Source" if len(recipe["sources"]) == 1 else "Sources"
        parts += ['      <section class="sources">',
                  f'        <h3 class="section-title">{heading}</h3>',
                  '        <ul class="source-list">']
        for s in recipe["sources"]:
            if s.get("url"):
                text = short_url(s["url"]) if s["text"] == s["url"] else s["text"]
                parts.append(f'          <li><a href="{esc(s["url"])}">{esc(text)}</a></li>')
            else:
                parts.append(f"          <li>{esc(s['text'])}</li>")
        parts += ["        </ul>", "      </section>"]
    if not parts:
        return ""
    return "\n".join(['    <footer class="recipe-foot">'] + parts + ["    </footer>"])


def render_recipe(recipe, built):
    counter = itertools.count(1)
    blocks = [_section_html(s, built, counter) for s in recipe["sections"]]
    blocks.append(_footer_html(recipe, built))
    with open(os.path.join(TEMPLATES, "recipe.html"), encoding="utf-8") as f:
        page = f.read()
    return (page.replace("{{BODY}}", "\n".join(b for b in blocks if b))
                .replace("{{DESCRIPTION}}", esc(f"Phil’s recipe for {recipe['title']}."))
                .replace("{{TITLE}}", esc(recipe["title"]))
                .replace("{{SLUG}}", esc(recipe["slug"])))


# --- main ------------------------------------------------------------------

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "data", "recipes.json"))
    ap.add_argument("--out", default=REPO)
    ap.add_argument("--all", action="store_true", help="build every recipe, not just the design test")
    ap.add_argument("--only", help="comma-separated slugs to build instead of the design-test list")
    args = ap.parse_args(argv)

    with open(args.data, encoding="utf-8") as f:
        recipes = json.load(f)
    if not args.all:
        recipes = select(recipes, args.only.split(",") if args.only else DESIGN_TEST)

    write(os.path.join(args.out, "index.html"), render_index(recipes))
    write(os.path.join(args.out, "assets", "search-index.js"), search_index_js(recipes))
    built = {r["slug"] for r in recipes}
    pages = os.path.join(args.out, "recipes")
    for r in recipes:
        write(os.path.join(pages, f"{r['slug']}.html"), render_recipe(r, built))
    removed = [f for f in os.listdir(pages) if f.endswith(".html") and f[:-5] not in built]
    for f in removed:
        os.remove(os.path.join(pages, f))
    print(f"Built index.html, assets/search-index.js and {len(recipes)} recipe pages"
          + (f"; removed {len(removed)} old page(s)." if removed else "."))


if __name__ == "__main__":
    main()
