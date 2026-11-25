"""The remotes a forge fake merges through, `ModelGit` and a real repository
(`fakes.repo.RealRepo`): each of the forge's three merges gives the same history on both, and a
rebase merge drops a merge commit with the edit only it made, as git does."""

from typing import TYPE_CHECKING, Protocol

import pytest

from fakes.forge import Remote
from fakes.git import Landed, ModelGit
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
    def outside_merge_commit(
        self, branch: str, other: str, files: dict[str, bytes]
    ) -> str: ...


def model(folder: Path) -> ModelGit:
    """A `ModelGit` with one commit of `FILES`."""
    return ModelGit.init(folder / "checkout", dict(FILES))


def real(folder: Path) -> RealRepo:
    """A real repository with one commit of `FILES`."""
    return RealRepo.init(folder, dict(FILES))


MAKERS = pytest.mark.parametrize("make", [model, real], ids=["model", "real"])


def parents_of(remote: Shared, sha: str, folder: Path) -> tuple[str, ...]:
    """The parents of a commit on the remote."""
    if isinstance(remote, ModelGit):
        return remote.objects[sha].parents
    assert isinstance(remote, RealRepo)
    listed = run_git(remote.origin, "rev-list", "--parents", "-n", "1", sha)
    return tuple(listed.split()[1:])


def show(remote: Shared, sha: str, path: str) -> bytes | None:
    """A file of a commit on the remote."""
    if isinstance(remote, ModelGit):
        return remote.objects[sha].tree.get(path)
    assert isinstance(remote, RealRepo)
    listed = run_git(remote.origin, "ls-tree", "--name-only", sha, path)
    if not listed:
        return None
    return (run_git(remote.origin, "show", f"{sha}:{path}") + "\n").encode()


@MAKERS
def test_a_squash_a_merge_and_a_rebase_each_report_the_base_they_went_onto(
    tmp_path: Path, make: Callable[[Path], Shared]
) -> None:
    remote = make(tmp_path)
    remote.outside_commit("topic", {"a.txt": b"a\n"})
    head = remote.outside_commit("topic", {"b.txt": b"b\n"})
    base = remote.head_of("main")
    assert base is not None
    squashed = remote.merge_into("main", head, method="squash", message="squash (#1)")
    assert isinstance(squashed, Landed)
    assert (squashed.base_parent, parents_of(remote, squashed.commit, tmp_path)) == (
        base,
        (base,),
    )
    second = remote.outside_commit("next", {"c.txt": b"c\n"}, start="main")
    before = remote.head_of("main")
    assert before is not None
    joined = remote.merge_into("main", second, method="merge", message="merge (#2)")
    assert isinstance(joined, Landed)
    assert parents_of(remote, joined.commit, tmp_path) == (before, second)
    remote.outside_commit("third", {"d.txt": b"d\n"}, start="main")
    third = remote.outside_commit("third", {"e.txt": b"e\n"})
    onto = remote.head_of("main")
    replayed = remote.merge_into("main", third, method="rebase", message="unused")
    assert isinstance(replayed, Landed)
    assert replayed.base_parent == onto
    first = parents_of(remote, replayed.commit, tmp_path)
    assert first != (onto,)
    assert parents_of(remote, first[0], tmp_path) == (onto,)
    assert remote.head_of("main") == replayed.commit


@MAKERS
def test_a_rebase_merge_drops_a_merge_commit_and_the_edit_only_it_made(
    tmp_path: Path, make: Callable[[Path], Shared]
) -> None:
    remote = make(tmp_path)
    remote.outside_commit("topic", {"a.txt": b"a\n"})
    remote.outside_commit("main", {"other.txt": b"o\n"})
    head = remote.outside_merge_commit("topic", "main", {"merge-only.txt": b"m\n"})
    assert show(remote, head, "merge-only.txt") == b"m\n"
    replayed = remote.merge_into("main", head, method="rebase", message="unused")
    assert isinstance(replayed, Landed)
    assert show(remote, replayed.commit, "a.txt") == b"a\n"
    assert show(remote, replayed.commit, "merge-only.txt") is None


@MAKERS
def test_a_conflicting_merge_is_a_conflict_on_both(
    tmp_path: Path, make: Callable[[Path], Shared]
) -> None:
    remote = make(tmp_path)
    clash = remote.outside_commit("clash", {"README.md": b"theirs\n"})
    remote.outside_commit("main", {"README.md": b"ours\n"})
    for method in ("squash", "merge", "rebase"):
        assert remote.merge_into("main", clash, method=method, message="m") == Conflict(
            files=("README.md",)
        )


@MAKERS
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
