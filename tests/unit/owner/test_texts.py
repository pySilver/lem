"""The rulings the owner's texts hold in one place (`docs/rulings/history.md`, "Kept in one place"):
each is still in the text and the place the ruling names."""

from typing import TYPE_CHECKING

from fakes.command import lem
from lem.kernel import paths
from lem.records.tickets import Ticket
from unit.task.spaces import made, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

SKILL = paths.root() / "skills" / "lem"


def text(name: str) -> str:
    return " ".join((SKILL / name).read_text(encoding="utf-8").split())


def rows(name: str) -> list[str]:
    return [
        line
        for line in (SKILL / name).read_text(encoding="utf-8").splitlines()
        if line.startswith(("| `", "| a helper", "| bare"))
    ]


def row(name: str, head: str) -> str:
    found = [line for line in rows(name) if line.startswith(f"| {head}")]
    assert len(found) == 1, (head, found)
    return found[0]


def test_his_status_and_a_tasks_corrections_are_subcommands() -> None:
    assert "`stages/away.md`" in row("SKILL.md", "`im-away`, `im-back`")
    corrections = row("SKILL.md", "`be-careful`, `standard-track`, `drop`")
    assert "`stages/correct.md`" in corrections


def test_read_shows_a_ticket_and_writes_nothing_to_it() -> None:
    read = row("SKILL.md", "`read <ticket>`")
    assert "it opens no task and writes nothing to the ticket" in read


def test_a_helper_starts_from_plain_words() -> None:
    helper = row("SKILL.md", "a helper")
    assert "Plain words start one too, with or without `/lem`" in helper
    assert "Never a page for this." in text("SKILL.md")


def test_what_waits_is_one_list_and_the_status_only_reads() -> None:
    status = row("SKILL.md", "bare `/lem`, `status`")
    assert status.startswith(
        "| bare `/lem`, `status` | the one list of what waits for the owner"
    )
    assert "and the status only reads" in text("stages/status.md")
    assert "lem waiting" in text("stages/status.md")


def test_status_names_the_field_and_step_for_an_unpaid_ticket(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    ticket = Ticket(tracker="github", id="#42", repo="o/r")
    made(where, "gift-note", status="dropped", ticket=ticket)
    shown = result(lem("task", "show", "gift-note", cwd=tmp_path))
    assert shown["ticket"]["owed"] == ["dropped"]
    status = text("stages/status.md")
    assert "`ticket.owed`" in status
    assert "`lem issue STEP SLUG`" in status
    assert "`drop` for `dropped`" in status


def test_the_holds_keep_what_has_no_options_and_a_block_leaves_no_document() -> None:
    owner = row("SKILL.md", "`owner`")
    assert "no choice of a build waits for him" in owner
    blocked = row("SKILL.md", "`blocked`")
    assert (
        "its one line names what to do and it leaves no breaker's document" in blocked
    )


def test_the_size_of_a_change_decides_its_path() -> None:
    said = text("SKILL.md")
    assert "The fast track is for one plain change" in said
    assert "Every other request takes the standard track" in said


def test_his_away_is_the_machines_and_a_night_runs_without_him() -> None:
    away = text("stages/away.md")
    assert "His status is the machine's" in away
    assert "a night's, which runs without him until it ends" in away
    assert "lem owner watch --seen N" in away
