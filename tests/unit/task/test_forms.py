"""The typed records of a task's investigation and plan talk, in the one form the landing and
the board read (`InvestigationForm`, `TalkForm` and `TalkStartForm` of `main`): each rule refuses
with the words of the real command, and the record ends its stage's span."""

from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT, record
from lem.app.tasks import investigated, talked
from lem.kernel.errors import Refusal
from lem.model.task import investigation, spans, talk
from lem.model.task.investigation import Findings
from lem.model.task.span_forms import Given
from lem.records.holds import OwnerHold
from lem.records.work import Talk
from unit.task import spaces

if TYPE_CHECKING:
    from lem.records.record import Record

SLUG = "invoice-total"
LATER = MOMENT + timedelta(minutes=9)
FIX = Findings(
    kind="fix",
    call="full",
    line="the invoice total adds the refund as a payment",
    where="billing/invoice.py:total",
    reproduced=True,
)
QUESTION = Findings(
    kind="question", call="answer", line="the refund writes a credit note"
)
TALK = Talk(
    reviewer="codex",
    turns=6,
    questions=3,
    settled=2,
    open=1,
    repaired=2,
    design=1,
    unargued=0,
    root=1,
    layer=1,
    shared=1,
    at=MOMENT,
)
NO_QUESTION = replace(
    TALK,
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


def refused(given: Findings) -> str:
    """The why of the refusal of `given`."""
    with pytest.raises(Refusal) as caught:
        investigation.investigation(given, report=None, now=MOMENT)
    assert caught.value.code == "investigation"
    assert caught.value.why.startswith("lem task investigated SLUG --kind fix|question")
    return caught.value.why


def talk_refused(counts: Talk) -> str:
    """The why of the refusal of the talk `counts`."""
    with pytest.raises(Refusal) as caught:
        talk.talked(record(SLUG), talk=counts)
    assert caught.value.code == "talk"
    assert caught.value.why.startswith(
        "lem task talked SLUG --reviewer AGENT --turns N"
    )
    return caught.value.why


def test_a_fix_and_a_question_in_their_form() -> None:
    found = investigation.investigation(FIX, report="investigation.md", now=MOMENT)
    assert (found.kind, found.call, found.where, found.reproduced, found.report) == (
        "fix",
        "full",
        "billing/invoice.py:total",
        True,
        "investigation.md",
    )
    answered = investigation.investigation(QUESTION, report=None, now=MOMENT)
    assert (answered.call, answered.reproduced, answered.at) == ("answer", None, MOMENT)


def test_a_bug_that_is_none_or_unreproduced_needs_no_place() -> None:
    for call in ("not-a-bug", "not-reproduced"):
        given = replace(FIX, call=call, where=None, reproduced=False)
        assert investigation.investigation(given, report=None, now=MOMENT).where is None


def test_a_call_the_kind_does_not_have() -> None:
    assert (
        "call is small, full, not-a-bug or not-reproduced for a fix, and answer for a "
        "question; this one is 'answer' for a fix"
    ) in refused(replace(FIX, call="answer"))
    assert "this one is 'full' for a question" in refused(
        replace(QUESTION, call="full")
    )


def test_a_line_that_is_not_one_line() -> None:
    for line in ("", "  ", "the cause\nand more"):
        assert "line is one line of text" in refused(replace(FIX, line=line)), line


def test_an_empty_place() -> None:
    assert "where is the cause's file and symbol, as PATH:SYMBOL" in refused(
        replace(FIX, where=" ")
    )


def test_a_question_reproduces_nothing() -> None:
    assert "reproduced is a fix's" in refused(replace(QUESTION, reproduced=True))


def test_a_fix_says_whether_the_bug_was_reproduced() -> None:
    assert "with --reproduced or --not-reproduced" in refused(
        replace(FIX, reproduced=None)
    )


def test_a_plain_cause_has_a_place() -> None:
    assert "a plain cause has a place: where names the cause's file and symbol" in (
        refused(replace(FIX, call="small", where=None))
    )


def test_not_reproduced_that_says_it_was() -> None:
    assert (
        "not-reproduced is a bug that was not reproduced, and this record says it was"
    ) in refused(replace(FIX, call="not-reproduced"))


def started(name: str, **fields: str) -> Record:
    """A building task with the span `name` open."""
    given = Given(name=name, edge="start", job=fields.get("job"), by=fields.get("by"))
    return spans.marked(record(SLUG, status="building"), given=given, now=MOMENT)


def test_the_record_ends_the_investigations_span_and_an_unreproduced_bug_waits() -> (
    None
):
    found = investigation.investigation(FIX, report=None, now=LATER)
    written = investigation.investigated(
        started("investigation", job="fix"), found=found, now=LATER
    )
    assert written.task.investigation == found
    assert written.task.spans[0].end == LATER
    assert written.task.hold is None
    unreproduced = replace(FIX, call="not-reproduced", where=None, reproduced=False)
    held = investigation.investigated(
        record(SLUG, status="building"),
        found=investigation.investigation(unreproduced, report=None, now=LATER),
        now=LATER,
    )
    assert held.task.hold == OwnerHold(
        on="fact", line="the investigation waits for one more fact", since=LATER
    )


def test_the_command_writes_the_findings_with_the_report(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="building")
    folder = where.state / "tasks" / SLUG
    (folder / "investigation.md").write_text("# The cause\n", encoding="utf-8")
    written = investigated.investigated(where.state, SLUG, FIX)
    assert written.report == "investigation.md"
    assert spaces.read(where, SLUG).task.investigation == written
    ran = lem(
        *("task", "investigated", SLUG, "--kind", "question", "--call", "answer"),
        *("--line", "a credit note", "--reproduced"),
        cwd=where.checkout,
    )
    assert ran.code == 2
    assert "a question reproduces nothing" in ran.stderr
    typed = lem(
        *("task", "investigated", SLUG, "--kind", "fix", "--call", "maybe"),
        *("--line", "x"),
        cwd=where.checkout,
    )
    assert typed.code == 2


def test_the_investigator_keeps_the_root_cause_method() -> None:
    root = Path(__file__).resolve().parents[3]
    brief = (root / "skills/lem/prompts/investigator.md").read_text(encoding="utf-8")
    assert "**Find the cause** with the method of the `lem-root-cause` skill" in brief
    assert (root / "skills/lem-root-cause/SKILL.md").is_file()


def test_a_talk_in_its_form_and_a_talk_of_no_question() -> None:
    assert talk.refusal(TALK) is None
    assert talk.refusal(NO_QUESTION) is None


def test_what_breaks_a_rule_of_the_talk_and_not_a_count_is_taken() -> None:
    # more decisions two questions named than design choices, and more turns than its bound
    over = replace(
        TALK,
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
    for counts in (
        replace(TALK, shared=2),
        over,
        replace(NO_QUESTION, turns=3, unargued=1),
    ):
        assert talk.refusal(counts) is None
    assert talk.bound(over) == 10
    assert over.turns > talk.bound(over)


def test_a_blank_reviewer() -> None:
    assert "reviewer names the agent that argued the plan with its defender" in (
        talk_refused(replace(TALK, reviewer=" "))
    )


def test_a_count_below_zero() -> None:
    for changes in ({"layer": -1}, {"shared": -1}, {"turns": -6}):
        assert "each N is a whole number, 0 or more" in talk_refused(
            replace(TALK, **changes)
        )


def test_fewer_than_two_turns() -> None:
    assert "a talk has two turns at the least" in talk_refused(
        replace(NO_QUESTION, turns=1)
    )


def test_a_talk_of_no_question_and_two_turns_with_a_question_raised_after_the_list() -> (
    None
):
    assert (
        "a talk of no question and two turns has no turn after the list, so unargued is 0"
    ) in talk_refused(replace(NO_QUESTION, unargued=1))


def test_settled_and_open_that_do_not_add_up_to_questions() -> None:
    assert "settled and open add up to questions" in talk_refused(
        replace(TALK, settled=1)
    )


def test_more_design_choices_than_open_questions() -> None:
    assert "design is at most open" in talk_refused(replace(TALK, design=2))


def test_more_repairs_than_questions() -> None:
    counts = replace(TALK, settled=3, open=0, design=0, repaired=4, root=0, layer=0)
    assert "repaired is at most questions" in talk_refused(counts)


def test_more_repairs_at_the_cause_and_layers_than_repairs() -> None:
    counts = replace(TALK, layer=2, shared=0)
    assert "root and layer add up to at most repaired" in talk_refused(counts)


def test_the_talks_start_names_its_reviewer_and_its_record_ends_it() -> None:
    begun = started("plan-talk", by="codex")
    assert begun.task.spans[0].by == "codex"
    written = talk.talked(begun, talk=replace(TALK, at=LATER))
    assert written.task.talk == replace(TALK, at=LATER)
    assert written.task.spans[0].end == LATER
    for fields in ({}, {"job": "fix"}, {"by": " "}):
        with pytest.raises(Refusal) as caught:
            started("plan-talk", **fields)
        assert (
            "the span plan-talk takes --by AGENT, the reviewer, and nothing else"
            in (caught.value.why)
        )


def test_the_command_writes_the_talk_with_its_bound(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="planned")
    written = talked.talked(where.state, SLUG, TALK)
    assert (written.bound, written.talk.reviewer) == (14, "codex")
    assert spaces.read(where, SLUG).task.talk == written.talk
    counts = ("--turns", "five", "--questions", "0", "--settled", "0", "--open", "0")
    rest = ("--repaired", "0", "--design", "0", "--unargued", "0", "--root", "0")
    ran = lem(
        *("task", "talked", SLUG, "--reviewer", "codex", *counts, *rest),
        *("--layer", "0", "--shared", "0"),
        cwd=where.checkout,
    )
    assert ran.code == 2
    assert "'five' is not a valid integer" in ran.stderr
