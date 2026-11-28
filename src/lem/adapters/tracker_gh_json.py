"""An issue and its comments as `gh` prints them, and the facts the tracker gives of them.

`gh issue view --json number,title,body,state,stateReason,labels,url,author,assignees` prints
the issue (gh 2.101.0, these among its JSON FIELDS); `gh api .../comments --paginate --slurp`
prints the REST list of the comments, one array of the pages.
"""

import msgspec

from lem.adapters.tracker_gh_facts import Comment, Issue

VIEW = "number,title,body,state,stateReason,labels,url,author,assignees"


class GhLogin(msgspec.Struct, frozen=True):
    """A person as gh names one."""

    login: str = ""


class GhLabel(msgspec.Struct, frozen=True):
    """A label as gh names one."""

    name: str = ""


class GhIssue(msgspec.Struct, frozen=True, rename="camel"):
    """An issue as `gh issue view --json VIEW` prints it."""

    number: int
    url: str
    title: str = ""
    body: str = ""
    state: str = ""
    state_reason: str | None = None
    labels: list[GhLabel] = []
    author: GhLogin | None = None
    assignees: list[GhLogin] = []


class GhComment(msgspec.Struct, frozen=True):
    """A comment as GitHub's REST list of an issue's comments gives it."""

    id: int | None = None
    body: str | None = None
    user: GhLogin | None = None
    created_at: str | None = None
    html_url: str | None = None


def issue_of(found: GhIssue) -> Issue:
    """The issue as the tracker gives it: its state and its reason in small letters."""
    return Issue(
        number=found.number,
        url=found.url,
        title=found.title,
        body=found.body,
        state=found.state.lower(),
        state_reason=(found.state_reason or "").lower() or None,
        labels=tuple(label.name for label in found.labels if label.name),
        author=found.author.login if found.author else None,
        assignees=tuple(person.login for person in found.assignees if person.login),
    )


def comment_of(found: GhComment) -> Comment:
    """One comment as the tracker gives it."""
    return Comment(
        id=found.id,
        author=found.user.login if found.user else None,
        at=found.created_at,
        text=found.body or "",
        url=found.html_url,
    )
