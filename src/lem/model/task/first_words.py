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
    starts it before that, or the tasks it needs."""
    task = line.task
    if not task.after:
        return ()
    if task.order is None:
        return (needs(task.after),)
    which = ordered_by(line, task.order)
    slug = named or task.slug
    needed = named_tasks(task.after)
    start = f'"start {slug} now" starts it before that.'
    return (f"It waits for {needed}, {which} {start}",)


def ordered_by(line: Line, order: str) -> str:
    """Whose order queued the task: his, as he said, or the one open task that fits it."""
    if not line.shape.fits:
        return "as you said;"
    words = order.replace('"', "'")
    return f'the one open task that fits "{words}";'


def needs(after: tuple[str, ...]) -> str:
    """The line of a task queued by a need: the tasks it waits for, and when it starts."""
    needed = named_tasks(after)
    ends = (
        "that task lands or is answered"
        if len(after) == 1
        else "each of them lands or is answered"
    )
    return f"It waits for {needed}, and starts when {ends}."


def named_tasks(slugs: tuple[str, ...]) -> str:
    """The tasks a queued task waits for, as one phrase: `a`, `a and b`, `a, b and c`."""
    if len(slugs) == 1:
        return slugs[0]
    head = ", ".join(slugs[:-1])
    last = slugs[-1]
    return f"{head} and {last}"


def correction(named: str | None, *, fast: bool) -> str:
    """The commands that correct the read, the fast track's two or the standard track's one.
    In the task's own session they need no task; in another session each names it."""
    task = f" {named}" if named else ""
    careful = f"/lem be-careful{task}"
    listed = f"/lem standard-track{task}, {careful}" if fast else careful
    return f"Wrong read? {listed}."
