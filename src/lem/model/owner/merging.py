"""Who the merge of an open pull request waits for
(`board_model.merge_wait` on `main`): only the owner's is a row of what waits for him.

`reads`: the merge agent, while no settled read covers the proposed tip, and after Lem refused a
merge because the base moved and no read of that tip answered it. `merges`: the board's server,
on a read whose verdict is `merge` for a request the merge agent may merge, while the owner's
merge stands, or while a merge call is queued on the forge. `relands`: the task's
session, once a read of the tip said that the moved base needs another round. `owner`: an open
task with no proposal, a refusal by GitHub or by Lem's rules, a read that calls him, and a read
that came after Lem's refusal for the base and gave no verdict. A merge intent with no outcome on
record asks the owner to check GitHub. A parked task waits for no new merge.
"""

from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.model.landing import merge, merge_recheck, merge_standing, mergeread
from lem.records.holds import Parked
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.owner.looks import Look
    from lem.records.landing.merge import Refused
    from lem.records.landing.propose import MergeRead

type Wait = Literal["owner", "reads", "merges", "relands"]

OWNER: Wait = "owner"
MERGES: Wait = "merges"
RELANDS: Wait = "relands"


def merge_wait(look: Look) -> Wait | None:
    """Who the merge waits for, if it is still pending."""
    record = look.record
    task = record.task
    landing = record.landing or Landing()
    proposed = landing.proposed
    if (
        task.status != "open"
        or isinstance(task.hold, Parked)
        or landing.phase in {"merged", "ended"}
    ):
        return None
    if proposed is None or landing.intent is not None:
        return OWNER
    if landing.accepted is not None:
        return MERGES
    refused = landing.refused
    if refused is not None and refused.tip == proposed.tip:
        return refused_wait(look, landing, refused)
    return proposed_wait(look, landing)


def proposed_wait(look: Look, landing: Landing) -> Wait:
    """Who waits on a proposal no merge was refused for: a new round, the owner's merge that
    stands, or the newest read of the tip."""
    if mergeread.another_round(landing) is not None:
        return RELANDS
    read = mergeread.latest(landing, look.basis.tree)
    if read is None:
        return "reads"
    if merge_standing.standing_of(look.record) is not None:
        return MERGES
    if read.verdict == "merge" and owner_reason(look) is None:
        return MERGES
    return OWNER


def refused_wait(look: Look, landing: Landing, refused: Refused) -> Wait:
    """Who waits after a refused merge of the proposed tip: Lem's refusal for a moved base is
    the merge agent's to read, or a new round's; any other refusal is the owner's."""
    if refused.source != "lem" or refused.kind != "base":
        return OWNER
    base = look.basis.base
    if landing.standing is not None and base:
        return (
            RELANDS
            if merge_recheck.moved(landing, base)
            else proposed_wait(look, landing)
        )
    if mergeread.another_round(landing) is not None:
        return RELANDS
    if calls_after_base_refusal(
        landing,
        refused,
        base_tree=look.basis.tree,
        read_after_refusal=look.read_after_refusal,
    ):
        return OWNER
    return "reads"


def calls_after_base_refusal(
    landing: Landing,
    refused: Refused,
    *,
    base_tree: str | None = None,
    read_after_refusal: bool | None,
) -> bool:
    """Whether a read calls the owner with no verdict after a refusal for a moved base."""
    if refused.source != "lem" or refused.kind != "base":
        return False
    read = mergeread.latest(landing, base_tree)
    if read is None or read.verdict is not None:
        return False
    if read_after_refusal is not None:
        return read_after_refusal
    return read.at > refused.at


def calling(look: Look) -> MergeRead | None:
    """The settled review, if any, of a merge that waits for the owner."""
    landing = look.record.landing or Landing()
    read = mergeread.latest(landing, look.basis.tree)
    if landing.intent is not None or read is None:
        return None
    if read.verdict != "merge":
        return read
    why = owner_reason(look)
    return None if why is None else replace(read, why=why)


def owner_reason(look: Look) -> str | None:
    """Why the landing rules assign the merge to the owner."""
    return merge.authority(look.record, verdict=False, land=look.basis.land)
