"""The rulings the owner's texts hold in one place (`docs/rulings/history.md`, "Kept in one place"):
each is still in the text and the place the ruling names."""

from pathlib import Path

import msgspec
import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT, record
from lem.kernel import paths
from lem.records.journal.task import StateNoted, Summary
from lem.records.tickets import Ticket
from lem.records.work import Investigation
from lem.store import tasks
from unit.task.spaces import made, result, workspace
from unit.task.spaces import rows as task_rows

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
    ticket = shown["ticket"]
    assert ticket["owed"] == ["dropped"]
    field = "ticket.owed"
    status = text("stages/status.md")
    assert f"`{field}`" in status
    assert f"`{field}`" in text("SKILL.md")
    assert "`lem issue STEP SLUG`" in status
    assert "`drop` for `dropped`" in status


def test_status_reads_an_ended_tasks_answer_from_its_investigation(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    slug = "colored-label"
    answer = "The label gets its color from the theme."
    investigation = Investigation(kind="question", call="answer", line=answer)
    made(where, slug, status="shaping", investigation=investigation)
    folder = Path(result(lem("task", "dir", slug, cwd=tmp_path))["folder"])
    report = folder / "investigation.md"
    report.write_text(f"# Investigation\n\n## Cause\n{answer}\n", encoding="utf-8")
    moved = result(
        lem("task", "move", slug, "answered", "--line", answer, cwd=tmp_path)
    )
    assert moved["status"] == "answered"
    (ended,) = task_rows(lem("task", "list", "--ended", cwd=tmp_path))
    assert (ended["slug"], ended["status"]) == (slug, "answered")
    assert answer not in str(ended)
    assert answer in report.read_text(encoding="utf-8")
    status = text("stages/status.md")
    assert "`lem task list --ended`" in status
    assert "read `investigation.md`" in status
    assert "`lem task dir SLUG`" in status


@pytest.mark.parametrize("kept", [True, False], ids=["investigation", "state-line"])
def test_status_names_the_answer_kept_after_the_report_is_gone(
    tmp_path: Path, *, kept: bool
) -> None:
    where = workspace(tmp_path)
    slug = "colored-label"
    answer = "The label gets its color from the theme."
    investigation = Investigation(kind="question", call="answer", line=answer)
    last = StateNoted(at=MOMENT, status="answered", line=answer)
    summary = Summary(
        at=MOMENT,
        statuses=("answered",),
        last_state=last,
        first=MOMENT,
        last=MOMENT,
        entries=1,
    )
    made = record(
        slug, status="answered", investigation=investigation if kept else None
    )
    tasks.create(where.state, replace(made, journal=(summary,)))
    folder = Path(result(lem("task", "dir", slug, cwd=tmp_path))["folder"])
    assert not (folder / "investigation.md").exists()
    stored = msgspec.json.decode((folder / "task.json").read_bytes())
    if kept:
        assert stored["task"]["investigation"]["line"] == answer
    else:
        assert stored["journal"][0]["last_state"]["line"] == answer
    status = text("stages/status.md")
    assert "`task.json`" in status
    assert "`task.investigation.line`" in status
    assert "`last_state.line`" in status


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
