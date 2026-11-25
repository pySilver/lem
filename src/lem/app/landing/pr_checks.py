"""The checks in the pull request's text (`main:land.pr_text`, `criteria_check_line`,
`polished`): each command with what it returned, the check of the criteria, the polish pass,
the cause a bug's investigation found, the bar, and the size of the change."""

from typing import TYPE_CHECKING

from lem.app.landing.pr_inputs import Lines
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.checks import Checked, Outcome
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


def criteria_line(record: Record) -> str:
    """How many criteria's tests pass on the branch and fail on the base commit, taken from
    the polish pass at its commit when the checks took them, and how many have no test."""
    checked = (record.landing or Landing()).checked
    runs = checked.criteria if checked else ()
    shown = [run for run in runs if run.red_on_base and run.green_on_tip]
    line = (
        f"- the tests of the criteria: {len(shown)} pass on the branch and fail on the "
        "base commit"
    )
    taken = next((run.taken_at for run in shown if run.taken_at), None)
    if taken:
        line = (
            f"{line}, taken from the polish pass at {taken[:SHORT]}, and not run again"
        )
    without = sum(1 for found in record.task.criteria.criteria if found.no_test)
    has = "criterion has" if without == 1 else "criteria have"
    return f"{line}; {without} {has} no test" if without else line


def polish_line(landing: Landing) -> str:
    """The polish pass: its commits and the items it filed."""
    polished = landing.polished
    if polished is None:
        return "- the polish pass: none is on record"
    commits, filed = polished.commits, len(polished.filed)
    plural = "" if commits == 1 else "s"
    items = "item" if filed == 1 else "items"
    return f"- the polish pass: {commits} commit{plural}, {filed} {items} filed in the backlog"


def cause(record: Record, *, before: bool) -> Lines:
    """The cause a bug's investigation found, with its place; none for a question."""
    found = record.task.investigation
    if found is None or found.kind != "fix" or not found.line:
        return ()
    where = f" ({found.where})" if found.where else ""
    when = " before the build" if before else ""
    return (f"- the cause, as the investigation{when} found it: {found.line}{where}",)


def bar(checked: Checked | None, *, full: bool) -> Lines:
    """The bar: each file whose bar the change lowered, with its reason on the standard
    track, or that no mark of a lowered bar was found."""
    lowered = checked.lowered if checked else ()
    if not lowered:
        return (NO_BAR,)
    if full:
        reasons = tuple(
            f"  - `{found.path}` ({found.how}): {found.reason or 'no reason given'}"
            for found in lowered
        )
        return ("- the bar is lowered, with these reasons:", *reasons)
    listed = "; ".join(f"`{found.path}` ({found.how})" for found in lowered)
    return (f"- the bar is lowered: {listed}",)


def size(checked: Checked | None) -> str:
    """The size of the change: its files and changed lines."""
    found = checked.size if checked else None
    if found is None:
        return "- size: ? files, ? changed lines"
    return f"- size: {found.files} files, {found.lines} changed lines"
