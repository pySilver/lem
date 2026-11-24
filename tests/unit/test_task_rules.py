"""The rules of a task's state and of the event log, as calls of the functions that hold
them: the type line of a state block (`type_line`), the steps a ticket still waits for
(`ticket_owed`), and the form of each record `lem project log` checks before it appends
(`investigation_form`, `read_form`, `start_form`, `talk_start_form`, `talk_form`). Each
rule takes the fields and returns or refuses with the words a refusal of the real
command prints. That `state` and `log` call these rules, refuse with exit 1 and append
nothing then, and that `tasks` gives the newest record, are facts only the real command
shows: tests/lem-settings.sh runs one journey for each.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, cast

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import project

if TYPE_CHECKING:
    from collections.abc import Callable


class Refuses(unittest.TestCase):
    """A rule that refuses raises SettingsError, whose words name the fix."""

    def refused(self, call: Callable[..., object], *args: object) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            call(*args)
        return str(caught.exception)


class TypeLine(Refuses):
    """`type: TYPE, because WHY`, which the status and the board read from a
    state block."""

    def test_a_line_that_names_no_type_is_free(self) -> None:
        self.assertIsNone(project.type_line("lead: builder"))
        self.assertIsNone(project.type_line("the type: fix, because x"))

    def test_a_type_with_its_reason(self) -> None:
        self.assertEqual(
            project.type_line(
                "  type: fix, because the ask says the total is wrong today  "
            ),
            {"type": "fix", "why": "the ask says the total is wrong today"},
        )

    def test_each_of_the_eight_types_is_taken(self) -> None:
        self.assertEqual(
            project.TYPES,
            ("feat", "fix", "docs", "refactor", "perf", "test", "chore", "question"),
        )
        for kind in project.TYPES:
            self.assertEqual(
                cast("dict", project.type_line(f"type: {kind}, because a reason"))[
                    "type"
                ],
                kind,
            )

    def test_a_type_that_is_none_of_the_eight_names_them(self) -> None:
        message = self.refused(
            project.type_line, "type: defect, because the total is wrong"
        )
        self.assertIn("'defect' is not a type of request", message)
        self.assertIn("feat, fix, docs, refactor, perf, test, chore, question", message)

    def test_a_misspelled_type_names_the_nearest(self) -> None:
        self.assertIn(
            "did you mean 'fix'?",
            self.refused(project.type_line, "type: fux, because the total is wrong"),
        )

    def test_a_type_without_its_reason(self) -> None:
        self.assertIn(
            (
                "the line 'type: fix' names the type without its reason: "
                "write it as `type: fix, because ...`"
            ),
            self.refused(project.type_line, "type: fix"),
        )


class TicketOwed(unittest.TestCase):
    """The steps a ticket still waits for once its task ended, from its status and the
    steps written down."""

    TRACKER = {"kind": "linear"}

    def test_no_tracker_owes_nothing(self) -> None:
        self.assertEqual(project.ticket_owed("landed", [], None), [])

    def test_a_task_that_still_runs_owes_nothing(self) -> None:
        self.assertEqual(project.ticket_owed("building", ["started"], self.TRACKER), [])
        self.assertEqual(project.ticket_owed(None, [], self.TRACKER), [])

    def test_a_landed_task_owes_the_comment_and_the_status_not_written_down(
        self,
    ) -> None:
        self.assertEqual(
            project.ticket_owed("landed", ["started"], self.TRACKER),
            ["commented", "landed"],
        )
        self.assertEqual(
            project.ticket_owed("landed", ["started", "commented"], self.TRACKER),
            ["landed"],
        )
        self.assertEqual(
            project.ticket_owed(
                "landed", ["started", "commented", "landed"], self.TRACKER
            ),
            [],
        )

    def test_a_dropped_task_owes_its_drop_comment(self) -> None:
        self.assertEqual(
            project.ticket_owed("dropped", ["started", "commented"], self.TRACKER),
            ["dropped"],
        )
        self.assertEqual(project.ticket_owed("dropped", ["dropped"], self.TRACKER), [])

    def test_an_answered_task_owes_the_answer_comment_until_it_is_written_down(
        self,
    ) -> None:
        self.assertEqual(
            project.ticket_owed("answered", [], self.TRACKER), ["answered"]
        )
        self.assertEqual(
            project.ticket_owed("answered", ["answered"], self.TRACKER), []
        )


class InvestigationForm(Refuses):
    """What an investigation found: its type, its call, one line, a fix's place and
    whether it reproduced the bug."""

    def fix(self, **changes: object) -> dict:
        return {
            "type": "fix",
            "call": "full",
            "line": "the invoice total adds the refund as a payment",
            "where": "billing/invoice.py:total",
            "reproduced": True,
            **changes,
        }

    def test_a_fix_and_a_question_in_their_form(self) -> None:
        self.assertIsNone(project.investigation_form(self.fix()))
        self.assertIsNone(
            project.investigation_form(
                {
                    "type": "question",
                    "call": "answer",
                    "line": "the refund writes a credit note",
                }
            )
        )

    def test_a_bug_that_is_none_needs_no_place(self) -> None:
        self.assertIsNone(
            project.investigation_form(
                {
                    "type": "fix",
                    "call": "not-a-bug",
                    "line": "a refund is a credit note",
                    "reproduced": False,
                }
            )
        )
        self.assertIsNone(
            project.investigation_form(
                {
                    "type": "fix",
                    "call": "not-reproduced",
                    "line": "a refund of 10 gave 90",
                    "reproduced": False,
                }
            )
        )

    def test_a_missing_or_an_unknown_field(self) -> None:
        message = self.refused(
            project.investigation_form, {"type": "fix", "call": "full"}
        )
        self.assertIn(
            "investigation takes type=fix|question call=CALL line=TEXT", message
        )
        self.assertIn("and nothing else; this one has call, type", message)
        self.assertIn(
            "this one has call, cause, line, reproduced, type, where",
            self.refused(project.investigation_form, self.fix(cause="x")),
        )

    def test_a_type_that_is_neither_fix_nor_question(self) -> None:
        self.assertIn(
            "type is fix or question, not 'bug'",
            self.refused(project.investigation_form, self.fix(type="bug")),
        )

    def test_a_call_the_type_does_not_have(self) -> None:
        self.assertIn(
            (
                "call is small, full, not-a-bug or not-reproduced for a fix, and "
                "answer for a question; this one is 'maybe' for a fix"
            ),
            self.refused(
                project.investigation_form,
                self.fix(call="maybe", line="x", reproduced=False),
            ),
        )
        self.assertIn(
            "this one is 'answer' for a fix",
            self.refused(project.investigation_form, self.fix(call="answer")),
        )

    def test_a_line_that_is_not_one_line(self) -> None:
        for line in ("", "  ", "the cause\nand more"):
            self.assertIn(
                "line is one line of text",
                self.refused(project.investigation_form, self.fix(line=line)),
            )

    def test_an_empty_place(self) -> None:
        self.assertIn(
            "where is the cause's file and symbol, as path:symbol",
            self.refused(project.investigation_form, self.fix(where=" ")),
        )

    def test_a_question_reproduces_nothing(self) -> None:
        self.assertIn(
            "reproduced is a fix's",
            self.refused(
                project.investigation_form,
                {
                    "type": "question",
                    "call": "answer",
                    "line": "the refund writes a credit note",
                    "reproduced": True,
                },
            ),
        )

    def test_a_fix_says_whether_the_bug_was_reproduced_as_json(self) -> None:
        self.assertIn(
            "written with :=",
            self.refused(
                project.investigation_form,
                self.fix(where="a.py:f", line="x", reproduced="true"),
            ),
        )
        fields = self.fix()
        del fields["reproduced"]
        self.assertIn(
            "reproduced:=true or reproduced:=false",
            self.refused(project.investigation_form, fields),
        )

    def test_a_plain_cause_has_a_place(self) -> None:
        fields = self.fix(call="small", line="the total skips credit notes")
        del fields["where"]
        self.assertIn(
            "a plain cause has a place: where names the cause's file and symbol",
            self.refused(project.investigation_form, fields),
        )

    def test_not_reproduced_that_says_it_was(self) -> None:
        self.assertIn(
            (
                "not-reproduced is a bug that was not reproduced, "
                "and this record says it was"
            ),
            self.refused(
                project.investigation_form,
                self.fix(call="not-reproduced", line="a refund of 10 gave 90"),
            ),
        )


class ReadForm(Refuses):
    """The personas' read of the criteria, which the landing reads."""

    QUIET = [
        {"name": "the buyer, opus", "why": "the model was at capacity"},
        {"name": "the clerk, opus", "why": "the model was at capacity"},
    ]

    def read(self, **changes: object) -> dict:
        return {
            "by": "lead",
            "asked": 2,
            "answered": 2,
            "families": ["opus"],
            "silent": [],
            "criteria": 1,
            "flagged": 0,
            "split": False,
            "digest": "0123456789ab",
            **changes,
        }

    def test_a_read_in_its_form(self) -> None:
        self.assertIsNone(project.read_form(self.read()))
        self.assertIsNone(
            project.read_form(
                self.read(
                    by="lem",
                    families=["opus", "sol"],
                    split=True,
                    criteria=2,
                    flagged=2,
                )
            )
        )
        self.assertIsNone(
            project.read_form(
                self.read(
                    asked=3, silent=[{"name": "the clerk, sol", "why": "a timeout"}]
                )
            )
        )

    def test_a_read_in_which_nobody_answered_in_its_form(self) -> None:
        self.assertIsNone(
            project.read_form(self.read(answered=0, families=[], silent=self.QUIET))
        )

    def test_a_missing_or_an_unknown_field(self) -> None:
        fields = self.read()
        del fields["silent"]
        message = self.refused(project.read_form, fields)
        self.assertIn("criteria.read takes by=lem|lead asked:=N answered:=N", message)
        self.assertIn(
            (
                "and nothing else; this one has answered, asked, by, criteria, digest, "
                "families, flagged, split"
            ),
            message,
        )

    def test_by_someone_else(self) -> None:
        self.assertIn(
            "by is lem, when Lem ran the read",
            self.refused(project.read_form, self.read(by="owner")),
        )

    def test_a_count_that_is_no_whole_number(self) -> None:
        for value in ("2", -1, True):
            self.assertIn(
                "each N is a whole number, written with :=",
                self.refused(project.read_form, self.read(asked=value)),
            )

    def test_families_that_are_no_list_of_names_each_once(self) -> None:
        for families in ("opus", ["opus", "opus"], [""], []):
            self.assertIn(
                "families is the list of the model families that answered",
                self.refused(project.read_form, self.read(families=families)),
            )

    def test_silent_sources_without_their_name_and_why(self) -> None:
        for silent in (
            {},
            [{"name": "the buyer"}],
            [{"name": "the buyer", "why": " "}],
        ):
            self.assertIn(
                'silent is a list of {"name": ..., "why": ...}',
                self.refused(project.read_form, self.read(silent=silent)),
            )

    def test_a_split_that_is_no_boolean(self) -> None:
        self.assertIn(
            "split is true when the two families answered a criterion differently",
            self.refused(project.read_form, self.read(split="false")),
        )

    def test_a_digest_that_is_not_the_twelve_characters(self) -> None:
        self.assertIn(
            "digest is the twelve characters",
            self.refused(project.read_form, self.read(digest="abc")),
        )

    def test_fewer_than_two_personas_asked(self) -> None:
        self.assertIn(
            "a read asks two personas at the least",
            self.refused(project.read_form, self.read(asked=1, answered=1)),
        )

    def test_more_answered_than_asked(self) -> None:
        self.assertIn(
            "answered is at most asked",
            self.refused(project.read_form, self.read(answered=3)),
        )

    def test_a_read_in_which_nobody_answered_with_a_family_a_flag_or_an_unnamed_source(
        self,
    ) -> None:
        said = "a read in which nobody answered has families:='[]'"
        self.assertIn(
            said,
            self.refused(
                project.read_form,
                self.read(answered=0, silent=[{"name": "a", "why": "b"}]),
            ),
        )
        self.assertIn(
            said,
            self.refused(
                project.read_form,
                self.read(answered=0, families=["opus"], silent=self.QUIET),
            ),
        )
        self.assertIn(
            said,
            self.refused(
                project.read_form,
                self.read(answered=0, families=[], silent=self.QUIET[:1]),
            ),
        )
        self.assertIn(
            said,
            self.refused(
                project.read_form,
                self.read(answered=0, families=[], silent=self.QUIET, flagged=1),
            ),
        )

    def test_fewer_answered_than_asked_with_nobody_named(self) -> None:
        self.assertIn(
            "silent names each source that did not, with why",
            self.refused(project.read_form, self.read(asked=3)),
        )

    def test_no_criterion_or_more_flagged_than_read(self) -> None:
        said = (
            "a read has one criterion at the least, and no more "
            "criteria flagged than it read"
        )
        self.assertIn(said, self.refused(project.read_form, self.read(flagged=2)))
        self.assertIn(said, self.refused(project.read_form, self.read(criteria=0)))

    def test_a_split_with_one_family(self) -> None:
        self.assertIn(
            "a split is between two model families, and families names one",
            self.refused(project.read_form, self.read(split=True)),
        )


class StartForm(Refuses):
    """The start of each stage, from which the board draws its span."""

    def test_each_start_in_its_form(self) -> None:
        for event, fields in [
            ("interview.start", {}),
            ("scout.start", {}),
            ("scout", {}),
            ("criteria.read.start", {"by": "lem"}),
            ("criteria.read.start", {"by": "lead"}),
            ("investigation.start", {"type": "fix"}),
            ("investigation.start", {"type": "question"}),
            ("builder.start", {"job": "task 2 of 3"}),
            *(("builder.start", {"job": job}) for job in project.BUILDER_JOBS),
            ("polish.start", {"before": "abc1234"}),
            ("gate.start", {"tip": "abc123456", "commands": 1}),
            ("review.start", {"attempt": 2, "floor": "round"}),
        ]:
            with self.subTest(event=event, fields=fields):
                self.assertIsNone(project.start_form(event, fields))

    def test_a_start_that_takes_nothing_with_a_field(self) -> None:
        self.assertIn(
            "interview.start takes nothing; this one has by",
            self.refused(project.start_form, "interview.start", {"by": "lem"}),
        )

    def test_a_start_without_its_field(self) -> None:
        self.assertIn(
            (
                "criteria.read.start takes by=lem|lead, and nothing else; "
                "this one has no field"
            ),
            self.refused(project.start_form, "criteria.read.start", {}),
        )

    def test_a_value_the_field_does_not_have(self) -> None:
        self.assertIn(
            "by is 'owner'",
            self.refused(project.start_form, "criteria.read.start", {"by": "owner"}),
        )
        self.assertIn(
            "floor is 'half'",
            self.refused(
                project.start_form, "review.start", {"attempt": 1, "floor": "half"}
            ),
        )

    def test_another_field_in_place_of_its_own(self) -> None:
        self.assertIn(
            "investigation.start takes type=fix|question",
            self.refused(
                project.start_form, "investigation.start", {"kind": "question"}
            ),
        )

    def test_a_job_no_builder_has(self) -> None:
        message = self.refused(
            project.start_form, "builder.start", {"job": "the polish pass"}
        )
        self.assertIn("builder.start takes job=", message)
        self.assertIn("the polish pass logs its own start", message)
        self.assertIn(
            "job is 'task 0 of 3'",
            self.refused(project.start_form, "builder.start", {"job": "task 0 of 3"}),
        )

    def test_a_script_start_in_another_form(self) -> None:
        self.assertIn(
            "gate.start takes tip=TIP commands:=N",
            self.refused(project.start_form, "gate.start", {"tip": "abc123456"}),
        )

    def test_a_tip_that_is_no_commit(self) -> None:
        self.assertIn(
            "the tip is a commit, as git names it",
            self.refused(
                project.start_form, "gate.start", {"tip": "main", "commands": 1}
            ),
        )
        self.assertIn(
            "the tip is a commit, as git names it",
            self.refused(project.start_form, "polish.start", {"before": "abc"}),
        )

    def test_a_count_below_one_or_no_number(self) -> None:
        self.assertIn(
            "commands is a whole number, 1 or more, written with :=",
            self.refused(
                project.start_form, "gate.start", {"tip": "abc1234", "commands": 0}
            ),
        )
        self.assertIn(
            "attempt is a whole number, 1 or more",
            self.refused(
                project.start_form, "review.start", {"attempt": True, "floor": "read"}
            ),
        )


class TalkStartForm(Refuses):
    """The start of a plan talk names its reviewer and nothing else."""

    def test_a_start_that_names_its_reviewer(self) -> None:
        self.assertIsNone(project.talk_start_form({"reviewer": "codex"}))

    def test_a_start_with_no_reviewer_another_field_or_a_blank_one(self) -> None:
        said = "plan.talk.start takes reviewer=AGENT, and nothing else"
        self.assertIn(
            f"{said}; this one has no field", self.refused(project.talk_start_form, {})
        )
        self.assertIn(
            f"{said}; this one has reviewer, turns",
            self.refused(project.talk_start_form, {"reviewer": "codex", "turns": 2}),
        )
        self.assertIn(said, self.refused(project.talk_start_form, {"reviewer": " "}))


class TalkForm(Refuses):
    """A plan talk's record: its reviewer and its counts, which agree with
    each other."""

    def talk(self, **changes: object) -> dict:
        return {
            "reviewer": "codex",
            "turns": 6,
            "questions": 3,
            "settled": 2,
            "open": 1,
            "repaired": 2,
            "design": 1,
            "unargued": 0,
            "root": 1,
            "layer": 1,
            "shared": 1,
            **changes,
        }

    def test_a_talk_in_its_form(self) -> None:
        self.assertIsNone(project.talk_form(self.talk()))

    def test_a_talk_of_no_question_and_two_turns(self) -> None:
        self.assertIsNone(
            project.talk_form(
                self.talk(
                    turns=2,
                    questions=0,
                    settled=0,
                    open=0,
                    repaired=0,
                    design=0,
                    root=0,
                    layer=0,
                    shared=0,
                )
            )
        )

    def test_what_breaks_a_rule_of_the_talk_and_not_a_count_is_taken(self) -> None:
        # more decisions two questions named than design choices, and more turns than
        # its bound
        self.assertIsNone(project.talk_form(self.talk(shared=2)))
        self.assertIsNone(
            project.talk_form(
                self.talk(
                    turns=11,
                    questions=2,
                    settled=1,
                    open=1,
                    repaired=1,
                    design=1,
                    unargued=3,
                    root=0,
                    layer=0,
                    shared=0,
                )
            )
        )
        self.assertIsNone(
            project.talk_form(
                self.talk(
                    turns=3,
                    questions=0,
                    settled=0,
                    open=0,
                    repaired=0,
                    design=0,
                    unargued=1,
                    root=0,
                    layer=0,
                    shared=0,
                )
            )
        )

    def test_a_missing_or_an_unknown_field(self) -> None:
        fields = self.talk()
        for key in ("root", "layer", "shared"):
            del fields[key]
        message = self.refused(project.talk_form, fields)
        self.assertIn("plan.talk takes reviewer=AGENT turns:=N", message)
        self.assertIn(
            (
                "and nothing else; this one has design, open, questions, repaired, "
                "reviewer, settled, turns, unargued"
            ),
            message,
        )
        self.assertIn(
            "and nothing else; this one has bound, design,",
            self.refused(project.talk_form, self.talk(bound=5)),
        )

    def test_a_blank_reviewer(self) -> None:
        self.assertIn(
            "reviewer names the agent that argued the plan with its defender",
            self.refused(project.talk_form, self.talk(reviewer=" ")),
        )

    def test_a_count_that_is_no_whole_number(self) -> None:
        for changes in ({"layer": "1"}, {"turns": "5"}, {"shared": -1}, {"open": True}):
            self.assertIn(
                "each N is a whole number, written with := so that it stays one",
                self.refused(project.talk_form, self.talk(**changes)),
            )

    def test_fewer_than_two_turns(self) -> None:
        self.assertIn(
            "a talk has two turns at the least",
            self.refused(
                project.talk_form,
                self.talk(
                    turns=1,
                    questions=0,
                    settled=0,
                    open=0,
                    repaired=0,
                    design=0,
                    root=0,
                    layer=0,
                    shared=0,
                ),
            ),
        )

    def test_a_talk_of_no_question_and_two_turns_with_a_question_raised_after_the_list(
        self,
    ) -> None:
        self.assertIn(
            (
                "a talk of no question and two turns has no turn after the list, "
                "so unargued is 0"
            ),
            self.refused(
                project.talk_form,
                self.talk(
                    turns=2,
                    questions=0,
                    settled=0,
                    open=0,
                    repaired=0,
                    design=0,
                    unargued=1,
                    root=0,
                    layer=0,
                    shared=0,
                ),
            ),
        )

    def test_settled_and_open_that_do_not_add_up_to_questions(self) -> None:
        self.assertIn(
            "settled and open add up to questions",
            self.refused(project.talk_form, self.talk(settled=1)),
        )

    def test_more_design_choices_than_open_questions(self) -> None:
        self.assertIn(
            "design is at most open",
            self.refused(project.talk_form, self.talk(design=2)),
        )

    def test_more_repairs_than_questions(self) -> None:
        self.assertIn(
            "repaired is at most questions",
            self.refused(
                project.talk_form,
                self.talk(settled=3, open=0, design=0, repaired=4, root=0, layer=0),
            ),
        )

    def test_more_repairs_at_the_cause_and_layers_than_repairs(self) -> None:
        self.assertIn(
            "root and layer add up to at most repaired",
            self.refused(project.talk_form, self.talk(layer=2, shared=0)),
        )


CODEX = {
    "agent": "codex",
    "model": "gpt-6.2-sol",
    "effort": "high",
    "seat": "codex/gpt-6.2-sol:high",
    "from": "Lem's default",
}
CLAUDE = {
    "agent": "claude",
    "model": "opus",
    "effort": "high",
    "seat": "claude/opus:high",
    "from": "Lem's default",
}


class SeatCall(unittest.TestCase):
    """`seat_call`: what a seat whose agent gave one of the four errors comes to, the
    fallback's seat that stands in or the first line of the block, from the seat that
    failed, its error and the fallback."""

    def test_the_fallback_stands_in_for_a_reviewer_with_no_tokens(self) -> None:
        # criterion 3: a Codex reviewer with no tokens, the fallback claude/opus:high
        self.assertEqual(
            project.seat_call("reviewer", "codex/gpt-6.2-sol:high", "tokens", CLAUDE),
            {
                "took": {
                    "agent": "claude",
                    "model": "opus",
                    "effort": "high",
                    "seat": "claude/opus:high",
                }
            },
        )

    def test_a_project_with_no_fallback_blocks_in_the_words_of_criterion_5(
        self,
    ) -> None:
        self.assertEqual(
            project.seat_call(
                "reviewer",
                "codex/gpt-6.2-sol:high",
                "tokens",
                {"seat": False, "from": ".lem/settings.toml"},
            ),
            {
                "block": (
                    "the reviewer `codex/gpt-6.2-sol:high` gave an error: "
                    "no tokens, and this project permits no fallback"
                )
            },
        )

    def test_the_stand_in_that_fails_too_and_a_fallback_that_is_the_named_seat_block(
        self,
    ) -> None:
        # one rule for both: the seat that failed is the fallback, a stand-in's or a
        # reviewer the settings name so
        self.assertEqual(
            project.seat_call("reviewer", "claude/opus:high", "login", CLAUDE),
            {
                "block": (
                    "the reviewer `claude/opus:high` gave an error: no login, "
                    "and it was the fallback"
                )
            },
        )

    def test_a_fallback_whose_agent_cannot_sit_in_the_planners_seat_blocks(
        self,
    ) -> None:
        self.assertEqual(
            project.seat_call("planner", "claude/opus:high", "model", CODEX),
            {
                "block": (
                    "the planner `claude/opus:high` gave an error: an unknown model, "
                    "and its fallback `codex/gpt-6.2-sol:high` cannot sit in the "
                    "planner's seat, which takes Claude Code only"
                )
            },
        )

    def test_the_merge_agent_takes_a_codex_fallback(self) -> None:
        self.assertEqual(
            project.seat_call("merger", "claude", "missing", CODEX)["took"]["seat"],
            "codex/gpt-6.2-sol:high",
        )


class FailedLine(Refuses):
    """The fixed line of a block a seat's error wrote, `the seat that failed: SEAT`,
    which `state` takes in that form only."""

    def test_the_line_of_each_seat_and_its_seat(self) -> None:
        for seat in ("reviewer", "planner", "merger"):
            project.fixed_form(f"the seat that failed: {seat}")
            self.assertEqual(
                project.failed_seat(
                    ["the reviewer gave an error", f"the seat that failed: {seat}"]
                ),
                seat,
            )
        self.assertIsNone(project.failed_seat(["the base is red"]))

    def test_another_seat_or_form_is_refused(self) -> None:
        for line in (
            "the seat that failed: experts",
            "the seat that failed:reviewer",
            "the seat that failed: the reviewer",
        ):
            with self.subTest(line=line):
                self.assertIn(
                    "`lem project seat-failed` writes it",
                    self.refused(project.fixed_form, line),
                )


class SeatCommands(Refuses):
    """`lem project seat`, `seat-failed` and `seat-again` over a task of a git
    repository of its own in a temporary folder, with a temporary XDG_CONFIG_HOME, so
    that no settings file and no state folder of this machine is read."""

    def setUp(self) -> None:
        self.kept = os.environ.get("XDG_CONFIG_HOME")
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        os.environ["XDG_CONFIG_HOME"] = str(Path(folder.name) / "home")
        self.addCleanup(self.home_back)

    def home_back(self) -> None:
        if self.kept is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.kept

    def repo(self, name: str, *seats: str) -> Path:
        """A repository NAME whose settings' [seats] hold SEATS, with the careful task
        `plan-talk` in its plan talk."""
        root = Path(os.environ["XDG_CONFIG_HOME"]).parent / name
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        (root / ".lem").mkdir()
        (root / project.SETTINGS).write_text(
            "\n".join(["[branch]", 'base = "main"', "[seats]", *seats]) + "\n",
            encoding="utf-8",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            project.cmd_task_dir(root, "plan-talk", "the export keeps its dates", None)
        project.cmd_state(
            root, "plan-talk", "building", ["the plan talk runs", "lead: session"]
        )
        return root

    def events(self, root: Path, *names: str) -> list[dict]:
        return [
            event
            for event in project.events_named(root, *names)
            if event.get("task") == "plan-talk"
        ]

    def test_a_codex_reviewer_with_no_tokens_takes_the_fallback_and_keeps_it(
        self,
    ) -> None:
        # criterion 3: mybaze names Codex as its reviewer, and its fallback is
        # Lem's default
        root = self.repo("mybaze", 'reviewer = "codex/gpt-6.2-sol:high"')
        self.assertEqual(
            project.cmd_seat(root, "plan-talk", "reviewer")["seat"],
            "codex/gpt-6.2-sol:high",
        )
        said = project.cmd_seat_failed(
            root,
            "plan-talk",
            "reviewer",
            "codex/gpt-6.2-sol:high",
            "tokens",
            "You have no tokens left",
        )
        self.assertEqual(
            (said["blocked"], said["seat"], said["from"], said["for"]),
            (False, "claude/opus:high", "stand-in", "codex/gpt-6.2-sol:high"),
        )
        self.assertEqual(
            said["say"],
            (
                "the reviewer `codex/gpt-6.2-sol:high` gave an error: "
                "no tokens; `claude/opus:high` stands in for it from now on, "
                "and the pull request says so"
            ),
        )
        [event] = self.events(root, "seat.stand-in")
        self.assertEqual(
            {key: event[key] for key in ("seat", "failed", "took", "error", "said")},
            {
                "seat": "reviewer",
                "failed": "codex/gpt-6.2-sol:high",
                "took": "claude/opus:high",
                "error": "tokens",
                "said": "You have no tokens left",
            },
        )
        # the task goes on: no block, and every later open of the reviewer takes
        # the stand-in
        self.assertEqual(project.read_tasks(root)[0]["status"], "building")
        now = project.cmd_seat(root, "plan-talk", "reviewer")
        self.assertEqual(
            (now["seat"], now["agent"], now["from"]),
            ("claude/opus:high", "claude", "stand-in"),
        )
        # the stand-in is the reviewer's alone
        self.assertEqual(
            project.cmd_seat(root, "plan-talk", "planner")["from"], "Lem's default"
        )

    def test_a_project_with_no_fallback_blocks_waits_for_the_owner_and_his_go_on_tries_the_seat_again(
        self,
    ) -> None:
        # criterion 5, its four steps
        root = self.repo(
            "billing-core", 'reviewer = "codex/gpt-6.2-sol:high"', "fallback = false"
        )
        said = project.cmd_seat_failed(
            root, "plan-talk", "reviewer", "codex/gpt-6.2-sol:high", "tokens", None
        )
        line = (
            "the reviewer `codex/gpt-6.2-sol:high` gave an error: no tokens, and this "
            "project permits no fallback"
        )
        self.assertEqual(
            (said["blocked"], said["status"], said["say"]), (True, "blocked", line)
        )
        task = project.read_tasks(root)[0]
        self.assertEqual(
            (
                task["status"],
                task["state"].splitlines()[0].split(" ", 2)[2],
                task["state"].splitlines()[1],
            ),
            ("blocked", line, "the seat that failed: reviewer"),
        )
        self.assertEqual(
            [event["failed"] for event in self.events(root, "seat.blocked")],
            ["codex/gpt-6.2-sol:high"],
        )
        # "Waits for you" shows it, with its first line
        from lem import board_model as bm

        model, _ = project.waiting_model(root, project.load(root))
        rows = bm.waits_of(model)
        self.assertEqual(
            [(row["kind"], row["t"].slug, row["t"].text) for row in rows],
            [("blocked", "plan-talk", line)],
        )
        # the afternoon: the owner's go on
        again = project.cmd_seat_again(root, "plan-talk")
        self.assertEqual(
            (again["status"], again["name"], again["seat"]),
            ("building", "reviewer", "codex/gpt-6.2-sol:high"),
        )
        task = project.read_tasks(root)[0]
        self.assertEqual(task["status"], "building")
        self.assertEqual(
            task["state"].splitlines()[0].split(" ", 2)[2],
            "the owner's go on: the reviewer codex/gpt-6.2-sol:high is tried again",
        )
        self.assertIn("lead: session", task["state"].splitlines())
        self.assertEqual(
            project.cmd_seat(root, "plan-talk", "reviewer")["seat"],
            "codex/gpt-6.2-sol:high",
        )
        self.assertIn(
            "has no line `the seat that failed: SEAT`",
            self.refused(project.cmd_seat_again, root, "plan-talk"),
        )

    def test_a_stand_in_that_fails_too_blocks_and_the_go_on_ends_the_stand_in(
        self,
    ) -> None:
        root = self.repo("mybaze", 'reviewer = "codex/gpt-6.2-sol:high"')
        project.cmd_seat_failed(
            root, "plan-talk", "reviewer", "codex/gpt-6.2-sol:high", "tokens", None
        )
        said = project.cmd_seat_failed(
            root, "plan-talk", "reviewer", "claude/opus:high", "login", None
        )
        self.assertEqual(
            said["say"],
            (
                "the reviewer `claude/opus:high` gave an error: no login, "
                "and it was the fallback"
            ),
        )
        self.assertEqual(project.read_tasks(root)[0]["status"], "blocked")
        project.cmd_seat_again(root, "plan-talk")
        self.assertEqual(
            project.cmd_seat(root, "plan-talk", "reviewer")["seat"],
            "codex/gpt-6.2-sol:high",
        )
        self.assertEqual(
            [event["seat"] for event in self.events(root, "seat.again")], ["reviewer"]
        )

    def test_a_planner_whose_fallback_is_codex_blocks(self) -> None:
        root = self.repo("notes-app", 'fallback = "codex/gpt-6.2-sol:high"')
        said = project.cmd_seat_failed(
            root, "plan-talk", "planner", "claude/opus:high", "tokens", None
        )
        self.assertTrue(said["blocked"])
        self.assertIn(
            "cannot sit in the planner's seat, which takes Claude Code only",
            said["say"],
        )
        self.assertEqual(
            project.read_tasks(root)[0]["state"].splitlines()[1],
            "the seat that failed: planner",
        )

    def test_the_experts_and_the_session_take_no_fallback(self) -> None:
        # criterion 8
        root = self.repo("notes-app")
        self.assertIn(
            "the other expert answers alone",
            self.refused(
                project.cmd_seat_failed,
                root,
                "plan-talk",
                "experts",
                "claude/fable:high",
                "tokens",
                None,
            ),
        )
        self.assertIn(
            "the session seat is the Claude session that runs the task",
            self.refused(
                project.cmd_seat_failed,
                root,
                "plan-talk",
                "session",
                "claude/opus:high",
                "tokens",
                None,
            ),
        )
        self.assertIn(
            "the experts are one or two that take no fallback seat",
            self.refused(project.cmd_seat, root, "plan-talk", "experts"),
        )
        self.assertEqual(self.events(root, *project.SEAT_EVENTS), [])

    def test_a_slow_agent_or_a_wrong_line_is_no_seat_that_failed(self) -> None:
        root = self.repo("notes-app")
        self.assertIn(
            "A slow agent is no error: wait for it",
            self.refused(
                project.cmd_seat_failed,
                root,
                "plan-talk",
                "reviewer",
                "claude/opus:high",
                "slow",
                None,
            ),
        )
        self.assertIn(
            "--seat = 'codex'",
            self.refused(
                project.cmd_seat_failed,
                root,
                "plan-talk",
                "reviewer",
                "codex",
                "tokens",
                None,
            ),
        )
        self.assertEqual(self.events(root, *project.SEAT_EVENTS), [])

    def test_the_events_and_open_over_a_block_are_the_commands_own(self) -> None:
        root = self.repo("billing-core", "fallback = false")
        self.assertIn(
            "written by `lem project seat-failed`",
            self.refused(
                project.cmd_log, root, "plan-talk", "seat.stand-in", ["seat=reviewer"]
            ),
        )
        project.cmd_seat_failed(
            root, "plan-talk", "merger", "claude/opus:high", "tokens", None
        )
        self.assertIn(
            "`lem project seat-again plan-talk` writes it",
            self.refused(
                project.cmd_state, root, "plan-talk", "open", ["pull request x"]
            ),
        )

    def test_the_owners_go_on_over_a_merge_agents_block_gives_open_with_its_pull_request(
        self,
    ) -> None:
        # criterion 5, the merge agent's seat: an open task, its merge agent with no
        # tokens and no fallback, then the go on
        root = self.repo(
            "billing-core", 'merger = "codex/gpt-6.2-sol:high"', "fallback = false"
        )
        url = "https://github.com/acme/billing-core/pull/85"
        project.cmd_state(
            root,
            "plan-talk",
            "open",
            [f"pull request {url}", "green: the checks and the review passed"],
        )
        said = project.cmd_seat_failed(
            root, "plan-talk", "merger", "codex/gpt-6.2-sol:high", "tokens", None
        )
        self.assertEqual(
            (said["blocked"], said["say"]),
            (
                True,
                (
                    "the merge agent `codex/gpt-6.2-sol:high` gave an error: "
                    "no tokens, and this project permits no fallback"
                ),
            ),
        )
        again = project.cmd_seat_again(root, "plan-talk")
        self.assertEqual(
            (again["status"], again["name"], again["seat"]),
            ("open", "merger", "codex/gpt-6.2-sol:high"),
        )
        task = project.read_tasks(root)[0]
        lines = task["state"].splitlines()
        self.assertEqual(
            (task["status"], lines[0].split(" ", 2)[2]),
            (
                "open",
                (
                    "the owner's go on: the merge agent codex/gpt-6.2-sol:high is "
                    "tried again"
                ),
            ),
        )
        self.assertEqual(
            lines[1:],
            [f"pull request {url}", "green: the checks and the review passed"],
        )
        self.assertEqual(
            [event["seat"] for event in self.events(root, "seat.again")], ["merger"]
        )

    def test_a_leads_state_never_comes_over_a_seats_block(self) -> None:
        # the defender's seat-failed wrote `blocked` before the lead's `building` of the
        # pair's open: that `building` would take the task out of "Waits for you",
        # seat-again would refuse it, and the lead's wait would loop
        root = self.repo(
            "billing-core", 'reviewer = "codex/gpt-6.2-sol:high"', "fallback = false"
        )
        project.cmd_seat_failed(
            root, "plan-talk", "reviewer", "codex/gpt-6.2-sol:high", "tokens", None
        )
        for status, lines in (
            (
                "building",
                ["the plan talk runs", "lead: session", "defender: opus, high"],
            ),
            ("held", ["one more fact"]),
            ("planned", ["the plan talk is done"]),
            ("ready", ["report written"]),
        ):
            with self.subTest(status=status):
                message = self.refused(
                    project.cmd_state, root, "plan-talk", status, lines
                )
                self.assertIn("the seat that failed: reviewer", message)
                self.assertIn("`lem project seat-again plan-talk`", message)
                self.assertEqual(project.read_tasks(root)[0]["status"], "blocked")
        # the owner's go on lifts it, and a second block of a seat may come over
        # the first
        self.assertEqual(
            project.cmd_seat_again(root, "plan-talk")["status"], "building"
        )
        project.cmd_seat_failed(
            root, "plan-talk", "reviewer", "codex/gpt-6.2-sol:high", "tokens", None
        )
        project.cmd_seat_failed(
            root, "plan-talk", "planner", "claude/opus:high", "login", None
        )
        self.assertEqual(project.read_tasks(root)[0]["status"], "blocked")
        # the owner's drop and park still come over it
        project.cmd_state(root, "plan-talk", "parked", ["the owner parked it"])
        self.assertEqual(project.read_tasks(root)[0]["status"], "parked")


if __name__ == "__main__":
    unittest.main()
