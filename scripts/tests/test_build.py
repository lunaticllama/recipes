"""Tests for build.py (recipes.json -> site files).

Run from the repo root:  python -m unittest discover -s scripts/tests -t scripts
"""
import json
import os
import re
import tempfile
import unittest

import tests.helpers  # noqa: F401  (puts scripts/ on sys.path)
import build


def recipe(title, slug, sections):
    return {"slug": slug, "title": title, "sections": sections, "sources": [], "notes": [], "tags": []}


def section(items, name=None, groups=None):
    sec = {"ingredient_groups": groups or [{"items": items}], "steps": ["Do it."], "notes": []}
    if name:
        sec["name"] = name
    return sec


ADANA = recipe("Adana Kebab", "adana-kebab", [section(["500 grams ground lamb", "Kosher salt"])])
FALAFEL = recipe("Falafel", "falafel", [
    section(["1½ cups dry chickpeas"]),
    section(["¼ cup tahini"], name="Easy Tahini Sauce")])
PORK = recipe("Pulled Pork", "pulled-pork", [section(
    ["[Traditional “Sweet and Tangy” BBQ Sauce](recipe:traditional-sweet-and-tangy-bbq-sauce) (see recipe)"])])
THAI = recipe("Thai “Puffy” Eggs", "thai-puffy-eggs", [section(["2 large eggs"])])
AMP = recipe("Lamb & Beet Pot Pie <Test>", "lamb-beet-pot-pie-test", [section(["1 pound ground lamb"])])


class SearchIndex(unittest.TestCase):
    def test_entries_have_title_slug_and_plain_ingredients(self):
        entries = build.search_entries([PORK])
        self.assertEqual(entries, [{
            "title": "Pulled Pork", "slug": "pulled-pork",
            "ingredients": ["Traditional “Sweet and Tangy” BBQ Sauce (see recipe)"], "tags": []}])

    def test_tags_are_included(self):
        tagged = dict(ADANA, tags=["thanksgiving", "side dish"])
        self.assertEqual(build.search_entries([tagged])[0]["tags"], ["thanksgiving", "side dish"])

    def test_sub_recipe_ingredients_are_included(self):
        entry = build.search_entries([FALAFEL])[0]
        self.assertEqual(entry["ingredients"], ["1½ cups dry chickpeas", "¼ cup tahini"])

    def test_index_script_sets_window_variable(self):
        js = build.search_index_js([ADANA])
        self.assertTrue(js.startswith("window.RECIPES = "))
        data = json.loads(js[len("window.RECIPES = "):].rstrip().rstrip(";"))
        self.assertEqual(data[0]["slug"], "adana-kebab")


class Letters(unittest.TestCase):
    def test_letter_of_skips_quotes_and_accents(self):
        self.assertEqual(build.letter_of("Adana Kebab"), "A")
        self.assertEqual(build.letter_of("“Sweet” Sauce"), "S")
        self.assertEqual(build.letter_of("Échalote Tart"), "E")
        self.assertEqual(build.letter_of("7-Layer Dip"), "#")

    def test_groups_are_sorted_by_title(self):
        groups = build.group_by_letter([THAI, ADANA, FALAFEL, recipe("apple pie", "apple-pie", [])])
        self.assertEqual(list(groups), ["A", "F", "T"])
        self.assertEqual([r["title"] for r in groups["A"]], ["Adana Kebab", "apple pie"])


class IndexPage(unittest.TestCase):
    def setUp(self):
        self.html = build.render_index([ADANA, FALAFEL, THAI, AMP])

    def test_every_letter_has_a_button_and_empty_ones_are_disabled(self):
        buttons = re.findall(r'<button[^>]*data-letter="([A-Z#])"[^>]*>', self.html)
        self.assertEqual(buttons, list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        self.assertRegex(self.html, r'<button[^>]*data-letter="A"(?![^>]*disabled)[^>]*>')
        self.assertRegex(self.html, r'<button[^>]*data-letter="B"[^>]*disabled[^>]*>')

    def test_letter_lists_link_to_recipe_pages(self):
        self.assertIn('<a href="recipes/adana-kebab.html">Adana Kebab</a>', self.html)
        self.assertIn('id="letter-F"', self.html)
        self.assertNotIn('id="letter-B"', self.html)

    def test_titles_are_escaped(self):
        self.assertIn("Lamb &amp; Beet Pot Pie &lt;Test&gt;", self.html)
        self.assertNotIn("<Test>", self.html)

    def test_page_loads_assets(self):
        for asset in ("assets/style.css", "assets/fuse.min.js", "assets/search-index.js", "assets/recipes.js"):
            self.assertIn(asset, self.html)

    def test_no_placeholders_left(self):
        self.assertNotIn("{{", self.html)


class OnlySubset(unittest.TestCase):
    def test_only_listed_recipes_are_kept(self):
        kept = build.select([ADANA, FALAFEL, THAI], ["falafel", "adana-kebab"])
        self.assertEqual([r["slug"] for r in kept], ["adana-kebab", "falafel"])

    def test_missing_recipe_is_an_error(self):
        with self.assertRaises(SystemExit):
            build.select([ADANA], ["adana-kebab", "no-such-recipe"])


def _build_into(out, recipes, *extra):
    data = os.path.join(out, "recipes.json")
    with open(data, "w", encoding="utf-8") as f:
        json.dump(recipes, f)
    build.main(["--data", data, "--out", out, *extra])


class FullBuild(unittest.TestCase):
    def test_default_builds_every_recipe(self):
        with tempfile.TemporaryDirectory() as out:
            _build_into(out, [ADANA, FALAFEL, THAI])
            self.assertEqual(sorted(os.listdir(os.path.join(out, "recipes"))),
                             ["adana-kebab.html", "falafel.html", "thai-puffy-eggs.html"])

    def test_cross_links_resolve_in_a_full_build(self):
        bbq = recipe("Traditional “Sweet and Tangy” BBQ Sauce", "traditional-sweet-and-tangy-bbq-sauce",
                     [section(["1 cup ketchup"])])
        with tempfile.TemporaryDirectory() as out:
            _build_into(out, [PORK, bbq])
            with open(os.path.join(out, "recipes", "pulled-pork.html"), encoding="utf-8") as f:
                self.assertIn('<a href="traditional-sweet-and-tangy-bbq-sauce.html">', f.read())


class LinkCheck(unittest.TestCase):
    def test_clean_build_has_no_broken_links(self):
        with tempfile.TemporaryDirectory() as out:
            _build_into(out, [ADANA, FALAFEL])
            self.assertEqual(build.broken_links(out), [])

    def test_broken_link_is_reported(self):
        with tempfile.TemporaryDirectory() as out:
            _build_into(out, [ADANA, FALAFEL])
            page = os.path.join(out, "recipes", "falafel.html")
            with open(page, "a", encoding="utf-8") as f:
                f.write('<a href="no-such-page.html">x</a><a href="https://example.com/">ok</a>'
                        '<a href="#top">ok</a>')
            broken = build.broken_links(out)
        self.assertEqual(broken, [("recipes/falafel.html", "no-such-page.html")])


class RichText(unittest.TestCase):
    def test_escapes_and_links(self):
        out = build.render_rich("Mix <b> & [the Kitchn](http://kitchn.com/a?b=1&c=2) well", set())
        self.assertEqual(out, 'Mix &lt;b&gt; &amp; <a href="http://kitchn.com/a?b=1&amp;c=2">the Kitchn</a> well')

    def test_recipe_links_only_to_built_pages(self):
        text = "[BBQ Sauce](recipe:bbq-sauce) (see recipe)"
        self.assertEqual(build.render_rich(text, {"bbq-sauce"}),
                         '<a href="bbq-sauce.html">BBQ Sauce</a> (see recipe)')
        self.assertEqual(build.render_rich(text, set()), "BBQ Sauce (see recipe)")

    def test_unsafe_link_schemes_become_text(self):
        self.assertEqual(build.render_rich("[x](javascript:alert)", set()), "x")


FULL = recipe("Falafel", "falafel", [
    {"ingredient_groups": [{"items": ["1½ cups dry chickpeas", "7 cloves garlic"]}],
     "steps": ["Rinse (method from [the Kitchn](http://kitchn.com/soak)).\nIn the meantime, add parsley.",
               "Fry."],
     "notes": [{"name": "Chicken Variation", "text": "Use chicken."}]},
    {"name": "Easy Tahini Sauce",
     "ingredient_groups": [{"name": "Sauce", "items": ["¼ cup tahini"]}], "steps": [], "notes": []},
])
FULL["sources"] = [{"text": "http://minimalistbaker.com/classic-vegan-falafel-gf/",
                    "url": "http://minimalistbaker.com/classic-vegan-falafel-gf/"},
                   {"text": "Phil’s own recipe"}]
FULL["notes"] = [{"name": "Alternative", "text": "Bake instead.\nAt 400F."}]


class RecipePage(unittest.TestCase):
    def setUp(self):
        self.html = build.render_recipe(FULL, {"falafel"})

    def test_head_and_header(self):
        self.assertIn("<title>Falafel · Phil’s Recipes</title>", self.html)
        self.assertIn('<a href="../index.html">Phil’s Recipes</a>', self.html)
        self.assertIn('data-root="../"', self.html)
        self.assertIn('data-current="falafel"', self.html)
        self.assertIn('<h1 class="recipe-title">Falafel</h1>', self.html)
        self.assertIn('href="../assets/style.css"', self.html)
        self.assertNotIn("{{", self.html)

    def test_checklist_has_unique_ids(self):
        ids = re.findall(r'<input id="(ing-\d+)" type="checkbox">', self.html)
        self.assertEqual(ids, ["ing-1", "ing-2", "ing-3"])
        self.assertIn('<label for="ing-3">¼ cup tahini</label>', self.html)

    def test_steps_and_paragraphs(self):
        self.assertEqual(self.html.count("<li><div class=\"step-text\">"), 2)
        self.assertIn('<p>Rinse (method from <a href="http://kitchn.com/soak">the Kitchn</a>).</p>'
                      '<p>In the meantime, add parsley.</p>', self.html)

    def test_sub_recipe_heading_and_group(self):
        self.assertIn('<h2 class="sub-title">Easy Tahini Sauce</h2>', self.html)
        self.assertIn('<h4 class="group-title">Sauce</h4>', self.html)

    def test_ingredient_only_section_has_no_directions(self):
        sauce = self.html.split('<h2 class="sub-title">Easy Tahini Sauce</h2>')[1]
        self.assertNotIn("Directions", sauce.split("</section>\n    </div>")[0])
        self.assertEqual(self.html.count('<h3 class="section-title">Directions</h3>'), 1)

    def test_notes_and_sources(self):
        self.assertIn('<h4 class="group-title">Chicken Variation</h4>', self.html)
        self.assertIn("<p>Use chicken.</p>", self.html)
        self.assertIn('<h4 class="group-title">Alternative</h4>', self.html)
        self.assertIn("<p>Bake instead.</p><p>At 400F.</p>", self.html)
        self.assertIn('<a href="http://minimalistbaker.com/classic-vegan-falafel-gf/">'
                      'minimalistbaker.com/classic-vegan-falafel-gf</a>', self.html)
        self.assertIn("<li>Phil’s own recipe</li>", self.html)
        self.assertIn('<h3 class="section-title">Sources</h3>', self.html)

    def test_plain_note_under_notes_heading_has_no_extra_label(self):
        r = dict(FULL, notes=[{"name": "Note", "text": "Roast the pumpkin first."}])
        footer = build.render_recipe(r, set()).split('class="recipe-foot"')[1]
        self.assertIn('<h3 class="section-title">Notes</h3>', footer)
        self.assertNotIn('<h4 class="group-title">Note</h4>', footer)
        self.assertIn("<p>Roast the pumpkin first.</p>", footer)

    def test_single_source_heading(self):
        r = dict(FULL, sources=[{"text": "Phil’s own recipe"}])
        self.assertIn('<h3 class="section-title">Source</h3>', build.render_recipe(r, set()))

    def test_buttons(self):
        self.assertIn('data-action="print"', self.html)
        self.assertRegex(self.html, r'<button[^>]*data-action="wake"[^>]*hidden[^>]*>Keep screen on</button>')

    def test_recipe_without_steps_or_sources_still_renders(self):
        bare = recipe("Braised Lamb Shanks", "braised-lamb-shanks", [section(["2 lamb shanks"])])
        bare["sections"][0]["steps"] = []
        html = build.render_recipe(bare, set())
        self.assertIn("2 lamb shanks", html)
        self.assertNotIn("Directions", html)
        self.assertNotIn("Source", html)


class WritesFiles(unittest.TestCase):
    def test_build_writes_recipe_pages_and_removes_stale_ones(self):
        with tempfile.TemporaryDirectory() as out:
            data = os.path.join(out, "recipes.json")
            with open(data, "w", encoding="utf-8") as f:
                json.dump([ADANA, FALAFEL, THAI], f)
            os.makedirs(os.path.join(out, "recipes"))
            stale = os.path.join(out, "recipes", "old-recipe.html")
            open(stale, "w").close()
            build.main(["--data", data, "--out", out, "--only", "adana-kebab,falafel"])
            self.assertEqual(sorted(os.listdir(os.path.join(out, "recipes"))),
                             ["adana-kebab.html", "falafel.html"])

    def test_build_writes_index_and_search_index(self):
        with tempfile.TemporaryDirectory() as out:
            data = os.path.join(out, "recipes.json")
            with open(data, "w", encoding="utf-8") as f:
                json.dump([ADANA, FALAFEL, THAI], f)
            build.main(["--data", data, "--out", out, "--only", "adana-kebab,falafel"])
            with open(os.path.join(out, "index.html"), encoding="utf-8") as f:
                html = f.read()
            with open(os.path.join(out, "assets", "search-index.js"), encoding="utf-8") as f:
                js = f.read()
        self.assertIn("Falafel", html)
        self.assertNotIn("Puffy", html)
        self.assertNotIn("Puffy", js)


if __name__ == "__main__":
    unittest.main()
