"""The links of a breaker's row: its document and its handoff on Artifacts, and the owner's
decision that helped it."""

from typing import TYPE_CHECKING

from lem.board.inputs.parts import Link
from lem.board.views.artifacts.addresses import file_link

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.records.decisions import Breaker


def files_of(world: World, seen: Seen, breaker: Breaker) -> tuple[Link, ...]:
    """The breaker's document and its handoff, where the task's folder has them."""
    slug = seen.record.task.slug
    named = ((breaker.document, "the document"), (breaker.handoff, "the handoff"))
    return tuple(
        file_link(world, slug, path, label, f"Open {path} on Artifacts")
        for path, label in named
        if path in seen.files
    )


def help_link(helped: int) -> Link:
    """The owner's decision that helped the breaker, on the same tab."""
    return Link(
        href=f"#dec-{helped}",
        label=f"decision {helped}",
        title=f"Decision {helped}, your help",
        anchor=f"dec-{helped}",
    )
