"""What is new on a workspace's list of what waits for the owner, from the memory of the last look
(`push.gained` on `main`).

The first look at a workspace that the memory does not know records its rows and sends nothing.
After it, a row is news when the last look did not have it, unless it left less than FLAP
seconds ago: a row that leaves the list and comes back soon is not sent twice. A row is known by
its key (`model/owner/looks.Row.key`), so a second breaker of one task is news of its own.
"""

from typing import TYPE_CHECKING

from lem.adapters.notify_push_devices import Memory

if TYPE_CHECKING:
    from collections.abc import Sequence

# A row that leaves the list and comes back within this time is not sent again, in seconds.
# A guess: a task that moves from one state that waits to another in a few minutes is one
# thing for the owner (`push.FLAP_SECONDS` on `main`).
FLAP = 300.0


def gained(
    memory: Memory | None, rows: Sequence[str], now: float, flap: float = FLAP
) -> tuple[tuple[str, ...], Memory]:
    """The rows that are news, in their order, and the memory to keep."""
    present = frozenset(rows)
    if memory is None:
        return (), Memory(rows=tuple(sorted(present)))
    gone = left_at(memory, present, now)
    since = now - flap
    order = dict.fromkeys(rows)
    news = tuple(key for key in order if fresh(key, memory, gone, since))
    return news, remembered(present, gone, since)


def fresh(key: str, memory: Memory, gone: dict[str, float], since: float) -> bool:
    """Whether a row the list has now is news: the last look did not have it, and it did
    not leave after `since`."""
    return key not in memory.rows and gone.get(key, since) <= since


def left_at(memory: Memory, present: frozenset[str], now: float) -> dict[str, float]:
    """When each row that left the list left: the memory's, and now for each row that left
    since the last look."""
    left = dict.fromkeys(frozenset(memory.rows) - present, now)
    return {**memory.gone, **left}


def remembered(present: frozenset[str], gone: dict[str, float], since: float) -> Memory:
    """The memory to keep: the rows now, and those that left after `since` and are not
    back."""
    away = gone.keys() - present
    recent = {key: gone[key] for key in away if gone[key] > since}
    return Memory(rows=tuple(sorted(present)), gone=recent)
