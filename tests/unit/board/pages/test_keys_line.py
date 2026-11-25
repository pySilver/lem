"""Render the complete keyboard guide for Tasks and Waits."""

from msgspec.structs import replace

from fixtures.board import columns, frame, waiting
from lem.board.inputs.layout import KeyGroup, Keys
from lem.board.inputs.page import Page
from lem.board.pages.render import section
from unit.board.pages.markup import Parsed


def test_the_key_lines_put_a_middle_dot_between_actions() -> None:
    tasks = Page(frame=frame.FRAME, tasks=columns.TASKS)
    waits = Page(
        frame=replace(
            frame.FRAME,
            viewer=replace(frame.FRAME.viewer, view="waits"),
            keys=Keys(
                id="waits-keys",
                groups=(
                    KeyGroup(keys=("J", "K", "↑", "↓"), word="move"),
                    KeyGroup(keys=("Enter",), word="go or open"),
                ),
            ),
        ),
        waits=waiting.WAITS,
    )
    for page, identity, words in (
        (
            tasks,
            "kanban-keys",
            "J K ↑ ↓ move · H L ← → column · Enter open · Esc close",
        ),
        (waits, "waits-keys", "J K ↑ ↓ move · Enter go or open"),
    ):
        found = Parsed(section("page.html", page)).root.one(id_=identity)
        assert found.words() == words
