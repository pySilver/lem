"""`checks`: the project's commands on a tip, the criteria's check, the bar and the size
(`landing.md` A, `Checked`)."""

from typing import Literal

from lem.records.base import Frozen, Moment, Sha, TaskPath


class Outcome(Frozen, frozen=True, kw_only=True):
    """One command's run: its exit, its last line, its whole output, whether it passed, and
    whether it ran under the serial lock."""

    command: str
    exit: int
    last: str
    output: TaskPath
    passed: bool
    serial: bool = False


class CriterionCheck(Frozen, frozen=True, kw_only=True):
    """One criterion's tests: red on the base and green on the tip, or taken from the polish
    pass's run at `taken_at`."""

    criterion: int
    red_on_base: bool
    green_on_tip: bool
    taken_at: Sha | None = None


class Lowered(Frozen, frozen=True, kw_only=True):
    """A file whose bar the change lowered (a removed test, an assertion loosened): the marked
    line (160 characters at most, `land.bar_of` on `main`), the builder's reason, and the
    reviewer's answer to it, which `land.not_green` on `main` shows beside it."""

    path: str
    how: str
    line: str | None = None
    reason: str | None = None
    reviewer: str | None = None


class ChangeSize(Frozen, frozen=True, kw_only=True):
    """The change's size: files, lines, and whether it came in parts."""

    files: int
    lines: int
    in_parts: bool = False


class Removed(Frozen, frozen=True, kw_only=True):
    """What `checks` removed from the worktree before it ran: untracked files and bytecode."""

    untracked: tuple[str, ...] = ()
    bytecode: tuple[str, ...] = ()


class Edited(Frozen, frozen=True, kw_only=True):
    """An existing file of the tests that the change edits, and its kind."""

    path: str
    kind: Literal["snapshot", "test configuration", "test"]


class Checked(Frozen, frozen=True, kw_only=True):
    """`checks` on a tip: its tree, its base and the base's tree, one digest of the inputs that
    make a passed run hold no more (the commands and the serial ones, `land.same_checks` on
    `main`), the criteria's contract mark it ran under, each command's outcome, the criteria,
    the bar with the existing tests the change edits and the kinds of file it has no marks
    for, the size, whether the change brought its own checks, what was removed, and the backlog
    items `file` committed after."""

    tip: Sha
    tree: Sha
    base: Sha
    base_tree: Sha | None = None
    inputs: str
    contract: str | None = None
    outcome: Literal["passed", "red", "refused", "stopped"]
    outcomes: tuple[Outcome, ...] = ()
    criteria: tuple[CriterionCheck, ...] = ()
    lowered: tuple[Lowered, ...] = ()
    edited: tuple[Edited, ...] = ()
    not_covered: tuple[str, ...] = ()
    size: ChangeSize | None = None
    own_checks: bool = False
    removed: Removed | None = None
    items_after: tuple[str, ...] = ()
    at: Moment
