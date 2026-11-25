"""A task that goes on from a dropped one (`project.resumed_slug`, `went_on_in` on `main`): its
slug, the first of its line with the next free number (`gift-note-2`, then `gift-note-3`), and
what it takes of the dropped task: its ticket, which a resumed task holds from then on.

A dropped task goes on in one task only; a second resume names the one it went on in.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task

# The most tasks one line of resumes holds, past which a slug is refused: a line goes round.
LONGEST = 999


def first_of(slug: str, every: tuple[Record, ...]) -> str:
    """The first task of the line `slug` is in, by the task each one went on from."""
    origins = {record.task.slug: record.task.resumed_from for record in every}
    met = [slug]
    origin = origins.get(slug)
    while origin is not None:
        if origin in met:
            listed = ", ".join(met)
            raise Refusal(
                "resume-line",
                f"the line of resumes of {slug} goes round: {origin} is met twice "
                f"({listed})",
                "the records of that line name each other: the owner opens a new task",
            )
        met.append(origin)
        origin = origins.get(origin)
    return met[-1]


def next_slug(slug: str, every: tuple[Record, ...]) -> str:
    """The slug of the task a dropped `slug` goes on in."""
    first = first_of(slug, every)
    taken = {record.task.slug for record in every}
    return next(
        f"{first}-{number}"
        for number in range(2, LONGEST + 1)
        if f"{first}-{number}" not in taken
    )


def went_on_in(slug: str, every: tuple[Record, ...]) -> str | None:
    """The task a dropped `slug` went on in already, or None."""
    return next(
        (record.task.slug for record in every if record.task.resumed_from == slug), None
    )


def origin_of(made: Task, every: tuple[Record, ...]) -> Task | None:
    """The dropped task `made` goes on from, or None; refused when it is no dropped task, or
    went on in another already."""
    origin = made.resumed_from
    if origin is None:
        return None
    statuses = (one.task.status for one in every if one.task.slug == origin)
    status = next(statuses, "no task")
    if status != "dropped":
        raise Refusal(
            "from",
            f"--from names the dropped task a new one goes on from, and {origin} is {status}",
            "drop it first, or leave --from out",
        )
    again = went_on_in(origin, every)
    if again is not None and again != made.slug:
        raise Refusal(
            "resumed",
            f"the dropped task {origin} goes on in {again} already",
            f"lem task resume {again} when that one is parked or dropped too",
        )
    return next(one.task for one in every if one.task.slug == origin)


def carried(made: Record, every: tuple[Record, ...]) -> Record:
    """The new record with the ticket of the dropped task it goes on from, when it names
    none of its own."""
    origin = origin_of(made.task, every)
    if origin is None or made.task.ticket is not None or origin.ticket is None:
        return made
    ticket = replace(origin.ticket, steps=())
    return replace(made, task=replace(made.task, ticket=ticket))
