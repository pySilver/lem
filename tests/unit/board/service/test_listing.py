"""The machine's list of workspaces from each command that makes a task wait for this machine's
board server (`cli/listing.py`): the open of a task and of its session, the pull request and the
merge agent's read each put the main checkout there once, also from the task's worktree; a
refusal writes no list; and a list that cannot be written is a refusal, never a silent stall.

Each command runs in this process (`lem.cli.lazy.main`) with a home of its own; the open of a
task is the real one, and the other three run with their use case replaced, since what is checked
is that the command puts its workspace on the list, not what the use case does."""

import json
import stat
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from lem.app.landing import mergeread, propose
from lem.app.sessions import here, opening
from lem.board import workspaces
from lem.cli import lazy
from lem.kernel import folders
from lem.kernel.envelope import Envelope
from unit.task.spaces import workspace

if TYPE_CHECKING:
    from pathlib import Path

SLUG = "gift-note"
OPEN = ("task", "open", SLUG, "--ask", "add a gift note")
# The commands whose use case the test replaces (`replaced`).
REPLACED = (
    ("session", "open", SLUG, "--why", "new"),
    ("land", "propose", SLUG, "--title", "feat: x", "--notes", "n.md"),
    ("land", "merge-review", SLUG),
)


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home folder of Lem for this case alone."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    return tmp_path / "config" / "lem"


def lem(
    capsys: pytest.CaptureFixture[str], where: Path, *argv: str
) -> dict[str, object]:
    """`lem --repo WHERE ARGV` in this process: its envelope, with its exit code."""
    code = lazy.main(["--repo", str(where), *argv])
    return {**json.loads(capsys.readouterr().out), "code": code}


def replaced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each use case of `REPLACED` gives a plain envelope, and the session's is open."""
    done = Envelope(ok=True)
    made = SimpleNamespace(already=False, said=lambda: None)
    monkeypatch.setattr(here, "bound", lambda folder: folder)
    monkeypatch.setattr(here, "enveloped", lambda *given: done)
    monkeypatch.setattr(opening, "open_session", lambda *given: made)
    monkeypatch.setattr(propose, "run", lambda *given, **words: done)
    monkeypatch.setattr(mergeread, "run", lambda *given, **words: done)


def test_the_open_of_a_task_puts_its_workspace_on_the_list_once(
    tmp_path: Path, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = workspace(tmp_path / "shop")
    assert not (home / workspaces.WORKSPACES).exists()
    assert lem(capsys, where.checkout, *OPEN)["code"] == 0
    assert workspaces.listed(home) == (str(where.checkout.resolve()),)
    # the same open again is a retry: it passes, and the list holds the checkout once
    assert lem(capsys, where.checkout, *OPEN)["code"] == 0
    assert workspaces.listed(home) == (str(where.checkout.resolve()),)


@pytest.mark.parametrize("argv", REPLACED, ids=[" ".join(one[:2]) for one in REPLACED])
def test_the_session_the_pull_request_and_the_merge_read_put_the_workspace_on_the_list(
    tmp_path: Path,
    home: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    argv: tuple[str, ...],
) -> None:
    other = workspace(tmp_path / "other")
    workspaces.changed(home, str(other.checkout.resolve()), add=True)
    where = workspace(tmp_path / "shop")
    worktree = where.checkout / ".lem" / "worktrees" / SLUG
    worktree.mkdir(parents=True)
    (where.checkout / ".git" / "worktrees" / SLUG).mkdir(parents=True)
    (where.checkout / ".git" / "worktrees" / SLUG / "commondir").write_text("../..\n")
    (worktree / ".git").write_text(
        f"gitdir: {where.checkout / '.git' / 'worktrees' / SLUG}\n"
    )
    replaced(monkeypatch)
    assert lem(capsys, worktree, *argv)["code"] == 0
    assert workspaces.listed(home) == (
        str(other.checkout.resolve()),
        str(where.checkout.resolve()),
    )


def test_a_refused_open_writes_no_list(
    tmp_path: Path, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = workspace(tmp_path / "shop")
    (where.state / folders.MARKER).unlink()
    (where.state / "events.jsonl").write_text('{"event": "task.open"}\n')
    refused = lem(capsys, where.checkout, *OPEN)
    assert refused["code"] == 1
    assert isinstance(refused["refusal"], dict)
    assert refused["refusal"]["code"] == "old-state"
    assert not (home / workspaces.WORKSPACES).exists()


def test_a_list_that_cannot_be_written_refuses_the_open(
    tmp_path: Path, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = workspace(tmp_path / "shop")
    folders.home_marked(home)
    home.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        refused = lem(capsys, where.checkout, *OPEN)
    finally:
        home.chmod(stat.S_IRWXU)
    assert refused["code"] == 1
    assert isinstance(refused["refusal"], dict)
    assert refused["refusal"]["code"] == "workspaces-write"
    assert str(home / workspaces.WORKSPACES) in refused["refusal"]["why"]
    assert workspaces.listed(home) == ()
