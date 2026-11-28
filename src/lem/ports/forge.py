"""The `Forge` port: the pull requests of the repository on GitHub (the design's part 4).

`merge` pins only the head: a retarget after the read is a race no client can close, so the
caller checks the destination `pull` reports after every merge (`landing.md` H 2). An update with
no title changes the body alone, so that a title the owner gave on the forge stays, and gives
the pull request as the forge holds it after the edit. A ref is deleted by its full name, only
at the commit named.
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from lem.ports.forge_facts import (
        MergeMethod,
        MergeOutcome,
        MergeText,
        Pull,
        Repo,
    )
    from lem.records.base import Sha


class ForgePulls(Protocol):
    """The pull requests, and the merge."""

    def repo(self) -> Repo: ...
    def find_pulls(self, head: str, base: str | None) -> tuple[Pull, ...]: ...
    def open_pull(self, head: str, base: str, title: str, body: str) -> Pull: ...
    def update_pull(self, number: int, title: str | None, body: str) -> Pull: ...
    def pull(self, number: int) -> Pull: ...
    def open_pulls(self) -> tuple[Pull, ...]: ...
    def merge(
        self,
        number: int,
        expected_head: Sha,
        method: MergeMethod,
        text: MergeText,
    ) -> MergeOutcome: ...


class ForgeRefs(Protocol):
    """The forge's branches: the delete of a task branch's copy, with a lease, and every open
    pull request whose base is a branch, each one or a fault, never a page of them."""

    def delete_ref(self, name: str, expect: Sha) -> bool: ...
    def pulls_into(self, branch: str) -> tuple[Pull, ...]: ...


class Forge(ForgePulls, ForgeRefs, Protocol):
    """The whole port."""
