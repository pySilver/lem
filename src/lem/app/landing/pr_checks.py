"""The checks in the pull request's text (`main:land.pr_text`, `criteria_check_line`,
`polished`): each command with what it returned, the check of the criteria, the polish pass,
the cause a bug's investigation found, the bar, and the size of the change."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.landing.checks import Checked, Lowered, Outcome
    from lem.records.record import Record

SHORT = 9
NO_BAR = "- the bar: no mark of a lowered bar found"


def command_line(outcome: Outcome) -> str:
    """A command with what it returned last, or its exit when it printed nothing."""
    serial = " (serial, under the lock)" if outcome.serial else ""
    said = outcome.last or f"exit {outcome.exit}"
    return f"- check, `{outcome.command}`{serial}: {said}"


def commands(checked: Checked | None) -> Lines:
    """Each command of the checks, in the order they ran."""
    return tuple(map(command_line, checked.outcomes if checked else ()))


def cause(record: Record, *, before: bool) -> Lines:
    """The cause a bug's investigation found, with its place; none for a question."""
    found = record.task.investigation
    if found is None or found.kind != "fix" or not found.line:
        return ()
    where = f" ({found.where})" if found.where else ""
    when = " before the build" if before else ""
    return (f"- the cause, as the investigation{when} found it: {found.line}{where}",)


def lowered_lines(checked: Checked | None, *, full: bool) -> Lines:
    """The bar: each file whose bar the change lowered, with its reason on the standard
    track, or that no mark of a lowered bar was found."""
    lowered = checked.lowered if checked else ()
    if not lowered:
        return (NO_BAR,)
    if not full:
        listed = "; ".join(map(named, lowered))
        return (f"- the bar is lowered: {listed}",)
    return ("- the bar is lowered, with these reasons:", *map(reasoned, lowered))


def named(lowered: Lowered) -> str:
    """A lowered bar's file and how."""
    return f"`{lowered.path}` ({lowered.how})"


def reasoned(lowered: Lowered) -> str:
    """One lowered bar with the builder's reason."""
    why = lowered.reason or "no reason given"
    return f"  - `{lowered.path}` ({lowered.how}): {why}"


def size(checked: Checked | None) -> str:
    """The size of the change: its files and changed lines."""
    found = checked.size if checked else None
    if found is None:
        return "- size: ? files, ? changed lines"
    return f"- size: {found.files} files, {found.lines} changed lines"
