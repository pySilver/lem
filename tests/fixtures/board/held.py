"""The afternoon's tasks that something holds: a build its breaker stopped, which waits for the
owner; a breaker the owner parked; criteria that changed from his No on the board and wait for
his yes again; and a reviewer's item he started and parked."""

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
from fixtures.board.moments import ago
from lem.model.criteria import digest
from lem.records.criteria import Change, Criteria, Pair
from lem.records.decisions import Breaker
from lem.records.holds import BreakerHold, OwnerHold, Parked
from lem.records.journal.task import DecisionNoted, OwnerAct
from lem.records.questions import Answer, Question
from lem.records.task import Shape, Task
from lem.records.work import Plan

GIFT_WHAT = (
    "The gift note has no place in the export that keeps criterion 1 and the export's "
    "readers"
)
GIFT_QUESTION = "breaker:gift-note-in-export:1:20261125T154000Z"
GIFT_CRITERIA = (
    criterion(
        1,
        'An order with the gift note "for Ania" has that text in the last column of '
        "its row.",
    ),
    criterion(2, "An order with no gift note has an empty cell, not the word None."),
)
GIFT_SPANS = (
    ran("scout", 149.5, 147),
    ran("interview", 149, 141),
    ran("lead", 127),
    ran("task", 110.5, 74, job="task 1 of 3"),
    ran("task", 73.5, 20, job="task 2 of 3"),
)
GIFT = record(
    Task(
        slug="gift-note-in-export",
        ask="Add the gift note to the CSV export",
        opened=ago(150.5),
        status="building",
        since=ago(127),
        hold=BreakerHold(number=1, since=ago(20)),
        branch="feat/gift-note-in-export",
        shape=Shape(
            type="feat",
            why="the export gets a new column",
            track="full",
            then="interview",
        ),
        lead="builder",
        plan=Plan(path="docs/plans/2026-11-25-gift-note-in-export.md", tasks=3),
        spans=GIFT_SPANS,
        criteria=Criteria(
            size="full",
            why="the export gets a new column and two readers of it.",
            criteria=GIFT_CRITERIA,
            digest="9985a3fdb8a3",
            approvals=(
                approval(
                    128,
                    "owner",
                    "full",
                    GIFT_CRITERIA,
                    "the export gets a new column and two readers of it.",
                    "9985a3fdb8a3",
                ),
            ),
            reads=(read(138, 133, 2, "9985a3fdb8a3"),),
        ),
        decisions=(
            Breaker(
                id=1,
                at=ago(20),
                cause="criteria",
                what=GIFT_WHAT,
                document="breaker-1.md",
                handoff="handoff.md",
            ),
        ),
        questions=(
            Question(
                id=GIFT_QUESTION,
                topic="breaker",
                question="Breaker 1 of gift-note-in-export: help, park or drop the task?",
                options=("help", "park", "drop"),
                asked=ago(20),
            ),
        ),
    ),
    None,
    journal(
        moved(150, "shaping", "the interview waits for the owner", hold="owner"),
        *marks(GIFT_SPANS),
        moved(133, "shaping", "the criteria wait for the owner", hold="owner"),
        moved(127, "building", "lead: builder"),
        moved(112, "building", "plan committed, 3 tasks"),
        DecisionNoted(at=ago(20), id=1, what=GIFT_WHAT),
        moved(20, "building", "breaker 1 waits for the owner", hold="breaker"),
    ),
)

FEE_WHAT = "The fee notice goes to 212 merchants, and a mail cannot be called back"
FEE_PARKED = "wait for the merchants' association to confirm the fee date"
FEE_SPANS = (ran("lead", 260, 190), ran("task", 236.5, 205, job="task 2 of 2"))
FEE = record(
    Task(
        slug="fee-notice-to-merchants",
        ask="Tell each merchant about the new card fee by mail",
        opened=ago(260.5),
        status="building",
        since=ago(260),
        hold=Parked(since=ago(190), words=FEE_PARKED),
        branch="feat/fee-notice-to-merchants",
        shape=Shape(
            type="feat",
            why="the merchants get a new mail",
            track="full",
            then="lead",
        ),
        lead="builder",
        plan=Plan(path="docs/plans/2026-11-25-fee-notice-to-merchants.md", tasks=2),
        spans=FEE_SPANS,
        decisions=(
            Breaker(
                id=1,
                at=ago(205),
                cause="irreversible",
                what=FEE_WHAT,
                document="breaker-1.md",
                handoff="handoff.md",
                irreversible="person",
            ),
        ),
        questions=(
            Question(
                id="breaker:fee-notice-to-merchants:1:20261125T123500Z",
                topic="breaker",
                question=(
                    "Breaker 1 of fee-notice-to-merchants: help, park or drop the task?"
                ),
                options=("help", "park", "drop"),
                asked=ago(205),
                answer=Answer(
                    option="park",
                    label="Park",
                    note=FEE_PARKED,
                    source="session",
                    at=ago(190),
                ),
                took_effect="the owner parked it",
            ),
        ),
    ),
    None,
    journal(
        moved(260, "building", "lead: builder"),
        *marks(FEE_SPANS),
        moved(238, "building", "plan committed, 2 tasks"),
        DecisionNoted(at=ago(205), id=1, what=FEE_WHAT),
        moved(205, "building", "breaker 1 waits for the owner", hold="breaker"),
        moved(190, "building", f"the owner parked it: {FEE_PARKED}", hold="parked"),
    ),
)

STOCK_NOTE = "criterion 1 should also warn when only one is left"
STOCK_BEFORE = (
    criterion(1, 'A product with 3 in stock says "3 left" under its price.'),
    criterion(2, 'A product with none in stock says "Sold out" and no number.'),
)
STOCK_AFTER = (
    criterion(
        1,
        'A product with 3 in stock says "3 left" under its price, and one with 1 in '
        'stock says "Only 1 left" in the warning color: the blue mug, with 1 in stock, '
        'says "Only 1 left".',
    ),
    STOCK_BEFORE[1],
)
STOCK_SHEET = """## Acceptance criteria

Size: full, because the product page gets a new line.

1. {first}
2. {second}
"""
STOCK_PRIOR = STOCK_SHEET.format(
    first=STOCK_BEFORE[0].text, second=STOCK_BEFORE[1].text
)
STOCK_CRITERIA = STOCK_SHEET.format(
    first=STOCK_AFTER[0].text, second=STOCK_AFTER[1].text
)
STOCK_BEFORE_DIGEST = digest.of_texts("full", STOCK_BEFORE)
STOCK_SPANS = (ran("scout", 30.5, 28), ran("interview", 30, 22))
STOCK_ASKED = "criterion:stock-on-product-page:20261125T154600Z"
STOCK_AGAIN = "criterion:stock-on-product-page:20261125T155200Z"
STOCK = record(
    Task(
        slug="stock-on-product-page",
        ask="Show how many are left on the product page",
        opened=ago(31.5),
        status="shaping",
        since=ago(31),
        hold=OwnerHold(
            on="criteria",
            line="the criteria wait for the owner: changed from the owner's note",
            since=ago(8),
        ),
        shape=Shape(
            type="feat",
            why="the product page gets a new line",
            track="full",
            then="interview",
        ),
        spans=STOCK_SPANS,
        criteria=Criteria(
            size="full",
            why="the product page gets a new line.",
            criteria=STOCK_AFTER,
            digest=digest.of_tests("full", STOCK_AFTER),
            reads=(read(19, 14, 2, STOCK_BEFORE_DIGEST, flagged=1),),
            change=Change(
                at=ago(8),
                text=STOCK_PRIOR,
                words=STOCK_NOTE,
                pairs=(
                    Pair(
                        change="changed", before=STOCK_BEFORE[0], after=STOCK_AFTER[0]
                    ),
                ),
                before=STOCK_BEFORE_DIGEST,
                after=digest.of_texts("full", STOCK_AFTER),
            ),
        ),
        questions=(
            Question(
                id=STOCK_ASKED,
                topic="criterion",
                question="Approve the criteria?",
                options=("yes", "no"),
                digest=digest.shown(STOCK_PRIOR.encode()),
                asked=ago(14),
                answer=Answer(
                    option="no",
                    label="No",
                    note=STOCK_NOTE,
                    source="board",
                    via="door",
                    device="phone",
                    agent="Mozilla/5.0 (iPhone)",
                    at=ago(10),
                ),
                took_effect="the criteria changed from the owner's note",
            ),
            Question(
                id=STOCK_AGAIN,
                topic="criterion",
                question="Approve the criteria?",
                options=("yes", "no"),
                digest=digest.shown(STOCK_CRITERIA.encode()),
                asked=ago(8),
            ),
        ),
    ),
    None,
    journal(
        moved(31, "shaping", "the interview waits for the owner", hold="owner"),
        *marks(STOCK_SPANS),
        moved(14, "shaping", "the criteria wait for the owner", hold="owner"),
        OwnerAct(
            at=ago(10), act="answer", question=STOCK_ASKED, option="no", via="door"
        ),
        moved(
            8,
            "shaping",
            "the criteria wait for the owner: changed from the owner's note",
            hold="owner",
        ),
    ),
)

ITEM = ".lem/state/backlog/the-export-s-check-fails-by-chance.md"
CHECK = record(
    Task(
        slug="export-check-by-chance",
        ask=ITEM,
        opened=ago(7),
        status="queued",
        since=ago(7),
        hold=Parked(since=ago(6), words="the check waits for the new export"),
        backlog_item=ITEM,
        after="refund-rounding",
    ),
    None,
    journal(
        moved(7, "queued", "it starts after refund-rounding"),
        moved(
            6,
            "queued",
            "the owner parked it: the check waits for the new export",
            hold="parked",
        ),
    ),
)
