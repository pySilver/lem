"""The afternoon's view Backlog, as today's board draws it: the reviewer's two items (one
undecided, one a parked task holds), then the backlog's items by their worth, the refuted
proposal under Decided against."""

from typing import TYPE_CHECKING

from fixtures.board.moments import BASE
from fixtures.board.shown import document, task
from lem.board.inputs.backlog import Added, Backlog, Entry, Filter, Holds, Shelf
from lem.board.inputs.forms import ActForm, Field
from lem.board.inputs.layout import KeyGroup, Keys
from lem.board.inputs.parts import Chip, Link

if TYPE_CHECKING:
    from lem.board.inputs.text import Look

REVIEWER = (
    "added by the reviewer of the night's and the retro's proposals on 2026-11-25"
)
OPENS = "Lem opens the task's own session in agterm, which reads this item."
TODAY = Chip(label="today", title="added 2026-11-25")
STATE = ".lem/state/backlog"


def start(path: str) -> ActForm:
    """The form that starts a task from the item at `path`."""
    return ActForm(
        action=f"{BASE}/start",
        label="Start a task",
        icon="play",
        press="go",
        busy="Starting…",
        fields=(Field(name="item", shown=path),),
    )


def drop(path: str) -> ActForm:
    """The form that drops the reviewer's item at `path`."""
    return ActForm(
        action=f"{BASE}/backlog/drop",
        label="Drop",
        icon="xmark",
        busy="Dropping…",
        fields=(Field(name="item", shown=path),),
    )


RECEIPT_TEXT = (
    "The reviewer passed 1 proposal about lessons on 2026-11-25: `retro of 2026-11-25 #1`."
    "\n\n## Read the receipt's total by its label, never by its row\n\n"
    "From the retro of 2026-11-25, proposal 1. Its source: the task refund-line-on-receipt's "
    "records. Where: `AGENTS.md`.\n\n"
    "A refund line moved the total's row, and a test that read the row failed."
)
CHECK_TEXT = (
    "The reviewer passed 1 proposal about tests on 2026-11-25: `night of 2026-11-25 #1`."
    "\n\n## Make the check of the monthly export wait for its file\n\n"
    "From the night of 2026-11-25, proposal 1. Its source: the checks of "
    "coupon-has-a-slug. Where: `tests/test_export.py:test_monthly`.\n\n"
    "The check read the export before its file was whole, and failed once in the last ten "
    "runs."
)
LINT_TEXT = (
    "The reviewer refuted `retro of 2026-11-25 #2` on 2026-11-25.\n\n"
    "From the retro of 2026-11-25, proposal 2. Its source: the task coupon-has-a-slug's "
    "records. Where: `AGENTS.md`.\n\n"
    "A builder forgot it once.\n\n"
    "Decided against: a first-time lesson, with no question in it"
)
FOOTER_TEXT = (
    "Seen in the polish pass of the order date: the footer's last line wraps when the "
    "invoice prints on A5."
)
QUERY_TEXT = (
    "The investigation of the slow export found one query for each order. One query for "
    "the month would take the minute away."
)
RECEIPT_ITEM = Entry(
    key="-read-the-receipt-s-total-by-its-label",
    path=f"{STATE}/read-the-receipt-s-total-by-its-label.md",
    title="Read the receipt's total by its label",
    worth="later",
    tags=(
        Chip(
            label="undecided",
            look="you",
            title="No task builds this item, and you have not dropped it",
        ),
        TODAY,
    ),
    where="AGENTS.md",
    added=Added(said=REVIEWER),
    body=document("bl--read-the-receipt-s-total-by-its-label", RECEIPT_TEXT),
    holds=Holds(
        start=start(f"{STATE}/read-the-receipt-s-total-by-its-label.md"),
        drop=drop(f"{STATE}/read-the-receipt-s-total-by-its-label.md"),
        note=(
            "Start a task opens its own session in agterm, which reads this item. Drop "
            "removes the file, and the day's record of the proposals keeps the drop, so no "
            "later reviewer proposes it again."
        ),
    ),
)
CHECK_ITEM = Entry(
    key="-the-export-s-check-fails-by-chance",
    path=f"{STATE}/the-export-s-check-fails-by-chance.md",
    title="The export's check fails by chance",
    worth="later",
    tags=(
        Chip(
            label="held by export-check-by-chance",
            look="lead",
            title="The task export-check-by-chance builds this item",
        ),
        TODAY,
    ),
    where="tests/test_export.py:test_monthly",
    added=Added(said=REVIEWER),
    body=document("bl--the-export-s-check-fails-by-chance", CHECK_TEXT),
    holds=Holds(
        held_by=Link(
            href=task("export-check-by-chance", under="backlog"),
            label="export-check-by-chance",
            frame=True,
        ),
        held=(
            "(parked) builds this item. It leaves the backlog with that task's landing, and "
            "is undecided again when the task is dropped."
        ),
    ),
)
FOOTER_ITEM = Entry(
    key="invoice-footer-wraps",
    path="docs/backlog/invoice-footer-wraps.md",
    title="The invoice footer wraps on A5",
    worth="yes",
    tags=(TODAY,),
    where="invoice/footer.py:footer",
    added=Added(said="added by t on 2026-11-25"),
    body=document("bl-invoice-footer-wraps", FOOTER_TEXT),
    holds=Holds(start=start("docs/backlog/invoice-footer-wraps.md"), note=OPENS),
)
QUERY_ITEM = Entry(
    key="export-in-one-query",
    path="docs/backlog/export-in-one-query.md",
    title="Read the monthly export in one query",
    worth="later",
    tags=(TODAY,),
    where="no place in the code named",
    added=Added(said="added by t on 2026-11-25"),
    body=document("bl-export-in-one-query", QUERY_TEXT),
    holds=Holds(start=start("docs/backlog/export-in-one-query.md"), note=OPENS),
)
LINT_ITEM = Entry(
    key="-run-make-lint-before-each-commit",
    path=f"{STATE}/run-make-lint-before-each-commit.md",
    title="Run make lint before each commit",
    worth="no",
    tags=(TODAY,),
    where="AGENTS.md",
    added=Added(said=REVIEWER),
    body=document("bl--run-make-lint-before-each-commit", LINT_TEXT),
    holds=Holds(
        start=start(f"{STATE}/run-make-lint-before-each-commit.md"), note=OPENS
    ),
)


def chip(
    key: str, shown: str, label: str, look: Look, count: int, title: str
) -> Filter:
    """A chip of the filter, off."""
    return Filter(
        key=key,
        shown=shown,
        label=label,
        look=look,
        count=count,
        href=f"{BASE}/backlog?{key}={shown}",
        title=title,
    )


BACKLOG = Backlog(
    summary=(
        "2 items in docs/backlog · 3 of the reviewer in .lem/state/backlog, 1 undecided · "
        "read 16:00"
    ),
    read_again=f"{BASE}/backlog?read=1",
    every=Filter(
        key="",
        shown="",
        label="All",
        count=5,
        on=True,
        href=f"{BASE}/backlog",
        title="Every item: the filter off",
    ),
    filters=(
        chip(
            "worth",
            "yes",
            "Worth doing",
            "gate",
            1,
            "Only the items whose worth is yes",
        ),
        chip(
            "worth", "later", "Later", "you", 3, "Only the items whose worth is later"
        ),
        chip(
            "worth",
            "no",
            "Decided against",
            "quiet",
            1,
            "Only the items whose worth is no",
        ),
        chip(
            "only",
            "stale",
            "Where no longer resolves",
            "bad",
            0,
            "Only the items where the place the item names is not there any more",
        ),
        chip(
            "only",
            "new",
            "Not committed",
            "gate",
            0,
            "Only the items added or edited, and not committed yet",
        ),
    ),
    shelves=(
        Shelf(
            key="reviewer",
            look="you",
            name="The reviewer's items",
            title=(
                "What the night and the retro proposed and the reviewer passed, in "
                ".lem/state/backlog: start a task or drop it"
            ),
            entries=(RECEIPT_ITEM, CHECK_ITEM),
        ),
        Shelf(key="yes", look="gate", name="Worth doing", entries=(FOOTER_ITEM,)),
        Shelf(key="later", look="you", name="Later", entries=(QUERY_ITEM,)),
        Shelf(
            key="no",
            look="quiet",
            name="Decided against",
            recessive=True,
            entries=(LINT_ITEM,),
        ),
    ),
)
KEYS = Keys(
    id="backlog-keys",
    groups=(
        KeyGroup(keys=("/",), word="filter"),
        KeyGroup(keys=("J", "K"), word="move"),
        KeyGroup(keys=("Enter",), word="open or close"),
        KeyGroup(keys=("R",), word="read again"),
    ),
)
