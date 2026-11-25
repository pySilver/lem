"""`merge-review`: the merge agent's read of the proposed tip on origin's base (`landing.md` C,
"In `open`"; D, the merge read's carry).

A read is usable while it gave a verdict for the proposed tip on origin's base as it is now. The
plain path writes the agent's brief and takes its reply; an unusable answer, a read carried over a
moved base, `another round` and a safe read on a moved base are the step `land-merge`'s.
"""

from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.model.landing.world import World, later
from lem.records.landing.propose import MergeRead, Proposed
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "merge-review"
type Verdict = Literal["merge", "call"]
VERDICTS: tuple[Verdict, ...] = ("merge", "call")
# The marks of markdown a reply's first line may carry around its verdict.
MARKS = str.maketrans("", "", "*#`_")


def read_of(landing: Landing) -> MergeRead | None:
    """The newest read with a verdict for the proposed tip, on whatever base it read."""
    proposed = landing.proposed
    tip = proposed.tip if proposed else None
    found = [read for read in landing.reads if read.verdict and read.tip == tip]
    return found[-1] if found else None


def usable(landing: Landing, world: World) -> MergeRead | None:
    """The newest read with a verdict for the proposed tip on origin's base now."""
    read = read_of(landing)
    return read if read is not None and read.base == world.base else None


def verdict_of(reply: str) -> Verdict | None:
    """The verdict on the reply's first line: its first word, `merge` or `call`, after a
    `Verdict:` the merge agent's prompt asks for."""
    lines = reply.strip().splitlines() or [""]
    plain = lines[0].lower().translate(MARKS)
    words = plain.strip().removeprefix("verdict:").split() or [""]
    first = words[0].strip(":._")
    return next((word for word in VERDICTS if word == first), None)


def brief_refusal(record: Record) -> Refusal | Proposed:
    """The proposal the brief is of, or why there is none to read."""
    proposed = (record.landing or Landing()).proposed
    slug = record.task.slug
    if proposed is None:
        return Refusal(
            "no-pull",
            f"{slug} proposes no pull request yet",
            f"lem land propose {slug} comes first",
        )
    return proposed


def old(slug: str, read: str, now: str) -> Refusal:
    """The refusal of a reply of the brief of another tip and base (`read`) than those
    `now`."""
    return Refusal(
        "old-tip",
        f"the reply is of the brief of {read}, and the proposal is {now} now",
        f"lem land merge-review {slug} writes the brief of them now",
    )


def decide(
    record: Record, world: World, reply: str, read: tuple[str, str]
) -> Refusal | MergeRead:
    """The read to record for the reply of the brief of `read`, its tip and base, or why it
    is refused: a reply of another tip, or of a base that moved since, covers nothing now."""
    proposed = brief_refusal(record)
    if isinstance(proposed, Refusal):
        return proposed
    if read != (proposed.tip, world.base):
        now = f"{proposed.tip} on {world.base}"
        return old(record.task.slug, " on ".join(read), now)
    if world.base != proposed.base:
        return later(
            "a read of a base that moved after the checks: safe or another round",
            "land-merge",
        )
    verdict = verdict_of(reply)
    if verdict is None:
        return later("a reply with no verdict on its first line", "land-merge")
    landing = record.landing or Landing()
    return MergeRead(
        tip=proposed.tip,
        base=world.base,
        base_tree=world.base_tree,
        verdict=verdict,
        why=reply.strip(),
        attempts=len(landing.reads) + 1,
        at=world.now,
    )
