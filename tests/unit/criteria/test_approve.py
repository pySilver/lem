"""Who approves a task's criteria, and when: the owner's yes of the bytes his page showed, Lem's
in his name on the fast track, the lead's after a clear read, and one without him while the task
runs alone; each a new number, kept word for word with no test line."""

from datetime import date
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.app.criteria import approve, persona
from lem.kernel.errors import Refusal
from lem.model.criteria import digest, reads
from lem.records.questions import Answer, Question
from lem.records.task import Shape
from lem.store import places, tasks
from unit.criteria import world

if TYPE_CHECKING:
    from pathlib import Path

SMALL = approve.Asked(by="lem")


def owners(path: Path, shown: str | None = None) -> approve.Asked:
    return approve.Asked(by="owner", path=path, shown=shown)


def refused(checkout: Path, asked: approve.Asked) -> Refusal:
    with pytest.raises(Refusal) as caught:
        approve.approved(checkout, world.SLUG, asked)
    return caught.value


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    return world.workspace(tmp_path / "shop")


def test_the_bytes_the_page_showed_are_approved(checkout: Path) -> None:
    world.task(checkout, hold=world.WAITS)
    path = world.sheet(checkout, world.FULL)
    made = approve.approved(
        checkout, world.SLUG, owners(path, digest.shown(path.read_bytes()))
    )
    task = world.read(checkout).task
    assert (made.number, made.by, made.size) == (1, "owner", "full")
    assert task.criteria.approvals == (made,)
    assert task.hold is None
    assert [one.text for one in made.criteria][1].startswith(
        "An order with no gift note"
    )


def test_a_file_that_changed_after_the_page_is_not_approved(checkout: Path) -> None:
    world.task(checkout, hold=world.WAITS)
    path = world.sheet(checkout, world.FULL)
    shown = digest.shown(path.read_bytes())
    path.write_text(world.FULL.replace("1042", "1043"), encoding="utf-8")
    assert refused(checkout, owners(path, shown)).code == "shown-changed"
    assert world.read(checkout).task.criteria.approvals == ()


def test_each_approval_is_a_new_number_and_names_the_one_it_replaces(
    checkout: Path,
) -> None:
    world.task(checkout)
    path = world.sheet(checkout, world.FULL)
    approve.approved(checkout, world.SLUG, owners(path))
    second = approve.approved(checkout, world.SLUG, owners(path))
    assert (second.number, second.replaces) == (2, 1)


def test_the_criteria_he_approves_have_no_test_line(checkout: Path) -> None:
    world.task(checkout)
    path = world.sheet(checkout, world.FULL.replace("row.\n", "row.\n" + world.TESTED))
    assert refused(checkout, owners(path)).code == "test-lines"


def test_his_no_on_record_refuses_his_yes_and_an_approval_without_him(
    checkout: Path,
) -> None:
    said = Answer(option="no", label="No", source="board", at=world.EARLY)
    question = Question(
        id="criterion:gift-note:20260101T090000Z",
        topic="criterion",
        question="Approve the criteria?",
        options=("yes", "no"),
        asked=world.EARLY,
        answer=said,
    )
    world.task(
        checkout, hold=world.WAITS, questions=(question,), night=date(2026, 11, 24)
    )
    path = world.sheet(checkout, world.FULL)
    assert refused(checkout, owners(path)).code == "said-no"
    alone = approve.Asked(by="alone", path=path)
    assert refused(checkout, alone).code == "said-no"


def test_lem_approves_the_fast_track_in_his_name_as_the_first_contract_only(
    checkout: Path,
) -> None:
    world.task(checkout)
    world.sheet(checkout, world.SMALL)
    made = approve.approved(checkout, world.SLUG, SMALL)
    assert (made.by, made.size) == ("lem", "small")
    assert refused(checkout, SMALL).code == "approved"


def test_lem_approves_no_standard_track(checkout: Path) -> None:
    world.task(checkout)
    world.sheet(checkout, world.FULL)
    assert refused(checkout, SMALL).code == "not-small"


def test_a_request_someone_else_wrote_waits_for_his_yes_while_he_is_there(
    checkout: Path,
) -> None:
    shape = Shape(type="docs", why="a word", track="small", someone_else=True)
    world.task(checkout, shape=shape)
    path = world.sheet(checkout, world.SMALL)
    assert refused(checkout, SMALL).code == "not-his"
    assert refused(checkout, approve.Asked(by="alone", path=path)).code == "not-his"
    assert approve.approved(checkout, world.SLUG, owners(path)).by == "owner"


def test_a_request_someone_else_wrote_is_approved_without_him_while_he_is_away(
    checkout: Path,
) -> None:
    shape = Shape(type="docs", why="a word", track="small", someone_else=True)
    world.task(checkout, shape=shape)
    path = world.sheet(checkout, world.SMALL)
    world.away()
    assert refused(checkout, SMALL).code == "not-his"
    assert approve.approved(
        checkout, world.SLUG, approve.Asked(by="alone", path=path)
    ).by == ("alone")


def test_a_nights_task_is_approved_without_him_and_never_in_his_name(
    checkout: Path,
) -> None:
    world.task(checkout, night=date(2026, 11, 24))
    path = world.sheet(checkout, world.SMALL)
    assert "the night of 2026-11-24" in refused(checkout, SMALL).why
    assert approve.approved(
        checkout, world.SLUG, approve.Asked(by="alone", path=path)
    ).by == ("alone")


def test_his_own_request_is_approved_in_his_name_even_while_he_is_away(
    checkout: Path,
) -> None:
    world.task(checkout)
    path = world.sheet(checkout, world.SMALL)
    world.away()
    assert refused(checkout, approve.Asked(by="alone", path=path)).code == "his-request"
    assert approve.approved(checkout, world.SLUG, SMALL).by == "lem"


def test_an_approval_without_him_needs_a_task_that_runs_without_him(
    checkout: Path,
) -> None:
    world.task(checkout)
    path = world.sheet(checkout, world.FULL)
    assert refused(checkout, approve.Asked(by="alone", path=path)).code == "with-owner"


def test_the_full_approval_replaces_the_small_one_while_it_runs_alone(
    checkout: Path,
) -> None:
    world.task(checkout, night=date(2026, 11, 24))
    path = world.sheet(checkout, world.SMALL)
    approve.approved(checkout, world.SLUG, approve.Asked(by="alone", path=path))
    path.write_text(world.FULL, encoding="utf-8")
    grown = approve.approved(checkout, world.SLUG, approve.Asked(by="alone", path=path))
    assert (grown.number, grown.size, grown.replaces) == (2, "full", 1)
    assert refused(checkout, approve.Asked(by="alone", path=path)).code == "approved"


def test_with_the_owner_back_it_waits_for_his_yes(checkout: Path) -> None:
    world.task(checkout)
    path = world.sheet(checkout, world.FULL)
    world.away()
    world.away(gone=False)
    assert refused(checkout, approve.Asked(by="alone", path=path)).code == "with-owner"


def read_done(checkout: Path, answered: int, flagged: int = 0) -> None:
    sheet = world.plan(checkout, world.FULL.replace("row.\n", "row.\n" + world.TESTED))
    marked = digest.of_texts("full", approve.texts.sheet_at(sheet, "x").criteria)
    silent = () if answered else (reads.silent_of("Ania, opus: no answer"),) * 2
    found = reads.Found(
        asked=2,
        answered=answered,
        families=("opus",) if answered else (),
        silent=silent,
        criteria=2,
        flagged=flagged,
        digest=marked,
    )
    persona.noted(checkout, world.SLUG, ("done", "lead"), found)


def test_the_lead_freezes_the_plans_criteria_after_a_clear_read(checkout: Path) -> None:
    world.task(checkout, status="building")
    read_done(checkout, answered=2)
    made = approve.approved(checkout, world.SLUG, approve.Asked(by="read"))
    assert (made.by, made.criteria[0].tests) == ("read", ())
    assert world.read(checkout).task.criteria.criteria[0].tests


@pytest.mark.parametrize("first", ["read", "owner"])
def test_a_read_freezes_only_the_first_contract(checkout: Path, first: str) -> None:
    world.task(checkout, status="building")
    read_done(checkout, answered=2)
    if first == "read":
        approve.approved(checkout, world.SLUG, approve.Asked(by="read"))
    else:
        path = world.sheet(checkout, world.FULL)
        approve.approved(checkout, world.SLUG, owners(path))
    before = world.read(checkout).task.criteria.approvals
    request = approve.Asked(by="read")
    assert refused(checkout, request).code == "approved"
    changed = world.plan(checkout, world.FULL.replace("1042", "1043"))
    marked = digest.of_texts("full", approve.texts.sheet_at(changed, "x").criteria)
    persona.noted(
        checkout,
        world.SLUG,
        ("done", "lead"),
        reads.Found(
            asked=2,
            answered=2,
            families=("opus",),
            criteria=2,
            flagged=0,
            digest=marked,
        ),
    )
    assert refused(checkout, request).code == "criteria-differ"
    assert world.read(checkout).task.criteria.approvals == before


def test_a_read_nobody_answered_is_started_once_more_then_the_build_goes_on(
    checkout: Path,
) -> None:
    world.task(checkout, status="building")
    read_done(checkout, answered=0)
    assert refused(checkout, approve.Asked(by="read")).code == "unanswered"
    read_done(checkout, answered=0)
    assert approve.approved(checkout, world.SLUG, approve.Asked(by="read")).by == "read"


def test_a_doubt_or_a_read_of_other_criteria_waits_for_the_owner(
    checkout: Path,
) -> None:
    world.task(checkout, status="building")
    assert refused(checkout, approve.Asked(by="read")).code == "no-worktree"
    world.plan(checkout, world.FULL)
    assert refused(checkout, approve.Asked(by="read")).code == "not-read"
    read_done(checkout, answered=2, flagged=1)
    assert refused(checkout, approve.Asked(by="read")).code == "doubt"


def test_the_yes_waits_while_a_change_stopped_before_its_file(checkout: Path) -> None:
    question = Question(
        id="criterion:gift-note:20260101T090000Z",
        topic="criterion",
        question="Approve the criteria?",
        options=("yes", "no"),
        digest="0" * 16,
        asked=world.EARLY,
    )
    world.task(checkout, hold=world.WAITS, questions=(question,))
    path = world.sheet(checkout, world.FULL)
    assert refused(checkout, owners(path)).code == "changed-meanwhile"
    state = checkout / places.STATE
    record = tasks.read(state, world.SLUG)
    tasks.update(
        state,
        world.SLUG,
        lambda found: replace(found, task=replace(found.task, questions=())),
        record.revision,
    )
    assert approve.approved(checkout, world.SLUG, owners(path)).number == 1
