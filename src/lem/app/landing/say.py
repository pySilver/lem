"""What a landing step says after it: the envelope's `next` for the due step, and the refusal
of a step that is not due."""

from typing import TYPE_CHECKING

from lem.kernel.envelope import Next
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.landing.world import Due

RESTS = frozenset(("wait", "done", "none"))
INPUTS = (
    "TITLE and SUBJECT are the report's commit subject, FILE the pull request's notes"
)


def words_of(due: Due) -> str:
    """The words a due step's command takes past its slug, each input the caller gives as a
    placeholder that `INPUTS` names."""
    if due.step == "propose":
        return " --title TITLE --notes FILE"
    if due.step == "merge":
        return f" --by {due.by} --message SUBJECT"
    return ""


def following(slug: str, due: Due) -> Next:
    """The due step's command, or the wait and why; the owner's merge is his to give. A
    command that takes an input of the caller's names it as a placeholder, and `why` says
    what each is."""
    if due.step == "done":
        return Next(act="done", why=due.why)
    if due.step in RESTS or due.by == "owner":
        return Next(act="wait", why=due.why)
    words = words_of(due)
    command = f"lem land {due.step} {slug}{words}"
    why = f"{due.why}; {INPUTS}" if words else due.why
    return Next(act="run", command=command, why=why)


def not_due(slug: str, verb: str, due: Due) -> Refusal:
    """The refusal of the step `verb`, which is not the due one."""
    if due.step in RESTS:
        fix = f"no step is due: {due.why}"
    else:
        fix = f"lem land {due.step} {slug} is the step that is due"
    return Refusal("not-due", f"lem land {verb} {slug} is not due: {due.why}", fix)
