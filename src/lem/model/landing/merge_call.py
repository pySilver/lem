"""The forge's merge call: its intent, its method, and the one commit's subject and body
(`main:land.merge_locked`, `squash_body`).

`branch.history = "squash"` lands the branch as one commit with the subject of the builder's
report, and a body that lists the task's decisions, then the line of a merge on a base a safe
read covered, and last names the task;
`"keep"` lands the branch's own commits (a rebase on the forge), which take no subject.
"""

from typing import TYPE_CHECKING, Literal

from lem.model.landing import merge_decided, merge_lines, mergeread
from lem.records.base import Frozen, Sha
from lem.records.landing.merge import MergeIntent
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.merge_asked import Asked
    from lem.model.landing.world import World
    from lem.records.record import Record

# How the forge lands the branch: one squashed commit, or its own commits replayed.
type Method = Literal["squash", "rebase"]


class Merging(Frozen, frozen=True, kw_only=True):
    """The merge to call: its intent, the forge's method, and the one commit's subject and
    body (a squash's; a rebase lands the branch's own commits)."""

    intent: MergeIntent
    method: Method
    subject: str
    body: str


def moved_line(landing: Landing, world: World) -> str | None:
    """The line of a merge on a base that a safe read of the merge agent covered, for the
    one commit's body; None on the checks' own base."""
    read = mergeread.latest(landing, world.base_tree)
    if read is None or read.base_call != "safe":
        return None
    ran = landing.checked.base if landing.checked else world.base
    bases = (ran, world.base)
    return merge_lines.base_line(world.rules.base, bases, read.why or "")


def merging(record: Record, world: World, asked: Asked, tip: Sha) -> Merging:
    """The call `asked` for of the proposed `tip`: its intent, and a squash with the
    report's subject and a body that lists the task's decisions and names the task, with the
    line of a merge on a base a safe read covered between; or a rebase that keeps the
    branch's commits."""
    by, via = asked.by, asked.via
    intent = MergeIntent(tip=tip, by=by, via=via, at=world.now)
    if world.rules.history == "keep":
        return Merging(intent=intent, method="rebase", subject="", body="")
    body = merge_lines.squash_body(
        record.task.slug,
        moved_line(record.landing or Landing(), world),
        merge_decided.block(record.task.decisions),
    )
    subject = asked.subject or ""
    return Merging(intent=intent, method="squash", subject=subject, body=body)
