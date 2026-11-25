"""The rows of an open pull request whose merge waits for the owner (`board_model.waits_of` on
`main`): the merge review that calls him first, when the merge agent's read calls him, then his
merge, which says whether the forge calls the request conflicting."""

from typing import TYPE_CHECKING

from lem.model.owner import merging
from lem.model.owner.looks import Row
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.owner.looks import Look, Rows
    from lem.records.landing.propose import MergeRead


def merge_rows(look: Look) -> Rows:
    """The merge review that calls the owner, and the merge that waits for him."""
    record = look.record
    if (
        merging.merge_wait(record, read_after_refusal=look.read_after_refusal)
        != merging.OWNER
    ):
        return ()
    merge = merge_row(look)
    read = merging.calling(record)
    if read is None:
        return (merge,)
    return (review_row(record.task.slug, read), merge)


def merge_row(look: Look) -> Row:
    """His merge of the pull request, or his check of an unresolved call."""
    task = look.record.task
    intent = (look.record.landing or Landing()).intent
    key = f"merge:{task.slug}"
    return Row(
        kind="merge",
        key=key,
        task=task.slug,
        since=task.since if intent is None else intent.at,
        conflict=look.conflict,
        read_after_refusal=look.read_after_refusal,
    )


def review_row(slug: str, read: MergeRead) -> Row:
    """The merge review that calls him, with the read's why and tip."""
    key = f"review:{slug}"
    return Row(
        kind="review",
        key=key,
        task=slug,
        since=read.at,
        why=read.why,
        tip=read.tip,
    )
