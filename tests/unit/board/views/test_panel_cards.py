"""The cards of a task's Overview that the refund line does not show (`main`'s
`board_task.breaker_card`, `parked_card`, `answered_card` and `cards_card`): a breaker that waits,
a park, the owner's answer on record, and the cards of the task's session."""

import dataclasses
from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.records import record as task_record
from fixtures.board.moments import ago
from lem.board.inputs.forms import Typed
from lem.board.inputs.layout import Viewer
from lem.board.views import owed
from lem.board.views.panel.building import building
from lem.board.views.panel.important import important
from lem.board.views.panel.panel import panel
from lem.board.views.panel.phases import phases
from lem.board.views.panel.told import outcome
from lem.records.decisions import Breaker, Taken
from lem.records.journal.task import SpanMark, StateNoted
from lem.records.questions import Answer
from lem.records.task import Shape
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.task.overview import Overview
    from lem.board.views.world import World
    from lem.records.record import Record

GIFT = "gift-note-in-export"
FEE = "fee-notice-to-merchants"


def overview_of(afternoon: World, slug: str) -> Overview:
    """The Overview of task `slug` of `afternoon`."""
    found = panel(afternoon, slug, "overview").overview
    assert found is not None
    return found


def test_the_large_card_shows_the_first_line_until_a_later_state(
    tmp_path: Path,
) -> None:
    base = world(tmp_path)
    seen = owed.seen(base, GIFT)
    line = 'fix: "the footer says Terms and conditions". Fast track: one builder.'
    shape = Shape(
        type="fix", why="one typo", track="small", then="fast", first_line=line
    )
    shaped = task_record(GIFT, status="building", shape=shape)
    start = StateNoted(at=ago(5), status="building", line="one builder")
    builder = SpanMark(at=ago(4), name="small", edge="start")
    later = StateNoted(at=ago(3), status="ready", line="the report is written")

    def shown(record: Record) -> str | None:
        given = msgspec.structs.replace(seen, record=record)
        return overview_of(dataclasses.replace(base, tasks=(given,)), GIFT).now.opening

    assert shown(msgspec.structs.replace(shaped, journal=(start, builder))) == line
    ready = msgspec.structs.replace(shaped.task, status="ready")
    assert (
        shown(msgspec.structs.replace(shaped, task=ready, journal=(start, later)))
        is None
    )
    assert shown(task_record(GIFT, status="building")) is None


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        ("## Request\nFix the sheet.\n", ""),
        ("## Outcome\n\n## Done when\n- The total appears.\n", ""),
        ("## Outcome\nOne line\nand its end.\n", "One line and its end."),
        (
            (
                "## Outcome\nThe total stays\nin the export.\n\n"
                "### Example\n\nThe total is 12.\n\n## Done when\nIgnore this."
            ),
            "The total stays in the export.\n\n### Example\n\nThe total is 12.",
        ),
    ],
    ids=["missing", "empty", "last", "subheading"],
)
def test_the_overview_reads_only_the_outcome_section(text: str, shown: str) -> None:
    assert outcome(text) == shown


def test_a_task_without_a_worktree_can_show_its_outcome_without_filed_items(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, GIFT)
    text = "The totals stay with the export."
    no_tree = msgspec.structs.replace(
        seen, filed=None, prose=(("task.md", f"## Outcome\n{text}"),)
    )
    card = building(found, no_tree)
    assert card and card.outcome and card.outcome.text == text
    assert card.filed is None and card.on_branch == ()


def test_phase_progress_follows_the_work_even_with_a_decision_past_the_personas(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, "refund-line-on-receipt")
    record = seen.record
    assert record.landing and record.landing.reviews
    decision = Taken(
        id=100,
        at=ago(5),
        what="Where to put the note?",
        chose="the export",
        why="Its readers use the export",
        by="dialectic",
    )
    change = msgspec.structs.replace(
        record.task, status="landing", decisions=(decision,)
    )
    shown = phases(msgspec.structs.replace(record, task=change))
    assert [phase.name for phase in shown if phase.past] == [
        "Criteria",
        "Plan",
        "Build",
        "Checks",
    ]
    assert [phase.name for phase in shown if phase.current] == ["Review"]


def test_the_board_marks_the_important_decisions_but_not_the_breaker(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    record = owed.seen(found, "refund-line-on-receipt").record
    landing = record.landing
    assert landing and landing.proposed
    base = Taken(
        id=1, at=ago(5), what="Where?", chose="the export", why="the rule", by="lead"
    )
    change = msgspec.structs.replace
    decisions = (
        change(base, id=1, by="dialectic"),
        change(base, id=2, unsettled=True),
        change(base, id=3, by="owner", breaker=6),
        change(base, id=4),
        change(base, id=5),
        Breaker(
            id=6,
            at=ago(10),
            cause="criteria",
            what="no option keeps the criterion",
            document="breaker-6.md",
            handoff="handoff.md",
        ),
    )
    proposed = change(landing.proposed, reasons=("decision 4 needs a look",))
    given = change(
        record,
        task=change(record.task, decisions=decisions),
        landing=change(landing, proposed=proposed),
    )
    assert [one.id for one in important(given)] == [1, 2, 3, 4]


def test_an_ended_tasks_outcome_omits_an_empty_list_of_filed_items(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, GIFT)
    card_input = msgspec.structs.replace(seen, filed=())
    active = building(found, card_input)
    assert active and active.filed and "no backlog item filed" in active.filed
    ended = msgspec.structs.replace(seen.record.task, status="landed")
    closed = msgspec.structs.replace(
        card_input, record=msgspec.structs.replace(seen.record, task=ended)
    )
    card = building(found, closed)
    assert card is not None and card.filed is None and card.on_branch == ()


def test_a_breaker_that_waits_is_the_first_card_with_its_document_and_the_owners_answer(
    tmp_path: Path,
) -> None:
    found = overview_of(world(tmp_path), GIFT).breaker
    assert found is not None
    assert (found.waits, found.head) == (True, "The build stopped · breaker 1")
    assert found.why == "No option keeps the criteria you approved"
    assert found.at.shown == "20m"
    assert found.document is not None
    assert found.document.text.startswith("# The gift note has no place")
    assert found.missing is None
    assert found.artifact.href.endswith("/artifacts/breaker-1.md/")
    assert found.handoff is not None
    assert found.handoff.label == "the handoff"
    assert found.where == "help, park or drop it here, or help in the task’s session."
    assert found.answer is not None
    assert [one.option for one in found.answer.choices] == ["help", "park", "drop"]
    typed = found.ways[-1].typed
    assert typed == (
        Typed(command=f"/lem park {GIFT}", does="puts the task aside"),
        Typed(command=f"/lem drop {GIFT}", does="ends it"),
    )


def test_the_large_card_of_a_breaker_sends_the_owner_to_its_document(
    tmp_path: Path,
) -> None:
    found = overview_of(world(tmp_path), GIFT).now
    assert found.head == "The build stopped: its breaker waits for you"
    assert found.breaker == (
        "Its document is the first card above: read it, then help, park or drop the task."
    )
    assert (found.ways, found.answer, found.where, found.shown) == (
        (),
        None,
        None,
        None,
    )


def test_a_parked_task_says_since_when_why_and_how_it_comes_back(
    tmp_path: Path,
) -> None:
    found = overview_of(world(tmp_path), FEE)
    assert found.parked is not None
    assert found.parked.since == "12:50"
    assert found.parked.why == (
        "The owner parked it: wait for the merchants' association to confirm the fee date"
    )
    assert found.parked.resume == f"/lem resume {FEE}"
    assert found.breaker is not None
    assert not found.breaker.waits
    assert found.breaker.where == (
        "The task is parked: this breaker waits for nobody until you bring it back."
    )
    assert found.breaker.answer is None
    assert (found.now.who, found.now.head) == (
        "Nobody acts",
        "Parked: nobody works on it until you bring it back",
    )
    assert found.now.ways[-1].typed[0].command == f"/lem resume {FEE}"


def test_the_owners_answer_on_record_shows_until_the_session_takes_it(
    tmp_path: Path,
) -> None:
    afternoon = world(tmp_path)
    seen = owed.seen(afternoon, GIFT)
    task = seen.record.task
    asked = task.questions[0]
    picked = Answer(
        option="drop",
        label="Drop",
        note="the export changes next week",
        source="board",
        device="phone",
        at=ago(5),
    )
    questions = (msgspec.structs.replace(asked, answer=picked),)
    record = msgspec.structs.replace(
        seen.record, task=msgspec.structs.replace(task, questions=questions)
    )
    changed = msgspec.structs.replace(seen, record=record)
    tasks = tuple(changed if one is seen else one for one in afternoon.tasks)
    found = overview_of(dataclasses.replace(afternoon, tasks=tasks), GIFT)
    assert found.answered is not None
    assert (
        found.answered.took == "You picked Drop for breaker 1 at 15:55, from the phone."
    )
    assert found.answered.note == "the export changes next week"
    assert found.now.head == "Helped: its lead has not started yet"


def test_each_card_of_the_tasks_session_waits_with_its_way_to_answer(
    tmp_path: Path,
) -> None:
    found = overview_of(world(tmp_path), "refund-rounding")
    assert found.cards_said == "1 card waits for your answer"
    (card,) = found.cards
    assert card.prompt == "Round each line of a refund, or only its total?"
    assert card.link is not None
    assert card.link.href.endswith(
        "/tasks/refund-rounding/card/4F9A1C2E-7B3D-4E8F-A1B2-C3D4E5F60718"
    )
    assert card.since.shown == "50m"


def test_a_page_that_may_not_act_offers_no_answer_and_no_way_to_a_card(
    tmp_path: Path,
) -> None:
    afternoon = world(tmp_path)
    viewer = Viewer(host="studio", workspace="shop", base=afternoon.viewer.base)
    looking = dataclasses.replace(afternoon, viewer=viewer)
    assert overview_of(looking, "refund-rounding").cards[0].link is None
    breaker = overview_of(looking, GIFT).breaker
    assert breaker is not None
    assert breaker.answer is None
    assert breaker.where == "help in the task’s session."
