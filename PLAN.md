# Phil's Recipes: Plan

**Status:** Step 1 done (repo created and cloned). Next: Step 2.

## 1. Where it lives
- **Repo:** a new public repo, `lunaticllama/recipes`, created with the `gh` command-line tool and cloned to `C:\Users\Phil\Documents\GitHub\recipes`.
- **Address:** `recipes.philipmtaylor.com`. The repo gets a `CNAME` file, and Phil adds one DNS record at the registrar (`recipes` → `lunaticllama.github.io`). GitHub Pages serves the site from the root of `main`.
- **Separation:** nothing changes in `lunaticllama.github.io`, and the professional site won't link to the recipes for now.
- **Public during development:** the site goes live at step 6, with only the test pages, and stays visible while we work on the design.
- **Why public:** GitHub Pages only serves private repos on a paid plan.

## 2. Repo layout
```
index.html                       ← landing page
recipes/<name>.html              ← one page per recipe (112, generated)
assets/style.css                 ← Phil's style.css + additions
assets/recipes.js                ← search, A–Z, "Keep screen on"
assets/fuse.min.js               ← fuzzy-search library, saved in the repo
data/recipes.json                ← parsed recipes
scripts/sync.py                  ← fetch doc → recipes.json → report
scripts/parser.py                ← parsing rules, no network calls
scripts/build.py                 ← recipes.json → HTML pages
scripts/templates/recipe.html    ← page template from the mockup
scripts/tests/                   ← parser tests + real doc snippets
scripts/requirements.txt         ← google-auth, requests
.github/workflows/sync-recipes.yml
.gitignore                       ← includes the key file
README.md                        ← setup guide
PLAN.md                          ← this file
CNAME
```

## 3. Source doc and access
- **Doc:** "Phil's Recipes", ID `1lwmkqIVbK3HX9ZZRpDlZ7B7TJCTkH3I_yyCPLMZUw0w`, 112 recipes.
- **Recipe boundaries:** the titles are currently Heading 2. The parser uses whatever heading level the titles have, so changing that later won't break it.
- **During the build:** the doc is read through Phil's connected Google Docs account, read-only.
- **Nightly runs:** the Action uses a service account, with its key stored as the GitHub secret `GOOGLE_SERVICE_ACCOUNT_JSON`. The doc is shared with the service account's email, view-only.
- **Running it locally:** the key goes in a file, `service-account.json`, which is listed in `.gitignore` and never committed.

## 4. Doc edits for Phil to make (in step 3)
**Needed: add a colon at the end of each of these lines.**

| Recipe | Lines |
|---|---|
| Basic Roast Fish | Watercress Sauce for Fish |
| Lamb & Beet Pot Pie | Yogurt Pie Crust, Pie Filling |
| Steak | Spicy Fennel Steak |
| Tofu Stir Fry | Basic Stir Fry Sauce, Hot and Sour Sauce, General Tso's Variation, General Tso's Sauce, Tofu, Stir Fry |
| Zucchini Fritters | Simple Tzatziki Sauce |

**Optional:**
- **Moussaka:** its one step is copied from Moroccan Grilled Chicken.
- **Braised Lamb Shanks:** has no steps.
- **Bigos and Pumpkin Ravioli:** have no directions.
- **Paella:** moving the Salmorra block below the main Directions, with "Directions:" before its cooking sentence, makes it a proper sub-recipe.
- **Pasta Broccoli Bolognese:** has two step 3s.
- **Pulled Pork:** "(recipe below)" could become "(see recipe)".

## 5. Parser rules
- **Cleanup:** strip zero-width characters, split paragraphs at soft line breaks (Shift+Enter), and ignore blank lines and punctuation-only lines.
- **Labels:**
  - Recognized labels: Ingredients, Directions or Instructions (colon optional), Source or Sources, Recipe:, Based off of this:, Note, Variations, Alternative and Tags.
  - Lines ending in "…Directions:" or "…Source:" count as those labels too.
  - A colon in the middle of a line, as in "Both optional: Pinch cayenne", does not make it a label.
- **Ingredient groups:** before a section's directions, lines ending in a colon are group names. That covers "For the Kebabs:", "Pork Ingredients:", "For the Dough:" and the others.
- **Sub-recipes:** they appear as named sections inside the parent recipe, never as separate recipes. A sub-recipe starts at either of:
  - a label that comes after directions have begun
  - a short line on its own followed by an Ingredients label, such as "Asian Marinade" or "Kimchi Quesadillas"
- **Steps:**
  - Typed numbers (`1.\t`, `1. `, `3\t.`) and real Docs lists both count, and steps are renumbered in order.
  - Unnumbered lines continue the previous step.
  - If a Directions section has no numbered lines, its text becomes a single step.
  - Numbered lines with no Directions label count as directions.
  - More than one Directions section is supported.
- **Short text-only variations** become named notes: Chicken Variation, Optional protein addition, Simple Soy Sauce and similar.
- **Sources** are saved as text plus a link, using the real hyperlink targets from the doc, so linked text like "Breadsticks - Preppy Kitchen" stays clickable. Plain-text sources are kept as text.
- **Nothing is dropped:** long sentences sitting inside ingredient lists, and anything else the parser can't place, go to notes.
- **Tags:** a "Tags:" line is saved if one ever appears. No tag filter on the site for now.

## 6. What `recipes.json` holds for each recipe
`slug`, `title`, `sections[]` (each with an optional `name`, `ingredient_groups[]` (optional `name` plus `items[]`), `steps[]` and `notes[]`), `sources[]` (text plus an optional URL), `notes[]` and `tags[]`.

## 7. Problem report
It's printed on every run and appears in the Action's log. It flags:
- an empty Ingredients section
- an empty Directions section
- no steps
- an unusually short recipe
- lines where the parser guessed

Before the doc edits it should flag Moussaka, Bigos, Pumpkin Ravioli and Braised Lamb Shanks. Each one stops being flagged once it's fixed in the doc. Flagged recipes still publish.

## 8. The site
- **Design:** Phil's `recipe.html` and `style.css`, unchanged, including the DM Serif Display and DM Sans fonts. Matching styles are added for sub-recipe headings, sources and notes. On phones, ingredients stack above the steps as in the mockup, with no sticky panel.
- **Landing page (`index.html`):** the title, the search box, and an A–Z row.
  - Clicking a letter lists the recipes starting with it, by name. Letters with no recipes are greyed out.
  - While you type, matching recipes replace the A–Z list.
  - **During the design test:** the search and A–Z list cover only the 5 test recipes, so every link works. They switch to all 112 recipes in step 9.
- **Search:** fuzzy, so typos still match. It covers titles and all ingredients, including sub-recipe ingredients, and will cover tags once they exist.
- **Recipe pages (`/recipes/<name>.html`):**
  - The same header and search box. Results appear only while typing, with the current recipe in bold.
  - The "Phil's Recipes" title links back home.
  - The ingredient checklist, numbered steps, sub-recipe sections, and clickable sources and notes.
- **Cross-links** (the only ones):
  - Pulled Pork ↔ Traditional "Sweet and Tangy" BBQ Sauce
  - Basic Curry → Tofu Stir Fry
  - Quesadillas → Kale, Poblano, and Black Bean Tacos
  - Buffalo Chicken Dip → Blue Cheese Dressing
  - Pasta Broccoli Bolognese → Italian Sausage
  - Korean Spicy Beef Soup, Phil's Chinese Cabbage, Taiwanese Spicy Beef Soup and Yucatan Shrimp → Chili Oil
  - **Not linked:** Korean Spicy Beef Soup → Beef Stock, and anything to Pancakes.
- **"Keep screen on":** keeps the phone's screen awake while a recipe is open. The button is hidden on browsers that don't support it.
- **Print:** the print styles from the mockup print just the recipe, without the header, search or buttons.
- **Search engines:** the pages can show up in Google (no `noindex`).
- **Page addresses:** each one comes from the recipe title. Renaming a recipe changes its address and the old one stops working; there are no redirects.

## 9. Nightly GitHub Action
- **When it runs:** every night at about 3 AM ET, and whenever started from the Actions tab.
- **Steps:** sync the doc, run the parser tests, build the pages, then commit to `main` and push. It commits only when something changed and deletes pages for recipes removed from the doc.
- **Safety check:** if the recipe count falls more than 10% below the count in the committed `recipes.json` (currently 112), the run fails and nothing is published.

## 10. Tests
Python's built-in `unittest`, using snippets from the real doc:
- labelled ingredient groups (Adana Kebab, Pulled Pork, Breadsticks, Gremolata)
- every sub-recipe example (Falafel, Kimchi Pancake, Pork Cutlets, Steak, Enchiladas, Quesadillas, Tofu Stir Fry, Watercress Sauce)
- multiple Directions sections (Basic Roast Fish, Basic Curry)
- steps with no Directions label, and an ingredients-only recipe
- the problem report catching Moussaka, Bigos and Pumpkin Ravioli
- soft line breaks, zero-width characters and blank lines
- the step-number variants
- each kind of source (linked text, bare URLs, plain text)
- cross-links, including the exclusions
- nothing being dropped

## 11. README
- creating the Google Cloud project, turning on the Docs API, and creating the service account and its key
- sharing the doc with the service account
- adding the GitHub secret
- the DNS record for the subdomain
- running the sync locally on Windows
- the doc formatting the parser expects (headings, labels, colons, sub-recipes, Tags)
- reading the problem report
- what to do if the 10% check fails

## 12. Later, not now
- tag filter
- link from philipmtaylor.com

## 13. Build order

**Phase 1: setup and data**
1. ✅ Create the `lunaticllama/recipes` repo with `gh` and clone it locally. Pages stays off for now.
2. Write the parser, its tests and the sync script, then run them against the real doc to produce `data/recipes.json`. Show Phil the problem report. No pages yet.
3. **Clean up the doc.**
   - Phil makes the needed edits from section 4, plus any of the optional ones.
   - Re-read the doc, rerun the parser and check the report. The only flags left should be for recipes Phil chose not to fix. Anything else gets shown to Phil, with the exact recipe and line, before moving on.

**Phase 2: design test (index page + 5 test pages)**
4. Build `index.html` with the title, the search box and the A–Z row, linked to the 5 test pages only.
5. Build the 5 test recipe pages:
   - **Adana Kebab:** labelled ingredient groups ("For the Kebabs:", "For Serving:"). It matches the mockup, so it's a direct comparison.
   - **Falafel:** a sub-recipe (Easy Tahini Sauce), a link inside a step, extra text after the last step, and a source.
   - **Jerk Chicken:** a second, unlabelled block of ingredients after a blank line, and a step that wraps onto a second line.
   - **Tofu Stir Fry:** the most complex layout:
     - two sauce sub-recipes (Basic Stir Fry Sauce, Hot and Sour Sauce)
     - the General Tso's Variation, with its Sauce, Tofu and Stir Fry ingredient groups
     - a second Directions section ("General Tso's Special Directions:")
     - its own source
   - **Thai Noodle Bowls with Tofu and Veggies:** three ingredient groups (Tofu:, Salad:, Dressing:), heavy use of soft line breaks, and a source.

   The design test won't show two things. Cross-links and the look of a flagged recipe (missing steps) aren't on any of these 5 pages, so they're checked in step 9.
6. **Put the site live.**
   - Push to `main`, add the `CNAME` file, turn on Pages and set the custom domain with `gh`.
   - Phil adds the DNS record (`recipes` → `lunaticllama.github.io`).
   - Once GitHub has issued the https certificate, turn on "Enforce HTTPS". That can take up to a day.
7. **Test**, on the live site, on desktop, on Phil's phone and in print preview:
   - search with typos
   - the A–Z letters
   - ingredient checkboxes
   - source links
   - "Keep screen on" (which needs https, so the phone part waits for the certificate)
8. **Finalize the design with Phil.** Make Phil's changes and push them until Phil signs off on how the index and recipe pages look.

**Phase 3: full site (only after the design is approved)**
9. Build all 112 recipe pages from the final template and switch the index to all 112. Check every page and every cross-link, including how flagged recipes look.
10. Add the nightly workflow, including the 10% safety check.
11. Write the README.
12. **Connect the nightly sync.**
    - Phil creates the service account, shares the doc with it and adds the GitHub secret, following the README.
    - Start a manual run of the workflow and confirm it syncs, builds and commits correctly.
13. Show Phil the final report and a sample of pages, then push the finished site to `main`.
