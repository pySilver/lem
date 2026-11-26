"""What every stage of the landing reads: the world gathered now, and what a stage says of it,
held or due (`landing.md` C).

The world is gathered fresh by `app/landing/world.py` before each step: the worktree, origin's
base and the task's branch there, the forge's pull request, the settings of the main checkout and
the moment. A stage's `holds` reads it with the record and says `Held` or `Due`; nothing here
starts a process or reads a clock.
"""

from typing import Literal

from lem.model.landing.queue_evidence import Event
from lem.records.base import Frozen, Moment, Sha

type Verb = Literal[
    "start",
    "base",
    "polish",
    "checks",
    "read",
    "file",
    "propose",
    "merge-review",
    "merge",
    "merged",
    "clean",
]
# No step is due: the task waits (for the owner, a builder, the forge), it ended, or it is not
# ready to land.
type Rest = Literal["wait", "done", "none"]
type Merger = Literal["owner", "merger"]


class Rules(Frozen, frozen=True, kw_only=True):
    """The settings a landing reads, from the main checkout: the base, who lands, what lands,
    the protected branches, and the checks."""

    base: str
    land: Literal["agent", "owner"] = "agent"
    history: Literal["squash", "keep"] = "squash"
    protected: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    serial: tuple[str, ...] = ()
    setup: tuple[str, ...] = ()
    own_checks: bool = False


class PullSeen(Frozen, frozen=True, kw_only=True):
    """The task's pull request as the forge reports it now."""

    number: int
    url: str
    title: str
    body: str = ""
    state: Literal["open", "closed", "merged"]
    head: Sha
    base: str
    queued: str | None = None
    dequeued: str | None = None
    queue_event: Event | None = None
    queue_entered: Event | None = None
    merge_commit: Sha | None = None
    merged_head: Sha | None = None
    base_parent: Sha | None = None


class World(Frozen, frozen=True, kw_only=True):
    """The facts of one moment: the task's branch and worktree (its tip and tree, clean, a
    rebase in progress), origin's base, its tree and whether the tip holds it, origin's task
    branch and whether the tip holds it, the local branch and whether origin's base holds it,
    the pull request on record, the open ones on the branch while none is on record
    (`candidates`), the settings and the moment."""

    rules: Rules
    branch: str
    base: Sha
    base_tree: Sha
    now: Moment
    tip: Sha | None = None
    tree: Sha | None = None
    clean: bool = False
    rebasing: bool = False
    base_in_tip: bool = False
    remote: Sha | None = None
    remote_in_tip: bool = False
    local: Sha | None = None
    local_in_base: bool = False
    pull: PullSeen | None = None
    candidates: tuple[PullSeen, ...] = ()
    item_chain: tuple[Sha, ...] = ()
    own_item_removed_from: Sha | None = None
    dequeued: str | None = None

    def items_from(self, tip: Sha) -> bool:
        """Whether the item-only history joins the checked tip to this tip."""
        chain = self.item_chain
        if not chain or chain[0] != tip:
            return False
        return chain[-1] == self.tip


class Held(Frozen, frozen=True, kw_only=True):
    """A stage whose evidence holds for the world now, and why."""

    why: str


class Due(Frozen, frozen=True, kw_only=True):
    """The step that is due and why; `by` says who merges when the merge is due."""

    step: Verb | Rest
    why: str
    by: Merger | None = None
