"""A workspace whose tracker is GitHub's, over an in-memory stand-in for the issues of origin
(`FakeIssues`, the parts `lem.app.tasks.issues.facts.Issues` names), and the tasks a test puts
there. The adapter itself is held by `tests/contract/test_tracker.py`, against a stand-in for gh."""

import dataclasses
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.records import MOMENT
from fakes.records import noted as note
from lem.adapters.tracker_gh_facts import Checked, Comment, Issue
from lem.kernel.errors import Refusal
from lem.ports.tracker import Receipt, TicketView
from lem.records.tickets import Ticket, TicketStep
from lem.store import tasks
from unit.task.spaces import SETTINGS, made, read, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.wiring import Ports
    from lem.ports.tracker import TrackerStep
    from lem.records.record import Record
    from lem.store.places import Workspace

GITHUB = f'{SETTINGS}[tracker]\nkind = "github"\n'
REPO = "acme/shop"
SLUG = "export-keeps-gift-note"
OUTCOME = (
    "# The gift note\n\n## Outcome\n\n**The export keeps the gift note of each order, "
    "as the shop shows it.**\n\nToday:\n\n1. The export drops it.\n"
)


def gift_note(**fields: object) -> Issue:
    """Issue 42 of acme/shop, open, with one comment's worth of fields over it."""
    issue = Issue(
        number=42,
        url=f"https://github.com/{REPO}/issues/42",
        title="The export drops the gift note",
        body="Each export drops the gift note.\n\nSee order 7.",
        state="open",
        labels=("bug",),
        author="ann",
    )
    return replace(issue, **fields)


@dataclass
class FakeIssues:
    """Origin's issues in memory, the person signed in, and every call that asked GitHub."""

    repo: str = REPO
    login: str | None = "octo-cat"
    issues: dict[int, Issue] = field(default_factory=dict)
    threads: dict[int, list[Comment]] = field(default_factory=dict)
    refuse_add: str | None = None
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
        self.threads.setdefault(number, []).append(
            Comment(author=self.login, text=body)
        )
        return f"https://github.com/{repo}/issues/{number}#issuecomment-1"

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
        changing = {"assign", "unassign", "comment", "close"}
        return [call for call in self.calls if call[0] in changing]


@dataclass
class World:
    """A workspace, its ports with the fake issues, and the issues."""

    where: Workspace
    ports: Ports
    fake: FakeIssues

    def task(
        self,
        status: str,
        slug: str = SLUG,
        *,
        steps: tuple[str, ...] = (),
        ticket: str = "#42",
        line: str = "task 1 of 2",
        **fields: object,
    ) -> Record:
        """A task of issue `ticket` in `status`, with the steps written down, a state with
        `line`, and its task.md."""
        written = tuple(step_of(step) for step in steps)
        made_ticket = Ticket(tracker="github", id=ticket, repo=REPO, steps=written)
        made(
            self.where,
            slug,
            status=status,
            ask="Each export drops the gift note.",
            ticket=made_ticket,
            **fields,
        )
        folder = self.where.state / "tasks" / slug
        (folder / "task.md").write_text(OUTCOME, encoding="utf-8")
        return noted(self.where, slug, line)

    def steps(self, slug: str = SLUG) -> list[str]:
        """The steps written down for the task's issue, with the login of `assigned`."""
        ticket = read(self.where, slug).task.ticket
        found = ticket.steps if ticket else ()
        return [
            f"{step.act} {step.login}" if step.login else step.act for step in found
        ]

    def issue(self, number: int = 42) -> Issue:
        return self.fake.issues[number]

    def thread(self, number: int = 42) -> list[str]:
        return [comment.text for comment in self.fake.threads.get(number, [])]


def step_of(written: str) -> TicketStep:
    """A step as a test names it: `assigned octo-cat`, `started`."""
    act, _, login = written.partition(" ")
    return msgspec.convert(
        {"act": act, "at": MOMENT, "login": login or None},
        TicketStep,
    )


def noted(where: Workspace, slug: str, line: str) -> Record:
    """The task with one state entry of `line` in its journal."""
    record = read(where, slug)
    return tasks.update(where.state, slug, note(line), record.revision)


def world(tmp_path: Path, settings: str = GITHUB) -> World:
    """A workspace whose tracker is GitHub's, with issue 42 of acme/shop."""
    where = workspace(tmp_path / "shop", settings)
    fake = FakeIssues(issues={42: gift_note()})
    fake.threads[42] = [Comment(author="bob", text="Same here, on order 9.")]
    git = ModelGit(checkout=where.checkout)
    ports = dataclasses.replace(fake_ports(git, LocalForge(remote=git)), tracker=fake)
    return World(where=where, ports=ports, fake=fake)
