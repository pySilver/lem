"""The cases of the review of the step: what a read must say to count, silence that proves
nothing, the lead's freeze of what `record` refuses, an approval of a question that is no longer
the wait's, a fast-track approval in the second its task grew, two changes at once, the mark the
landing compares after a new approval, and the words of a call that refuses."""

import dataclasses
from datetime import date
from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from fakes.command import lem
from lem.app.criteria import approve, change, persona, typed
from lem.app.decisions import criterion
from lem.app.landing import pr_tests
from lem.kernel.errors import Refusal
from lem.model.criteria import contract, digest, reads, waits
from lem.model.decisions.criterion import Asked
from lem.model.landing import green
from lem.records.work import Span
from lem.store import places, tasks
from unit.criteria import world
from unit.landing import proposals

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

PLANNED = world.FULL.replace("row.\n", "row.\n" + world.TESTED)
FOUND = reads.Found(
    asked=3, answered=2, families=("opus",), criteria=2, flagged=0, digest="a" * 12
)
NOTE = "criterion 2 must also cover empty rows"
CHANGED = world.FULL.replace('the word "None".', 'the word "None", nor "null".')


def refused(call: Callable[..., object], *args: object) -> Refusal:
    with pytest.raises(Refusal) as caught:
        call(*args)
    return caught.value


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    found = world.workspace(tmp_path / "shop")
    world.task(found, status="building")
    return found


@pytest.mark.parametrize(
    "wrong",
    [
        msgspec.structs.replace(FOUND, families=("opus", " ")),
        msgspec.structs.replace(FOUND, silent=()),
        msgspec.structs.replace(FOUND, asked=1, answered=1, silent=()),
        msgspec.structs.replace(FOUND, answered=4),
        msgspec.structs.replace(FOUND, answered=0),
        msgspec.structs.replace(
            FOUND, asked=4, silent=(reads.silent_of("Ania, opus: no answer"),)
        ),
        msgspec.structs.replace(FOUND, silent=(reads.silent_of("Ania, : no answer"),)),
        msgspec.structs.replace(FOUND, criteria=0, flagged=0),
        msgspec.structs.replace(FOUND, flagged=3),
        msgspec.structs.replace(FOUND, split=True),
    ],
    ids=[
        "blank family",
        "no silent",
        "one asked",
        "too many answered",
        "nobody answered with a family",
        "too few silent",
        "missing source family",
        "no criterion",
        "more flags",
        "split of one",
    ],
)
def test_a_read_of_another_form_is_refused(checkout: Path, wrong: reads.Found) -> None:
    before = world.read(checkout)
    code = refused(persona.noted, checkout, world.SLUG, ("done", "lead"), wrong).code
    assert code == "criteria-read"
    assert world.read(checkout) == before


@pytest.mark.parametrize(
    ("asked", "answered", "families", "sources", "accepted"),
    [
        (2, 2, ("opus",), ("Ania, sol",), True),
        (2, 0, (), ("Ania, opus", "Ania, sol", "Bea, opus", "Bea, sol"), True),
        (3, 1, ("opus",), ("Ania, sol", "Ania, sol"), False),
        (3, 1, ("opus",), ("Ania, opus", "Ania, Opus", "Bea, opus"), False),
        (2, 0, (), ("Ania, Opus", "Ania, Sol", "Bea, opus"), True),
    ],
    ids=[
        "partial",
        "wholly-silent",
        "duplicate",
        "same-family-case",
        "different-seats",
    ],
)
def test_a_panel_read_counts_distinct_personas_and_sources(
    checkout: Path,
    asked: int,
    answered: int,
    families: tuple[str, ...],
    sources: tuple[str, ...],
    *,
    accepted: bool,
) -> None:
    ran = lem(
        "criteria",
        "read",
        world.SLUG,
        "done",
        "--by",
        "lead",
        "--asked",
        str(asked),
        "--answered",
        str(answered),
        "--criteria",
        "2",
        "--flagged",
        "0",
        "--digest",
        "a" * 12,
        *(word for family in families for word in ("--family", family)),
        *(word for source in sources for word in ("--silent", f"{source}: no answer")),
        cwd=checkout,
    )
    assert ran.code == (0 if accepted else 1), ran.stdout
    recorded = world.read(checkout).task.criteria.reads
    if accepted:
        assert tuple(one.name for one in recorded[-1].silent) == sources
    else:
        assert recorded == ()
        refusal = ran.envelope()["refusal"]
        assert isinstance(refusal, dict) and refusal["code"] == "criteria-read"


def test_one_family_in_two_cases_is_one_family_and_no_split(checkout: Path) -> None:
    ran = lem(
        "criteria",
        "read",
        world.SLUG,
        "done",
        "--by",
        "lead",
        "--asked",
        "2",
        "--answered",
        "2",
        "--criteria",
        "1",
        "--flagged",
        "0",
        "--digest",
        "a" * 12,
        "--family",
        "opus",
        "--family",
        "Opus",
        "--split",
        cwd=checkout,
    )
    refusal = ran.envelope()["refusal"]
    assert isinstance(refusal, dict), ran.stdout
    assert refusal["code"] == "criteria-read"
    assert world.read(checkout).task.criteria.reads == ()


def unanswered(checkout: Path, marked: str) -> None:
    silent = tuple(
        reads.silent_of(f"{name}, opus: no answer") for name in ("Ania", "Bea")
    )
    found = reads.Found(
        asked=2, answered=0, silent=silent, criteria=2, flagged=0, digest=marked
    )
    persona.noted(checkout, world.SLUG, ("done", "lead"), found)


def plan_mark(checkout: Path) -> str:
    path = world.plan(checkout, PLANNED)
    sheet = approve.texts.sheet_at(path, "x")
    return digest.of_texts(sheet.size, sheet.criteria)


def test_silence_and_a_read_of_other_criteria_prove_no_second_unanswered_read(
    checkout: Path,
) -> None:
    marked = plan_mark(checkout)
    read = approve.Asked(by="read")
    persona.noted(checkout, world.SLUG, ("silent", "lead"), None)
    persona.noted(checkout, world.SLUG, ("silent", "lead"), None)
    assert refused(approve.approved, checkout, world.SLUG, read).code == "not-read"
    unanswered(checkout, marked)
    assert refused(approve.approved, checkout, world.SLUG, read).code == "unanswered"


def test_an_unanswered_read_of_other_criteria_is_no_first_one(checkout: Path) -> None:
    marked = plan_mark(checkout)
    unanswered(checkout, "b" * 12)
    unanswered(checkout, marked)
    read = approve.Asked(by="read")
    assert refused(approve.approved, checkout, world.SLUG, read).code == "unanswered"
    unanswered(checkout, marked)
    assert approve.approved(checkout, world.SLUG, read).by == "read"


def test_the_lead_freezes_no_small_plan_and_no_unapproved_fast_track(
    checkout: Path,
) -> None:
    world.plan(checkout, world.SMALL)
    read = approve.Asked(by="read")
    assert refused(approve.approved, checkout, world.SLUG, read).code == "small-plan"
    plan = world.worktree(checkout) / "docs" / "plans" / "2026-11-25-gift-note.md"
    plan.unlink()
    world.sheet(checkout, world.SMALL)
    assert refused(approve.approved, checkout, world.SLUG, read).code == "unapproved"


def test_a_clear_lead_read_freezes_the_plan_and_is_reported_without_a_wait(
    checkout: Path,
) -> None:
    mark = plan_mark(checkout)
    read = replace(FOUND, asked=2, digest=mark)
    for invalid in (
        replace(read, asked=1, answered=1),
        replace(read, answered=0),
        replace(read, answered=3),
        replace(read, asked=3),
    ):
        assert (
            refused(persona.noted, checkout, world.SLUG, ("done", "lead"), invalid).code
            == "criteria-read"
        )
    incomplete = lem(
        "criteria", "read", world.SLUG, "done", "--by", "lead", cwd=checkout
    )
    assert incomplete.code == 2
    assert world.read(checkout).task.criteria.reads == ()

    persona.noted(checkout, world.SLUG, ("done", "lead"), read)
    assert len(world.read(checkout).task.criteria.reads) == 1
    other = world.sheet(checkout, CHANGED)
    assert (
        lem(
            "criteria",
            "approve",
            world.SLUG,
            "--read",
            "--file",
            str(other),
            cwd=checkout,
        ).code
        == 2
    )
    frozen = approve.approved(checkout, world.SLUG, approve.Asked(by="read"))
    assert (frozen.by, frozen.digest) == ("read", mark)
    edit = Asked(
        how="changed",
        number=2,
        was="Not the criterion.",
        now="The cell stays empty.",
        why="Say it directly",
        by="lead",
    )
    before = world.read(checkout)
    assert (
        "after every earlier change"
        in refused(criterion.recorded, checkout, world.SLUG, edit).why
    )
    record = world.read(checkout)
    assert record == before
    assert green.reasons(replace(record, landing=proposals.full().landing), ()) == ()
    scout = Span(name="scout", start=world.EARLY, end=world.EARLY)
    rendered = pr_tests.first(
        replace(record, task=replace(record.task, spans=(scout,)))
    )
    assert (
        "- the criteria were read by 2 of 2 personas asked, one model family (opus); nobody confused; the build started with no wait for the owner"
        in rendered
    )
    assert "the change was not read" not in "\n".join(rendered)
    assert pr_tests.SCOUT in rendered
    assert str(checkout) not in "\n".join(rendered)


def test_a_page_of_an_older_question_approves_nothing_and_a_yes_answers_the_wait(
    tmp_path: Path,
) -> None:
    checkout = world.workspace(tmp_path / "page")
    world.task(checkout, hold=world.WAITS)
    sheet = world.sheet(checkout, world.FULL)
    typed.typed(checkout, world.SLUG, "why two columns?")
    first = waits.question_of(world.read(checkout).task)
    assert first is not None
    again = typed.unchanged(checkout, world.SLUG)
    old = approve.Asked(by="owner", path=sheet, shown=again.shown, question=first.id)
    assert refused(approve.approved, checkout, world.SLUG, old).code == "other-question"
    new = dataclasses.replace(old, question=again.question)
    approve.approved(checkout, world.SLUG, new)
    task = world.read(checkout).task
    said = task.questions[-1].answer
    assert said is not None
    assert (task.questions[-1].id, said.option) == (again.question, "yes")


def test_a_fast_track_approval_in_the_second_its_task_grew_answers_no_wait(
    tmp_path: Path,
) -> None:
    grown = world.workspace(tmp_path / "grown")
    world.task(grown, night=date(2026, 11, 24))
    path = world.sheet(grown, world.SMALL)
    made = approve.approved(grown, world.SLUG, approve.Asked(by="alone", path=path))
    world.sheet(grown, world.FULL)
    state = grown / places.STATE
    record = tasks.read(state, world.SLUG)
    hold = replace(world.WAITS, since=made.at)
    tasks.update(
        state,
        world.SLUG,
        lambda found: replace(found, task=replace(found.task, hold=hold)),
        record.revision,
    )
    assert typed.typed(grown, world.SLUG, NOTE).recorded


def test_a_second_change_waits_for_the_first_ones_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = world.workspace(tmp_path / "two")
    world.task(checkout, hold=world.WAITS)
    world.sheet(checkout, world.FULL)
    typed.typed(checkout, world.SLUG, NOTE)

    class Cut:
        @staticmethod
        def write_whole(path: Path, body: bytes) -> None:
            raise OSError(path, body)

    monkeypatch.setattr(change, "files", Cut)
    to_b = checkout / "b.md"
    to_b.write_text(CHANGED, encoding="utf-8")
    with pytest.raises(OSError):
        change.changed(checkout, world.SLUG, to_b, NOTE)
    monkeypatch.undo()
    to_c = checkout / "c.md"
    to_c.write_text(CHANGED.replace("1042", "1043"), encoding="utf-8")
    assert refused(change.changed, checkout, world.SLUG, to_c, "c").code == (
        "changed-meanwhile"
    )


def test_the_contract_moves_with_another_approval_and_a_recorded_change(
    checkout: Path,
) -> None:
    path = world.sheet(checkout, world.FULL)
    approve.approved(checkout, world.SLUG, approve.Asked(by="owner", path=path))
    first = contract.mark(world.read(checkout).task)
    assert first is not None
    assert contract.moved(world.read(checkout).task, first) is None
    approve.approved(checkout, world.SLUG, approve.Asked(by="owner", path=path))
    assert contract.moved(world.read(checkout).task, first) is None
    world.sheet(checkout, CHANGED)
    approve.approved(checkout, world.SLUG, approve.Asked(by="owner", path=path))
    moved = contract.moved(world.read(checkout).task, first)
    assert moved is not None
    assert moved.code == "contract-moved"


def test_alone_takes_no_shown_and_the_help_of_show_gives_the_form(
    tmp_path: Path,
) -> None:
    checkout = world.workspace(tmp_path / "cli")
    world.task(checkout)
    ran = lem(
        "criteria",
        "approve",
        world.SLUG,
        "--file",
        "x",
        "--alone",
        "--shown",
        "d",
        cwd=checkout,
    )
    assert ran.code == 2
    shown = lem("criteria", "show", "--help", cwd=checkout)
    assert "## Acceptance criteria" in shown.stdout
    assert "Size: full, because" in shown.stdout
    assert "- test: `" in shown.stdout


def test_a_change_first_refuses_a_yes_to_the_text_before_it(tmp_path: Path) -> None:
    checkout = world.workspace(tmp_path / "before")
    world.task(checkout, hold=world.WAITS)
    sheet = world.sheet(checkout, world.FULL)
    before = digest.shown(sheet.read_bytes())
    typed.typed(checkout, world.SLUG, NOTE)
    to_b = checkout / "b.md"
    to_b.write_text(CHANGED, encoding="utf-8")
    change.changed(checkout, world.SLUG, to_b, NOTE)
    old = approve.Asked(by="owner", path=sheet, shown=before)
    assert refused(approve.approved, checkout, world.SLUG, old).code == "shown-changed"
    assert world.read(checkout).task.criteria.approvals == ()
