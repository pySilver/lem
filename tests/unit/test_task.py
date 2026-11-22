"""What a landing reads of a repository before its step, as calls of the functions it calls with the
settings it loaded once: `may_land`, which `lem project may-land` prints. Whether the base branch
exists is a fact only git shows, and tests/lem-settings.sh checks it in a real repository. And what
`lem project prune` does with each task (`task_calls`); what it removes from a folder is
tests/lem-state.sh's.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import importlib
import io
import json
import shlex
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

    def test_the_fast_tracks_wait_for_his_yes_and_the_standard_tracks(self):
        self.assertEqual(project.track_of(f"2026-11-19T09:50Z held: {project.FAST_WAIT}\ntype: fix, because a word"), "fast")
        self.assertEqual(project.track_of("2026-11-19T09:50Z held: the criteria wait for the owner\nnobody confused"), "standard")


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


class DroppedRefusal(unittest.TestCase):
    """The refusal of `may-start` for a task queued behind a dropped task prints the commands of the
    owner's "start SLUG now" whole, from the task's own block, for the agent to run on his word."""

    ORDER = ["the owner's order: \"After the \"gift note\" task\"", "after: gift-note-in-export",
             "type: feat, because a new order", "then: the interview"]
    # his reply, with a double quote and an apostrophe of his, put in as the refusal says: '\'' for his '
    REPLY = 'start it, it\'s "fine"'

    def run_as_printed(self, command: str) -> list[str]:
        """The arguments the shell gives the command after his words go in where HIS WORDS stands."""
        return shlex.split(command.replace(project.HIS_WORDS, self.REPLY.replace("'", "'\\''")))

    def test_his_order_is_logged_then_the_block_is_written_again_without_its_after_line(self):
        logged, written = project.start_commands("export-notes-in-order", self.ORDER)
        self.assertEqual(self.run_as_printed(logged), [
            "lem", "decisions", "log", "export-notes-in-order", "--by", "owner", "--what", "the owner's order",
            "--chose", "start now", "--why", "his word", "--words", self.REPLY])
        self.assertEqual(self.run_as_printed(written), [
            "lem", "project", "state", "export-notes-in-order", "queued", "the owner's order: \"After the \"gift note\" task\"",
            "type: feat, because a new order", "then: the interview", f"the owner's order was removed: \"{self.REPLY}\""])

    def test_a_need_gets_its_block_again_and_no_log(self):
        need = ["it needs the cache that caches-the-list adds", "after: caches-the-list", "then: the lead"]
        self.assertEqual([shlex.split(c) for c in project.start_commands("shows-the-list", need)],
                         [["lem", "project", "state", "shows-the-list", "queued", need[0], "then: the lead"]])

    def test_the_after_line_is_read_from_every_line_its_first_too(self):
        first = ["after: gift-note-in-export", "type: fix, because the order is lost", "then: the fast track"]
        self.assertEqual(project.after_in(first), "gift-note-in-export")
        self.assertEqual(project.after_in(self.ORDER), "gift-note-in-export")
        self.assertIsNone(project.after_in(["the owner's order was removed: \"start it\"", "then: the interview"]))
        self.assertEqual([shlex.split(c) for c in project.start_commands("t", first)],
                         [["lem", "project", "state", "t", "queued", "type: fix, because the order is lost", "then: the fast track"]])

    def test_the_refusal_says_his_word_comes_first_and_prints_each_command_on_its_line(self):
        said = project.dropped_refusal("export-notes-in-order", "gift-note-in-export", self.ORDER)
        self.assertTrue(said.startswith("the task 'export-notes-in-order' is queued after 'gift-note-in-export', which was dropped"))
        self.assertIn("nothing below runs before it", said)
        self.assertIn("run `lem project may-start export-notes-in-order` once more and run the commands that it prints then, never ones printed before his word", said)
        self.assertIn("a single quote of his is written '\\''", said)
        self.assertIn("/lem drop export-notes-in-order", said)
        printed = [row for row in said.splitlines() if row.startswith("lem ")]
        self.assertEqual(printed, project.start_commands("export-notes-in-order", self.ORDER))
        self.assertNotIn(project.HIS_WORDS, project.dropped_refusal("t", "a", ["it needs a", "after: a"]))


class FixedForm(unittest.TestCase):
    """`state` refuses a line that starts as one of the three lines the first line reads and is not in
    its form, and takes every other line as it is."""

    def refused(self, line: str) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            project.fixed_form(line)
        return str(caught.exception)

    def test_each_of_the_three_in_another_form_names_its_form(self):
        self.assertIn("`the owner's order: \"HIS WORDS\"`", self.refused("the owner's order: After gift-note-in-export"))
        self.assertIn("`the owner's order: \"HIS WORDS\"`", self.refused("the owner's order: \"After gift-note-in-export\" now"))
        said = self.refused("then: an interview")
        for path in ("`then: the interview`", "`then: the fast track`", "`then: the lead`"):
            self.assertIn(path, said)
        self.assertIn("`the one open task that fits his words`", self.refused("the one open task that fit his words"))

    def test_the_forms_and_every_free_line_pass(self):
        for line in ('the owner\'s order: "After the "gift note" task"', "the owner's order: \"After gift-note-in-export\"",
                     "then: the interview", "then: the fast track", "then: the lead", "the one open task that fits his words",
                     'the owners order: "After gift-note-in-export"', 'the order waits for the owner: After the gift note',
                     'the owner\'s order was removed: "start it"', "after: gift-note-in-export", "it needs the export's column"):
            with self.subTest(line=line):
                self.assertIsNone(project.fixed_form(line))
        self.assertEqual(project.ORDER_LINE.fullmatch('the owner\'s order: "After the "gift note" task"')["words"], 'After the "gift note" task')


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
        self.write("brief.md", "Read `skills/lem/prompts/small.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\ntask: readme-receive-typo\nbranch: docs/readme-receive-typo\n")
        self.assertEqual(self.say("building", "small change: one builder", "type: docs, because a word of the README"),
                         'docs: "the README says receive, not recieve". Branch docs/readme-receive-typo. '
                         "Fast track: one builder, the checks, one read, then the pull request. Nothing waits for you. "
                         "Wrong read? /lem standard-track, /lem be-careful.")

    def test_the_fast_track_of_someone_elses_ticket_waits_for_his_yes(self):
        self.write("ask.txt", "SHOP-14\n")
        self.write("ticket.txt", "SHOP-14\n")
        self.write("criteria.md", "## Acceptance criteria\n\nSize: small, because one word.\n\n1. The footer says Terms.\n")
        self.write("brief.md", "Read `skills/lem/prompts/small.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: fix/shop-14-footer-terms\nrequest by: someone else\n")
        fast = ('fix: "the footer says Terms". Branch fix/shop-14-footer-terms. Fast track: one builder, the checks, one read, then the pull request. ')
        # with the owner there, the first block is the wait for his yes, before the builder
        self.assertEqual(self.say("held", project.FAST_WAIT, "type: fix, because the footer is wrong today"),
                         fast + "Someone else wrote the request, so its criterion waits for your yes before the builder starts. "
                                "Wrong read? /lem standard-track, /lem be-careful.")
        # while he is away, its builder's block is the first, and the criterion was approved without him
        self.assertEqual(self.say("building", "small change: one builder", "type: fix, because the footer is wrong today"),
                         fast + "Nothing waits for you but the pull request, which calls you: you did not approve its criterion. "
                                "Wrong read? /lem standard-track, /lem be-careful.")
        # queued behind another task, its yes still comes before its builder: the wait comes first, then
        # the steps of the track, then what waits for him
        queued = self.say("queued", "it needs the footer's new text", "after: footer-text", "type: fix, because x", "then: the fast track")
        self.assertIn("It waits for footer-text, and starts when that task lands or is answered. Then the fast track: one builder, the checks, "
                      "one read, then the pull request. Someone else wrote the request, so its criterion waits for your yes before the builder "
                      "starts.", queued)

    def test_the_standard_track_with_an_interview_quotes_the_outcome(self):
        self.write("ask.txt", "Add the gift note to the CSV export, Ania asked twice\n")
        self.write("task.md", "# Gift note\n\n## Outcome\n\nAn export holds the gift note. The shop reads it.\n\n## Done when\n\n- a row\n")
        self.write("brief.md", "Read `skills/lem/prompts/lead.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: feat/gift-note-in-export\nstop after the plan: no\n")
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
        self.write("brief.md", "Read `skills/lem/prompts/lead.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: shop-12-export-the-gift-note\nrequest by: someone else\n")
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
        self.write("brief.md", "Read `skills/lem/prompts/small.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: feat/note-on-label\n")
        said = self.say("queued", "it waits for the export", "after: gift-note-in-export", "type: feat, because a new line")
        # the wait comes before the steps of the track, which run when it ends
        self.assertEqual(said, 'feat: "put the gift note on the label too". Branch feat/note-on-label. '
                               "It waits for gift-note-in-export, and starts when that task lands or is answered. "
                               "Then the fast track: one builder, the checks, one read, then the pull request. Nothing waits for you. "
                               "Wrong read? /lem standard-track, /lem be-careful.")

    def test_a_task_queued_by_his_order_says_so_and_his_word_that_starts_it(self):
        self.write("ask.txt", "After one-lem-parallel-landings: unit cases for the functions that are pure today\n")
        self.write("brief.md", "Read `skills/lem/prompts/lead.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: test/tests-at-the-unit-level\nstop after the plan: no\n")
        order = "the owner's order: \"After one-lem-parallel-landings\""
        said = self.say("queued", order, "after: one-lem-parallel-landings", "type: test, because tests only", "then: the interview")
        self.assertEqual(said, 'test: "after one-lem-parallel-landings: unit cases for the functions that are pure today". '
                               "Branch test/tests-at-the-unit-level. It waits for one-lem-parallel-landings, as you said; "
                               '"start task now" starts it before that. Then the standard track: an interview here, then acceptance '
                               "criteria for your yes. After that it runs to the pull request without you. Wrong read? /lem be-careful.")
        # the fast track's line puts his word in place of "Nothing waits for you"
        self.write("brief.md", "Read `skills/lem/prompts/small.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: test/tests-at-the-unit-level\n")
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

    def held_for_his_order(self) -> tuple[Path, str]:
        """The task of criterion 3: held while he was away, since two open tasks fit "the gift note"."""
        task = self.dir / "export-notes-in-order"
        task.mkdir()
        (task / "ask.txt").write_text("/lem After the gift note: the export keeps the notes in their order\n")
        (task / "task.md").write_text("# Notes in order\n\n## Outcome\n\nThe export keeps the notes in their order.\n")
        (task / "brief.md").write_text("Read `skills/lem/prompts/lead.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: feat/export-notes-in-order\nstop after the plan: no\n")
        hold = ['the order waits for the owner: "After the gift note"', "type: feat, because a new order"]
        return task, "2026-11-21T10:00Z held: " + "\n".join(hold)

    def test_a_task_held_for_his_order_gets_its_first_line_with_his_answer(self):
        task, hold = self.held_for_his_order()
        # the hold names no path: no line while he is away
        self.assertIsNone(project.opening_line_of(task, self.main, "held", hold.split(": ", 1)[1].splitlines(), "", None, False))
        # his answer "after gift-note-in-export": the queued block, with no type line of its own since the hold has it
        queued = ['the owner\'s order: "After the gift note"', "after: gift-note-in-export", "then: the interview"]
        said = project.opening_line_of(task, self.main, "queued", queued, hold, None, False)
        self.assertEqual(said, 'feat: "the export keeps the notes in their order". Branch feat/export-notes-in-order. '
                               'It waits for gift-note-in-export, as you said; "start export-notes-in-order now" starts it before that. '
                               "Then the standard track: an interview here, then acceptance criteria for your yes. "
                               "After that it runs to the pull request without you. Wrong read? /lem be-careful.")
        named = project.opening_line_of(task, self.main, "queued", queued, hold, None, False, task="export-notes-in-order")
        self.assertTrue(named.startswith('export-notes-in-order · feat: "the export keeps the notes in their order".'), named)
        # the one question's own hold between the two changes nothing
        asked = "2026-11-21T18:00Z held: the request waits for one answer\n\n" + hold
        self.assertEqual(project.opening_line_of(task, self.main, "queued", queued, asked, None, False), said)
        # said one time: the block its wait ends in says nothing
        older = "2026-11-21T18:01Z queued: " + "\n".join(queued) + "\n\n" + asked
        self.assertIsNone(project.opening_line_of(task, self.main, "held", ["the interview waits for the owner"], older, None, False))

    def test_no_order_gives_the_line_of_a_task_that_starts_at_once(self):
        task, hold = self.held_for_his_order()
        said = project.opening_line_of(task, self.main, "held", ["the interview waits for the owner"], hold, None, False)
        self.assertEqual(said, 'feat: "the export keeps the notes in their order". Branch feat/export-notes-in-order. '
                               "Standard track: an interview here now, then acceptance criteria for your yes. "
                               "After that it runs to the pull request without you. Wrong read? /lem be-careful.")
        # the hold's careful line stands for a block that has none
        careful = hold + "\ncareful: this changes the export a shop reads"
        self.assertTrue(project.opening_line_of(task, self.main, "held", ["the interview waits for the owner"], careful, None, False)
                        .startswith("Careful: this changes the export a shop reads. feat:"))
        # a block's own type line wins over the hold's
        fixed = project.opening_line_of(task, self.main, "held", ["the interview waits for the owner", "type: fix, because the order is lost"], hold, None, False)
        self.assertTrue(fixed.startswith('fix: "the export keeps'), fixed)
        # an older typed block that is no hold of his order said the line already, as before
        self.assertIsNone(project.opening_line_of(task, self.main, "held", ["the interview waits for the owner"],
                                                  "2026-11-21T10:00Z held: breaker 1 waits for the owner\ntype: feat, because x", None, False))

    def test_a_free_order_line_still_says_the_wait(self):
        # "the owners order", with no apostrophe, is a free line: the wait follows the `after:` line
        self.write("ask.txt", "After gift-note-in-export: the export keeps the notes in their order\n")
        said = self.say("queued", 'the owners order: "After gift-note-in-export"', "after: gift-note-in-export",
                        "type: feat, because a new order", "then: the interview")
        self.assertEqual(said, 'feat: "after gift-note-in-export: the export keeps the notes in their order". '
                               "It waits for gift-note-in-export, and starts when that task lands or is answered. "
                               "Then the standard track: an interview here, then acceptance criteria for your yes. "
                               "After that it runs to the pull request without you. Wrong read? /lem be-careful.")
        found = self.say("queued", "it needs the export's column", "after: gift-note-in-export", "investigation: bug", "type: fix, because x")
        self.assertIn("starts when that task lands or is answered. Then an investigator finds the cause first.", found)

    def test_the_ask_is_quoted_without_the_lem_that_carried_it(self):
        # no outcome, no criterion, no backlog item: the quote falls back to ask.txt, which keeps the command
        self.write("ask.txt", "/lem After the gift note: the export keeps the notes in their order\n")
        said = self.say("held", "the interview waits for the owner", "type: feat, because a new order")
        self.assertTrue(said.startswith('feat: "after the gift note: the export keeps the notes in their order". Standard track:'), said)
        self.assertNotIn("/lem After", said)

    def test_another_session_names_the_task_and_its_commands(self):
        self.write("ask.txt", "the footer says Terms, not Terms and Conditions\n")
        self.write("criteria.md", "## Acceptance criteria\n\nSize: small, because one word.\n\n1. The footer says Terms.\n")
        self.write("brief.md", "Read `skills/lem/prompts/small.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.\nbranch: fix/footer-terms\n")
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

    def test_an_outcome_in_bold_as_prompts_writing_asks(self):
        # github-issues-tracker, 2026-11-22: its first line quoted only the second line of this sentence
        self.assertEqual(project.outcome_of("## Outcome\n\n**A developer whose team keeps its work in GitHub Issues gives Lem an issue, "
                                            "and Lem reads it,\nworks it and reports on it the way it does a Linear ticket.**\n\nToday:\n\n1. step\n"),
                         "A developer whose team keeps its work in GitHub Issues gives Lem an issue, and Lem reads it, "
                         "works it and reports on it the way it does a Linear ticket")
        self.assertEqual(project.outcome_of("## Outcome\n\n**The export keeps the gift note of each order.**\n"),
                         "The export keeps the gift note of each order")
        self.assertIsNone(project.outcome_of("## Outcome\n\n**Today:**\n\n1. Invoice 1042 is 100 EUR.\n2. It shows 70.\n"))
        self.assertEqual(project.outcome_of("## Outcome\n\nThe export keeps the gift note\nof each order. It shows on the slip.\n"),
                         "The export keeps the gift note of each order")

    def test_the_words_it_quotes(self):
        self.assertEqual(project.first_sentence("The footer says Terms.  It is wrong."), "The footer says Terms")
        self.assertEqual(project.in_his_words("README says it"), "README says it")
        self.assertEqual(project.in_his_words("I see 0"), "I see 0")
        self.assertEqual(project.criterion_of("1. A refund lowers the total,\n   never below 0:\n   1. Invoice 1042\n"), "A refund lowers the total, never below 0")
        self.assertIsNone(project.outcome_of("## Outcome\n\n1. Invoice 1042 is 100 EUR.\n2. It shows 70.\n"))
        self.assertEqual(project.outcome_of("## Outcome\n\n**Today:**\n\n1. step\n\nThe invoice shows 70 EUR after the refund.\n"),
                         "The invoice shows 70 EUR after the refund")
        # the outcome's first sentence in bold, as writing.md asks, over two lines: that sentence, never
        # the line that continues it
        self.assertEqual(project.outcome_of("## Outcome\n\n**A merge from the board no longer holds the owner's other acts\n"
                                            "on the board.** It still merges under the task's own lock.\n\nToday:\n\n1. step\n"),
                         "A merge from the board no longer holds the owner's other acts on the board")
        self.assertEqual(project.outcome_of("## Outcome\n\n**What the owner sees after it:**\n\n1. step\n\nThe invoice shows 70 EUR after the refund.\n"),
                         "The invoice shows 70 EUR after the refund")
        # a line that opens with a bold label is no outcome to quote: the paragraph after it is
        self.assertEqual(project.outcome_of("## Outcome\n\n**Today:** the invoice shows 100 EUR after the refund.\n\n"
                                            "The invoice shows 70 EUR after the refund.\n"),
                         "The invoice shows 70 EUR after the refund")

    def test_a_bold_outcome_is_quoted_whole(self):
        # brief-reads-installed-lem, 2026-11-22: one bold sentence wrapped over two lines
        self.assertEqual(project.outcome_of("## Outcome\n\n**The brief names the Lem that is\ninstalled when it starts.**\n"),
                         "The brief names the Lem that is installed when it starts")
        # done-column-shows-newest, 2026-11-22: one bold sentence on one line, with prose after it
        self.assertEqual(project.outcome_of("## Outcome\n\n**Done shows at most the 20 newest ended tasks, and one row at its foot "
                                            "leads to the rest.**\n\nThe rest stay in the backlog.\n"),
                         "Done shows at most the 20 newest ended tasks, and one row at its foot leads to the rest")
        # a bold label of a few words is still no quote, on its own line or before the text
        self.assertEqual(project.outcome_of("## Outcome\n\n**Today:**\nThe invoice shows 100 EUR after the refund.\n"),
                         "The invoice shows 100 EUR after the refund")
        self.assertIsNone(project.outcome_of("## Outcome\n\n**Today:** it shows 100.\n\n1. step\n"))

    def test_only_the_marks_of_a_bold_run_leave_the_quote(self):
        # bold-outcome-quoted-whole, 2026-11-22: prose that names the marks in code keeps them
        self.assertEqual(project.outcome_of("## Outcome\n\nWhen the Outcome is one bold sentence, the first line quotes it, "
                                            "without the `**` marks. A label is no quote.\n"),
                         "When the Outcome is one bold sentence, the first line quotes it, without the `**` marks")
        self.assertEqual(project.outcome_of("## Outcome\n\n**The check reads `src/**/*.py` and\npasses `**kwargs` on.**\n"),
                         "The check reads `src/**/*.py` and passes `**kwargs` on")

    def test_a_code_span_among_the_first_words_makes_no_label(self):
        # bold-label-skips-code-spans, 2026-11-22: the label test stopped at the `**` inside the code span
        self.assertEqual(project.outcome_of("## Outcome\n\n**Lem reads `**/*.md` and\nquotes each file once.**\n"),
                         "Lem reads `**/*.md` and quotes each file once")
        self.assertEqual(project.outcome_of("## Outcome\n\n**Pass `**kwargs` on to the handler every time.**\n"),
                         "Pass `**kwargs` on to the handler every time")
        # a bold label of a few words is still no quote
        self.assertEqual(project.outcome_of("## Outcome\n\n**Today:**\nThe invoice shows 100 EUR after the refund.\n"),
                         "The invoice shows 100 EUR after the refund")
        self.assertIsNone(project.outcome_of("## Outcome\n\n**Today:** `**` shows 100.\n\n1. step\n"))

    def test_a_bold_label_or_a_rule_is_no_quote(self):
        # a bold run that closes on its line and ends in a colon is a label at any length
        self.assertEqual(project.outcome_of("## Outcome\n\n**Before and after the change:**\n\nThe invoice shows 70 EUR after the refund.\n"),
                         "The invoice shows 70 EUR after the refund")
        self.assertEqual(project.outcome_of("## Outcome\n\n**Before and after the change**:\nThe invoice shows 70 EUR after the refund.\n"),
                         "The invoice shows 70 EUR after the refund")
        # a *** rule is no bold line
        self.assertEqual(project.outcome_of("## Outcome\n\n***\nThe invoice shows 70 EUR after the refund.\n"),
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


class InterviewEvents(unittest.TestCase):
    """The end of an interview's questions and the skip question are two events of one form each, which
    take nothing (`STARTS`), so that the board tells who acts on a held interview; `log` refuses either
    with a field, as it refuses `interview.start by=lem`, and writes nothing then."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        project.STATE_ROOTS[self.root] = self.root / "state"
        self.addCleanup(project.STATE_ROOTS.pop, self.root)
        (self.root / "state" / "tasks" / "report-dates-stay-whole").mkdir(parents=True)

    def log(self, event: str, *pairs: str) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            project.cmd_log(self.root, "report-dates-stay-whole", event, list(pairs))

    def test_each_takes_nothing_and_a_field_is_refused(self):
        for event, said in (("interview.end", "interview.end, the end of the questions to the owner, takes nothing"),
                            ("read.skip.asked", "read.skip.asked, the question whether the owner skips the personas' read, takes nothing")):
            with self.subTest(event=event):
                self.log(event)
                for pair in ("by=lem", "answer=y"):
                    with self.assertRaises(project.SettingsError) as caught:
                        self.log(event, pair)
                    self.assertIn(said, str(caught.exception))
        self.assertEqual([record["event"] for record in project.events_named(self.root, "interview.end", "read.skip.asked")], ["interview.end", "read.skip.asked"])
        self.assertEqual({k for record in project.events_named(self.root, "interview.end", "read.skip.asked") for k in record}, {"ts", "event", "task"})

    def test_a_resumed_task_takes_both_with_the_interviews_start(self):
        self.assertTrue({"interview.start", "interview.end", "read.skip.asked"} <= set(project.RESUMED_EVENTS))


class Words(unittest.TestCase):
    """A task's words (ask.txt) are written once: the same words again pass, other words are refused."""

    def test_the_same_words_again_and_other_words(self):
        self.assertIsNone(project.ask_refusal("gift-note", None, "Add the gift note"))
        self.assertIsNone(project.ask_refusal("gift-note", "Add the gift note\n", "  Add the gift note "))
        said = project.ask_refusal("gift-note", "Add the gift note\n", "Add the gift note to the slip")
        self.assertIn("the task 'gift-note' holds other words already", said)
        self.assertIn("Add the gift note", said)
        self.assertIn("choose another name", said)


class OneWriter(unittest.TestCase):
    """Two writers of one task's state at one moment: the lead's `building` and the owner's drop."""

    def test_a_drop_that_comes_while_another_write_runs_stays_on_top(self):
        import threading
        from unittest import mock
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        directory = Path(folder.name)
        (directory / "state.md").write_text("2026-11-21T10:00Z building: lead: builder 1\n", encoding="utf-8")
        events = []
        lead_read, go = threading.Event(), threading.Event()
        refusal = project.parked_refusal

        def paused(slug, now, status, resumed=False):
            # the lead has read `building` and decided; the owner's drop comes now
            if status == "building":
                lead_read.set()
                go.wait(5)
            return refusal(slug, now, status, resumed)
        said = {}

        def write(status, line):
            try:
                said[status] = project.cmd_state(ROOT, "gift-note", status, [line])
            except project.SettingsError as error:
                said[status] = str(error)
        with mock.patch.object(project, "task_directory", return_value=directory), mock.patch.object(project, "load", return_value={}), \
                mock.patch.object(project, "task_worktree", return_value={}), mock.patch.object(project, "opening_line", return_value=None), \
                mock.patch.object(project, "append_event", side_effect=lambda root, name, slug, fields: events.append(fields["status"])), \
                mock.patch.object(project, "parked_refusal", side_effect=paused):
            lead = threading.Thread(target=write, args=("building", "lead: builder 2"))
            lead.start()
            self.assertTrue(lead_read.wait(5))
            owner = threading.Thread(target=write, args=("dropped", "the owner dropped it"))
            owner.start()
            # the drop has had its moment to write while the lead still holds its read
            owner.join(0.5)
            go.set()
            lead.join(5)
            owner.join(5)
        blocks = (directory / "state.md").read_text(encoding="utf-8").split("\n\n")
        self.assertEqual([block.split()[1] for block in blocks], ["dropped:", "building:", "building:"], blocks)
        self.assertEqual(events, ["building", "dropped"])


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


class TicketId(unittest.TestCase):
    """The id of a ticket by the kind of the project's tracker (github-issues-tracker, criterion 2)."""

    def refused(self, tracker: dict | None, given: str) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            project.ticket_id(tracker, given)
        return str(caught.exception)

    def test_an_issue_is_its_number_after_a_hash_in_one_saved_form(self):
        for given in ("42", "#42", "#042", "042"):
            with self.subTest(given=given):
                self.assertEqual(project.ticket_id({"kind": "github"}, given), "#42")

    def test_github_refuses_a_linear_id_and_no_number(self):
        for given in ("MBZ-12", "0", "#0", "#", "42a", "# 42", "-42"):
            with self.subTest(given=given):
                self.assertIn("is not an issue's number, such as 42 or #42: the project's tracker is github", self.refused({"kind": "github"}, given))

    def test_linear_refuses_a_number_and_keeps_its_own_form(self):
        self.assertEqual(project.ticket_id({"kind": "linear"}, "mbz-12"), "MBZ-12")
        for given in ("42", "#42"):
            with self.subTest(given=given):
                self.assertIn("is not a ticket's id, such as MBZ-12: the project's tracker is linear", self.refused({"kind": "linear"}, given))

    def test_a_project_with_no_tracker_takes_no_ticket_and_says_how_to_add_one(self):
        said = self.refused(None, "MBZ-12")
        self.assertIn("has no [tracker]", said)
        self.assertIn('kind = "linear" or kind = "github"', said)


class TicketOwed(unittest.TestCase):
    """What an ended task still owes its ticket, the assignee Lem added among it."""

    TRACKER = {"kind": "github"}

    def test_a_drop_or_an_answer_owes_the_removal_of_the_assignee_lem_added(self):
        self.assertEqual(project.ticket_owed("dropped", ["started", "assigned"], self.TRACKER), ["dropped", "unassigned"])
        self.assertEqual(project.ticket_owed("answered", ["assigned", "started"], self.TRACKER), ["answered", "unassigned"])
        self.assertEqual(project.ticket_owed("dropped", ["assigned", "unassigned", "started", "dropped"], self.TRACKER), [])
        # an issue that had an assignee got none from Lem: nothing to remove
        self.assertEqual(project.ticket_owed("dropped", ["started"], self.TRACKER), ["dropped"])

    def test_a_landing_keeps_the_assignee_and_a_running_task_owes_nothing(self):
        self.assertEqual(project.ticket_owed("landed", ["assigned", "started"], self.TRACKER), ["commented", "landed"])
        self.assertEqual(project.ticket_owed("building", ["assigned", "started"], self.TRACKER), [])

    def test_a_task_whose_ticket_another_task_holds_owes_it_nothing(self):
        # decision 23: a resume moved the ticket to the new task, and the dropped one's drop comment would tell the issue's readers the work was dropped
        self.assertEqual(project.ticket_owed("dropped", ["started", "assigned"], self.TRACKER, held_by="gift-note-2"), [])
        self.assertEqual(project.ticket_owed("answered", [], self.TRACKER, held_by="gift-note-2"), [])

    def test_the_holder_is_the_mark_and_else_the_task_a_resume_went_on_in(self):
        with tempfile.TemporaryDirectory() as folder:
            project.STATE_ROOTS[ROOT] = Path(folder)
            self.addCleanup(project.STATE_ROOTS.pop, ROOT, None)
            old = {"slug": "gift-note", "ticket": "#42"}
            new = {"slug": "gift-note-2", "ticket": "#42"}
            # no mark and no resume: the task holds its own ticket
            self.assertIsNone(project.ticket_held_by(ROOT, old, None))
            (Path(folder) / "tickets").mkdir()
            (Path(folder) / "tickets" / "42").write_text("gift-note\n", encoding="utf-8")
            self.assertIsNone(project.ticket_held_by(ROOT, old, None))
            (Path(folder) / "tickets" / "42").write_text("gift-note-2\n", encoding="utf-8")
            self.assertEqual(project.ticket_held_by(ROOT, old, new), "gift-note-2")
            # the resumed task gave the ticket back and its mark went: the old task still owes nothing
            (Path(folder) / "tickets" / "42").unlink()
            self.assertEqual(project.ticket_held_by(ROOT, old, new), "gift-note-2")
            self.assertIsNone(project.ticket_held_by(ROOT, old, {**new, "ticket": "#43"}))

    def test_the_steps_are_read_one_a_line_with_the_login_of_the_assignee(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.assertEqual(project.ticket_steps_of(directory), ([], None))
            (directory / "ticket-steps.txt").write_text("assigned octo-cat\nstarted\n", encoding="utf-8")
            self.assertEqual(project.ticket_steps_of(directory), (["assigned", "started"], "octo-cat"))


class TicketClaim(unittest.TestCase):
    """The claim of a ticket (decision 17): a mark in the state folder only one task takes, before
    the scan of the tasks; a ticket goes back only once its old task owes it nothing (decision 12)."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.state = Path(folder.name)
        project.STATE_ROOTS[ROOT] = self.state
        self.addCleanup(project.STATE_ROOTS.pop, ROOT, None)

    def task(self, slug: str, status: str | None, owed: tuple[str, ...] = (), ticket: str = "#42") -> dict:
        (self.state / "tasks" / slug).mkdir(parents=True, exist_ok=True)
        return {"slug": slug, "status": status, "ticket": ticket, "ticket_owed": list(owed)}

    def refused(self, slug: str, tasks: list[dict], kind: str = "github", succeeds: str | None = None) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            project.claim_ticket(ROOT, slug, "#42", tasks, kind, succeeds)
        return str(caught.exception)

    def mark(self) -> str:
        return (self.state / "tickets" / "42").read_text(encoding="utf-8").strip()

    def test_two_opens_in_one_moment_one_takes_the_ticket(self):
        # both scanned the tasks before either wrote ticket.txt: neither scan sees a holder
        self.assertIsNotNone(project.claim_ticket(ROOT, "export-keeps-gift-note", "#42", [], "github"))
        self.assertEqual(self.mark(), "export-keeps-gift-note")
        self.task("export-keeps-gift-note", None)
        said = self.refused("gift-note-in-export", [])
        self.assertIn("the task 'export-keeps-gift-note' already holds the ticket #42", said)
        # a retry of the same task passes, and makes no new mark
        self.assertIsNone(project.claim_ticket(ROOT, "export-keeps-gift-note", "#42", [], "github"))
        self.assertEqual(sorted(path.name for path in (self.state / "tickets").iterdir()), ["42"])

    def test_a_landed_task_keeps_its_ticket_and_the_refusal_names_it(self):
        project.claim_ticket(ROOT, "export-keeps-gift-note", "#42", [], "github")
        landed = self.task("export-keeps-gift-note", "landed")
        said = self.refused("gift-note-again", [landed])
        self.assertIn("the task 'export-keeps-gift-note' landed the ticket #42", said)
        self.assertIn("start the new task from the owner's own words", said)

    def test_an_ended_task_that_still_owes_holds_the_ticket_and_the_refusal_names_the_step_by_kind(self):
        project.claim_ticket(ROOT, "export-keeps-gift-note", "#42", [], "github")
        dropped = self.task("export-keeps-gift-note", "dropped", ("dropped", "unassigned"))
        said = self.refused("gift-note-again", [dropped])
        self.assertIn("is dropped and still owes the ticket #42 dropped, unassigned", said)
        self.assertIn("`lem issue drop export-keeps-gift-note`", said)
        answered = {**dropped, "status": "answered", "ticket_owed": ["answered"]}
        self.assertIn("the lem-linear skill's step `answer` for export-keeps-gift-note, run from a session", self.refused("gift-note-again", [answered], kind="linear"))

    def test_a_ticket_given_back_goes_to_the_new_task(self):
        project.claim_ticket(ROOT, "export-keeps-gift-note", "#42", [], "github")
        paid = self.task("export-keeps-gift-note", "dropped")
        self.assertIsNotNone(project.claim_ticket(ROOT, "gift-note-again", "#42", [paid], "github"))
        self.assertEqual(self.mark(), "gift-note-again")

    def test_a_resumed_task_takes_the_mark_of_the_task_it_goes_on_from_and_no_other(self):
        project.claim_ticket(ROOT, "gift-note", "#42", [], "github")
        old = self.task("gift-note", "dropped", ("dropped",))
        project.claim_ticket(ROOT, "gift-note-2", "#42", [old], "github", succeeds="gift-note")
        self.assertEqual(self.mark(), "gift-note-2")
        # a live task with the ticket and no mark (a state folder from before the marks) refuses the resume too
        (self.state / "tickets" / "42").unlink()
        live = self.task("export-keeps-gift-note", "building")
        self.assertIn("the task 'export-keeps-gift-note' already holds the ticket #42", self.refused("gift-note-3", [old, live], succeeds="gift-note"))
        self.assertFalse((self.state / "tickets" / "42").exists())

    def refused_in(self, slug: str, tasks: list[dict], succeeds: str | None = None, seen: list[str] | None = None) -> None:
        """An opening that claims #42 for SLUG and is refused after the claim, as `task-dir` is by
        other words under its slug and `resume` by a branch git cannot make."""
        with self.assertRaises(project.SettingsError):
            with project.held_ticket(ROOT, slug, "#42", tasks, "github", succeeds):
                if seen is not None:
                    seen.append(self.mark())
                raise project.SettingsError("refused after the claim")

    def test_an_opening_refused_after_its_claim_gives_the_mark_back(self):
        self.refused_in("gift-note-words", [])
        self.assertFalse((self.state / "tickets" / "42").exists())
        # the ticket then opens under another slug
        self.assertIsNotNone(project.claim_ticket(ROOT, "gift-note-in-the-export", "#42", [], "github"))
        # a retry's mark was there before its claim, and stays
        self.task("gift-note-in-the-export", None)
        self.refused_in("gift-note-in-the-export", [])
        self.assertEqual(self.mark(), "gift-note-in-the-export")

    def test_a_resume_refused_after_its_claim_gives_the_mark_back_to_the_dropped_task(self):
        project.claim_ticket(ROOT, "gift-note", "#42", [], "github")
        old = self.task("gift-note", "dropped", ("dropped", "unassigned"))
        seen: list[str] = []
        self.refused_in("gift-note-2", [old], succeeds="gift-note", seen=seen)
        self.assertEqual((seen, self.mark()), (["gift-note-2"], "gift-note"))
        # a dropped task that had no mark gets none
        (self.state / "tickets" / "42").unlink()
        self.refused_in("gift-note-2", [old], succeeds="gift-note")
        self.assertFalse((self.state / "tickets" / "42").exists())

    def test_a_mark_whose_task_folder_is_gone_is_named_with_the_fix(self):
        (self.state / "tickets").mkdir()
        (self.state / "tickets" / "42").write_text("gone-task\n", encoding="utf-8")
        said = self.refused("gift-note", [])
        self.assertIn(f"{self.state / 'tickets' / '42'}", said)
        self.assertIn("names the task 'gone-task', whose folder is not there", said)
        self.assertIn("remove the mark (rm", said)


# The moment the cases below count back from, once for the run: a fixture and its assertions name the same second.
MOMENT = project.datetime.now(project.timezone.utc)


def back(days: float, seconds: int = 0) -> str:
    """A `ts` DAYS before MOMENT, and SECONDS after that."""
    return (MOMENT - project.timedelta(days=days) + project.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def block(days: float, status: str, text: str) -> str:
    """A state.md of one block, DAYS before now."""
    return f"{back(days)[:16]}Z {status}: {text}\n"


PULL_12 = "https://github.com/acme/shop/pull/12"


class Summarized(unittest.TestCase):
    """The log of criterion 1 in a state folder of its own: `report-dates` landed 35 days ago with pull
    request 12 and 60 events, `invoice-fix` landed 4 days ago, `gift-note` builds, and `old-idea` was
    parked 65 days ago. `state.keep_days` is 30."""

    def setUp(self):
        from unittest import mock
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.state = self.root / "state"
        self.state.mkdir()
        project.STATE_ROOTS[self.root] = self.state
        self.addCleanup(project.STATE_ROOTS.pop, self.root)
        for patched in (mock.patch.object(project, "load", return_value={"state": {"keep_days": 30, "from": ".lem/project.toml"}}),
                        mock.patch.object(project, "owner_records", return_value=[])):
            patched.start()
            self.addCleanup(patched.stop)
        self.task("report-dates", block(35, "landed", "main: pull request 12 is merged"))
        self.task("invoice-fix", block(4, "landed", "main: pull request 14 is merged"))
        self.task("gift-note", block(2, "building", "lead: builder"))
        self.task("old-idea", block(65, "parked", "the owner put it aside"))
        self.log = self.state / "events.jsonl"
        self.log.write_bytes(b"".join(json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n" for record in self.records()))
        self.before = self.log.read_bytes()

    def task(self, slug: str, state: str) -> None:
        directory = self.state / "tasks" / slug
        (directory / "reports").mkdir(parents=True)
        (directory / "state.md").write_text(state, encoding="utf-8")
        (directory / "ask.txt").write_text(f"The ask of {slug}.\n", encoding="utf-8")

    @staticmethod
    def state_event(ts: str, slug: str, status: str, text: str, *lines: str, **more) -> dict:
        return {"ts": ts, "event": "task.state", "task": slug, "status": status, "text": text, "lines": list(lines), "ask": f"The ask of {slug}.", **more}

    def records(self) -> list[dict]:
        rd = "report-dates"
        mine = [
            {"ts": back(41), "event": "task.mode", "task": rd, "mode": "alone", "by": "lem", "words": "the night of 2026-10-01", "all": False, "was": "with-owner"},
            self.state_event(back(41, 1), rd, "held", "the interview waits for the owner", "type: feat, because the report shows no dates"),
            {"ts": back(41, 2), "event": "task.criteria", "task": rd, "size": "full", "why": "the report every merchant reads", "digest": "d1",
             "criteria": ["Each report shows its dates."]},
            self.state_event(back(40), rd, "building", "lead: builder", "plan committed with 2 tasks", branch="feat/report-dates", head="abc1234", subject="feat: dates"),
        ]
        mine += [{"ts": back(39, n), "event": "gate", "task": rd, "command": f"check {n}", "exit": 0, "last": "ok", "tip": "abc1234"} for n in range(50)]
        mine += [
            {"ts": back(38), "event": "review", "task": rd, "attempt": 1, "round": 1, "of": 1, "kind": "read", "verdict": "clean", "must_fix": 0, "should": 0, "nit": 0,
             "tip": "abc1234", "careful": True, "careful_why": "it changes the report every merchant reads"},
            {"ts": back(37), "event": "proposed", "task": rd, "green": True, "not_green": [], "tip": "abc1234"},
            self.state_event(back(37, 1), rd, "open", "the pull request waits for its merge", f"pull request: {PULL_12}", "green"),
            {"ts": back(37, 2), "event": "session.transcript", "task": rd, "claude": "c1", "transcript": "/t/c1.jsonl", "source": "startup"},
            {"ts": back(36), "event": "merge.review", "task": rd, "verdict": "merge", "calls": False, "why": "it reads well", "by": "claude", "tip": "abc1234"},
            self.state_event(back(35), rd, "landed", "main: pull request 12 is merged"),
        ]
        others = [
            self.state_event(back(70), "old-idea", "building", "lead: builder"),
            self.state_event(back(65), "old-idea", "parked", "the owner put it aside"),
            self.state_event(back(39, 30), "invoice-fix", "building", "lead: builder"),
            self.state_event(back(4), "invoice-fix", "landed", "main: pull request 14 is merged"),
            self.state_event(back(3), "gift-note", "building", "lead: builder"),
            {"ts": back(2), "event": "session.transcript", "task": "gift-note", "claude": "c2", "transcript": "/t/c2.jsonl", "source": "startup"},
        ]
        # report-dates' events among the others, in the order of their times
        return sorted(mine + others, key=lambda record: record["ts"])

    def lines(self) -> list[bytes]:
        return self.log.read_bytes().split(b"\n")[:-1]

    def prune(self, dry: bool = False) -> dict:
        answer, code = project.cmd_prune(self.root, dry, None)
        self.assertEqual(code, 0, answer)
        return answer

    def test_an_old_ended_task_becomes_one_summary_and_every_other_line_stays_as_it_was(self):
        bm = importlib.import_module("lem_board_model")
        events = [json.loads(line) for line in self.before.split(b"\n")[:-1]]
        self.assertEqual(sum(1 for e in events if e["task"] == "report-dates"), 60)
        card = bm.derive(events, [], bm.now_ms()).by_slug["report-dates"]
        answer = self.prune()
        self.assertEqual(answer["summarized"], [{"task": "report-dates", "status": "landed", "events": 60}])
        self.assertEqual(answer["events"], 60)
        self.assertIn("replaced the 60 events of 1 such tasks with one summary event each", answer["said"])
        old_lines = self.before.split(b"\n")[:-1]
        kept = [line for line in old_lines if json.loads(line)["task"] != "report-dates"]
        new_lines = self.lines()
        summary = [json.loads(line) for line in new_lines if json.loads(line)["task"] == "report-dates"]
        self.assertEqual(len(summary), 1, new_lines)
        # every other line byte for byte, in its order, with the summary in the place of the task's newest event
        self.assertEqual([line for line in new_lines if json.loads(line)["task"] != "report-dates"], kept)
        newest = max(n for n, line in enumerate(old_lines) if json.loads(line)["task"] == "report-dates")
        self.assertEqual(new_lines.index(next(line for line in new_lines if b'"task.summary"' in line)), newest - 59)
        s = summary[0]
        self.assertEqual((s["event"], s["status"], s["text"], s["lines"]), ("task.summary", "landed", "main: pull request 12 is merged", []))
        # the facts the board's model reads from the 60 events
        self.assertEqual((s["since"], s["first"], s["last"]), (project.stamp_ms(card.since), project.stamp_ms(card.first), project.stamp_ms(card.last_ts)))
        self.assertEqual((s["since"], s["first"]), (back(35), back(41, 1)))
        self.assertEqual(s["ts"], back(35))
        self.assertEqual(s["pr"], {"url": PULL_12, "n": "12", "repo": "acme/shop"})
        self.assertEqual(s["pr"], bm.pr_of(card))
        self.assertEqual(s["type"], {"type": "feat", "why": "the report shows no dates"})
        self.assertEqual(s["size"], "full")
        self.assertEqual(s["size"], bm.criteria_size(card))
        self.assertEqual(s["lead"], "builder")
        self.assertEqual(s["careful"], bm.careful_of(card))
        self.assertEqual(s["proposal"], {"ts": back(37), "green": True, "reasons": [], "tip": "abc1234"})
        self.assertEqual((s["ask"], s["branch"], s["night"], s["events"]), ("The ask of report-dates.", "feat/report-dates", "2026-10-01", 60))
        self.assertEqual((s["opened"], s["newest"]), (back(41), back(35)))
        self.assertFalse(s["talked"])
        # a parked task and every task that has not ended stay whole however old
        self.assertEqual(sum(1 for line in new_lines if b'"old-idea"' in line), 2)

    def test_a_second_prune_leaves_the_log_as_it_is(self):
        self.prune()
        after = self.log.read_bytes()
        inode = self.log.stat().st_ino
        again = self.prune()
        self.assertEqual(self.log.read_bytes(), after)
        self.assertEqual(self.log.stat().st_ino, inode, "a prune that summarizes nothing writes no new log")
        self.assertEqual((again["summarized"], again["events"]), ([], 0))
        # and the summarized task stays old, dated by its summary
        calls = {call["task"]: call for call in project.task_calls([{"slug": "report-dates", "state": block(35, "landed", "x")}],
                                                                   project.log_events(self.root), project.datetime.now(project.timezone.utc) - project.timedelta(days=30))}
        self.assertEqual((calls["report-dates"]["call"], calls["report-dates"]["last_event"]), ("old", back(35)))

    def test_a_dry_run_names_the_task_with_the_count_of_its_events_and_changes_no_file(self):
        answer = self.prune(dry=True)
        self.assertEqual(answer["summarized"], [{"task": "report-dates", "status": "landed", "events": 60}])
        self.assertIn("would replace the 60 events of 1 such tasks", answer["said"])
        self.assertEqual(self.log.read_bytes(), self.before)
        self.assertEqual(sorted(path.name for path in self.state.iterdir()), ["events.jsonl", "tasks"], "a dry run opens no lock file and leaves no new log")

    def test_a_summary_with_a_newer_event_is_summarized_again_over_the_old_one(self):
        self.prune()
        # a hook logged a transcript of the task after its summary, and the days passed again
        lines = self.lines()
        late = {"ts": back(31), "event": "session.transcript", "task": "report-dates", "claude": "c3", "transcript": "/t/c3.jsonl", "source": "resume"}
        at = next(n for n, line in enumerate(lines) if json.loads(line)["ts"] > late["ts"])
        lines.insert(at, json.dumps(late).encode("utf-8"))
        self.log.write_bytes(b"".join(line + b"\n" for line in lines))
        first = next(json.loads(line) for line in lines if b'"task.summary"' in line)
        answer = self.prune()
        self.assertEqual(answer["summarized"], [{"task": "report-dates", "status": "landed", "events": 2}])
        again = [json.loads(line) for line in self.lines() if json.loads(line)["task"] == "report-dates"]
        self.assertEqual(len(again), 1)
        self.assertEqual(again[0], {**first, "ts": back(31), "events": 61})
        self.assertEqual(again[0]["size"], "full", "a second summary keeps the criteria's size")

    def test_an_append_waits_for_the_lock_of_the_log(self):
        import threading
        written = threading.Event()

        def append():
            project.append_event(self.root, "session.wake", "gift-note", {"why": "a test"})
            written.set()
        with project.lem_state.events_lock(self.state):
            writer = threading.Thread(target=append)
            writer.start()
            self.assertFalse(written.wait(0.5), "an append went on while another held the log's lock")
            self.assertNotIn(b'"session.wake"', self.log.read_bytes())
        writer.join(5)
        self.assertTrue(written.is_set())
        self.assertIn(b'"session.wake"', self.lines()[-1])

    def paused_prune(self, while_paused) -> dict:
        """Run `prune` in a thread that stops between its read of the log and its write of the new one,
        call WHILE_PAUSED there, then let it go on; prune's answer."""
        import threading
        from unittest import mock
        read, go, said = threading.Event(), threading.Event(), {}
        real = project.summarized_log

        def paused(lines, made):
            read.set()
            go.wait(10)
            return real(lines, made)

        def run():
            said["answer"] = project.cmd_prune(self.root, False, None)
        with mock.patch.object(project, "summarized_log", side_effect=paused):
            pruner = threading.Thread(target=run)
            pruner.start()
            self.assertTrue(read.wait(10))
            while_paused()
            go.set()
            pruner.join(10)
        return said["answer"][0]

    def test_a_state_and_a_transcript_written_from_other_processes_while_prune_writes_are_in_the_new_log(self):
        import subprocess
        scripts = str(Path(project.__file__).resolve().parent)
        setup = f"import sys; from pathlib import Path; sys.path.insert(0, {scripts!r}); import project, session_hook; root, state = Path({str(self.root)!r}), Path({str(self.state)!r}); project.STATE_ROOTS[root] = state; "
        writes = [
            setup + 'project.append_event(root, "task.state", "gift-note", {"status": "ready", "text": "the build is done", "lines": []})',
            setup + 'session_hook.keep_transcript(state, "gift-note", {"session_id": "c9", "transcript_path": "/t/c9.jsonl", "source": "startup"})',
        ]
        started = []

        def write_now():
            started.extend(subprocess.Popen([sys.executable, "-B", "-c", code]) for code in writes)
            for _ in range(20):
                if all(one.poll() is None for one in started):
                    break
            import time
            time.sleep(0.7)
            # both wait for the lock that prune holds
            self.assertEqual([one.poll() for one in started], [None, None])
            self.assertEqual(self.log.read_bytes(), self.before)
        answer = self.paused_prune(write_now)
        self.assertEqual([one.wait(10) for one in started], [0, 0])
        self.assertEqual(answer["summarized"], [{"task": "report-dates", "status": "landed", "events": 60}])
        records = [json.loads(line) for line in self.lines()]
        gift = [(r["event"], r.get("status") or r.get("claude")) for r in records if r["task"] == "gift-note"]
        self.assertEqual(gift[:2], [("task.state", "building"), ("session.transcript", "c2")])
        self.assertEqual(sorted(gift[2:]), [("session.transcript", "c9"), ("task.state", "ready")])
        self.assertEqual([r["event"] for r in records if r["task"] == "report-dates"], ["task.summary"])
        self.assertEqual(len(records), len(set(json.dumps(r, sort_keys=True) for r in records)), "an event is in the log twice")

    def test_an_append_with_no_lock_between_the_read_and_the_replace_goes_on_in_the_new_log(self):
        old = {"ts": back(0), "event": "session.wake", "task": "gift-note", "why": "a writer of an older Lem"}

        def unlocked():
            with self.log.open("a", encoding="utf-8") as out:
                out.write(json.dumps(old) + "\n")
        self.paused_prune(unlocked)
        lines = self.lines()
        self.assertEqual(json.loads(lines[-1]), old)
        self.assertEqual(sum(1 for line in lines if b'"task.summary"' in line), 1)

    def test_the_log_command_refuses_a_summary(self):
        with self.assertRaises(project.SettingsError) as said:
            project.cmd_log(self.root, "gift-note", "task.summary", ["status=landed"])
        self.assertIn("written by `lem project prune` only", str(said.exception))
        self.assertEqual(self.log.read_bytes(), self.before)

    def test_tasks_read_the_same_night_and_times_from_the_summary(self):
        before = {t["slug"]: t for t in project.read_tasks(self.root)}["report-dates"]
        self.prune()
        self.assertEqual([json.loads(line)["event"] for line in self.lines() if json.loads(line)["task"] == "report-dates"], ["task.summary"])
        after = {t["slug"]: t for t in project.read_tasks(self.root)}["report-dates"]
        self.assertEqual((after["status"], after["since"], after["night"], after["proposal"]), (before["status"], before["since"], before["night"], before["proposal"]))
        self.assertEqual(after["night"], "2026-10-01")


class ResumeSummarized(unittest.TestCase):
    """`lem project resume` of a dropped task, `card-foot`, with its breaker that waits and its handoff:
    refused once its events became its summary, and resumed while they are whole."""

    def setUp(self):
        from unittest import mock
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name).resolve()
        self.state = self.root / "state"
        project.STATE_ROOTS[self.root] = self.state
        self.addCleanup(project.STATE_ROOTS.pop, self.root)
        self.directory = self.state / "tasks" / "card-foot"
        (self.directory / "reports").mkdir(parents=True)
        (self.directory / "state.md").write_text(block(35, "dropped", "the owner dropped it"), encoding="utf-8")
        (self.directory / "ask.txt").write_text("Put the card's foot under the total\n", encoding="utf-8")
        (self.directory / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        (self.directory / "decisions.jsonl").write_text(json.dumps({"kind": "breaker", "id": 1, "document": "breaker-1.md"}) + "\n", encoding="utf-8")
        self.log = self.state / "events.jsonl"
        self.log.write_text("".join(json.dumps(record) + "\n" for record in [
            {"ts": back(40), "event": "task.state", "task": "card-foot", "status": "building", "text": "lead: builder", "lines": [], "branch": "feat/card-foot"},
            {"ts": back(39), "event": "criteria.approved", "task": "card-foot", "number": 1, "by": "owner"},
            {"ts": back(35), "event": "task.state", "task": "card-foot", "status": "dropped", "text": "the owner dropped it", "lines": []},
        ]), encoding="utf-8")
        settings = {"places": {"worktrees": {"path": str(self.root / ".lem" / "worktrees")}}, "state": {"keep_days": 30, "from": ".lem/project.toml"}}
        for patched in (mock.patch.object(project, "load", return_value=settings), mock.patch.object(project, "main_checkout", return_value=self.root),
                        mock.patch.object(project, "cmd_worktree", return_value={"worktree": str(self.root / ".lem" / "worktrees" / "card-foot-2")}),
                        mock.patch.object(project, "cmd_state", return_value={"since": "2026-11-05T10:00Z"})):
            patched.start()
            self.addCleanup(patched.stop)

    def summarize(self) -> None:
        answer, code = project.cmd_prune(self.root, False, None)
        self.assertEqual((code, answer["summarized"]), (0, [{"task": "card-foot", "status": "dropped", "events": 3}]))

    def test_a_dropped_task_whose_events_became_a_summary_is_refused_with_its_ask(self):
        from unittest import mock
        self.summarize()
        with mock.patch.object(project, "taken_on_remote") as remote, self.assertRaises(project.SettingsError) as said:
            project.cmd_resume(self.root, "card-foot")
        message = str(said.exception)
        self.assertIn("the events of 'card-foot' (its approved criteria, the personas' read, its decisions' events) became one summary event past state.keep_days", message)
        self.assertIn("so a resumed task would start with none of them", message)
        self.assertIn("A new task with its ask is the way on", message)
        self.assertTrue(message.endswith("\n/lem Put the card's foot under the total"), message)
        remote.assert_not_called()
        self.assertFalse((self.state / "tasks" / "card-foot-2").exists())

    def test_a_dropped_task_whose_events_are_whole_resumes_as_before(self):
        from unittest import mock
        with mock.patch.object(project, "taken_on_remote"):
            said = project.cmd_resume(self.root, "card-foot")
        self.assertEqual((said["task"], said["resumed"], said["from"]), ("card-foot-2", "dropped", "card-foot"))
        carried = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if json.loads(line)["task"] == "card-foot-2"]
        self.assertEqual([(e["event"], e["from"], e["was_at"]) for e in carried], [("criteria.approved", "card-foot", back(39))])

    def test_a_resume_whose_log_is_summarized_after_its_read_carries_what_it_read(self):
        from unittest import mock
        # the board server's prune summarizes the task while the resume asks origin for the new branch
        with mock.patch.object(project, "taken_on_remote", side_effect=lambda *args: self.summarize()):
            said = project.cmd_resume(self.root, "card-foot")
        self.assertEqual(said["task"], "card-foot-2")
        records = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["event"] for r in records if r["task"] == "card-foot"], ["task.summary"])
        self.assertEqual([(r["event"], r["from"]) for r in records if r["task"] == "card-foot-2"], [("criteria.approved", "card-foot")])


if __name__ == "__main__":
    unittest.main()
