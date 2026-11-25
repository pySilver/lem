"""`lem issue read ISSUE`: one issue of origin's repository, by its number (`42`, `#42`) or its
address, with its comments apart from its text. It writes nothing.

The address of another repository's issue is refused before gh is asked, and so is the number of
a pull request (gh's issue view answers for one) and an issue that moved to another repository:
Lem reads the issues of origin.
"""

import re
from typing import TYPE_CHECKING

from lem.app.tasks.issues import facts, status
from lem.app.tasks.issues.results import IssueRead
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.adapters.tracker_gh_facts import Issue
    from lem.app.wiring import Ports
    from lem.store.places import Workspace

# An issue's address, with what GitHub may put after it (a comment's anchor, a query).
ADDRESS = re.compile(
    r"https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/issues/(?P<number>[0-9]+)(?:[/?#]\S*)?"
)
NUMBER = re.compile(r"#?([0-9]+)")
ELSEWHERE = "start the task from the owner's own words, with the address in them"


def number_of(given: str, origin: str) -> int:
    """The number of an issue of origin from `42`, `#42` or its address."""
    given = given.strip()
    address = ADDRESS.fullmatch(given)
    if address and not status.same(address["repo"], origin):
        raise Refusal(
            "issue-elsewhere",
            f"the address names an issue of {address['repo']}, and Lem reads the issues "
            f"of origin, which is {origin}",
            f"give the number or the address of an issue of {origin}, or {ELSEWHERE}",
        )
    number = None if address else NUMBER.fullmatch(given)
    found = address["number"] if address else number and number[1]
    if not found:
        raise Refusal(
            "issue-word",
            f"{given!r} is no issue's number or address",
            f"give 42, #42 or https://github.com/{origin}/issues/42",
        )
    if not int(found):
        raise Refusal(
            "issue-word", "issue 0 is no issue", "GitHub numbers its issues from 1"
        )
    return int(found)


def repository_of(issue: Issue, origin: str) -> str:
    """The repository of the issue's own address: refused for a pull request, and for an
    issue that moved to another repository."""
    address = ADDRESS.fullmatch(issue.url)
    named = f"#{issue.number} of {origin}"
    if address is None:
        kind = "a pull request" if "/pull/" in issue.url else "no issue"
        raise Refusal(
            "not-an-issue",
            f"{named} is {kind} ({issue.url}), not an issue",
            "give the number of an issue",
        )
    if not status.same(address["repo"], origin):
        raise Refusal(
            "issue-elsewhere",
            f"issue {named} is now {issue.url}, an issue of another repository, and Lem "
            f"reads the issues of origin, which is {origin}",
            ELSEWHERE,
        )
    return address["repo"]


def read(ports: Ports, where: Workspace, given: str) -> IssueRead:
    """The issue `given`, its comments apart, and what `lem task open` takes for it."""
    status.github(where.checkout)
    issues = facts.of(ports)
    origin = issues.origin()
    issue = issues.issue(origin, number_of(given, origin))
    repo = repository_of(issue, origin)
    asked = bool(issue.body.strip())
    return IssueRead(
        id=f"#{issue.number}",
        number=issue.number,
        repository=repo,
        url=issue.url,
        title=issue.title,
        text=issue.body,
        state=issue.state,
        state_reason=issue.state_reason,
        labels=issue.labels,
        author=issue.author,
        assignees=issue.assignees,
        comments=issues.comments(repo, issue.number),
        ask=issue.body if asked else issue.title,
        ask_is="text" if asked else "title",
        task_open=("--ticket", f"#{issue.number}", "--ticket-repo", repo),
    )
