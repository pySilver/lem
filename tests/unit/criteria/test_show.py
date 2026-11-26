"""The criteria as they stand: from the plan, or the fast track's `criteria.md`; against their
approval and each recorded change; kept in the record; their mark; the personas' read and his
word on its skip; and the commands that print them."""

from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.command import lem
from lem.app.criteria import approve, marks, persona, show, skipping
from lem.kernel.errors import Refusal
from lem.model.criteria import reads, skip
from lem.records.holds import OwnerHold
from unit.criteria import world

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.records.task import Task

PLANNED = world.FULL.replace("row.\n", "row.\n" + world.TESTED) + (
    "   - no test: an empty cell is the CSV's own.\n"
)


def refused(call: Callable[..., object], *args: object) -> Refusal:
    with pytest.raises(Refusal) as caught:
        call(*args)
    return caught.value


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    found = world.workspace(tmp_path / "shop")
    world.task(found, status="building")
    return found


def approved(checkout: Path, text: str = world.FULL) -> None:
    path = world.sheet(checkout, text)
    approve.approved(checkout, world.SLUG, approve.Asked(by="owner", path=path))


def test_the_plans_criteria_against_the_approved_ones(checkout: Path) -> None:
    assert refused(show.shown, checkout, world.SLUG).code == "no-worktree"
    world.worktree(checkout)
    assert refused(show.shown, checkout, world.SLUG).code == "no-plan"
    approved(checkout)
    world.plan(checkout, PLANNED)
    seen = show.shown(checkout, world.SLUG)
    assert (seen.small, seen.size, len(seen.criteria)) == (False, "full", 2)
    assert seen.plan.endswith("docs/plans/2026-11-25-gift-note.md")
    world.plan(checkout, PLANNED.replace("1042", "1043"))
    differs = refused(show.shown, checkout, world.SLUG)
    assert (differs.code, "criterion 1 of" in differs.why) == ("criteria-differ", True)
    world.plan(checkout, world.SMALL)
    assert refused(show.shown, checkout, world.SLUG).code == "track"


def test_a_plan_cannot_add_an_unrecorded_criterion(checkout: Path) -> None:
    approved(checkout)
    world.plan(checkout, PLANNED + "3. The new column is sorted.\n")
    before = world.read(checkout)
    problem = refused(show.recorded, checkout, world.SLUG)
    assert problem.code == "criteria-differ"
    assert "lem decisions criterion" in problem.fix
    assert world.read(checkout) == before


def test_a_plan_never_puts_a_task_on_the_fast_track(checkout: Path) -> None:
    world.plan(checkout, world.SMALL)
    assert refused(show.shown, checkout, world.SLUG).code == "small-plan"


def test_the_fast_tracks_criterion_needs_its_approval_and_is_recorded(
    checkout: Path,
) -> None:
    world.worktree(checkout)
    world.sheet(checkout, world.SMALL)
    assert refused(show.shown, checkout, world.SLUG).code == "unapproved"
    approve.approved(checkout, world.SLUG, approve.Asked(by="lem"))
    world.sheet(checkout, world.SMALL + "   - no test: one word of a text\n")
    seen = show.recorded(checkout, world.SLUG)
    kept = world.read(checkout).task.criteria
    assert seen.small
    assert (kept.digest, kept.criteria[0].no_test) == (
        seen.digest,
        "one word of a text",
    )


def test_the_plan_of_the_task_it_came_from(checkout: Path) -> None:
    world.task(checkout, "gift-note-2", resumed_from=world.SLUG)
    world.worktree(checkout, "gift-note-2")
    folder = world.worktree(checkout, "gift-note-2") / "docs" / "plans"
    folder.mkdir(parents=True)
    (folder / "2026-11-24-gift-note.md").write_text(PLANNED, encoding="utf-8")
    seen = show.shown(checkout, "gift-note-2")
    assert seen.plan.endswith("2026-11-24-gift-note.md")


def test_the_mark_of_a_file_and_of_the_criteria_as_they_stand(checkout: Path) -> None:
    path = world.sheet(checkout, world.FULL)
    of_file = marks.marked(checkout, world.SLUG, path)
    world.plan(checkout, PLANNED)
    assert marks.marked(checkout, world.SLUG, None).digest == of_file.digest
    assert marks.approved(checkout, world.SLUG).approved is None
    approved(checkout)
    found = marks.approved(checkout, world.SLUG).approved
    assert found is not None
    assert found.digest == of_file.digest


def test_the_reads_start_and_end_and_a_wrong_form_is_refused(checkout: Path) -> None:
    persona.noted(checkout, world.SLUG, ("start", "lem"), None)
    found = reads.Found(
        asked=3,
        answered=2,
        families=("opus",),
        silent=(reads.silent_of("Olek, opus: no answer in 10 minutes"),),
        criteria=2,
        flagged=1,
        digest="a" * 12,
    )
    done = persona.noted(checkout, world.SLUG, ("done", "lem"), found)
    assert done.ended is not None
    assert (done.started <= done.ended, done.flagged) == (True, 1)
    assert len(world.read(checkout).task.criteria.reads) == 1
    for wrong in (
        msgspec.structs.replace(found, asked=1),
        msgspec.structs.replace(found, answered=4),
        msgspec.structs.replace(found, families=()),
        msgspec.structs.replace(found, digest="d1"),
        msgspec.structs.replace(found, answered=0),
    ):
        assert refused(
            persona.noted, checkout, world.SLUG, ("done", "lem"), wrong
        ).code == ("criteria-read")
    silent = persona.noted(checkout, world.SLUG, ("silent", "lead"), None)
    assert (silent.by, silent.answered) == ("lead", 0)


@pytest.mark.parametrize("wrong", ["family", "flag", "missed", "duplicate"])
def test_a_read_cannot_claim_a_family_or_findings_it_did_not_get(
    checkout: Path, wrong: str
) -> None:
    name = reads.silent_of("Ania, opus: no answer")
    other = reads.silent_of("Olek, opus: no answer")
    nobody = reads.Found(
        asked=2,
        answered=0,
        criteria=1,
        flagged=0,
        digest="a" * 12,
        silent=(name, other),
    )
    variants = {
        "family": msgspec.structs.replace(nobody, families=("opus",)),
        "flag": msgspec.structs.replace(nobody, flagged=1),
        "missed": msgspec.structs.replace(nobody, silent=(name,)),
        "duplicate": msgspec.structs.replace(
            nobody, answered=2, families=("opus", "opus"), silent=()
        ),
    }
    before = world.read(checkout)
    problem = refused(
        persona.noted, checkout, world.SLUG, ("done", "lead"), variants[wrong]
    )
    assert problem.code == "criteria-read"
    assert world.read(checkout) == before


@pytest.mark.parametrize(
    ("args", "code", "why"),
    [
        (("--asked", "-1"), 2, "Invalid value"),
        (("--asked", "two"), 2, "Invalid value"),
        (("--split", "false"), 2, "unexpected extra argument"),
        (("--by", "owner"), 2, "Invalid value"),
        (("--unknown", "x"), 2, "No such option"),
        (("--silent", "the buyer, opus: "), 1, "PERSONA, FAMILY: WHY"),
    ],
    ids=["negative", "text", "split", "by", "unknown", "silent"],
)
def test_a_bad_read_call_writes_no_read(
    checkout: Path, args: tuple[str, str], code: int, why: str
) -> None:
    supplied = ("--asked", "2") if args[0] != "--asked" else ()
    who = ("--by", "lead") if args[0] != "--by" else ()
    before = world.read(checkout)
    ran = lem(
        "criteria",
        "read",
        world.SLUG,
        "done",
        *who,
        *supplied,
        "--answered",
        "2",
        "--family",
        "opus",
        "--criteria",
        "1",
        "--flagged",
        "0",
        "--digest",
        "a" * 12,
        *args,
        cwd=checkout,
    )
    assert ran.code == code
    assert why in ran.stderr + ran.stdout
    assert world.read(checkout) == before


def test_his_word_on_the_skip_holds_the_task_and_gives_the_interview_back(
    tmp_path: Path,
) -> None:
    checkout = world.workspace(tmp_path / "skip")
    world.task(checkout, hold=world.INTERVIEW)
    skipping.skipped(checkout, world.SLUG, "asked")
    task: Task = world.read(checkout).task
    assert task.hold == OwnerHold(on="skip-read", line=skip.ASKED, since=world.EARLY)
    kept = skipping.skipped(checkout, world.SLUG, "yes")
    assert (kept.skip, world.read(checkout).task.hold) == ("yes", world.INTERVIEW)


def test_the_commands_print_their_outcome_and_refuse_with_exit_1(
    tmp_path: Path,
) -> None:
    checkout = world.workspace(tmp_path / "cmd")
    world.task(checkout)
    world.sheet(checkout, world.SMALL)
    ran = lem("criteria", "approve", world.SLUG, "--small", cwd=checkout)
    assert (ran.code, ran.envelope()["ok"]) == (0, True)
    again = lem("criteria", "approve", world.SLUG, "--small", cwd=checkout)
    refusal = again.envelope()["refusal"]
    assert isinstance(refusal, dict)
    assert (again.code, refusal["code"]) == (1, "approved")
    wrong = lem(
        "criteria", "approve", world.SLUG, "--read", "--file", "x", cwd=checkout
    )
    assert wrong.code == 2
    changed = lem(
        "criteria", "change", world.SLUG, "--pairs", "--words", "x", cwd=checkout
    )
    assert changed.code == 2
    listed = lem("decisions", "list", world.SLUG, cwd=checkout)
    assert (listed.code, listed.result()) == (0, [])
    pending = lem("decisions", "pending", cwd=checkout)
    assert pending.result() == {"waiting": [], "parked": [], "ended": []}
