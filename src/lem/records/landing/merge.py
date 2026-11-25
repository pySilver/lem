"""The merge and what follows it: a refusal, the intent before the forge call, the forge's
acceptance, the merge, and the cleanup (`landing.md` A, C and E).

A merge is an intent before the forge call; under the merge lock an intent is reconciled with
what the forge shows before any new call: replaced by `Merged`, `MergeAccepted` or a definite
`Refused`, or kept while only an open pull request is visible.
"""

from typing import Literal

from lem.records.base import Frozen, Moment, Sha

type Merger = Literal["owner", "merger"]
# Where a merge was asked for; `github` is a merge someone made on GitHub, which Lem saw.
type Via = Literal["session", "server", "board", "github"]


class Refused(Frozen, frozen=True, kw_only=True):
    """A merge refused, by the forge or by Lem: the tip, the kind, the line as said, and who
    asked for the merge."""

    tip: Sha
    source: Literal["github", "lem"]
    kind: Literal["rule", "tip", "base", "target"]
    line: str
    by: Merger
    at: Moment


class MergeIntent(Frozen, frozen=True, kw_only=True):
    """A merge call about to go to the forge, written under the merge lock before the call."""

    tip: Sha
    by: Merger
    via: Via
    at: Moment


class MergeAccepted(Frozen, frozen=True, kw_only=True):
    """The forge took the call and the pull request is not merged yet; `queued` is the forge's
    own word for the wait (a merge queue, an automatic merge)."""

    tip: Sha
    at: Moment
    queued: str


class Merged(Frozen, frozen=True, kw_only=True):
    """The merge: who and how, the merge commit, the forge's head at the merge and the parent
    on the base, the destination the forge reports, what the checks and the read covered of
    the base, what they did not, the base checkout left behind, and whether the pull request's
    text was updated."""

    by: Merger
    via: Via
    commit: Sha
    merged_head: Sha
    parent: Sha
    destination: str
    base_checked: Sha
    base_merged: Sha
    base_read: Sha | None = None
    uncovered: str | None = None
    left_behind: str | None = None
    text_updated: bool = True
    at: Moment


class Cleaned(Frozen, frozen=True, kw_only=True):
    """`clean`: what went (the worktree, the branch, the forge's copy) and what stayed, with
    the rebase that made a divergent local branch."""

    worktree_gone: bool
    branch_gone: bool
    forge_branch_gone: bool
    branch_left: str | None = None
    rebased: bool = False
    at: Moment
