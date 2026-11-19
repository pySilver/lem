"""land.py's rules that take facts and return a result, each called in this process.

What only git can show stays in the blocks of tests/, which run the real commands in throwaway
repositories; here a rule gets the text git gave and is asked for its result.
"""

import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
land = importlib.import_module("land")

# One defect outside the change, as a review's record names it.
DEFECT = {"where": "src/json.py:parse", "title": "Empty input crashes the parser", "what": "parse with an empty string raises IndexError, on the base commit too."}

# The bar's marks of a Python file, each written in two pieces: the bar reads a .py file's marks,
# and this file adds none of the ones it feeds it.
NOQA = "#" + " noqa"
SKIP = "pytest.mark" + ".skip"
FLAKY = "pytest.mark" + ".flaky"


def patch(path: str, minus: tuple[str, ...] = (), plus: tuple[str, ...] = (), *, was: str | None = None, new: bool = False, gone: bool = False) -> str:
    """One file's part of `git diff -U0 -M`: its header, then one hunk of the lines that went and came.
    `was` is the name before a move, `new` a file the base lacks, `gone` one the tip lacks."""
    before = was or path
    lines = [f"diff --git a/{before} b/{path}", "--- /dev/null" if new else f"--- a/{before}", "+++ /dev/null" if gone else f"+++ b/{path}"]
    lines.append(f"@@ -1,{len(minus)} +1,{len(plus)} @@")
    return "\n".join([*lines, *(f"-{line}" for line in minus), *(f"+{line}" for line in plus)])


def bar(*patches: str, rows: tuple[str, ...] = (), plan: str = "", files: tuple[str, ...] = ()) -> dict:
    """land.bar_of over the parts of a diff, the name-status rows, the plan and the changed files."""
    return land.bar_of("\n".join(patches), list(rows), plan, list(files))


def lowered(result: dict) -> list[tuple[str, str]]:
    """Each lowered bar of a result as its file and what lowers it, in order."""
    return sorted((entry["file"], entry["what"]) for entry in result["lowered"])


class DefectsOutside(unittest.TestCase):
    """`land.defects_of`: the defects a review's record names outside the change."""

    def refusal(self, value: object) -> str:
        with self.assertRaises(land.LandError) as raised:
            land.defects_of(value)
        return str(raised.exception)

    def test_a_count_is_refused(self) -> None:
        said = self.refusal(2)
        self.assertIn("`outside` is the list", said)
        self.assertIn('"where"', said)

    def test_a_defect_with_only_its_place_is_refused(self) -> None:
        said = self.refusal([{"where": "app.txt"}])
        self.assertIn("`outside` is the list", said)
        self.assertIn('"title"', said)

    def test_zero_is_no_defect_and_nothing_to_file(self) -> None:
        self.assertEqual(land.defects_of(0), [])
        self.assertEqual(land.to_file([{"round": 1, "answered": True, "outside": land.defects_of(0)}]), [])

    def test_a_named_defect_is_kept_and_waits_to_be_filed(self) -> None:
        padded = {key: f" {text} " for key, text in DEFECT.items()}
        self.assertEqual(land.defects_of([padded]), [DEFECT])
        self.assertEqual(land.to_file([{"round": 2, "answered": True, "outside": [DEFECT]}]), [{"round": 2, **DEFECT}])


class Bar(unittest.TestCase):
    """`land.bar_of`: where a change lowers the bar, from the diff git gave."""

    def test_a_new_suppression_lowers_the_bar(self) -> None:
        result = bar(patch("calc.py", plus=(f"import os  {NOQA}: F401",), new=True))
        self.assertEqual(result["lowered"], [{"file": "calc.py", "what": NOQA, "line": f"import os  {NOQA}: F401", "reason": None}])

    def test_a_suppression_that_only_got_a_space_is_none(self) -> None:
        result = bar(patch("plug.py", minus=(f"import plugin {NOQA}: F401",), plus=(f"import plugin  {NOQA}: F401",)))
        self.assertEqual(result["lowered"], [])

    def test_a_suppression_that_got_wider_is_a_new_one(self) -> None:
        result = bar(patch("plug.py", minus=(f"import other  {NOQA}: E402",), plus=(f"import other  {NOQA}",)))
        self.assertEqual([entry["line"] for entry in result["lowered"]], [f"import other  {NOQA}"])

    def test_a_skip_of_a_whole_module(self) -> None:
        result = bar(patch("tests/test_base.py", plus=("import pytest", f'pytestmark = {SKIP}(reason="later")')))
        self.assertEqual(lowered(result), [("tests/test_base.py", SKIP)])

    def test_fewer_assertions_in_a_test_file(self) -> None:
        fewer = bar(patch("tests/test_base.py", minus=("    assert 1 + 1 == 2", "    assert 2 + 2 == 4"), plus=("    assert 1 + 1 == 2",)))
        more = bar(patch("tests/test_base.py", plus=("    assert 3 + 3 == 6",)))
        self.assertEqual(lowered(fewer), [("tests/test_base.py", "1 assertion(s) fewer")])
        self.assertEqual(more["lowered"], [])

    def test_an_assertion_out_of_a_rust_module(self) -> None:
        result = bar(patch("lib.rs", minus=("#[cfg(test)]", "mod tests {", "    #[test]", "    fn it_is_one() { assert_eq!(super::one(), 1); }", "}")))
        self.assertEqual(lowered(result), [("lib.rs", "1 assertion(s) fewer")])

    def test_a_deleted_test_file_is_one_entry(self) -> None:
        result = bar(patch("tests/test_base.py", minus=("def test_base():", "    assert 1 + 1 == 2"), gone=True), rows=("D\ttests/test_base.py",))
        self.assertEqual(lowered(result), [("tests/test_base.py", "a test file is deleted")])

    def test_a_test_file_moved_out_of_the_tests(self) -> None:
        out = bar(rows=("R100\ttests/test_old.py\tattic/old.py",))
        within = bar(rows=("R100\ttests/test_old.py\ttests/unit/test_old.py",))
        self.assertEqual(lowered(out), [("tests/test_old.py", "a test file is moved out of the tests, to attic/old.py")])
        self.assertEqual(within["lowered"], [])

    def test_a_focus_mark_is_named_without_its_parenthesis(self) -> None:
        result = bar(patch("tests/focus.test.js", plus=('it.only("runs alone", () => {});', 'fit("runs alone too", () => {});', 'fdescribe("a group alone", () => {});',
                                                         'test.only("one test", () => {});', 'describe.only("one group", () => {});', "profit(1);"), new=True))
        self.assertEqual([what for _, what in lowered(result)], ["describe.only", "fdescribe", "fit", "it.only", "test.only"])

    def test_marks_in_a_runners_settings(self) -> None:
        result = bar(
            patch("pyproject.toml", plus=("[tool.pytest.ini_options]", "addopts = \"--deselect tests/test_calc.py::test_add -k 'not slow' --reruns 3\"")),
            patch("package.json", minus=('{"name": "shop"}',), plus=('{"name": "shop", "jest": {"testPathIgnorePatterns": ["slow"]}}',)),
        )
        self.assertEqual(lowered(result), [("package.json", "testPathIgnorePatterns"), ("pyproject.toml", "--deselect"), ("pyproject.toml", "--reruns"), ("pyproject.toml", "-k 'not")])

    def test_a_coverage_threshold_that_went_down(self) -> None:
        result = bar(
            patch("pyproject.toml", minus=("fail_under = 90",), plus=("fail_under = 10",)),
            patch("package.json", minus=('{"jest": {"coverageThreshold": {"global": {"lines": 80}}}}',), plus=('{"jest": {"coverageThreshold": {"global": {"lines": 50}}}}',)),
            patch(".github/workflows/ci.yml", minus=("      - run: pytest --cov-fail-under=80",), plus=("      - run: pytest",)),
            patch("setup.cfg", minus=("fail_under = 70",), plus=("fail_under = 75",)),
        )
        self.assertEqual(lowered(result), [(".github/workflows/ci.yml", "cov-fail-under (80) is gone"), ("package.json", "lines went from 80 to 50"), ("pyproject.toml", "fail_under went from 90 to 10")])

    def test_a_flaky_decorator(self) -> None:
        result = bar(patch("tests/test_calc.py", plus=("import pytest", f"@{FLAKY}(reruns=5)")))
        self.assertEqual(lowered(result), [("tests/test_calc.py", FLAKY)])

    def test_a_document_may_quote_a_mark(self) -> None:
        result = bar(patch("docs/backlog/a-note.md", plus=(f"A {NOQA} in a note is no mark.", f"{SKIP} neither."), new=True), files=("docs/backlog/a-note.md",))
        self.assertEqual((result["lowered"], result["not_covered"]), ([], []))

    def test_the_tests_snapshots_and_settings_the_change_edits(self) -> None:
        rows = ("M\t.github/workflows/ci.yml", "M\tpackage.json", "M\tpyproject.toml", "M\ttests/__snapshots__/total.snap", "M\ttests/test_calc.py",
                "A\ttests/test_new.py", "R100\ttests/test_a.py\ttests/test_b.py", "R090\ttests/test_c.py\ttests/test_d.py", "M\tshop.py")
        self.assertEqual(bar(rows=rows)["edited"], [
            {"file": ".github/workflows/ci.yml", "kind": "test configuration"}, {"file": "package.json", "kind": "test configuration"},
            {"file": "pyproject.toml", "kind": "test configuration"}, {"file": "tests/__snapshots__/total.snap", "kind": "snapshot"},
            {"file": "tests/test_calc.py", "kind": "test"}, {"file": "tests/test_d.py", "kind": "test"},
        ])

    def test_the_kinds_of_file_the_bar_has_no_marks_for(self) -> None:
        result = bar(files=("x.rb", "calc.py", "docs/guide.md", "data.json", "Makefile", "lib/y.RB"))
        self.assertEqual(result["not_covered"], [".rb"])
        self.assertNotIn("own_patterns", result)

    def test_the_plan_gives_each_file_its_reason(self) -> None:
        plan = "\n".join(["# bar-change", "", "## Tasks", "", "- calc.py: a line of another section is no reason.", "", "## The bar", "",
                          "- calc.py: the import registers a plugin.", "- `tests/test_base.py`: the sum moved to another module with its test.", "", "## Notes", "",
                          "- plug.py: after the section, no reason either."])
        result = bar(patch("calc.py", plus=(f"import os  {NOQA}: F401",)), patch("plug.py", plus=(f"import other  {NOQA}",)),
                     patch("tests/test_base.py", plus=(f"pytestmark = {SKIP}",)), plan=plan)
        self.assertEqual(sorted((entry["file"], entry["reason"]) for entry in result["lowered"]), [
            ("calc.py", "the import registers a plugin."), ("plug.py", None), ("tests/test_base.py", "the sum moved to another module with its test."),
        ])


class BarRefusal(unittest.TestCase):
    """`land.bar_refusal`: what the checks say of a bar lowered with no reason, on each track."""

    def test_the_fast_track_has_no_plan_and_names_the_standard_track(self) -> None:
        found = bar(patch("tests/test_old.py", plus=(f"@{SKIP}",), new=True), plan="")
        said = land.bar_refusal(found["lowered"], small=True)
        self.assertEqual([entry["reason"] for entry in found["lowered"]], [None])
        self.assertIn(f"tests/test_old.py ({SKIP})", said)
        self.assertIn("standard track", said)

    def test_the_standard_track_names_the_plans_section(self) -> None:
        found = bar(patch("calc.py", plus=(f"import os  {NOQA}",)))
        said = land.bar_refusal(found["lowered"], small=False)
        self.assertIn(f"calc.py ({NOQA})", said)
        self.assertIn("`## The bar`", said)
        self.assertNotIn("standard track", said)

    def test_a_reason_for_each_file_is_no_refusal(self) -> None:
        found = bar(patch("calc.py", plus=(f"import os  {NOQA}",)), plan="## The bar\n\n- calc.py: the import registers a plugin.\n")
        self.assertIsNone(land.bar_refusal(found["lowered"], small=False))
        self.assertIsNone(land.bar_refusal([], small=True))


if __name__ == "__main__":
    unittest.main()
