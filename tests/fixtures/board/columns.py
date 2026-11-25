"""The afternoon's view Tasks, as today's board draws its four columns: each task a card, with
its line, its time and its chips."""

from fixtures.board.moments import pull
from fixtures.board.receipt import REASONS
from fixtures.board.shown import gone, kind, since, task
from lem.board.inputs.parts import Chip, Link
from lem.board.inputs.tasks import Column, TaskCard, Tasks

GREEN = (
    "The checks passed with the bar where it was, the review left no must-fix, no "
    "criterion changed, and no decision past the personas was taken without an answer"
)
FAST = Chip(
    label="fast track",
    icon="code",
    look="lead",
    title=(
        "The fast track: one builder makes it, with no lead and no plan, and the landing "
        "checks it"
    ),
)
NOT_GREEN = "\n".join(REASONS)


def pull_chip(number: int) -> Chip:
    """The chip of a pull request of the shop."""
    url = pull(number)
    title = f"Open the pull request on the forge: {url}"
    link = Link(href=url, label=f"#{number}", title=title, out=True)
    return Chip(
        label=f"#{number}",
        icon="code-pull-request",
        look="gate",
        title=title,
        link=link,
    )


def green() -> Chip:
    """The chip of a pull request that is green."""
    return Chip(label="green", icon="check", look="ok", title=GREEN)


YOU = Column(
    key="you",
    look="you",
    title="Waits for you",
    total=3,
    empty="Nothing waits for you",
    cards=(
        TaskCard(
            slug="gift-note-in-export",
            title="Gift note in export",
            href=task("gift-note-in-export"),
            ask="Add the gift note to the CSV export",
            status="building",
            look="you",
            line="The build stopped, and its breaker waits for you",
            line_title=(
                "The gift note has no place in the export that keeps criterion 1 and the "
                "export's readers: no option of the ladder keeps the outcome the owner "
                "approved"
            ),
            live=True,
            since=since(20, "20m", "in this state since 15:40"),
            chips=(
                kind("feat", "the export gets a new column"),
                Chip(
                    label="breaker 1 waits",
                    icon="triangle-exclamation",
                    look="you",
                    live=True,
                    title=(
                        "Breaker 1: The gift note has no place in the export that keeps "
                        "criterion 1 and the export's readers\n"
                        "no option keeps the criteria you approved"
                    ),
                ),
            ),
        ),
        TaskCard(
            slug="stock-on-product-page",
            title="Stock on product page",
            href=task("stock-on-product-page"),
            ask="Show how many are left on the product page",
            status="shaping",
            look="you",
            line="The criteria changed from your note, and wait for your yes again",
            live=True,
            since=since(8, "8m 00s", "in this state since 15:52"),
            chips=(kind("feat", "the product page gets a new line"),),
        ),
        TaskCard(
            slug="refund-line-on-receipt",
            title="Refund line on receipt",
            href=task("refund-line-on-receipt"),
            ask="Show a refund as a line of its own on the receipt",
            status="open",
            look="you",
            line=f"Waits for the merge: pull request [#44]({pull(44)})",
            line_title="not green",
            since=since(448, "7h 28m", "in this state since 08:32"),
            chips=(
                kind("feat", "the receipt gets a new line"),
                Chip(
                    label="not green",
                    icon="triangle-exclamation",
                    look="you",
                    title=NOT_GREEN,
                ),
                pull_chip(44),
            ),
        ),
    ),
)
BUILD = Column(
    key="build",
    look="lead",
    title="Building",
    total=2,
    empty="No task builds",
    cards=(
        TaskCard(
            slug="refund-rounding",
            title="Refund rounding",
            href=task("refund-rounding"),
            ask="Round refunds the way the payment provider does",
            status="building",
            look="lead",
            line="Its companion talks the plan through",
            live=True,
            since=since(69, "1h 09m", "in this state since 14:51"),
            chips=(
                kind("feat", "refunds get a new rule"),
                Chip(
                    label="plan talk",
                    icon="table-columns",
                    look="lead",
                    live=True,
                    title=(
                        "A companion session talks the plan through, with the reviewer in "
                        "its other pane; an agent builds it after the talk"
                    ),
                ),
            ),
        ),
        TaskCard(
            slug="cart-total-after-coupon",
            title="Cart total after coupon",
            href=task("cart-total-after-coupon"),
            ask="The cart total is wrong after a coupon since yesterday",
            status="building",
            look="lead",
            line=(
                "Investigating: an investigator reproduces the bug and finds its cause"
            ),
            line_title="fix, because the ask says the total is wrong since yesterday",
            live=True,
            since=since(12, "12m", "in this state since 15:48"),
            chips=(
                kind("fix", "the ask says the total is wrong since yesterday"),
                Chip(
                    label="no session",
                    icon="triangle-exclamation",
                    look="bad",
                    title=(
                        "No agent runs the task now: “Open a session” on its page starts "
                        "a fresh one"
                    ),
                ),
            ),
        ),
    ),
)
CHECKS = Column(
    key="checks",
    look="gate",
    title="Checks and review",
    total=1,
    empty="No branch is checked or reviewed",
    cards=(
        TaskCard(
            slug="coupon-has-a-slug",
            title="Coupon has a slug",
            href=task("coupon-has-a-slug"),
            ask="Give each coupon a slug for its link",
            status="landing",
            look="gate",
            line="The checks start",
            live=True,
            since=since(8.5, "8m 30s", "in this state since 15:51"),
            chips=(kind("feat", "a coupon gets a new field"), FAST),
        ),
    ),
)
DONE = Column(
    key="done",
    look="done",
    title="Done",
    total=3,
    empty="Nothing landed yet",
    cards=(
        TaskCard(
            slug="footer-terms-typo",
            title="Footer terms typo",
            href=task("footer-terms-typo"),
            ask='The footer says "Terms and condtions"',
            status="landed",
            look="done",
            line=f"Landed: main: pull request [#41]({pull(41)}) is merged",
            since=gone(32, "32m ago", "ended 15:28"),
            chips=(
                kind("fix", "the footer shows a typo today"),
                FAST,
                green(),
                pull_chip(41),
            ),
        ),
        TaskCard(
            slug="order-date-on-invoice",
            title="Order date on invoice",
            href=task("order-date-on-invoice"),
            ask="Print the order date on the invoice",
            status="landed",
            look="done",
            line=f"Landed: main: pull request [#38]({pull(38)}) is merged",
            since=gone(160, "2h 40m ago", "ended 13:20"),
            chips=(
                kind("feat", "the invoice gets a new line"),
                green(),
                pull_chip(38),
            ),
        ),
        TaskCard(
            slug="why-export-is-slow",
            title="Why export is slow",
            href=task("why-export-is-slow"),
            ask="Why does the monthly export take a minute?",
            status="answered",
            look="done",
            line=(
                "The answer: the export reads each order of the month with its own query"
            ),
            since=gone(185, "3h 05m ago", "ended 12:55"),
            chips=(kind("question", "the ask asks why"),),
        ),
    ),
)
TASKS = Tasks(columns=(YOU, BUILD, CHECKS, DONE))
