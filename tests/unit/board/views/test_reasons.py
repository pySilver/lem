"""The reasons a pull request is not green, cut into rows as the board lists them
(`main`'s `board_model.reason_parts` and `board_pages.reason_list`)."""

from typing import TYPE_CHECKING

import msgspec

from fixtures.board import waiting
from fixtures.board.moments import BASE
from fixtures.board.receipt import RECEIPT, SLUG
from lem.board.views import owed
from lem.board.views.reasons import reasons
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def proposing(*lines: str, green: bool = False) -> Record:
    """The refund line's record with a proposal of `lines`."""
    landing = RECEIPT.landing
    assert landing is not None
    assert landing.proposed is not None
    proposed = msgspec.structs.replace(landing.proposed, reasons=lines, green=green)
    changed = msgspec.structs.replace(landing, proposed=proposed)
    return msgspec.structs.replace(RECEIPT, landing=changed)


def test_the_refund_lines_four_reasons_are_the_rows_every_list_shows(
    tmp_path: Path,
) -> None:
    """`main`'s `test_board_model.py` Merge.test_not_green_has_the_proposals_reasons: the
    proposal's reasons, each a row with its head, what it is about, its detail and its link."""
    record = owed.seen(world(tmp_path), SLUG).record
    key = f"wr-{SLUG}"
    assert reasons(record, key, "waits", BASE) == waiting.reasons(key, "waits")
    for key in ("v", "pr", "cf"):
        assert reasons(record, key, None, BASE) == waiting.reasons(key, None)


def test_a_green_proposal_or_none_has_no_reasons() -> None:
    assert reasons(proposing(green=True), "v", None, BASE) is None
    bare = msgspec.structs.replace(RECEIPT, landing=None)
    assert reasons(bare, "v", None, BASE) is None


def test_a_breaker_reason_links_to_its_row_and_a_quote_or_code_stays_whole() -> None:
    record = proposing(
        "breaker 2 waits for the owner: it stopped. The case (a `a; b` path) stays",
        'the bar is lower: "one; two". It says so in acme/web#7',
    )
    found = reasons(record, "k", "tasks", BASE)
    assert found is not None
    first, second = found.rows
    assert first.head == "Breaker 2 waits for the owner"
    assert first.ref is not None
    assert (first.ref.label, first.ref.anchor) == ("breaker 2", "dec-2")
    assert first.detail == ("It stopped", "The case (a `a; b` path) stays")
    assert second.ref is None
    assert second.detail == (
        '"one; two"',
        "It says so in [acme/web#7](https://github.com/acme/web/pull/7)",
    )


def test_a_proposal_with_no_line_is_an_empty_list() -> None:
    found = reasons(proposing(), "v", None, BASE)
    assert found is not None
    assert found.rows == ()
