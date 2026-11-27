"""The machine's list of workspaces from every command of `lem` (`cli/listing.py`): a command in a
repository where Lem is set up puts its main checkout there before its own work, also from the
task's worktree, never the worktree itself; a wrong call, a repository with no settings and a
refused workspace write no list; and a list that cannot be written is a refusal before the
command's effect, also when Lem's home folder is not there yet.

Each command runs in this process (`lem.cli.lazy.main`) with a home of its own."""

import json
import stat
from typing import TYPE_CHECKING

import pytest

from fakes.records import record
from lem.board import workspaces
from lem.cli import lazy
from lem.kernel import folders
from lem.store import tasks
from unit.task.spaces import read, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

SLUG = "gift-note"
OPEN = ("task", "open", SLUG, "--ask", "add a gift note")
READ = (
    "task", "read", SLUG, "--type", "fix", "--why", "use dates", "--track", "small",
    "--then", "fast", "--after", "dates",
)  # fmt: skip


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home folder of Lem for this case alone, not made yet."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    return tmp_path / "config" / "lem"


def lem(
    capsys: pytest.CaptureFixture[str], where: Path, *argv: str
) -> dict[str, object]:
    """`lem --repo WHERE ARGV` in this process: its envelope, with its exit code."""
    code = lazy.main(["--repo", str(where), *argv])
    out = capsys.readouterr().out
    return {**(json.loads(out) if out.strip() else {}), "code": code}


def worktree_of(where: Workspace) -> Path:
    """A linked worktree of the task, as git lays it out."""
    tree = where.checkout / ".lem" / "worktrees" / SLUG
    gitdir = where.checkout / ".git" / "worktrees" / SLUG
    tree.mkdir(parents=True)
    gitdir.mkdir(parents=True)
    (gitdir / "commondir").write_text("../..\n")
    (tree / ".git").write_text(f"gitdir: {gitdir}\n")
    return tree


def code_of(found: dict[str, object]) -> object:
    """The code of a printed refusal."""
    refusal = found.get("refusal")
    return refusal.get("code") if isinstance(refusal, dict) else None


def test_the_open_of_a_task_puts_its_workspace_on_the_list_once(
    tmp_path: Path, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = workspace(tmp_path / "shop")
    assert lem(capsys, where.checkout, *OPEN)["code"] == 0
    assert workspaces.listed(home) == (str(where.checkout.resolve()),)
    # the same open again is a retry: it passes, and the list holds the checkout once
    assert lem(capsys, where.checkout, *OPEN)["code"] == 0
    assert workspaces.listed(home) == (str(where.checkout.resolve()),)


def test_a_read_that_queues_a_task_puts_its_repository_on_the_list_from_its_worktree(
    tmp_path: Path, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    other = workspace(tmp_path / "other")
    workspaces.changed(home, str(other.checkout.resolve()), add=True)
    where = workspace(tmp_path / "shop")
    tasks.create(where.state, record("dates", status="building"))
    tasks.create(where.state, record(SLUG, status="shaping"))
    assert lem(capsys, worktree_of(where), *READ)["code"] == 0
    assert read(where, SLUG).task.status == "queued"
    assert workspaces.listed(home) == (
        str(other.checkout.resolve()),
        str(where.checkout.resolve()),
    )


def test_a_wrong_call_a_refused_workspace_and_no_settings_write_no_list(
    tmp_path: Path, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = workspace(tmp_path / "shop")
    wrong = lem(capsys, where.checkout, "task", "open", SLUG)
    assert wrong["code"] == 2
    old = workspace(tmp_path / "old")
    (old.state / folders.MARKER).unlink()
    (old.state / "events.jsonl").write_text('{"event": "task.open"}\n')
    refused = lem(capsys, old.checkout, *OPEN)
    assert (refused["code"], code_of(refused)) == (1, "old-state")
    bare = workspace(tmp_path / "bare")
    (bare.lem / "settings.toml").unlink()
    lem(capsys, bare.checkout, "task", "list")
    assert not (home / workspaces.WORKSPACES).exists()


@pytest.mark.parametrize("made", ["home", "no-home"])
def test_a_list_that_cannot_be_written_refuses_before_the_command_does_anything(
    tmp_path: Path, home: Path, capsys: pytest.CaptureFixture[str], made: str
) -> None:
    where = workspace(tmp_path / "shop")
    shut = home if made == "home" else home.parent
    if made == "home":
        folders.home_marked(home)
    else:
        shut.mkdir(parents=True)
    shut.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        refused = lem(capsys, where.checkout, *OPEN)
    finally:
        shut.chmod(stat.S_IRWXU)
    assert (refused["code"], code_of(refused)) == (1, "workspaces-write")
    assert not (where.state / "tasks" / SLUG).exists()
    assert workspaces.listed(home) == ()
