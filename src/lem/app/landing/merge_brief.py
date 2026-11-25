"""The merge agent's brief: the standing text it follows, by its place in the plugin, and the
facts of the task as JSON, published at a path named by the tip and the base it reads, so that
the brief of a later base never takes the place of the one an agent was started with
(`main:land.cmd_merge_review`, `brief_file`; `skills/lem/prompts/merge.md`)."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import merge_world
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing import merge
from lem.records.base import Frozen, Sha
from lem.records.landing.record import Landing, Pull

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.records.landing.propose import Proposed

SHORT = 12
BRIEF = "merge-brief-{0}-{1}.md"
# The first line of every brief: the standing text by its place in the plugin, never by the
# folder of the Lem that wrote the brief, which an update replaces.
FOLLOW = (
    "Read `skills/lem/prompts/merge.md` in the folder that `lem version` prints as `root`, "
    "and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, "
    "with `lem doctor` as the check. Your reply is the review, in the form that file gives, "
    "and nothing else: its first line `Verdict: merge.` or `Verdict: call.`, and on a moved "
    "base its second line `Base: safe.` or `Base: another round.`, each with one sentence of "
    "why."
)
# The task's files the agent reads where they are, each by the key the standing text names.
BODY = "{0}\n\nThe facts of this task, as `lem land merge-review` gave them:\n\n```json\n{1}\n```\n"
TASK_FILES = (
    ("words", "ask.txt"),
    ("request", "task.md"),
    ("criteria", "criteria.md"),
    ("report", "report.md"),
    ("notes", "notes.md"),
    ("investigation", "investigation.md"),
)


class Brief(Frozen, frozen=True, kw_only=True):
    """The brief the merge agent reads: its path, and the tip and base it is of."""

    brief: str
    tip: Sha
    base: Sha


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
    pictures: tuple[str, ...]
    filed: tuple[str, ...]
    stand_ins: tuple[str, ...]
    try_it: dict[str, str] = msgspec.field(name="try")
    base: Sha
    moved: merge_world.Moved | None


def path_of(context: Context, tip: str, base: str) -> Path:
    """The brief of `tip` on `base` in the task's folder."""
    return context.folder / BRIEF.format(tip[:SHORT], base[:SHORT])


def found(folder: Path, pattern: str) -> tuple[str, ...]:
    """The files of the task's folder that `pattern` names, by their whole paths, sorted."""
    return tuple(sorted(str(path) for path in folder.glob(pattern) if path.is_file()))


def texts_of(folder: Path, proposed: Proposed) -> dict[str, str]:
    """The task's files the agent reads, by their keys: the pull request's text, the owner's
    words, the request, the criteria, the report, the notes, an investigation."""
    texts = {
        key: str(folder / name) for key, name in TASK_FILES if (folder / name).is_file()
    }
    if proposed.text:
        texts["pull_request_text"] = str(folder / proposed.text)
    return texts


def facts_of(context: Context, landing: Landing, read: tuple[Pull, Proposed]) -> Facts:
    """The facts of the proposed tip (`read`: its pull request and proposal) on origin's base
    now; `range` starts at the base the checks ran on."""
    world, (pull, proposed) = context.world, read
    ran = landing.checked.base if landing.checked else world.base
    worktree, task = str(context.worktree), context.record.task
    return Facts(
        task=task.slug,
        worktree=worktree,
        task_directory=str(context.folder),
        pull_request=pull,
        tip=proposed.tip,
        range=f"{ran}..{proposed.tip}",
        diff=f"git -C {worktree} diff {ran}..{proposed.tip}",
        changed=context.ports.git.diff_stat(
            context.workspace.checkout, ran, proposed.tip
        ).paths,
        track="standard" if task.shape and task.shape.track == "full" else "fast",
        files=texts_of(context.folder, proposed),
        reviews=found(context.folder, "reviews/review-*"),
        decisions=f"lem decisions list {task.slug}",
        green=not proposed.reasons,
        not_green=proposed.reasons,
        careful=proposed.careful,
        land=world.rules.land,
        owner_merges=merge.authority(context.record, world),
        relands=landing.relands,
        pictures=found(context.folder, "media/**/*.*"),
        filed=tuple(done.path for done in landing.filed if done.path),
        stand_ins=tuple(f"{one.seat}: {one.took}" for one in task.stand_ins),
        try_it={"worktree": worktree, "checkout": f"gh pr checkout {pull.number}"},
        base=world.base,
        moved=merge_world.moved_of(context, proposed.tip),
    )


def published(context: Context) -> Brief:
    """Publish the brief of the proposed tip on origin's base now, once: a brief already
    published for that tip and base is the one a fresh merge agent reads again."""
    landing = context.record.landing or Landing()
    pull, proposed = landing.pull, landing.proposed
    if pull is None or proposed is None:
        slug = context.record.task.slug
        raise Refusal(
            "no-pull",
            f"{slug} proposes no pull request yet",
            f"lem land propose {slug}",
        )
    path = path_of(context, proposed.tip, context.world.base)
    if not path.is_file():
        facts = msgspec.json.encode(facts_of(context, landing, (pull, proposed)))
        shown = msgspec.json.format(facts, indent=2).decode()
        files.publish(path, BODY.format(FOLLOW, shown).encode())
    return Brief(brief=str(path), tip=proposed.tip, base=context.world.base)
