"""The facts of a task's header that say where its work is (`board_task.facts` on `main`): its
branch, its pull request, its session, and its time in its state or since it ended."""

from typing import TYPE_CHECKING

from lem.app.sessions.acts import Open
from lem.board.inputs import clock
from lem.board.inputs.names import pull_link
from lem.board.inputs.task.head import Fact
from lem.board.views import sessions
from lem.board.views.panel.common import closed, pull_of, stamp

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World

SESSION = "session"
TIME = "time"


def places(world: World, seen: Seen, standing: Standing) -> tuple[Fact | None, ...]:
    """The branch, the pull request, the session and the time, each None with nothing to
    say."""
    return (
        branch_fact(seen),
        pull_fact(seen),
        session_fact(world, seen),
        time_fact(world, seen, standing),
    )


def branch_fact(seen: Seen) -> Fact | None:
    """The task's branch, in monospace, with a button that copies it."""
    branch = seen.record.task.branch
    if branch is None:
        return None
    return Fact(key="branch", term="Branch", text=branch, mono=True, copy=branch)


def pull_fact(seen: Seen) -> Fact | None:
    """The pull request as a link, with green or not green under it."""
    record = seen.record
    pull = pull_of(record)
    if pull is None:
        return None
    proposed = record.landing.proposed if record.landing else None
    word = None
    if proposed is not None:
        word = "green" if proposed.green else "not green"
    return Fact(
        key="pr", term="Pull request", link=pull_link(pull, whole=True), sub=word
    )


def session_fact(world: World, seen: Seen) -> Fact | None:
    """The task's session in agterm with its jump while it lives; while none lives and the
    task goes on, that none runs, and when the last one opened."""
    session, task = seen.session, seen.record.task
    if session is None:
        return None
    if session.live:
        return live_fact(world, seen)
    if closed(task):
        return None
    opens = [act.at for act in seen.acts if isinstance(act, Open)]
    sub = f"the last opened {stamp(world, opens[-1])}" if opens else None
    return Fact(key=SESSION, term="Session", text="none runs", yours=True, sub=sub)


def live_fact(world: World, seen: Seen) -> Fact:
    """The task's live session by its name, with its agterm id and, on this Mac, its jump."""
    agterm = sessions.jump_of(seen.acts, seen.session) or ""
    opened = sessions.acted(seen.acts)
    return Fact(
        key=SESSION,
        term="Session",
        text=opened.name if opened else seen.record.task.slug,
        mono=True,
        title=f"The agterm session of the task: {agterm}",
        jump=agterm if world.viewer.local and agterm else None,
    )


def time_fact(world: World, seen: Seen, standing: Standing) -> Fact:
    """How long the task is in its state, or how long ago it ended and how long it was
    open."""
    task, now = seen.record.task, world.clock.now
    if closed(task):
        return ended_fact(world, seen, standing)
    since = stamp(world, standing.since)
    opened = stamp(world, task.opened)
    return Fact(
        key=TIME,
        term="In this state",
        when=clock.since(standing.since, now),
        sub=f"since {since} · opened {opened}",
    )


def ended_fact(world: World, seen: Seen, standing: Standing) -> Fact:
    """How long ago the task ended, and how long it was open."""
    open_for = standing.since - seen.record.task.opened
    seconds = open_for.total_seconds()
    return Fact(
        key=TIME,
        term="Ended",
        when=clock.gone(standing.since, world.clock.now),
        sub=f"· open for {clock.length(seconds)}",
    )
