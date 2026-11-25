"""`LocalForge` against the `Forge` port's contract, over `ModelGit` and over a real repository,
and what it does besides, as GitHub would: a queue, a rule, a merge by another hand, a retarget,
a close, a lagging report and a failed edit."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from contract.suites.forge import TEXT, ForgeContract
from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.repo import RealRepo
from lem.ports.faults import Unanswered
from lem.ports.forge_facts import MergeDenied, MergeDone, MergeOutcome, MergeTaken

if TYPE_CHECKING:
    from pathlib import Path

FILES = {"README.md": b"one\n"}


@dataclass(frozen=True)
class LocalWorld:
    """A `LocalForge` over a remote a test pushes to."""

    forge: LocalForge
    remote: ModelGit | RealRepo

    def push(self, branch: str, files: dict[str, bytes | None]) -> str:
        return self.remote.outside_commit(branch, files)

    def head(self, branch: str) -> str | None:
        return self.remote.head_of(branch)

    def settle(self, number: int, outcome: MergeOutcome) -> MergeOutcome:
        return self.forge.settle(number) if isinstance(outcome, MergeTaken) else outcome


class TestLocalForgeOverModelGit(ForgeContract):
    def world(self, folder: Path) -> LocalWorld:
        remote = ModelGit.init(folder / "checkout", dict(FILES))
        return LocalWorld(forge=LocalForge(remote=remote), remote=remote)


class TestLocalForgeOverRealGit(ForgeContract):
    def world(self, folder: Path) -> LocalWorld:
        remote = RealRepo.init(folder, dict(FILES))
        return LocalWorld(forge=LocalForge(remote=remote), remote=remote)


class TestLocalForgeInAQueue(ForgeContract):
    def world(self, folder: Path) -> LocalWorld:
        remote = ModelGit.init(folder / "checkout", dict(FILES))
        return LocalWorld(forge=LocalForge(remote=remote, queue=True), remote=remote)


def opened(
    tmp_path: Path,
    *,
    queue: bool = False,
    refuse: str | None = None,
    lag: int = 0,
    fail_edits: bool = False,
) -> tuple[LocalForge, ModelGit, str]:
    """A forge with one open pull request, number 1, and its head."""
    remote = ModelGit.init(tmp_path / "checkout", dict(FILES))
    forge = LocalForge(
        remote=remote, queue=queue, refuse=refuse, lag=lag, fail_edits=fail_edits
    )
    head = remote.outside_commit("fix-the-login", {"a.txt": b"a\n"})
    forge.open_pull("fix-the-login", "main", "Fix the login", "body")
    return forge, remote, head


def test_a_queued_merge_is_taken_then_merged_when_the_queue_reaches_it(
    tmp_path: Path,
) -> None:
    forge, remote, head = opened(tmp_path, queue=True)
    assert forge.merge(1, head, "squash", TEXT) == MergeTaken(queued="the merge queue")
    waiting = forge.pull(1)
    assert (waiting.state, waiting.queued) == ("open", "the merge queue")
    done = forge.settle(1)
    assert isinstance(done, MergeDone)
    assert remote.head_of("main") == done.commit
    assert forge.merge_calls == [(1, head)]


def test_a_rule_of_the_base_refuses_in_githubs_words(tmp_path: Path) -> None:
    forge, _remote, head = opened(tmp_path, refuse="Required status check is expected")
    assert forge.merge(1, head, "squash", TEXT) == MergeDenied(
        kind="rule", said="Required status check is expected"
    )


def test_another_hand_a_retarget_and_a_close_show_in_the_report(tmp_path: Path) -> None:
    forge, _remote, head = opened(tmp_path)
    forge.retarget(1, "release")
    assert forge.pull(1).base == "release"
    forge.retarget(1, "main")
    assert isinstance(forge.outside_merge(1), MergeDone)
    merged = forge.pull(1)
    assert (merged.state, merged.merged_head) == ("merged", head)
    assert isinstance(forge.merge(1, head, "squash", TEXT), MergeDenied)
    second, _remote, _head = opened(tmp_path / "second")
    second.close(1)
    assert second.pull(1).state == "closed"


def test_a_lagging_report_shows_the_pull_request_open_after_its_merge(
    tmp_path: Path,
) -> None:
    forge, _remote, head = opened(tmp_path, lag=2)
    assert isinstance(forge.merge(1, head, "squash", TEXT), MergeDone)
    assert [forge.pull(1).state for _ in range(3)] == ["open", "open", "merged"]


def test_a_conflicting_merge_is_refused_for_the_base(tmp_path: Path) -> None:
    forge, remote, _head = opened(tmp_path)
    clash = remote.outside_commit("clash", {"README.md": b"theirs\n"})
    forge.open_pull("clash", "main", "Clash", "body")
    remote.outside_commit("main", {"README.md": b"ours\n"})
    assert forge.merge(2, clash, "merge", TEXT) == MergeDenied(
        kind="base", said="the merge has conflicts"
    )
    assert forge.pull(2).mergeable == "conflicting"


def test_a_failed_edit_keeps_the_text_before(tmp_path: Path) -> None:
    forge, _remote, _head = opened(tmp_path, fail_edits=True)
    with pytest.raises(Unanswered, match="502"):
        forge.update_pull(1, "Fixed", "the new text")
    assert forge.bodies[1] == "body"


def test_the_queue_merges_only_the_head_it_took_of_a_request_still_open(
    tmp_path: Path,
) -> None:
    forge, remote, head = opened(tmp_path, queue=True)
    base = remote.head_of("main")
    assert isinstance(forge.merge(1, head, "squash", TEXT), MergeTaken)
    remote.outside_commit("fix-the-login", {"a.txt": b"later\n"})
    assert forge.settle(1) == MergeDenied(kind="tip", said="Head branch was modified")
    removed = forge.pull(1)
    assert (removed.state, removed.queued, removed.dequeued) == (
        "open",
        None,
        "the head moved after the merge was queued",
    )
    assert remote.head_of("main") == base
    plain, _remote, _head = opened(tmp_path / "plain")
    assert (plain.pull(1).queued, plain.pull(1).dequeued) == (None, None)


def test_the_queue_does_not_merge_a_closed_request_and_says_so(tmp_path: Path) -> None:
    forge, remote, head = opened(tmp_path, queue=True)
    base = remote.head_of("main")
    forge.merge(1, head, "squash", TEXT)
    forge.close(1)
    assert isinstance(forge.settle(1), MergeDenied)
    assert forge.pull(1).dequeued == "the pull request was closed"
    assert remote.head_of("main") == base


def test_a_queue_that_removes_a_request_says_why(tmp_path: Path) -> None:
    forge, _remote, head = opened(tmp_path, queue=True)
    forge.merge(1, head, "squash", TEXT)
    forge.dequeue(1, "a required check failed")
    assert (forge.pull(1).queued, forge.pull(1).dequeued) == (
        None,
        "a required check failed",
    )


def test_a_rebase_merge_replays_each_commit_onto_the_base(tmp_path: Path) -> None:
    forge, remote, _head = opened(tmp_path)
    second = remote.outside_commit("fix-the-login", {"b.txt": b"b\n"})
    base = remote.head_of("main")
    done = forge.merge(1, second, "rebase", TEXT)
    assert isinstance(done, MergeDone)
    assert done.base_parent == base
    tip = remote.objects[done.commit]
    assert len(tip.parents) == 1
    assert remote.objects[tip.parents[0]].parents == (base,)
