"""The afternoon's tasks that run: a careful change whose plan talk put up a card for the owner,
a bug whose investigation runs with no session, and a fast-track change in its checks."""

from fixtures.board.make import (
    approval,
    criterion,
    journal,
    marks,
    moved,
    ran,
    read,
    record,
)
from fixtures.board.moments import ago, sha
from lem.records.criteria import Criteria
from lem.records.landing.record import Landing
from lem.records.landing.start import Based, Started
from lem.records.questions import Question
from lem.records.task import Shape, Task
from lem.records.work import Investigation

# The agterm page the card of the plan talk went up as, which names the card.
CARD = "4F9A1C2E-7B3D-4E8F-A1B2-C3D4E5F60718"
CARD_PROMPT = "Round each line of a refund, or only its total?"
ROUNDING_CRITERIA = (
    criterion(
        1, "A refund of 10.005 EUR pays back 10.01 EUR, as the provider rounds it."
    ),
)
ROUNDING_SPANS = (
    ran("interview", 94.5, 86),
    ran("lead", 69),
    ran("plan-talk", 55),
)
ROUNDING = record(
    Task(
        slug="refund-rounding",
        ask="Round refunds the way the payment provider does",
        opened=ago(95.5),
        status="building",
        since=ago(69),
        branch="feat/refund-rounding",
        shape=Shape(
            type="feat",
            why="refunds get a new rule",
            track="full",
            then="interview",
        ),
        lead="session",
        spans=ROUNDING_SPANS,
        criteria=Criteria(
            size="full",
            why="refunds get a new rule.",
            criteria=ROUNDING_CRITERIA,
            digest="21623180ffe8",
            approvals=(
                approval(
                    70,
                    "owner",
                    "full",
                    ROUNDING_CRITERIA,
                    "refunds get a new rule.",
                    "21623180ffe8",
                ),
            ),
            reads=(read(82, 78, 1, "21623180ffe8"),),
        ),
        questions=(
            Question(
                id=f"card:refund-rounding:{CARD}",
                topic="card",
                question=CARD_PROMPT,
                options=("line", "total"),
                asked=ago(50),
            ),
        ),
    ),
    None,
    journal(
        moved(95, "shaping", "the interview waits for the owner", hold="owner"),
        *marks(ROUNDING_SPANS),
        moved(78, "shaping", "the criteria wait for the owner", hold="owner"),
        moved(69, "building", "lead: session"),
    ),
)

CART_SPANS = (ran("investigation", 11.5),)
CART = record(
    Task(
        slug="cart-total-after-coupon",
        ask="The cart total is wrong after a coupon since yesterday",
        opened=ago(12),
        status="building",
        since=ago(12),
        shape=Shape(
            type="fix",
            why="the ask says the total is wrong since yesterday",
            track="small",
            then="investigation",
        ),
        investigation=Investigation(kind="fix"),
        spans=CART_SPANS,
    ),
    None,
    journal(
        moved(12, "building", "an investigator reproduces the bug and finds its cause"),
        *marks(CART_SPANS),
    ),
)

SLUG_CRITERIA = (criterion(1, "A coupon named Summer Sale has the slug summer-sale."),)
COUPON_TIP = sha("coupon-has-a-slug")
COUPON_SPANS = (ran("small", 29.5, 9, job="the small change"), ran("checks", 8))
COUPON = record(
    Task(
        slug="coupon-has-a-slug",
        ask="Give each coupon a slug for its link",
        opened=ago(30.5),
        status="landing",
        since=ago(8.5),
        branch="feat/coupon-has-a-slug",
        shape=Shape(
            type="feat", why="a coupon gets a new field", track="small", then="fast"
        ),
        lead="small",
        spans=COUPON_SPANS,
        criteria=Criteria(
            size="small",
            why="the request is one sentence.",
            criteria=SLUG_CRITERIA,
            digest="82487a746466",
            approvals=(
                approval(
                    30,
                    "lem",
                    "small",
                    SLUG_CRITERIA,
                    "the request is one sentence.",
                    "82487a746466",
                ),
            ),
        ),
    ),
    Landing(
        pushed=COUPON_TIP,
        started=Started(
            round=1, branch="feat/coupon-has-a-slug", base_ref="main", at=ago(8.5)
        ),
        based=Based(
            tip=COUPON_TIP,
            base=sha("main under the coupon"),
            before=COUPON_TIP,
            carried=False,
            at=ago(8.5),
        ),
    ),
    journal(
        moved(30, "building", "small change: one builder"),
        *marks(COUPON_SPANS),
        moved(9, "ready", "the report is written"),
        moved(8.5, "landing", "the checks start"),
    ),
)
