"""The merge agent's review on a task's Overview (`board_task.merge_review_card` on `main`): the
first card while the task is open and `merge-review.md` is in its folder, under its verdict."""

from typing import TYPE_CHECKING

import msgspec

from lem.board.inputs import clock
from lem.board.inputs.task.cards import Review
from lem.board.views.artifacts import addresses, documents
from lem.board.views.panel.common import stamp
from lem.model.landing import mergeread
from lem.model.owner import merging

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document, Link, When
    from lem.board.views.world import Seen, World
    from lem.records.landing.propose import MergeRead

NAME = "merge-review.md"


def review(world: World, seen: Seen) -> Review | None:
    """The merge review of the task of `seen`, or None."""
    record = seen.record
    text = seen.text(NAME)
    if record.task.status != "open" or text is None or record.landing is None:
        return None
    again = mergeread.another_round(record.landing)
    read = again or mergeread.latest(record.landing, seen.basis.tree)
    calls = read is None or merging.calling(seen.merge_look()) is not None
    calls = calls and again is None
    return Review(
        calls=calls,
        head=heading(calls=calls, again=again is not None),
        why=read.why if read else None,
        at=written(world, read),
        text=reviewed(world, seen, text),
        artifact=artifact(world, record.task.slug, NAME),
    )


def heading(*, calls: bool, again: bool) -> str:
    """What the review asks for."""
    if again:
        return "The merge review · it needs another round"
    return (
        "The merge review · it calls you" if calls else "The merge review · it merges"
    )


def reviewed(world: World, seen: Seen, text: str) -> Document:
    """The review's text, with the task's pictures."""
    slug = seen.record.task.slug
    media = addresses.media_href(world, slug)
    forge = documents.forge_of(seen.record)
    return documents.document(f"merge-review-{slug}", text, forge, media=media)


def written(world: World, read: MergeRead | None) -> When | None:
    """How long ago the merge agent wrote it, with its clock time as the hover."""
    if read is None:
        return None
    return clock.since(read.at, world.clock.now, stamp(world, read.at))


def artifact(world: World, slug: str, name: str) -> Link:
    """The link that opens the file `name` on the tab Artifacts."""
    title = f"Open {name} on Artifacts"
    link = addresses.file_link(world, slug, name, name, title)
    return msgspec.structs.replace(link, icon="file-lines")
