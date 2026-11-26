"""The merge agent's brief: the standing text it follows, by its place in the plugin, and the
facts of the task as JSON (`merge_facts.py`), published once for each dispatch at a path named
by the tip and the base it reads, the round and the dispatch's number (`main:land.brief_file`).

The brief of a later base never takes the place of the one an agent was started with, and a
fresh agent asked again on the same seat reads the same brief. A stand-in, or a seat the
settings changed, is a new dispatch with a brief of its own, whose facts name the stand-in;
the brief the agent before it read stays as it was (`merge_dispatch.py`).
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import merge_dispatch, merge_facts
from lem.app.sessions.seating import Shown
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Sha
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.landing.propose import Proposed
    from lem.records.landing.record import Pull
    from lem.records.record import Record

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
    """The brief the merge agent reads: its path, the tip and base it is of, the seat it
    starts on, and the number of its dispatch, which the reply carries back."""

    brief: str
    tip: Sha
    base: Sha
    seat: Shown
    dispatch: int


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
    """Start the merge agent on the seat in use (a stand-in while one holds): its dispatch on
    record, and its brief published once; a dispatch repeated reads the brief it had."""
    read = proposal_of(context.record)
    dispatch, shown = merge_dispatch.dispatched(context, read[1].tip)
    path = context.folder / dispatch.brief
    if not path.is_file():
        files.publish(path, text_of(context, read))
    return Brief(
        brief=str(path),
        tip=dispatch.tip,
        base=dispatch.base,
        seat=shown,
        dispatch=dispatch.number,
    )
