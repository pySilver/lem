"""The `Tracker` port's first adapter: GitHub Issues through `gh`, in the main checkout, on the
issues of origin's repository (the design's part 4).

The port's `read` and `step` are here. `lem issue` takes a step in its parts (who is signed in,
the assignees, the comments with Lem's last line, an add written down before it is made), so the
adapter gives those parts too (`IssueReads`, `IssueWrites`, `TrackerChecks`), which
`lem.app.tasks.issues.facts.Issues` names.
"""

import re
from typing import TYPE_CHECKING

from lem.adapters.tracker_gh_check import TrackerChecks
from lem.adapters.tracker_gh_issues import IssueReads, IssueWrites
from lem.kernel.errors import Refusal
from lem.ports.tracker import Receipt, TicketView

if TYPE_CHECKING:
    from lem.ports.place import Place
    from lem.ports.tracker import TrackerStep

NUMBER = re.compile(r"#?([0-9]+)")


class TrackerGh(TrackerChecks, IssueReads, IssueWrites):
    """The whole port, and the parts `lem issue` takes a step in."""

    def number(self, ticket: str) -> int:
        """The issue's number of `ticket` (`42`, `#42`); refused for any other id."""
        found = NUMBER.fullmatch(ticket)
        if found is None or not int(found[1]):
            raise Refusal(
                "no-ticket",
                f"no ticket {ticket} in the issues of GitHub: an issue is its number",
                "give the issue's number, as 42 or #42",
            )
        return int(found[1])

    def read(self, ticket: str) -> TicketView:
        number = self.number(ticket)
        found = self.issue(self.origin(), number)
        return TicketView(
            id=f"#{number}",
            title=found.title,
            body=found.body,
            state=found.state,
            url=found.url,
            assignees=found.assignees,
        )

    def step(self, ticket: str, step: TrackerStep, text: str) -> Receipt:
        """The step in one go, with nothing written down: the person signed in for an issue
        with no assignee at the start; the comment at the end, and the close for a landing."""
        repo, number = self.origin(), self.number(ticket)
        if step == "start":
            did = self.started(repo, number)
        else:
            did = self.ended(repo, number, text, close=step == "land")
        wrote = None if step == "start" else text
        return Receipt(
            ticket=f"#{number}",
            step=step,
            did=did,
            wrote=wrote,
            url=f"https://github.com/{repo}/issues/{number}",
        )

    def started(self, repo: str, number: int) -> tuple[str, ...]:
        """The person signed in as the assignee of an issue that has none."""
        if self.issue(repo, number).assignees:
            return ()
        login = self.who()
        if self.assign(repo, number, login) is not None:
            return ()
        return (f"added the assignee {login}",)

    def ended(
        self, repo: str, number: int, text: str, *, close: bool
    ) -> tuple[str, ...]:
        """The end's comment, and for a landing the close of an issue still open."""
        self.comment(repo, number, text)
        if not close or self.issue(repo, number).state == "closed":
            return ("posted the comment",)
        self.close(repo, number)
        return ("posted the comment", "closed the issue as completed")


def bind(place: Place) -> TrackerGh:
    """The adapter for `place`: gh in its main checkout, with the command's environment."""
    return TrackerGh(checkout=place.checkout, environ=place.environ)
