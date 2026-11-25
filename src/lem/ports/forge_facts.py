"""What the `Forge` port gives back: the repository, a pull request as the forge reports it,
and the three outcomes of a merge call."""

from typing import Literal

from lem.records.base import Frozen, Sha

type Mergeable = Literal["mergeable", "conflicting", "unknown"]
type MergeMethod = Literal["squash", "merge", "rebase"]


class Repo(Frozen, frozen=True, kw_only=True):
    """The repository on the forge: `OWNER/NAME` and its address."""

    name: str
    url: str


class Pull(Frozen, frozen=True, kw_only=True):
    """A pull request as the forge reports it now: its state, who opened it (the forge's
    login, `author.login` of gh), its text as it stands (an edit keeps what the owner changed
    in it, `land.noted` on `main`), head and base (the
    destination, from the forge itself), whether it can merge, the forge's word for a queued
    merge or for its removal from the queue and why, and once merged: the merge commit, the
    head it merged, and the commit of the base it went onto (the merge commit's first parent
    for a squash or a merge, the parent before the first replayed commit for a rebase,
    `land.moved_line` on `main`)."""

    number: int
    url: str
    title: str
    body: str = ""
    state: Literal["open", "closed", "merged"]
    author: str | None = None
    head: Sha
    head_ref: str
    base: str
    mergeable: Mergeable = "unknown"
    queued: str | None = None
    dequeued: str | None = None
    merge_commit: Sha | None = None
    merged_head: Sha | None = None
    base_parent: Sha | None = None


class MergeText(Frozen, frozen=True, kw_only=True):
    """The merge commit's subject and body."""

    subject: str
    body: str


class MergeDone(Frozen, frozen=True, kw_only=True):
    """The forge merged: the merge commit, the head it merged, and the commit of the base it
    went onto (as `Pull.base_parent`)."""

    commit: Sha
    merged_head: Sha
    base_parent: Sha


class MergeTaken(Frozen, frozen=True, kw_only=True):
    """The forge took the call and has not merged yet: its own word for the wait."""

    queued: str


class MergeDenied(Frozen, frozen=True, kw_only=True):
    """The forge refused the call: a rule of the base branch, a head that moved, or a base the
    merge cannot take; its words as said."""

    kind: Literal["rule", "tip", "base"]
    said: str


type MergeOutcome = MergeDone | MergeTaken | MergeDenied
