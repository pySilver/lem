"""The first words of a task's first line: the task's name for another session, a careful
topic, the type with his words, the branch, what the task waits for, and the commands that
correct the read (`compose_opening_line` and `correction` on `main`)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.model.task.first_line import Line

type Words = tuple[str | None, ...]


def head(line: Line, named: str | None) -> Words:
    """The task's name for another session, a careful topic first, the type with the words
    it quotes (a double quote of his own as a single one), and the branch."""
    careful = "; ".join(line.shape.careful).rstrip(".")
    quote = line.quote.replace('"', "'") if line.quote else None
    kind = line.shape.type
    typed = f'{kind}: "{quote}".' if quote else f"{kind}."
    branch = line.task.branch
    return (
        f"{named} ·" if named else None,
        f"Careful: {careful}." if careful else None,
        typed,
        f"Branch {branch}." if branch else None,
    )


def waits(line: Line, named: str | None) -> Words:
    """What a queued task waits for, before the steps of its track, which run when the wait
    ends: his order (as he said, or the one open task that fits his words) with his word that
    starts it before that, or the task it needs."""
    task = line.task
    if task.after is None:
        return ()
    if task.order is None:
        return (
            f"It waits for {task.after}, and starts when that task lands or is answered.",
        )
    which = "as you said;"
    if line.shape.fits:
        words = task.order.replace('"', "'")
        which = f'the one open task that fits "{words}";'
    slug = named or task.slug
    start = f'"start {slug} now" starts it before that.'
    return (f"It waits for {task.after}, {which} {start}",)


def correction(named: str | None, *, fast: bool) -> str:
    """The commands that correct the read, the fast track's two or the standard track's one.
    In the task's own session they need no task; in another session each names it."""
    task = f" {named}" if named else ""
    careful = f"/lem be-careful{task}"
    listed = f"/lem standard-track{task}, {careful}" if fast else careful
    return f"Wrong read? {listed}."
