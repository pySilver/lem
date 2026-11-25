"""What the GitHub tracker reads of an issue beyond the `Tracker` port's `TicketView`: the issue
with its state's reason, labels and author, its comments, and the tracker's check.

These are the facts the steps of `lem issue` need (who is signed in, the assignees, the comments
with Lem's last line); they go into `lem.ports` when the port takes the methods that give them
(`notes/task.md`, "issues").
"""

from lem.records.base import Frozen


class Comment(Frozen, frozen=True, kw_only=True):
    """One comment of an issue: its author's login, when, its text, and its address."""

    author: str | None = None
    at: str | None = None
    text: str
    url: str | None = None


class Issue(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """An issue as GitHub gives it: `state` is `open` or `closed`, and `url` is its own address,
    which names another repository for an issue that moved, and `/pull/` for a pull request."""

    number: int
    url: str
    title: str
    body: str
    state: str
    state_reason: str | None = None
    labels: tuple[str, ...] = ()
    author: str | None = None
    assignees: tuple[str, ...] = ()


class Missing(Frozen, frozen=True, kw_only=True):
    """A thing the tracker lacks, and its fix."""

    what: str
    fix: str


class Checked(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The tracker's check: origin's repository, where `gh` is, whether it is signed in, whether
    the issues are on and the repository holds one, and each missing thing."""

    repository: str | None = None
    gh: str | None = None
    signed_in: bool | None = None
    issues_on: bool | None = None
    has_issues: bool | None = None
    missing: tuple[Missing, ...] = ()
