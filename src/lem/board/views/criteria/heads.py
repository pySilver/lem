"""What happened to the criteria before the build, at the top of their card
(`board_task.criteria_head` on `main`): the personas' read and the approval. Each change of an
approved criterion follows them (`changes.py`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.parts import Row
from lem.board.views.criteria.stale import read_stale
from lem.board.views.criteria.terms import FAMILIES, criteria_count
from lem.board.views.criteria.unread import READ, unread

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.records.approvals import PersonaRead

# Who approved the criteria, as the row says it.
APPROVED = MappingProxyType(
    {
        "owner": "Approved by you",
        "lem": "The fast track: Lem approved its one criterion in your name",
        "read": "Frozen by the personas’ read, with no wait for you",
        "alone": "Approved without you, as the task ran alone",
    }
)


def silent_of(read: PersonaRead) -> tuple[str, ...]:
    """Each persona that gave no answer, and why."""
    return tuple(f"no answer from {one.name} ({one.why})" for one in read.silent)


def read_row(world: World, seen: Seen) -> Row | None:
    """The personas' newest read: nobody answered, what they flagged, or that they have not
    read the criteria."""
    criteria = seen.record.task.criteria
    if not criteria.reads:
        return unread(seen)
    read = criteria.reads[-1]
    time = time_of(world, read)
    if not read.answered:
        said = (
            f"(0 of {read.asked}), run by {run_by(read)}: it found nothing, either way"
        )
        return Row(
            id=READ,
            look="bad",
            icon="triangle-exclamation",
            head="Nobody answered the personas’ read",
            text=said,
            subs=silent_of(read),
            time=time,
        )
    return Row(
        id=READ,
        look="you" if read.split or read.flagged else "done",
        icon="users",
        head=flagged(read),
        text=f"· {read_by(read)}, run by {run_by(read)}",
        subs=silent_of(read) + stale_of(seen, read),
        time=time,
    )


def time_of(world: World, read: PersonaRead) -> str:
    """When the read ended, or began while it runs."""
    return stamp(read.ended or read.started, world.clock.now, world.clock.zone)


def stale_of(seen: Seen, read: PersonaRead) -> tuple[str, ...]:
    """The line that the criteria changed after the read, when they did."""
    stale = read_stale(seen.record.task, read)
    return (stale,) if stale else ()


def run_by(read: PersonaRead) -> str:
    """Who ran the read: the agent, or Lem."""
    return "the agent" if read.by == "lead" else "Lem"


def flagged(read: PersonaRead) -> str:
    """What the read found: a split of the model families, how many criteria it flagged."""
    split = "The two model families split on a criterion. " if read.split else ""
    count = criteria_count(read.criteria)
    found = f"{read.flagged} of {count} flagged" if read.flagged else "Nobody confused"
    return f"{split}{found}"


def read_by(read: PersonaRead) -> str:
    """Who read: how many personas of how many families."""
    count = len(read.families)
    families = FAMILIES.get(count) or f"{count} model families"
    named = ", ".join(read.families)
    return f"read by {read.answered} of {read.asked} personas, {families} ({named})"
