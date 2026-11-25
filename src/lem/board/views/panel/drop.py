"""The drop's confirm step from the board (`board_task.drop_step` on `main`): what waits, what a
drop ends, the owner's note (what he typed in the row), and Confirm, which posts his Drop as the
answer to the row's question; else why there is nothing to drop from the board."""

from typing import TYPE_CHECKING

from lem.board.inputs.forms import ActForm, Field, TextBox
from lem.board.inputs.task.steps import Confirm, Drop
from lem.board.views import hovers, offers
from lem.board.views.panel import confirm
from lem.board.views.panel.answered import answered
from lem.board.views.panel.stopped import stopped

if TYPE_CHECKING:
    from lem.board.inputs.task.steps import NotNow
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.records.questions import Question

# The longest note a drop takes.
NOTE = 2000


def drop(
    world: World, seen: Seen, standing: Standing, asked: confirm.Asked
) -> Drop | NotNow:
    """The drop's step of the task of `seen`, or why there is nothing to drop now."""
    slug = seen.record.task.slug
    question = asking(seen)
    said = refused(world, seen, standing, asked, question)
    if said is not None or question is None:
        return confirm.not_now(world, slug, said or "")
    acting = world.viewer.may_act
    return Drop(
        confirm=Confirm(
            look="you",
            label="Drop: confirm",
            eyebrow=f"Drop {slug}?",
            form=drop_form(world, slug, question.id, asked) if acting else None,
            back=confirm.back(world, slug) if acting else None,
            words=None if acting else elsewhere(slug),
            sheet=acting,
        ),
        what=what_of(seen, question),
        said=(
            "A drop ends the task: its session gives a ticket what it is still owed, then "
            "removes the worktree, and the branch keeps its commits. The board records "
            "your Drop and wakes the task’s session, which drops it as /lem drop "
            f"{slug} does."
        ),
    )


def asking(seen: Seen) -> Question | None:
    """The open question of a breaker or a plan that a Drop answers, or None."""
    task = seen.record.task
    found = offers.open_question(task, "breaker") or offers.open_question(task, "plan")
    return found if found is not None and "drop" in found.options else None


def refused(
    world: World,
    seen: Seen,
    standing: Standing,
    asked: confirm.Asked,
    question: Question | None,
) -> str | None:
    """Why the step drops nothing: his answer is on record, nothing asks for a drop, or the
    Drop he opened was for a wait that is over."""
    slug = seen.record.task.slug
    made = answered(world, seen)
    if made is not None:
        took = made.took.removesuffix(".")
        return f"{took}: the task’s session takes it."
    if question is None:
        label = standing.label.lower()
        return (
            "Nothing to drop from the board: no plan or breaker of this task waits for "
            f"you. The task is {label}; /lem drop {slug} in any session ends it."
        )
    if asked.key and asked.key != question.id:
        return (
            f"The Drop you opened was for a wait of {slug} that is over. Read what waits "
            "now, then answer it on its Overview."
        )
    return None


def what_of(seen: Seen, question: Question) -> str:
    """What waits: the breaker that stopped the build, or the plan."""
    breaker = stopped(seen.record.task)
    if question.topic == "breaker" and breaker is not None:
        why = hovers.stop_words(breaker)
        return f"**The build stopped:** {breaker.what}, since {why}."
    return "**The plan waits for your read:** a drop ends the task before its build."


def elsewhere(slug: str) -> str:
    """Where the owner drops it from a page that may not act."""
    return (
        "Drop it on this board on the Mac or through the tailnet door, or type "
        f"/lem drop {slug} in any session."
    )


def drop_form(world: World, slug: str, key: str, asked: confirm.Asked) -> ActForm:
    """Confirm, which posts his Drop as the answer to the question `key`, with his note."""
    named = (("key", key), ("option", "drop"), ("confirm", "yes"))
    workspace = world.viewer.workspace
    box = TextBox(
        name="words",
        id=f"drop-words-{workspace}-{slug}",
        label="Your note, if you like",
        placeholder="why, in your words",
        rows=2,
        longest=NOTE,
        words=asked.words[:NOTE],
    )
    return ActForm(
        action=confirm.act_href(world, slug, "answer"),
        label="Confirm",
        icon="xmark",
        press="risk",
        busy="Dropping…",
        fields=tuple(
            Field(name=name, shown=shown)
            for name, shown in (*named, *confirm.under_field(world))
        ),
        box=box,
    )
