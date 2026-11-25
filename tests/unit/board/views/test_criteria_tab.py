"""The tab Criteria and decisions of the refund line, as today's board draws it: the plan's How
it works, the read and the approval, each criterion with its case, its chart and its test, and
the two decisions, the important one with its story and its chart."""

from typing import TYPE_CHECKING

from fixtures.board import panel
from fixtures.board.receipt import SLUG
from lem.board.views import owed
from lem.board.views.criteria.tab import criteria
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path


def test_the_refund_line_s_criteria_and_decisions_are_today_s(tmp_path: Path) -> None:
    """The ruling "Stories, flowcharts and pictures early"
    (`ruling:stories-flowcharts-and-pictures-early-cbb94ea4fd6cc50d`): a decision's story and
    its chart, a criterion's case and its chart, as `main`'s board draws them."""
    found = world(tmp_path)
    assert criteria(found, owed.seen(found, SLUG)) == panel.CRITERIA
