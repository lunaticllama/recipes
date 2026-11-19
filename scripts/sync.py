"""Fetch the recipes Google Doc, parse it into data/recipes.json and print the problem report.

Usage (from the repo root):
  python scripts/sync.py                       # fetch with the service account
  python scripts/sync.py --doc-json doc.json   # parse a saved Docs API response instead

The service account key is read from the GOOGLE_SERVICE_ACCOUNT_JSON environment
variable (the key file's contents) or, failing that, from service-account.json.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parser as recipe_parser  # noqa: E402

DOC_ID = "1lwmkqIVbK3HX9ZZRpDlZ7B7TJCTkH3I_yyCPLMZUw0w"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]


def load_key(path):
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        return json.loads(raw)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    sys.exit(f"No service account key: set GOOGLE_SERVICE_ACCOUNT_JSON or create {path}")


def fetch_doc(doc_id, key_info):
    import requests
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(key_info, scopes=SCOPES)
    creds.refresh(Request())
    resp = requests.get(f"https://docs.googleapis.com/v1/documents/{doc_id}",
                        params={"includeTabsContent": "true"},
                        headers={"Authorization": f"Bearer {creds.token}"}, timeout=60)
    resp.raise_for_status()
    return resp.json()


MAX_DROP = 0.10


def previous_count(path):
    """Number of recipes in the current recipes.json, or None if there isn't one."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return len(json.load(f))


def check_count(new, old, allow_drop):
    """Stop if the doc suddenly has far fewer recipes (e.g. a bad edit or a failed read)."""
    if old is None or allow_drop or new >= old * (1 - MAX_DROP):
        return
    sys.exit(f"Safety check failed: the doc now has {new} recipes, down from {old} "
             f"(more than {MAX_DROP:.0%} fewer). Nothing was written or published. "
             "If the recipes were removed on purpose, run again with --allow-drop "
             "(in GitHub: Actions > Sync recipes > Run workflow, tick 'Allow a big drop').")


# --- ignore list and the "Recipe doc check" issue text ---------------------

IGNORE_FILE = os.path.join(REPO, "scripts", "report_ignore.txt")
SITE = "https://recipes.philipmtaylor.com"
LABELS = {
    "count-drop": "Recipe count dropped",
    "dropped": "Line not used",
    "empty-ingredients": "Empty Ingredients",
    "empty-directions": "Empty Directions",
    "no-steps": "No steps",
    "short": "Very short",
    "copied-step": "Copied step",
    "cross-link": "Cross-link",
    "guess": "Check this line",
}


def load_ignores(text):
    """Parse report_ignore.txt: one "Recipe — check" (or "Recipe | check") per line."""
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for sep in (" — ", " | ", " - "):
            if sep in line:
                recipe, kind = line.rsplit(sep, 1)
                entries.append((recipe.strip(), kind.strip()))
                break
    return entries


def read_ignores(path=IGNORE_FILE):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return load_ignores(f.read())


def apply_ignores(problems, ignores):
    """Split problems into (kept, ignored) and list ignore entries that matched nothing."""
    keys = {(recipe_parser._key(r), k.lower()): (r, k) for r, k in ignores}
    used, kept, ignored = set(), [], []
    for p in problems:
        key = (recipe_parser._key(p["recipe"]), p["kind"])
        if key in keys:
            ignored.append(p)
            used.add(key)
        else:
            kept.append(p)
    unused = [entry for key, entry in keys.items() if key not in used]
    return kept, ignored, unused


def _order(p):
    kinds = recipe_parser.KIND_ORDER
    return (p["recipe"].casefold(), kinds.index(p["kind"]) if p["kind"] in kinds else 99, p["detail"])


def report_markdown(problems, recipes, n_recipes):
    """The "Recipe doc check" issue text, or "" when there's nothing to look at.

    Contains no dates, so the text only changes when the problems change.
    """
    if not problems:
        return ""
    slugs = {r["title"]: r["slug"] for r in recipes}
    by_recipe = {}
    for p in sorted(problems, key=_order):
        by_recipe.setdefault(p["recipe"], []).append(p)
    n = len(by_recipe)
    out = [f"The nightly check of the recipes doc found something in {n} recipe"
           f"{'s' if n != 1 else ''}. {'It still publishes' if n == 1 else 'They still publish'}"
           f" ({n_recipes} recipes in the doc).",
           "",
           f"**{n} recipe{' needs' if n == 1 else 's need'} a look**"]
    for title, ps in by_recipe.items():
        out.append("")
        out.append(f"### [{title}]({SITE}/recipes/{slugs[title]}.html)" if title in slugs else f"### {title}")
        out += [f"- **{LABELS.get(p['kind'], p['kind'])}:** {p['detail']}" for p in ps]
    out += ["",
            "---",
            "Fix these in the Google Doc; this issue closes itself once the check is clean. "
            "To leave a flag as it is, add a line like `Pasta Carbonara — copied-step` to "
            "`scripts/report_ignore.txt`."]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc-json", help="parse this saved Docs API JSON instead of fetching")
    ap.add_argument("--doc-id", default=DOC_ID)
    ap.add_argument("--key", default=os.path.join(REPO, "service-account.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "data", "recipes.json"))
    ap.add_argument("--allow-drop", action="store_true",
                    help="write recipes.json even if the recipe count fell more than 10%%")
    ap.add_argument("--check", action="store_true",
                    help="only print the problem report; don't write recipes.json")
    ap.add_argument("--report-md", help="also write the report as Markdown for the GitHub issue "
                                        "(an empty file when there's nothing to look at)")
    args = ap.parse_args(argv)

    if args.doc_json:
        with open(args.doc_json, encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = fetch_doc(args.doc_id, load_key(args.key))

    result = recipe_parser.parse_document(doc)
    kept, ignored, unused = apply_ignores(result.problems, read_ignores())
    old = previous_count(args.out)
    if args.check:
        try:
            check_count(len(result.recipes), old, args.allow_drop)
        except SystemExit as e:
            kept.append({"recipe": "(whole doc)", "kind": "count-drop", "detail": str(e)})

    print(recipe_parser.format_report(recipe_parser.Result(result.recipes, kept)))
    if ignored:
        print(f"\nIgnored (listed in scripts/report_ignore.txt): "
              + "; ".join(f"{p['recipe']} — {p['kind']}" for p in ignored))
    if unused:
        print("\nThese report_ignore.txt entries no longer match anything and can be removed: "
              + "; ".join(f"{r} — {k}" for r, k in unused))
    if args.report_md:
        with open(args.report_md, "w", encoding="utf-8", newline="\n") as f:
            f.write(report_markdown(kept, result.recipes, len(result.recipes)))
    if args.check:
        return

    check_count(len(result.recipes), old, args.allow_drop)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result.recipes, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {len(result.recipes)} recipes to {os.path.relpath(args.out, REPO)}")


if __name__ == "__main__":
    main()
