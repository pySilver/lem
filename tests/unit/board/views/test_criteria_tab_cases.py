"""The tab Criteria and decisions beyond the refund line: a breaker that waits and one the
owner parked, criteria held by their tests and criteria the checks took from the polish pass,
approved criteria the plan has not recorded, a change of the build the owner took over, a task
that ended with neither card, and a pruned task."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from fixtures.board.ended import INVOICE_TIP
from fixtures.board.moments import BASE, ago
from lem.board.inputs.parts import Link
from lem.board.inputs.task.decisions import Part
from lem.board.views import owed
from lem.board.views.criteria.tab import criteria
from lem.records.approvals import Approval
from lem.records.decisions import CriterionChanged
from lem.records.journal.task import Summary
from lem.records.landing.checks import CriterionCheck
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import Seen

GIFT = "gift-note-in-export"
INVOICE = "order-date-on-invoice"
SHORT = INVOICE_TIP[:7]


def with_task(seen: Seen, **changes: object) -> Seen:
    """The task of `seen` with other fields."""
    task = replace(seen.record.task, **changes)
    return replace(seen, record=replace(seen.record, task=task))


def test_a_breaker_that_waits_is_first_and_says_where_he_answers(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    tab = criteria(found, owed.seen(found, GIFT))
    assert tab.decisions_said == "1 breaker"
    row = tab.decisions[0]
    assert (row.kind, row.look, row.mark) == ("breaker", "you", "breaker")
    assert row.chose == "No option keeps the criteria you approved"
    assert row.who == "it waits for you · 15:40"
    files = [
        Link(
            href=f"{BASE}/tasks/{GIFT}/artifacts/{name}/",
            label=label,
            title=f"Open {name} on Artifacts",
            frame=True,
        )
        for name, label in (
            ("breaker-1.md", "the document"),
            ("handoff.md", "the handoff"),
        )
    ]
    assert row.parts[0] == Part(label="Now", text="It waits for you")
    assert row.parts[1] == Part(label="Its files", links=tuple(files))
    assert row.parts[2].label == "Where you answer"
    assert row.parts[2].text and row.parts[2].text.startswith("Read its document")


def test_a_parked_breaker_waits_for_nobody(tmp_path: Path) -> None:
    found = world(tmp_path)
    row = criteria(found, owed.seen(found, "fee-notice-to-merchants")).decisions[0]
    assert row.look == "quiet"
    assert row.chose == (
        "The next step cannot be undone by a later “no”: it sends something to a person"
    )
    assert row.parts[0].text == (
        "The task is parked: it waits for nobody until /lem resume fee-notice-to-merchants"
    )
    assert [part.label for part in row.parts] == ["Now", "Its files"]


def test_criteria_held_by_their_tests_say_the_commit_they_ran_on(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    tab = criteria(found, owed.seen(found, INVOICE))
    one = tab.criteria[0]
    assert (one.look, one.icon, one.label) == ("done", "check", "held by its tests")
    assert one.tests == (
        (
            "sh tests/order-date.sh",
            f"passes on the branch, fails on the base commit (checked on {SHORT})",
        ),
    )
    assert tab.reads[0].head == "Nobody confused"
    assert tab.reads[0].text == (
        "· read by 3 of 3 personas, two model families (opus, sol), run by Lem"
    )
    assert tab.reads[1].text == "after the personas’ read"
    assert tab.decisions_empty is None
    assert tab.decisions == ()


def test_a_taken_result_is_the_polish_pass_and_its_commit(tmp_path: Path) -> None:
    """`main`'s test_board_model.TakenFromPolish.test_a_taken_result_is_the_span_of_the_criterias_tests_with_the_pass_and_its_commit:
    where the tab draws the criteria's tests, a result the checks took from the polish pass
    names the pass and its commit."""
    found = world(tmp_path)
    seen = owed.seen(found, INVOICE)
    stated = replace(seen.record.task.criteria, red=None)
    landing = seen.record.landing
    assert landing and landing.checked
    taken = CriterionCheck(
        criterion=1, red_on_base=True, green_on_tip=True, taken_at=INVOICE_TIP
    )
    checked = replace(landing.checked, criteria=(taken,))
    polished = with_task(seen, criteria=stated)
    polished = replace(
        polished,
        record=replace(polished.record, landing=replace(landing, checked=checked)),
    )
    one = criteria(found, polished).criteria[0]
    assert one.tests == (
        (
            "sh tests/order-date.sh",
            (
                "passes on the branch, fails on the base commit, taken from the polish "
                f"pass at {SHORT}, not run again"
            ),
        ),
    )
    assert one.label == "held by its tests"


def test_a_run_of_the_tests_says_nothing_of_the_polish_pass(tmp_path: Path) -> None:
    """`main`'s test_board_model.TakenFromPolish.test_a_run_of_the_tests_says_nothing_of_the_polish_pass:
    the invoice's checks ran the criteria's tests themselves after its polish pass."""
    found = world(tmp_path)
    tab = criteria(found, owed.seen(found, INVOICE))
    assert not any("polish pass" in said for _, said in tab.criteria[0].tests)


def test_approved_criteria_the_plan_has_not_recorded_wait_for_their_tests(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    tab = criteria(found, owed.seen(found, GIFT))
    assert [one.note for one in tab.criteria] == [
        "no test yet: the agent adds its tests in the plan",
        "no test yet: the agent adds its tests in the plan",
    ]
    assert tab.criteria[1].text == (
        "An order with no gift note has an empty cell, not the word None."
    )
    assert [row.id for row in tab.reads] == ["crit-read", "crit-approved"]
    assert tab.reads[1].head == "Approved by you"


def test_a_change_of_the_build_is_his_once_he_approved_it(tmp_path: Path) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, GIFT)
    first = seen.record.task.criteria.approvals[0]
    change = CriterionChanged(
        id=2,
        at=ago(60),
        how="changed",
        criterion=2,
        why="the export's readers read an empty cell as no note",
        approval=1,
        was=first.criteria[1].text,
        now="An order with no gift note has an empty cell.",
        by="lead",
    )
    second = Approval(
        number=2,
        at=ago(50),
        by="owner",
        size="full",
        why=first.why,
        digest="0123456789ab",
        criteria=first.criteria,
        replaces=1,
    )
    stated = replace(seen.record.task.criteria, approvals=(first, second))
    changed = with_task(
        seen, decisions=(*seen.record.task.decisions, change), criteria=stated
    )
    tab = criteria(found, changed)
    row = tab.reads[-1]
    assert (row.id, row.look, row.icon) == ("crit-change-2", "done", "check")
    assert row.head == "Criterion 2 changed during the build"
    assert row.subs[1] == (
        "the export's readers read an empty cell as no note · by the agent · Approved by "
        "you afterwards (approval 2): it is yours, and no cause of not green"
    )
    assert tab.reads[1].subs == ("approval 2; it replaces approval 1",)


def test_a_task_that_ended_with_neither_card_says_so(tmp_path: Path) -> None:
    found = world(tmp_path)
    tab = criteria(found, owed.seen(found, "why-export-is-slow"))
    assert tab.ended == "The task ended with no criteria and no decision on record"
    assert tab.criteria_said is None
    assert tab.decisions_empty is None


def test_a_pruned_task_says_what_went_with_its_journal(tmp_path: Path) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, INVOICE)
    summary = Summary(
        at=ago(1),
        statuses=("building", "landed"),
        first=ago(330),
        last=ago(160),
        entries=40,
    )
    tab = criteria(
        found, replace(seen, record=replace(seen.record, journal=(summary,)))
    )
    assert tab.went and tab.went.id == "went-criteria"
    assert tab.went.said.startswith(
        "Its acceptance criteria, their approval, the personas’ read and its decisions "
        "went with its events"
    )
    assert tab.criteria == ()
