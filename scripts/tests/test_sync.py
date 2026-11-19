"""Tests for sync.py: the 10% safety check.

Run from the repo root:  python -m unittest discover -s scripts/tests -t scripts
"""
import contextlib
import io
import json
import os
import tempfile
import unittest

from tests.helpers import make_doc
import sync

ONE = "## Recipe {n}\nIngredients:\nSalt\nDirections:\n1.\tCook it.\n"


def doc_with(n):
    return make_doc("".join(ONE.format(n=i) for i in range(n)))


class CountCheck(unittest.TestCase):
    def test_no_previous_file_is_fine(self):
        sync.check_count(5, None, allow_drop=False)

    def test_small_drop_is_fine(self):
        sync.check_count(108, 118, allow_drop=False)  # 8.5% drop

    def test_drop_over_ten_percent_stops(self):
        with self.assertRaises(SystemExit) as cm:
            sync.check_count(106, 118, allow_drop=False)  # 10.2% drop
        self.assertIn("118", str(cm.exception))
        self.assertIn("106", str(cm.exception))

    def test_allow_drop_overrides(self):
        sync.check_count(10, 118, allow_drop=True)

    def test_growth_is_fine(self):
        sync.check_count(130, 118, allow_drop=False)


class MainRespectsCheck(unittest.TestCase):
    def run_main(self, out, n, *extra):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(doc_with(n), f)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                sync.main(["--doc-json", f.name, "--out", out, *extra])
        finally:
            os.remove(f.name)

    def test_big_drop_leaves_committed_file_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "recipes.json")
            self.run_main(out, 20)
            with self.assertRaises(SystemExit):
                self.run_main(out, 10)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)), 20)

    def test_allow_drop_writes_the_smaller_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "recipes.json")
            self.run_main(out, 20)
            self.run_main(out, 10, "--allow-drop")
            with open(out, encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)), 10)


CARBONARA = {"recipe": "Pasta Carbonara", "kind": "copied-step",
             "detail": "step 2 is identical to a step in “Pasta Broccoli Bolognese”"}
RAVIOLI = {"recipe": "Pumpkin Ravioli", "kind": "no-steps", "detail": "no steps"}
RAVIOLI_GUESS = {"recipe": "Pumpkin Ravioli", "kind": "guess",
                 "detail": "step number looks mistyped (“3,” instead of “3.”); treated it as step 3"}
RECIPES = [{"title": "Pasta Carbonara", "slug": "pasta-carbonara"},
           {"title": "Pumpkin Ravioli", "slug": "pumpkin-ravioli"}]


class IgnoreList(unittest.TestCase):
    def test_parse(self):
        text = "# comment\n\nPasta Carbonara — copied-step\nSteak | short\n  Bigos - no-steps  \n"
        self.assertEqual(sync.load_ignores(text),
                         [("Pasta Carbonara", "copied-step"), ("Steak", "short"), ("Bigos", "no-steps")])

    def test_matching_ignores_case_and_quotes(self):
        kept, ignored, unused = sync.apply_ignores(
            [CARBONARA, RAVIOLI], [("pasta carbonara", "copied-step"), ("Moussaka", "no-steps")])
        self.assertEqual(kept, [RAVIOLI])
        self.assertEqual(ignored, [CARBONARA])
        self.assertEqual(unused, [("Moussaka", "no-steps")])

    def test_repo_ignore_file_lists_carbonara(self):
        with open(sync.IGNORE_FILE, encoding="utf-8") as f:
            self.assertIn(("Pasta Carbonara", "copied-step"), sync.load_ignores(f.read()))


class IssueText(unittest.TestCase):
    def test_clean_report_is_empty(self):
        self.assertEqual(sync.report_markdown([], RECIPES, 118), "")

    def test_report_groups_by_recipe_with_page_links(self):
        md = sync.report_markdown([RAVIOLI, RAVIOLI_GUESS], RECIPES, 118)
        self.assertIn("1 recipe needs a look", md)
        self.assertIn("### [Pumpkin Ravioli](https://recipes.philipmtaylor.com/recipes/pumpkin-ravioli.html)", md)
        self.assertIn("- **No steps:** no steps", md)
        self.assertIn("- **Check this line:** step number looks mistyped", md)
        self.assertIn("report_ignore.txt", md)

    def test_unknown_recipe_has_no_link(self):
        md = sync.report_markdown([{"recipe": "(before the first recipe)", "kind": "dropped",
                                    "detail": "line not placed anywhere"}], RECIPES, 118)
        self.assertIn("### (before the first recipe)", md)

    def test_text_is_stable_between_runs(self):
        a = sync.report_markdown([RAVIOLI_GUESS, RAVIOLI], RECIPES, 118)
        b = sync.report_markdown([RAVIOLI, RAVIOLI_GUESS], RECIPES, 118)
        self.assertEqual(a, b)


class CheckMode(unittest.TestCase):
    def run_main(self, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(make_doc(ONE.format(n=1) + "## Pumpkin Ravioli\nIngredients:\nFresh pasta dough\n"), f)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                sync.main(["--doc-json", f.name, *args])
        finally:
            os.remove(f.name)
        return out.getvalue()

    def test_check_does_not_write_recipes_json(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "recipes.json")
            text = self.run_main("--check", "--out", out)
            self.assertFalse(os.path.exists(out))
        self.assertIn("Pumpkin Ravioli", text)

    def test_report_md_is_written(self):
        with tempfile.TemporaryDirectory() as d:
            md = os.path.join(d, "report.md")
            self.run_main("--check", "--out", os.path.join(d, "r.json"), "--report-md", md)
            with open(md, encoding="utf-8") as f:
                self.assertIn("Pumpkin Ravioli", f.read())


if __name__ == "__main__":
    unittest.main()
