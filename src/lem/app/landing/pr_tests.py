"""The first lines of the standard track's checks (`main:land.criteria_check_line`,
`polished`): each command; how many criteria's tests pass on the branch and fail on the base
commit, whether the checks took them from the polish pass, and how many criteria have no test;
what the polish pass did; the personas' read; the scout; and the cause."""

from typing import TYPE_CHECKING

from lem.app.landing import pr_checks, pr_read, pr_unread
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.record import Record

SHORT = 9
SCOUT = (
    "- the criteria were written from the scout's facts of the code, read during the "
    "interview"
)
LINE = "- the tests of the criteria: {0} pass on the branch and fail on the base commit"


def taken(record: Record) -> str:
    """The part of the criteria's line that says the checks took the tests' run from the
    polish pass at its commit; empty when they ran them."""
    checked = (record.landing or Landing()).checked
    runs = checked.criteria if checked else ()
    commit = next((run.taken_at for run in runs if run.taken_at), None)
    if commit is None:
        return ""
    short = commit[:SHORT]
    return f", taken from the polish pass at {short}, and not run again"


def criteria_line(record: Record) -> str:
    """How many criteria's tests pass on the branch and fail on the base commit, and how
    many criteria have no test."""
    checked = (record.landing or Landing()).checked
    runs = checked.criteria if checked else ()
    shown = sum(1 for run in runs if run.red_on_base and run.green_on_tip)
    return LINE.format(shown) + taken(record) + untested(record)


def untested(record: Record) -> str:
    """The part of the criteria's line that counts the criteria with no test."""
    without = sum(1 for found in record.task.criteria.criteria if found.no_test)
    has = "criterion has" if without == 1 else "criteria have"
    return f"; {without} {has} no test" if without else ""


def polish_line(landing: Landing) -> str:
    """The polish pass: its commits and the items it filed."""
    polished = landing.polished
    if polished is None:
        return "- the polish pass: none is on record"
    count, filed = polished.commits, len(polished.filed)
    commits = "commit" if count == 1 else "commits"
    nouns = "item" if filed == 1 else "items"
    return f"- the polish pass: {count} {commits}, {filed} {nouns} filed in the backlog"


def scout(record: Record) -> tuple[str, ...]:
    """The criteria were written from the scout's facts: no path, the forge has no file of
    this machine."""
    scouted = any(span.name == "scout" for span in record.task.spans)
    return (SCOUT,) if scouted else ()


def first(record: Record) -> Lines:
    """The checks before the bar: each command, the criteria's tests, the polish pass, the
    personas' read and what changed after it, the scout, and the cause."""
    landing = record.landing or Landing()
    tests = (criteria_line(record), polish_line(landing))
    read = (pr_read.read_line(record), *pr_unread.unread(record))
    read += scout(record)
    cause = pr_checks.cause(record, before=True)
    return (*pr_checks.commands(landing.checked), *tests, *read, *cause)
