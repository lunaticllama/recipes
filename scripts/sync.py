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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc-json", help="parse this saved Docs API JSON instead of fetching")
    ap.add_argument("--doc-id", default=DOC_ID)
    ap.add_argument("--key", default=os.path.join(REPO, "service-account.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "data", "recipes.json"))
    args = ap.parse_args(argv)

    if args.doc_json:
        with open(args.doc_json, encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = fetch_doc(args.doc_id, load_key(args.key))

    result = recipe_parser.parse_document(doc)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result.recipes, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(recipe_parser.format_report(result))
    print(f"\nWrote {len(result.recipes)} recipes to {os.path.relpath(args.out, REPO)}")


if __name__ == "__main__":
    main()
