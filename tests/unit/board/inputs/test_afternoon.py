"""The showcase afternoon as records: eleven tasks written through the store and read back
whole, each journal in the order of its moments, Lem's acts on their sessions beside them, and
every file a record cites in its task's folder."""

from typing import TYPE_CHECKING

import msgspec

from fixtures.board.beside import ACTS, RECORDS, lay
from fixtures.board.moments import NOW
from lem.app.sessions import log
from lem.records.decisions import Breaker
from lem.records.holds import Parked
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path


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
    if record.task.criteria.change:
        paths.add(record.task.criteria.change.text)
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
        "gate/01.log",
        "gate/02.log",
        "pr.md",
        "decisions.md",
    }


def test_the_records_are_the_form_this_release_writes_and_reads() -> None:
    for each in RECORDS:
        encoded = tasks.encode(each)
        assert msgspec.json.decode(encoded, type=type(each)) == each
