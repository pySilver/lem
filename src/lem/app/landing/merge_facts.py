"""The facts of a task as the merge agent's brief gives them, by the keys of its standing text
(`skills/lem/prompts/merge.md`; `main:land.cmd_merge_review`): the task's folder and worktree,
the pull request, the range and its diff, the track, the task's files, the reviews, whether it
is green and careful, who lands, why the owner merges, the pictures, the filed items, the
stand-ins, the two ways the owner tries the branch, the base it reads, and what moved on it."""

import shlex
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import merge_artifacts, merge_compared, merge_time, merge_world
from lem.model.landing import merge
from lem.records.base import Frozen, Sha
from lem.records.landing.record import Pull

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.landing.propose import Proposed
    from lem.records.landing.record import Landing

# The task's files the agent reads where they are, each by the key the standing text names.
TASK_FILES = (
    ("words", "ask.txt"),
    ("request", "task.md"),
    ("criteria", "criteria.md"),
    ("report", "report.md"),
    ("notes", "notes.md"),
    ("investigation", "investigation.md"),
)


class Moved(Frozen, frozen=True, kw_only=True):
    """What moved on the base since the checks, as the merge agent's brief gives it: the base
    the checks ran on, the base now, each commit between them by its sha and subject, the
    files they changed, and which of those the task's change touches too
    (`main:land.moved_of`)."""

    checks_ran_on: Sha
    base_now: Sha
    commits: tuple[tuple[Sha, str], ...]
    files: tuple[str, ...]
    overlap: tuple[str, ...]


class Facts(msgspec.Struct, frozen=True, kw_only=True):
    """The facts of the task as the brief gives them, by the keys of the standing text."""

    task: str
    worktree: str
    task_directory: str
    pull_request: Pull
    tip: Sha
    range: str
    diff: str
    changed: tuple[str, ...]
    track: str
    files: dict[str, str]
    reviews: tuple[str, ...]
    decisions: str
    green: bool
    not_green: tuple[str, ...]
    careful: bool
    land: str
    owner_merges: str | None
    relands: int
    time: merge_time.Time
    pictures: tuple[str, ...]
    filed: tuple[str, ...]
    stand_ins: tuple[str, ...]
    try_it: dict[str, str] = msgspec.field(name="try")
    base: Sha
    moved: Moved | None


def found(folder: Path, pattern: str) -> tuple[str, ...]:
    """The files of the task's folder that `pattern` names, by their whole paths, sorted."""
    paths = filter(Path.is_file, folder.glob(pattern))
    return tuple(sorted(map(str, paths)))


def texts_of(folder: Path, proposed: Proposed) -> dict[str, str]:
    """The task's files the agent reads, by their keys: the pull request's text, the owner's
    words, the request, the criteria, the report, the notes, an investigation."""
    texts: dict[str, str] = {}
    for key, name in TASK_FILES:
        if (folder / name).is_file():
            texts[key] = str(folder / name)
    if proposed.text:
        texts["pull_request_text"] = str(folder / proposed.text)
    return texts


def facts_of(context: Context, landing: Landing, read: tuple[Pull, Proposed]) -> Facts:
    """The facts of the proposed tip (`read`: its pull request and proposal) on origin's base
    now; `range` starts at the base the checks ran on."""
    pull, proposed = read
    ran = landing.checked.base if landing.checked else context.world.base
    worktree, task = str(context.worktree), context.record.task
    return Facts(
        task=task.slug,
        worktree=worktree,
        task_directory=str(context.folder),
        pull_request=pull,
        tip=proposed.tip,
        range=f"{ran}..{proposed.tip}",
        diff=f"git -C {shlex.quote(worktree)} diff {ran}..{proposed.tip}",
        changed=context.ports.git.diff_stat(
            context.workspace.checkout, ran, proposed.tip
        ).paths,
        track="standard" if task.shape and task.shape.track == "full" else "fast",
        files=texts_of(context.folder, proposed),
        reviews=tuple(
            str(context.folder / one.review) for one in landing.reviews if one.review
        ),
        decisions=f"lem decisions list {task.slug}",
        green=not proposed.reasons,
        not_green=proposed.reasons,
        careful=proposed.careful,
        land=context.world.rules.land,
        owner_merges=merge.authority(context.record, context.world, verdict=False),
        relands=landing.relands,
        time=merge_compared.compared(context.record, context.workspace.state),
        pictures=merge_artifacts.pictures_of(context.folder),
        filed=merge_artifacts.items_of(context, proposed),
        stand_ins=tuple(f"{one.seat}: {one.took}" for one in task.stand_ins),
        try_it={"worktree": worktree, "checkout": f"gh pr checkout {pull.number}"},
        base=context.world.base,
        moved=moved_of(context, proposed.tip),
    )


def what_moved(context: Context, ran: Sha, tip: Sha) -> Moved:
    """What moved on origin's base since the checks ran on `ran`, beside the files of the
    change up to `tip`."""
    git, checkout, now = (
        context.ports.git,
        context.workspace.checkout,
        context.world.base,
    )
    files = git.diff_stat(checkout, ran, now).paths
    own = set(git.diff_stat(checkout, ran, tip).paths)
    return Moved(
        checks_ran_on=ran,
        base_now=now,
        commits=tuple(
            (made.sha, made.subject) for made in git.commits(checkout, ran, now)
        ),
        files=files,
        overlap=tuple(path for path in files if path in own),
    )


def moved_of(context: Context, tip: Sha) -> Moved | None:
    """What moved on origin's base since the checks ran, beside the files of the change; None
    when origin's base has the checks' base tree (nothing moved, or a revert)."""
    landing = context.record.landing
    checked = landing.checked if landing else None
    if checked is None or merge_world.checks_tree(context) == context.world.base_tree:
        return None
    return what_moved(context, checked.base, tip)
