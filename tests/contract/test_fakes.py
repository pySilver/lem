"""The fakes of the terminal and the ports to the outside against their contracts."""

from typing import TYPE_CHECKING

from contract.suites.outside import (
    HarnessContract,
    JudgeContract,
    NotifierContract,
    Reached,
    TrackerContract,
)
from contract.suites.terminal import TerminalContract
from fakes.harness import FakeHarness
from fakes.outside import FakeJudge, FakeTracker, RecordingNotifier
from fakes.terminal import FakeTerminal
from lem.ports.terminal import Unreadable
from lem.ports.tracker import TicketView

if TYPE_CHECKING:
    from pathlib import Path


class TestFakeTerminal(TerminalContract):
    def terminal(self, folder: Path) -> FakeTerminal:
        return FakeTerminal()


class TestFakeHarness(HarnessContract):
    def harness(self) -> FakeHarness:
        return FakeHarness()


class TestFakeTracker(TrackerContract):
    def tracker(self) -> tuple[FakeTracker, str]:
        ticket = TicketView(
            id="MBZ-12", title="Fix the login", body="", state="open", url="u"
        )
        return FakeTracker(tickets={"MBZ-12": ticket}), "MBZ-12"


class TestRecordingNotifier(NotifierContract):
    def notifier(self) -> tuple[RecordingNotifier, Reached]:
        notifier = RecordingNotifier()

        def reached() -> tuple[tuple[str, ...], tuple[str, ...]]:
            started = tuple(wait.id for wait in notifier.started_waits)
            return started, tuple(notifier.ended_waits)

        return notifier, reached


class TestFakeJudge(JudgeContract):
    def judge(self) -> FakeJudge:
        return FakeJudge(over={"The login drops the session": 0.8})


class TestFakeJudgeWithNoKey(JudgeContract):
    def judge(self) -> FakeJudge:
        return FakeJudge(key=False)


def test_an_unreadable_terminal_is_told_from_an_empty_one() -> None:
    assert FakeTerminal().sessions() == ()
    assert FakeTerminal(unreadable="agterm did not answer").sessions() == Unreadable(
        why="agterm did not answer"
    )
