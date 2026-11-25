"""What the afternoon holds beside its task records: Lem's acts on each task's agterm sessions,
the tasks' own files (`task.md`, a breaker's document, the merge review, the checks' output, the
pictures), the backlog's items, and the board server's record of the owner's Inbox.

No record of the rebuild holds these (`notes/board-inputs.md` names each one's owner); a view
reads them through a port or a file, as `main`'s board does. `lay` writes the whole afternoon
into a workspace of its own, its records through the store.
"""

import json
import zlib
from typing import TYPE_CHECKING

from fixtures.board import prose
from fixtures.board.ended import EXPORT, FOOTER, INVOICE
from fixtures.board.held import CHECK, FEE, GIFT, STOCK
from fixtures.board.moments import TODAY, ago
from fixtures.board.receipt import RECEIPT
from fixtures.board.working import CART, COUPON, ROUNDING
from lem.app.sessions import log
from lem.app.sessions.acts import Act, Close, CloseWhy, Open
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

RECORDS = (
    CART,
    CHECK,
    COUPON,
    EXPORT,
    FEE,
    FOOTER,
    GIFT,
    INVOICE,
    RECEIPT,
    ROUNDING,
    STOCK,
)
# The tailnet address of the owner's Inbox in the board server's record of it.
INBOX_TAILNET = "https://studio.tail4e2a.ts.net:8443/"
OUTCOME = f"""**A refund shows on the receipt as a line of its own, and the total under it is what the customer paid.**

Today:
1. Order 1042 is 100.00 EUR.
2. A refund of 30.00 EUR comes in.
3. The receipt shows 70.00 EUR, and no line says why.

After:
1. Order 1042 is 100.00 EUR.
2. A refund of 30.00 EUR comes in.
3. The receipt shows `Refund -30.00` under the items, and `Total 70.00` under it.

```mermaid
{prose.DEMO_CHART}
```

| Receipt | Today | After |
| --- | --- | --- |
| The refund | not shown | a line of its own, in green |
| The total | 70.00 | 70.00, under the refund |"""
RECEIPT_TASK = f"""# refund-line-on-receipt

## The ask, verbatim

Show a refund as a line of its own on the receipt

## Type

feat, because the receipt gets a new line

## Outcome

{OUTCOME}
"""
INVOICE_TASK = """# order-date-on-invoice

## The ask, verbatim

Print the order date on the invoice

## Type

feat, because the invoice gets a new line

## Outcome

Each invoice says when its order was placed, under the order's number, in the shop's language.
A customer who asks about an old order finds the date on the paper they already have.
"""
INVESTIGATION = """# Investigation

The export reads every order of the month one query at a time.
A month of 4,000 orders makes 4,000 queries.
Each query waits about 15 ms for the database.
"""
REPORT = """# Report

The refund line is in, under the items, and the total under it.

![The receipt of order 1042 after a refund of 30.00 EUR](media/receipt-after.png)
*The refund reads `-30.00` in green; the total under it is 70.00.*
"""
# The criteria of the stock line as its session changed them from the owner's note, which wait
# for his yes again.
STOCK_CRITERIA = """## Acceptance criteria

Size: full, because the product page gets a new line.

1. A product with 3 in stock says "3 left" under its price, and one with 1 in stock says "Only 1 left" in the warning color: the blue mug, with 1 in stock, says "Only 1 left".
2. A product with none in stock says "Sold out" and no number.
"""
# A picture's bytes: the smallest PNG, one white pixel.
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8ffff3f0005fe02fea7d6a4b40000000049454e44ae426082"
)
FILES = (
    (
        "gift-note-in-export",
        "breaker-1.md",
        prose.GIFT_BREAKER.replace("{slug}", "gift-note-in-export"),
    ),
    ("gift-note-in-export", "handoff.md", prose.GIFT_HANDOFF),
    (
        "fee-notice-to-merchants",
        "breaker-1.md",
        prose.FEE_BREAKER.replace("{slug}", "fee-notice-to-merchants"),
    ),
    ("footer-terms-typo", "merge-review.md", prose.TYPO_REVIEW),
    ("refund-line-on-receipt", "merge-review.md", prose.MERGE_REVIEW),
    ("refund-line-on-receipt", "task.md", RECEIPT_TASK),
    ("refund-line-on-receipt", "report.md", REPORT),
    (
        "refund-line-on-receipt",
        "gate/01.log",
        "\x1b[32m....................\x1b[0m\n214 passed in 3.1s\n",
    ),
    ("refund-line-on-receipt", "gate/02.log", "All checks passed!\n"),
    ("order-date-on-invoice", "task.md", INVOICE_TASK),
    ("why-export-is-slow", "investigation.md", INVESTIGATION),
    ("stock-on-product-page", "criteria.md", STOCK_CRITERIA),
)
PICTURES = (
    ("refund-line-on-receipt", "media/receipt-before.png"),
    ("refund-line-on-receipt", "media/receipt-after.png"),
)
BACKLOG = (
    (
        "docs/backlog/invoice-footer-wraps.md",
        prose.FOOTER_ITEM.format(today=TODAY.isoformat()),
    ),
    (
        "docs/backlog/export-in-one-query.md",
        (
            f"---\nworth: later\nadded: {TODAY.isoformat()}\n---\n\n# Read the monthly export "
            "in one query\n\nThe investigation of the slow export found one query for each "
            "order. One query for the month would take the minute away.\n"
        ),
    ),
)


def session(slug: str, minutes: float) -> str:
    """The agterm id of the session task `slug` opened `minutes` before now: the form of
    today's showcase, made from the task's name and the minute."""
    crc = zlib.crc32(slug.encode())
    return f"{crc:08X}-0000-4000-8000-{int(minutes * 10):012X}"


def opened(slug: str, minutes: float, phase: str, why: str) -> Open:
    """A session Lem opened for task `slug`, `minutes` before now."""
    return Open(
        at=ago(minutes),
        session=session(slug, minutes),
        name=slug,
        phase=phase,
        why=why,
        workspace="demo",
    )


def closed(slug: str, opened_at: float, minutes: float, why: CloseWhy) -> Close:
    """The session task `slug` opened `opened_at` minutes before now, which Lem closed
    `minutes` before now."""
    return Close(at=ago(minutes), session=session(slug, opened_at), why=why)


INVOICE_SLUG = "order-date-on-invoice"
RECEIPT_SLUG = "refund-line-on-receipt"
# Lem's acts on each task's sessions, as today's afternoon logs them: the task that never had
# a session (`cart-total-after-coupon`) and the reviewer's item the owner parked have none.
ACTS: tuple[tuple[str, tuple[Act, ...]], ...] = (
    (
        "footer-terms-typo",
        (
            opened("footer-terms-typo", 52.5, "fast", "new"),
            closed("footer-terms-typo", 52.5, 31, "ended"),
        ),
    ),
    ("coupon-has-a-slug", (opened("coupon-has-a-slug", 30.5, "fast", "new"),)),
    (
        "gift-note-in-export",
        (
            opened("gift-note-in-export", 150.5, "shape", "new"),
            opened("gift-note-in-export", 127.5, "build", "handoff"),
        ),
    ),
    (
        "fee-notice-to-merchants",
        (
            opened("fee-notice-to-merchants", 260.5, "build", "new"),
            closed("fee-notice-to-merchants", 260.5, 189.5, "owner"),
        ),
    ),
    ("stock-on-product-page", (opened("stock-on-product-page", 31.5, "shape", "new"),)),
    (
        "refund-rounding",
        (
            opened("refund-rounding", 95.5, "shape", "new"),
            opened("refund-rounding", 69.5, "build", "handoff"),
        ),
    ),
    (
        INVOICE_SLUG,
        (
            opened(INVOICE_SLUG, 330.5, "shape", "new"),
            opened(INVOICE_SLUG, 308.5, "build", "handoff"),
            opened(INVOICE_SLUG, 245.5, "land", "handoff"),
            closed(INVOICE_SLUG, 245.5, 158, "ended"),
        ),
    ),
    (
        "why-export-is-slow",
        (
            opened("why-export-is-slow", 205.5, "build", "new"),
            closed("why-export-is-slow", 205.5, 184.5, "ended"),
        ),
    ),
    (
        RECEIPT_SLUG,
        (
            opened(RECEIPT_SLUG, 609.5, "shape", "night"),
            opened(RECEIPT_SLUG, 479.5, "land", "handoff"),
        ),
    ),
)
# The board server's record of what it sent to the owner's Inbox: the breaker of the gift note,
# as `main`'s `lem_inbox.Watcher` writes it. A page shows it only while he is away.
INBOX = {
    "running": True,
    "url": "http://plannotator.localhost:50026/",
    "tailnet_url": INBOX_TAILNET,
    "why": None,
    "said": "",
    "problem": None,
    "sent": [
        {
            "key": "breaker:gift-note-in-export:1:20261125T154000Z",
            "task": "gift-note-in-export",
            "kind": "breaker",
            "form": "question",
            "asks": True,
            "session": "6f1c2a9e-demo",
            "tip": None,
            "message_id": "msg_01DEMOGIFTNOTEBREAKER1",
            "thread_id": "msg_01DEMOGIFTNOTEBREAKER1",
            "thread_url": (
                "http://plannotator.localhost:50026/#thread=msg_01DEMOGIFTNOTEBREAKER1"
            ),
            "questions": ["q1"],
            "woke": [],
        }
    ],
}
# The reviewer's items of the state folder's backlog, by name, from the night's and the
# retro's proposals: one undecided, one the parked task holds, one refuted.
REVIEWED = (
    (
        "read-the-receipt-s-total-by-its-label.md",
        """---
worth: later
where: AGENTS.md
added: 2026-11-25
proposals: retro of 2026-11-25 #1
---
# Read the receipt's total by its label

The reviewer passed 1 proposal about lessons on 2026-11-25: retro of 2026-11-25 #1.

## Read the receipt's total by its label, never by its row

From the retro of 2026-11-25, proposal 1. Its source: the task refund-line-on-receipt's records. Where: `AGENTS.md`.

A refund line moved the total's row, and a test that read the row failed.
""",
    ),
    (
        "the-export-s-check-fails-by-chance.md",
        """---
worth: later
where: tests/test_export.py:test_monthly
added: 2026-11-25
proposals: night of 2026-11-25 #1
---
# The export's check fails by chance

The reviewer passed 1 proposal about tests on 2026-11-25: night of 2026-11-25 #1.

## Make the check of the monthly export wait for its file

From the night of 2026-11-25, proposal 1. Its source: the checks of coupon-has-a-slug. Where: `tests/test_export.py:test_monthly`.

The check read the export before its file was whole, and failed once in the last ten runs.
""",
    ),
    (
        "run-make-lint-before-each-commit.md",
        """---
worth: no
where: AGENTS.md
added: 2026-11-25
proposals: retro of 2026-11-25 #2
---
# Run make lint before each commit

The reviewer refuted retro of 2026-11-25 #2 on 2026-11-25.

From the retro of 2026-11-25, proposal 2. Its source: the task coupon-has-a-slug's records. Where: `AGENTS.md`.

A builder forgot it once.

Decided against: a first-time lesson, with no question in it
""",
    ),
)


def write(path: Path, body: str | bytes) -> None:
    """Write a file whole, its folder made first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(body, bytes):
        path.write_bytes(body)
    else:
        path.write_text(body, encoding="utf-8")


def lay(folder: Path) -> Path:
    """The afternoon in a main checkout under `folder`: its `.git` and `.lem`, each task's
    record through the store, Lem's acts on its sessions, its files and pictures, the
    backlog's items and the reviewer's, the Inbox's record and the mark of demo data. Gives
    the checkout."""
    checkout = folder / "shop"
    (checkout / ".git").mkdir(parents=True)
    (checkout / ".lem").mkdir()
    state = places.state_of(checkout)
    write(state / "demo", "The tasks in this folder are examples.\n")
    for each in RECORDS:
        tasks.create(state, each)
    for slug, acts in ACTS:
        for act in acts:
            log.append(places.task_folder(state, slug), act)
    for slug, name, body in FILES:
        write(places.task_folder(state, slug) / name, body)
    for slug, name in PICTURES:
        write(places.task_folder(state, slug) / name, PNG)
    for name, body in BACKLOG:
        write(checkout / name, body)
    for name, body in REVIEWED:
        write(state / "backlog" / name, body)
    write(state / "inbox.json", json.dumps(INBOX, indent=2) + "\n")
    return checkout
