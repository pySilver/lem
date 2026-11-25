"""The one push that tells the owner what is new on the lists of what waits: the first new
row's verb, its task's page, and how many more came (`push.Watcher.look` on `main`)."""

from typing import TYPE_CHECKING

from lem.adapters.notify_push_devices import Said
from lem.board.inputs.names import title_of
from lem.model.owner import verbs

if TYPE_CHECKING:
    from lem.app.owner.looking import Looked
    from lem.board.push.waits import New
    from lem.records.record import Record


def said_of(host: str, news: list[New]) -> Said:
    """The push of the news: the first row's verb, its task and workspace, and how many
    more."""
    name, found, row = news[0]
    record = record_of(found, row.task)
    return Said(
        title=verbs.verb(row, record.task, record.landing),
        body=body_of(news),
        url=f"/{host}/{name}/tasks/{row.task}",
        tag=f"lem-{row.key}",
    )


def record_of(found: Looked, slug: str) -> Record:
    """The record of the task `slug` in the look."""
    records = (one.record for one in found.looks)
    return next(one for one in records if one.task.slug == slug)


def body_of(news: list[New]) -> str:
    """The push's line: the first new row's task and workspace, and how many more came."""
    name, _, row = news[0]
    title = title_of(row.task)
    count = len(news) - 1
    more = f" · and {count} more" if count else ""
    return f"{title} · {name}{more}"
