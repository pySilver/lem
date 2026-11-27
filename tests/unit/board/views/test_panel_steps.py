"""The steps of the owner's acts that ask first (`main`'s `board_task.park_step`, `drop_step`,
`card_step`, `merge_step` and `not_now`): each step, and the one that says why there is nothing
to do now."""

import dataclasses
from typing import TYPE_CHECKING

import msgspec

from fixtures.board.moments import ago
from fixtures.board.receipt import SLUG
from lem.board.inputs.layout import Viewer
from lem.board.views import owed
from lem.board.views.panel.confirm import Asked
from lem.board.views.panel.opened import Opened
from lem.board.views.panel.panel import panel
from lem.records.questions import Answer
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import World

GIFT = "gift-note-in-export"
QUESTION = "breaker:gift-note-in-export:1:20261125T154000Z"
ROUNDING = "refund-rounding"
CARD = "4F9A1C2E-7B3D-4E8F-A1B2-C3D4E5F60718"


def looking(afternoon: World) -> World:
    """The afternoon on a page that may not act (a phone with no door)."""
    viewer = Viewer(host="studio", workspace="shop", base=afternoon.viewer.base)
    return dataclasses.replace(afternoon, viewer=viewer)


def answering(afternoon: World, slug: str, source: str = "board") -> World:
    """The afternoon with the owner's answer to the first question of task `slug`."""
    seen = owed.seen(afternoon, slug)
    task = seen.record.task
    picked = Answer(
        option="b",
        label="B",
        source="board" if source == "board" else "session",
        device="phone",
        at=ago(5),
    )
    first = msgspec.structs.replace(task.questions[0], answer=picked)
    questions = (first, *task.questions[1:])
    record = msgspec.structs.replace(
        seen.record, task=msgspec.structs.replace(task, questions=questions)
    )
    changed = msgspec.structs.replace(seen, record=record)
    tasks = tuple(changed if one is seen else one for one in afternoon.tasks)
    return dataclasses.replace(afternoon, tasks=tasks)


def test_a_park_takes_one_line_of_why_and_the_breakers_question(tmp_path: Path) -> None:
    opened = Opened(asked=Asked(key=QUESTION, words="  wait   for the export "))
    found = panel(world(tmp_path), GIFT, "park", opened=opened)
    assert found.park is not None
    assert found.park.what.startswith(
        "**The build stopped:** The gift note has no place"
    )
    form = found.park.confirm.form
    assert form is not None
    assert form.action.endswith(f"/tasks/{GIFT}/answer")
    assert [(one.name, one.shown) for one in form.fields] == [
        ("key", QUESTION),
        ("option", "park"),
        ("confirm", "yes"),
    ]
    assert form.box is not None
    assert form.box.name == "words"
    assert form.box.words == "wait for the export"
    assert form.box.id == "park-why-shop-gift-note-in-export"
    assert found.head is not None
    assert found.head.acts is None
    assert not any(tab.current for tab in found.tabs)


def test_a_park_opened_for_a_wait_that_is_over_says_so(tmp_path: Path) -> None:
    opened = Opened(asked=Asked(key="breaker:gift-note-in-export:1:20261124T100000Z"))
    found = panel(world(tmp_path), GIFT, "park", opened=opened)
    assert found.not_now is not None
    assert found.not_now.said.startswith(
        f"The Park you opened was for a wait of {GIFT} that is over"
    )
    assert found.not_now.back.label == "Back to the task"


def test_a_page_that_may_not_act_says_where_to_park_merge_and_drop(
    tmp_path: Path,
) -> None:
    afternoon = looking(world(tmp_path))
    park = panel(afternoon, GIFT, "park").park
    assert park is not None
    assert (park.confirm.form, park.confirm.sheet) == (None, False)
    assert park.confirm.words == (
        "Park it on this board on the Mac or through the tailnet door, or type "
        f"/lem park {GIFT} in any session."
    )
    merge = panel(afternoon, SLUG, "merge").merge
    assert merge is not None
    assert merge.confirm.form is None
    assert merge.confirm.words is not None
    assert f"/lem land {SLUG}" in merge.confirm.words


def test_a_drop_posts_the_owners_drop_as_the_answer_to_the_breaker(
    tmp_path: Path,
) -> None:
    found = panel(world(tmp_path), GIFT, "drop", opened=Opened(asked=Asked(words="no")))
    assert found.drop is not None
    assert found.drop.confirm.eyebrow == f"Drop {GIFT}?"
    form = found.drop.confirm.form
    assert form is not None
    assert form.action.endswith(f"/tasks/{GIFT}/answer")
    assert [(one.name, one.shown) for one in form.fields] == [
        ("key", QUESTION),
        ("option", "drop"),
        ("confirm", "yes"),
    ]
    assert form.box is not None
    assert form.box.words == "no"


def test_nothing_waits_to_be_dropped_on_an_open_pull_request(tmp_path: Path) -> None:
    found = panel(world(tmp_path), SLUG, "drop")
    assert found.not_now is not None
    assert found.not_now.said == (
        "Nothing to drop from the board: no plan or breaker of this task waits for you. "
        f"The task is waits for the merge; /lem drop {SLUG} in any session ends it."
    )


def test_an_answer_on_record_ends_the_park_and_the_drop(tmp_path: Path) -> None:
    afternoon = answering(world(tmp_path), GIFT)
    for shows in ("park", "drop"):
        found = panel(afternoon, GIFT, shows)
        assert found.not_now is not None
        assert found.not_now.said == (
            "You picked B for breaker 1 at 15:55, from the phone: the task’s session "
            "takes it."
        )


def test_a_card_of_the_tasks_session_opens_its_own_page_in_a_frame(
    tmp_path: Path,
) -> None:
    found = panel(world(tmp_path), ROUNDING, "card", opened=Opened(page=CARD))
    assert found.card is not None
    assert found.card.frame == f"/studio/shop/tasks/{ROUNDING}/cards/{CARD}/"
    assert found.card.title == "Round each line of a refund, or only its total?"
    assert found.card.keep == f"card-{CARD}"
    assert found.card.confirm.sheet


def test_a_card_that_no_longer_waits_says_what_took_effect(tmp_path: Path) -> None:
    afternoon = answering(world(tmp_path), ROUNDING)
    found = panel(afternoon, ROUNDING, "card", opened=Opened(page=CARD))
    assert found.not_now is not None
    assert found.not_now.id == "card-step"
    assert found.not_now.said == (
        "B was taken on the board at 15:55, from the phone. This card no longer waits "
        "for you."
    )
    gone = panel(afternoon, ROUNDING, "card", opened=Opened(page="no-such-card"))
    assert gone.not_now is not None
    assert gone.not_now.said.startswith("This card no longer waits for you:")


def test_nothing_to_merge_while_the_task_is_not_open(tmp_path: Path) -> None:
    found = panel(world(tmp_path), GIFT, "merge")
    assert found.not_now is not None
    assert found.not_now.said == "Nothing to merge now: the task is waits for you."
