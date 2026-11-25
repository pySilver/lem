"""The showcase afternoon as the views read it: `fixtures.board.beside.lay` in a folder of the
case, gathered at the fixture's minute for the owner on this Mac, with git's answers of the
afternoon (the refund line's newest commit, and no backlog item filed on its branch).

Each fixture of `tests/fixtures/board/` is what a view gives of this world.
"""

from typing import TYPE_CHECKING

from fixtures.board.beside import lay
from fixtures.board.moments import NOW, sha
from fixtures.board.receipt import TIP
from fixtures.board.shown import VERSION, VIEWER, ZONE
from lem.board.views.gather import Ask, gather
from lem.board.views.world import Clock, Place
from lem.ports.git_facts import Commit

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import World

RECEIPT_BRANCH = "feat/refund-line-on-receipt"
SUBJECT = "docs(plans): the refund line on the receipt"
BASE = sha("main under the receipt")
# The workspace's path as the showcase's machine has it.
PATH = "/work/shop"
PLACE = Place(repo="shop", base="main", path=PATH)


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


def world(folder: Path) -> World:
    """The afternoon laid in `folder`, as the views read it."""
    checkout = lay(folder)
    ask = Ask(
        viewer=VIEWER,
        clock=Clock(now=NOW, zone=ZONE),
        version=VERSION,
        place=PLACE,
        home=folder / "home",
        git=AfternoonGit(),
    )
    return gather(checkout, ask)
