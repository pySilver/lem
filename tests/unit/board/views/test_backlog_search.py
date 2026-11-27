"""The backlog's part of the search over every card and the count on the Backlog key
(`main`'s `tests/unit/test_board_model.py` Search): the reviewer's items before the others, the
undecided ones first, then the other items by their worth, a refuted one under Decided against
and never counted."""

from datetime import UTC, datetime

from msgspec import structs

from fixtures.board.held import CHECK
from fixtures.board.moments import BASE
from lem.board.views.backlog import counts, groups, search
from lem.board.views.backlog_read import Entry, Shelved

NOW = datetime(2026, 11, 22, 10, 0, tzinfo=UTC)
FLAKY = ".lem/state/backlog/a-flaky-check.md"
# The task that started from the reviewer's flaky check, and builds it.
HOLDER = structs.replace(
    CHECK,
    task=structs.replace(
        CHECK.task,
        slug="flaky-export-check",
        status="building",
        hold=None,
        backlog_item=FLAKY,
        after=(),
    ),
)


def folder(stem: str, title: str, worth: str | None = None) -> Entry:
    return Entry(path=f"docs/backlog/{stem}.md", key=stem, title=title, worth=worth)


def mine(stem: str, title: str, worth: str = "later") -> Entry:
    path = f".lem/state/backlog/{stem}.md"
    return Entry(path=path, key=f"-{stem}", reviewer=True, title=title, worth=worth)


# As the read gives them: the backlog folder's items, then the reviewer's, a held one before
# an undecided one.
ENTRIES = (
    folder("export-in-one-query", "Read the monthly export in one query", "later"),
    folder("odd-item", "An item with no worth"),
    folder(
        "the-board-s-done-column-has-no-limit",
        "The board's done column has no limit",
        "yes",
    ),
    folder("a-thing-not-to-do", "A thing not to do", "no"),
    mine("a-flaky-check", "A check of the export fails by chance"),
    mine("export-in-one-query", "The lessons of the export"),
)
SHELVED = Shelved(
    folder="docs/backlog", reviewer=".lem/state/backlog", entries=ENTRIES, read=NOW
)


def test_criterion_4_the_backlog_by_worth_after_the_reviewer_s_undecided_and_held_items() -> (
    None
):
    """The backlog's part of `main`'s Search.test_criterion_4_the_order_the_columns_then_the_
    parked_then_every_ended_task_newest_first_then_the_backlog_by_worth, and of
    Search.test_criterion_5_each_chip_says_its_place_and_its_state_in_the_color_of_its_column:
    an item of each folder with one stem is two rows."""
    rows = search.search_rows(SHELVED, (HOLDER,), BASE)
    assert [(row.key, row.chip, row.look) for row in rows] == [
        ("-export-in-one-query", "Backlog · undecided", "you"),
        ("-a-flaky-check", "Backlog · held by flaky-export-check", "lead"),
        ("the-board-s-done-column-has-no-limit", "Backlog · worth: yes", "gate"),
        ("export-in-one-query", "Backlog · worth: later", "you"),
        ("odd-item", "Backlog · worth: unset", "quiet"),
        ("a-thing-not-to-do", "Backlog · worth: no", "quiet"),
    ]
    assert rows[0].href == f"{BASE}/backlog#item--export-in-one-query"
    assert not any(row.open or row.frame for row in rows)


def test_criterion_2_every_backlog_item_is_a_row_and_no_read_gives_none() -> None:
    """The backlog's part of `main`'s Search.test_criterion_2_every_task_a_parked_one_and_an_
    ended_one_done_draws_no_card_for_and_every_backlog_item."""
    rows = search.search_rows(SHELVED, (HOLDER,), BASE)
    assert len(rows) == len(ENTRIES)
    assert {row.kind for row in rows} == {"item"}
    assert search.search_rows(None, (HOLDER,), BASE) == ()


def test_the_undecided_count_is_the_reviewer_s_items_no_task_holds() -> None:
    assert groups.undecided(SHELVED, (HOLDER,)) == 1
    folder_only = structs.replace(SHELVED, entries=ENTRIES[:4])
    assert groups.undecided(folder_only, (HOLDER,)) == 0
    assert groups.undecided(None, (HOLDER,)) is None


def test_a_task_that_ended_holds_its_item_no_more() -> None:
    dropped = structs.replace(
        HOLDER, task=structs.replace(HOLDER.task, status="dropped")
    )
    assert groups.undecided(SHELVED, (dropped,)) == 2
    assert groups.holder((dropped,), FLAKY) is None


def test_criterion_4_a_refuted_item_of_the_reviewer_is_not_counted_and_is_under_decided_against() -> (
    None
):
    """`main`'s Search.test_criterion_4_a_refuted_item_of_the_reviewer_is_not_counted_and_is_
    under_decided_against: two of the reviewer's items that wait for the owner and one refuted
    give 2 on the key, and the view lists all 3."""
    shelved = structs.replace(
        SHELVED,
        entries=(
            mine("the-board-s-colors", "The board's colors"),
            mine("run-make-lint-before-each-commit", "Run make lint", "no"),
            mine("a-flaky-check", "A flaky check"),
        ),
    )
    assert counts.work_count(shelved) == 2
    assert groups.undecided(shelved, ()) == 2
    waiting = groups.reviewer_entries(shelved, ())
    assert [entry.key for entry, _ in waiting] == [
        "-the-board-s-colors",
        "-a-flaky-check",
    ]
    refused = groups.worth_entries(shelved, "no")
    assert [entry.key for entry in refused] == ["-run-make-lint-before-each-commit"]
    rows = {row.key: row.chip for row in search.search_rows(shelved, (), BASE)}
    assert rows == {
        "-the-board-s-colors": "Backlog · undecided",
        "-a-flaky-check": "Backlog · undecided",
        "-run-make-lint-before-each-commit": "Backlog · worth: no",
    }
