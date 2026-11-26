"""The step of a card of a task's session (`board_task.card_step` on `main`): the card's own page
in a frame of the board, which posts its answer itself; a card that no longer waits says what
took effect, and a page that may not act says where to answer."""

from typing import TYPE_CHECKING
from urllib.parse import quote

from lem.board.inputs.task.steps import Card, Confirm
from lem.board.views.panel import confirm
from lem.board.views.panel.asked import page_of
from lem.board.views.panel.common import stamp

if TYPE_CHECKING:
    from lem.board.inputs.task.steps import NotNow
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Row, Rows
    from lem.records.questions import Question

STEP = "card-step"
# The end of the key of a card the board's answer ended (`app.js` reads it).
ANSWERED = ":answered"
ELSEWHERE = (
    "Answer this card on the board on the Mac the task runs on or through its tailnet "
    "door, or in the task’s session there."
)
GONE = (
    "This card no longer waits for you: the session that put it up no longer runs, or it "
    "holds no such card."
)


def card(world: World, seen: Seen, rows: Rows, page: str) -> Card | NotNow:
    """The step of the card `page` of the task of `seen`, with its rows of what waits."""
    slug = seen.record.task.slug
    row = row_of(rows, page)
    if row is None:
        return ended(world, seen, page)
    if not world.viewer.may_act:
        return confirm.not_now(world, slug, ELSEWHERE)
    return Card(
        confirm=Confirm(
            look="you",
            label="A card of the task’s session",
            eyebrow="Card · the task’s session asks",
            back=confirm.back(world, slug),
            words="A question back goes to the task’s session, at the Mac.",
            sheet=True,
        ),
        frame=frame_of(world, slug, page),
        title=row.prompt or "The card of the task’s session",
        keep=f"card-{page}",
    )


def row_of(rows: Rows, page: str) -> Row | None:
    """The row of the open card `page`, or None."""
    cards = (one for one in rows if one.kind == "card")
    return next((one for one in cards if paged(one.card, page)), None)


def paged(card: str | None, page: str) -> bool:
    """Whether the card's question id names the page `page`."""
    return card is not None and card.startswith("card:") and page_of(card) == page


def frame_of(world: World, slug: str, page: str) -> str:
    """The card's own page, which the board serves in a frame."""
    parts = (world.viewer.base, "tasks", quote(slug, safe=""), "cards")
    named = quote(page, safe="")
    return "/".join((*parts, named, ""))


def ended(world: World, seen: Seen, page: str) -> NotNow:
    """A card that no longer waits: what took effect. A board's answer gives it the key of an
    answered card, which the board whose own frame took that answer keeps as its receipt
    (`app.js`); every other board shows this line."""
    slug = seen.record.task.slug
    asked = next(
        (one for one in seen.record.task.questions if paged(one.id, page)), None
    )
    if asked is None or asked.answer is None:
        return confirm.not_now(world, slug, GONE, card=STEP)
    said = f"{took(world, asked)}. This card no longer waits for you."
    keep = f"card-{page}{ANSWERED}" if asked.answer.source == "board" else None
    return confirm.not_now(world, slug, said, card=STEP, keep=keep)


def took(world: World, asked: Question) -> str:
    """`B was taken on the board at 15:42, from the phone`."""
    made = asked.answer
    if made is None:
        return "The card was closed"
    board = made.source == "board"
    where = "on the board" if board else "in the session"
    device = f", from the {made.device}" if board and made.device else ""
    at = stamp(world, made.at)
    return f"{made.label} was taken {where} at {at}{device}"
