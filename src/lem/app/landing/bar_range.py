"""The bar applies to the diff the checks read, including a tip that only adds filed items."""

from typing import TYPE_CHECKING

from lem.model.landing.bar import edited_kind
from lem.records.landing.checks import Edited

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.landing.checks import Checked

type Span = tuple[str, str]


def saved(context: Context, span: Span) -> Checked | None:
    """The check run's bar when its diff covers this range."""
    landing = context.record.landing
    checked = landing.checked if landing else None
    if checked is None or checked.bar_base != span[0]:
        return None
    tip = span[1]
    if checked.tip == tip:
        return checked
    if tip == context.world.tip and context.world.items_from(checked.tip):
        return checked
    return None


def for_review(
    context: Context, span: Span, paths: tuple[str, ...]
) -> tuple[Edited, ...]:
    """The tests to read first: the saved bar or the existing files the review range edits."""
    held = saved(context, span)
    if held is not None:
        return held.edited
    git, where = context.ports.git, context.worktree
    return tuple(
        Edited(path=path, kind=kind)
        for path in sorted(paths)
        if (kind := edited_kind(path)) is not None
        and all(git.show(where, rev, path) is not None for rev in span)
    )
