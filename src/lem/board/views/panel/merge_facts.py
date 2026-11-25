"""The facts of the merge's confirm step (`board_task.merge_step` on `main`): the pull request,
the commit it merges with its subject, the branch, the base it lands on, and how it lands."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import pull_link
from lem.board.inputs.task.head import Fact
from lem.board.views.panel.common import pull_of

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.records.record import Record

PULL = "pr"
# How much of a commit's id the step shows.
SHORT = 12


def facts(world: World, seen: Seen) -> tuple[Fact, ...]:
    """The step's facts, in their order."""
    record = seen.record
    branch = record.task.branch
    found = (
        pull_fact(record),
        commit_fact(seen),
        Fact(key="branch", term="Branch", text=branch, mono=True) if branch else None,
        Fact(key="into", term="Into", text=base_of(world, record), mono=True),
        lands_as(record),
    )
    return tuple(fact for fact in found if fact is not None)


def pull_fact(record: Record) -> Fact:
    """The pull request it merges, or that the branch lands on the base itself."""
    pull = pull_of(record)
    if pull is None:
        sub = "none: the branch lands on the base itself"
        return Fact(key=PULL, term="Pull request", sub=sub)
    return Fact(key=PULL, term="Pull request", link=pull_link(pull, whole=True))


def commit_fact(seen: Seen) -> Fact:
    """The proposed commit, with its subject when it is the branch's newest."""
    landing = seen.record.landing
    tip = landing.proposed.tip if landing and landing.proposed else ""
    head = seen.head
    subject = head.subject if head and tip and head.sha.startswith(tip) else None
    return Fact(
        key="commit",
        term="Commit",
        text=tip[:SHORT] or "none on record",
        mono=True,
        sub=subject,
    )


def base_of(world: World, record: Record) -> str:
    """The base branch the task lands on: its landing's, else the workspace's."""
    started = record.landing.started if record.landing else None
    return started.base_ref if started else world.place.base


def lands_as(record: Record) -> Fact | None:
    """How the branch lands: one commit under the pull request's title."""
    pull = pull_of(record)
    if pull is None:
        return None
    return Fact(key="as", term="Lands as", text=f"one commit: `{pull.title}`")
