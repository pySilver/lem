"""The head and the button of the merge's confirm step (`board_task.merge_step` on `main`): its
label and eyebrow, the form that merges the commit it shows, where the page may act, and the
way back; else where the owner merges it."""

from typing import TYPE_CHECKING

from lem.board.inputs.forms import ActForm, Field
from lem.board.inputs.task.steps import Confirm
from lem.board.views.panel import confirm
from lem.board.views.panel.common import pull_of

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World


def confirm_of(world: World, seen: Seen, *, green: bool) -> Confirm:
    """The step's head, its button, and the way back."""
    slug = seen.record.task.slug
    tip = tip_of(seen)
    acting = world.viewer.may_act and bool(tip)
    pull = pull_of(seen.record)
    named = f"Merge #{pull.number}" if pull else "Merge"
    return Confirm(
        look="done" if green else "you",
        label="Merge: confirm",
        eyebrow=f"{named} · confirm",
        form=merge_form(world, seen, tip) if acting else None,
        back=confirm.back(world, slug) if acting else None,
        words=None if acting else elsewhere(slug),
        sheet=acting,
    )


def elsewhere(slug: str) -> str:
    """Where the owner merges it from a page that may not act."""
    return (
        "Merge it on this board on the Mac or through the tailnet door, or type "
        f"/lem land {slug} in the task’s session."
    )


def tip_of(seen: Seen) -> str:
    """The commit Lem proposed last, or "" with no proposal."""
    landing = seen.record.landing
    proposed = landing.proposed if landing else None
    return proposed.tip if proposed else ""


def merge_form(world: World, seen: Seen, tip: str) -> ActForm:
    """The button that merges the commit the step shows."""
    record = seen.record
    named = (("confirm", "yes"), ("tip", tip), *confirm.under_field(world))
    return ActForm(
        action=confirm.act_href(world, record.task.slug, "merge"),
        label="Approve",
        icon="code-pull-request",
        press="risk",
        busy="Approving…",
        fields=tuple(Field(name=name, shown=shown) for name, shown in named),
    )
