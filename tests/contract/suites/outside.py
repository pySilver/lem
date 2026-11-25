"""The contracts of the ports to the outside: `Harness`, `Tracker`, `Notifier` and `Judge`.
The fakes pass them now; each adapter's step runs them against its adapter (with a stand-in
for the tool behind it)."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from lem.ports.harness import Signs, Tokens, Transcript
from lem.ports.judge import Candidate, Defect, NotAsked, Score
from lem.ports.notifier import Wait

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.ports.harness import Harness
    from lem.ports.judge import Judge
    from lem.ports.notifier import Notifier
    from lem.ports.tracker import Tracker

# What reached the owner: the ids of the waits told, and of the waits ended.
type Reached = Callable[[], tuple[tuple[str, ...], tuple[str, ...]]]

WAIT = Wait(
    id="merge:fix-the-login",
    kind="merge",
    task="fix-the-login",
    workspace="project",
    say="Merge the pull request",
    url="/host/project/tasks/fix-the-login",
    since=datetime(2026, 11, 25, 10, 0, tzinfo=UTC),
)


class HarnessContract:
    """What every `Harness` gives for a task with no session."""

    def harness(self) -> Harness:
        raise NotImplementedError

    def test_a_task_with_no_session_has_no_transcript_and_no_tokens(self) -> None:
        harness = self.harness()
        assert harness.transcripts("no-such-task") == ()
        assert harness.tokens(()) == Tokens()
        gone = Transcript(path="/nowhere/gone.jsonl", claude="gone")
        assert harness.signs(gone) == Signs(read=False)


class TrackerContract:
    """What every `Tracker` does with a ticket it has, and one it does not."""

    def tracker(self) -> tuple[Tracker, str]:
        """A tracker, and the id of a ticket it has."""
        raise NotImplementedError

    def test_a_ticket_reads_by_its_id_and_a_step_gives_its_receipt(self) -> None:
        tracker, ticket = self.tracker()
        assert tracker.read(ticket).id == ticket
        receipt = tracker.step(ticket, "start", "Lem started a task on this ticket.")
        assert (receipt.ticket, receipt.step) == (ticket, "start")

    def test_a_ticket_that_is_not_there_is_a_fault(self) -> None:
        tracker, _ticket = self.tracker()
        with pytest.raises(Exception, match="no ticket"):
            tracker.read("NOPE-1")


class NotifierContract:
    """What every `Notifier` tells the owner: each wait once, and its end."""

    def notifier(self) -> tuple[Notifier, Reached]:
        """A notifier, and a function that gives what reached the owner: the ids started and
        the ids ended."""
        raise NotImplementedError

    def test_a_wait_is_told_once_and_its_end_once(self) -> None:
        notifier, reached = self.notifier()
        notifier.started(WAIT)
        notifier.started(WAIT)
        notifier.ended(WAIT.id)
        notifier.ended(WAIT.id)
        notifier.ended("never:started")
        assert reached() == ((WAIT.id,), (WAIT.id,))


class JudgeContract:
    """What every `Judge` answers: a score between 0 and 1, or why it was not asked."""

    def judge(self) -> Judge:
        raise NotImplementedError

    def test_a_score_is_a_likelihood_or_jev_was_not_asked(self) -> None:
        judge = self.judge()
        defect = Defect(
            where="src/login.py", title="The login drops the session", what="x"
        )
        over = judge.over_bar(defect)
        assert isinstance(over, NotAsked) or 0 <= over.score <= 1
        held = Candidate(path="docs/backlog/a.md", title="The login drops the session")
        same = judge.same_items(defect, (held,))
        if not isinstance(same, NotAsked):
            assert all(
                isinstance(score, Score) and score.path == "docs/backlog/a.md"
                for score in same
            )
