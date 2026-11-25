"""What `lem land next` and the merge's steps say comes next: the due step's whole command, each
input the caller gives as a placeholder that `why` names (and no other), or the wait and why;
after the merge agent's brief, the form that writes its reply down, with the brief's own tip and
base (`main:land.cmd_merge_review`'s `next`)."""

from typing import TYPE_CHECKING

from lem.kernel.envelope import Next

if TYPE_CHECKING:
    from lem.model.landing.world import Due

RESTS = frozenset(("wait", "done", "none"))
# Each step whose command takes an input of the caller's: its words, and what each is.
INPUTS = (
    (
        "propose",
        " --title TITLE --notes FILE",
        "TITLE is the report's commit subject, FILE the pull request's notes",
    ),
    (
        "merge",
        " --by merger --message SUBJECT",
        "SUBJECT is the report's commit subject",
    ),
)


def following(slug: str, due: Due, *, squash: bool = True) -> Next:
    """The due step's command, or the wait and why; the owner's merge is his to give. A merge
    that keeps the branch's commits takes no subject."""
    if due.step == "done":
        return Next(act="done", why=due.why)
    if due.step in RESTS or due.by == "owner":
        return Next(act="wait", why=due.why)
    words, said = next(
        ((words, said) for step, words, said in INPUTS if step == due.step), ("", None)
    )
    if due.step == "merge" and not squash:
        words, said = " --by merger", None
    command = f"lem land {due.step} {slug}{words}"
    why = f"{due.why}; {said}" if said else due.why
    return Next(act="run", command=command, why=why)


def answered(slug: str, brief: str, read: tuple[str, str]) -> Next:
    """After the merge agent's brief `brief` of `read` (its tip and base): the command that
    writes its reply down, and the one for an agent that ended with no answer."""
    tip, base = read
    pinned = f"--tip {tip} --base {base}"
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
