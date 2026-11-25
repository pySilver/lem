"""What the owner's Inbox holds of a task's rows of what waits for him (`board_model.inbox_of` on
`main`, its keys): a merge review counts as its merge, and a thing sent under its question's id
(`breaker:SLUG:1:MOMENT`) counts for the row of that question (`breaker:SLUG:1`)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.board.views.inbox_read import Inbox, Sent
    from lem.model.owner.looks import Row, Rows


def sent_of(record: Inbox, slug: str, rows: Rows) -> list[Sent]:
    """What the Inbox holds of the task's rows now: a review counts as its merge, and a
    thing sent under its question's id counts for the row of that question."""
    keys = {key_of(row, slug) for row in rows}
    of_task = (one for one in record.sent if one.task == slug)
    return [one for one in of_task if named(one.key, keys)]


def key_of(row: Row, slug: str) -> str:
    """The key the Inbox holds a row's thing under: a merge review is its merge's."""
    return f"merge:{slug}" if row.kind == "review" else row.key


def named(key: str, keys: set[str]) -> bool:
    """Whether a sent thing's key is one of the rows', or a question's id under one."""
    return key in keys or key.rpartition(":")[0] in keys
