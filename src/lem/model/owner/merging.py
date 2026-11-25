"""Who the merge of an open pull request waits for, from the task's record alone
(`board_model.merge_wait` on `main`): only the owner's is a row of what waits for him.

`reads`: the merge agent, while no settled read covers the proposed tip, and after Lem refused a
merge because the base moved and no read of that tip answered it. `merges`: the board's server,
on a read whose verdict is `merge` for a request the merge agent may merge, while the owner's
merge stands, or while a merge call is queued on the forge. `relands`: the task's
session, once a read of the tip said that the moved base needs another round. `owner`: an open
task with no proposal, a refusal by GitHub or by Lem's rules, a read that calls him, and a read
that came after Lem's refusal for the base and gave no verdict. A merge intent with no outcome on
record asks the owner to check GitHub.
"""

from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.model.landing import merge, merge_asked, merge_standing, mergeread
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.merge import Refused
    from lem.records.landing.propose import MergeRead, Proposed
    from lem.records.record import Record

type Wait = Literal["owner", "reads", "merges", "relands"]

OWNER: Wait = "owner"
MERGES: Wait = "merges"


def merge_wait(record: Record) -> Wait | None:
    """Who the merge of the task waits for; None for a task that is not open."""
    landing = record.landing or Landing()
    proposed = landing.proposed
    if record.task.status != "open":
        return None
    if proposed is None or landing.intent is not None:
        return OWNER
    if landing.accepted is not None:
        return MERGES
    refused = landing.refused
    if refused is not None and refused.tip == proposed.tip:
        return refused_wait(landing, refused)
    return proposed_wait(record, landing, proposed)


def proposed_wait(record: Record, landing: Landing, proposed: Proposed) -> Wait:
    """Who waits on a proposal no merge was refused for: a new round, the owner's merge that
    stands, or the newest read of the tip."""
    if mergeread.another_round(landing) is not None:
        return "relands"
    if merge_standing.standing_of(record) is not None:
        return MERGES
    return read_wait(record, mergeread.latest(landing), proposed)


def read_wait(record: Record, read: MergeRead | None, proposed: Proposed) -> Wait:
    """Who waits on the newest settled read of the tip: the merge agent with none, the server
    on a `merge` it may follow, else the owner."""
    if read is None:
        return "reads"
    if read.verdict == "merge" and owner_reason(record, proposed) is None:
        return MERGES
    return OWNER


def refused_wait(landing: Landing, refused: Refused) -> Wait:
    """Who waits after a refused merge of the proposed tip: Lem's refusal for a moved base is
    the merge agent's to read, or a new round's; any other refusal is the owner's."""
    if refused.source != "lem" or refused.kind != "base":
        return OWNER
    if mergeread.another_round(landing) is not None:
        return "relands"
    if calls_after_base_refusal(landing, refused):
        return OWNER
    return "reads"


def calls_after_base_refusal(landing: Landing, refused: Refused) -> bool:
    """Whether a read calls the owner with no verdict after a refusal for a moved base."""
    if refused.source != "lem" or refused.kind != "base":
        return False
    read = mergeread.latest(landing)
    return read is not None and read.verdict is None and read.at >= refused.at


def calling(record: Record) -> MergeRead | None:
    """The settled review, if any, of a merge that waits for the owner."""
    landing = record.landing or Landing()
    read, proposed = mergeread.latest(landing), landing.proposed
    if landing.intent is not None or read is None:
        return None
    if read.verdict != "merge":
        return read
    if proposed is None:
        return None
    why = owner_reason(record, proposed)
    return None if why is None else replace(read, why=why)


def owner_reason(record: Record, proposed: Proposed) -> str | None:
    """Why the record calls the owner after a merge verdict, if it has a reason."""
    if merge_asked.contract_moved(record):
        return merge.MOVED
    if proposed.who_acts != OWNER:
        return None
    if not proposed.green:
        return merge.NOT_GREEN
    if proposed.careful:
        return merge.CAREFUL
    return merge.LAND_OWNER
