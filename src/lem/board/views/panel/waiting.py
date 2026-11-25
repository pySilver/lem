"""What a task waits for, in words (`board_model.waits_for` on `main`): each thing the owner
does in it with where he answers, else what its landing waits for, else the task it starts
after; the header's fact "Waits for" and its key line say it."""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.inputs.names import title_of
from lem.board.views import telling, words
from lem.board.views.panel import pulls
from lem.board.views.panel.answer import answer
from lem.board.views.panel.common import closed, pull_of
from lem.board.views.where import recovery, where
from lem.model.owner import verbs

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.model.owner.looks import Rows


class Waiting(NamedTuple):
    """What the task waits for: its words, whether it is the owner's, and where he answers."""

    text: str
    yours: bool
    where: str | None = None


def waits_for(seen: Seen, rows: Rows) -> Waiting | None:
    """What the task of `seen` waits for, with the rows of what waits for the owner of it;
    None when it waits for nothing."""
    record = seen.record
    if rows:
        return Waiting(
            text=verbs_of(seen, rows), yours=True, where=answered(seen, rows)
        )
    landing = telling.waiting(record)
    if landing is not None:
        return Waiting(text=landing, yours=False)
    task = record.task
    if task.status == "queued" and task.after:
        named = title_of(task.after[0])
        return Waiting(
            text=words.capital(f"it starts after “{named}” ends"), yours=False
        )
    return None


def verbs_of(seen: Seen, rows: Rows) -> str:
    """Each thing the owner does in the task, its pull requests linked."""
    record = seen.record
    pull = pull_of(record)
    said = (verbs.verb(row, record.task, record.landing) for row in rows)
    forge = pulls.forge_of(pull.url if pull else None)
    return pulls.linked("; ".join(said), forge)


def answered(seen: Seen, rows: Rows) -> str:
    """Where the owner answers: where a row of a session that is gone says first, then the
    words of his other row for the session he opens; else where the task says."""
    task = seen.record.task
    pending = recovery(seen.record)
    if pending is not None:
        return pending
    gone = next(
        (
            row
            for row in rows
            if row.kind == "stopped" or (row.kind == "session" and not row.deaf)
        ),
        None,
    )
    after = next((row.after for row in rows if row.after), None)
    if gone is None:
        return answer(task, after)
    if len(rows) > 1:
        then = f" {answer(task, after)}"
    else:
        then = "" if closed(task) else f" Or type /lem drop {task.slug} to end it."
    return where(seen, gone) + then
