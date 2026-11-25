"""The feed's words of the merge's entries: the merge agent's read, with its call on a moved base,
a refusal, the merge, and a new round (`merge_review_said` and `merge.refused` of `main`; the
merge and the new round had a state of their own there)."""

from typing import TYPE_CHECKING

from lem.board.views.activity.told import ALERT, BAD, DONE, GATE, PAGE, YOU, Told
from lem.model.landing import mergeread

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.records.journal.merge import LandAgain, MergeNoted, ReadNoted, RefusalNoted
    from lem.records.landing.propose import MergeRead

READ = "The merge agent read the task"
MOVED = "The merge agent read the task and the moved base"
AGAIN = "Lem lands it again"
# Lem recorded another round in the place of the merge agent's answer, which it could not record.
UNRECORDED = "The merge agent's answer could not be recorded"
SHORT = 9


def read(entry: ReadNoted) -> Told:
    """The merge agent's read: its verdict, and on a moved base its call on that base."""
    seen = entry.read
    look, verdict = verdict_of(seen)
    sub = said_by(seen)
    if seen.base_call is None:
        return Told(look, PAGE, READ, verdict, sub)
    return moved(seen, Told(look, PAGE, MOVED, verdict, sub))


def moved(seen: MergeRead, plain: Told) -> Told:
    """The read of a moved base: safe, so the verdict holds; another round; or another round
    Lem recorded in the place of an answer it could not record."""
    short = seen.base[:SHORT]
    base = f"the moved base {short}"
    if seen.base_call == "safe":
        safe = f"{base} is safe; {plain.text}"
        return Told(plain.look, PAGE, MOVED, safe, plain.sub)
    if seen.no_answer:
        said = f"{base} gets another round of the checks in doubt: {AGAIN}"
        return Told(GATE, PAGE, UNRECORDED, said, plain.sub)
    said = f"{base} needs another round of the checks: {AGAIN}"
    return Told(GATE, PAGE, MOVED, said, plain.sub)


def verdict_of(seen: MergeRead) -> tuple[Look, str]:
    """A read that calls the owner is his; one that merges is the landing's."""
    if seen.verdict == "call":
        return YOU, "it calls you"
    if seen.verdict == "merge":
        return GATE, "it merges"
    if not mergeread.settled(seen):
        return GATE, "another read is due"
    return YOU, "no verdict was recorded. The owner merges it."


def said_by(seen: MergeRead) -> str:
    """The read's sentence of why, or who read it."""
    if seen.why:
        return seen.why
    return f"by {seen.by}" if seen.by else ""


def refusal(entry: RefusalNoted) -> Told:
    """A merge refused: by Lem, of the owner's merge or the merge agent's, or by GitHub."""
    refused = entry.refusal
    if refused.source == "github":
        head = "GitHub refused the merge"
    elif refused.by == "owner":
        head = "Lem refused your merge"
    else:
        head = "Lem refused the merge agent’s merge"
    return Told(BAD, ALERT, head, refused.line)


def merged(entry: MergeNoted) -> Told:
    """The merge: whose, and its commit."""
    done = entry.merged
    if done.by == "owner":
        whose = "your merge"
    elif done.via == "server":
        whose = "the merge agent’s merge, which the board’s server ran"
    else:
        whose = "the merge agent’s merge"
    commit = done.commit[:SHORT]
    return Told(DONE, "code-branch", "The pull request is merged", whose, commit)


def again(entry: LandAgain) -> Told:
    """A new round of the landing, and whether a conflict on GitHub brought it."""
    said = f"round {entry.round}"
    if entry.conflicting:
        said = f"{said}: GitHub calls the pull request conflicting"
    return Told(GATE, "rotate", AGAIN, said)
