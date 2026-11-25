"""Open, next, close and list of a task's session, on the fake terminal and harness: the brief,
the launch line, no focus, the record of each open and close, and each refusal."""

import dataclasses
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import msgspec
import pytest

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.records import MOMENT, record
from lem.app.sessions import acts, brief, closing, handing, listing, log, opening
from lem.app.sessions.here import Here
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.ports.harness import Seat, Signs, Transcript
from lem.ports.terminal import Opening, Pane
from lem.records.holds import Parked
from lem.records.sessions import SessionLine
from lem.records.task import Shape
from lem.store import places, sessions, tasks
from unit.sessions.harness import SigningHarness
from unit.sessions.terminal import CALLER, with_caller
from unit.sessions.terminal import LookingTerminal as FakeTerminal

if TYPE_CHECKING:
    from pathlib import Path

    from fakes.harness import FakeHarness
    from lem.records.record import Record

SLUG = "gift-note"
LATER = MOMENT + timedelta(minutes=5)
HANDOFF = """<!-- lem: old form -->
task: gift-note · from shape · written: 2026-11-25T10:07Z

<!-- a comment of the template -->

## Settled

- the criteria

## Open

none

## Next step

Plan the column.

## Failed

none

## Changed files

none
"""


def here_of(
    checkout: Path,
    terminal: FakeTerminal | None = None,
    harness: FakeHarness | None = None,
) -> Here:
    """A workspace in `checkout` with Lem set up, on fakes."""
    (checkout / ".git").mkdir(parents=True, exist_ok=True)
    (checkout / ".lem").mkdir(exist_ok=True)
    places.state_of(checkout)
    git = ModelGit(checkout=checkout)
    ports = fake_ports(git, LocalForge(remote=git), terminal or with_caller(), harness)
    return Here(where=places.workspace(checkout), ports=ports, caller="S-MINE")


def made(here: Here, slug: str = SLUG, **fields: object) -> Record:
    """A task of the workspace, with `fields` over a queued one."""
    return tasks.create(here.where.state, record(slug, **fields))


def test_open_writes_the_brief_and_opens_in_the_main_checkout_in_the_callers_workspace(
    tmp_path: Path,
) -> None:
    terminal, harness = with_caller(), SigningHarness()
    here = here_of(tmp_path, terminal, harness)
    made(here)
    got = opening.open_session(here, SLUG, "new", None, MOMENT)
    assert (got.session, got.phase, got.already) == ("session-1", "shape", False)
    path = here.folder(SLUG) / brief.BRIEF
    text = path.read_text().splitlines()
    assert text[0] == brief.FIRST
    assert text[2:] == [
        f"task: {SLUG}",
        "phase: shape",
        "opened because: new",
        f"task directory: {here.folder(SLUG)}",
        f"main checkout: {tmp_path}",
        "worktree: none yet",
    ]
    # Lem's default seat of a task's session, `claude/opus:high` (the owner, 2026-11-22)
    seat = Seat(agent="claude", model="opus", effort="high")
    assert harness.launches == [(seat, str(path), tmp_path, paths.root())]
    assert [(o.name, o.cwd, o.command, o.workspace) for o in terminal.openings] == [
        (SLUG, str(tmp_path), ("claude-1",), "W-1")
    ]
    assert [line.session for line in log.read(here.folder(SLUG))] == ["session-1"]
    assert not any(pane.selected for pane in terminal.panes.values())


class LosingTerminal(FakeTerminal):
    """A terminal that stops answering once it made a session."""

    def open(self, opening: Opening) -> str:
        made = super().open(opening)
        self.unreadable = "agterm stopped answering"
        return made


def test_a_session_made_is_on_record_before_the_terminal_is_asked_again(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path, LosingTerminal(panes={CALLER.id: CALLER}))
    made(here)
    got = opening.open_session(here, SLUG, "new", None, MOMENT)
    assert [line.session for line in log.read(here.folder(SLUG))] == [got.session]


def test_a_second_open_gives_the_session_that_runs(tmp_path: Path) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here)
    opening.open_session(here, SLUG, "new", None, MOMENT)
    again = opening.open_session(here, SLUG, "dead", None, LATER)
    assert (again.session, again.already) == ("session-1", True)
    assert len(terminal.openings) == 1
    assert again.said() == f"{SLUG} already runs in the session `{SLUG}`"
    terminal.close("session-1", when_unselected=False)
    fresh = opening.open_session(here, SLUG, "dead", None, LATER)
    assert (fresh.session, fresh.already) == ("session-2", False)


def test_a_new_session_goes_to_the_workspace_of_the_tasks_newest(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    terminal.panes["S-HIS"] = Pane(id="S-HIS", name="notes", workspace="W-2")
    here = here_of(tmp_path, terminal)
    made(here)
    old = acts.Open(
        at=MOMENT, session="S-OLD", name=SLUG, phase="shape", why="new", workspace="W-2"
    )
    log.append(here.folder(SLUG), old)
    got = opening.open_session(here, SLUG, "dead", None, LATER)
    assert terminal.openings[-1].workspace == "W-2"
    assert got.workspace == "W-2"


@pytest.mark.parametrize(
    ("fields", "code"),
    [
        ({"hold": Parked(since=MOMENT)}, "parked"),
        ({"status": "landed"}, "ended"),
        ({"after": "first-task"}, "queued-after"),
        ({"after": "never-made"}, "queued-after"),
    ],
)
def test_open_refuses_a_task_that_gets_no_session_now(
    tmp_path: Path, fields: dict[str, Any], code: str
) -> None:
    here = here_of(tmp_path)
    made(here, "first-task", status="building")
    made(here, **fields)
    with pytest.raises(Refusal) as refused:
        opening.open_session(here, SLUG, "new", None, MOMENT)
    assert refused.value.code == code
    assert log.read(here.folder(SLUG)) == ()


def test_open_refuses_a_task_that_is_not_there_and_a_terminal_that_does_not_read(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path, FakeTerminal(unreadable="agterm does not answer"))
    with pytest.raises(Refusal, match="no task gift-note"):
        opening.open_session(here, SLUG, "new", None, MOMENT)
    made(here)
    with pytest.raises(Refusal, match="agterm does not answer"):
        opening.open_session(here, SLUG, "new", None, MOMENT)


def test_a_queued_task_opens_once_the_task_it_waits_for_landed(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    made(here, "first-task", status="landed")
    made(here, after="first-task", lead="builder")
    assert opening.open_session(here, SLUG, "queue", None, MOMENT).phase == "build"


def building(here: Here) -> None:
    """The task's record after the owner's yes: the build, with its lead."""
    current = tasks.read(here.where.state, SLUG)
    shape = Shape(type="feat", why="a column", track="full")
    task = msgspec.structs.replace(
        current.task, status="building", lead="session", shape=shape
    )
    tasks.update(
        here.where.state,
        SLUG,
        lambda before: msgspec.structs.replace(before, task=task),
        current.revision,
    )


def test_next_opens_the_next_phase_after_a_handoff_in_its_form(tmp_path: Path) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="shaping")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    here = dataclasses.replace(here, caller="session-1")
    with pytest.raises(Refusal) as same:
        handing.hand_on(here, SLUG, same=False, now=LATER)
    assert same.value.code == "same-phase"
    assert "--same" in same.value.fix
    building(here)
    with pytest.raises(Refusal, match="is not there"):
        handing.hand_on(here, SLUG, same=False, now=LATER)
    folder = here.folder(SLUG)
    (folder / "handoff.md").write_text(HANDOFF.replace("## Next step", "## Later"))
    with pytest.raises(Refusal, match="it lacks ## Next step"):
        handing.hand_on(here, SLUG, same=False, now=LATER)
    (folder / "handoff.md").write_text(HANDOFF.replace("from shape", "from build"))
    with pytest.raises(
        Refusal, match="is from build, and the phase that ends is shape"
    ):
        handing.hand_on(here, SLUG, same=False, now=LATER)
    (folder / "handoff.md").write_text(HANDOFF.replace("10:07Z", "09:07Z"))
    with pytest.raises(Refusal, match="older session's"):
        handing.hand_on(here, SLUG, same=False, now=LATER)
    (folder / "handoff.md").write_text(HANDOFF)
    got = handing.hand_on(here, SLUG, same=False, now=LATER)
    assert (got.session, got.phase, got.old, got.ended) == (
        "session-2",
        "build",
        "session-1",
        "shape",
    )
    assert got.close == (
        f"lem session close {SLUG} --session session-1 --why handoff --when-unselected"
    )
    opens = [line for line in log.read(folder) if isinstance(line, acts.Open)]
    assert [line.why for line in opens] == ["new", "handoff"]
    assert "phase: build" in (folder / brief.BRIEF).read_text()
    assert terminal.renamed == [("session-1", f"{SLUG} · handed off")]


def test_next_with_same_opens_a_fresh_session_of_the_same_phase(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    made(here, status="shaping")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    here = dataclasses.replace(here, caller="session-1")
    (here.folder(SLUG) / "handoff.md").write_text(HANDOFF)
    got = handing.hand_on(here, SLUG, same=True, now=LATER)
    assert (got.phase, got.ended, got.old) == ("shape", "shape", "session-1")
    with pytest.raises(Refusal, match="no session of other-task"):
        made(here, "other-task")
        handing.hand_on(here, "other-task", same=True, now=LATER)


def closing_of(**fields: object) -> closing.Closing:
    """A close of the task's newest session, with `fields`."""
    asked = closing.Closing(slug=SLUG, why="handoff", every=0.0)
    return msgspec.structs.replace(asked, **fields)


def test_close_never_closes_the_session_he_looks_at_and_waits_when_told(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here)
    opening.open_session(here, SLUG, "new", None, MOMENT)
    terminal.panes["S-HIS"] = Pane(id="S-HIS", name="notes")
    terminal.select("session-1")
    with pytest.raises(Refusal) as refused:
        closing.close_session(here, closing_of(), lambda _: None, lambda: LATER)
    assert refused.value.code == "selected"
    assert "--when-unselected" in refused.value.fix
    assert terminal.closed == []
    looks: list[float] = []

    def he_leaves(every: float) -> None:
        looks.append(every)
        terminal.select("S-HIS")

    got = closing.close_session(
        here, closing_of(when_unselected=True, every=5.0), he_leaves, lambda: LATER
    )
    assert (got.session, got.closed, looks) == ("session-1", True, [5.0])
    assert terminal.closed == ["session-1"]
    closes = [
        line for line in log.read(here.folder(SLUG)) if isinstance(line, acts.Close)
    ]
    assert [(line.session, line.why, line.at) for line in closes] == [
        ("session-1", "handoff", LATER)
    ]
    again = closing.close_session(here, closing_of(), lambda _: None, lambda: LATER)
    assert again.closed is False
    assert (
        len(
            [
                line
                for line in log.read(here.folder(SLUG))
                if isinstance(line, acts.Close)
            ]
        )
        == 1
    )


def test_close_refuses_a_session_lem_did_not_open_for_the_task(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    made(here)
    with pytest.raises(Refusal, match="no session of gift-note is on record"):
        closing.close_session(here, closing_of(), lambda _: None, lambda: LATER)
    opening.open_session(here, SLUG, "new", None, MOMENT)
    with pytest.raises(Refusal, match="S-HIS is no session of gift-note"):
        closing.close_session(
            here, closing_of(session="S-HIS"), lambda _: None, lambda: LATER
        )


def test_list_gives_each_tasks_newest_session_with_its_phase_now_and_its_signs(
    tmp_path: Path,
) -> None:
    terminal, harness = with_caller(), SigningHarness()
    here = here_of(tmp_path, terminal, harness)
    made(here, status="shaping")
    made(here, "quiet-task")
    made(
        here,
        "gone-task",
        status="building",
        shape=Shape(type="fix", why="w", track="small"),
    )
    opening.open_session(here, SLUG, "new", None, MOMENT)
    opening.open_session(here, "gone-task", "new", None, MOMENT)
    terminal.close("session-2", when_unselected=False)
    folder = here.folder(SLUG)
    for claude, pane in (("c-old", "S-OTHER"), ("c-new", "session-1")):
        line = SessionLine(
            at=MOMENT,
            source="startup",
            claude=claude,
            transcript=f"/t/{claude}",
            pane=pane,
            task=SLUG,
        )
        sessions.append(folder, line)
    harness.by_task[SLUG] = (
        Transcript(path="/t/c-old", claude="c-old"),
        Transcript(path="/t/c-new", claude="c-new"),
    )
    harness.signs_of["/t/c-new"] = Signs(sign=LATER, turn="runs")
    found = {entry.task: entry for entry in listing.list_sessions(here, LATER)}
    assert sorted(found) == ["gift-note", "gone-task"]
    mine, gone = found[SLUG], found["gone-task"]
    assert (mine.session, mine.phase, mine.opened_in, mine.live, mine.selected) == (
        "session-1",
        "shape",
        "shape",
        True,
        False,
    )
    assert (mine.sign, mine.turn, mine.signs) == (LATER, "runs", True)
    assert (gone.live, gone.phase, gone.signs, gone.sign) == (
        False,
        "fast",
        False,
        None,
    )


def test_list_asks_the_terminal_nothing_when_no_session_was_opened(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path, FakeTerminal(unreadable="agterm does not answer"))
    made(here)
    assert listing.list_sessions(here, LATER) == ()


def test_next_from_an_old_session_after_another_took_over_is_refused(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    made(here, status="shaping")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    (here.folder(SLUG) / "handoff.md").write_text(HANDOFF)
    handing.hand_on(
        dataclasses.replace(here, caller="session-1"), SLUG, same=True, now=LATER
    )
    from_the_first = Here(where=here.where, ports=here.ports, caller="session-1")
    with pytest.raises(Refusal) as refused:
        handing.hand_on(from_the_first, SLUG, same=True, now=LATER)
    assert refused.value.code == "taken-over"
    assert "--session session-1 --why handoff" in refused.value.fix
    from_the_second = Here(where=here.where, ports=here.ports, caller="session-2")
    got = handing.hand_on(from_the_second, SLUG, same=True, now=LATER)
    assert (got.old, got.session) == ("session-2", "session-3")
    assert "--session session-2 " in got.close


class ClickedTerminal(FakeTerminal):
    """A terminal whose owner selects the session in the moment Lem closes it."""

    clicks: int = 0

    def close(self, session: str, *, when_unselected: bool) -> None:
        if self.clicks:
            self.clicks -= 1
            self.select(session)
        super().close(session, when_unselected=when_unselected)


def test_a_close_the_owner_cut_off_by_his_click_is_never_said_done(
    tmp_path: Path,
) -> None:
    terminal = ClickedTerminal(panes={CALLER.id: CALLER})
    here = here_of(tmp_path, terminal)
    made(here)
    opening.open_session(here, SLUG, "new", None, MOMENT)
    terminal.panes["S-HIS"] = Pane(id="S-HIS", name="notes")
    terminal.clicks = 1
    with pytest.raises(Refusal) as refused:
        closing.close_session(here, closing_of(), lambda _: None, lambda: LATER)
    assert refused.value.code == "selected"
    assert "session-1" in terminal.panes
    terminal.clicks = 1

    def he_leaves(_every: float) -> None:
        terminal.select("S-HIS")

    got = closing.close_session(
        here, closing_of(when_unselected=True), he_leaves, lambda: LATER
    )
    assert got.closed is True
    assert "session-1" not in terminal.panes


def test_a_transcript_that_gives_nothing_is_no_sign_read(tmp_path: Path) -> None:
    harness = SigningHarness()
    here = here_of(tmp_path, with_caller(), harness)
    made(here, status="shaping")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    line = SessionLine(
        at=MOMENT,
        source="startup",
        claude="c1",
        transcript="/gone/c1.jsonl",
        pane="session-1",
        task=SLUG,
    )
    sessions.append(here.folder(SLUG), line)
    harness.by_task[SLUG] = (Transcript(path="/gone/c1.jsonl", claude="c1"),)
    (entry,) = listing.list_sessions(here, LATER)
    assert (entry.live, entry.signs, entry.sign, entry.turn) == (
        True,
        False,
        None,
        None,
    )
