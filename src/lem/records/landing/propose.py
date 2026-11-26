"""The pull request's proposal, each start of the merge agent and its read, and the owner's
standing merge (`landing.md` A, `Proposed`, `MergeRead`, `Standing`)."""

from typing import Literal

from lem.records.base import Frozen, Moment, Sha, TaskPath


class OwnerMerge(Frozen, frozen=True, kw_only=True):
    """The owner's merge refused for the base: it stands while coverage holds and the reasons
    are the same, else it ended; why, either way."""

    state: Literal["stands", "ended"]
    why: str


class Proposed(Frozen, frozen=True, kw_only=True):
    """`propose`: the tip and base, the criteria's contract mark it proposed under, green or the
    reasons it is not, the careful call and whether it includes the owner's word, the notes,
    the pull request's text the forge confirmed
    and the body that waits, whether a merge read carried, the owner's standing merge, and who
    acts on the merge."""

    tip: Sha
    base: Sha
    contract: str | None = None
    green: bool
    reasons: tuple[str, ...] = ()
    careful: bool = False
    owner_careful: bool = False
    notes_path: TaskPath | None = None
    text: TaskPath | None = None
    text_waits: TaskPath | None = None
    merge_review: Literal["carried"] | None = None
    merge_review_why: str | None = None
    owner_merge: OwnerMerge | None = None
    who_acts: Literal["owner", "merger"]
    at: Moment


class MergeDispatch(Frozen, frozen=True, kw_only=True):
    """One start of the merge agent: its number, which its reply carries back, the tip, base
    and round of its brief, the seat it was started on, and the brief it reads."""

    number: int
    tip: Sha
    base: Sha
    round: int
    seat: str
    brief: TaskPath
    at: Moment


class MergeRead(Frozen, frozen=True, kw_only=True):
    """The merge agent's read of a tip on a base: its verdict, its call on a moved base, why,
    the read it carried from, the attempts, an unusable answer, the brief it read, and the
    dispatch it answers."""

    tip: Sha
    base: Sha
    base_tree: Sha
    verdict: Literal["merge", "call"] | None = None
    base_call: Literal["safe", "another round"] | None = None
    why: str | None = None
    carried_from: Sha | None = None
    attempts: int = 1
    no_answer: bool = False
    by: str | None = None
    brief: TaskPath | None = None
    dispatch: int | None = None
    at: Moment


class Standing(Frozen, frozen=True, kw_only=True):
    """The owner's merge, refused for the base, that the server carries out when the read is
    safe: the tip, the digest of the reasons it was not green, and his act."""

    tip: Sha
    reasons_digest: str
    by_act: str
    at: Moment
