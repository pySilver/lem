"""`lem task worktree` on real git: the worktree on its branch cut from origin's base, taken as
it is when it is there, a branch origin has refused, `checks.setup` run once with its log, and
its path alone."""

from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from fakes.repo import RealRepo
from lem.app.tasks import ports, worktree
from lem.kernel.errors import Refusal
from lem.records.task import Shape
from unit.task.spaces import SETTINGS, made, read, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

SLUG = "gift-note"
SHAPE = Shape(type="feat", why="a new note", track="small")


def real(tmp_path: Path, settings: str = SETTINGS) -> tuple[RealRepo, Workspace]:
    """A workspace over a real repository with an origin, and its shaped task."""
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    where = workspace(repo.checkout, settings)
    made(where, SLUG, status="building", shape=SHAPE)
    return repo, where


def test_the_worktree_is_cut_from_origins_base_on_type_slug(tmp_path: Path) -> None:
    repo, where = real(tmp_path)
    repo.outside_commit("main", {"NEWS.md": b"news\n"})
    ran = lem("task", "worktree", SLUG, cwd=repo.checkout)
    made_tree = result(ran)
    path = where.lem / "worktrees" / SLUG
    assert (made_tree["worktree"], made_tree["branch"], made_tree["made"]) == (
        str(path),
        f"feat/{SLUG}",
        True,
    )
    assert (path / "NEWS.md").is_file()
    assert read(where, SLUG).task.branch == f"feat/{SLUG}"
    assert (where.lem / "worktrees" / ".gitignore").read_text(encoding="utf-8") == "*\n"
    again = result(lem("task", "worktree", SLUG, cwd=repo.checkout))
    assert again.get("made", False) is False


def test_its_path_alone_makes_nothing(tmp_path: Path) -> None:
    repo, where = real(tmp_path)
    ran = lem("task", "worktree", SLUG, "--path", cwd=repo.checkout)
    assert result(ran)["worktree"] == str(where.lem / "worktrees" / SLUG)
    assert not (where.lem / "worktrees" / SLUG).exists()


def test_a_branch_origin_has_and_no_task_holds_is_refused(tmp_path: Path) -> None:
    repo, where = real(tmp_path)
    repo.outside_commit(f"feat/{SLUG}", {"THEIRS.md": b"x\n"})
    record = read(where, SLUG)
    with pytest.raises(Refusal) as refused:
        worktree.made(ports.bound(where), where, record, (None, None))
    assert refused.value.code == "branch-taken"


@pytest.mark.parametrize("branch", ["main", "release"])
def test_the_base_or_a_protected_branch_is_refused(tmp_path: Path, branch: str) -> None:
    settings = f'{SETTINGS}protected = ["release"]\n'
    repo, _where = real(tmp_path, settings)
    ran = lem("task", "worktree", SLUG, "--branch", branch, cwd=repo.checkout)
    assert refusal(ran)["code"] == "protected"


def test_checks_setup_runs_once_in_the_new_worktree_with_its_log(
    tmp_path: Path,
) -> None:
    settings = f'{SETTINGS}[checks]\nsetup = ["echo ready > made.txt"]\n'
    repo, where = real(tmp_path, settings)
    ran = result(lem("task", "worktree", SLUG, cwd=repo.checkout))
    assert ran["setup"] == [{"command": "echo ready > made.txt", "exit": 0}]
    assert (where.lem / "worktrees" / SLUG / "made.txt").is_file()
    log = where.state / "tasks" / SLUG / "setup.log"
    assert log.read_text(encoding="utf-8").startswith("$ echo ready > made.txt\n")


def test_a_setup_that_fails_is_refused_and_the_worktree_stays(tmp_path: Path) -> None:
    settings = f'{SETTINGS}[checks]\nsetup = ["exit 3", "echo never"]\n'
    repo, where = real(tmp_path, settings)
    ran = lem("task", "worktree", SLUG, cwd=repo.checkout)
    refused = refusal(ran)
    assert (refused["code"], "exit 3" in refused["why"]) == ("setup", True)
    assert (where.lem / "worktrees" / SLUG / "README.md").is_file()
    log = (where.state / "tasks" / SLUG / "setup.log").read_text(encoding="utf-8")
    assert "never" not in log


def test_another_checkout_is_named_with_repo(tmp_path: Path) -> None:
    repo, _where = real(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    ran = lem("task", "worktree", SLUG, "--checkout", str(other), cwd=repo.checkout)
    assert refusal(ran)["code"] == "checkout"
