"""Build the site from data/recipes.json.

Usage (from the repo root):
  python scripts/build.py                     # every recipe
  python scripts/build.py --only falafel,steak  # just these (for testing)

Writes index.html, assets/search-index.js and recipes/<slug>.html, deletes
recipe pages for recipes that are no longer in the doc, then fails if any link
between pages points to a page that doesn't exist.
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

LETTERS = list(string.ascii_uppercase)


def esc(s):
    return html.escape(s, quote=True)


def select(recipes, slugs):
    by_slug = {r["slug"]: r for r in recipes}
    missing = [s for s in slugs if s not in by_slug]
    if missing:
        sys.exit(f"Recipes not found in recipes.json: {', '.join(missing)}")
    return [r for r in recipes if r["slug"] in set(slugs)]


# --- search index ----------------------------------------------------------

def search_entries(recipes):
    return [{"title": r["title"], "slug": r["slug"],
             "ingredients": [plain_text(i) for s in r["sections"]
                             for g in s["ingredient_groups"] for i in g["items"]],
             "tags": r.get("tags", [])}
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


def _notes_html(notes, built, indent, under_notes_heading=False):
    out = []
    for n in notes:
        name = n.get("name") or "Note"
        # Under a "Notes" heading, a label that just says "Note" adds nothing.
        label = "" if under_notes_heading and name.lower() in ("note", "notes") else             f'<h4 class="group-title">{esc(name)}</h4>'
        out.append(f'{indent}<div class="note">{label}{paragraphs(n["text"], built)}</div>')
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
        parts += _notes_html(recipe["notes"], built, "        ", under_notes_heading=True)
        parts.append("      </section>")
    # Tags and sources share one column, tags first.
    tags = recipe.get("tags") or []
    sources = recipe["sources"]
    if tags or sources:
        parts.append('      <section class="recipe-meta">')
        if tags:
            heading = "Tag" if len(tags) == 1 else "Tags"
            parts += ['        <div class="tags">',
                      f'          <h3 class="section-title">{heading}</h3>',
                      '          <ul class="tag-list">']
            parts += [f"            <li>{esc(t)}</li>" for t in tags]
            parts += ["          </ul>", "        </div>"]
        if sources:
            heading = "Source" if len(sources) == 1 else "Sources"
            parts += ['        <div class="sources">',
                      f'          <h3 class="section-title">{heading}</h3>',
                      '          <ul class="source-list">']
            for s in sources:
                if s.get("url"):
                    text = short_url(s["url"]) if s["text"] == s["url"] else s["text"]
                    parts.append(f'            <li><a href="{esc(s["url"])}">{esc(text)}</a></li>')
                else:
                    parts.append(f"            <li>{esc(s['text'])}</li>")
            parts += ["          </ul>", "        </div>"]
        parts.append("      </section>")
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


LOCAL_HREF = re.compile(r'href="(?![a-z][a-z0-9+.-]*:|#|//)([^"#?]+\.html)')


def broken_links(out):
    """Return (page, href) for every link between pages whose target page is missing."""
    pages = [os.path.join(out, "index.html")]
    rec_dir = os.path.join(out, "recipes")
    if os.path.isdir(rec_dir):
        pages += [os.path.join(rec_dir, f) for f in sorted(os.listdir(rec_dir)) if f.endswith(".html")]
    broken = []
    for page in pages:
        with open(page, encoding="utf-8") as f:
            text = f.read()
        for href in LOCAL_HREF.findall(text):
            target = os.path.normpath(os.path.join(os.path.dirname(page), html.unescape(href)))
            if not os.path.exists(target):
                broken.append((os.path.relpath(page, out).replace(os.sep, "/"), href))
    return broken


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "data", "recipes.json"))
    ap.add_argument("--out", default=REPO)
    ap.add_argument("--only", help="comma-separated slugs to build instead of every recipe (for testing)")
    args = ap.parse_args(argv)

    with open(args.data, encoding="utf-8") as f:
        recipes = json.load(f)
    if args.only:
        recipes = select(recipes, args.only.split(","))

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
    broken = broken_links(args.out)
    if broken:
        sys.exit("Broken links:\n" + "\n".join(f"  {page} -> {href}" for page, href in broken))


if __name__ == "__main__":
    main()
