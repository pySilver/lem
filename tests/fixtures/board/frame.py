"""The frame of the afternoon's page Tasks, as today's board draws it for the owner on this Mac:
its head, the phone's bar, the sidebar with what waits for him, the bar above the view, the
status bar, the search over every card, and the view's keys."""

from typing import TYPE_CHECKING

from fixtures.board.moments import BASE, NOW
from fixtures.board.shown import VERSION, VIEWER, since, task
from lem.board.inputs.layout import (
    Head,
    KeyGroup,
    Keys,
    Phonebar,
    Statusbar,
    Topbar,
)
from lem.board.inputs.page import Frame
from lem.board.inputs.parts import Chip, When
from lem.board.inputs.search import Found, Search
from lem.board.inputs.sidebar import Flag, Notice, Sidebar, ViewButton, Waiting
from lem.board.inputs.switcher import Switcher

if TYPE_CHECKING:
    from lem.board.inputs.text import Look

DEMO = "These tasks are examples and not real work. Nothing on this page waits for you."
GIFT = "gift-note-in-export"
CARD = "4F9A1C2E-7B3D-4E8F-A1B2-C3D4E5F60718"
WAITING = (
    Waiting(
        id=f"w-breaker-{GIFT}-1-20261125T154000Z",
        slug=GIFT,
        look="you",
        icon="triangle-exclamation",
        verb=f"Read the breaker of {GIFT}",
        since=since(20, "20m", "since the build stopped"),
        task="Gift note in export",
        href=task(GIFT),
        title=(
            f"Read the breaker of {GIFT} · Gift note in export\n"
            "The gift note has no place in the export that keeps criterion 1 and the "
            "export's readers\n"
            "Where you answer: Read its document, first on the task’s Overview. Then help, "
            "park or drop the task on this board, or help in the task’s session. Or type "
            f"/lem park {GIFT} to put the task aside, or /lem drop {GIFT} to end it."
        ),
    ),
    Waiting(
        id="w-session-cart-total-after-coupon",
        slug="cart-total-after-coupon",
        look="bad",
        icon="triangle-exclamation",
        verb="No session runs this task",
        since=since(12, "12m", "since it opened"),
        task="Cart total after coupon",
        href=task("cart-total-after-coupon"),
        title=(
            "No session runs this task · Cart total after coupon\n"
            "Where you answer: Open a session here or on the task’s header: a fresh agent "
            "reads the task’s state and goes on from there."
        ),
    ),
    Waiting(
        id=f"w-card-refund-rounding-{CARD}",
        slug="refund-rounding",
        look="you",
        icon="user",
        verb="Round each line of a refund, or only its total?",
        since=since(50, "50m", "since the session asked"),
        task="Refund rounding",
        href=task("refund-rounding", f"card/{CARD}"),
        title=(
            "Round each line of a refund, or only its total? · Refund rounding\n"
            "Where you answer: on the card, here or in the task’s session at the Mac. The "
            "board takes an answer with a note, never a conversation: a question back goes "
            "to the session at the Mac."
        ),
    ),
    Waiting(
        id="w-criterion-stock-on-product-page-20261125T155200Z",
        slug="stock-on-product-page",
        look="you",
        icon="file-lines",
        verb="Approve the criteria",
        since=since(8, "8m 00s", "in this state"),
        task="Stock on product page",
        href=task("stock-on-product-page"),
        title=(
            "Approve the criteria · Stock on product page\n"
            "Where you answer: The criteria changed from your note, and wait for your yes "
            "again, each changed one with its text before beside it. Approve or change them "
            "in the task’s session, or on this board: Yes, or No with your words, and Lem "
            "changes them and asks for your yes again."
        ),
    ),
    Waiting(
        id="w-review-refund-line-on-receipt",
        slug="refund-line-on-receipt",
        look="you",
        icon="file-lines",
        verb="Read the merge review",
        since=since(440, "7h 20m", "since the merge agent wrote it"),
        task="Refund line on receipt",
        things=2,
        href=task("refund-line-on-receipt"),
        title=(
            "Read the merge review · Refund line on receipt\n"
            "Where you answer: The merge review is the first card of the task’s Overview. "
            "The change does what both criteria say; it is not green for two choices taken "
            "without you, and I would keep both.\n"
            "2 things of this task wait for you: Waits for you lists each"
        ),
    ),
)
SIDEBAR = Sidebar(
    repo="shop",
    repo_title="shop · tasks land on main",
    beacon="lem serve reads this workspace's files and tells the page each change",
    notices=(
        Notice(
            id="notice-demo",
            kind="demo",
            icon="triangle-exclamation",
            head="Demo data.",
            said=DEMO,
        ),
    ),
    waits_count=5,
    waits_title="6 things you do, in 5 tasks",
    waits=WAITING,
    views=(
        ViewButton(
            key="tasks",
            label="Tasks",
            icon="square-kanban",
            href=f"{BASE}/",
            kbd="T",
            rail_title="Tasks · key T",
            count=8,
            current=True,
        ),
        ViewButton(
            key="waits",
            label="Waits for you",
            icon="inbox",
            href=f"{BASE}/waits",
            kbd="W",
            rail_title="5 tasks wait for you",
            count=5,
            look="you",
        ),
        ViewButton(
            key="backlog",
            label="Backlog",
            icon="list-check",
            href=f"{BASE}/backlog",
            kbd="B",
            rail_title="Backlog · key B",
            count=4,
            count_title="Backlog items outside Decided against",
        ),
        ViewButton(
            key="activity",
            label="Activity",
            icon="list-timeline",
            href=f"{BASE}/activity",
            kbd="A",
            rail_title="Activity · key A",
        ),
    ),
    flags=(Flag(kind="demo", title=f"Demo data: {DEMO[0].lower()}{DEMO[1:]}"),),
    switcher=Switcher(
        name="shop",
        title="shop: 5 wait for you · 2 build · 1 in checks and review\n/work/shop",
    ),
)


def found(
    slug: str, title: str, chip: str, look: Look, *, ended: bool = False
) -> Found:
    """A task's row of the search."""
    return Found(
        kind="task",
        key=slug,
        title=title,
        chip=chip,
        look=look,
        href=task(slug),
        open=not ended,
        frame=True,
    )


def item(key: str, title: str, chip: str, look: Look) -> Found:
    """A backlog item's row of the search."""
    href = f"{BASE}/backlog#item-{key}"
    return Found(kind="item", key=key, title=title, chip=chip, look=look, href=href)


SEARCH = Search(
    field="search-q-shop",
    rows=(
        found(GIFT, "Gift note in export", "Waits for you · building", "you"),
        found(
            "stock-on-product-page",
            "Stock on product page",
            "Waits for you · shaping",
            "you",
        ),
        found(
            "refund-line-on-receipt",
            "Refund line on receipt",
            "Waits for you · open",
            "you",
        ),
        found("refund-rounding", "Refund rounding", "Building · building", "lead"),
        found(
            "cart-total-after-coupon",
            "Cart total after coupon",
            "Building · building",
            "lead",
        ),
        found(
            "coupon-has-a-slug",
            "Coupon has a slug",
            "Checks and review · landing",
            "gate",
        ),
        found("fee-notice-to-merchants", "Fee notice to merchants", "parked", "quiet"),
        found("export-check-by-chance", "Export check by chance", "parked", "quiet"),
        found(
            "footer-terms-typo",
            "Footer terms typo",
            "landed 2026-11-25",
            "done",
            ended=True,
        ),
        found(
            "order-date-on-invoice",
            "Order date on invoice",
            "landed 2026-11-25",
            "done",
            ended=True,
        ),
        found(
            "why-export-is-slow",
            "Why export is slow",
            "answered 2026-11-25",
            "done",
            ended=True,
        ),
        item(
            "-read-the-receipt-s-total-by-its-label",
            "Read the receipt's total by its label",
            "Backlog · undecided",
            "you",
        ),
        item(
            "-the-export-s-check-fails-by-chance",
            "The export's check fails by chance",
            "Backlog · held by export-check-by-chance",
            "lead",
        ),
        item(
            "invoice-footer-wraps",
            "The invoice footer wraps on A5",
            "Backlog · worth: yes",
            "gate",
        ),
        item(
            "export-in-one-query",
            "Read the monthly export in one query",
            "Backlog · worth: later",
            "you",
        ),
        item(
            "-run-make-lint-before-each-commit",
            "Run make lint before each commit",
            "Backlog · worth: no",
            "quiet",
        ),
    ),
)
# How many entries the journals of the afternoon's eleven records hold, which the status
# bar counts in the place of today's events.
ENTRIES = 118
TOPBAR = Topbar(
    title="Tasks",
    summary="5 wait for you, 2 build, 1 in checks and review, 2 parked",
    chips=(
        Chip(label="tasks land on **main**", icon="code-branch"),
        Chip(
            label="**1** proposed · 1 not green", icon="code-pull-request", look="you"
        ),
        Chip(label="**2** landed today", icon="check", look="ok"),
    ),
    new_task=f"{BASE}/new",
)
FRAME = Frame(
    viewer=VIEWER,
    head=Head(
        title="DEMO · Tasks · Lem · shop · 2 build · 5 for you",
        stream=f"{BASE}/stream",
        version=VERSION,
        jump=f"{BASE}/agterm",
    ),
    phonebar=Phonebar(
        title="shop · demo data",
        waits=5,
        waits_label="5 tasks wait for you: open the list",
        new_task=f"{BASE}/new",
    ),
    sidebar=SIDEBAR,
    topbar=TOPBAR,
    statusbar=Statusbar(
        read=When(at=NOW, shown="just now", ticks="ago"),
        events=f"{ENTRIES} entries",
        forge="example tasks: no forge is asked",
        forge_title="A board of example tasks asks GitHub nothing",
        live="live-studio-shop",
    ),
    search=SEARCH,
    keys=Keys(
        id="kanban-keys",
        groups=(
            KeyGroup(keys=("J", "K", "↑", "↓"), word="move"),
            KeyGroup(keys=("H", "L", "←", "→"), word="column"),
            KeyGroup(keys=("Enter",), word="open"),
            KeyGroup(keys=("Esc",), word="close"),
        ),
    ),
    demo=True,
)
