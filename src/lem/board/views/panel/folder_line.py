"""What the folder of a summarized task holds, as the folder says it now (`board_task.files_line`
on `main`): with no file beside its small record, what stayed and the rule that removed the rest,
with `state.keep_days` as the settings give it now; with files beside it, only how many."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import plural

if TYPE_CHECKING:
    from lem.board.views.world import Seen

# What each file of a task's small record is to the owner: one name for a part of more files.
RECORD = (
    (("ask.txt", "task.md"), "its request"),
    (("ticket.txt", "ticket-repo.txt", "ticket-steps.txt"), "its ticket’s files"),
    (("resumed-from.txt",), "the name of the task it was resumed from"),
)
SMALL = frozenset(name for names, _words in RECORD for name in names)


def files_line(seen: Seen, keep_days: int | None) -> str:
    """The folder's line of the summarized task of `seen`."""
    record = f"its small record: {listed(kept_words(seen))}"
    left = [name for name in seen.files if name not in SMALL]
    if left:
        verb = "is" if len(left) == 1 else "are"
        return f"{plural(len(left), 'file')} of its folder {verb} still there beside {record}."
    if keep_days:
        days = (
            f"after {plural(keep_days, 'day')} in which nothing of it happened "
            "(state.keep_days, as the settings say now)"
        )
    else:
        days = (
            "after state.keep_days days in which nothing of it happened (the settings "
            "do not read now, so the board does not say that number)"
        )
    return (
        f"What stayed of its folder is {record}. Its other files left: "
        f"Lem keeps only this record of an ended task {days}."
    )


def kept_words(seen: Seen) -> list[str]:
    """What stayed of the small record: its state, which the record holds, its request, its
    pull request when it had one, its ticket and the task it was resumed from."""
    stayed = ["its state"]
    landing = seen.record.landing
    named = [
        said for names, said in RECORD if any(name in seen.files for name in names)
    ]
    if named[:1] == ["its request"]:
        stayed.append(named.pop(0))
    if landing is not None and landing.pull is not None:
        stayed.append("its pull request")
    return [*stayed, *named]


def listed(parts: list[str]) -> str:
    """Parts of one sentence: `a`, `a and b`, `a, b and c`."""
    if len(parts) == 1:
        return parts[0]
    *firsts, last = parts
    first = ", ".join(firsts)
    return f"{first} and {last}"
