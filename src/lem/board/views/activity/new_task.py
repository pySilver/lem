"""The page of a new task, `/HOST/WORKSPACE/new` (`board_pages.new_page` on `main`): the form
that starts a task from the owner's words, where the page may act, and the way back to the
tasks. A page that may not act has no form, and its template says how to start a task in a
session instead.

The box keeps its id across a refresh (`nt-words-WORKSPACE`), so that the words the owner types
on the phone stay while the page refreshes.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.activity import NewTask
from lem.board.inputs.forms import ActForm, TextBox
from lem.board.inputs.parts import Link

if TYPE_CHECKING:
    from lem.board.views.world import World

# The most characters the box takes, as `main`'s form took them.
LONGEST = 2000
ROWS = 5


def new_task(world: World) -> NewTask:
    """The page of a new task in the world's workspace."""
    viewer = world.viewer
    cancel = Link(href=f"{viewer.base}/", label="Cancel")
    if not viewer.may_act:
        return NewTask(cancel=cancel)
    box = TextBox(
        name="words",
        id=f"nt-words-{viewer.workspace}",
        label="What should Lem do?",
        placeholder="Add the gift note to the CSV export",
        rows=ROWS,
        longest=LONGEST,
        required=True,
    )
    form = ActForm(
        action=f"{viewer.base}/start",
        label="Start the task",
        icon="play",
        press="go",
        busy="Starting…",
        box=box,
    )
    return NewTask(form=form, cancel=cancel)
