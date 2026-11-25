"""What a merge checks against the world read again under the merge lock (`landing.md` H 1, 2
and 4; `main:land.merge_locked`): the pull request as proposed and into the task's base, the
local tip, the checks of that tip, and origin's base, unmoved since the checks by its tree or
covered by a safe read.

The forge pins only the head; everything else is read again here, before the intent is
written. `checks` is the tree of the base the checks ran on, which the app reads from git.
"""

from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing import checks, mergeread
from lem.model.landing.invariants import protected
from lem.model.landing.world import Due, Merger, World
from lem.records.landing.merge import Refused
from lem.records.landing.propose import Standing
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record

TIP = "tip"


def forge_side(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """Why the pull request is not the one proposed: none, not open, retargeted before the
    merge, or at another head."""
    slug, pull, base = record.task.slug, world.pull, world.rules.base
    if pull is None:
        return Refusal(
            "no-pull", f"{slug} has no pull request", f"lem land next {slug}"
        )
    if pull.state != "open":
        return Refusal(
            "closed",
            f"the pull request {pull.url} is {pull.state} on GitHub: nothing was merged",
            f"lem land merged {slug} writes it down first",
        )
    if pull.base != base:
        return Refusal(
            "target",
            f"the pull request {pull.url} is on {pull.base} on GitHub, not on {base}, the "
            "base of the task's settings: its base was changed there; nothing was merged",
            f"gh pr edit {pull.number} --base {base}, then lem land merge {slug} again",
        )
    if pull.head != proposed.tip:
        return Refusal(
            TIP,
            f"the pull request's head is {pull.head}, not the proposed {proposed.tip}",
            f"lem land next {slug} names the new round",
        )
    return None


def covered(record: Record, world: World, tip: str) -> Refusal | None:
    """Why no passed run of the checks covers `tip` with the definitions as now (H 1), by the
    checks' own rule."""
    found = checks.holds(record, replace(world, tip=tip))
    if not isinstance(found, Due):
        return None
    slug = record.task.slug
    return Refusal(
        "checks-changed",
        f"no passed run of the checks covers {tip} with the checks as they are now: "
        f"{found.why}",
        f"lem land next {slug} names the step that runs them",
    )


def our_side(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """Why the proposal is not what the checks covered: a local tip that moved, or no passed
    run of the checks of that tip as they are now."""
    if world.tip != proposed.tip:
        slug = record.task.slug
        return Refusal(
            TIP,
            f"the task's branch is at {world.tip}, not the proposed {proposed.tip}",
            f"lem land next {slug} names the new round",
        )
    return covered(record, world, proposed.tip)


def base_side(record: Record, world: World, checks_tree: str) -> Refusal | None:
    """Why origin's base may not take the merge: protected, or moved since the checks (by its
    tree) with no safe read of the merge agent that covers it now."""
    guard = protected(world.rules.base, world.rules, "merges")
    if guard is not None or world.base_tree == checks_tree:
        return guard
    landing = record.landing or Landing()
    read = mergeread.usable(landing, world)
    if read is not None and read.base_call == "safe":
        return None
    slug, branch = record.task.slug, world.rules.base
    ran = landing.checked.base if landing.checked else "the checks' base"
    return Refusal(
        "base",
        f"origin's {branch} moved after the checks ran on {ran}, and no read of the merge "
        f"agent covers {branch} at {world.base} as safe: nothing was merged",
        f"lem land merge-review {slug} writes the brief of what moved; a fresh merge agent "
        "reads it, and on `Base: safe.` the merge goes on that base",
    )


def digest_of(reasons: tuple[str, ...]) -> str:
    """One digest of the reasons a proposal is not green, which a standing merge keeps."""
    return files.digest(msgspec.json.encode(reasons))


def standing_of(landing: Landing) -> Standing | None:
    """The owner's merge that stands for the proposed tip: refused for the base, with the
    reasons it is not green unchanged since (`landing.md` D, "Standing merge")."""
    proposed, standing = landing.proposed, landing.standing
    if proposed is None or standing is None or standing.tip != proposed.tip:
        return None
    return standing if standing.reasons_digest == digest_of(proposed.reasons) else None


def kept(
    landing: Landing, refusal: Refusal, asked: tuple[Merger, str], now: Moment
) -> tuple[Refused, Standing | None] | None:
    """What a refusal of the merge for the base keeps (`asked`: who asked, through what): its
    `Refused` of Lem for the proposed tip, so the server tries that tip no more, and, for the
    owner's merge, his merge standing until a safe read (`main:land.kept_refusal`). None for
    any other refusal, which keeps nothing."""
    proposed = landing.proposed
    if refusal.code != "base" or proposed is None:
        return None
    by, via = asked
    refused = Refused(
        tip=proposed.tip, source="lem", kind="base", line=refusal.why, by=by, at=now
    )
    if by != "owner":
        return refused, None
    reasons = digest_of(proposed.reasons)
    standing = Standing(tip=proposed.tip, reasons_digest=reasons, by_act=via, at=now)
    return refused, standing
