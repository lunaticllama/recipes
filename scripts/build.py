"""Build the site from data/recipes.json.

Usage (from the repo root):
  python scripts/build.py            # design test: only the DESIGN_TEST recipes
  python scripts/build.py --all      # every recipe (from step 9 on)

Writes index.html and assets/search-index.js. Recipe pages come in step 5.
"""
import argparse
import html
import json
import os
import re
import string
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser import plain_text  # noqa: E402

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
    print(f"Built index.html and assets/search-index.js for {len(recipes)} recipes.")


if __name__ == "__main__":
    main()
