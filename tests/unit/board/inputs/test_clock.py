"""The words the board makes of a record's facts: a length, a time since, a clock time with its
date on another day, a task's title and address, and a pull request's link."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import pytest

from lem.board.inputs import clock, names
from lem.board.inputs.parts import When
from lem.records.landing.record import Pull

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.board.inputs.text import View

NOW = datetime(2026, 11, 25, 16, 0, tzinfo=UTC)
ZONE = ZoneInfo("UTC")


@pytest.mark.parametrize(
    ("seconds", "shown"),
    [
        (0, "0s"),
        (-3, "0s"),
        (45, "45s"),
        (44.6, "45s"),
        (187, "3m 07s"),
        (599, "9m 59s"),
        (600, "10m"),
        (25 * 60 + 40, "25m"),
        (2 * 3600 + 5 * 60, "2h 05m"),
        (47 * 3600 + 59 * 60, "47h 59m"),
        (48 * 3600, "2d 0h"),
        (3 * 86400 + 4 * 3600 + 59 * 60, "3d 4h"),
    ],
)
def test_a_length_keeps_its_seconds_under_ten_minutes_and_its_minutes_under_two_days(
    seconds: float, shown: str
) -> None:
    assert clock.length(seconds) == shown


def test_the_length_formatter_has_no_separate_hours_formatter() -> None:
    assert not hasattr(clock, "hours_of")


@pytest.mark.parametrize(
    ("seconds", "shown"),
    [(0, "just now"), (4.9, "just now"), (5, "5s ago"), (1920, "32m ago")],
)
def test_a_time_since_is_just_now_under_five_seconds(
    seconds: float, shown: str
) -> None:
    assert clock.ago(seconds) == shown


def test_a_clock_time_has_its_date_only_on_another_day_of_the_zone_shown() -> None:
    assert clock.stamp(NOW - timedelta(minutes=20), NOW, ZONE) == "15:40"
    assert (
        clock.stamp(NOW - timedelta(hours=16, minutes=10), NOW, ZONE) == "Nov 24 23:50"
    )
    # in Tokyo the page's minute is 01:00 of the next day, so the same morning is a day back
    morning = NOW - timedelta(hours=7, minutes=30)
    assert clock.stamp(morning, NOW, ZONE) == "08:30"
    assert clock.stamp(morning, NOW, ZoneInfo("Asia/Tokyo")) == "Nov 25 17:30"


def test_a_moment_as_the_page_prints_it_keeps_the_moment_and_says_how_it_moves() -> (
    None
):
    began = NOW - timedelta(minutes=448)
    assert clock.since(began, NOW, "in this state since 08:32") == When(
        at=began, shown="7h 28m", title="in this state since 08:32", ticks="since"
    )
    assert clock.gone(began, NOW) == When(at=began, shown="7h 28m ago", ticks="ago")
    assert clock.fixed(began, NOW, ZONE, "ended") == When(
        at=began, shown="08:32", title="ended"
    )


def test_the_repeated_hour_counts_as_an_hour_of_elapsed_time() -> None:
    zone = ZoneInfo("America/New_York")
    first = datetime(2026, 11, 1, 1, 15, tzinfo=zone)
    second = first.replace(fold=1)
    assert clock.since(first, second).shown == "1h 00m"
    assert clock.gone(first, second).shown == "1h 00m ago"


@pytest.mark.parametrize("formatter", [clock.since, clock.gone])
@pytest.mark.parametrize("naive", ["began", "now"])
def test_elapsed_time_requires_a_zone_for_both_moments(
    formatter: Callable[[datetime, datetime], When], naive: str
) -> None:
    began, now = NOW - timedelta(hours=1), NOW
    if naive == "began":
        began = began.replace(tzinfo=None)
    else:
        now = now.replace(tzinfo=None)
    with pytest.raises(ValueError, match="time zone"):
        formatter(began, now)


def test_a_title_is_the_slug_in_words_and_an_empty_slug_is_a_task() -> None:
    assert names.title_of("report-dates-stay-whole") == "Report dates stay whole"
    assert names.title_of("") == "A task"


def test_a_task_address_names_its_tab_and_the_view_under_its_panel_but_the_kanban() -> (
    None
):
    base = "/studio/shop"
    assert names.task_href(base, "fix-it") == "/studio/shop/tasks/fix-it"
    assert (
        names.task_href(base, "fix-it", "criteria", "waits")
        == "/studio/shop/tasks/fix-it/criteria?in=waits"
    )
    assert names.task_href(base, "fix-it", None, "tasks") == "/studio/shop/tasks/fix-it"


@pytest.mark.parametrize(
    ("under", "suffix"),
    [
        ("new", ""),
        ("tasks", ""),
        ("waits", "?in=waits"),
        ("backlog", "?in=backlog"),
        ("activity", "?in=activity"),
        ("done", "?in=done"),
    ],
)
def test_overview_omits_its_tab_and_keeps_only_a_view_it_can_open_over(
    under: View, suffix: str
) -> None:
    address = "/studio/shop/tasks/fix-it"
    assert (
        names.task_href("/studio/shop", "fix-it", "overview", under) == address + suffix
    )
    assert (
        names.task_href("/studio/shop", "fix-it", "criteria", under)
        == f"{address}/criteria{suffix}"
    )


def test_an_artifact_address_quotes_its_path_and_keeps_the_slash_before_the_view() -> (
    None
):
    assert (
        names.task_href(
            "/studio/shop", "fix-it", "artifacts", "waits", artifact="gate/check #1.log"
        )
        == "/studio/shop/tasks/fix-it/artifacts/gate/check%20%231.log/?in=waits"
    )
    assert (
        names.task_href("/studio/shop", "fix-it", artifact="report.md")
        == "/studio/shop/tasks/fix-it/artifacts/report.md/"
    )


def test_a_pull_request_links_to_the_forge_by_its_number_or_its_repository_and_number() -> (
    None
):
    pull = Pull(number=44, url="https://github.com/acme/shop/pull/44", title="feat: x")
    short = names.pull_link(pull)
    assert (short.label, short.href, short.out) == ("#44", pull.url, True)
    assert short.title == f"Open the pull request on the forge: {pull.url}"
    assert names.pull_link(pull, whole=True).label == "acme/shop#44"
    chip = names.pull_chip(pull)
    assert (chip.label, chip.icon, chip.look, chip.link) == (
        "#44",
        "code-pull-request",
        "gate",
        short,
    )
    odd = Pull(number=7, url="https://example.com/merge/7", title="x")
    assert names.repository(odd) is None
    assert names.pull_link(odd, whole=True).label == "#7"


def test_a_count_says_its_word_once_or_in_its_plural() -> None:
    assert (names.plural(1, "task"), names.plural(2, "task")) == ("1 task", "2 tasks")
