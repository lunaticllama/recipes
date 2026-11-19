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
            "ingredients": ["Traditional “Sweet and Tangy” BBQ Sauce (see recipe)"]}])

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


class DesignTestSubset(unittest.TestCase):
    def test_only_listed_recipes_are_kept(self):
        kept = build.select([ADANA, FALAFEL, THAI], ["falafel", "adana-kebab"])
        self.assertEqual([r["slug"] for r in kept], ["adana-kebab", "falafel"])

    def test_missing_design_test_recipe_is_an_error(self):
        with self.assertRaises(SystemExit):
            build.select([ADANA], ["adana-kebab", "no-such-recipe"])

    def test_default_list_matches_plan(self):
        self.assertEqual(build.DESIGN_TEST, [
            "adana-kebab", "falafel", "jerk-chicken", "tofu-stir-fry",
            "general-tsos-stir-fry", "thai-noodle-bowls-with-tofu-and-veggies"])


class WritesFiles(unittest.TestCase):
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
