"""land.py's rules that take facts and return a result, each called in this process.

What only git can show stays in the blocks of tests/, which run the real commands in throwaway
repositories; here a rule gets the text git gave and is asked for its result.
"""

import importlib
import sys
import tempfile
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


SLUG = "landing-in-the-background"


def gate_end(task: str, result: str, seconds: int, ts: str = "2026-11-19T10:22:44Z") -> dict:
    """One `gate.end` event as `lem project log` writes it."""
    return {"ts": ts, "event": "gate.end", "task": task, "result": result, "seconds": seconds, "tip": "abc123456", "say": f"{task}: ..."}


class ChecksSay(unittest.TestCase):
    """`land.checks_say`: the one line for the owner at each end of a run of the checks, with no question."""

    def test_a_passed_run_names_the_review(self) -> None:
        self.assertEqual(land.checks_say(SLUG, "passed", next_due="review"), f"{SLUG}: the checks passed; the review runs, nothing for you")

    def test_a_passed_run_with_no_review_due_names_the_proposal(self) -> None:
        for due in ("none", "owner"):
            self.assertEqual(land.checks_say(SLUG, "passed", next_due=due), f"{SLUG}: the checks passed; no review is due, so it is proposed, nothing for you")

    def test_a_red_run_names_each_command_and_the_repair(self) -> None:
        self.assertEqual(land.checks_say(SLUG, "red", red=["bash tests/all.sh"]), f"{SLUG}: the checks are red on bash tests/all.sh; a builder repairs it, nothing for you")
        self.assertIn("on ruff check . and pytest -q;", land.checks_say(SLUG, "red", red=["ruff check .", "pytest -q"]))

    def test_a_refused_run_names_what_was_refused(self) -> None:
        said = land.checks_say(SLUG, "refused", refused="a criterion's test does not hold")
        self.assertEqual(said, f"{SLUG}: the checks refused the change: a criterion's test does not hold; a builder repairs it, nothing for you")

    def test_a_stopped_run_waits_for_the_owner(self) -> None:
        self.assertEqual(land.checks_say(SLUG, "stopped"), f"{SLUG}: the checks were stopped; the landing waits for your word")

    def test_no_line_asks_a_question(self) -> None:
        lines = [land.checks_say(SLUG, "passed"), land.checks_say(SLUG, "red", red=["x"]), land.checks_say(SLUG, "refused"), land.checks_say(SLUG, "stopped")]
        self.assertFalse(any("?" in line for line in lines))
        self.assertTrue(all(line.startswith(f"{SLUG}: ") for line in lines))

    def test_another_result_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            land.checks_say(SLUG, "green")


class Duration(unittest.TestCase):
    """`land.duration`: seconds as a person reads them."""

    def test_the_forms(self) -> None:
        self.assertEqual([land.duration(n) for n in (26, 266, 840, 60)], ["26 s", "4 min 26 s", "14 min", "1 min"])


class LastRun(unittest.TestCase):
    """`land.last_seconds`: the length of the checks' last finished run, from the event log."""

    def test_the_newest_passed_end_of_any_task(self) -> None:
        events = [gate_end("one", "passed", 300), {"event": "gate", "task": "two", "exit": 0}, gate_end("two", "passed", 266), gate_end("two", "red", 20), gate_end("one", "stopped", 5)]
        self.assertEqual(land.last_seconds(events), 266)

    def test_no_passed_run_is_none(self) -> None:
        self.assertIsNone(land.last_seconds([gate_end("one", "red", 20), gate_end("one", "refused", 400), {"event": "gate.start", "task": "one"}]))
        self.assertIsNone(land.last_seconds([]))


class Overdue(unittest.TestCase):
    """`land.is_overdue` and `land.overdue_say`: checks that run more than three times as long as their last finished run."""

    def test_more_than_three_times_is_overdue(self) -> None:
        # the last run of lem-landing-page's checks: 4 min 26 s (2026-11-19)
        self.assertTrue(land.is_overdue(840, 266))
        self.assertFalse(land.is_overdue(798, 266))
        self.assertFalse(land.is_overdue(120, 266))

    def test_with_no_last_run_nothing_is_overdue(self) -> None:
        self.assertFalse(land.is_overdue(10_000, None))
        self.assertFalse(land.is_overdue(None, 266))

    def test_a_short_last_run_is_no_measure_in_the_first_minute(self) -> None:
        # the guards check's last run of `true` rounds to 0 s (hero-logo-animated-background, gate/01.log)
        # or to 1 s under the load of tests/all.sh (load-gate-default-forty), and a slow run read at 3 s
        # or 5 s was called overdue (2026-11-22)
        for last in (0, 1, 2):
            self.assertFalse(land.is_overdue(3, last))
            self.assertFalse(land.is_overdue(5, last))
            self.assertFalse(land.is_overdue(59, last))
        self.assertTrue(land.is_overdue(61, 0))
        self.assertTrue(land.is_overdue(61, 1))
        self.assertTrue(land.is_overdue(10_000, 0))

    def test_the_floor_is_one_minute(self) -> None:
        self.assertEqual(land.OVERDUE_FLOOR, 60)
        self.assertFalse(land.is_overdue(59, 10))
        self.assertTrue(land.is_overdue(60, 10))

    def test_the_line_says_both_lengths_and_the_stop(self) -> None:
        self.assertEqual(land.overdue_say(SLUG, 840, 266),
                         f'{SLUG}: the checks run for 14 min, more than three times their last run of 4 min 26 s; "stop the checks" stops them')


class Resumed(unittest.TestCase):
    """`land.resumed_line` and `land.ended_of`: what a session that did not start the run says of its end."""

    def test_a_passed_end_is_past_and_the_landing_goes_on_from_its_first_step(self) -> None:
        said = land.resumed_line(SLUG, gate_end(SLUG, "passed", 266))
        self.assertEqual(said, f"{SLUG}: its last run of the checks ended at 2026-11-19 10:22 UTC, passed; the landing goes on from its first step, as after a cut-off")
        self.assertNotIn("the review runs", said)

    def test_a_stopped_end_waits_for_the_owner(self) -> None:
        self.assertTrue(land.resumed_line(SLUG, gate_end(SLUG, "stopped", 30)).endswith("stopped; the landing waits for your word"))

    def test_the_end_as_status_prints_it(self) -> None:
        end = gate_end(SLUG, "red", 20)
        self.assertEqual(land.ended_of(end, SLUG), {"at": end["ts"], "tip": "abc123456", "result": "red", "seconds": 20, "say": end["say"], "resumed": land.resumed_line(SLUG, end)})
        self.assertIsNone(land.ended_of(None, SLUG))


class HeldRefusal(unittest.TestCase):
    """`land.held_refusal`: what a step of a task says when another step of it holds the task's step lock."""

    HOLDER = {"step": "checks", "pid": 4242, "since": "2026-11-19T10:18:18Z"}

    def test_a_second_run_of_the_checks_is_refused_because_they_already_run(self) -> None:
        said = land.held_refusal(SLUG, "checks", self.HOLDER)
        self.assertIn(f"the checks of {SLUG} already run (since 2026-11-19 10:18 UTC, in process 4242): a second run is refused", said)
        self.assertIn(f"`lem land checks {SLUG} --status`", said)

    def test_another_step_waits_for_the_end_of_the_checks(self) -> None:
        said = land.held_refusal(SLUG, "read", self.HOLDER)
        self.assertIn(f"the checks of {SLUG} run", said)
        self.assertIn("their end comes first", said)
        self.assertIn("the session that started them goes on when they end", said)

    def test_a_step_that_holds_the_lock_is_named(self) -> None:
        said = land.held_refusal(SLUG, "checks", {"step": "read", "pid": 7, "since": "2026-11-19T10:18:18Z"})
        self.assertIn(f"`lem land read {SLUG}`", said)
        self.assertIn("in process 7", said)
        self.assertIsNotNone(land.held_refusal(SLUG, "checks", None))


if __name__ == "__main__":
    unittest.main()


class WhoMerges(unittest.TestCase):
    """Who may merge a proposed request: the merge agent only a green one that is not careful, with the
    review's careful call and its own verdict to merge, where the settings let it; the owner always."""

    def refusal(self, land_: str = "agent", careful: tuple[str, ...] = (), reasons: tuple[str, ...] = (), called: bool = True, verdict: str | None = "merge") -> str | None:
        return land.merger_refusal("gift-note", land_, list(careful), list(reasons), called, {"verdict": verdict} if verdict else None)

    def test_a_green_request_that_is_not_careful_with_a_merge_verdict(self) -> None:
        self.assertIsNone(self.refusal())

    def test_the_owner_merges_where_the_settings_say_so(self) -> None:
        self.assertIn('branch.land is "owner"', self.refusal(land_="owner"))

    def test_a_careful_request_calls_him_whatever_the_review_found(self) -> None:
        self.assertIn("a careful request is merged by the owner", self.refusal(careful=("its plan says careful: yes",)))

    def test_a_request_that_is_not_green_calls_him(self) -> None:
        self.assertIn("the request is not green (decision 1 was taken without the owner)", self.refusal(reasons=("decision 1 was taken without the owner",)))

    def test_no_careful_call_of_the_review_calls_him(self) -> None:
        self.assertIn("no review that answered made the careful call", self.refusal(called=False))

    def test_no_merge_review_or_a_call_keeps_the_merge_his(self) -> None:
        self.assertIn("lem land merge-review gift-note --file FILE", self.refusal(verdict=None))
        self.assertIn("the merge review calls the owner", self.refusal(verdict="call"))


class MergeReview(unittest.TestCase):
    """The merge agent's verdict is the first line of its review, and the task's time is measured
    against the earlier tasks of its track in the event log."""

    def test_the_verdict_is_the_first_line(self) -> None:
        self.assertEqual(land.verdict_of("\nVerdict: merge. A typo in the footer, with its test.\n\nMore."), "merge")
        self.assertEqual(land.verdict_of("**Verdict: call.** The change is careful."), "call")
        self.assertIsNone(land.verdict_of("A fine change.\nVerdict: merge."))

    def test_the_time_against_the_median_of_the_same_track(self) -> None:
        def ev(task: str, event: str, at: str, **more: object) -> dict:
            return {"ts": f"2026-11-20T{at}:00Z", "event": event, "task": task, **more}
        events = [
            ev("a", "task.criteria", "08:00", size="small"), ev("a", "proposed", "08:10"),
            ev("b", "task.criteria", "08:00", size="small"), ev("b", "proposed", "08:30"),
            ev("big", "task.criteria", "08:00", size="full"), ev("big", "proposed", "11:00"),
            ev("c", "task.criteria", "09:00", size="small"), ev("c", "proposed", "12:00"),
        ]
        found = land.task_time(events, "c")
        self.assertEqual((found["seconds"], found["expected"]), (3 * 3600, 20 * 60))
        self.assertIn("the median of 2 earlier tasks of the fast track", found["from"])
        self.assertEqual(land.task_time(events, "a")["expected"], None)
        self.assertEqual(land.task_time(events, "nobody")["seconds"], None)


class MergeBriefPictures(unittest.TestCase):
    """`land.pictures_of`: the pictures of the task's `media/` folder that the merge brief names, each
    a picture the board's media route shows, by its path from the task directory."""

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.directory = Path(folder.name) / "hero-logo-animated-background"
        self.directory.mkdir()

    def test_the_pictures_of_the_folder_and_its_subfolder_and_nothing_else(self) -> None:
        media = self.directory / "media"
        (media / "phone").mkdir(parents=True)
        for name in ("hero-before-dark.png", "hero-after-dark.png", "logo.JPEG", "spinner.gif", "card.webp", "notes.txt", "mark.svg", ".hidden.png"):
            (media / name).write_bytes(b"x")
        (media / "phone" / "hero-after.png").write_bytes(b"x")
        (media / "empty").mkdir()
        (self.directory / "report.md").write_text("![after](media/hero-after-dark.png)\n", encoding="utf-8")
        self.assertEqual(land.pictures_of(self.directory), [
            "media/card.webp", "media/hero-after-dark.png", "media/hero-before-dark.png", "media/logo.JPEG",
            "media/phone/hero-after.png", "media/spinner.gif",
        ])

    def test_no_media_folder_is_no_picture(self) -> None:
        self.assertEqual(land.pictures_of(self.directory), [])


class MergeBriefTry(unittest.TestCase):
    """`land.try_of`: the two ways the owner gets the branch, which a review that calls him ends with."""

    PR = {"number": 41, "url": "https://github.com/example/shop/pull/41"}

    def test_a_worktree_under_the_main_checkout_is_named_from_it(self) -> None:
        main = Path("/work/shop")
        self.assertEqual(land.try_of(main, main / ".lem" / "worktrees" / "board-colors", self.PR),
                         {"worktree": ".lem/worktrees/board-colors", "checkout": "gh pr checkout 41"})

    def test_a_worktree_outside_it_is_named_whole(self) -> None:
        self.assertEqual(land.try_of(Path("/work/shop"), Path("/elsewhere/board-colors"), self.PR),
                         {"worktree": "/elsewhere/board-colors", "checkout": "gh pr checkout 41"})


class MovedBase(unittest.TestCase):
    """A merge that the moved base refused: which refusals are kept for the tip, when what was said of
    the tip at the merge holds for the tip of the new landing, and when the owner's merge stands."""

    def test_only_a_rule_of_lem_is_kept_for_the_tip(self) -> None:
        self.assertTrue(land.kept_refusal("merger", "rule") and land.kept_refusal("merger", "tip") and land.kept_refusal("merger", "base"))
        self.assertTrue(land.kept_refusal("owner", "base"))
        self.assertFalse(land.kept_refusal("owner", "tip") or land.kept_refusal("owner", "rule"))
        # a git or gh call that failed has no kind: the next try runs it again
        self.assertFalse(land.kept_refusal("merger", None))

    def test_the_tip_of_a_rebase_with_no_conflict_carries_what_was_said(self) -> None:
        rebased = {"from": "aaa", "to": "bbb"}
        self.assertEqual(land.tip_carry({"proposed": "aaa", "rebase_carried": rebased}, "bbb", []), ("rebase", None))
        self.assertEqual(land.tip_carry({"proposed": "aaa"}, "aaa", []), ("same", None))
        # a careful request carries over a rebase with no conflict all the same
        self.assertEqual(land.tip_carry({"proposed": "aaa", "rebase_carried": rebased}, "bbb", ["the owner says so"]), ("rebase", None))
        # a commit after the rebase, a tip no record names, or a first proposal carry nothing
        self.assertEqual(land.tip_carry({"proposed": "aaa", "rebase_carried": rebased}, "ccc", []), (None, "a commit came after the rebase"))
        self.assertEqual(land.tip_carry({"proposed": "aaa"}, "bbb", []), (None, "a commit came after the tip proposed before"))
        self.assertEqual(land.tip_carry({"rebase_carried": rebased}, "bbb", []), (None, None))

    def test_the_owners_merge_stands_while_the_change_and_its_reasons_stay(self) -> None:
        tap = {"tip": "aaa", "not_green": ["the bar is lower"], "via": "server", "at": "2026-11-21T10:00:00Z"}
        kept = {"proposed": "aaa", "rebase_carried": {"from": "aaa", "to": "bbb"}, "owner_tap": tap}
        stood = land.moved_carry(kept, "bbb", [], ["the bar is lower"])
        self.assertEqual((stood["owner_merge"], stood["owner_why"], stood["tap"]), ("stands", None, {**tap, "tip": "bbb"}))
        gone = land.moved_carry(kept, "ccc", [], ["the bar is lower"])
        self.assertEqual((gone["owner_merge"], gone["owner_why"], gone["tap"]), ("ended", "a commit came after the rebase", None))
        gone = land.moved_carry(kept, "bbb", [], [])
        self.assertEqual(gone["owner_merge"], "ended")
        self.assertIn("not the ones the owner saw", gone["owner_why"])
        # with no merge of his on record there is nothing to stand or end
        self.assertEqual(land.moved_carry({**kept, "owner_tap": None}, "bbb", [], [])["owner_merge"], None)

    # the reviews that answered, as `cmd_base` reads them: round 1 of a change whose patch is p1
    READ = {"answered": ["codex"], "round": 1, "must_fix": 0, "patch": "p1", "contents": {"shop.txt": {"base": "b1", "tip": "t1", "modes": ["100644", "100644"]}}}
    NOW = {"patch": "p1", "contents": {"shop.txt": {"base": "b1", "tip": "t1", "modes": ["100644", "100644"]}}}

    def assert_why(self, answered: list[dict], now: dict, expected: str | None) -> None:
        why = land.why_uncovered(answered, "docs/backlog", now)
        self.assertEqual(why, expected)
        # the reason is None exactly when the rule of `cmd_base` says that a review covers the change
        held = bool(answered) and not answered[-1]["must_fix"] and land.covered("docs/backlog", answered[-1], now)
        self.assertEqual(why is None, held)

    def test_why_no_review_covers_the_change_names_the_newest_reviews_reason(self) -> None:
        fixed = {"patch": "p2", "contents": {"shop.txt": {"base": "b1", "tip": "t2", "modes": ["100644", "100644"]}}}
        self.assert_why([], self.NOW, "no review answered for the change")
        # round 2, at the tip it read, left 1 must-fix; a builder fixed it and no review read the fix
        self.assert_why([self.READ, {**self.READ, "round": 2, "must_fix": 1}], fixed, "round 2 left 1 must-fix, and no review read the change after it")
        self.assert_why([self.READ], fixed, "no review read what changed after round 1")
        self.assert_why([self.READ], self.NOW, None)

    def test_a_rebase_with_no_conflict_carries_the_newest_review_with_what_it_left_open(self) -> None:
        fixed = {"patch": "p2", "contents": {"shop.txt": {"base": "b1", "tip": "t2", "modes": ["100644", "100644"]}}}
        open_one = {**self.READ, "round": 2, "must_fix": 1}
        self.assertTrue(land.review_carries([self.READ], "docs/backlog", self.NOW))
        # round 2 left 1 must-fix at the tip it read, and nothing came after it: the review carries, its must-fix too
        self.assertTrue(land.review_carries([self.READ, open_one], "docs/backlog", self.NOW))
        # the form an earlier rebase carried covers the change as well
        self.assertTrue(land.review_carries([{**open_one, "carried": [{"patch": "p2", "contents": fixed["contents"], "onto": "abc"}]}], "docs/backlog", fixed))
        # no review answered, or a commit came after the newest one: nothing carries
        self.assertFalse(land.review_carries([], "docs/backlog", self.NOW))
        self.assertFalse(land.review_carries([self.READ, open_one], "docs/backlog", fixed))
        # an earlier review that covers the change carries nothing when a newer one does not
        self.assertFalse(land.review_carries([self.READ, {**self.READ, "round": 2, "patch": "p0", "contents": None}], "docs/backlog", self.NOW))

    def test_a_covered_change_with_an_open_must_fix_keeps_its_reason(self) -> None:
        # the review carries over a clean rebase, and a conflict on it still keeps why no review covers it with nothing to fix
        open_one = {**self.READ, "round": 2, "must_fix": 1}
        self.assertTrue(land.review_carries([self.READ, open_one], "docs/backlog", self.NOW))
        self.assert_why([self.READ, open_one], self.NOW, "round 2 left 1 must-fix, and no review read the change after it")

    def test_the_line_of_a_carried_review_names_its_open_must_fix(self) -> None:
        self.assertIsNone(land.review_line(None))
        self.assertEqual(land.review_line({"round": 1, "must_fix": 0}), "the review carried over the rebase")
        self.assertEqual(land.review_line({"round": 2, "must_fix": 1}), "the review carried over the rebase, and its open must-fix")

    def test_an_ended_merge_says_that_no_review_covers_the_change(self) -> None:
        tap = {"tip": "aaa", "not_green": ["two rounds reviewed it"], "via": "server", "at": "2026-11-22T10:00:00Z"}
        uncovered = {"from": "aaa", "to": "bbb", "why": "round 2 left 1 must-fix, and no review read the change after it"}
        kept = {"proposed": "aaa", "rebase_uncovered": uncovered, "owner_tap": tap}
        ended = land.moved_carry(kept, "bbb", [], ["two rounds reviewed it"])
        self.assertEqual(ended["owner_why"], "no review covers the change: round 2 left 1 must-fix, and no review read the change after it")
        self.assertNotIn("conflict", ended["owner_why"])
        # a commit after that rebase is a cause of its own
        self.assertEqual(land.moved_carry(kept, "ccc", [], ["two rounds reviewed it"])["owner_why"], "a commit came after the rebase")

    # A proposal of aaa with the merge agent's verdict and the owner's merge, a conflict, and a builder's
    # resolution from aaa to bbb whose read is attempt 3; round 1 read the change, careful false.
    ROUND = {"attempt": 1, "round": 1, "answered": ["codex"], "must_fix": 0, "should": 0, "nit": 0, "careful": False, "careful_why": "it reaches no topic", "tip": "aaa"}
    SOLVED = {"attempt": 3, "round": 1, "of": "resolution", "kind": "read", "answered": ["codex"], "must_fix": 0, "should": 0, "nit": 0, "careful": False, "careful_why": "it reaches no topic", "tip": "bbb"}
    RESOLVED = {
        "proposed": "aaa", "merge_review": {"verdict": "merge", "tip": "aaa", "calls": False},
        "owner_tap": {"tip": "aaa", "not_green": [], "via": "server", "at": "2026-11-22T10:00:00Z"},
        "resolution": {"files": ["shop.txt"], "before": "aaa", "after": "bbb", "covered": True, "read": 3},
        "reads": [ROUND, SOLVED],
    }

    def resolved(self, why_careful: tuple[str, ...] = (), reasons: tuple[str, ...] = (), **kept: object) -> dict:
        return land.moved_carry({**self.RESOLVED, **kept}, "bbb", list(why_careful), list(reasons))

    def test_a_clean_read_of_a_resolution_carries_the_merge_review_and_the_owners_merge(self) -> None:
        carry = self.resolved()
        self.assertEqual((carry["how"], carry["merge_review"], carry["merge_why"], carry["owner_merge"]), ("resolution", True, None, "stands"))
        self.assertEqual(carry["review"], "one read of the resolution")
        self.assertEqual(land.merge_line(carry), "the merge review carried over the resolved conflict: the resolution read found nothing")

    def test_a_read_of_a_resolution_with_a_finding_carries_nothing(self) -> None:
        met = "the rebase met a conflict, and"
        for counts, said in (({"should": 1}, "0 must-fix, 1 should and 0 nit"), ({"must_fix": 1}, "1 must-fix, 0 should and 0 nit"), ({"nit": 2}, "0 must-fix, 0 should and 2 nit")):
            carry = self.resolved(reads=[self.ROUND, {**self.SOLVED, **counts}])
            self.assertEqual((carry["how"], carry["merge_review"], carry["owner_merge"]), (None, False, "ended"))
            self.assertEqual(carry["merge_why"], f"{met} the read of its resolution found {said}")
            self.assertEqual(carry["owner_why"], carry["merge_why"])
            self.assertEqual(land.merge_line(carry), f"a fresh merge agent reads it: {met} the read of its resolution found {said}")
        # the fix of a must-fix is a commit after the resolution; the read's counts stay the reason
        fixed = land.moved_carry({**self.RESOLVED, "reads": [self.ROUND, {**self.SOLVED, "must_fix": 1}]}, "ccc", [], [])
        self.assertEqual(fixed["merge_why"], f"{met} the read of its resolution found 1 must-fix, 0 should and 0 nit")

    def test_a_read_of_a_resolution_that_did_not_answer_or_did_not_run_carries_nothing(self) -> None:
        silent = {**self.SOLVED, "answered": [], "verdict": "not reviewed"}
        unread = {**self.RESOLVED["resolution"], "read": None}
        self.assertEqual(self.resolved(resolution=unread, reads=[self.ROUND, silent])["merge_why"], "the rebase met a conflict, and the read of its resolution did not answer")
        self.assertEqual(self.resolved(resolution=unread, reads=[self.ROUND])["merge_why"], "the rebase met a conflict, and the read of its resolution did not run")
        self.assertIsNone(self.resolved(resolution=unread, reads=[self.ROUND])["review"])

    def test_a_careful_request_never_carries_over_a_resolved_conflict(self) -> None:
        carry = self.resolved(why_careful=("the owner says so",))
        self.assertEqual((carry["how"], carry["merge_review"], carry["owner_merge"]), (None, False, "ended"))
        self.assertEqual(carry["merge_why"], "the rebase met a conflict, and the request is careful: the owner says so")
        self.assertEqual(carry["owner_why"], "the rebase met a conflict, and the request is careful: the owner says so")

    def test_a_rounds_careful_call_holds_against_a_resolution_read_that_makes_none(self) -> None:
        # round 1 called it careful; the read of the resolution said it is not, so `careful` now gives no reason
        called = {**self.ROUND, "kind": "full", "careful": True, "careful_why": "it reaches the topic of payments."}
        carry = self.resolved(reads=[called, self.SOLVED])
        self.assertEqual(carry["merge_why"], "the rebase met a conflict, and the request is careful: the review says so: it reaches the topic of payments")
        self.assertFalse(carry["merge_review"])

    def test_a_commit_after_the_resolution_carries_nothing(self) -> None:
        carry = land.moved_carry(self.RESOLVED, "ccc", [], [])
        self.assertEqual((carry["how"], carry["merge_why"], carry["owner_why"]), (None, "the rebase met a conflict, and a commit came after its resolution", "the rebase met a conflict, and a commit came after its resolution"))

    def test_the_items_filed_after_a_clean_read_of_the_resolution_keep_its_carry(self) -> None:
        # the read of the resolution found nothing in the change and saw one defect outside it, which `file` commits on top
        seen = {**self.SOLVED, "outside": [{**DEFECT, "item": "docs/backlog/empty-input-crashes-the-parser.md"}]}
        kept = {**self.RESOLVED, "reads": [self.ROUND, seen]}
        moved = land.filed_on(kept, "bbb", "fff")
        self.assertEqual(moved, {"resolution": {**self.RESOLVED["resolution"], "after": "fff"}})
        carry = land.moved_carry({**kept, **moved}, "fff", [], [])
        self.assertEqual((carry["how"], carry["merge_review"], carry["owner_merge"]), ("resolution", True, "stands"))
        # the tip a rebase with no conflict made, carried or not, moves the same way; a record of another tip stays
        rebased = {"proposed": "aaa", "rebase_carried": {"from": "aaa", "to": "bbb"}, "rebase_uncovered": {"from": "aaa", "to": "ccc", "why": "w"}}
        self.assertEqual(land.filed_on(rebased, "bbb", "fff"), {"rebase_carried": {"from": "aaa", "to": "fff"}})
        self.assertEqual(land.filed_on(rebased, "ccc", "fff"), {"rebase_uncovered": {"from": "aaa", "to": "fff", "why": "w"}})
        self.assertEqual(land.filed_on(kept, "bbb", "bbb"), {})

    def test_a_second_rebase_after_a_resolution_says_that_the_base_moved_again(self) -> None:
        for key in ("rebase_carried", "rebase_uncovered"):
            carry = land.moved_carry({**self.RESOLVED, key: {"from": "bbb", "to": "ccc", "why": "w"}}, "ccc", [], [])
            self.assertEqual((carry["how"], carry["merge_why"]), (None, "the rebase met a conflict, and the base moved again after its resolution"))

    def test_the_line_of_a_resolution_read_names_its_kind(self) -> None:
        self.assertEqual(self.resolved()["review"], "one read of the resolution")
        self.assertEqual(self.resolved(reads=[self.ROUND, {**self.SOLVED, "kind": "full"}])["review"], "a read of the resolution by the project's full set")

    def test_a_resolved_conflict_that_no_review_covered_keeps_the_reviews_reason(self) -> None:
        uncovered = {"from": "aaa", "to": "bbb", "why": "round 2 left 1 must-fix, and no review read the change after it"}
        carry = self.resolved(resolution={**self.RESOLVED["resolution"], "covered": False, "read": None}, reads=[self.ROUND], rebase_uncovered=uncovered)
        self.assertEqual(carry["merge_why"], "the rebase met a conflict, and no review covers the change: round 2 left 1 must-fix, and no review read the change after it")

    def test_a_carrying_tip_with_no_merge_review_on_record_starts_the_first_one(self) -> None:
        for review in (None, {"verdict": None, "tip": "aaa"}, {"verdict": "merge", "tip": "zzz"}):
            carry = self.resolved(merge_review=review)
            self.assertEqual((carry["how"], carry["merge_review"], carry["merge_why"]), ("resolution", False, "no merge review of the earlier tip was on record"))
            # the owner's merge has its own last fact, and stands
            self.assertEqual(carry["owner_merge"], "stands")
            self.assertEqual(land.merge_line(carry), "a fresh merge agent reads it: no merge review of the earlier tip was on record")

    def test_a_carrying_tip_whose_reasons_for_not_green_changed_words_ends_only_the_owners_merge(self) -> None:
        # the read of the resolution words a lowered bar in its own words, so the reasons are not the ones he saw
        carry = self.resolved(reasons=("the bar is lower in tests/a.py: the read says the builder's reason holds",))
        self.assertEqual((carry["how"], carry["merge_review"], carry["owner_merge"]), ("resolution", True, "ended"))
        self.assertEqual(carry["owner_why"], "the reasons the request is not green are not the ones the owner saw when he merged it")

    def test_the_line_of_a_moved_base_says_what_carried(self) -> None:
        sync = {"conflicting": True, "onto": "abc", "moved": True, "conflict": ["shop.txt"], "resolved": True, "carried": None}
        self.assertEqual(
            land.sync_line({**sync, "carry": self.resolved()}, "main"),
            "rebased on main after the forge called it conflicting; one conflict in shop.txt, resolved by a builder; one read of the resolution; "
            "the merge review carried over the resolved conflict: the resolution read found nothing; the checks passed again",
        )
        careful = self.resolved(why_careful=("the owner says so",))
        self.assertEqual(
            land.sync_line({**sync, "carry": careful}, "main"),
            "rebased on main after the forge called it conflicting; one conflict in shop.txt, resolved by a builder; one read of the resolution; "
            "a fresh merge agent reads it: the rebase met a conflict, and the request is careful: the owner says so; the checks passed again",
        )
        rebased = land.moved_carry({"proposed": "aaa", "rebase_carried": {"from": "aaa", "to": "bbb"}, "merge_review": {"verdict": "call", "tip": "aaa"},
                                    "sync": {"carried": {"round": 2, "must_fix": 1}}}, "bbb", [], [])
        self.assertEqual(
            land.sync_line({"onto": "abc", "moved": True, "carried": {"round": 2, "must_fix": 1}, "carry": rebased}, "main"),
            "rebased on main; the review carried over the rebase, and its open must-fix; the merge review carried over the rebase; the checks passed again",
        )


class TaskFile(unittest.TestCase):
    """A file a step names: from the working directory, else by its path inside the task directory."""

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.here = Path(folder.name) / "main"
        self.directory = Path(folder.name) / "state" / "tasks" / "gift-note"
        (self.directory / "reviews").mkdir(parents=True)
        self.here.mkdir()
        (self.directory / "reviews" / "review-1.json").write_text("{}", encoding="utf-8")

    def test_a_relative_path_that_the_working_directory_lacks_is_the_task_directorys(self) -> None:
        found = land.task_file("reviews/review-1.json", "--record", self.directory, self.here)
        self.assertEqual(found, str(self.directory / "reviews" / "review-1.json"))

    def test_the_working_directory_comes_first(self) -> None:
        (self.here / "reviews").mkdir()
        (self.here / "reviews" / "review-1.json").write_text("{}", encoding="utf-8")
        self.assertEqual(land.task_file("reviews/review-1.json", "--record", self.directory, self.here), str(self.here / "reviews" / "review-1.json"))

    def test_a_file_in_neither_place_is_refused_with_both(self) -> None:
        with self.assertRaises(land.LandError) as caught:
            land.task_file("notes.md", "--notes", self.directory, self.here)
        self.assertIn(str(self.here / "notes.md"), str(caught.exception))
        self.assertIn(str(self.directory / "notes.md"), str(caught.exception))

    def test_an_absolute_path_is_taken_as_it_is(self) -> None:
        absolute = self.directory / "reviews" / "review-1.json"
        self.assertEqual(land.task_file(str(absolute), "--record", self.directory, self.here), str(absolute))
        with self.assertRaises(land.LandError):
            land.task_file(str(self.here / "missing.json"), "--record", self.directory, self.here)


class EventLog(unittest.TestCase):
    """Each reader of the repository's event log, with an event whose words hold the characters that
    str.splitlines breaks at and json.dumps(ensure_ascii=False) keeps."""

    WORDS = "a\u2028b\u2029c\x85d"

    def setUp(self) -> None:
        import json
        import types
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        state = Path(folder.name)
        self.task = types.SimpleNamespace(slug="demo", directory=state / "tasks" / "demo")
        records = [{"ts": "2026-11-21T10:00:00Z", "event": "gate.wait", "task": "demo", "say": self.WORDS},
                   {"ts": "2026-11-21T10:00:01Z", "event": "gate.end", "task": "demo", "say": self.WORDS, "result": "passed"}]
        (state / "events.jsonl").write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")

    def test_every_reader_reads_the_event_whole(self) -> None:
        self.assertEqual([record["say"] for record in land.events_of(self.task)], [self.WORDS, self.WORDS])
        self.assertEqual([record["say"] for record in land.events_all(self.task)], [self.WORDS, self.WORDS])
        self.assertEqual([record["say"] for record in land.gate_ends(self.task)], [self.WORDS])
        self.assertEqual((land.waits_of(self.task, "2026-11-21T09:00:00Z") or {}).get("say"), self.WORDS)


class ResumedRead(unittest.TestCase):
    """A read a resumed task copied from the task it came from is compared with his approval by the
    time it had there (`was_at`), not by the time of the copy."""

    APPROVED = {"approvals": [{"by": "owner", "at": "2026-11-20T10:05:00Z", "digest": "d1", "number": 1}], "history": [], "criteria_digest": "d1"}

    def test_his_approval_after_the_read_it_came_with(self) -> None:
        copied = {"ts": "2026-11-21T09:00:00Z", "was_at": "2026-11-20T10:00:00Z", "answered": 2, "digest": "d1"}
        self.assertEqual(land.when(copied), "2026-11-20T10:00:00Z")
        self.assertTrue(land.approved_after(self.APPROVED, copied))

    def test_a_read_of_the_task_itself_after_his_approval(self) -> None:
        own = {"ts": "2026-11-21T09:00:00Z", "answered": 2, "digest": "d1"}
        self.assertFalse(land.approved_after(self.APPROVED, own))
        self.assertFalse(land.approved_alone({"approvals": [{"by": "alone", "at": "2026-11-20T10:05:00Z"}]}, own))


class InterviewApproved(unittest.TestCase):
    """`land.interview_unapproved`: a task that had an interview is proposed only over criteria the
    owner approved, or that were approved while it ran without him; a complete request (no interview)
    and the fast track ask nothing of it."""

    INTERVIEW = [{"event": "interview.start", "task": "gift-note"}, {"event": "criteria.read", "task": "gift-note"}]

    def test_an_interview_with_no_approval_of_his(self) -> None:
        self.assertTrue(land.interview_unapproved(self.INTERVIEW, [], small=False))
        self.assertTrue(land.interview_unapproved(self.INTERVIEW, [{"by": "read"}], small=False))
        self.assertTrue(land.interview_unapproved(self.INTERVIEW, [{"by": "lem"}], small=False))

    def test_his_approval_or_one_without_him(self) -> None:
        self.assertFalse(land.interview_unapproved(self.INTERVIEW, [{"by": "owner"}], small=False))
        self.assertFalse(land.interview_unapproved(self.INTERVIEW, [{"by": "lem"}, {"by": "alone"}], small=False))

    def test_a_complete_request_and_the_fast_track(self) -> None:
        self.assertFalse(land.interview_unapproved([{"event": "criteria.read", "task": "gift-note"}], [], small=False))
        self.assertFalse(land.interview_unapproved(self.INTERVIEW, [], small=True))


class FailedAttempt(unittest.TestCase):
    """`land.failed_attempt`: the record of a review that got no answer at all, which counts as an
    attempt with no careful call: nobody answered, a reason for each silent source, no finding."""

    DIED = {"attempt": 1, "tip": "a" * 40, "kind": "read", "answered": [], "silent": [{"name": "the review agent", "why": "it ended with no files"}]}

    def test_a_review_agent_that_died(self) -> None:
        self.assertTrue(land.failed_attempt(self.DIED))
        self.assertTrue(land.failed_attempt({**self.DIED, "must_fix": 0, "outside": []}))

    def test_a_review_that_answered_or_found_something_is_none(self) -> None:
        self.assertFalse(land.failed_attempt({**self.DIED, "answered": ["codex"]}))
        self.assertFalse(land.failed_attempt({**self.DIED, "must_fix": 1}))
        self.assertFalse(land.failed_attempt({**self.DIED, "outside": [{"where": "a.py", "title": "t", "what": "w"}]}))

    def test_no_reason_is_none(self) -> None:
        self.assertFalse(land.failed_attempt({**self.DIED, "silent": []}))
        self.assertFalse(land.failed_attempt({key: value for key, value in self.DIED.items() if key != "silent"}))


class ReadOfATip(unittest.TestCase):
    """A review's record and a merge agent's answer are of the tip their brief named: the record names
    it and one of another tip is refused, and each proposed tip has an answer file of its own."""

    def test_the_record_of_the_tip_now(self) -> None:
        self.assertIsNone(land.record_tip_refusal("a" * 40, "a" * 40, "gift-note"))

    def test_the_record_of_an_earlier_tip_is_refused(self) -> None:
        said = land.record_tip_refusal("a" * 40, "b" * 40, "gift-note")
        self.assertIn(f"the record is of the review of {'a' * 12}, and the branch is at {'b' * 12} now", said)
        self.assertIn("`lem land read gift-note`", said)

    def test_a_tip_that_is_no_whole_commit_is_refused(self) -> None:
        for said in (None, "a" * 9, "HEAD"):
            self.assertIn("40 hex digits", land.record_tip_refusal(said, "a" * 40, "gift-note"))

    def test_each_tip_and_base_has_its_own_brief_and_answer_file(self) -> None:
        import types
        task = types.SimpleNamespace(directory=Path("/state/tasks/gift-note"))
        self.assertEqual(land.answer_file(task, "abc123456789" + "0" * 28, "def456789012" + "0" * 28).name, "merge-answer-abc123456789-def456789012.md")
        self.assertEqual(land.brief_file(task, "abc123456789" + "0" * 28, "def456789012" + "0" * 28).name, "merge-brief-abc123456789-def456789012.md")
        self.assertNotEqual(land.answer_file(task, "a" * 40, "c" * 40), land.answer_file(task, "b" * 40, "c" * 40))
        # a brief for a later base never takes the place of the brief an agent was started with
        self.assertNotEqual(land.brief_file(task, "a" * 40, "c" * 40), land.brief_file(task, "a" * 40, "d" * 40))


class ExpectedTip(unittest.TestCase):
    """`land.expected_refusal`: a merge given the tip its caller saw (`--tip`) merges that proposal only."""

    def test_the_tip_that_was_proposed(self) -> None:
        self.assertIsNone(land.expected_refusal("a" * 40, "a" * 40, "gift-note"))
        self.assertIsNone(land.expected_refusal(None, "a" * 40, "gift-note"))

    def test_a_tip_proposed_after_it_is_refused(self) -> None:
        said = land.expected_refusal("a" * 40, "b" * 40, "gift-note")
        self.assertIn(f"the merge was asked for {'a' * 9}, and the proposal is {'b' * 9} now", said)
        self.assertIn("nothing was merged", said)

    def test_an_empty_or_short_tip_is_refused(self) -> None:
        self.assertIn("the whole commit", land.expected_refusal("", "a" * 40, "gift-note"))
        self.assertIn("the whole commit", land.expected_refusal("a" * 9, "a" * 40, "gift-note"))


class ForgeBase(unittest.TestCase):
    """`land.base_refusal`: a pull request whose base on GitHub is not the task's base is neither merged
    nor recorded as landed, and the refusal names the branch GitHub has."""

    VIEW = {"state": "OPEN", "baseRefName": "main", "headRefOid": "a" * 40}

    def test_the_tasks_base(self) -> None:
        self.assertIsNone(land.base_refusal(self.VIEW, "main", "https://github.com/acme/shop/pull/7", "gift-note"))

    def test_another_base_is_named(self) -> None:
        said = land.base_refusal({**self.VIEW, "baseRefName": "release-2"}, "main", "https://github.com/acme/shop/pull/7", "gift-note")
        self.assertIn("is on release-2 on GitHub, not on main", said)
        self.assertIn("gh pr edit 7 --base main", said)

    def test_no_base_in_the_answer_is_refused(self) -> None:
        self.assertIn("names no base branch", land.base_refusal({"state": "OPEN"}, "main", "https://github.com/acme/shop/pull/7", "gift-note"))


class ProtectedBranch(unittest.TestCase):
    """`land.protected_refusal`: the name of the branch Lem pushes or deletes, checked against the
    settings where it does so: the base and each protected branch are refused, with the way out."""

    BRANCH = {"base": "main", "protected": ["release", "fix/gift-note"]}

    def test_a_task_branch_that_is_not_protected(self) -> None:
        self.assertIsNone(land.protected_refusal("fix/footer", self.BRANCH, "pushes"))

    def test_a_protected_name_is_refused_and_named(self) -> None:
        said = land.protected_refusal("fix/gift-note", self.BRANCH, "pushes")
        self.assertIn("fix/gift-note is in branch.protected", said)
        self.assertIn("Lem pushes nothing to it", said)

    def test_the_base_is_refused(self) -> None:
        self.assertIn("main is the base branch", land.protected_refusal("main", self.BRANCH, "deletes"))


class SameChecks(unittest.TestCase):
    """`land.same_checks`: a green result holds only for the commands that ran, in their order and with
    their serial flags; a command added, removed, moved to `serial` or none at all asks for the checks."""

    SAVED = [{"command": "python3 -m unittest", "exit": 0}, {"command": "sh e2e.sh", "exit": 0, "serial": True}]

    def test_the_commands_that_ran(self) -> None:
        self.assertTrue(land.same_checks(self.SAVED, ["python3 -m unittest"], ["sh e2e.sh"]))

    def test_a_command_added_or_removed(self) -> None:
        self.assertFalse(land.same_checks(self.SAVED, ["python3 -m unittest", "ruff check"], ["sh e2e.sh"]))
        self.assertFalse(land.same_checks(self.SAVED, ["python3 -m unittest"], []))

    def test_a_command_moved_to_serial(self) -> None:
        self.assertFalse(land.same_checks(self.SAVED, [], ["python3 -m unittest", "sh e2e.sh"]))

    def test_no_command_holds_no_result(self) -> None:
        # docs/settings.md: "With no command, only the task that adds one can land"
        self.assertFalse(land.same_checks(self.SAVED, [], []))
        self.assertFalse(land.same_checks([], [], []))


class TakenFromPolish(unittest.TestCase):
    """`land.taken_from_polish`: the checks take the polish pass's result of the criteria's tests only
    when the pass committed anything, on the standard track, and the five inputs its run reported are
    the ones `lem criteria inputs` gives now; in every other case they run the tests themselves."""

    TIP, BASE, PLAN = "a1b2c3d" + "0" * 33, "b0" * 20, "/repo/.lem/worktrees/t/docs/plans/2026-11-21-t.md"
    INPUTS = {"tip": TIP, "base": BASE, "plan": PLAN, "setup": [], "serial": []}
    # the pass's run of `lem criteria red`, as `polish --done` keeps it
    RAN = {
        "task": "t", "ok": True, "digest": "d1", "base": BASE[:9], "tip": TIP[:9], "setup": [],
        "tests": [{"criterion": 1, "command": "sh tests/t.sh", "files": ["tests/t.sh"], "on_branch": 0, "on_base": 1, "problem": None}],
        "without_a_test": [], "run_without": ["t.txt"], "inputs": INPUTS,
    }
    POLISH = {"before": "c0" * 20, "after": TIP, "done": True, "commits": 1, "filed": [], "criteria": RAN}

    def taken(self, polish: dict | None = None, small: bool = False, **now: object) -> dict | None:
        return land.taken_from_polish(self.POLISH if polish is None else polish, {**self.INPUTS, **now}, small)

    def test_the_tip_the_pass_ended_on_takes_its_result_and_names_the_pass_and_its_commit(self) -> None:
        self.assertEqual(self.taken(), {**self.RAN, "taken": {"from": "polish", "at": self.TIP}})

    def test_a_base_branch_that_moved_on_with_the_same_merge_base_changes_nothing(self) -> None:
        # origin's base took commits of its own: the merge-base of the tip and it is still the base commit of both runs
        self.assertEqual(self.taken(base=self.BASE)["taken"], {"from": "polish", "at": self.TIP})

    def test_the_fast_track_runs_the_tests(self) -> None:
        self.assertIsNone(self.taken(small=True))

    def test_a_pass_with_no_commits_runs_the_tests(self) -> None:
        self.assertIsNone(self.taken({**self.POLISH, "commits": 0, "criteria": None}))

    def test_no_pass_or_one_not_done_runs_the_tests(self) -> None:
        self.assertIsNone(land.taken_from_polish(None, self.INPUTS, False))
        self.assertIsNone(self.taken({"before": self.TIP, "done": False}))

    def test_a_commit_after_the_pass_runs_the_tests(self) -> None:
        # a builder's repair of a failed check: the branch is at e4f5a6b now
        self.assertIsNone(self.taken(tip="e4f5a6b" + "0" * 33))

    def test_a_rebased_tip_runs_the_tests_though_after_has_its_new_name(self) -> None:
        rebased = "f0" * 20
        # `through_rebase` gives `after` the rebased commit's name; the run still names the tip it ran on
        self.assertIsNone(self.taken({**self.POLISH, "after": rebased}, tip=rebased, base="d0" * 20))

    def test_after_decides_nothing_when_the_inputs_are_the_same(self) -> None:
        self.assertEqual(self.taken({**self.POLISH, "after": "f0" * 20})["taken"]["at"], self.TIP)
        self.assertEqual(self.taken({**self.POLISH, "after": None})["taken"]["at"], self.TIP)

    def test_a_merge_base_that_moved_under_the_same_tip_runs_the_tests(self) -> None:
        # the base branch took in a commit of the branch: the same tip has another base commit
        self.assertIsNone(self.taken(base="d0" * 20))

    def test_another_plan_file_runs_the_tests(self) -> None:
        self.assertIsNone(self.taken(plan="/repo/.lem/worktrees/t/docs/plans/2026-11-22-t.md"))

    def test_another_serial_or_setup_runs_the_tests(self) -> None:
        self.assertIsNone(self.taken(serial=["sh tests/e2e"]))
        self.assertIsNone(self.taken(setup=["npm ci"]))

    def test_no_inputs_now_or_a_run_with_none_runs_the_tests(self) -> None:
        self.assertIsNone(land.taken_from_polish(self.POLISH, None, False))
        self.assertIsNone(self.taken({**self.POLISH, "criteria": {**self.RAN, "inputs": None}}))
        self.assertIsNone(self.taken({**self.POLISH, "criteria": {**self.RAN, "ok": False}}))

    def test_the_end_of_the_checks_names_the_commit_of_a_taken_result_and_nothing_for_a_run(self) -> None:
        # `taken_at` gives the `taken` field of the run's `gate.end`
        self.assertEqual(land.taken_at(self.taken()), self.TIP[:9])
        self.assertIsNone(land.taken_at(self.RAN))
        self.assertIsNone(land.taken_at(None))


M1, M2, M3 = "1" * 40, "2" * 40, "3" * 40
TIP = "a" * 40


class ReadOfAMovedBase(unittest.TestCase):
    """A base that moved after the checks: what the merge agent's brief says moved, its call on the move
    as its answer's second line, which base a read covers, what a safe read answers, the line of the
    merge, and what `propose` carries onto a new tip."""

    def test_the_base_call_is_the_second_line(self) -> None:
        self.assertEqual(land.base_call_of("Verdict: merge. Fine.\nBase: safe. B changed only docs/board.md.\n\nMore."), ("safe", "B changed only docs/board.md."))
        self.assertEqual(land.base_call_of("**Verdict: call.** Careful.\n**Base: another round.** B renamed `total`, which the change calls."),
                         ("another round", "B renamed `total`, which the change calls."))
        self.assertEqual(land.base_call_of("Verdict: merge.\n\nbase: Another Round: the settings moved."), ("another round", "the settings moved."))

    def test_no_base_call_or_no_why_is_none(self) -> None:
        self.assertIsNone(land.base_call_of("Verdict: merge. Fine."))
        self.assertIsNone(land.base_call_of("Verdict: merge. Fine.\nIts test proves it.\nBase: safe. Late."))
        self.assertIsNone(land.base_call_of("Verdict: merge. Fine.\nBase: safe."))
        self.assertIsNone(land.base_call_of("Verdict: merge. Fine.\nBase: maybe. Who knows."))

    def test_what_moved_beside_the_change(self) -> None:
        moved = land.moved_of(M1, M2, "abc1234\0docs: the board\ndef5678\0fix: land\n", ["docs/board.md", "land.py"], ["land.py", "tests/t.sh"])
        self.assertEqual(moved, {"checks_ran_on": M1, "base_now": M2, "range": f"{M1}..{M2}", "files": ["docs/board.md", "land.py"], "overlap": ["land.py"],
                                 "commits": [{"commit": "abc1234", "subject": "docs: the board"}, {"commit": "def5678", "subject": "fix: land"}]})

    def test_no_file_moved_is_no_move(self) -> None:
        # an empty commit on the base moves nothing
        self.assertIsNone(land.moved_of(M1, M2, "abc1234\0chore: empty\n", [], ["land.py"]))

    def test_a_safe_read_covers_its_own_base(self) -> None:
        review = {"tip": TIP, "verdict": "merge", "base": M2, "base_call": "safe", "base_why": "docs only"}
        self.assertEqual(land.read_base(review, TIP, None), M2)

    def test_no_read_covers_a_base_without_a_safe_call(self) -> None:
        self.assertIsNone(land.read_base({"tip": TIP, "base": M2, "base_call": "another round"}, TIP, None))
        self.assertIsNone(land.read_base({"tip": TIP, "base": M1, "base_call": None}, TIP, None))
        self.assertIsNone(land.read_base({"tip": "b" * 40, "base": M2, "base_call": "safe"}, TIP, None))
        self.assertIsNone(land.read_base(None, TIP, None))

    def test_after_another_round_no_read_of_the_tip_covers_a_base(self) -> None:
        self.assertIsNone(land.read_base({"tip": TIP, "base": M3, "base_call": "safe"}, TIP, TIP))
        self.assertEqual(land.read_base({"tip": TIP, "base": M3, "base_call": "safe"}, TIP, "b" * 40), M3)

    def test_a_safe_read_answers_only_lems_base_refusal_of_its_tip(self) -> None:
        base = {"tip": TIP, "by": "owner", "from": "lem", "kind": "base"}
        self.assertTrue(land.refusal_answered(base, TIP))
        self.assertFalse(land.refusal_answered({**base, "tip": "b" * 40}, TIP))
        self.assertFalse(land.refusal_answered({**base, "kind": "rule"}, TIP))
        self.assertFalse(land.refusal_answered({**base, "kind": "tip"}, TIP))
        self.assertFalse(land.refusal_answered({"tip": TIP, "from": "github", "said": "a required review"}, TIP))
        self.assertFalse(land.refusal_answered(None, TIP))

    def test_a_read_on_the_checks_base_answers_lems_base_refusal_too(self) -> None:
        # main moved, the merge was refused, then a revert gave main the checks' tree again: the brief named
        # the checks' own base, its read has no call on a move, and it answers the refusal as a safe read does
        base = {"tip": TIP, "by": "merger", "from": "lem", "kind": "base"}
        self.assertTrue(land.read_answers(base, TIP, None, True))
        self.assertTrue(land.read_answers(base, TIP, "safe", False))
        self.assertFalse(land.read_answers(base, TIP, "another round", False))
        self.assertFalse(land.read_answers(base, TIP, None, False))
        self.assertFalse(land.read_answers({**base, "kind": "rule"}, TIP, None, True))
        self.assertFalse(land.read_answers({"tip": TIP, "from": "github", "said": "a required review"}, TIP, None, True))

    def test_the_line_names_both_bases_and_the_why(self) -> None:
        line = land.base_line("main", M1, M2, "B changed only docs/board.md.")
        self.assertEqual(line, f"The checks ran on main at {M1[:9]}; it merged on main at {M2[:9]}, after the merge agent's read of what moved: B changed only docs/board.md.")

    def test_a_base_no_read_covered_is_named(self) -> None:
        line = land.uncovered_line("main", M1, M3, M2)
        self.assertIn(f"it merged on main at {M3[:9]}, which no read of the merge agent covered (its read covered {M2[:9]})", line)
        self.assertIn(f"The checks ran on main at {M1[:9]}", line)

    def test_the_refusal_names_the_read_or_a_new_landing(self) -> None:
        read = land.moved_refusal("gift-note", "origin/main", ["docs/board.md"], "merger", None, False)
        self.assertIn("origin/main moved after the checks ran, by files (docs/board.md)", read)
        self.assertIn("`lem land merge-review gift-note` writes its brief", read)
        self.assertNotIn("lem land start", read)
        later = land.moved_refusal("gift-note", "origin/main", ["docs/board.md", "a", "b", "c", "d", "e"], "owner", M2, False)
        self.assertIn(f"the read of {M2[:9]} said safe, and it covers no later base", later)
        self.assertIn("(docs/board.md, a, b, c, d, ...)", later)
        self.assertIn("the owner's merge stands, and goes through after a read that says `Base: safe.`", later)
        again = land.moved_refusal("gift-note", "origin/main", ["land.py"], "merger", None, True)
        self.assertIn("the merge agent's read of this tip said another round", again)
        self.assertIn("lem land start", again)

    def test_a_carried_review_drops_its_call_on_the_base(self) -> None:
        review = {"tip": TIP, "verdict": "merge", "calls": False, "why": None, "by": "claude/opus:high", "at": "2026-11-22T10:00:00Z",
                  "base": M2, "base_call": "another round", "base_why": "B renamed total"}
        carried = land.carried_review(review, "b" * 40, False, None, TIP)
        self.assertEqual(carried, {"tip": "b" * 40, "verdict": "merge", "calls": False, "why": None, "by": "claude/opus:high", "at": "2026-11-22T10:00:00Z",
                                   "carried_from": TIP})
