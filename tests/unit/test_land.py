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
        self.assertEqual(land.tap_after(tap, "aaa", "bbb", rebased, ["the bar is lower"]), ({**tap, "tip": "bbb"}, None))
        gone, why = land.tap_after(tap, "aaa", "ccc", rebased, ["the bar is lower"])
        self.assertIsNone(gone)
        self.assertIn("a commit came after the rebase", why)
        gone, why = land.tap_after(tap, "aaa", "bbb", rebased, [])
        self.assertIsNone(gone)
        self.assertIn("not the ones the owner saw", why)
        self.assertEqual(land.tap_after(None, "aaa", "bbb", rebased, []), (None, None))
