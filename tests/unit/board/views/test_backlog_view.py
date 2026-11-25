"""The afternoon's backlog as the views read it and show it: the Backlog view, its keys, its
rows of the search, and the count on the Backlog key, each the fixture of
`tests/fixtures/board/`.

`lay` writes the items and the reviewer's items, not the code they name: each case writes
`invoice/footer.py`, `AGENTS.md` and `tests/test_export.py` as `main`'s showcase did, so that
every place an item names is still there.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from msgspec import structs

from fixtures.board.frame import SEARCH
from fixtures.board.moments import BASE, NOW
from fixtures.board.shelves import BACKLOG, KEYS
from lem.board.views.backlog import groups, search, view
from lem.board.views.backlog.ledger import Adding
from lem.board.views.backlog.read import read
from lem.board.views.backlog.wanted import Wanted, wanted
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import World

FOOTER = "docs/backlog/invoice-footer-wraps.md"
QUERY = "docs/backlog/export-in-one-query.md"
# The code the afternoon's items name, as `main`'s showcase writes it.
CODE = (
    ("invoice/footer.py", "def footer(order):\n    return order.shop.address\n"),
    ("AGENTS.md", "# The shop\n\nRun `make test` and `make lint` before a commit.\n"),
    ("tests/test_export.py", "def test_monthly():\n    assert True\n"),
)


class AfternoonLedger:
    """Git's answers of the afternoon: both items of the backlog folder committed by `t` on
    2026-11-25, in a commit that names no task, and nothing git does not have."""

    def __init__(self, unsaved: tuple[tuple[str, str], ...] = ()) -> None:
        self.left = unsaved

    def adds(self, where: Path, folder: str) -> tuple[Adding, ...] | None:
        paths = (QUERY, FOOTER)
        return (
            Adding(
                author="t", day="2026-11-25", subject="docs: the backlog", paths=paths
            ),
        )

    def unsaved(self, where: Path, folder: str) -> tuple[tuple[str, str], ...] | None:
        return self.left


def laid(folder: Path, git: AfternoonLedger | None = None) -> World:
    """The afternoon with its backlog read, the code its items name written."""
    seen = world(folder)
    checkout = folder / "shop"
    for name, body in CODE:
        path = checkout / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    shelved = read(checkout, seen.place, git or AfternoonLedger(), NOW)
    return replace(seen, backlog=shelved)


def records_of(seen: World) -> tuple:
    return tuple(each.record for each in seen.tasks)


def test_the_afternoon_s_backlog_is_the_reviewer_s_items_then_the_items_by_worth(
    tmp_path: Path,
) -> None:
    """The fixture's view: the reviewer's undecided item, then the one the parked task holds,
    then Worth doing, Later, and the refuted proposal under Decided against."""
    seen = laid(tmp_path)
    assert view.backlog(seen, Wanted()) == BACKLOG
    assert view.KEYS == KEYS


def test_the_search_lists_the_afternoon_s_items_in_the_order_of_the_view(
    tmp_path: Path,
) -> None:
    """The item rows of the fixture's search (`main`'s
    `test_board_model.py` Search.test_criterion_4_the_order_..._then_the_backlog_by_worth,
    the backlog's part): the reviewer's undecided item, the held one, then by worth."""
    seen = laid(tmp_path)
    items = tuple(row for row in SEARCH.rows if row.kind == "item")
    assert search.search_rows(seen.backlog, records_of(seen), BASE) == items


def test_the_backlog_key_counts_the_afternoon_s_one_undecided_item(
    tmp_path: Path,
) -> None:
    seen = laid(tmp_path)
    assert groups.undecided(seen.backlog, records_of(seen)) == 1


def test_the_filter_of_the_address_turns_its_chip_on_and_a_second_press_off(
    tmp_path: Path,
) -> None:
    seen = laid(tmp_path)
    shown = view.backlog(seen, wanted({"worth": ["yes"], "q": [" footer "]}))
    chips = {(chip.key, chip.shown): chip for chip in shown.filters}
    assert shown.query == "footer"
    assert not shown.every.on
    assert chips["worth", "yes"].on
    assert chips["worth", "yes"].href == f"{BASE}/backlog?q=footer"
    assert chips["worth", "later"].href == f"{BASE}/backlog?q=footer&worth=later"
    # every item stays: the page's controller hides those the filter leaves out
    assert sum(len(shelf.entries) for shelf in shown.shelves) == 5
    # a value the filter does not know is no filter
    assert wanted({"worth": ["maybe"], "only": ["old"]}) == Wanted()


def test_an_item_git_does_not_have_is_new_and_not_committed(tmp_path: Path) -> None:
    """An item the closing pass filed a minute ago: new, not committed, and counted by the
    chip Not committed; one with a change since is edited."""
    git = AfternoonLedger(unsaved=(("??", QUERY), (" M", FOOTER)))
    shown = view.backlog(laid(tmp_path, git), Wanted())
    entries = {entry.key: entry for shelf in shown.shelves for entry in shelf.entries}
    query, footer = entries["export-in-one-query"], entries["invoice-footer-wraps"]
    assert query.new
    assert [tag.label for tag in query.tags] == ["new, not committed", "today"]
    assert [tag.label for tag in footer.tags] == ["edited, not committed", "today"]
    chips = {chip.shown: chip.count for chip in shown.filters}
    assert chips["new"] == 2


def test_with_no_answer_from_git_no_line_says_who_added_an_item(tmp_path: Path) -> None:
    class Silent(AfternoonLedger):
        def adds(self, where: Path, folder: str) -> tuple[Adding, ...] | None:
            return None

    shown = view.backlog(laid(tmp_path, Silent()), Wanted())
    entries = {entry.key: entry for shelf in shown.shelves for entry in shelf.entries}
    assert entries["invoice-footer-wraps"].added is None
    assert entries["-read-the-receipt-s-total-by-its-label"].added is not None


def test_a_page_that_may_not_act_gives_the_line_to_type(tmp_path: Path) -> None:
    seen = laid(tmp_path)
    away = replace(seen, viewer=structs.replace(seen.viewer, may_act=False))
    shown = view.backlog(away, Wanted())
    receipt = shown.shelves[0].entries[0].holds
    assert receipt.start is None
    assert (
        receipt.typed
        == "/lem new .lem/state/backlog/read-the-receipt-s-total-by-its-label.md"
    )
    assert (
        receipt.note == "Drop it on this board on the Mac or through the tailnet door."
    )


def test_with_no_read_the_view_says_so_and_the_key_counts_nothing(
    tmp_path: Path,
) -> None:
    seen = world(tmp_path)
    shown = view.backlog(seen, Wanted())
    assert shown.empty == "The backlog was not read: the status bar says why."
    assert shown.shelves == ()
    assert groups.undecided(None, records_of(seen)) is None
    assert search.search_rows(None, records_of(seen), BASE) == ()
