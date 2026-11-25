"""The parts of a step on an issue that `lem issue` takes one by one, which the `Tracker` port's
`read` and `step` do not give: who is signed in, the issue's assignees and comments, each write,
and the check. The GitHub adapter gives them (`lem.adapters.tracker_github`); they go into the
port when `core` takes them (`notes/task.md`, "issues").
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from lem.adapters.tracker_gh_facts import Checked, Comment, Issue
    from lem.app.wiring import Ports


class IssueReading(Protocol):
    """What a step reads: origin's repository, the person signed in, an issue, its comments,
    and the tracker's check."""

    def origin(self) -> str: ...
    def who(self) -> str: ...
    def issue(self, repo: str, number: int) -> Issue: ...
    def comments(self, repo: str, number: int) -> tuple[Comment, ...]: ...
    def check(self) -> Checked: ...


class IssueWriting(Protocol):
    """What a step writes: an assignee added (gh's words when it refused) or removed, one
    comment, a close."""

    def assign(self, repo: str, number: int, login: str) -> str | None: ...
    def unassign(self, repo: str, number: int, login: str) -> None: ...
    def comment(self, repo: str, number: int, body: str) -> str: ...
    def close(self, repo: str, number: int) -> None: ...


@runtime_checkable
class Issues(IssueReading, IssueWriting, Protocol):
    """Both."""


def of(ports: Ports) -> Issues:
    """The tracker of `ports` as the issues of GitHub; a fault when its adapter gives no such
    parts."""
    tracker = ports.tracker
    if isinstance(tracker, Issues):
        return tracker
    raise Fault(
        f"the tracker's adapter {type(tracker).__name__} gives no parts of a step on an "
        "issue of GitHub (lem.app.tasks.issues.facts.Issues)"
    )
