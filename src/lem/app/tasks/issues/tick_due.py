"""What the comments of a feature's issue ask of a tick (`tick.py`): Lem's parts comment is the
first comment whose last line is `lem: NAME parts`. With none, the tick posts it; with one whose
text differs, it edits that comment; with one of the same text, it writes nothing.
"""

from typing import TYPE_CHECKING, Literal

from lem.app.tasks.issues.comment import last_line
from lem.kernel.errors import Fault
from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.adapters.tracker_gh_facts import Comment
    from lem.app.tasks.issues.run import Run

# What each write did, as `did` and the line for the owner say it.
POSTED = "posted the parts comment"
EDITED = "edited the parts comment"


class Due(Frozen, frozen=True, kw_only=True):
    """What to write: post the comment, edit the one of the id `comment`, or nothing."""

    act: Literal["post", "edit", "none"]
    comment: int | None = None


def same_text(found: str, wanted: str) -> bool:
    """Whether a comment's text is the wanted one, apart from line ends and the space at its
    two ends, which GitHub may change."""
    return found.replace("\r\n", "\n").strip() == wanted.strip()


def mine(found: tuple[Comment, ...], marker: str) -> Comment | None:
    """The first comment whose last line is `marker`, or None."""
    marked = (one for one in found if last_line(one.text) == marker)
    return next(marked, None)


def due(found: tuple[Comment, ...], body: str, marker: str) -> Due:
    """What the comments `found` ask for, so that the parts comment says `body`."""
    comment = mine(found, marker)
    if comment is None:
        return Due(act="post")
    if same_text(comment.text, body):
        return Due(act="none")
    if comment.id is None:
        raise Fault(f"the tracker gave the comment {marker!r} no id to edit it by")
    return Due(act="edit", comment=comment.id)


def written(run: Run, body: str, marker: str) -> None:
    """Post the parts comment, or edit it when its text differs; nothing when it is the
    same."""
    found = due(run.issues.comments(run.repo, run.number), body, marker)
    if found.act == "post":
        run.issues.comment(run.repo, run.number, body)
        run.did.append(POSTED)
    elif found.act == "edit" and found.comment is not None:
        run.issues.edit_comment(run.repo, found.comment, body)
        run.did.append(EDITED)
