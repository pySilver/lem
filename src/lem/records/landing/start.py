"""The landing's first steps: `start`, `base` with a conflict's resolution, and the polish pass
(`landing.md` A)."""

from typing import Literal

from lem.records.base import Frozen, Moment, Sha, TaskPath


class Started(Frozen, frozen=True, kw_only=True):
    """`start` of a round: the branch, the base it lands on, whether a conflict on the forge
    woke it, and why the landing started over, if it did."""

    round: int
    branch: str
    base_ref: str
    conflicting: bool = False
    start_over: str | None = None
    at: Moment


class Based(Frozen, frozen=True, kw_only=True):
    """`base`: the tip after the rebase onto `base`, the tip before it, whether the review and
    checks carried over it and the reviewed tip that carry was judged for, and what the rebase
    changed that no review has shown."""

    tip: Sha
    base: Sha
    before: Sha
    carried: bool
    reviewed: Sha | None = None
    unshown_paths: tuple[str, ...] = ()
    unshown_commits: tuple[Sha, ...] = ()
    at: Moment


class Resolution(Frozen, frozen=True, kw_only=True):
    """A builder's resolution of a conflict with the base: the files, the tips before and
    after, the base it was made on, and the review attempt that read it."""

    files: tuple[str, ...]
    before: Sha
    after: Sha
    base: Sha
    read: int | None = None


class PassRun(Frozen, frozen=True, kw_only=True):
    """The test run of the polish pass: its five inputs as one digest, and its outcome."""

    inputs: str
    outcome: Literal["passed", "red", "refused", "stopped"]
    tip: Sha


class Polished(Frozen, frozen=True, kw_only=True):
    """The polish pass of the standard track: the tips before and after, its commits, what it
    filed, and its test run, which `checks` may take."""

    before: Sha
    after: Sha | None = None
    commits: int = 0
    filed: tuple[TaskPath, ...] = ()
    run: PassRun | None = None
    report: TaskPath | None = None
    at: Moment
