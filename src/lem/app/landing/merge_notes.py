"""The lines put on the pull request after it opens."""

from typing import TYPE_CHECKING

from lem.app.landing import merge_world, stand_ins
from lem.kernel.errors import Refusal
from lem.model.landing import merge_lines, reconcile

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.landing.record import Landing
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


def body_of(body: str, record: Record, moved: str | None) -> str | None:
    """The body with the lines of the moved base and the merger's stand-ins, if any."""
    fallback = stand_ins.lines(record.task.stand_ins, "merger")
    if moved is None and not fallback:
        return None
    shown = body if moved is None else merge_lines.noted_body(body, moved) or body
    for earlier, final in fallback.items():
        replaces = None if earlier == final else earlier
        shown = merge_lines.noted_body(shown, final, replaces=replaces) or shown
    return shown


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
