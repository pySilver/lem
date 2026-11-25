"""An issue through `gh`: who is signed in, the issue, its comments (`IssueReads`), and the four
writes Lem makes to it: an assignee added or removed, a comment, a close (`IssueWrites`)."""

from typing import TYPE_CHECKING

import msgspec

from lem.adapters.forge_gh_shell import last_words
from lem.adapters.tracker_gh_json import VIEW, GhComment, GhIssue, comment_of, issue_of
from lem.adapters.tracker_gh_shell import GH, GhRun
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.adapters.tracker_gh_facts import Comment, Issue

ISSUE = "issue"
EDIT = "edit"
REPO = "--repo"
# What gh says of a number that names no issue nor pull request of the repository.
NO_ISSUE = "could not resolve to an issue"


class IssueReads(GhRun):
    """What Lem reads of an issue, and of the person signed in to gh."""

    def who(self) -> str:
        """The login of the person signed in to gh; refused when gh cannot tell."""
        ran = self.tried("api", "user", "--jq", ".login")
        login = ran.stdout.strip()
        if ran.returncode or not login:
            raise Refusal(
                "gh-signed-out",
                f"gh cannot tell who is signed in ({last_words(ran)})",
                "sign it in with gh auth login, then run this again",
            )
        return login

    def issue(self, repo: str, number: int) -> Issue:
        """The issue `number` of `repo`; refused when gh finds none."""
        ran = self.tried(ISSUE, "view", str(number), REPO, repo, "--json", VIEW)
        if ran.returncode and NO_ISSUE in last_words(ran).lower():
            raise Refusal(
                "no-issue",
                f"#{number} of {repo} is no issue: {last_words(ran)}",
                f"give the number or the address of an issue of {repo}",
            )
        if ran.returncode:
            raise Unanswered(GH, last_words(ran))
        return issue_of(msgspec.json.decode(ran.stdout, type=GhIssue))

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]:
        """Every comment of the issue, page after page, oldest first."""
        path = f"repos/{repo}/issues/{number}/comments"
        said = self.said("api", path, "--paginate", "--slurp")
        pages = msgspec.json.decode(said, type=list[list[GhComment]])
        return tuple(comment_of(found) for page in pages for found in page)


class IssueWrites(GhRun):
    """The writes Lem makes to an issue."""

    def assign(self, repo: str, number: int, login: str) -> str | None:
        """Add `login` as an assignee: None when gh took it, else gh's words."""
        ran = self.tried(ISSUE, EDIT, str(number), REPO, repo, "--add-assignee", login)
        return last_words(ran) if ran.returncode else None

    def unassign(self, repo: str, number: int, login: str) -> None:
        """Remove `login` from the assignees."""
        self.said(ISSUE, EDIT, str(number), REPO, repo, "--remove-assignee", login)

    def comment(self, repo: str, number: int, body: str) -> str:
        """Post one comment, and give its address."""
        posted = (ISSUE, "comment", str(number), REPO, repo, "--body-file", "-")
        return self.said(*posted, stdin=body).strip()

    def close(self, repo: str, number: int) -> None:
        """Close the issue as completed."""
        self.said(ISSUE, "close", str(number), REPO, repo, "--reason", "completed")
