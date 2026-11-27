"""The showcase afternoon as records: eleven tasks written through the store and read back
whole, each journal in the order of its moments, Lem's acts on their sessions beside them, and
every file a record cites in its task's folder."""

from hashlib import sha256
from typing import TYPE_CHECKING

import msgspec
import pytest

from fixtures.board import panel
from fixtures.board.beside import ACTS, RECORDS, lay
from fixtures.board.moments import NOW
from lem.app.landing import world
from lem.app.sessions import log
from lem.model.landing import checks
from lem.model.landing.world import Held, World
from lem.records.decisions import Breaker
from lem.records.holds import Parked
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def test_each_task_of_the_afternoon_is_one_record_the_store_reads_back_whole(
    tmp_path: Path,
) -> None:
    state = places.state_of(lay(tmp_path))
    read = tasks.every(state)
    assert read == tuple(sorted(RECORDS, key=lambda each: each.task.slug))
    statuses = {each.task.slug: each.task.status for each in read}
    assert statuses == {
        "cart-total-after-coupon": "building",
        "coupon-has-a-slug": "landing",
        "export-check-by-chance": "queued",
        "fee-notice-to-merchants": "building",
        "footer-terms-typo": "landed",
        "gift-note-in-export": "building",
        "order-date-on-invoice": "landed",
        "refund-line-on-receipt": "open",
        "refund-rounding": "building",
        "stock-on-product-page": "shaping",
        "why-export-is-slow": "answered",
    }


@pytest.mark.parametrize(
    "record",
    [each for each in RECORDS if each.landing and each.landing.checked],
    ids=lambda each: each.task.slug,
)
def test_the_afternoons_passed_checks_cover_the_proposed_tip(
    record: Record, tmp_path: Path
) -> None:
    workspace = places.workspace(lay(tmp_path))
    record = tasks.read(workspace.state, record.task.slug)
    landing = record.landing
    assert landing and landing.checked and landing.proposed and record.task.branch
    rules = world.rules(workspace)
    assert rules.commands == tuple(each.command for each in landing.checked.outcomes)
    current = World(
        rules=rules,
        branch=record.task.branch,
        base=landing.proposed.base,
        base_tree=landing.checked.base_tree or "",
        tip=landing.proposed.tip,
        now=NOW,
    )
    assert checks.holds(record, current) == Held(why="the checks passed on this tip")


def test_each_journal_is_in_the_order_of_its_moments_and_none_is_after_now() -> None:
    for each in RECORDS:
        moments = [entry.at for entry in each.journal]
        assert moments == sorted(moments), each.task.slug
        assert all(moment <= NOW for moment in moments), each.task.slug
        assert each.task.opened <= each.task.since <= NOW, each.task.slug


def test_the_two_parked_tasks_and_their_holds_keep_their_status() -> None:
    parked = {
        each.task.slug: each.task.status
        for each in RECORDS
        if isinstance(each.task.hold, Parked)
    }
    assert parked == {
        "fee-notice-to-merchants": "building",
        "export-check-by-chance": "queued",
    }


def test_lems_acts_on_each_tasks_sessions_read_back_beside_its_record(
    tmp_path: Path,
) -> None:
    state = places.state_of(lay(tmp_path))
    for slug, acts in ACTS:
        assert log.read(places.task_folder(state, slug)) == acts
    assert log.read(places.task_folder(state, "cart-total-after-coupon")) == ()


def cited(slug: str) -> set[str]:
    """Every path in its task's folder that a record of the afternoon cites."""
    record = next(each for each in RECORDS if each.task.slug == slug)
    paths: set[str] = set()
    for decision in record.task.decisions:
        if isinstance(decision, Breaker):
            paths |= {decision.document, decision.handoff}
    if record.task.investigation and record.task.investigation.report:
        paths.add(record.task.investigation.report)
    landing = record.landing
    if landing and landing.checked:
        paths |= {outcome.output for outcome in landing.checked.outcomes}
    if landing and landing.proposed:
        paths |= {
            path
            for path in (landing.proposed.text, landing.proposed.notes_path)
            if path
        }
    return paths


def test_every_file_a_record_cites_is_in_its_tasks_folder(tmp_path: Path) -> None:
    state = places.state_of(lay(tmp_path))
    for each in RECORDS:
        slug = each.task.slug
        for path in cited(slug):
            assert (places.task_folder(state, slug) / path).is_file(), (slug, path)
    assert cited("refund-line-on-receipt") == {
        "checks/r1-1-000000000001.log",
        "checks/r1-2-000000000002.log",
        "pr.md",
        "decisions.md",
    }


def test_the_records_are_the_form_this_release_writes_and_reads() -> None:
    for each in RECORDS:
        encoded = tasks.encode(each)
        assert msgspec.json.decode(encoded, type=type(each)) == each


def test_the_overview_shows_the_two_receipts_from_the_showcase(tmp_path: Path) -> None:
    # The two calls to receipt() in main:tests/board-showcase.py produce these PNGs.
    state = places.state_of(lay(tmp_path))
    media = places.task_folder(state, panel.SLUG) / "media"
    assert panel.OVERVIEW.building
    (shot,) = panel.OVERVIEW.building.shots
    assert shot.before
    names = [picture.src.rsplit("/", 1)[-1] for picture in (shot.before, shot.after)]
    assert [sha256((media / name).read_bytes()).hexdigest() for name in names] == [
        "f1867e74b53234dee82e893d6c5d589104f48039e0443b18c36215d5c430a92d",
        "59e8c460fa8e186a3726fff065aa5adba44a6092ee046b7fabedecf1b7a07fb1",
    ]
