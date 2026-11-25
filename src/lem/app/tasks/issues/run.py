"""One step of `lem issue` on one task: the task's record, its issue, and what the step did and
wrote down so far."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.app.tasks import ticket
from lem.app.tasks.issues.results import Stepped
from lem.model.task import tickets

if TYPE_CHECKING:
    from pathlib import Path

    from lem.adapters.tracker_gh_facts import Issue
    from lem.app.tasks.issues.facts import Issues
    from lem.records.record import Record
    from lem.records.tickets import TicketAct


@dataclass(kw_only=True)
class Run:
    """The task, every record, its issue (`repo`, `number`), and the step's account."""

    state: Path
    record: Record
    every: tuple[Record, ...]
    issues: Issues
    repo: str
    number: int
    did: list[str] = field(default_factory=list)
    wrote: list[str] = field(default_factory=list)

    @property
    def acts(self) -> frozenset[str]:
        """The steps written down for the issue when the step began."""
        return frozenset(step.act for step in tickets.of(self.record.task).steps)

    @property
    def named(self) -> str:
        """The issue as a line names it: `issue #42 of acme/shop`."""
        return f"issue #{self.number} of {self.repo}"

    def write(self, act: TicketAct, login: str | None = None) -> None:
        """Write the step `act` down (`lem task ticket`), with the login of `assigned`."""
        ticket.recorded(self.state, self.record.task.slug, act, login)
        self.wrote.append(f"{act} {login}" if login else act)

    def stepped(self, step: str, issue: Issue | None) -> Stepped:
        """What the step prints: the issue as it is after the step, when it was read."""
        return Stepped(
            slug=self.record.task.slug,
            ticket=f"#{self.number}",
            repository=self.repo,
            step=step,
            url=issue.url if issue else None,
            state=issue.state if issue else None,
            assignees=issue.assignees if issue else None,
            did=tuple(self.did),
            wrote=tuple(self.wrote),
        )
