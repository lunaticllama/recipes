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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc-json", help="parse this saved Docs API JSON instead of fetching")
    ap.add_argument("--doc-id", default=DOC_ID)
    ap.add_argument("--key", default=os.path.join(REPO, "service-account.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "data", "recipes.json"))
    ap.add_argument("--allow-drop", action="store_true",
                    help="write recipes.json even if the recipe count fell more than 10%%")
    args = ap.parse_args(argv)

    if args.doc_json:
        with open(args.doc_json, encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = fetch_doc(args.doc_id, load_key(args.key))

    result = recipe_parser.parse_document(doc)
    print(recipe_parser.format_report(result))
    check_count(len(result.recipes), previous_count(args.out), args.allow_drop)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result.recipes, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {len(result.recipes)} recipes to {os.path.relpath(args.out, REPO)}")


if __name__ == "__main__":
    main()
