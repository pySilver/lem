"""What `lem land read SLUG` gives the review agent: the review that is due, its floor and why,
the facts of the change, the reviews before it, and its inputs, with nothing of the builder's
reasoning (`land.cmd_read` on `main`, its output with no record). The brief is published as
`reviews/read-N-DIGEST.json` in the task's folder, N being the attempt, and the agent reads it as
`prompts/review.md` says.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import review_edited, review_facts
from lem.kernel import files
from lem.model.landing import review_due
from lem.records.base import Frozen
from lem.records.landing.checks import Lowered
from lem.records.landing.record import Landing
from lem.records.landing.review import Reviewed
from lem.records.landing.start import Resolution

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context


# How many changed lines one reader takes as one piece; a larger change is read task by task,
# in the plan's own cuts. A guess (2026-11-15), not a measurement (`READ_AT` on `main`).
READ_AT = 800
RANGE_DIFF = "git range-diff {0}..{1} {2}..{3}"
# The characters of the digest that names a published brief.
SHORT = 12
# The folder of the project's review tool, where it keeps each profile and lens.
REVIEW_TOOL = ".revmux"
# Where the review agent writes its record, in the task's folder, by the attempt.
RECORD = "reviews/review-{0}.json"


class Inputs(Frozen, frozen=True, kw_only=True):
    """What a reviewer gets: the owner's words and the request, the plan or the criterion's
    file, the range and the worktree, the lowered bar, the topics, the items the branch adds,
    the base's items, and the review tool's folder."""

    ask: str
    words: str | None = None
    request: str | None = None
    plan: str | None = None
    range: str
    rules: str
    worktree: str
    lowered: tuple[Lowered, ...] = msgspec.field(default=(), name="bar")
    topics: tuple[str, ...] = ()
    filed: tuple[review_facts.Seen, ...] = ()
    backlog: tuple[review_facts.Seen, ...] = ()
    edited: tuple[review_edited.Edited, ...] = ()
    review: str = REVIEW_TOOL


class Brief(Frozen, frozen=True, kw_only=True):
    """The review that is due: its attempt and round, the tip it reads, its floor and why, the
    kinds, each reason the request is careful, the track, the plan's tasks, the change's lines
    and whether it is read in parts, a conflict's resolution, the reviews before it, the
    inputs, and where the record goes."""

    task: str
    attempt: int
    round: int
    tip: str
    floor: str
    floor_why: str
    careful: tuple[str, ...] = ()
    small: bool
    tasks: int | None = None
    lines: int
    in_parts: bool
    resolution: Resolution | None = None
    range_diff: str | None = None
    reads: tuple[Reviewed, ...] = ()
    inputs: Inputs
    record: str


def there(path: Path) -> str | None:
    """The path, when a file is there."""
    return str(path) if path.is_file() else None


def inputs(
    context: Context, found: review_facts.Gathered, topics: tuple[str, ...]
) -> Inputs:
    """The reviewer's inputs, each file of the task's folder that is there; the plan, or the
    fast track's criterion file."""
    folder, task, world = context.folder, context.record.task, context.world
    checked = (context.record.landing or Landing()).checked
    span = f"{world.base}..{world.tip}"
    return Inputs(
        ask=task.ask,
        words=there(folder / "ask.txt"),
        request=there(folder / "task.md"),
        plan=task.plan.path if task.plan else there(folder / "criteria.md"),
        range=span,
        rules=f"lem --repo {context.worktree} rules --range {span}",
        worktree=str(context.worktree),
        lowered=checked.lowered if checked else (),
        topics=topics,
        filed=found.filed,
        backlog=found.backlog,
        edited=found.edited,
    )


def made(
    context: Context,
    found: review_facts.Gathered,
    facts: review_due.Facts,
    topics: tuple[str, ...],
) -> Brief:
    """The brief of the review that is due now."""
    landing, task = context.record.landing or Landing(), context.record.task
    resolution = review_due.resolution_due(landing, context.world)
    attempt = len(landing.reviews) + 1
    least = review_due.floor(context.record, facts.careful, resolution=bool(resolution))
    return Brief(
        task=task.slug,
        attempt=attempt,
        round=max(len(review_due.rounds(landing)) + (resolution is None), 1),
        tip=context.world.tip or "",
        floor=least.kind,
        floor_why=least.why,
        careful=facts.careful,
        small=bool(task.shape and task.shape.track == "small"),
        tasks=task.plan.tasks if task.plan else None,
        lines=found.lines,
        in_parts=found.lines > READ_AT,
        resolution=resolution,
        range_diff=range_of(context, resolution),
        reads=landing.reviews,
        inputs=inputs(context, found, topics),
        record=RECORD.format(attempt),
    )


def range_of(context: Context, resolution: Resolution | None) -> str | None:
    """The command that shows what a builder's resolution changed: the task's commits before
    the rebase beside the same commits after it (prompt step 1, `land.due_of` on `main`)."""
    if resolution is None:
        return None
    git = context.ports.git
    old = git.merge_base(context.worktree, resolution.before, resolution.after)
    commits = (
        old or resolution.base,
        resolution.before,
        resolution.base,
        resolution.after,
    )
    return RANGE_DIFF.format(*(one[:SHORT] for one in commits))


def published(context: Context, brief: Brief) -> str:
    """Publish the brief in the task's folder, once for its attempt, and give its path."""
    encoded = msgspec.json.format(msgspec.json.encode(brief))
    short = files.digest(encoded)[:SHORT]
    named = f"reviews/read-{brief.attempt}-{short}.json"
    files.publish(context.folder / named, encoded)
    return named
