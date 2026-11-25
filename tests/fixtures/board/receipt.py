"""The task of the board's picture of one task, `refund-line-on-receipt`: a night task that shows
every form a document of Lem's takes. A criterion with its case and its chart, the plan's chart,
an important decision with its story and its chart, a pull request that is not green for four
reasons, and the merge agent's read that calls the owner."""

from fixtures.board.make import (
    approval,
    criterion,
    journal,
    marks,
    moved,
    passed,
    ran,
    record,
)
from fixtures.board.moments import TODAY, ago, pull, sha
from lem.records.criteria import Criteria
from lem.records.decisions import Story, Taken
from lem.records.journal.landing import CheckEnd, CommandEnd, NotGreen, ReviewRound
from lem.records.journal.merge import ReadNoted
from lem.records.journal.task import DecisionNoted
from lem.records.landing.checks import ChangeSize, Checked, CriterionCheck, Lowered
from lem.records.landing.propose import MergeRead, Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.landing.review import Finding, Named, Reviewed
from lem.records.landing.start import Based, Started
from lem.records.task import Shape, Task
from lem.records.work import Plan

SLUG = "refund-line-on-receipt"
CHART = """flowchart TD
  A["A refund of 30 EUR comes in"] --> B{"Is it larger than the total?"}
  B -->|"no"| C["The receipt shows a line: Refund -30.00"]
  B -->|"yes"| D["The receipt shows 0.00 and a credit note"]
  C --> E["The new total stands under it\""""
DECISION_CHART = """flowchart TD
  A["The receipt has its items"] --> B{"Where does the refund go?"}
  B -->|"A"| C["In the items: the total reads as a price"]
  B -->|"B"| D["Under the items: the total stands under it"]
  B -->|"C"| E["In a footer: the customer looks for it"]
"""
CRITERIA = (
    criterion(
        1,
        "A refund shows on the receipt as a line of its own, and the total stands "
        "under it:",
        "Order 1042 is 100.00 EUR, and a refund of 30.00 EUR comes in.",
        "The receipt shows `Refund -30.00` under the items.",
        "The total under it is 70.00.",
        chart=CHART,
        test="tests/refund.sh",
    ),
    criterion(
        2,
        "A refund larger than the total shows 0.00 and a credit note for the rest.",
        test="tests/refund.sh",
    ),
)
SIZE_WHY = "the receipt gets a new line and a rule for a refund larger than the total."
WHERE = "Where the refund line goes on the receipt"
CHOSE = "B: a line of its own under the items, then the total"
DECIDED = Taken(
    id=1,
    at=ago(560),
    what=WHERE,
    chose=CHOSE,
    why="the total stands under what changed it",
    by="dialectic",
    said=(
        "the developer picked B, the support person picked B, the accountant leaned "
        "to C"
    ),
    options=(
        "A: in the items, as a negative price",
        CHOSE,
        "C: in the footer, beside the payment",
    ),
    levels=(
        ("gate", "no ruling covers it"),
        ("personas", "two for B, one for C: no clear pick"),
        (
            "dialectic",
            (
                "B held: the case against it found no reader that takes the last line "
                "above the total as an item"
            ),
        ),
    ),
    chart=DECISION_CHART,
    story=Story(
        case=(
            "Order 1042 has three items, 100.00 EUR.",
            "A refund of 30.00 EUR comes in.",
            "The receipt prints its lines in the order of the choice.",
            "A customer reads the last line above the total as the price of an item.",
        ),
        case_was="derived",
        cause=(
            "The receipt prints every line of an order in one list, and the total is "
            "the last of them."
        ),
    ),
)
COLORED = Taken(
    id=2,
    at=ago(540),
    what="How the refund line is colored",
    chose="the theme's green, as a credit",
    why=(
        "a refund is money back to the customer, which the shop's receipts show in green"
    ),
    by="lead",
)
TIP = sha("refund-line-on-receipt")
BASE = sha("main under the receipt")
REASONS = (
    (
        "decision 1 was taken without the owner (Where the refund line goes on the "
        'receipt): "B: a line of its own under the items, then the total", by the '
        "dialectic"
    ),
    (
        "the owner did not approve the criteria: they were approved on "
        f"{TODAY.isoformat()} while the task ran without the owner"
    ),
    (
        "the bar is lower in `tests/test_receipt.py` (one assertion fewer). The builder: "
        "the old check read the total from a fixed row of the receipt, which the refund "
        "line moves; `test_total_after_refund` reads the same value by its label, which "
        "is what a customer reads. The review: the reason holds; the new test covers the "
        "row the old one read, and no other test lost a line. The resolution of round 1 "
        "did not touch the file"
    ),
    (
        "two rounds reviewed it: the last one left no must-fix, and round 1 left 1 "
        "must-fix that pull request #44 answers"
    ),
)
ANSWERED = ("codex", "claude")
CORRECTNESS = (Named(name="correctness", why="the total changes"),)
FIRST = Reviewed(
    attempt=1,
    tip=TIP,
    of="change",
    scope="whole",
    floor="round",
    kind="round",
    careful=True,
    careful_why="the total a customer pays changes",
    answered=ANSWERED,
    ran=CORRECTNESS,
    findings=(
        Finding(
            id="r1.1",
            level="must-fix",
            where="receipt/lines.py:total",
            title="A refund larger than the total gives a negative total",
            what="a refund of 120.00 EUR on order 1042 prints Total -20.00",
            against="over",
        ),
        Finding(
            id="r1.2",
            level="should",
            where="tests/test_receipt.py:test_total_after_refund",
            title="The test reads the total by its row",
            what="the refund line moves the row the old check read",
            against="cheap",
        ),
    ),
    to_file=("r1.1",),
    review="reviews/review-1.json",
    at=ago(462),
)
SECOND = Reviewed(
    attempt=2,
    tip=TIP,
    of="change",
    scope="whole",
    floor="round",
    kind="round",
    careful=True,
    careful_why="the total a customer pays changes",
    answered=ANSWERED,
    ran=CORRECTNESS,
    findings=(
        Finding(
            id="r2.1",
            level="nit",
            where="receipt/lines.py:REFUND",
            title="The refund's label is a literal",
            what="the label Refund is written in the code, not in the translations",
            against="under",
        ),
    ),
    review="reviews/review-2.json",
    at=ago(450),
)
READ = MergeRead(
    tip=TIP,
    base=BASE,
    base_tree=sha("main's tree under the receipt"),
    verdict="call",
    why=(
        "Verdict: call. The change does what both criteria say; it is not green for "
        "two choices taken without you, and I would keep both."
    ),
    by="claude",
    brief="merge-brief.md",
    at=ago(440),
)
SPANS = (
    ran("lead", 596, 480),
    ran("task", 587.5, 520, job="task 1 of 2"),
    ran("task", 519.5, 480, job="task 2 of 2"),
    ran("checks", 478, 474),
    ran("review", 473, 450),
)
RECEIPT = record(
    Task(
        slug=SLUG,
        ask="Show a refund as a line of its own on the receipt",
        opened=ago(610),
        status="open",
        since=ago(448),
        branch="feat/refund-line-on-receipt",
        night=TODAY,
        mode="alone",
        mode_since=ago(610),
        shape=Shape(
            type="feat",
            why="the receipt gets a new line",
            track="full",
            then="interview",
        ),
        lead="builder",
        plan=Plan(path=f"docs/plans/{TODAY.isoformat()}-{SLUG}.md", tasks=2),
        spans=SPANS,
        criteria=Criteria(
            size="full",
            why=SIZE_WHY,
            criteria=CRITERIA,
            how=(
                "A refund becomes a line of the receipt; the rule for one larger than "
                "the total is the second branch."
            ),
            digest="3d32aa263163",
            approvals=(
                approval(598, "alone", "full", CRITERIA, SIZE_WHY, "255979939181"),
            ),
        ),
        decisions=(DECIDED, COLORED),
    ),
    Landing(
        phase="open",
        pull=Pull(
            number=44,
            url=pull(44),
            title="feat(receipt): a refund shows as a line of its own",
        ),
        pushed=TIP,
        started=Started(
            round=1, branch="feat/refund-line-on-receipt", base_ref="main", at=ago(479)
        ),
        based=Based(tip=TIP, base=BASE, before=TIP, carried=False, at=ago(478.5)),
        checked=Checked(
            tip=TIP,
            tree=sha("refund-line-on-receipt's tree"),
            base=BASE,
            inputs="5f1d0c7a2b3e",
            outcome="passed",
            outcomes=(
                passed("make test", "214 passed", 1),
                passed("make lint", "All checks passed", 2),
            ),
            criteria=(
                CriterionCheck(criterion=1, red_on_base=True, green_on_tip=True),
                CriterionCheck(criterion=2, red_on_base=True, green_on_tip=True),
            ),
            lowered=(
                Lowered(
                    path="tests/test_receipt.py",
                    how="one assertion fewer",
                    reason=(
                        "the old check read the total from a fixed row of the receipt, "
                        "which the refund line moves; `test_total_after_refund` reads "
                        "the same value by its label, which is what a customer reads"
                    ),
                    reviewer=(
                        "the reason holds; the new test covers the row the old one "
                        "read, and no other test lost a line"
                    ),
                ),
            ),
            size=ChangeSize(files=4, lines=86),
            at=ago(474),
        ),
        reviews=(FIRST, SECOND),
        proposed=Proposed(
            tip=TIP,
            base=BASE,
            green=False,
            reasons=REASONS,
            careful=True,
            notes_path="decisions.md",
            text="pr.md",
            who_acts="owner",
            at=ago(448),
        ),
        reads=(READ,),
    ),
    journal(
        moved(605, "shaping", "the interview waits for the owner", hold="owner"),
        *marks(SPANS),
        moved(596, "building", "lead: builder"),
        moved(590, "building", "plan committed, 2 tasks"),
        DecisionNoted(at=ago(560), id=1, what=WHERE),
        DecisionNoted(at=ago(540), id=2, what=COLORED.what),
        moved(480, "ready", "the report is written"),
        moved(479, "landing", "the checks start"),
        CheckEnd(
            at=ago(474),
            outcome="passed",
            say="The checks passed: make test, make lint",
            commands=(
                CommandEnd(name="make test", passed=True, last="214 passed"),
                CommandEnd(name="make lint", passed=True, last="All checks passed"),
            ),
        ),
        ReviewRound(at=ago(462), review=FIRST),
        ReviewRound(at=ago(450), review=SECOND),
        NotGreen(at=ago(448), tip=TIP, reasons=REASONS),
        moved(448, "open", "pull request https://github.com/acme/shop/pull/44"),
        ReadNoted(at=ago(440), read=READ),
    ),
)
