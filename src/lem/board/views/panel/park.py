"""The park's confirm step of a task whose breaker waits for the owner (`board_task.park_step`
on `main`): what stopped it, what a park keeps, a box for his one line of why, and one button;
else why there is nothing to park now."""

from typing import TYPE_CHECKING

from lem.board.inputs.forms import ActForm, Field, TextBox
from lem.board.inputs.task.steps import Confirm, Park
from lem.board.views import hovers, offers
from lem.board.views.panel import confirm
from lem.board.views.panel.answered import answered
from lem.board.views.panel.stopped import stopped

if TYPE_CHECKING:
    from lem.board.inputs.task.steps import NotNow
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World

# The longest line of why a park takes.
WHY = 300


def park(
    world: World, seen: Seen, standing: Standing, asked: confirm.Asked
) -> Park | NotNow:
    """The park's step of the task of `seen`, or why there is nothing to park now."""
    task = seen.record.task
    breaker = stopped(task)
    said = refused(world, seen, standing, asked)
    if said is not None or breaker is None:
        return confirm.not_now(world, task.slug, said or nothing(standing))
    why = hovers.stop_words(breaker)
    return Park(
        confirm=park_confirm(world, seen, breaker.id, asked),
        what=f"**The build stopped:** {breaker.what}, since {why}.",
        said=(
            "A parked task keeps its worktree, its branch and its files. Nothing of it "
            "waits for you, and nobody works on it, until /lem resume "
            f"{task.slug} in any session brings it back."
        ),
    )


def nothing(standing: Standing) -> str:
    """That no breaker of the task waits for the owner, and where it stands."""
    label = standing.label.lower()
    return (
        f"Nothing to park: no breaker of this task waits for you. The task is {label}."
    )


def refused(
    world: World, seen: Seen, standing: Standing, asked: confirm.Asked
) -> str | None:
    """Why the step parks nothing: no breaker waits, his answer is on record, or the Park
    he opened was for a wait that is over."""
    task = seen.record.task
    if not offers.park_offered(task):
        return nothing(standing)
    made = answered(world, seen)
    if made is not None:
        took = made.took.removesuffix(".")
        return f"{took}: the task’s session takes it."
    question = offers.open_question(task, "breaker")
    if asked.key and question is not None and asked.key != question.id:
        return (
            f"The Park you opened was for a wait of {task.slug} that is over: its "
            "breaker waits again. Read it, then answer it on its Overview."
        )
    return None


def park_confirm(
    world: World, seen: Seen, number: int, asked: confirm.Asked
) -> Confirm:
    """The step's head, its button with its box, and the way back."""
    slug = seen.record.task.slug
    acting = world.viewer.may_act
    question = offers.open_question(seen.record.task, "breaker")
    key = question.id if question else None
    return Confirm(
        look="you",
        label="Park: confirm",
        eyebrow=f"Park · breaker {number}",
        form=park_form(world, seen, key, asked) if acting else None,
        back=confirm.back(world, slug) if acting else None,
        words=None if acting else elsewhere(slug),
        sheet=acting,
    )


def elsewhere(slug: str) -> str:
    """Where the owner parks it from a page that may not act."""
    return (
        "Park it on this board on the Mac or through the tailnet door, or type "
        f"/lem park {slug} in any session."
    )


def park_form(
    world: World, seen: Seen, key: str | None, asked: confirm.Asked
) -> ActForm:
    """The button that parks the task, with its box for one line of why."""
    slug = seen.record.task.slug
    keyed = (("key", key),) if key else ()
    named = (*confirm.under_field(world), *keyed)
    return ActForm(
        action=confirm.act_href(world, slug, "park"),
        label="Park the task",
        icon="folder",
        press="go",
        busy="Parking…",
        fields=tuple(Field(name=name, shown=shown) for name, shown in named),
        box=why_box(world, slug, asked.words),
    )


def why_box(world: World, slug: str, typed: str) -> TextBox:
    """The box of his one line of why, with what he typed in the row so far; its id stays
    through a refresh."""
    workspace = world.viewer.workspace
    return TextBox(
        name="why",
        id=f"park-why-{workspace}-{slug}",
        label="Why, in one line",
        placeholder="the owner parked it",
        longest=WHY,
        words=" ".join(typed.split())[:WHY],
    )
