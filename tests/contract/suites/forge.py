"""The contract of the `Forge` port: what every implementation does, `LocalForge` now and the
`gh` adapter when `land-propose` builds it (against a scratch repository, trial S3).

A test file subclasses `ForgeContract` as `Test...` and gives `world`: a forge over a remote
with one commit on `main`, a hand that pushes a branch as someone else, and a look at a branch of
the remote that does not go through the forge. A forge that merges
through a queue gives `MergeTaken` where these cases expect `MergeDone`; `settle` then finishes
the merge, as the queue would.
"""

from typing import TYPE_CHECKING, Protocol

import pytest

from lem.ports.forge_facts import MergeDenied, MergeDone, MergeOutcome, MergeText

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.forge import Forge

TEXT = MergeText(subject="Fix the login", body="The login works again.")


class ForgeWorld(Protocol):
    """A forge for one case."""

    @property
    def forge(self) -> Forge: ...

    def push(self, branch: str, files: dict[str, bytes | None]) -> str: ...
    def head(self, branch: str) -> str | None: ...
    def settle(self, number: int, outcome: MergeOutcome) -> MergeOutcome: ...


class ForgeContract:
    """The cases every implementation of `Forge` passes."""

    def world(self, folder: Path) -> ForgeWorld:
        """A fresh forge in `folder`."""
        raise NotImplementedError

    def test_an_opened_pull_request_is_found_by_its_branch_with_its_head(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        head = world.push("fix-the-login", {"a.txt": b"a\n"})
        opened = world.forge.open_pull("fix-the-login", "main", "Fix the login", "body")
        assert (opened.state, opened.head, opened.base) == ("open", head, "main")
        found = world.forge.find_pulls("fix-the-login", "main")
        assert [(pull.number, pull.head) for pull in found] == [(opened.number, head)]
        assert world.forge.find_pulls("fix-the-login", "elsewhere") == ()
        assert opened.number in {pull.number for pull in world.forge.open_pulls()}
        assert world.forge.pull(opened.number).url == opened.url
        assert opened.author
        assert world.forge.pull(opened.number).author == opened.author
        assert world.forge.repo().name.count("/") == 1

    def test_a_pull_requests_head_follows_its_branch(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        world.push("fix-the-login", {"a.txt": b"a\n"})
        opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
        moved = world.push("fix-the-login", {"a.txt": b"b\n"})
        assert world.forge.pull(opened.number).head == moved

    def test_its_title_changes_and_a_second_one_for_the_branch_is_refused(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        world.push("fix-the-login", {"a.txt": b"a\n"})
        opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
        updated = world.forge.update_pull(opened.number, "Fixed", "new body")
        assert (updated.title, updated.body) == ("Fixed", "new body")
        assert world.forge.pull(opened.number).body == "new body"
        with pytest.raises(Exception, match="already exists"):
            world.forge.open_pull("fix-the-login", "main", "Again", "body")

    def test_a_merge_with_a_head_that_moved_is_refused_and_merges_nothing(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        reviewed = world.push("fix-the-login", {"a.txt": b"a\n"})
        opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
        world.push("fix-the-login", {"a.txt": b"moved\n"})
        refused = world.forge.merge(opened.number, reviewed, "squash", TEXT)
        assert isinstance(refused, MergeDenied)
        assert refused.kind == "tip"
        assert world.forge.pull(opened.number).state == "open"

    def test_a_merge_at_the_head_merges_and_reports_the_head_and_destination(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        head = world.push("fix-the-login", {"a.txt": b"a\n"})
        base = world.head("main")
        opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
        outcome = world.settle(
            opened.number, world.forge.merge(opened.number, head, "squash", TEXT)
        )
        assert isinstance(outcome, MergeDone)
        assert outcome.merged_head == head
        assert outcome.base_parent == base
        merged = world.forge.pull(opened.number)
        assert (merged.state, merged.base, merged.merged_head) == (
            "merged",
            "main",
            head,
        )
        assert (merged.merge_commit, merged.base_parent) == (outcome.commit, base)
        assert world.head("main") == outcome.commit
        assert opened.number not in {pull.number for pull in world.forge.open_pulls()}

    def test_a_branch_copy_is_deleted_only_at_the_commit_named(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        first = world.push("fix-the-login", {"a.txt": b"a\n"})
        second = world.push("fix-the-login", {"a.txt": b"b\n"})
        assert not world.forge.delete_ref("refs/heads/fix-the-login", first)
        assert world.head("fix-the-login") == second
        assert world.forge.delete_ref("refs/heads/fix-the-login", second)
        assert world.head("fix-the-login") is None
