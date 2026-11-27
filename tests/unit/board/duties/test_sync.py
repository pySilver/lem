"""The sync duty of the board server (`board/duties/sync.py`): a feature that waits for its parts
is woken with `lem: NAME sync` once for each commit of origin's base that its branch on origin
lacks, on `ModelGit` and the fake terminal; and the queue duty gives a feature its turn after a
`sync` wake. A `sync` line of the file of session acts is skipped by the reader of Lem 0.4.2."""

from datetime import timedelta
from typing import TYPE_CHECKING, Literal

import msgspec
import pytest
from msgspec.structs import replace

from fakes.git import ModelGit
from fakes.records import MOMENT
from lem.app.sessions import acts, log, opening
from lem.board.duties import queue, sync
from lem.board.duties.memory import Kept
from lem.kernel.errors import Refusal
from lem.records.base import Moment, Tagged
from lem.records.holds import Blocked
from lem.store import tasks
from unit.board.duties.world import duty_of
from unit.sessions.terminal import LookingTerminal, with_caller
from unit.sessions.world import here_of, made

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.sessions.here import Here

FEATURE = "save-items"
BRANCH = "feature/save-items"
PART = "save-endpoint"
LATER = MOMENT + timedelta(minutes=5)
HOUR = MOMENT + timedelta(hours=1)
SETTINGS = '[branch]\nbase = "main"\n'


def git_of(here: Here) -> ModelGit:
    git = here.ports.git
    assert isinstance(git, ModelGit)
    return git


def world(tmp_path: Path) -> Here:
    """A workspace whose settings name `main`, with a feature that waits for one part, and
    origin's `main` and the feature's branch as git last fetched them, the branch holding
    `main`."""
    here = here_of(tmp_path, with_caller())
    (here.where.checkout / ".lem" / "settings.toml").write_text(SETTINGS)
    made(here, PART, status="building", part_of=FEATURE, lead="builder")
    made(here, FEATURE, status="queued", branch=BRANCH, after=(PART,))
    git = git_of(here)
    first = git.store({"README.md": b"one\n"}, (), "the first commit")
    feature = git.store({"README.md": b"one\n", "F.md": b"f\n"}, (first,), "a part")
    git.fetched.update({"main": first, BRANCH: feature})
    return here


def landed_on_main(here: Here, name: str) -> str:
    """A commit on origin's `main` that the feature's branch lacks, as last fetched."""
    git = git_of(here)
    tip = git.fetched["main"]
    made = git.store({"README.md": b"one\n", name: b"x\n"}, (tip,), f"add {name}")
    git.fetched["main"] = made
    return made


def syncs(here: Here) -> list[str | None]:
    """The head of each `sync` wake of the feature, in order."""
    found = log.read(here.folder(FEATURE))
    return [
        act.head for act in found if isinstance(act, acts.Wake) and act.why == "sync"
    ]


def test_a_feature_whose_branch_holds_the_base_gets_no_wake(tmp_path: Path) -> None:
    here = world(tmp_path)
    sync.tick(duty_of(here, HOUR))
    assert syncs(here) == []
    assert log.read(here.folder(FEATURE)) == ()


def test_a_base_commit_wakes_the_feature_once_and_a_newer_one_again(
    tmp_path: Path,
) -> None:
    here = world(tmp_path)
    first = landed_on_main(here, "one.txt")
    kept = Kept()
    sync.tick(duty_of(here, HOUR, kept))
    sync.tick(duty_of(here, HOUR + timedelta(minutes=1), kept))
    assert syncs(here) == [first]
    # no session of the feature lived, so the wake opened one, though its parts are open
    opened = [
        act for act in log.read(here.folder(FEATURE)) if isinstance(act, acts.Open)
    ]
    assert [act.why for act in opened] == ["sync"]
    second = landed_on_main(here, "two.txt")
    sync.tick(duty_of(here, HOUR + timedelta(minutes=2), kept))
    assert syncs(here) == [first, second]


def test_a_live_session_of_the_feature_gets_the_line(tmp_path: Path) -> None:
    here = world(tmp_path)
    landed_on_main(here, "one.txt")
    sync.tick(duty_of(here, HOUR))
    terminal = here.ports.terminal
    assert isinstance(terminal, LookingTerminal)
    landed_on_main(here, "two.txt")
    sync.tick(duty_of(here, HOUR + timedelta(minutes=1)))
    assert terminal.told[-1][1] == f"lem: {FEATURE} sync"


def test_no_feature_on_record_makes_no_git_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path, with_caller())
    made(here, "a-task", status="queued", branch="fix/a-task")

    def asked(*_args: object) -> None:
        raise AssertionError("the duty read git")

    monkeypatch.setattr(git_of(here), "remote_head", asked)
    sync.tick(duty_of(here, HOUR))
    assert log.read(here.folder("a-task")) == ()


HELD = Blocked(why="the sync failed", fix="a builder repairs it", since=MOMENT)


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({"hold": HELD}, id="hold"),
        pytest.param({"after": ("other",)}, id="turn"),
        pytest.param({"status": "building", "lead": "builder"}, id="building"),
    ],
)
def test_a_feature_on_hold_whose_turn_came_or_that_is_not_queued_gets_no_wake(
    tmp_path: Path, fields: dict[str, object]
) -> None:
    here = world(tmp_path)
    made(here, "other", status="landed", since=LATER)
    landed_on_main(here, "one.txt")
    found = tasks.read(here.where.state, FEATURE)
    task = replace(found.task, **fields)
    tasks.update(
        here.where.state,
        FEATURE,
        lambda one: replace(one, task=task),
        found.revision,
    )
    sync.tick(duty_of(here, HOUR))
    assert syncs(here) == []


def test_the_queue_gives_a_feature_its_turn_after_a_sync_wake(tmp_path: Path) -> None:
    here = world(tmp_path)
    landed_on_main(here, "one.txt")
    sync.tick(duty_of(here, LATER))
    assert len(syncs(here)) == 1
    found = tasks.read(here.where.state, PART)
    part = replace(found.task, status="landed", since=HOUR)
    tasks.update(
        here.where.state, PART, lambda one: replace(one, task=part), found.revision
    )
    queue.tick(duty_of(here, HOUR + timedelta(minutes=1)))
    woken = log.read(here.folder(FEATURE))
    turns = [act for act in woken if isinstance(act, acts.Wake) and act.why == "queue"]
    assert len(turns) == 1


# Lem 0.4.2's form of the act `Wake`, copied from commit f8e4a91b (`app/sessions/acts.py`).
type OldWakeWhy = Literal[
    "merged", "conflict", "refused", "queue", "owner", "inbox", "status", "replaced"
]


class OldWake(Tagged, tag="wake", frozen=True, kw_only=True):
    at: Moment
    session: str
    why: OldWakeWhy
    head: str | None = None
    unread: bool = False
    after_end: bool = False


type OldAct = acts.Open | acts.Close | OldWake | acts.Stopped | acts.Worked


def test_a_sync_wake_is_skipped_by_the_reader_of_lem_0_4_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = world(tmp_path)
    folder = here.folder(FEATURE)
    head = "a" * 40
    log.append(folder, acts.Wake(at=MOMENT, session="S-1", why="queue"))
    log.append(folder, acts.Wake(at=LATER, session="S-1", why="sync", head=head))
    raw = (folder / log.ACTS).read_bytes().split(b"\n")
    written = [line for line in raw if line.strip()]
    assert msgspec.json.decode(written[1])["why"] == "sync"
    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(written[1], type=OldAct)
    monkeypatch.setattr(log, "Act", OldAct)
    assert log.read(folder) == (OldWake(at=MOMENT, session="S-1", why="queue"),)


def test_a_sync_opens_a_session_only_for_a_feature_before_its_turn(
    tmp_path: Path,
) -> None:
    here = world(tmp_path)
    made(here, "first", status="building", lead="builder")
    made(here, "waits", status="queued", after=("first",), lead="builder")
    with pytest.raises(Refusal) as refused:
        opening.open_session(here, "waits", "sync", None, HOUR)
    assert refused.value.code == "queued-after"
    with pytest.raises(Refusal):
        opening.open_session(here, FEATURE, "queue", None, HOUR)
    opened = opening.open_session(here, FEATURE, "sync", None, HOUR)
    assert opened.already is False
