"""Where a file of a task's folder goes on the map of every task (`artifacts.place` on `main`):
its section, a title a person reads, and its role.

A file is a document, which a person reads and which is a row of its section; a record, the
machine's file that a tab of the board shows readable, which hangs as a small link on the row of
its document; or a working file, which every file the map does not know is, so that nothing is
unreachable and nothing new makes a section of its own.
"""

from types import MappingProxyType
from typing import Literal

from lem.records.base import Frozen

type Role = Literal["doc", "record", "work"]

# The sections of every task's map, in the order a task runs, and the group of the working
# files after them.
REQUEST = "request"
CRITERIA = "criteria"
PLAN = "plan"
BUILD = "build"
CHECKS = "checks"
REVIEW = "review"
PR = "pr"
SECTIONS = (
    (REQUEST, "Request"),
    (CRITERIA, "Criteria"),
    (PLAN, "Plan"),
    (BUILD, "Build"),
    (CHECKS, "Checks"),
    (REVIEW, "Review"),
    (PR, "Pull request"),
)
WORK = "work"
GROUPS = (*(key for key, _ in SECTIONS), WORK)
CRITERIA_DOC = "criteria.md"
PR_DOC = "pr.md"
ASK = "ask.txt"
TICKET = "ticket.txt"
MEDIA_FOLDER = "media/"


class Spot(Frozen, frozen=True, kw_only=True):
    """A file's place on the map: its section (`group`), its title and role; for a record the
    document it belongs to, its link's word and the tab that shows it; for a working file its
    folder."""

    group: str
    title: str
    role: Role = "doc"
    of: str | None = None
    label: str | None = None
    tab: str | None = None
    folder: str | None = None


class Hang(Frozen, frozen=True, kw_only=True):
    """Where a record hangs: its document, the word of its link, and the tab that shows it."""

    of: str
    label: str
    tab: str | None = None


# The documents of a task's folder, by their name: their section and their title.
DOCS = MappingProxyType(
    {
        ASK: Spot(group=REQUEST, title="The request"),
        TICKET: Spot(group=REQUEST, title="The ticket"),
        "task.md": Spot(group=REQUEST, title="The task"),
        "brief.md": Spot(group=REQUEST, title="The brief"),
        "talk.md": Spot(group=REQUEST, title="The talk that led to the request"),
        "interview-notes.md": Spot(group=REQUEST, title="Interview notes"),
        "session.md": Spot(group=REQUEST, title="The task session's first read"),
        "outside.md": Spot(group=REQUEST, title="Outside the change"),
        CRITERIA_DOC: Spot(group=CRITERIA, title="Acceptance criteria"),
        "criteria-read.md": Spot(
            group=CRITERIA, title="The personas' read of the criteria"
        ),
        "criteria-page.html": Spot(group=CRITERIA, title="The criteria page"),
        "criteria-change.md": Spot(
            group=CRITERIA,
            title="The changed criteria, as the session wrote them for the change",
        ),
        "design.md": Spot(group=PLAN, title="Design"),
        "directions.md": Spot(group=PLAN, title="The owner's directions"),
        "scout.md": Spot(group=PLAN, title="The scout's report"),
        "investigation.md": Spot(group=PLAN, title="Investigation"),
        "handoff.md": Spot(group=PLAN, title="Handoff"),
        "talk-list.md": Spot(group=PLAN, title="The plan talk's list"),
        "report.md": Spot(group=BUILD, title="Report"),
        "breaker.md": Spot(group=BUILD, title="What stopped the build"),
        "setup.log": Spot(group=CHECKS, title="Worktree setup output"),
        PR_DOC: Spot(group=PR, title="Pull request text"),
        "notes.md": Spot(group=PR, title="Notes for the pull request"),
        "merge-review.md": Spot(group=PR, title="The merge review"),
        "handover.html": Spot(group=PR, title="The hand-over page"),
    }
)
# The records, by their name: the document they belong to, the word of their link, and the
# tab of the board that shows them readable.
RECORDS = MappingProxyType(
    {
        "criteria.json": Hang(of=CRITERIA_DOC, label="record", tab=CRITERIA),
        "criteria-before.json": Hang(
            of=CRITERIA_DOC, label="text before the change", tab=CRITERIA
        ),
        "decisions.jsonl": Hang(of=PR_DOC, label="decisions", tab=CRITERIA),
        "polish.json": Hang(of="report.md", label="polish pass", tab=CHECKS),
        "landing.json": Hang(of=PR_DOC, label="landing", tab=CHECKS),
        "read.json": Hang(of=PR_DOC, label="review's read", tab=CHECKS),
        "state.md": Hang(of=ASK, label="state", tab="timeline"),
        "ticket-steps.txt": Hang(of=TICKET, label="ticket steps", tab=None),
        "ticket-repo.txt": Hang(of=TICKET, label="ticket repository", tab=None),
        "resumed-from.txt": Hang(of=ASK, label="resumed from", tab=None),
        "release.txt": Hang(of=ASK, label="release", tab=None),
    }
)


def known(path: str) -> Spot | None:
    """The place of a document or a record the map knows by its name, or None."""
    return DOCS.get(path) or recorded(path)


def recorded(path: str) -> Spot | None:
    """The place of a record the map knows by its name: on the row of its document."""
    hang = RECORDS.get(path)
    if hang is None:
        return None
    doc = DOCS[hang.of]
    return Spot(
        group=doc.group,
        title=f"{doc.title} ({hang.label})",
        role="record",
        of=hang.of,
        label=hang.label,
        tab=hang.tab,
    )
