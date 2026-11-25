"""The owner's word over a merge call whose outcome nobody knows (`landing.md` C, "In `open`":
a new call only on his explicit word after his check of GitHub; E, "Stop or lost reply around
the merge call"), and his word while the merge agent's read is due.

His word over a kept intent names the moment of that call (`--checked`), which he reads in the
refusal that asked him to check GitHub: the command that wrote the intent cannot carry it, so a
replay of that command is refused, and a new call writes a new intent with a new moment. The
word is noted with what the forge showed when it came.
"""

from typing import TYPE_CHECKING

from lem.app.landing import changes
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.landing import merge_standing
from lem.model.landing.merge_evidence import new_call_refusal
from lem.records.journal.task import OwnerAct

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing import world
    from lem.model.landing.merge_asked import Asked
    from lem.records.landing.merge import MergeIntent
    from lem.records.record import Record


def explicit(asked: Asked, intent: MergeIntent, found: object) -> bool:
    """Whether a new call goes over the intent on record: only while GitHub shows the pull
    request open with nothing of the call (`found`, the reconcile's refusal), on the owner's
    own word for its tip that names the moment of that call."""
    if not isinstance(found, Refusal) or found.code != "intent":
        return False
    named = asked.checked == clock.compact(intent.at)
    return named and merge_standing.word(asked) and asked.tip == intent.tip


def unchecked(asked: Asked) -> None:
    """Refuse `--checked` where no merge call of an unknown outcome is on record."""
    if asked.checked is None:
        return
    raise Refusal(
        "checked",
        f"--checked names a merge call of {asked.checked}, and none is on record",
        "the owner merges with the words lem land next names",
    )


def heard(context: Context, record: Record, intent: MergeIntent) -> Record:
    """Note the owner's word over `intent`, and give the record after it."""
    stopped = new_call_refusal(record)
    if stopped is not None:
        raise stopped
    pull = context.world.pull
    shown = f"{pull.state} at {pull.head}" if pull else "no pull request"
    stamp = clock.compact(intent.at)
    entry = OwnerAct(
        at=context.world.now,
        act="merge again after his check of GitHub",
        question=f"the merge call of {stamp}",
        option=shown,
    )
    return context.write(record, lambda before: changes.noted(before, entry))


def admits(asked: Asked, context: Context, due: world.Due) -> bool:
    """Whether the owner's own word for the tip he saw is taken while the merge agent's read
    is due: as on `main`, his word needs no read; on a moved base it is refused for the base
    under the lock, and stands until a safe read."""
    return (
        due.step == "merge-review"
        and merge_standing.word(asked)
        and asked.tip is not None
    )
