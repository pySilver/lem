"""The merge agent's brief: the standing text it follows, by its place in the plugin, and the
facts of the task as JSON (`merge_facts.py`), published once at a path named by the tip and the
base it reads, so that the brief of a later base never takes the place of the one an agent was
started with, and a fresh agent asked again reads the same brief (`main:land.brief_file`)."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import merge_facts
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Sha
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.records.landing.propose import Proposed
    from lem.records.landing.record import Pull
    from lem.records.record import Record

SHORT = 12
BRIEF = "merge-brief-{0}-{1}-{2}.md"
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
BODY = (
    "{0}\n\nThe facts of this task, as `lem land merge-review` gave them:\n\n"
    "```json\n{1}\n```\n"
)


class Brief(Frozen, frozen=True, kw_only=True):
    """The brief the merge agent reads: its path, and the tip and base it is of."""

    brief: str
    tip: Sha
    base: Sha


def path_of(context: Context, tip: str, base: str) -> Path:
    """The brief of `tip` on `base` in the task's folder."""
    landing = context.record.landing or Landing()
    round_number = landing.round
    named = BRIEF.format(tip[:SHORT], base[:SHORT], round_number)
    return context.folder / named


def proposal_of(record: Record) -> tuple[Pull, Proposed]:
    """The pull request and the proposal the brief is of, or why there is none to read."""
    landing = record.landing or Landing()
    if landing.pull is None or landing.proposed is None:
        slug = record.task.slug
        raise Refusal(
            "no-pull",
            f"{slug} proposes no pull request yet",
            f"lem land propose {slug}",
        )
    return landing.pull, landing.proposed


def text_of(context: Context, read: tuple[Pull, Proposed]) -> bytes:
    """The brief's text: the line that names the standing text, then the facts."""
    landing = context.record.landing or Landing()
    facts = msgspec.json.encode(merge_facts.facts_of(context, landing, read))
    shown = msgspec.json.format(facts, indent=2).decode()
    return BODY.format(FOLLOW, shown).encode()


def published(context: Context) -> Brief:
    """Publish the brief of the proposed tip on origin's base now, once: a brief already
    published for that tip and base is the one a fresh merge agent reads again."""
    read = proposal_of(context.record)
    tip, base = read[1].tip, context.world.base
    path = path_of(context, tip, base)
    if not path.is_file():
        files.publish(path, text_of(context, read))
    return Brief(brief=str(path), tip=tip, base=base)
