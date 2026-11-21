"""What a landing reads of a repository before its step, as calls of the functions it calls with the
settings it loaded once: `may_land`, which `lem project may-land` prints. Whether the base branch
exists is a fact only git shows, and tests/lem-settings.sh checks it in a real repository. And what
`lem project prune` does with each task (`task_calls`); what it removes from a folder is
tests/lem-state.sh's.

    python3 -B -m unittest discover -s tests/unit
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
import project  # noqa: E402

# A checkout that is not on disk: the rules resolve paths under it and find nothing there.
ROOT = Path("/lem-unit/repo")


def settings(*lines: str) -> dict:
    """The settings of a main checkout on its base branch whose file holds these lines."""
    raw = project.settings_of("\n".join(lines) + "\n", ROOT / project.SETTINGS, tuple(project.TABLES))
    return project.decide(ROOT, ROOT, raw, {}, raw, None)


class MayLand(unittest.TestCase):
    """The refusals of `may-land` that the settings decide, before git is asked for the branch."""

    def refused(self, target: str, *lines: str) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            project.may_land(settings(*lines), target)
        return str(caught.exception)

    def test_a_protected_branch(self):
        self.assertIn("'release' is protected", self.refused("release", "[branch]", 'base = "main"', 'protected = ["release"]'))

    def test_settings_that_name_no_base(self):
        self.assertIn("names no branch.base", self.refused("main"))

    def test_a_branch_that_is_not_the_base(self):
        self.assertIn("land on 'main', not on 'feature'", self.refused("feature", "[branch]", 'base = "main"'))


class TrackOf(unittest.TestCase):
    """The track of a task, from the newest of its state lines that tells it (state.md, newest block first)."""

    def test_an_interview_above_the_fast_tracks_builder_is_the_standard_track(self):
        # `/lem standard-track` of a task whose small change had started: its interview waits now
        state = "2026-11-19T10:00Z held: the interview waits for the owner\ntype: feat, because the export gets a note\n\n2026-11-19T09:50Z building: small change: one builder"
        self.assertEqual(project.track_of(state), "standard")

    def test_the_fast_tracks_builder_and_a_lead(self):
        self.assertEqual(project.track_of("2026-11-19T09:50Z building: small change: one builder"), "fast")
        self.assertEqual(project.track_of("2026-11-19T09:50Z building: lead: builder\n\n2026-11-19T09:40Z building: small change: one builder"), "standard")
        self.assertIsNone(project.track_of("2026-11-19T09:50Z queued: it waits for a free place"))


class QueuedRefusal(unittest.TestCase):
    """The refusal of `may-start` for a queued task names the way out of a need and of the owner's order."""

    def test_both_ways_out_and_the_owners_word_first(self):
        said = project.queued_refusal("tests-at-the-unit-level", "one-lem-parallel-landings", "open")
        self.assertTrue(said.startswith("the task 'tests-at-the-unit-level' is queued after 'one-lem-parallel-landings', which is open: "
                                        "it starts when one-lem-parallel-landings is landed or answered"))
        self.assertIn("needs the result of one-lem-parallel-landings and no longer does, write its state `queued` again without the `after:` line", said)
        self.assertIn("first line says `the owner's order`, only the owner's word removes the order", said)
        self.assertLess(said.index("lem decisions log tests-at-the-unit-level --by owner --words"), said.index("the owner's order was removed"))
        self.assertIn("which is no task:", project.queued_refusal("a", "b", None))


class Parked(unittest.TestCase):
    """The owner's park: a task no agent works on is put aside, and it leaves `parked` only by a drop
    or by `resume`, which writes the block the park put aside."""

    def test_only_a_task_no_agent_works_on_is_parked(self):
        for now in project.PARKABLE:
            self.assertIsNone(project.parked_refusal("t", now, "parked"), now)
        self.assertIn("its lead or its investigator works now", project.parked_refusal("t", "building", "parked"))
        self.assertIn("its build is done", project.parked_refusal("t", "landing", "parked"))

    def test_a_parked_task_takes_a_drop_and_resume_only(self):
        self.assertIn("`lem project resume t` brings it back", project.parked_refusal("t", "parked", "building"))
        self.assertIn("is parked", project.parked_refusal("t", "parked", "held"))
        self.assertIsNone(project.parked_refusal("t", "parked", "dropped"))
        self.assertIsNone(project.parked_refusal("t", "parked", "held", resumed=True))

    def test_resume_finds_the_block_before_the_park(self):
        state = ("2026-11-20T02:00Z parked: the owner parked it: wait for the merchants\n\n"
                 "2026-11-20T01:00Z held: breaker 2 waits for the owner\nThe note has no place: no option keeps the approved criteria\n\n"
                 "2026-11-20T00:00Z building: task 2 of 3")
        blocks = project.blocks_of(state)
        self.assertEqual([block["status"] for block in blocks], ["parked", "held", "building"])
        self.assertEqual(next(block for block in blocks if block["status"] != "parked")["lines"],
                         ["breaker 2 waits for the owner", "The note has no place: no option keeps the approved criteria"])


class FirstLine(unittest.TestCase):
    """The task's first line to the owner (`stages/new.md`, "The request", step 7), which `state` prints
    as `say` for the block that names the task's path, composed from the files of its directory."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="lem-first-line-"))
        self.addCleanup(shutil.rmtree, self.dir)
        self.main = self.dir / "repo"
        self.main.mkdir()
        self.task = self.dir / "task"
        self.task.mkdir()

    def write(self, name: str, text: str) -> None:
        (self.task / name).write_text(text)

    def say(self, status: str, *lines: str, older: str = "", branch: str | None = None, night: bool = False) -> str | None:
        return project.opening_line_of(self.task, self.main, status, list(lines), older, branch, night)

    def test_the_fast_track_quotes_its_criterion(self):
        self.write("ask.txt", "fix the typo recieve in the README\n")
        self.write("criteria.md", "## Acceptance criteria\n\nSize: small, because one word.\n\n1. The README says receive, not recieve.\n")
        self.write("brief.md", "Read SKILL_DIR/prompts/small.md and follow it.\ntask: readme-receive-typo\nbranch: docs/readme-receive-typo\n")
        self.assertEqual(self.say("building", "small change: one builder", "type: docs, because a word of the README"),
                         'docs: "the README says receive, not recieve". Branch docs/readme-receive-typo. '
                         "Fast track: one builder, the checks, one read, then the pull request. Nothing waits for you. "
                         "Wrong read? /lem standard-track, /lem be-careful.")

    def test_the_standard_track_with_an_interview_quotes_the_outcome(self):
        self.write("ask.txt", "Add the gift note to the CSV export, Ania asked twice\n")
        self.write("task.md", "# Gift note\n\n## Outcome\n\nAn export holds the gift note. The shop reads it.\n\n## Done when\n\n- a row\n")
        self.write("brief.md", "Read SKILL_DIR/prompts/lead.md and follow it.\nbranch: feat/gift-note-in-export\nstop after the plan: no\n")
        self.assertEqual(self.say("held", "the interview waits for the owner", "type: feat, because the export gets a column"),
                         'feat: "an export holds the gift note". Branch feat/gift-note-in-export. Standard track: an interview here now, '
                         "then acceptance criteria for your yes. After that it runs to the pull request without you. Wrong read? /lem be-careful.")

    def test_a_plan_asked_for_says_so(self):
        self.write("ask.txt", "/lem plan the gift note in the export\n")
        self.write("brief.md", "branch: feat/gift-note\nstop after the plan: yes\n")
        said = self.say("held", "the interview waits for the owner", "type: feat, because a new column")
        self.assertIn("Standard track, because you asked for its plan: an interview here now", said)
        self.assertIn("After that a lead writes the plan and stops for you to read it.", said)

    def test_an_investigation_names_no_track(self):
        self.write("ask.txt", "Invoices show 0 after a refund since yesterday. Anna saw it on 1042.\n")
        self.assertEqual(self.say("building", "an investigator reproduces the bug and finds its cause", "investigation: bug",
                                  "type: fix, because the total is wrong today", branch="fix/invoice-total-after-refund"),
                         'fix: "invoices show 0 after a refund since yesterday". Branch fix/invoice-total-after-refund. '
                         "An investigator finds the cause first. Then I tell you what it found: the fast track, the standard track, or no bug.")
        said = self.say("building", "an investigator finds the answer", "investigation: question", "type: question, because a report")
        self.assertTrue(said.endswith("An investigator finds the answer first. Then I tell you the answer."), said)

    def test_a_complete_request_names_what_stands_in_for_the_interview(self):
        self.write("ask.txt", "Export the gift note\n")
        self.write("ticket.txt", "SHOP-12\n")
        self.write("brief.md", "Read SKILL_DIR/prompts/lead.md and follow it.\nbranch: shop-12-export-the-gift-note\nrequest by: someone else\n")
        said = self.say("building", "lead: builder", "type: feat, because a new column")
        self.assertEqual(said, 'feat: "export the gift note". Branch shop-12-export-the-gift-note. Standard track, with no interview, since the ticket '
                               "says what is wanted: a lead writes acceptance criteria, the personas read them, and they wait for your yes. "
                               "After that it runs to the pull request without you. Wrong read? /lem be-careful.")

    def test_careful_comes_first(self):
        self.write("ask.txt", "Round the card fee up\n")
        said = self.say("held", "the interview waits for the owner", "type: fix, because the fee is wrong",
                        "careful: this changes how a customer is charged")
        self.assertTrue(said.startswith('Careful: this changes how a customer is charged. fix: "round the card fee up".'), said)
        self.write("brief.md", "branch: fix/card-fee\ncareful: the owner says so\n")
        self.assertTrue(self.say("held", "the interview waits for the owner", "type: fix, because the fee").startswith("Careful: the owner says so. fix:"))

    def test_a_night_task_gets_none(self):
        self.write("ask.txt", "docs/backlog/export-note.md\n")
        self.assertIsNone(self.say("building", "small change: one builder", "type: docs, because a line", night=True))

    def test_no_branch_yet_leaves_the_branch_out(self):
        self.write("ask.txt", "Add the gift note to the export\n")
        said = self.say("held", "the interview waits for the owner", "type: feat, because a new column")
        self.assertNotIn("Branch", said)
        self.assertTrue(said.startswith('feat: "add the gift note to the export". Standard track:'), said)

    def test_a_second_block_gets_none(self):
        self.write("ask.txt", "Add the gift note\n")
        older = "2026-11-21T10:00Z held: the interview waits for the owner\ntype: feat, because a new column"
        self.assertIsNone(self.say("building", "lead: builder", "type: feat, because a new column", older=older))
        self.assertIsNone(self.say("held", "the criteria wait for the owner"))
        self.assertIsNone(self.say("held", "breaker 1 waits for the owner", "type: feat, because a new column"))

    def test_a_queued_task_says_what_it_waits_for(self):
        self.write("ask.txt", "Put the gift note on the label too\n")
        self.write("brief.md", "Read SKILL_DIR/prompts/small.md and follow it.\nbranch: feat/note-on-label\n")
        said = self.say("queued", "it waits for the export", "after: gift-note-in-export", "type: feat, because a new line")
        self.assertIn("Fast track: one builder", said)
        self.assertIn("It waits for gift-note-in-export, and starts when that task lands or is answered.", said)

    def test_a_task_queued_by_his_order_says_so_and_his_word_that_starts_it(self):
        self.write("ask.txt", "After one-lem-parallel-landings: unit cases for the functions that are pure today\n")
        self.write("brief.md", "Read SKILL_DIR/prompts/lead.md and follow it.\nbranch: test/tests-at-the-unit-level\nstop after the plan: no\n")
        order = "the owner's order: \"After one-lem-parallel-landings\""
        said = self.say("queued", order, "after: one-lem-parallel-landings", "type: test, because tests only", "then: the interview")
        self.assertEqual(said, 'test: "after one-lem-parallel-landings: unit cases for the functions that are pure today". '
                               "Branch test/tests-at-the-unit-level. It waits for one-lem-parallel-landings, as you said; "
                               '"start task now" starts it before that. Then the standard track: an interview here, then acceptance '
                               "criteria for your yes. After that it runs to the pull request without you. Wrong read? /lem be-careful.")
        # the fast track's line puts his word in place of "Nothing waits for you"
        self.write("brief.md", "Read SKILL_DIR/prompts/small.md and follow it.\nbranch: test/tests-at-the-unit-level\n")
        fast = self.say("queued", order, "after: one-lem-parallel-landings", "type: test, because tests only", "then: the fast track")
        self.assertIn("as you said; \"start task now\" starts it before that. Then the fast track: one builder,", fast)
        self.assertNotIn("Nothing waits for you", fast)
        # another session names the task in his word too
        named = project.opening_line_of(self.task, self.main, "queued", [order, "after: one-lem-parallel-landings", "type: test, because x",
                                        "then: the lead"], "", None, False, task="tests-at-the-unit-level")
        self.assertIn('"start tests-at-the-unit-level now" starts it before that. Then the standard track, with no interview,', named)

    def test_a_task_put_after_the_one_task_that_fits_says_which(self):
        self.write("ask.txt", "when the gift note lands, keep the notes in their order\n")
        said = self.say("queued", "the owner's order: \"when the gift note lands\"", "after: gift-note-in-export",
                        "the one open task that fits his words", "type: feat, because a new order", "then: the interview")
        self.assertIn('It waits for gift-note-in-export, the one open task that fits "when the gift note lands"; '
                      '"start task now" starts it before that.', said)

    def test_another_session_names_the_task_and_its_commands(self):
        self.write("ask.txt", "the footer says Terms, not Terms and Conditions\n")
        self.write("criteria.md", "## Acceptance criteria\n\nSize: small, because one word.\n\n1. The footer says Terms.\n")
        self.write("brief.md", "Read SKILL_DIR/prompts/small.md and follow it.\nbranch: fix/footer-terms\n")
        lines = ("building", ["small change: one builder", "type: fix, because the footer is wrong today"], "", None, False)
        self.assertEqual(project.opening_line_of(self.task, self.main, *lines, task="footer-terms"),
                         'footer-terms · fix: "the footer says Terms". Branch fix/footer-terms. '
                         "Fast track: one builder, the checks, one read, then the pull request. Nothing waits for you. "
                         "Wrong read? /lem standard-track footer-terms, /lem be-careful footer-terms.")
        # the task's own session keeps the form without the name
        self.assertTrue(project.opening_line_of(self.task, self.main, *lines).endswith("Wrong read? /lem standard-track, /lem be-careful."))
        self.write("brief.md", "branch: fix/card-fee\n")
        said = project.opening_line_of(self.task, self.main, "held", ["the interview waits for the owner", "type: fix, because the fee",
                                       "careful: this changes how a customer is charged"], "", None, False, task="card-fee")
        self.assertTrue(said.startswith("card-fee · Careful: this changes how a customer is charged. fix:"), said)
        self.assertTrue(said.endswith("Wrong read? /lem be-careful card-fee."), said)
        # the interview and the investigator's answer are the task's session's, never the caller's
        self.assertIn("Standard track: an interview in its own session now,", said)
        found = project.opening_line_of(self.task, self.main, "building", ["an investigator finds the cause", "investigation: bug", "type: fix, because x"],
                                        "", None, False, task="card-fee")
        self.assertTrue(found.endswith("Then its session tells you what it found: the fast track, the standard track, or no bug."), found)
        self.assertIsNone(project.opening_line_of(self.task, self.main, *lines[:4], True, task="footer-terms"))

    def test_the_words_it_quotes(self):
        self.assertEqual(project.first_sentence("The footer says Terms.  It is wrong."), "The footer says Terms")
        self.assertEqual(project.in_his_words("README says it"), "README says it")
        self.assertEqual(project.in_his_words("I see 0"), "I see 0")
        self.assertEqual(project.criterion_of("1. A refund lowers the total,\n   never below 0:\n   1. Invoice 1042\n"), "A refund lowers the total, never below 0")
        self.assertIsNone(project.outcome_of("## Outcome\n\n1. Invoice 1042 is 100 EUR.\n2. It shows 70.\n"))
        self.assertEqual(project.outcome_of("## Outcome\n\n**Today:**\n\n1. step\n\nThe invoice shows 70 EUR after the refund.\n"),
                         "The invoice shows 70 EUR after the refund")


# Words that hold the three characters str.splitlines breaks at and json.dumps(ensure_ascii=False) keeps.
SEPARATED = "a\u2028b\u2029c\x85d"


class EventLog(unittest.TestCase):
    """The repository's event log, read back with words that hold a line separator."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        project.STATE_ROOTS[self.root] = self.root / "state"
        self.addCleanup(project.STATE_ROOTS.pop, self.root)
        (self.root / "state").mkdir()

    def test_an_event_whose_words_hold_a_line_separator_reads_as_one_event(self):
        project.append_event(self.root, "gate.end", "demo", {"say": SEPARATED, "result": "passed"})
        found = project.events_named(self.root, "gate.end")
        self.assertEqual([record["say"] for record in found], [SEPARATED])


class Prune(unittest.TestCase):
    """What `lem project prune` does with each task, from its state.md and the event log alone: an open
    task is never touched, an ended one goes once nothing of it was logged for the days, and a state that
    does not read or that the log does not agree with is skipped with why, never guessed at."""

    CUTOFF = project.datetime(2026, 11, 1, tzinfo=project.timezone.utc)

    @staticmethod
    def state(status: str) -> str:
        return f"2026-10-20T10:00Z {status}: the line\n"

    def calls(self, found: list[dict], events: list[dict]) -> dict:
        return {call["task"]: (call["call"], call.get("why", "")) for call in project.task_calls(found, events, self.CUTOFF)}

    def test_each_call(self):
        found = [{"slug": slug, "state": text} for slug, text in (
            ("old-landed", self.state("landed")), ("late-event", self.state("dropped")), ("still-open", self.state("open")),
            ("no-state-yet", None), ("broken", "not a state line\n"), ("no-event", self.state("answered")),
            ("log-disagrees", self.state("landed")), ("bad-time", self.state("landed")))]
        events = [
            {"ts": "2026-10-20T10:00:00Z", "event": "task.state", "task": "old-landed", "status": "landed"},
            {"ts": "2026-10-20T10:00:00Z", "event": "task.state", "task": "late-event", "status": "dropped"},
            # an event after the end, a ticket's step, makes the task young again: its last event is what counts
            {"ts": "2026-11-02T08:00:00Z", "event": "ticket.step", "task": "late-event"},
            {"ts": "2026-10-01T10:00:00Z", "event": "task.state", "task": "still-open", "status": "open"},
            {"ts": "2026-10-20T10:00:00Z", "event": "task.state", "task": "log-disagrees", "status": "open"},
            {"ts": "yesterday", "event": "task.state", "task": "bad-time", "status": "landed"},
        ]
        calls = self.calls(found, events)
        self.assertEqual({task: call for task, (call, _why) in calls.items()}, {
            "old-landed": "old", "late-event": "young", "still-open": "open", "no-state-yet": "open", "broken": "skip",
            "no-event": "skip", "log-disagrees": "skip", "bad-time": "skip"})
        self.assertIn("does not read", calls["broken"][1])
        self.assertIn("holds no event of it", calls["no-event"][1])
        self.assertIn("says landed, and the newest state of it in the event log says open", calls["log-disagrees"][1])
        self.assertIn("'yesterday'", calls["bad-time"][1])


if __name__ == "__main__":
    unittest.main()
