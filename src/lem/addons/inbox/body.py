"""A note or one question in the task's Inbox thread."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.addons.inbox import merges
from lem.addons.inbox.stops import block, breaker
from lem.records.holds import Blocked, OwnerHold

if TYPE_CHECKING:
    from lem.addons.inbox.source import RowFacts
    from lem.records.landing.record import Landing

CHOICES = MappingProxyType(
    {
        "breaker": ("Help", "Park", "Drop"),
        "merge": ("Merge", "Not now"),
        "plan": ("Build", "Drop"),
    }
)


def question(found: RowFacts, plan: str | None) -> str:
    """The prompt and choices the owner can answer in their thread."""
    choices = CHOICES.get(found.row.kind, ())
    fence = "question" if choices else "question-text"
    label, context = words(found, plan)
    lines = "\n".join(f"- [ ] {choice}" for choice in choices)
    return f":::{fence}\n{label}\n\n{context}\n\n{lines}\n:::"


def words(found: RowFacts, plan: str | None) -> tuple[str, str]:
    """The question's subject and the state it asks about."""
    kind = found.row.kind
    task = found.look.record.task
    hold = task.hold
    if kind == "merge":
        return merge(found)
    if kind == "plan":
        instruction = "Read the attached plan first." if plan else task.ask
        return f"Build the plan of {task.slug}, or drop it?", instruction
    if isinstance(hold, OwnerHold) and hold.on == "order":
        return f"Which task should {task.slug} wait for?", hold.line
    return common(found)


def common(found: RowFacts) -> tuple[str, str]:
    """The other questions use the board's owner instruction."""
    task = found.look.record.task
    row = found.row
    hold = task.hold
    if row.kind == "breaker":
        return f"{task.slug} needs help, a park, or a drop.", breaker(found)
    if row.kind == "blocked":
        fallback = row.why or task.ask
        detail = block(task.slug, hold) if isinstance(hold, Blocked) else fallback
        return f"What should the session of {task.slug} do?", detail
    if isinstance(hold, OwnerHold):
        return f"{task.slug} waits for the owner.", hold.line
    return f"{task.slug} waits for the owner.", row.prompt or row.why or task.ask


def merge(found: RowFacts) -> tuple[str, str]:
    """Name the full tip and the merge reader's reason."""
    record = found.look.record
    tip = merges.tip_of(found)
    review = merges.review_of(found)
    why = (review.why or "") if review else ""
    slug = record.task.slug
    return f"Merge {slug} at commit {tip}?", merge_context(record.landing, why)


def merge_context(landing: Landing | None, why: str) -> str:
    """The pull request and the reason the merge agent calls the owner."""
    pull = landing.pull if landing else None
    url = pull.url if pull else ""
    return f"{url}\nThe merge agent calls the owner. {why}"
