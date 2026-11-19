# Phil's Recipes

The recipe site at **[recipes.philipmtaylor.com](https://recipes.philipmtaylor.com)**, built from the
"Phil's Recipes" Google Doc.

Phil edits the Google Doc as usual. Every night a GitHub Action reads the doc, turns each recipe
into a page, and publishes any changes. Nothing on the site needs editing by hand.

- [How it works](#how-it-works)
- [One-time setup](#one-time-setup)
  - [1. Google Cloud project and service account](#1-google-cloud-project-and-service-account)
  - [2. Share the doc with the service account](#2-share-the-doc-with-the-service-account)
  - [3. Add the GitHub secret](#3-add-the-github-secret)
  - [4. The web address (DNS and GitHub Pages)](#4-the-web-address-dns-and-github-pages)
- [Formatting recipes in the doc](#formatting-recipes-in-the-doc)
- [The doc check and the "Recipe doc check" issue](#the-doc-check-and-the-recipe-doc-check-issue)
- [If the nightly run fails](#if-the-nightly-run-fails)
- [Running it on your own PC (Windows)](#running-it-on-your-own-pc-windows)
- [What's in this repo](#whats-in-this-repo)

---

## How it works

1. **Every night at about 3 AM Eastern** (08:00 UTC, so 4 AM in summer), the **Sync recipes**
   workflow reads the doc using a Google *service account*: a robot Google account that has
   view-only access to this one doc.
2. It turns the doc into `data/recipes.json`, prints a **problem report**, and updates the
   **"Recipe doc check"** issue if there's anything to look at.
3. It runs the tests, rebuilds `index.html` and the pages in `recipes/`, and commits and pushes
   only if something changed. GitHub Pages then publishes the new version within a minute or two.
4. **Safety check:** if the doc suddenly has more than 10% fewer recipes than the last published
   version, the run stops and publishes nothing (see [If the nightly run fails](#if-the-nightly-run-fails)).

You can also run either workflow yourself from the **Actions** tab on GitHub (this works on a phone):

| Workflow | What it does |
|---|---|
| **Sync recipes** | The nightly job: sync, build and publish. Use it to publish an edit right away. |
| **Check recipe doc** | Only checks the doc and updates the "Recipe doc check" issue. Builds and publishes nothing. Use it right after adding a recipe. |

To start one: **Actions** → pick the workflow on the left → **Run workflow** → **Run workflow**.

---

## One-time setup

You only do this once. It takes about 15 minutes. Steps 1–3 connect the nightly sync to the doc;
step 4 is the web address, which is already done.

### 1. Google Cloud project and service account

Do this signed in to Google as the account that owns the recipes doc. No credit card or billing
is needed: the Google Docs API is free at this scale.

1. **Create a project.** Go to [console.cloud.google.com](https://console.cloud.google.com). In the
   project picker at the top, choose **New project**. Name it `phils-recipes` and click **Create**.
   Make sure the new project is selected in the picker before going on.
2. **Turn on the Google Docs API.** Go to **APIs & Services → Library**, search for
   **Google Docs API**, open it, and click **Enable**.
3. **Create the service account.** Go to **IAM & Admin → Service Accounts** and click
   **Create service account**.
   - Service account name: `recipes-sync`
   - Click **Create and continue**. Skip the "Grant this service account access" and
     "Grant users access" steps (it needs no roles; it only reads the one doc you share with it).
   - Click **Done**.
4. **Copy its email address.** In the list, it looks like
   `recipes-sync@<project-id>.iam.gserviceaccount.com`. You'll need it in step 2.
   (Google may change the project ID a little if the name is taken; this project's is
   `phils-recipe`, so the address is `recipes-sync@phils-recipe.iam.gserviceaccount.com`.)
5. **Create a key.** Click the service account, open the **Keys** tab, and choose
   **Add key → Create new key → JSON → Create**. A `.json` file downloads. This file is the
   service account's password: don't email it, share it or commit it.

> If key creation is blocked with a message about an organization policy, the Google account
> belongs to a Google Workspace organization that forbids keys. Personal Gmail accounts aren't
> affected.

### 2. Share the doc with the service account

1. Open the "Phil's Recipes" doc and click **Share**.
2. Paste the service account's email address, set it to **Viewer**, untick **Notify people**,
   and click **Share**.

The service account can now read this doc and nothing else in your Google account.

### 3. Add the GitHub secret

The nightly run reads the key from a GitHub secret, which is encrypted and never shown in logs.

1. On GitHub, open the repo and go to **Settings → Secrets and variables → Actions**.
2. Click **New repository secret**.
   - Name: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - Secret: open the downloaded `.json` file in Notepad, select everything, and paste it in.
3. Click **Add secret**.

(Or, from the repo folder: `gh secret set GOOGLE_SERVICE_ACCOUNT_JSON < path\to\key.json`.)

To run the sync on your own PC as well, save the key file in the repo folder as
**`service-account.json`**. `.gitignore` keeps it out of git. Then delete the downloaded copy
from your Downloads folder.

**Check that it works:** Actions → **Sync recipes** → **Run workflow**. After a minute or two the
run should finish with a green tick. Open it and expand **Sync the doc** to see the problem report.

Until the secret exists, the nightly run skips itself with a yellow warning instead of failing.

**Replacing the key** (if it may have leaked, or every few years): create a new key as in
step 1.5, update the GitHub secret and your local `service-account.json`, then delete the old
key on the service account's **Keys** tab.

### 4. The web address (DNS and GitHub Pages)

Already done; this is here for reference.

- The repo's `CNAME` file holds `recipes.philipmtaylor.com`. GitHub Pages serves the site from the
  root of the `main` branch (**Settings → Pages**).
- At GoDaddy (the DNS host for philipmtaylor.com) there's one record:

  | Type | Name | Value |
  |---|---|---|
  | CNAME | `recipes` | `lunaticllama.github.io` |

- Once GitHub has issued the https certificate, **Settings → Pages → Enforce HTTPS** is ticked.
  "Keep screen on" only works over https.

---

## Formatting recipes in the doc

The parser is forgiving, but it relies on a few conventions. Here's a recipe with everything in it:

```
Steak                                  ← recipe title, in the Heading 2 style
Ingredients:
Steaks, I prefer New York Strip Steak
Salt and black pepper

Directions:
1.  Thoroughly dry steaks with paper towels.
    Extra lines without a number continue the step above.
2.  Heat a cast iron pan until very hot.

Asian Marinade                         ← a sub-recipe: a short name, then "Ingredients:"
Ingredients:
¼ cup soy sauce

Directions:
1.  Mix all of the marinade ingredients together.

Note: Great on the grill too.          ← a note (Note:, Variations:, Alternative:)
Source: <link to the original recipe>  ← Source:, Sources:, Recipe: or Based off of this:
```

**Titles.** Each recipe starts with its title as a heading (currently **Heading 2**; the parser
uses whichever heading style the titles have, so changing it later is fine). The title becomes the
page address: "Pulled Pork" → `/recipes/pulled-pork.html`. **Renaming a recipe changes its address**
and the old address stops working.

**Ingredients.** Start with `Ingredients:`. To split them into groups, put a line ending in a colon
before each group: `For the Dough:`, `Sauce:`, `Pork Ingredients:`. A blank line inside the list
starts a new, unnamed group. A colon in the *middle* of a line ("Both optional: a pinch of
cayenne") is fine and doesn't start a group.

**Directions.** Start with `Directions:` (or `Instructions:`; a name in front, like
`General Tso's Special Directions:`, is fine). Number the steps `1.`, `2.`… or use a Docs numbered
list; they're renumbered on the site anyway. Lines without a number belong to the step above.
If the directions are a single paragraph with no number, that paragraph becomes one step.

**Sub-recipes** (a sauce, a dough, a variation with its own ingredients) go **after** the main
steps: a short name on its own line (with or without a colon), then `Ingredients:` on the next
line. They appear on the same page under their own heading, never as separate recipes.

**Notes.** `Note:`, `Notes:`, `Variations:` or `Alternative:`, with the text on the same line or
the lines below. A short name ending in a colon after the steps (`Chicken Variation:`) followed by
plain text also becomes a named note. If it's followed by numbered lines instead, it becomes a
small section with steps (like Cabbage Slaw's "Simple version:").

**Sources.** `Source:`, `Sources:`, `Recipe:` or `Based off of this:`, followed by links or text,
on the same line or the lines below. Links keep their real target, so linked text like
"Breadsticks - Preppy Kitchen" stays clickable.

**Tags.** Add a line like `Tags: thanksgiving, holiday, side dish` anywhere in the recipe (the
end is a good place). Separate tags with commas and leave out `#`. Search finds recipes by their
tags; the tags aren't shown on the pages yet.

**Soft line breaks** (Shift+Enter), blank lines and stray punctuation-only lines are all fine.

**Links between recipes** are a fixed list in `CROSS_LINKS` in `scripts/parser.py` (for example,
the BBQ sauce in Pulled Pork's ingredients links to the BBQ Sauce recipe). To add one, add a line
there: the recipe it appears in, the exact phrase to link, and the recipe it points to. If a
recipe in that list is renamed, the doc check says the link was skipped.

---

## The doc check and the "Recipe doc check" issue

Every sync (and every **Check recipe doc** run) prints a problem report. If there's anything in
it, the workflow opens a GitHub issue called **"Recipe doc check"**, and GitHub emails you. When
the report changes, the new version is posted as a comment (which also emails you). When the doc
is clean again, the issue closes itself. **Flagged recipes still publish**; the report just tells
you what to tidy up.

What the checks mean:

| In the report | In the issue | What it means and how to fix it |
|---|---|---|
| `[empty-ingredients]` | Empty Ingredients | An `Ingredients:` label with nothing under it. |
| `[empty-directions]` | Empty Directions | A `Directions:` label with nothing under it. |
| `[no-steps]` | No steps | The recipe has no directions at all. |
| `[short]` | Very short | Fewer than 25 words of ingredients and steps; often a recipe that's not finished. |
| `[copied-step]` | Copied step | A step is word-for-word the same as a step in another recipe; sometimes a copy-and-paste slip. |
| `[cross-link]` | Cross-link | A link between recipes couldn't be made, usually because a recipe was renamed. |
| `[dropped]` | Line not used | A line the parser couldn't place anywhere. Shouldn't happen; check the formatting around it. |
| `[guess]` | Check this line | The parser had to guess, e.g. a mistyped step number ("3," for "3."), two ingredients run together on one line, or a sentence sitting in an ingredient list. The text says which line. |

**Leaving a flag as it is.** Some flags are fine as they are (Pasta Carbonara shares a step with
Pasta Broccoli Bolognese on purpose). Add a line to **`scripts/report_ignore.txt`** with the
recipe title and the check name from the brackets:

```
Pasta Carbonara — copied-step
```

You can edit the file right on GitHub (open it → pencil icon → **Commit changes**). Ignored flags
still appear in the run log, and the log points out entries that no longer match anything.

---

## If the nightly run fails

GitHub emails you when a scheduled run fails. Open **Actions → Sync recipes**, click the failed
run, and expand the step with the red ✗.

**"Safety check failed: the doc now has N recipes, down from M"**: the doc had more than 10%
fewer recipes than the last published version, so nothing was written or published. The site
stays as it was.
- If recipes were deleted or the doc was damaged by mistake, restore them (in Google Docs,
  **File → Version history** helps). The next run publishes normally.
- If you removed them on purpose: **Actions → Sync recipes → Run workflow**, tick
  **Allow a big drop**, and **Run workflow**. That publishes the smaller set once; later runs
  compare against it.

**A 403 or "permission" error in "Sync the doc"**: the doc isn't shared with the service account,
or the Google Docs API isn't enabled for the project. Redo [setup steps 1.2 and 2](#one-time-setup).

**A 401, "invalid_grant" or "No service account key"**: the GitHub secret is missing or the key
was deleted. Create a new key and update the secret ([step 3](#3-add-the-github-secret)).

**"Run the parser tests" failed**: the code is broken, not the doc. Nothing is published.

**"Broken links" in "Build the pages"**: a link between pages points to a page that doesn't exist.
The log lists them. Nothing is published.

**Nightly runs stopped.** In a public repo, GitHub turns off scheduled workflows after **60 days
without a commit**. If the doc doesn't change for two months, nothing gets committed and GitHub
emails you a warning. To turn it back on: **Actions → Sync recipes → Enable workflow** (or run it
once by hand).

---

## Running it on your own PC (Windows)

You need Python 3.12 or newer and the repo cloned to `C:\Users\Phil\Documents\GitHub\recipes`.
Open a terminal in that folder.

```powershell
py -m pip install -r scripts\requirements.txt      # once

py scripts\sync.py --check     # just print the problem report; changes nothing
py scripts\sync.py             # read the doc and update data\recipes.json
py scripts\build.py            # rebuild index.html and recipes\*.html
py -m unittest discover -s scripts/tests -t scripts   # run the tests
```

`sync.py` needs the key in `service-account.json` in the repo folder (see
[step 3](#3-add-the-github-secret)). To preview the site, open `index.html` in a browser.
To publish, commit and push the changes (or just let the nightly run do it).

Other options:
- `py scripts\sync.py --allow-drop` — write `recipes.json` even if the safety check fails.
- `py scripts\build.py --only falafel,steak` — build just those pages (for testing).

---

## What's in this repo

```
index.html                      landing page: search and A–Z (generated)
recipes/<name>.html             one page per recipe (generated)
assets/style.css                the site design
assets/recipes.js               search, A–Z, Print and "Keep screen on"
assets/fuse.min.js              fuzzy-search library (Fuse.js 7.0.0)
assets/search-index.js          titles and ingredients for search (generated)
data/recipes.json               the parsed recipes (generated)
scripts/sync.py                 read the doc → recipes.json → problem report
scripts/parser.py               the parsing rules and cross-links (no network)
scripts/build.py                recipes.json → the HTML pages, then checks the links
scripts/update_issue.sh         opens, updates or closes the "Recipe doc check" issue
scripts/report_ignore.txt       doc-check flags to leave as they are
scripts/templates/              page templates
scripts/tests/                  tests, using snippets of the real doc
.github/workflows/              the nightly sync and the on-demand doc check
CNAME                           the custom web address
PLAN.md                         the project plan
```

The "generated" files are rewritten on every build, so don't edit them by hand; change the doc,
the templates or the scripts instead.
