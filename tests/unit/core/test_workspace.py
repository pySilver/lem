"""The workspace of a call: the main checkout of the folder it starts from, from a task's
worktree too, and its `.lem/`; a folder in no repository, or in one with no Lem, is refused."""

from typing import TYPE_CHECKING

import pytest

from fakes.repo import RealRepo, run_git
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path


def test_the_workspace_is_the_main_checkout_from_a_worktree_and_a_folder_in_it(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n", "src/a.py": b"a\n"})
    (repo.checkout / ".lem").mkdir()
    worktree = repo.checkout / ".lem" / "worktrees" / "fix-the-login"
    run_git(
        repo.checkout,
        "worktree",
        "add",
        "--quiet",
        "-b",
        "fix-the-login",
        str(worktree),
    )
    checkout = repo.checkout.resolve()
    for start in (repo.checkout, repo.checkout / "src", worktree, worktree / "src"):
        found = places.workspace(start)
        assert found == places.Workspace(
            checkout=checkout, lem=checkout / ".lem", state=checkout / ".lem" / "state"
        )
    assert run_git(worktree, "worktree", "list", "--porcelain").splitlines()[0] == (
        f"worktree {checkout}"
    )


def test_a_folder_in_no_repository_or_one_with_no_lem_is_refused(
    tmp_path: Path,
) -> None:
    with pytest.raises(Refusal) as nowhere:
        places.workspace(tmp_path)
    assert nowhere.value.code == "no-repository"
    assert "lem --repo PATH" in nowhere.value.fix
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    with pytest.raises(Refusal) as bare:
        places.workspace(repo.checkout)
    assert bare.value.code == "no-lem"
    assert bare.value.fix.startswith("lem init --base BRANCH")


def test_the_checkout_of_a_folder_needs_no_lem_and_is_found_from_a_worktree(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    worktree = tmp_path / "fix-the-login"
    run_git(repo.checkout, "worktree", "add", "--quiet", "-b", "fix", str(worktree))
    checkout = repo.checkout.resolve()
    assert places.checkout_of(repo.checkout) == checkout
    assert places.checkout_of(worktree) == checkout
    with pytest.raises(Refusal) as nowhere:
        places.checkout_of(tmp_path)
    assert nowhere.value.code == "no-repository"
