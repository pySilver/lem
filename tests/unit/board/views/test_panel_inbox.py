"""What a task's page says of the owner's Inbox while he is away (`main`'s `test_board_model.py`
Inbox: `board_model.inbox_of`, and `board_task.inbox_action` on the breaker's card and the large
card)."""

import dataclasses
from typing import TYPE_CHECKING

from fixtures.board.beside import INBOX_TAILNET
from fixtures.board.moments import NOW
from fixtures.board.receipt import SLUG
from lem.board.views import owed
from lem.board.views.inbox_read import Inbox, Sent
from lem.board.views.panel import inbox, inbox_words
from lem.board.views.panel.panel import panel
from lem.records.owner import Presence
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import World

GIFT = "gift-note-in-export"
QUESTION = "breaker:gift-note-in-export:1:20261125T154000Z"
THREAD = "msg_01DEMOGIFTNOTEBREAKER1"
AWAY = Presence(away=True, since=NOW, words="I'm away")


def away(afternoon: World, record: Inbox | None = None) -> World:
    """The afternoon while the owner is away, with the Inbox's record `record` (the
    afternoon's own when None)."""
    found = afternoon.inbox if record is None else record
    return dataclasses.replace(afternoon, presence=AWAY, inbox=found)


def sent(thread: str | None = THREAD) -> Sent:
    """The gift note's breaker question in the Inbox, in its thread `thread`."""
    return Sent(key=QUESTION, task=GIFT, kind="breaker", asks=True, thread_id=thread)


def said(afternoon: World, slug: str = GIFT) -> inbox.Said | None:
    """What the page of task `slug` says of the Inbox."""
    return inbox.inbox_of(afternoon, slug, owed.of_task(afternoon, slug))


def test_criterion_6_a_question_sent_while_he_is_away_links_to_its_thread_at_the_tailnet_address(
    tmp_path: Path,
) -> None:
    """`main`'s `test_board_model.py` Inbox.test_criterion_6_a_question_sent_while_he_is_
    away_links_to_its_thread_at_the_tailnet_address: the breaker's card names both places
    and links to the thread."""
    there = world(tmp_path)
    afternoon = away(there)
    thread = f"{INBOX_TAILNET}#thread={THREAD}"
    assert said(afternoon) == inbox.Said(thread=thread, asks=True)
    breaker = panel(afternoon, GIFT, "overview").overview
    assert breaker is not None
    assert breaker.breaker is not None
    (way,) = [one for one in breaker.breaker.ways if one.kind == "inbox"]
    assert way.said == "Answer in the task’s session on the Mac, or in the Inbox."
    assert way.link is not None
    assert way.link.href == thread
    assert breaker.breaker.where is None
    assert inbox.thread_link("https://studio.tail4e2a.ts.net:8443", 'm"1 <x>') == (
        "https://studio.tail4e2a.ts.net:8443/#thread=m%221%20%3Cx%3E"
    )
    assert said(there) is None


def test_criterion_7_with_the_door_closed_the_page_gets_why_and_no_link(
    tmp_path: Path,
) -> None:
    """`main`'s `test_board_model.py`
    Inbox.test_criterion_7_with_the_door_closed_the_page_gets_why_and_no_link."""
    afternoon = world(tmp_path)
    for why, words in (
        ("not running", inbox_words.WHY["not running"]),
        ("no tailnet address", inbox_words.NO_ADDRESS),
    ):
        closed = Inbox(running=why != "not running", why=why)
        assert said(away(afternoon, closed)) == inbox.Said(why=words)
        there = Inbox(running=why != "not running", why=why, sent=(sent(),))
        went = inbox_words.WHY_SENT[why]
        assert said(away(afternoon, there)) == inbox.Said(why=went)
    assert all(
        "no question went there" not in words for words in inbox_words.WHY_SENT.values()
    )
    later = said(away(afternoon, Inbox(why="later")))
    assert later is not None
    assert "“later”" in (later.why or "")
    odd = Inbox(running=True, tailnet_url="javascript:alert(1)", sent=(sent(),))
    assert said(away(afternoon, odd)) is None
    unsent = Inbox(
        running=True,
        tailnet_url=INBOX_TAILNET,
        problem="the send failed",
        sent=(sent(None),),
    )
    assert said(away(afternoon, unsent)) == inbox.Said(why=inbox_words.UNSENT)
    gift = panel(away(afternoon, unsent), GIFT, "overview").overview
    assert gift is not None
    assert gift.breaker is not None
    inboxed = [one for one in gift.breaker.ways if one.kind == "inbox"]
    assert [(one.said, one.link) for one in inboxed] == [(inbox_words.UNSENT, None)]


def test_a_note_says_whether_a_session_can_take_a_reply_and_the_merge_review_is_the_merges_thing(
    tmp_path: Path,
) -> None:
    """`main`'s `test_board_model.py` Inbox.test_a_note_says_whether_a_session_can_take_a_
    reply_and_the_merge_review_is_the_merges_thing: a note of a task no session runs is one
    no session can take a reply to; the merge review and the merge are one thing, a note,
    which the large card links to."""
    afternoon = world(tmp_path)
    cart = "cart-total-after-coupon"
    note = Sent(
        key=f"session:{cart}", task=cart, kind="session", asks=False, thread_id=THREAD
    )
    record = Inbox(running=True, tailnet_url=INBOX_TAILNET, sent=(note,))
    gone = said(away(afternoon, record), cart)
    assert gone is not None
    assert (gone.asks, gone.gone) == (False, True)
    merge = Sent(
        key=f"merge:{SLUG}", task=SLUG, kind="merge", asks=False, thread_id=THREAD
    )
    looked = away(
        afternoon, Inbox(running=True, tailnet_url=INBOX_TAILNET, sent=(merge,))
    )
    assert [row.kind for row in owed.of_task(looked, SLUG)] == ["review", "merge"]
    found = said(looked, SLUG)
    assert found == inbox.Said(thread=f"{INBOX_TAILNET}#thread={THREAD}")
    receipt = panel(looked, SLUG, "overview").overview
    assert receipt is not None
    inboxed = [one for one in receipt.now.ways if one.kind == "inbox"]
    assert [one.said for one in inboxed] == [
        "The Inbox has a note of it, not a question."
    ]
