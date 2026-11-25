"""The steps a task's first line names, by the path its read named (`Shape.then`): the fast
track, an interview, a lead with no interview, or an investigation first; and what waits for
the owner on each (`compose_opening_line` on `main`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.task.first_words import correction

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.model.task.first_line import Line
    from lem.model.task.first_words import Words

FAST_STEPS = "Fast track: one builder, the checks, one read, then the pull request."
NOTHING = "Nothing waits for you."
YES_FIRST = (
    "Someone else wrote the request, so its criterion waits for your yes before the "
    "builder starts."
)
NOT_APPROVED = (
    "Nothing waits for you but the pull request, which calls you: you did not approve "
    "its criterion."
)
READ = "a lead writes acceptance criteria, and the personas read them."
READ_YES = "a lead writes acceptance criteria, the personas read them, and they wait for your yes."
# The statuses before a builder starts: someone else's criterion waits for his yes there.
BEFORE_BUILDER = frozenset(("queued", "shaping"))


def standard(line: Line) -> str:
    """The standard track, with the plan he asked for; after a wait, its steps come then."""
    said = "Standard track:"
    if line.task.plan_only:
        said = "Standard track, because you asked for its plan:"
    return said.replace("Standard", "Then the standard", 1) if line.task.after else said


def after_that(line: Line) -> str:
    """What comes after the criteria: the plan he asked for, or the pull request."""
    if line.task.plan_only:
        return "After that a lead writes the plan and stops for you to read it."
    return "After that it runs to the pull request without you."


def fast(line: Line, named: str | None) -> Words:
    """The fast track's steps; someone else's request waits for his yes before the builder,
    and a builder that started without it leaves him the pull request."""
    task = line.task
    nothing = NOTHING if task.after is None or task.order is None else None
    if line.shape.someone_else:
        nothing = YES_FIRST if task.status in BEFORE_BUILDER else NOT_APPROVED
    steps = FAST_STEPS.replace("Fast", "Then the fast", 1) if task.after else FAST_STEPS
    return (steps, nothing, correction(named, fast=True))


def interview(line: Line, named: str | None) -> Words:
    """The standard track with an interview: in this session, or in the task's own."""
    now = "" if line.task.after else " now"
    here = "in its own session" if named else "here"
    return (
        f"{standard(line)} an interview {here}{now}, then acceptance criteria for your yes.",
        after_that(line),
        correction(named, fast=False),
    )


def lead(line: Line, named: str | None) -> Words:
    """The standard track with no interview, and what says what is wanted in its place."""
    track = standard(line).rstrip(":")
    read = READ_YES if line.shape.someone_else else READ
    return (
        f"{track}, with no interview, since {line.stands_in} says what is wanted: {read}",
        after_that(line),
        correction(named, fast=False),
    )


def investigation(line: Line, named: str | None) -> Words:
    """An investigator first, with no track: the answer to a question, or the cause of a bug
    and the call that follows it; another session speaks of the task's own."""
    investigator = "Then an investigator" if line.task.after else "An investigator"
    teller = "Then its session tells you" if named else "Then I tell you"
    found = line.task.investigation
    if line.shape.type == "question" or (
        found is not None and found.kind == "question"
    ):
        return (f"{investigator} finds the answer first.", f"{teller} the answer.")
    return (
        f"{investigator} finds the cause first.",
        f"{teller} what it found: the fast track, the standard track, or no bug.",
    )


STEPS: MappingProxyType[str, Callable[[Line, str | None], Words]] = MappingProxyType(
    {"fast": fast, "interview": interview, "lead": lead, "investigation": investigation}
)


def steps(line: Line, named: str | None) -> Words:
    """The steps of the path the read named."""
    return STEPS[line.then](line, named)
