"""The afternoon's three ended tasks: a typo on the fast track that the board's server merged, an
invoice line on the standard track that landed from its interview to its merge, and a question
its investigation answered."""

from fixtures.board.make import (
    RULES,
    approval,
    criterion,
    journal,
    marks,
    moved,
    passed,
    ran,
    read,
    record,
)
from fixtures.board.moments import ago, pull, sha
from lem.model.landing import checks
from lem.records.criteria import Criteria
from lem.records.journal.landing import CheckEnd, CommandEnd, ReviewRound
from lem.records.journal.merge import MergeNoted, ReadNoted
from lem.records.landing.checks import Checked, CriterionCheck
from lem.records.landing.merge import Cleaned, Merged
from lem.records.landing.propose import MergeRead, Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.landing.review import Finding, Named, Reviewed
from lem.records.landing.start import Based, PassRun, Polished, Started
from lem.records.red import Inputs, Red, RedTest
from lem.records.task import Shape, Task
from lem.records.work import Investigation, Plan

MAIN = sha("main before the afternoon")
TERMS = 'The footer says "Terms and conditions".'
FOOTER_TIP = sha("footer-terms-typo")
FOOTER_CRITERIA = (criterion(1, TERMS),)
FOOTER_DIGEST = "5677f2e003bc"
FOOTER_SPANS = (
    ran("small", 51.5, 44, job="the small change"),
    ran("checks", 43, 39.5),
    ran("review", 38.5, 35),
)
FOOTER_REVIEW = Reviewed(
    attempt=1,
    tip=FOOTER_TIP,
    of="change",
    scope="whole",
    floor="read",
    kind="read",
    answered=("codex",),
    findings=(
        Finding(
            id="r1.1",
            level="nit",
            where="templates/footer.html:3",
            title="The footer's link has no title",
            what="the link to the terms reads only its words",
            against="under",
        ),
    ),
    at=ago(35),
)
FOOTER_MERGED = Merged(
    by="merger",
    via="server",
    commit=sha("footer-terms-typo merged"),
    merged_head=FOOTER_TIP,
    parent=MAIN,
    destination="main",
    base_checked=MAIN,
    base_merged=MAIN,
    base_read=MAIN,
    at=ago(32),
)
FOOTER_READ = MergeRead(
    tip=FOOTER_TIP,
    base=MAIN,
    base_tree=sha("main's tree"),
    verdict="merge",
    by="claude",
    at=ago(33),
)
FOOTER = record(
    Task(
        slug="footer-terms-typo",
        ask='The footer says "Terms and condtions"',
        opened=ago(52.5),
        status="landed",
        since=ago(32),
        branch="fix/footer-terms-typo",
        shape=Shape(
            type="fix", why="the footer shows a typo today", track="small", then="fast"
        ),
        lead="small",
        spans=FOOTER_SPANS,
        criteria=Criteria(
            size="small",
            why="the request is one sentence.",
            criteria=FOOTER_CRITERIA,
            digest=FOOTER_DIGEST,
            approvals=(
                approval(
                    52,
                    "lem",
                    "small",
                    FOOTER_CRITERIA,
                    "the request is one sentence.",
                    FOOTER_DIGEST,
                ),
            ),
        ),
    ),
    Landing(
        phase="ended",
        pull=Pull(
            number=41,
            url=pull(41),
            title="fix(footer): the footer says Terms and conditions",
        ),
        pushed=FOOTER_TIP,
        started=Started(
            round=1, branch="fix/footer-terms-typo", base_ref="main", at=ago(43.5)
        ),
        based=Based(
            tip=FOOTER_TIP, base=MAIN, before=FOOTER_TIP, carried=False, at=ago(43.5)
        ),
        checked=Checked(
            tip=FOOTER_TIP,
            tree=sha("footer-terms-typo's tree"),
            base=MAIN,
            inputs=checks.inputs(RULES),
            criteria_digest=FOOTER_DIGEST,
            outcome="passed",
            outcomes=(
                passed("make test", "212 passed", 1),
                passed("make lint", "All checks passed", 2),
            ),
            at=ago(39),
        ),
        reviews=(FOOTER_REVIEW,),
        proposed=Proposed(
            tip=FOOTER_TIP, base=MAIN, green=True, who_acts="merger", at=ago(34)
        ),
        reads=(FOOTER_READ,),
        merged=FOOTER_MERGED,
        cleaned=Cleaned(
            worktree_gone=True, branch_gone=True, forge_branch_gone=True, at=ago(31)
        ),
    ),
    journal(
        moved(52, "building", "small change: one builder"),
        *marks(FOOTER_SPANS),
        moved(44, "ready", "the report is written"),
        moved(43.5, "landing", "the checks start"),
        CheckEnd(
            at=ago(39.5),
            outcome="passed",
            say="The checks passed: make test, make lint",
            commands=(
                CommandEnd(name="make test", passed=True, last="212 passed"),
                CommandEnd(name="make lint", passed=True, last="All checks passed"),
            ),
        ),
        ReviewRound(at=ago(35), review=FOOTER_REVIEW),
        moved(34, "open", "pull request https://github.com/acme/shop/pull/41"),
        ReadNoted(at=ago(33), read=FOOTER_READ),
        MergeNoted(at=ago(32), merged=FOOTER_MERGED),
        moved(
            32,
            "landed",
            "main: pull request https://github.com/acme/shop/pull/41 is merged",
        ),
    ),
)

ORDERED = (
    'The invoice of order 1042, placed on 3 May, says "Ordered 3 May 2026" under its '
    "number."
)
INVOICE_BASE = sha("main under the invoice")
INVOICE_BUILT = sha("order-date-on-invoice built")
INVOICE_TIP = sha("order-date-on-invoice polished")
INVOICE_CRITERIA = (criterion(1, ORDERED, test="tests/order-date.sh"),)
INVOICE_SPANS = (
    ran("scout", 329.5, 327),
    ran("interview", 329, 321),
    ran("lead", 308, 246),
    ran("task", 294.5, 268, job="task 1 of 2"),
    ran("task", 267.5, 247, job="task 2 of 2"),
    ran("polish", 244, 236),
    ran("checks", 235.5, 231),
    ran("review", 230, 219),
)
INVOICE_REVIEW = Reviewed(
    attempt=1,
    tip=INVOICE_TIP,
    of="change",
    scope="whole",
    floor="round",
    kind="round",
    answered=("codex", "claude"),
    ran=(Named(name="correctness", why="the invoice changes"),),
    left_out=(Named(name="security", why="no input is read"),),
    findings=(
        Finding(
            id="r1.1",
            level="should",
            where="invoice/date.py:ordered",
            title="The date's format is written twice",
            what="ordered() repeats the format DATE names",
            against="cheap",
        ),
        Finding(
            id="r1.2",
            level="nit",
            where="invoice/date.py:language",
            title="language() has no docstring",
            what="the function says nothing of what it gives",
            against="under",
        ),
        Finding(
            id="r1.3",
            level="nit",
            where="tests/order-date.sh:2",
            title="The test greps the source",
            what="the check reads the code, not the invoice",
            against="under",
        ),
    ),
    at=ago(219),
)
INVOICE_MERGED = Merged(
    by="owner",
    via="github",
    commit=sha("order-date-on-invoice merged"),
    merged_head=INVOICE_TIP,
    parent=INVOICE_BASE,
    destination="main",
    base_checked=INVOICE_BASE,
    base_merged=INVOICE_BASE,
    at=ago(160),
)
INVOICE_PLAN = Plan(path="docs/plans/2026-11-17-order-date-on-invoice.md", tasks=2)
INVOICE_DIGEST = "d29b4ee0e29f"
INVOICE = record(
    Task(
        slug="order-date-on-invoice",
        ask="Print the order date on the invoice",
        opened=ago(330.5),
        status="landed",
        since=ago(160),
        branch="feat/order-date-on-invoice",
        shape=Shape(
            type="feat",
            why="the invoice gets a new line",
            track="full",
            then="interview",
        ),
        lead="builder",
        plan=INVOICE_PLAN,
        spans=INVOICE_SPANS,
        criteria=Criteria(
            size="full",
            why="the invoice gets a new line.",
            criteria=INVOICE_CRITERIA,
            digest=INVOICE_DIGEST,
            approvals=(
                approval(
                    309,
                    "owner",
                    "full",
                    INVOICE_CRITERIA,
                    "the invoice gets a new line.",
                    "dd2eac845d2f",
                ),
            ),
            reads=(read(318, 314, 1, "dd2eac845d2f"),),
            red=Red(
                ok=True,
                at=ago(230.5),
                digest=INVOICE_DIGEST,
                inputs=Inputs(
                    tip=INVOICE_TIP,
                    base=INVOICE_BASE,
                    plan=INVOICE_PLAN.path,
                ),
                tests=(
                    RedTest(
                        criterion=1,
                        command="sh tests/order-date.sh",
                        files=("tests/order-date.sh",),
                        on_branch=0,
                        on_base=2,
                    ),
                ),
            ),
        ),
    ),
    Landing(
        phase="ended",
        pull=Pull(
            number=38,
            url=pull(38),
            title="feat(invoice): the order date on the invoice",
        ),
        pushed=INVOICE_TIP,
        started=Started(
            round=1,
            branch="feat/order-date-on-invoice",
            base_ref="main",
            at=ago(245),
        ),
        based=Based(
            tip=INVOICE_BUILT,
            base=INVOICE_BASE,
            before=INVOICE_BUILT,
            carried=False,
            at=ago(244.5),
        ),
        polished=Polished(
            before=INVOICE_BUILT,
            after=INVOICE_TIP,
            commits=2,
            filed=("docs/backlog/invoice-footer-wraps.md",),
            run=PassRun(inputs="77ab01c4e9d2", outcome="passed", tip=INVOICE_TIP),
            at=ago(236),
        ),
        checked=Checked(
            tip=INVOICE_TIP,
            tree=sha("order-date-on-invoice's tree"),
            base=INVOICE_BASE,
            inputs=checks.inputs(RULES, INVOICE_PLAN.path),
            criteria_digest=INVOICE_DIGEST,
            outcome="passed",
            outcomes=(
                passed("make test", "214 passed", 1),
                passed("make lint", "All checks passed", 2),
            ),
            criteria=(
                CriterionCheck(criterion=1, red_on_base=True, green_on_tip=True),
            ),
            at=ago(230.5),
        ),
        reviews=(INVOICE_REVIEW,),
        proposed=Proposed(
            tip=INVOICE_TIP,
            base=INVOICE_BASE,
            green=True,
            who_acts="owner",
            at=ago(218),
        ),
        merged=INVOICE_MERGED,
        cleaned=Cleaned(
            worktree_gone=True, branch_gone=True, forge_branch_gone=True, at=ago(158)
        ),
    ),
    journal(
        moved(330, "shaping", "the interview waits for the owner", hold="owner"),
        *marks(INVOICE_SPANS),
        moved(314, "shaping", "the criteria wait for the owner", hold="owner"),
        moved(308, "building", "lead: builder"),
        moved(296, "building", "plan committed, 2 tasks"),
        moved(246, "ready", "the report is written"),
        moved(245, "landing", "the checks start"),
        CheckEnd(
            at=ago(231),
            outcome="passed",
            say="The checks passed: make test, make lint",
            commands=(
                CommandEnd(name="make test", passed=True, last="214 passed"),
                CommandEnd(name="make lint", passed=True, last="All checks passed"),
            ),
        ),
        ReviewRound(at=ago(219), review=INVOICE_REVIEW),
        moved(218, "open", "pull request https://github.com/acme/shop/pull/38"),
        MergeNoted(at=ago(160), merged=INVOICE_MERGED),
        moved(
            160,
            "landed",
            "main: pull request https://github.com/acme/shop/pull/38 is merged",
        ),
    ),
)

EXPORT_SPANS = (ran("investigation", 204.5, 186),)
EXPORT = record(
    Task(
        slug="why-export-is-slow",
        ask="Why does the monthly export take a minute?",
        opened=ago(205.5),
        status="answered",
        since=ago(185),
        shape=Shape(
            type="question",
            why="the ask asks why",
            track="small",
            then="investigation",
        ),
        investigation=Investigation(
            kind="question",
            found="question",
            call="answer",
            line="the export reads each order of the month with its own query",
            where="reports/export.py:monthly",
            report="investigation.md",
            at=ago(186),
        ),
        spans=EXPORT_SPANS,
    ),
    None,
    journal(
        moved(205, "building", "an investigator finds the answer"),
        *marks(EXPORT_SPANS),
        moved(185, "answered", "the answer: one query for each order"),
    ),
)
