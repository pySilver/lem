"""The real repository the steps that need real git build on (`fakes.repo.RealRepo`): its
remote acts give what the forge's merge gives, as `ModelGit`'s do."""

from typing import TYPE_CHECKING, Protocol

import pytest

from fakes.forge import Remote
from fakes.git import ModelGit
from fakes.repo import RealRepo, run_git
from lem.ports.git_facts import Conflict

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

FILES = {"README.md": b"one\n"}


class Shared(Remote, Protocol):
    """A remote a test can also push to as someone else."""

    def outside_commit(
        self, branch: str, files: dict[str, bytes | None], start: str = "main"
    ) -> str: ...


def model(folder: Path) -> ModelGit:
    """A `ModelGit` with one commit of `FILES`."""
    return ModelGit.init(folder / "checkout", dict(FILES))


def real(folder: Path) -> RealRepo:
    """A real repository with one commit of `FILES`."""
    return RealRepo.init(folder, dict(FILES))


@pytest.mark.parametrize("make", [model, real], ids=["model", "real"])
def test_a_merge_on_the_remote_squashes_or_keeps_the_head(
    tmp_path: Path, make: Callable[[Path], Shared]
) -> None:
    remote = make(tmp_path)
    head = remote.outside_commit("topic", {"a.txt": b"a\n"})
    base = remote.head_of("main")
    squashed = remote.merge_into("main", head, squash=True, message="squash (#1)")
    assert isinstance(squashed, str)
    assert remote.head_of("main") == squashed
    assert squashed not in {head, base}
    conflict = remote.outside_commit("clash", {"README.md": b"theirs\n"})
    remote.outside_commit("main", {"README.md": b"ours\n"})
    assert remote.merge_into("main", conflict, squash=False, message="m") == Conflict(
        files=("README.md",)
    )


@pytest.mark.parametrize("make", [model, real], ids=["model", "real"])
def test_a_remote_branch_is_deleted_only_at_the_commit_named(
    tmp_path: Path, make: Callable[[Path], Shared]
) -> None:
    remote = make(tmp_path)
    head = remote.outside_commit("topic", {"a.txt": b"a\n"})
    base = remote.head_of("main")
    assert base is not None
    assert not remote.delete_remote("topic", base)
    assert remote.head_of("topic") == head
    assert remote.delete_remote("topic", head)
    assert remote.head_of("topic") is None


def test_a_real_repository_reads_no_setting_of_the_machine(tmp_path: Path) -> None:
    repo = real(tmp_path)
    assert run_git(repo.checkout, "log", "-1", "--format=%an <%ae>") == (
        "Lem Test <test@example.com>"
    )
