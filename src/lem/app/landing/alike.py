"""`lem land alike`: the items of the backlog folder, as the task's tip holds them, that Jev
reads as the same defect as a finding (`land.cmd_alike` on `main`). The fast track's builder
runs it before it files an item by hand (`prompts/small.md`, step 7).

It reads the worktree and asks Jev; it takes no lock and writes nothing, so a builder runs it
while the task's session waits. With Jev not asked, it lists every item for the agent to read.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import alike_words, backlog, frame, judge_same
from lem.app.tasks import where
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal
from lem.model.landing import alike as same
from lem.ports.judge import NotAsked
from lem.records.base import Frozen
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.items import BacklogItem, Defect

READ_THEM = (
    "Jev was not asked: read the items of `read` whose title or `where` is near the finding, "
    "and judge it by rule 6 as for the items `alike` names"
)
NAMED = (
    "read each item named here. One that holds the same defect gets no second file: name it "
    "on the finding's line. When it says `worth: no` and your call is over the bar, file a new "
    'item with `worth: later` whose run is followed by the line "The same defect as `PATH`, '
    'now over the bar.", and leave the old item as it is. A defect none of them holds you '
    "judge by the bar of rule 6"
)
NONE_NAMED = (
    f"Jev reads no item as the same defect at {same.SAME_AT} or more: judge the finding by "
    "the bar of rule 6"
)
OFF = NotAsked(why="off in the settings")
type Said = dict[str, float | None] | NotAsked


class Listed(Frozen, frozen=True, kw_only=True):
    """An item of the backlog folder, as the agent reads it with Jev not asked."""

    path: str
    title: str
    where: str | None = None
    worth: str | None = None


class Told(Frozen, frozen=True, kw_only=True):
    """What `alike` says: the task, the finding, how many items the folder holds, the items
    Jev names, why Jev was not asked and every item to read then, and what the agent does."""

    task: str
    finding: alike_words.Finding
    count: int = msgspec.field(name="items")
    named: tuple[same.Alike, ...] = msgspec.field(name="alike")
    jev: str | None = None
    read: tuple[Listed, ...] = ()
    next: str


def told(base: Told, shelved: tuple[BacklogItem, ...], said: Said) -> Told:
    """What `alike` says, from what Jev said of the finding."""
    if not shelved:
        why = "the backlog folder holds no item: judge the finding by the bar of rule 6"
        return msgspec.structs.replace(base, next=why)
    if isinstance(said, NotAsked):
        listed = msgspec.convert(shelved, tuple[Listed, ...], from_attributes=True)
        jev = f"Jev: not asked ({said.why})"
        return msgspec.structs.replace(base, jev=jev, read=listed, next=READ_THEM)
    found = same.named(judge_same.scored(said), shelved)
    if found:
        return msgspec.structs.replace(base, named=found, next=NAMED)
    return msgspec.structs.replace(base, next=NONE_NAMED)


def worktree_of(workspace: places.Workspace, slug: str) -> Path:
    """The task's worktree, refused when it is not there."""
    tasks.read(workspace.state, slug)
    path = where.worktree(workspace, slug)
    if not (path / ".git").exists():
        raise Refusal(
            "no-worktree",
            f"the task has no worktree at {path}, and `alike` reads the backlog folder as the "
            "task's tip holds it",
            f"lem task worktree {slug} makes it",
        )
    return path


def asked_of(
    workspace: places.Workspace, slug: str, defect: Defect
) -> tuple[tuple[BacklogItem, ...], Said]:
    """The items at the tip of the task's worktree, and Jev's scores of the finding against
    them, or why Jev was not asked."""
    ports = frame.bound(workspace)
    worktree = worktree_of(workspace, slug)
    tip = ports.git.tip(worktree, "HEAD") or ""
    shelved = backlog.at_tip(ports.git, worktree, tip)
    if not shelved or not judge_same.sends(workspace.checkout):
        return shelved, OFF
    staging = places.task_folder(workspace.state, slug) / judge_same.STAGED
    return shelved, judge_same.asked(ports.judge, staging, defect, shelved, {})


def run(folder: Path, slug: str, defect: Defect) -> Envelope:
    """`lem land alike SLUG --where PLACE --title TITLE --what FILE`."""
    shelved, said = asked_of(places.workspace(folder), slug, defect)
    base = Told(
        task=slug,
        finding=alike_words.Finding(where=defect.where, title=defect.title),
        count=len(shelved),
        named=(),
        next="",
    )
    encoded = msgspec.json.encode(told(base, shelved, said))
    return Envelope(ok=True, outcome=msgspec.Raw(encoded))
