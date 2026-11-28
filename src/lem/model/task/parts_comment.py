"""The parts comment on a feature's ticket: one line with a box for each part, and Lem's last
line `lem: NAME parts` (`docs/plans/2026-11-27-a-feature-in-parts.md`, "A part's ticket step").

Its text is a function of the records alone: every part of the feature (`feature_parts.py`),
a box set for each part that landed. A part that ended
without landing keeps its empty box and says how it ended. So the same records give the same
text, and a tick run again, or after a tick a stop lost, sets no box twice.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.records.task import Task

CODE = "not-a-feature"
LANDED = "landed"
# The ends of a part that set no box, said after its line.
UNLANDED = frozenset(("dropped", "answered"))


def marker(feature: str) -> str:
    """The last line that says the comment is Lem's parts comment of `feature`."""
    return f"lem: {feature} parts"


def words_of(ask: str) -> str:
    """What a part does, as its line says it: the first line of its ask with its spaces
    made one."""
    lines = (line.strip() for line in ask.splitlines())
    first = next((line for line in lines if line), "")
    return " ".join(first.split())


def line_of(part: Task) -> str:
    """The part's line: its box, set when it landed, its slug and what it does, and how it
    ended when it ended without landing."""
    box = "x" if part.status == LANDED else " "
    ended = f" ({part.status})" if part.status in UNLANDED else ""
    return f"- [{box}] {part.slug}: {words_of(part.ask)}{ended}"


def text(feature: Task, parts: tuple[Task, ...]) -> str:
    """The whole comment: a line for each part, an empty line, and the last line."""
    lines = "\n".join(line_of(part) for part in parts)
    return f"{lines}\n\n{marker(feature.slug)}\n"


def landed(parts: tuple[Task, ...]) -> int:
    """How many of `parts` landed."""
    return sum(part.status == LANDED for part in parts)


def refusal(task: Task, parts: tuple[Task, ...]) -> Refusal | None:
    """Why the task takes no parts comment, or None: it is a part, whose feature's ticket
    holds the comment, or no task names it as its feature."""
    if task.part_of is not None:
        return Refusal(
            CODE,
            f"{task.slug} is a part of {task.part_of}, and only the feature holds a ticket",
            f"lem issue tick {task.part_of}",
        )
    if not parts:
        return Refusal(
            CODE,
            f"{task.slug} is no feature: no task names it with --part-of, so its issue "
            "takes no parts comment",
            f"lem issue land {task.slug} at its landing is all its issue gets",
        )
    return None
