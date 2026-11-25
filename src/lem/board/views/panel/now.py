"""The large card of a task's Overview (`board_task.now_card` on `main`): what it does now and
who acts, its newest state's line, what its investigation found, where the owner answers, the
call to a breaker's document, the ways to the session and the Inbox, the answer the board takes
here, and the foot."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.now import Now
from lem.board.views import answering, offers
from lem.board.views.panel import heads, lines, now_parts, shown, ways
from lem.board.views.panel.answer import answer
from lem.model.owner import presence
from lem.records.holds import BreakerHold, OwnerHold, Parked

if TYPE_CHECKING:
    from lem.board.inputs.forms import AnswerForm, Way
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows

BREAKER = (
    "Its document is the first card above: read it, then help, park or drop the task."
)


def now(world: World, seen: Seen, rows: Rows, standing: Standing) -> Now:
    """The large card of the task of `seen`, with its rows of what waits for the owner."""
    task = seen.record.task
    after = next((row.after for row in rows if row.after), None)
    alone = presence.alone(task, world.presence)
    breaker = isinstance(task.hold, BreakerHold)
    line = None if breaker else shown.shown(seen.record) or None
    return Now(
        look=standing.look,
        icon=standing.icon,
        live=standing.live,
        who=now_parts.who_acts(standing, parked=isinstance(task.hold, Parked)),
        head=heads.now_head(seen, after, alone=alone),
        shown=line,
        more=more_of(seen),
        found=now_parts.found(task.investigation),
        report=report_of(seen),
        where=where_of(seen, standing, line, after),
        breaker=BREAKER if breaker and not working(seen) else None,
        ways=() if breaker else ways_of(world, seen, rows, standing),
        answer=None if breaker else answer_of(world, seen),
        foot=now_parts.foot(world, seen, standing),
    )


def more_of(seen: Seen) -> str | None:
    """Green or not green under the line of an open pull request."""
    landing = seen.record.landing
    proposed = landing.proposed if landing else None
    if seen.record.task.status != "open" or proposed is None:
        return None
    return "green" if proposed.green else "not green"


def report_of(seen: Seen) -> str | None:
    """The investigation's report, while the task's folder holds it."""
    if seen.record.task.investigation is None or now_parts.REPORT not in seen.files:
        return None
    return "The report is investigation.md in the task directory"


def where_of(
    seen: Seen, standing: Standing, line: str | None, after: str | None
) -> str | None:
    """Where the owner answers, while the task is his and the line above does not say it
    already."""
    task = seen.record.task
    if standing.column != "you" or isinstance(task.hold, BreakerHold):
        return None
    said = answer(task, after)
    return None if said == line else said


def working(seen: Seen) -> bool:
    """Whether the task's session works on the owner's answer now."""
    session = seen.session
    return session is not None and session.live and session.working


def ways_of(
    world: World, seen: Seen, rows: Rows, standing: Standing
) -> tuple[Way, ...]:
    """The Inbox's way while he is away, else the session's for his wait; the two lines a
    parked task's owner types."""
    task = seen.record.task
    found = ways.inbox_ways(world, seen, rows)
    if not found and standing.column == "you" and isinstance(task.hold, OwnerHold):
        found = ways.session_ways(world, seen)
    typed = lines.owner_lines(task) if isinstance(task.hold, Parked) else ()
    return (*found, *typed)


def answer_of(world: World, seen: Seen) -> AnswerForm | None:
    """The answer to a plan that waits for the owner's read, or to the skip of the personas'
    read, until his answer is on record."""
    task = seen.record.task
    for topic in ("plan", "skip"):
        asked = offers.open_question(task, topic)
        if asked is not None:
            return answering.form(world, asked, "panel", world.viewer.view)
    return None
