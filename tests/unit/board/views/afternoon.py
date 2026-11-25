"""The showcase afternoon as the views read it: `fixtures.board.beside.lay` in a folder of the
case, gathered at the fixture's minute for the owner on this Mac, with git's answers of the
afternoon (the refund line's newest commit, no backlog item filed on its branch, both items of
the backlog folder committed by `t` that day) and the code its items name, which `lay` does not
write and `main`'s showcase did (`invoice/footer.py`, `AGENTS.md`, `tests/test_export.py`), so
that every place an item names is still there.

Each fixture of `tests/fixtures/board/` is what a view gives of this world.
"""

from dataclasses import replace as change
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fixtures.board.beside import lay
from fixtures.board.moments import NOW, sha
from fixtures.board.receipt import TIP
from fixtures.board.shown import VERSION, VIEWER, ZONE
from lem.board.views import folder as documents
from lem.board.views.ask import Ask
from lem.board.views.backlog.ledger import Adding
from lem.board.views.gather import gather
from lem.board.views.world import Clock, Place
from lem.ports.git_facts import Commit
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.layout import Viewer
    from lem.board.views.world import World

RECEIPT_BRANCH = "feat/refund-line-on-receipt"
SUBJECT = "docs(plans): the refund line on the receipt"
BASE = sha("main under the receipt")
# The workspace's path as the showcase's machine has it.
PATH = "/work/shop"
PLACE = Place(repo="shop", base="main", path=PATH)
FOOTER = "docs/backlog/invoice-footer-wraps.md"
QUERY = "docs/backlog/export-in-one-query.md"
# The code the afternoon's items name, as `main`'s showcase writes it.
CODE = (
    ("invoice/footer.py", "def footer(order):\n    return order.shop.address\n"),
    ("AGENTS.md", "# The shop\n\nRun `make test` and `make lint` before a commit.\n"),
    ("tests/test_export.py", "def test_monthly():\n    assert True\n"),
)


class AfternoonGit:
    """Git's answers of the afternoon: one branch, the refund line's, with its newest commit
    on the base, and no file added on it."""

    def tip(self, where: Path, ref: str) -> str | None:
        return TIP if ref == RECEIPT_BRANCH else None

    def merge_base(self, where: Path, first: str, second: str) -> str | None:
        return BASE

    def commits(self, where: Path, since: str, until: str) -> tuple[Commit, ...]:
        return (Commit(sha=TIP, parents=(BASE,), subject=SUBJECT),)

    def changed_paths(self, where: Path, since: str, until: str) -> tuple[str, ...]:
        return ("receipt/lines.py", "tests/test_receipt.py")

    def show(self, where: Path, rev: str, path: str) -> bytes | None:
        return None


class AfternoonLedger:
    """Git's answers of the afternoon's backlog: both items of the backlog folder committed by
    `t` on 2026-11-25, in a commit that names no task, and nothing git does not have."""

    def adds(self, where: Path, folder: str) -> tuple[Adding, ...] | None:
        paths = (QUERY, FOOTER)
        return (
            Adding(
                author="t", day="2026-11-25", subject="docs: the backlog", paths=paths
            ),
        )

    def unsaved(self, where: Path, folder: str) -> tuple[tuple[str, str], ...] | None:
        return ()


def world(folder: Path, viewer: Viewer | None = None) -> World:
    """The afternoon for one viewer, or all its fixture prose for direct view tests."""
    checkout = lay(folder)
    for name, body in CODE:
        path = checkout / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    ask = Ask(
        viewer=viewer or VIEWER,
        clock=Clock(now=NOW, zone=ZONE),
        version=VERSION,
        place=PLACE,
        home=folder / "home",
        git=AfternoonGit(),
        ledger=AfternoonLedger(),
    )
    seen = gather(checkout, ask)
    if viewer is not None:
        return seen
    state = places.state_of(checkout)
    tasks = tuple(
        replace(
            task,
            prose=documents.prose_of(
                places.task_folder(state, task.record.task.slug), task.files
            ),
        )
        for task in seen.tasks
    )
    return change(seen, tasks=tasks)
