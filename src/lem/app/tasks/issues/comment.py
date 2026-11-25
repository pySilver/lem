"""The one comment of a task's end on its issue. Its last line is Lem's own, `lem: SLUG landed`
(`dropped`, `answered`), and before it posts, the issue's comments are read for that line: a
session cut off after the post posts no second one, and only writes the step down."""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from lem.app.tasks.issues.run import Run
    from lem.records.tickets import TicketAct

type EndStep = Literal["land", "drop", "answer"]

# The step written down for each end's comment, and the last word of its last line.
COMMENTED: MappingProxyType[str, TicketAct] = MappingProxyType(
    {"land": "commented", "drop": "dropped", "answer": "answered"}
)
LAST_WORD = MappingProxyType(
    {"land": "landed", "drop": "dropped", "answer": "answered"}
)


def last_line(text: str) -> str:
    """The last line of `text` that is not empty, stripped."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def commented(run: Run, step: EndStep, words: str) -> None:
    """Post the comment of `step` with `words`, unless it is written down or on the issue
    already; then write it down."""
    act = COMMENTED[step]
    if act in run.acts:
        return
    slug, word = run.record.task.slug, LAST_WORD[step]
    marker = f"lem: {slug} {word}"
    found = run.issues.comments(run.repo, run.number)
    if not any(last_line(comment.text) == marker for comment in found):
        run.issues.comment(run.repo, run.number, f"{words}\n\n{marker}\n")
        run.did.append("posted the comment")
    run.write(act)
