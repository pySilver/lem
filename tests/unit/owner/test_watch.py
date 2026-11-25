"""`lem owner watch`: it ends on his next word, at once when the count it was given is no longer
the mark's, writes nothing, and ends a stop with a refusal (`main`: `tests/lem-state.sh` "the
watch of the owner's mark in one repository ends after his away in another")."""

import os
import signal
from datetime import UTC, datetime

import pytest

from fakes.command import lem
from lem.app.owner import watch
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.store import owner
from unit.task.spaces import refusal, result

AWAY_AT = datetime(2026, 11, 19, 14, 5, tzinfo=UTC)


def test_a_count_that_is_no_longer_the_marks_ends_it_at_once() -> None:
    home = paths.home(os.environ)
    owner.change(home, "away", AWAY_AT, away=True)
    owner.change(home, "back", AWAY_AT, away=False)

    def never(_: float) -> None:
        raise AssertionError("the watch waited")

    seen = watch.watched(1, 5, never)
    assert (seen.away, seen.words, seen.seen) == (False, "back", 2)


def test_his_word_ends_it_with_that_word_and_it_writes_nothing() -> None:
    home = paths.home(os.environ)
    looks: list[float] = []

    def word(every: float) -> None:
        looks.append(every)
        owner.change(home, "I'm away", AWAY_AT, away=True)

    seen = watch.watched(0, 3, word)
    assert (seen.away, seen.since, seen.words, seen.seen) == (
        True,
        AWAY_AT,
        "I'm away",
        1,
    )
    assert looks == [3]
    assert owner.read(home).seen == 1


def test_a_stop_ends_it_with_a_refusal_that_asks_for_no_second_watch() -> None:
    before = signal.getsignal(signal.SIGTERM)

    def stopped(_: float) -> None:
        os.kill(os.getpid(), signal.SIGTERM)

    with pytest.raises(Refusal) as caught:
        watch.watched(0, 1, stopped)
    assert caught.value.code == "stopped"
    assert "start no other watch" in caught.value.fix
    assert signal.getsignal(signal.SIGTERM) == before


def test_it_is_refused_without_a_count_and_with_a_count_below_0() -> None:
    assert refusal(lem("owner", "watch"))["code"] == "seen"
    assert refusal(lem("owner", "watch", "--seen", "-1"))["code"] == "seen"
    assert (
        refusal(lem("owner", "watch", "--seen", "0", "--every", "0"))["code"] == "every"
    )


def test_the_command_ends_at_once_on_a_count_it_does_not_hold() -> None:
    owner.change(paths.home(os.environ), "away", AWAY_AT, away=True)
    assert result(lem("owner", "watch", "--seen", "0")) == {
        "away": True,
        "since": "2026-11-19T14:05:00Z",
        "words": "away",
        "seen": 1,
    }
