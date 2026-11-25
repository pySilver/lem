"""The ways from a thing that waits for the owner to where he answers it (`board_task.
session_action` and `inbox_action` on `main`): the jump to the task's session while it lives,
`Open a session` while none does, and, while he is away, the task's thread in the Inbox or why
the phone cannot open it."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.forms import Way
from lem.board.inputs.parts import Link
from lem.board.views import sessions
from lem.board.views.panel import inbox, opening

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows

INBOX = "inbox"
# The first words of a note no session takes a reply to, with the open here or without.
GONE = MappingProxyType({True: "{first}: open{again} one here.", False: "{first}."})


def session_way(world: World, seen: Seen) -> Way | None:
    """The task's live session and its jump, or `Open a session`, or None."""
    session = seen.session
    if session and session.live:
        opened = sessions.acted(seen.acts)
        name = opened.name if opened else seen.record.task.slug
        said = f"The task’s session, “{name}”, is in agterm on the Mac."
        return Way(said=said, jump=jump_of(world, seen))
    if not opening.opens(world, seen):
        return None
    form = opening.session_form(world, seen) if world.viewer.may_act else None
    return Way(said="No session of the task runs now.", form=form)


def jump_of(world: World, seen: Seen) -> str | None:
    """The agterm session a button jumps to, on a page for this Mac."""
    if not world.viewer.local:
        return None
    return sessions.jump_of(seen.acts, seen.session)


def inbox_ways(world: World, seen: Seen, rows: Rows) -> tuple[Way, ...]:
    """Where the owner answers while he is away and the task's thing went to his Inbox; none
    while it changes nothing of the session's line."""
    said = inbox.inbox_of(world, seen.record.task.slug, rows)
    if said is None:
        return ()
    if said.thread is None:
        why = Way(said=said.why or "", kind=INBOX)
        return (*session_ways(world, seen), why)
    link = Link(
        href=said.thread,
        label="Inbox",
        title="Open the task’s thread in the Inbox",
        out=True,
    )
    if said.asks:
        return (asked_way(world, seen, link),)
    if said.gone:
        return (gone_way(world, seen, link),)
    note = Way(
        said="The Inbox has a note of it, not a question.", link=link, kind=INBOX
    )
    return (*session_ways(world, seen), note)


def asked_way(world: World, seen: Seen, link: Link) -> Way:
    """A question in the Inbox: he answers in the task's session or there."""
    answer = "Answer in the task’s session on the Mac, or in the Inbox."
    return Way(said=answer, jump=jump_of(world, seen), link=link, kind=INBOX)


def session_ways(world: World, seen: Seen) -> tuple[Way, ...]:
    """The session's way, as one or none."""
    session = session_way(world, seen)
    return (session,) if session else ()


def gone_way(world: World, seen: Seen, link: Link) -> Way:
    """A note of a task no session can take a reply to: why, with `Open a session` where the
    page may act."""
    opens = opening.opens(world, seen) and world.viewer.may_act
    form = opening.session_form(world, seen) if opens else None
    said = f"{gone_first(seen, opens=opens)} The Inbox has a note, not a question."
    return Way(said=said, link=link, form=form, kind=INBOX)


def gone_first(seen: Seen, *, opens: bool) -> str:
    """Why no session takes a reply: it stopped, it does not answer, or none runs; with
    the open here when the page offers it."""
    session = seen.session
    if seen.stop is not None:
        return GONE[opens].format(first="The task’s session stopped", again=" a fresh")
    if session is not None and session.live:
        return "The task’s session does not answer."
    return GONE[opens].format(first="No session of the task runs now", again="")
