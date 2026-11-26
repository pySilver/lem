"""What `lem land next` and the merge's steps say comes next: the due step's whole command, each
input the caller gives as a placeholder that `why` names (and no other), or the wait and why;
after the merge agent's brief, the form that writes its reply down, with the brief's own tip and
base and the number of the dispatch that started the agent (`main:land.cmd_merge_review`'s
`next`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.kernel.envelope import Next

if TYPE_CHECKING:
    from lem.model.landing.world import Due

RESTS = frozenset(("wait", "done", "none"))
# Each step whose command takes an input of the caller's: its words, and what each is.
INPUTS = MappingProxyType(
    {
        "propose": (
            " --title TITLE --notes FILE",
            "TITLE is the report's commit subject, FILE the pull request's notes",
        ),
        "merge": (
            " --by merger --message SUBJECT",
            "SUBJECT is the report's commit subject",
        ),
    }
)
# A merge that keeps the branch's commits takes no subject.
KEEPS = (" --by merger", None)
NONE: tuple[str, str | None] = ("", None)


def following(slug: str, due: Due, *, squash: bool = True) -> Next:
    """The due step's command, or the wait and why; the owner's merge is his to give."""
    if due.step == "done":
        return Next(act="done", why=due.why)
    if due.step in RESTS or due.by == "owner":
        return Next(act="wait", why=due.why)
    keeps = due.step == "merge" and not squash
    words, said = KEEPS if keeps else INPUTS.get(due.step, NONE)
    why = f"{due.why}; {said}" if said else due.why
    command = f"lem land {due.step} {slug}{words}"
    return Next(act="run", command=command, why=why)


def answered(slug: str, brief: str, read: tuple[str, str, int]) -> Next:
    """After the merge agent's brief `brief` of `read` (its tip, base and dispatch): the
    command that writes its reply down, and the one for an agent that ended with no answer."""
    tip, base, dispatch = read
    pinned = f"--tip {tip} --base {base} --dispatch {dispatch}"
    return Next(
        act="spawn",
        job="merger",
        command=f"lem land merge-review {slug} --file FILE {pinned}",
        paths=(brief,),
        why=(
            f"a fresh merge agent reads {brief}, and FILE is its reply, the verdict on its "
            f"first line; an agent that ends with no answer is lem land merge-review {slug} "
            f"--no-answer {pinned}"
        ),
    )
