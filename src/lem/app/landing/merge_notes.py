"""The lines put on the pull request after it opens."""

from typing import TYPE_CHECKING

from lem.app.landing import merge_world, stand_ins
from lem.kernel.errors import Refusal
from lem.model.landing import merge_lines, reconcile
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.record import Record


def moved_line(context: Context, landing: Landing) -> str | None:
    """The line of a merge on a moved base, if it needs one."""
    merged = landing.merged
    if merged is None or merged.text_updated:
        return None
    if merged.uncovered is not None:
        return merged.uncovered
    tree = context.ports.git.tree(context.workspace.checkout, merged.parent)
    trees = reconcile.Trees(checks=merge_world.checks_tree(context), parent=tree)
    return reconcile.line_of(landing, merged, trees, context.world.rules.base)[0]


def wanted(record: Record, moved: str | None) -> tuple[str, ...]:
    """The lines the pull request's text must hold: the moved base's, and the final line of
    each stand-in of the merge agent."""
    fallback = stand_ins.finals(record.task.stand_ins, "merger")
    return fallback if moved is None else (moved, *fallback)


def wanted_of(context: Context, record: Record) -> tuple[str, ...]:
    """The lines the edit of the pull request's text puts on it now."""
    landing = record.landing or Landing()
    return wanted(record, moved_line(context, landing))


def body_of(body: str, record: Record, moved: str | None) -> str | None:
    """The body with the lines of the moved base and the merger's stand-ins, if any."""
    fallback = stand_ins.lines(record.task.stand_ins, "merger")
    if moved is None and not fallback:
        return None
    shown = body if moved is None else merge_lines.noted_body(body, moved) or body
    return with_stand_ins(shown, fallback)


def with_stand_ins(body: str, fallback: tuple[stand_ins.Line, ...]) -> str:
    """The body with each stand-in's final line, in place of its earlier one; an earlier line
    that a later stand-in has as its own stays once the final line is in."""
    finals = {final for _, final in fallback}
    for earlier, final in fallback:
        if earlier in finals and final in body.splitlines():
            continue
        replaces = None if earlier == final else earlier
        body = merge_lines.noted_body(body, final, replaces=replaces) or body
    return body


def edit_refusal(record: Record, said: str) -> Refusal:
    """The forge's edit failed, leaving the same step due."""
    slug = record.task.slug
    if record.landing is not None and record.landing.merged is not None:
        return Refusal(
            "text",
            f"GitHub merged the pull request and its newer text waits ({said})",
            f"lem land merged {slug} tries the edit again",
        )
    return Refusal(
        "text",
        f"the merge agent's read waits for the pull request's newer text ({said})",
        f"give lem land merge-review {slug} the same reply again",
    )
