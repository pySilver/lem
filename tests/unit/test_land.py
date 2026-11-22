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
        self.assertTrue(land.carried_over("aaa", "bbb", rebased))
        self.assertTrue(land.carried_over("aaa", "aaa", None))
        # a commit after the rebase, a conflict (no record), or a first proposal carry nothing
        self.assertFalse(land.carried_over("aaa", "ccc", rebased))
        self.assertFalse(land.carried_over("aaa", "bbb", None))
        self.assertFalse(land.carried_over(None, "bbb", rebased))

    def test_the_owners_merge_stands_while_the_change_and_its_reasons_stay(self) -> None:
        tap = {"tip": "aaa", "not_green": ["the bar is lower"], "via": "server", "at": "2026-11-21T10:00:00Z"}
        rebased = {"from": "aaa", "to": "bbb"}
        self.assertEqual(land.tap_after(tap, "aaa", "bbb", rebased, None, ["the bar is lower"]), ({**tap, "tip": "bbb"}, None))
        gone, why = land.tap_after(tap, "aaa", "ccc", rebased, None, ["the bar is lower"])
        self.assertIsNone(gone)
        self.assertIn("a commit came after the rebase", why)
        gone, why = land.tap_after(tap, "aaa", "bbb", rebased, None, [])
        self.assertIsNone(gone)
        self.assertIn("not the ones the owner saw", why)
        self.assertEqual(land.tap_after(None, "aaa", "bbb", rebased, None, []), (None, None))

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

    def test_an_ended_merge_says_that_no_review_covers_the_change(self) -> None:
        tap = {"tip": "aaa", "not_green": ["two rounds reviewed it"], "via": "server", "at": "2026-11-22T10:00:00Z"}
        uncovered = {"from": "aaa", "to": "bbb", "why": "round 2 left 1 must-fix, and no review read the change after it"}
        gone, why = land.tap_after(tap, "aaa", "bbb", None, uncovered, ["two rounds reviewed it"])
        self.assertIsNone(gone)
        self.assertEqual(why, "no review covers the change: round 2 left 1 must-fix, and no review read the change after it")
        self.assertNotIn("a commit came after the rebase", why)
        self.assertNotIn("conflict", why)
        # a commit after that rebase is a cause of its own
        gone, why = land.tap_after(tap, "aaa", "ccc", None, uncovered, ["two rounds reviewed it"])
        self.assertIn("a commit came after the rebase", why)

    def test_an_ended_merge_after_a_covering_review_keeps_its_line(self) -> None:
        tap = {"tip": "aaa", "not_green": [], "via": "server", "at": "2026-11-22T10:00:00Z"}
        today = "the change is not the one the owner merged: a commit came after the rebase, or the rebase met a conflict"
        # a review covered the change, so no rebase kept a reason it does not: a commit after the rebase
        self.assertEqual(land.tap_after(tap, "aaa", "ccc", {"from": "aaa", "to": "bbb"}, None, []), (None, today))
        # a review whose change found nothing to fix, and a rebase that met a conflict in README.md: no rebase_carried
        self.assertEqual(land.tap_after(tap, "aaa", "bbb", None, None, []), (None, today))


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
