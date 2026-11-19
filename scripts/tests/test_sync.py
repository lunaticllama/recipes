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


if __name__ == "__main__":
    unittest.main()
