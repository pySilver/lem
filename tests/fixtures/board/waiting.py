"""The afternoon's view Waits for you, as today's board draws it: one row for each thing the
owner does, the pull request's two things in one stack; then the two tasks he parked."""

from fixtures.board.moments import BASE, pull
from fixtures.board.shown import since, task
from lem.board.inputs.forms import ActForm, AnswerForm, Choice, Field, TextBox
from lem.board.inputs.layout import KeyGroup, Keys
from lem.board.inputs.parts import Chip, Link
from lem.board.inputs.waits import Acts, Parked, Reason, Reasons, Stack, Wait, Waits

GIFT = "gift-note-in-export"
GIFT_KEY = f"breaker:{GIFT}:1:20261125T154000Z"
GIFT_ID = f"breaker-{GIFT}-1-20261125T154000Z"
CARD = "4F9A1C2E-7B3D-4E8F-A1B2-C3D4E5F60718"
RECEIPT = "refund-line-on-receipt"
STOCK = "stock-on-product-page"
CART = "cart-total-after-coupon"
WAITS_FOR_YOU = "Waits for you"
MERGE_STATE = "Waits for the merge"
TYPED = "Your words, as you would type them in the session"


def answer(slug: str, key: str, row: str, question: str, label: str) -> AnswerForm:
    """The answer to a breaker on a row of the view: help, or park or drop, each of the two
    after its confirm step."""
    return AnswerForm(
        id=f"answer-row-{row}",
        action=f"{BASE}/tasks/{slug}/answer",
        question=question,
        fields=(Field(name="key", shown=key), Field(name="in", shown="waits")),
        note=TextBox(
            name="words",
            id=f"ans-row-shop-{row}",
            label=label,
            placeholder=TYPED,
            rows=2,
        ),
        choices=(
            Choice(option="help", label="Help", icon="circle-question", press="go"),
            Choice(
                option="park",
                label="Park…",
                icon="folder",
                confirm=f"{BASE}/tasks/{slug}/park",
            ),
            Choice(
                option="drop",
                label="Drop…",
                icon="xmark",
                press="risk",
                confirm=f"{BASE}/tasks/{slug}/drop",
            ),
        ),
    )


def one(wait: Wait, slug: str, title: str, state: str) -> Stack:
    """A stack of one thing: that thing's row alone."""
    return Stack(
        slug=slug,
        id=f"wait-stack-{slug}",
        look=wait.look,
        icon=wait.icon,
        title=title,
        count="1 thing",
        first=wait.verb,
        state=state,
        waits=(wait,),
    )


BREAKER = Wait(
    id=f"wait-{GIFT_ID}",
    kind="breaker",
    look="you",
    icon="triangle-exclamation",
    verb=f"Read the breaker of {GIFT}",
    href=task(GIFT, under="waits"),
    since=since(20, "20m", "since the build stopped"),
    task="Gift note in export",
    state=WAITS_FOR_YOU,
    what=(
        "The gift note has no place in the export that keeps criterion 1 and the export's "
        "readers"
    ),
    sub="No option keeps the criteria you approved",
    acts=Acts(
        answer=answer(
            GIFT,
            GIFT_KEY,
            GIFT_ID,
            f"Breaker 1 of {GIFT}: help, park or drop the task?",
            "Help needs your words for the lead",
        ),
    ),
    where=(
        "Read its document, first on the task’s Overview. Then help, park or drop the task "
        "on this board, or help in the task’s session. Or type /lem park "
        f"{GIFT} to put the task aside, or /lem drop {GIFT} to end it."
    ),
)
NO_SESSION = Wait(
    id=f"wait-session-{CART}",
    kind="session",
    look="bad",
    icon="triangle-exclamation",
    verb="No session runs this task",
    href=task(CART, under="waits"),
    since=since(12, "12m", "since it opened"),
    task="Cart total after coupon",
    state="Investigating",
    acts=Acts(
        forms=(
            ActForm(
                action=f"{BASE}/tasks/{CART}/session",
                label="Open a session",
                icon="play",
                press="go",
                busy="Opening…",
                fields=(Field(name="in", shown="waits"),),
            ),
        ),
    ),
    where=(
        "Open a session here or on the task’s header: a fresh agent reads the task’s "
        "state and goes on from there."
    ),
)
CARD_HREF = task("refund-rounding", f"card/{CARD}", under="waits")
ASKED = Wait(
    id=f"wait-card-refund-rounding-{CARD}",
    kind="card",
    look="you",
    icon="user",
    verb="Round each line of a refund, or only its total?",
    href=CARD_HREF,
    since=since(50, "50m", "since the session asked"),
    task="Refund rounding",
    state="Building",
    acts=Acts(
        links=(
            Link(
                href=CARD_HREF,
                label="Answer the card…",
                icon="user",
                press="go",
                frame=True,
            ),
        ),
    ),
    where=(
        "on the card, here or in the task’s session at the Mac. The board takes an answer "
        "with a note, never a conversation: a question back goes to the session at the Mac."
    ),
)
CRITERIA = Wait(
    id=f"wait-criterion-{STOCK}-20261125T155200Z",
    kind="criteria",
    look="you",
    icon="file-lines",
    verb="Approve the criteria",
    href=task(STOCK, under="waits"),
    since=since(8, "8m 00s", "in this state"),
    task="Stock on product page",
    state=WAITS_FOR_YOU,
    sub="The criteria changed from your note, and wait for your yes again",
    acts=Acts(
        links=(
            Link(
                href=task(STOCK, "criteria", under="waits"),
                label="Read and approve…",
                icon="file-lines",
                press="go",
                frame=True,
            ),
        ),
    ),
    where=(
        "The criteria changed from your note, and wait for your yes again, each changed "
        "one with its text before beside it. Approve or change them in the task’s session, "
        "or on this board: Yes, or No with your words, and Lem changes them and asks for "
        "your yes again."
    ),
)
REVIEW = Wait(
    id=f"wait-review-{RECEIPT}",
    kind="review",
    look="you",
    icon="file-lines",
    verb="Read the merge review",
    href=task(RECEIPT, under="waits"),
    since=since(440, "7h 20m", "since the merge agent wrote it"),
    task="Refund line on receipt",
    state=MERGE_STATE,
    where=(
        "The merge review is the first card of the task’s Overview. The change does what "
        "both criteria say; it is not green for two choices taken without you, and I would "
        "keep both."
    ),
)


def reasons(key: str, under: str | None) -> Reasons:
    """The four reasons the refund line's pull request is not green, as the list `key`
    shows them on a page over the view `under`."""
    return Reasons(
        id=key,
        rows=(
            Reason(
                head="Decision 1 was taken without the owner",
                about="Where the refund line goes on the receipt",
                detail=(
                    (
                        '"B: a line of its own under the items, then the total", by the '
                        "dialectic"
                    ),
                ),
                ref=Link(
                    href=task(RECEIPT, "criteria", under=under),
                    label="decision 1",
                    title="Open decision 1 on Criteria and decisions",
                    icon="arrow-right",
                    frame=True,
                    anchor="dec-1",
                ),
            ),
            Reason(
                head="The owner did not approve the criteria",
                detail=(
                    "They were approved on 2026-11-25 while the task ran without the owner",
                ),
            ),
            Reason(
                head="The bar is lower in `tests/test_receipt.py`",
                about="one assertion fewer",
                detail=(
                    (
                        "The builder: the old check read the total from a fixed row of the "
                        "receipt, which the refund line moves"
                    ),
                    (
                        "`test_total_after_refund` reads the same value by its label, which is "
                        "what a customer reads"
                    ),
                    "The review: the reason holds",
                    (
                        "The new test covers the row the old one read, and no other test lost "
                        "a line"
                    ),
                    "The resolution of round 1 did not touch the file",
                ),
            ),
            Reason(
                head="Two rounds reviewed it",
                detail=(
                    (
                        "The last one left no must-fix, and round 1 left 1 must-fix that pull "
                        f"request [#44]({pull(44)}) answers"
                    ),
                ),
            ),
        ),
    )


MERGE = Wait(
    id=f"wait-merge-{RECEIPT}",
    kind="merge",
    look="you",
    icon="code-branch",
    verb="Merge the pull request #44",
    href=task(RECEIPT, under="waits"),
    since=since(448, "7h 28m", "since it was proposed"),
    task="Refund line on receipt",
    state=MERGE_STATE,
    marks=(
        Chip(label="not green", icon="triangle-exclamation", look="you"),
        Chip(
            label="acme/shop#44",
            icon="code-pull-request",
            look="gate",
            title=f"Open the pull request on the forge: {pull(44)}",
            link=Link(
                href=pull(44),
                label="acme/shop#44",
                title=f"Open the pull request on the forge: {pull(44)}",
                out=True,
            ),
        ),
    ),
    reasons=reasons(f"wr-{RECEIPT}", "waits"),
    acts=Acts(
        links=(
            Link(
                href=f"{BASE}/tasks/{RECEIPT}/merge?in=waits",
                label="Merge…",
                icon="code-pull-request",
                press="risk",
                frame=True,
            ),
        ),
    ),
    where="Merge the pull request on GitHub or on this board.",
)
WAITS = Waits(
    stacks=(
        one(BREAKER, GIFT, "Gift note in export", WAITS_FOR_YOU),
        one(NO_SESSION, CART, "Cart total after coupon", "Investigating"),
        one(ASKED, "refund-rounding", "Refund rounding", "Building"),
        one(CRITERIA, STOCK, "Stock on product page", WAITS_FOR_YOU),
        Stack(
            slug=RECEIPT,
            id=f"wait-stack-{RECEIPT}",
            look="you",
            icon="file-lines",
            title="Refund line on receipt",
            count="2 things",
            first="Read the merge review",
            state=MERGE_STATE,
            waits=(REVIEW, MERGE),
        ),
    ),
    parked=(
        Parked(
            slug="fee-notice-to-merchants",
            title="Fee notice to merchants",
            href=task("fee-notice-to-merchants", under="waits"),
            since=since(190, "3h 10m", "parked at 12:50"),
            parked_at="Parked at 12:50",
            why=(
                "The owner parked it: wait for the merchants' association to confirm the "
                "fee date"
            ),
            breaker=(
                "Breaker 1 stopped its build: “The fee notice goes to 212 merchants, and a "
                "mail cannot be called back”, since the next step cannot be undone by a "
                "later “no”: it sends something to a person."
            ),
            resume="/lem resume fee-notice-to-merchants",
        ),
        Parked(
            slug="export-check-by-chance",
            title="Export check by chance",
            href=task("export-check-by-chance", under="waits"),
            since=since(6, "6m 00s", "parked at 15:54"),
            parked_at="Parked at 15:54",
            why="The owner parked it: the check waits for the new export",
            resume="/lem resume export-check-by-chance",
        ),
    ),
)
KEYS = Keys(
    id="waits-keys",
    groups=(
        KeyGroup(keys=("J", "K", "↑", "↓"), word="move"),
        KeyGroup(keys=("Enter",), word="go or open"),
    ),
)
