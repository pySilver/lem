"""An in-memory stand-in for the issues of origin on GitHub: the parts
`lem.app.tasks.issues.facts.Issues` names, every call that asked GitHub, and a comment's id that
names its issue (`number * COMMENTS + its place`). The adapter itself is held by
`tests/contract/test_tracker.py`, against a stand-in for gh."""

from dataclasses import dataclass, field

from msgspec.structs import replace

from lem.adapters.tracker_gh_facts import Checked, Comment, Issue
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.ports.tracker import Receipt, TicketView, TrackerStep

REPO = "acme/shop"
# How many comment ids each issue has: the id of a comment names its issue.
COMMENTS = 1000


@dataclass
class FakeIssues:
    """Origin's issues in memory, the person signed in, and every call that asked GitHub."""

    repo: str = REPO
    login: str | None = "octo-cat"
    issues: dict[int, Issue] = field(default_factory=dict)
    threads: dict[int, list[Comment]] = field(default_factory=dict)
    refuse_add: str | None = None
    cut_after_edit: bool = False
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def origin(self) -> str:
        return self.repo

    def who(self) -> str:
        self.calls.append(("who",))
        if self.login is None:
            raise Refusal(
                "gh-signed-out", "gh cannot tell who is signed in", "gh auth login"
            )
        return self.login

    def issue(self, repo: str, number: int) -> Issue:
        self.calls.append(("view", repo, str(number)))
        return self.issues[number]

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]:
        self.calls.append(("comments", repo, str(number)))
        return tuple(self.threads.get(number, ()))

    def assign(self, repo: str, number: int, login: str) -> str | None:
        self.calls.append(("assign", repo, str(number), login))
        if self.refuse_add:
            return self.refuse_add
        found = self.issues[number]
        self.issues[number] = replace(found, assignees=(*found.assignees, login))
        return None

    def unassign(self, repo: str, number: int, login: str) -> None:
        self.calls.append(("unassign", repo, str(number), login))
        found = self.issues[number]
        kept = tuple(name for name in found.assignees if name != login)
        self.issues[number] = replace(found, assignees=kept)

    def comment(self, repo: str, number: int, body: str) -> str:
        self.calls.append(("comment", repo, str(number)))
        thread = self.threads.setdefault(number, [])
        made = number * COMMENTS + len(thread) + 1
        thread.append(Comment(id=made, author=self.login, text=body))
        return f"https://github.com/{repo}/issues/{number}#issuecomment-{made}"

    def edit_comment(self, repo: str, comment: int, body: str) -> None:
        self.calls.append(("edit_comment", repo, str(comment)))
        thread = self.threads[comment // COMMENTS]
        place = next(at for at, one in enumerate(thread) if one.id == comment)
        thread[place] = replace(thread[place], text=body)
        if self.cut_after_edit:
            raise Unanswered("gh", "the session was cut off after the edit")

    def close(self, repo: str, number: int) -> None:
        self.calls.append(("close", repo, str(number)))
        found = self.issues[number]
        self.issues[number] = replace(found, state="closed", state_reason="completed")

    def check(self) -> Checked:
        return Checked(repository=self.repo, signed_in=True, issues_on=True)

    def read(self, ticket: str) -> TicketView:
        found = self.issues[int(ticket.removeprefix("#"))]
        return TicketView(
            id=ticket,
            title=found.title,
            body=found.body,
            state=found.state,
            url=found.url,
            assignees=found.assignees,
        )

    def step(self, ticket: str, step: TrackerStep, text: str) -> Receipt:
        return Receipt(ticket=ticket, step=step, wrote=text)

    def writes(self) -> list[tuple[str, ...]]:
        """The calls that changed an issue."""
        changing = {"assign", "unassign", "comment", "edit_comment", "close"}
        return [call for call in self.calls if call[0] in changing]
