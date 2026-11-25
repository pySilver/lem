"""The facts under a row's verb on Waits for you (`board_pages.wait_article` on `main`): a
breaker's what and why, the line of the owner's wait when the verb does not say it, and a merge's
marks and its reasons, or what green means."""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.inputs import names
from lem.board.inputs.parts import Chip
from lem.board.views import hovers, reasons, words
from lem.records.decisions import Breaker
from lem.records.holds import OwnerHold
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.board.inputs.waits import Reasons
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Row

GREEN = (
    "The checks passed with the bar where it was, the review left no must-fix, no "
    "criterion changed, and no decision past the personas was taken without an answer."
)


class Facts(NamedTuple):
    """What a row says under its verb: what it is about, its line, its marks, its reasons."""

    what: str | None = None
    sub: str | None = None
    marks: tuple[Chip, ...] = ()
    reasons: Reasons | None = None


def facts(world: World, seen: Seen, row: Row, verb: str) -> Facts:
    """The facts of `row`, whose verb is `verb`."""
    if row.kind == "breaker":
        return breaker_facts(seen)
    if row.kind == "merge":
        return merge_facts(world, seen)
    shown = held_line(seen) if row.kind in {"held", "criteria"} else ""
    if shown and shown.lower() != verb.lower():
        return Facts(sub=words.capital(shown))
    return Facts()


def held_line(seen: Seen) -> str:
    """The line of the owner's hold, in the board's words; "" with none."""
    hold = seen.record.task.hold
    line = hold.line if isinstance(hold, OwnerHold) else ""
    return words.said(line) if line else ""


def breaker_facts(seen: Seen) -> Facts:
    """The breaker that holds the task: what it is about, and why it stopped the build."""
    task = seen.record.task
    number = getattr(task.hold, "number", None)
    found = (
        one for one in task.decisions if isinstance(one, Breaker) and one.id == number
    )
    breaker = next(found, None)
    if breaker is None:
        return Facts()
    return Facts(what=breaker.what, sub=words.capital(hovers.stop_words(breaker)))


def merge_facts(world: World, seen: Seen) -> Facts:
    """A merge's marks (green or not, the pull request) and its reasons, or what green
    means."""
    landing = seen.record.landing or Landing()
    proposed = landing.proposed
    marks = marks_of(landing)
    if proposed is not None and proposed.green:
        return Facts(marks=marks, sub=GREEN)
    slug = seen.record.task.slug
    shown = reasons.reasons(seen.record, f"wr-{slug}", "waits", world.viewer.base)
    return Facts(marks=marks, reasons=shown)


def marks_of(landing: Landing) -> tuple[Chip, ...]:
    """A merge's marks: green or not green, and the pull request."""
    proposed, pull = landing.proposed, landing.pull
    found = (
        verdict_chip(green=proposed.green) if proposed else None,
        names.pull_chip(pull, whole=True) if pull else None,
    )
    return tuple(chip for chip in found if chip is not None)


def verdict_chip(*, green: bool) -> Chip:
    """Green, with what it means, or not green."""
    if green:
        return Chip(
            label="green", icon="check", look="ok", title=GREEN.removesuffix(".")
        )
    return Chip(label="not green", icon="triangle-exclamation", look="you")
