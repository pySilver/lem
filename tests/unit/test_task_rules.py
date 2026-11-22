"""The rules of a task's state and of the event log, as calls of the functions that hold them: the
type line of a state block (`type_line`), the steps a ticket still waits for (`ticket_owed`), and the
form of each record `lem project log` checks before it appends (`investigation_form`, `read_form`,
`start_form`, `talk_start_form`, `talk_form`). Each rule takes the fields and returns or refuses
with the words a refusal of the real command prints. That `state` and `log` call these rules, refuse
with exit 1 and append nothing then, and that `tasks` gives the newest record, are facts only the
real command shows: tests/lem-settings.sh runs one journey for each.

    python3 -B -m unittest discover -s tests/unit
"""

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
import project  # noqa: E402


class Refuses(unittest.TestCase):
    """A rule that refuses raises SettingsError, whose words name the fix."""

    def refused(self, call, *args) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            call(*args)
        return str(caught.exception)


class TypeLine(Refuses):
    """`type: TYPE, because WHY`, which the status and the board read from a state block."""

    def test_a_line_that_names_no_type_is_free(self):
        self.assertIsNone(project.type_line("lead: builder"))
        self.assertIsNone(project.type_line("the type: fix, because x"))

    def test_a_type_with_its_reason(self):
        self.assertEqual(project.type_line("  type: fix, because the ask says the total is wrong today  "),
                         {"type": "fix", "why": "the ask says the total is wrong today"})

    def test_each_of_the_eight_types_is_taken(self):
        self.assertEqual(project.TYPES, ("feat", "fix", "docs", "refactor", "perf", "test", "chore", "question"))
        for kind in project.TYPES:
            self.assertEqual(project.type_line(f"type: {kind}, because a reason")["type"], kind)

    def test_a_type_that_is_none_of_the_eight_names_them(self):
        message = self.refused(project.type_line, "type: defect, because the total is wrong")
        self.assertIn("'defect' is not a type of request", message)
        self.assertIn("feat, fix, docs, refactor, perf, test, chore, question", message)

    def test_a_misspelled_type_names_the_nearest(self):
        self.assertIn("did you mean 'fix'?", self.refused(project.type_line, "type: fux, because the total is wrong"))

    def test_a_type_without_its_reason(self):
        self.assertIn("the line 'type: fix' names the type without its reason: write it as `type: fix, because ...`",
                      self.refused(project.type_line, "type: fix"))


class TicketOwed(unittest.TestCase):
    """The steps a ticket still waits for once its task ended, from its status and the steps written down."""

    TRACKER = {"kind": "linear"}

    def test_no_tracker_owes_nothing(self):
        self.assertEqual(project.ticket_owed("landed", [], None), [])

    def test_a_task_that_still_runs_owes_nothing(self):
        self.assertEqual(project.ticket_owed("building", ["started"], self.TRACKER), [])
        self.assertEqual(project.ticket_owed(None, [], self.TRACKER), [])

    def test_a_landed_task_owes_the_comment_and_the_status_not_written_down(self):
        self.assertEqual(project.ticket_owed("landed", ["started"], self.TRACKER), ["commented", "landed"])
        self.assertEqual(project.ticket_owed("landed", ["started", "commented"], self.TRACKER), ["landed"])
        self.assertEqual(project.ticket_owed("landed", ["started", "commented", "landed"], self.TRACKER), [])

    def test_a_dropped_task_owes_its_drop_comment(self):
        self.assertEqual(project.ticket_owed("dropped", ["started", "commented"], self.TRACKER), ["dropped"])
        self.assertEqual(project.ticket_owed("dropped", ["dropped"], self.TRACKER), [])

    def test_an_answered_task_owes_the_answer_comment_until_it_is_written_down(self):
        self.assertEqual(project.ticket_owed("answered", [], self.TRACKER), ["answered"])
        self.assertEqual(project.ticket_owed("answered", ["answered"], self.TRACKER), [])


class InvestigationForm(Refuses):
    """What an investigation found: its type, its call, one line, a fix's place and whether it reproduced the bug."""

    def fix(self, **changes) -> dict:
        return {"type": "fix", "call": "full", "line": "the invoice total adds the refund as a payment",
                "where": "billing/invoice.py:total", "reproduced": True, **changes}

    def test_a_fix_and_a_question_in_their_form(self):
        self.assertIsNone(project.investigation_form(self.fix()))
        self.assertIsNone(project.investigation_form({"type": "question", "call": "answer", "line": "the refund writes a credit note"}))

    def test_a_bug_that_is_none_needs_no_place(self):
        self.assertIsNone(project.investigation_form({"type": "fix", "call": "not-a-bug", "line": "a refund is a credit note", "reproduced": False}))
        self.assertIsNone(project.investigation_form({"type": "fix", "call": "not-reproduced", "line": "a refund of 10 gave 90", "reproduced": False}))

    def test_a_missing_or_an_unknown_field(self):
        message = self.refused(project.investigation_form, {"type": "fix", "call": "full"})
        self.assertIn("investigation takes type=fix|question call=CALL line=TEXT", message)
        self.assertIn("and nothing else; this one has call, type", message)
        self.assertIn("this one has call, cause, line, reproduced, type, where", self.refused(project.investigation_form, self.fix(cause="x")))

    def test_a_type_that_is_neither_fix_nor_question(self):
        self.assertIn("type is fix or question, not 'bug'", self.refused(project.investigation_form, self.fix(type="bug")))

    def test_a_call_the_type_does_not_have(self):
        self.assertIn("call is small, full, not-a-bug or not-reproduced for a fix, and answer for a question; this one is 'maybe' for a fix",
                      self.refused(project.investigation_form, self.fix(call="maybe", line="x", reproduced=False)))
        self.assertIn("this one is 'answer' for a fix", self.refused(project.investigation_form, self.fix(call="answer")))

    def test_a_line_that_is_not_one_line(self):
        for line in ("", "  ", "the cause\nand more"):
            self.assertIn("line is one line of text", self.refused(project.investigation_form, self.fix(line=line)))

    def test_an_empty_place(self):
        self.assertIn("where is the cause's file and symbol, as path:symbol", self.refused(project.investigation_form, self.fix(where=" ")))

    def test_a_question_reproduces_nothing(self):
        self.assertIn("reproduced is a fix's", self.refused(
            project.investigation_form, {"type": "question", "call": "answer", "line": "the refund writes a credit note", "reproduced": True}))

    def test_a_fix_says_whether_the_bug_was_reproduced_as_json(self):
        self.assertIn("written with :=", self.refused(project.investigation_form, self.fix(where="a.py:f", line="x", reproduced="true")))
        fields = self.fix()
        del fields["reproduced"]
        self.assertIn("reproduced:=true or reproduced:=false", self.refused(project.investigation_form, fields))

    def test_a_plain_cause_has_a_place(self):
        fields = self.fix(call="small", line="the total skips credit notes")
        del fields["where"]
        self.assertIn("a plain cause has a place: where names the cause's file and symbol", self.refused(project.investigation_form, fields))

    def test_not_reproduced_that_says_it_was(self):
        self.assertIn("not-reproduced is a bug that was not reproduced, and this record says it was",
                      self.refused(project.investigation_form, self.fix(call="not-reproduced", line="a refund of 10 gave 90")))


class ReadForm(Refuses):
    """The personas' read of the criteria, which the landing reads."""

    QUIET = [{"name": "the buyer, opus", "why": "the model was at capacity"}, {"name": "the clerk, opus", "why": "the model was at capacity"}]

    def read(self, **changes) -> dict:
        return {"by": "lead", "asked": 2, "answered": 2, "families": ["opus"], "silent": [], "criteria": 1, "flagged": 0,
                "split": False, "digest": "0123456789ab", **changes}

    def test_a_read_in_its_form(self):
        self.assertIsNone(project.read_form(self.read()))
        self.assertIsNone(project.read_form(self.read(by="lem", families=["opus", "sol"], split=True, criteria=2, flagged=2)))
        self.assertIsNone(project.read_form(self.read(asked=3, silent=[{"name": "the clerk, sol", "why": "a timeout"}])))

    def test_a_read_in_which_nobody_answered_in_its_form(self):
        self.assertIsNone(project.read_form(self.read(answered=0, families=[], silent=self.QUIET)))

    def test_a_missing_or_an_unknown_field(self):
        fields = self.read()
        del fields["silent"]
        message = self.refused(project.read_form, fields)
        self.assertIn("criteria.read takes by=lem|lead asked:=N answered:=N", message)
        self.assertIn("and nothing else; this one has answered, asked, by, criteria, digest, families, flagged, split", message)

    def test_by_someone_else(self):
        self.assertIn("by is lem, when Lem ran the read", self.refused(project.read_form, self.read(by="owner")))

    def test_a_count_that_is_no_whole_number(self):
        for value in ("2", -1, True):
            self.assertIn("each N is a whole number, written with :=", self.refused(project.read_form, self.read(asked=value)))

    def test_families_that_are_no_list_of_names_each_once(self):
        for families in ("opus", ["opus", "opus"], [""], []):
            self.assertIn("families is the list of the model families that answered", self.refused(project.read_form, self.read(families=families)))

    def test_silent_sources_without_their_name_and_why(self):
        for silent in ({}, [{"name": "the buyer"}], [{"name": "the buyer", "why": " "}]):
            self.assertIn('silent is a list of {"name": ..., "why": ...}', self.refused(project.read_form, self.read(silent=silent)))

    def test_a_split_that_is_no_boolean(self):
        self.assertIn("split is true when the two families answered a criterion differently", self.refused(project.read_form, self.read(split="false")))

    def test_a_digest_that_is_not_the_twelve_characters(self):
        self.assertIn("digest is the twelve characters", self.refused(project.read_form, self.read(digest="abc")))

    def test_fewer_than_two_personas_asked(self):
        self.assertIn("a read asks two personas at the least", self.refused(project.read_form, self.read(asked=1, answered=1)))

    def test_more_answered_than_asked(self):
        self.assertIn("answered is at most asked", self.refused(project.read_form, self.read(answered=3)))

    def test_a_read_in_which_nobody_answered_with_a_family_a_flag_or_an_unnamed_source(self):
        said = "a read in which nobody answered has families:='[]'"
        self.assertIn(said, self.refused(project.read_form, self.read(answered=0, silent=[{"name": "a", "why": "b"}])))
        self.assertIn(said, self.refused(project.read_form, self.read(answered=0, families=["opus"], silent=self.QUIET)))
        self.assertIn(said, self.refused(project.read_form, self.read(answered=0, families=[], silent=self.QUIET[:1])))
        self.assertIn(said, self.refused(project.read_form, self.read(answered=0, families=[], silent=self.QUIET, flagged=1)))

    def test_fewer_answered_than_asked_with_nobody_named(self):
        self.assertIn("silent names each source that did not, with why", self.refused(project.read_form, self.read(asked=3)))

    def test_no_criterion_or_more_flagged_than_read(self):
        said = "a read has one criterion at the least, and no more criteria flagged than it read"
        self.assertIn(said, self.refused(project.read_form, self.read(flagged=2)))
        self.assertIn(said, self.refused(project.read_form, self.read(criteria=0)))

    def test_a_split_with_one_family(self):
        self.assertIn("a split is between two model families, and families names one", self.refused(project.read_form, self.read(split=True)))


class StartForm(Refuses):
    """The start of each stage, from which the board draws its span."""

    def test_each_start_in_its_form(self):
        for event, fields in [("interview.start", {}), ("scout.start", {}), ("scout", {}),
                              ("criteria.read.start", {"by": "lem"}), ("criteria.read.start", {"by": "lead"}),
                              ("investigation.start", {"type": "fix"}), ("investigation.start", {"type": "question"}),
                              ("builder.start", {"job": "task 2 of 3"}), *(("builder.start", {"job": job}) for job in project.BUILDER_JOBS),
                              ("polish.start", {"before": "abc1234"}), ("gate.start", {"tip": "abc123456", "commands": 1}),
                              ("review.start", {"attempt": 2, "floor": "round"})]:
            with self.subTest(event=event, fields=fields):
                self.assertIsNone(project.start_form(event, fields))

    def test_a_start_that_takes_nothing_with_a_field(self):
        self.assertIn("interview.start takes nothing; this one has by", self.refused(project.start_form, "interview.start", {"by": "lem"}))

    def test_a_start_without_its_field(self):
        self.assertIn("criteria.read.start takes by=lem|lead, and nothing else; this one has no field",
                      self.refused(project.start_form, "criteria.read.start", {}))

    def test_a_value_the_field_does_not_have(self):
        self.assertIn("by is 'owner'", self.refused(project.start_form, "criteria.read.start", {"by": "owner"}))
        self.assertIn("floor is 'half'", self.refused(project.start_form, "review.start", {"attempt": 1, "floor": "half"}))

    def test_another_field_in_place_of_its_own(self):
        self.assertIn("investigation.start takes type=fix|question", self.refused(project.start_form, "investigation.start", {"kind": "question"}))

    def test_a_job_no_builder_has(self):
        message = self.refused(project.start_form, "builder.start", {"job": "the polish pass"})
        self.assertIn("builder.start takes job=", message)
        self.assertIn("the polish pass logs its own start", message)
        self.assertIn("job is 'task 0 of 3'", self.refused(project.start_form, "builder.start", {"job": "task 0 of 3"}))

    def test_a_script_start_in_another_form(self):
        self.assertIn("gate.start takes tip=TIP commands:=N", self.refused(project.start_form, "gate.start", {"tip": "abc123456"}))

    def test_a_tip_that_is_no_commit(self):
        self.assertIn("the tip is a commit, as git names it", self.refused(project.start_form, "gate.start", {"tip": "main", "commands": 1}))
        self.assertIn("the tip is a commit, as git names it", self.refused(project.start_form, "polish.start", {"before": "abc"}))

    def test_a_count_below_one_or_no_number(self):
        self.assertIn("commands is a whole number, 1 or more, written with :=", self.refused(project.start_form, "gate.start", {"tip": "abc1234", "commands": 0}))
        self.assertIn("attempt is a whole number, 1 or more", self.refused(project.start_form, "review.start", {"attempt": True, "floor": "read"}))


class TalkStartForm(Refuses):
    """The start of a plan talk names its reviewer and nothing else."""

    def test_a_start_that_names_its_reviewer(self):
        self.assertIsNone(project.talk_start_form({"reviewer": "codex"}))

    def test_a_start_with_no_reviewer_another_field_or_a_blank_one(self):
        said = "plan.talk.start takes reviewer=AGENT, and nothing else"
        self.assertIn(f"{said}; this one has no field", self.refused(project.talk_start_form, {}))
        self.assertIn(f"{said}; this one has reviewer, turns", self.refused(project.talk_start_form, {"reviewer": "codex", "turns": 2}))
        self.assertIn(said, self.refused(project.talk_start_form, {"reviewer": " "}))


class TalkForm(Refuses):
    """A plan talk's record: its reviewer and its counts, which agree with each other."""

    def talk(self, **changes) -> dict:
        return {"reviewer": "codex", "turns": 6, "questions": 3, "settled": 2, "open": 1, "repaired": 2, "design": 1,
                "unargued": 0, "root": 1, "layer": 1, "shared": 1, **changes}

    def test_a_talk_in_its_form(self):
        self.assertIsNone(project.talk_form(self.talk()))

    def test_a_talk_of_no_question_and_two_turns(self):
        self.assertIsNone(project.talk_form(self.talk(turns=2, questions=0, settled=0, open=0, repaired=0, design=0, root=0, layer=0, shared=0)))

    def test_what_breaks_a_rule_of_the_talk_and_not_a_count_is_taken(self):
        # more decisions two questions named than design choices, and more turns than its bound
        self.assertIsNone(project.talk_form(self.talk(shared=2)))
        self.assertIsNone(project.talk_form(self.talk(turns=11, questions=2, settled=1, open=1, repaired=1, design=1, unargued=3, root=0, layer=0, shared=0)))
        self.assertIsNone(project.talk_form(self.talk(turns=3, questions=0, settled=0, open=0, repaired=0, design=0, unargued=1, root=0, layer=0, shared=0)))

    def test_a_missing_or_an_unknown_field(self):
        fields = self.talk()
        for key in ("root", "layer", "shared"):
            del fields[key]
        message = self.refused(project.talk_form, fields)
        self.assertIn("plan.talk takes reviewer=AGENT turns:=N", message)
        self.assertIn("and nothing else; this one has design, open, questions, repaired, reviewer, settled, turns, unargued", message)
        self.assertIn("and nothing else; this one has bound, design,", self.refused(project.talk_form, self.talk(bound=5)))

    def test_a_blank_reviewer(self):
        self.assertIn("reviewer names the agent that argued the plan with its defender", self.refused(project.talk_form, self.talk(reviewer=" ")))

    def test_a_count_that_is_no_whole_number(self):
        for changes in ({"layer": "1"}, {"turns": "5"}, {"shared": -1}, {"open": True}):
            self.assertIn("each N is a whole number, written with := so that it stays one", self.refused(project.talk_form, self.talk(**changes)))

    def test_fewer_than_two_turns(self):
        self.assertIn("a talk has two turns at the least", self.refused(
            project.talk_form, self.talk(turns=1, questions=0, settled=0, open=0, repaired=0, design=0, root=0, layer=0, shared=0)))

    def test_a_talk_of_no_question_and_two_turns_with_a_question_raised_after_the_list(self):
        self.assertIn("a talk of no question and two turns has no turn after the list, so unargued is 0", self.refused(
            project.talk_form, self.talk(turns=2, questions=0, settled=0, open=0, repaired=0, design=0, unargued=1, root=0, layer=0, shared=0)))

    def test_settled_and_open_that_do_not_add_up_to_questions(self):
        self.assertIn("settled and open add up to questions", self.refused(project.talk_form, self.talk(settled=1)))

    def test_more_design_choices_than_open_questions(self):
        self.assertIn("design is at most open", self.refused(project.talk_form, self.talk(design=2)))

    def test_more_repairs_than_questions(self):
        self.assertIn("repaired is at most questions", self.refused(project.talk_form, self.talk(settled=3, open=0, design=0, repaired=4, root=0, layer=0)))

    def test_more_repairs_at_the_cause_and_layers_than_repairs(self):
        self.assertIn("root and layer add up to at most repaired", self.refused(project.talk_form, self.talk(layer=2, shared=0)))


if __name__ == "__main__":
    unittest.main()
