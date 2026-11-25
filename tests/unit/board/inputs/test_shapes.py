"""Every input of the board is a typed, frozen struct a template only prints: it takes its fields
by keyword, refuses a key it does not know and a fact it lacks, holds no mapping and no value of
any type, and the whole page has one JSON schema."""

import importlib
import inspect
import pkgutil
import types
from datetime import UTC, datetime
from typing import Any, get_args, get_origin

import msgspec
import pytest

import lem.board.inputs
from fixtures.board import columns, frame, panel, waiting
from fixtures.board.held import STOCK
from lem.board.inputs.layout import Viewer
from lem.board.inputs.page import Page
from lem.board.inputs.parts import Chip, Input, Link, Note, When
from lem.board.inputs.switcher import Space
from lem.board.inputs.task.panel import Missing, Panel
from lem.board.inputs.task.steps import NotNow
from lem.board.inputs.tasks import Column, Older

# The walking skeleton's kanban, which `board-views` and `board-pages` leave for `tasks.py`.
SKELETON = "lem.board.inputs.kanban"


def defined() -> list[type[msgspec.Struct]]:
    """Every struct the inputs' modules define, but the skeleton's."""
    found: list[type[msgspec.Struct]] = []
    for each in pkgutil.walk_packages(lem.board.inputs.__path__, "lem.board.inputs."):
        if each.name == SKELETON:
            continue
        module = importlib.import_module(each.name)
        found.extend(
            kept
            for kept in vars(module).values()
            if isinstance(kept, type)
            and issubclass(kept, msgspec.Struct)
            and kept.__module__ == module.__name__
        )
    return found


STRUCTS = [each for each in defined() if issubclass(each, Input)]


def test_every_struct_of_the_inputs_is_an_input() -> None:
    assert [each for each in defined() if not issubclass(each, Input)] == []


@pytest.mark.parametrize("struct", STRUCTS, ids=lambda struct: struct.__qualname__)
def test_each_input_is_frozen_takes_keywords_and_refuses_a_key_it_does_not_know(
    struct: type[Input],
) -> None:
    assert issubclass(struct, Input)
    config = struct.__struct_config__
    assert (config.frozen, config.forbid_unknown_fields) == (True, True)
    taken = inspect.signature(struct).parameters.values()
    assert all(each.kind is inspect.Parameter.KEYWORD_ONLY for each in taken)
    assert struct.__doc__, "each input says what the page prints of it"


def kinds(hint: object) -> list[object]:
    """Every type a field's annotation names, through its unions, tuples and aliases."""
    value = getattr(hint, "__value__", None)
    if value is not None:
        return kinds(value)
    origin = get_origin(hint)
    if origin is None:
        return [hint]
    found: list[object] = [origin]
    for each in get_args(hint):
        found.extend(kinds(each))
    return found


@pytest.mark.parametrize("struct", STRUCTS, ids=lambda struct: struct.__qualname__)
def test_no_input_holds_a_mapping_a_list_or_a_value_of_any_type(
    struct: type[Input],
) -> None:
    hints = msgspec.structs.fields(struct)
    for field in hints:
        named = kinds(field.type)
        assert Any not in named, field.name
        assert not any(kind in {dict, list, set, object} for kind in named), field.name


@pytest.mark.parametrize("struct", STRUCTS, ids=lambda struct: struct.__qualname__)
def test_a_default_is_an_empty_value_or_a_fixed_word_never_a_mutable_one(
    struct: type[Input],
) -> None:
    for field in msgspec.structs.fields(struct):
        if field.default is msgspec.NODEFAULT:
            assert field.default_factory is msgspec.NODEFAULT, field.name
            continue
        assert isinstance(
            field.default, str | int | float | bool | tuple | types.NoneType
        )
        if isinstance(field.default, tuple):
            assert field.default == (), field.name


def test_the_whole_page_has_one_json_schema() -> None:
    schema = msgspec.json.schema(Page)
    assert schema["$ref"] == "#/$defs/Page"


def test_done_requires_its_total_even_when_it_has_no_cards() -> None:
    with pytest.raises(msgspec.ValidationError, match="missing required field `total`"):
        msgspec.json.decode(
            b'{"key":"done","look":"done","title":"Done","empty":"No ended tasks"}',
            type=Column,
        )


def test_done_keeps_its_total_when_it_draws_only_the_newest_cards() -> None:
    cards = tuple(
        msgspec.structs.replace(
            columns.DONE.cards[0], slug=slug, href=f"/studio/shop/tasks/{slug}"
        )
        for slug in (f"task-{number:02d}" for number in range(24, 4, -1))
    )
    done = msgspec.structs.replace(
        columns.DONE,
        total=25,
        cards=cards,
        older=Link(href="/studio/shop/done", label="5 older"),
    )
    restored = msgspec.json.decode(msgspec.json.encode(done), type=Column)
    assert restored.total == 25
    assert len(restored.cards) == 20
    assert restored.older and restored.older.label == "5 older"


@pytest.mark.parametrize("tab", ["drop", "park"])
@pytest.mark.parametrize("key", ["breaker:gift-note-in-export:0:old", waiting.GIFT_KEY])
def test_the_breaker_confirm_keeps_the_requested_key_and_words(
    tab: str, key: str
) -> None:
    words = "Wait for the next export.\nKeep the gift note."
    raw = msgspec.json.encode(
        {
            "host": "studio",
            "workspace": "shop",
            "base": "/studio/shop",
            "task": waiting.GIFT,
            "tab": tab,
            "key": key,
            "words": words,
        }
    )
    viewer = msgspec.json.decode(raw, type=Viewer)
    assert (viewer.tab, viewer.key, viewer.words) == (tab, key, words)
    assert msgspec.json.decode(msgspec.json.encode(viewer), type=Viewer) == viewer


def test_an_unreachable_workspace_keeps_its_fix_apart_from_its_last_answer() -> None:
    space = Space(
        id="ws-travel-shop",
        name="travel/shop",
        path="/work/shop",
        says="not reachable · last answer 5m ago",
        title="Leave travel and join it with the name in its board address.",
        reachable=False,
    )
    restored = msgspec.json.decode(msgspec.json.encode(space), type=Space)
    assert restored.title == space.title
    assert restored.says == space.says


def test_an_input_refuses_a_key_it_does_not_know_and_a_fact_it_lacks() -> None:
    moment = datetime(2026, 11, 25, 16, 0, tzinfo=UTC)
    good = msgspec.json.encode(When(at=moment, shown="just now"))
    assert msgspec.json.decode(good, type=When).shown == "just now"
    with pytest.raises(msgspec.ValidationError, match="unknown field `colour`"):
        msgspec.json.decode(
            b'{"at":"2026-11-25T16:00:00Z","shown":"x","colour":1}', type=When
        )
    with pytest.raises(msgspec.ValidationError, match="missing required field `shown`"):
        msgspec.json.decode(b'{"at":"2026-11-25T16:00:00Z"}', type=When)
    with pytest.raises(msgspec.ValidationError, match="timezone"):
        msgspec.json.decode(b'{"at":"2026-11-25T16:00:00","shown":"x"}', type=When)


def test_the_forge_age_in_each_bar_ticks_from_the_forge_look() -> None:
    read = frame.FRAME.statusbar.read
    looked = When(at=read.at.replace(minute=58, hour=15), shown="2m ago", ticks="ago")
    chip = Chip(label="checked", icon="eye", when=looked)
    top = msgspec.structs.replace(frame.TOPBAR, chips=(chip,))
    status = msgspec.structs.replace(
        frame.FRAME.statusbar, forge="the board looked at GitHub", forge_when=looked
    )
    restored = msgspec.json.decode(
        msgspec.json.encode(
            msgspec.structs.replace(frame.FRAME, topbar=top, statusbar=status)
        ),
        type=type(frame.FRAME),
    )
    assert restored.topbar.chips[0].when == restored.statusbar.forge_when == looked
    assert restored.statusbar.read == read


@pytest.mark.parametrize(
    "extra",
    [
        {},
        {"overview": panel.OVERVIEW},
        {"merge": panel.MERGE, "overview": panel.OVERVIEW},
    ],
)
def test_a_merge_panel_requires_its_confirm_body_or_an_explicit_refusal(
    extra: dict[str, object],
) -> None:
    raw = msgspec.json.encode({"slug": panel.SLUG, "shows": "merge", **extra})
    with pytest.raises(msgspec.ValidationError, match="panel"):
        msgspec.json.decode(raw, type=Panel)


def test_a_panel_keeps_an_explicit_refusal_or_missing_task() -> None:
    back = Link(href=frame.FRAME.viewer.base, label="Back")
    refusal = NotNow(id="merge", said="Lem merges it now", back=back)
    missing = Missing(title="A task", said="No task has this name", back=back.href)
    for expected in (
        Panel(slug=panel.SLUG, shows="merge", not_now=refusal),
        Panel(slug=panel.SLUG, shows="merge", missing=missing),
    ):
        assert (
            msgspec.json.decode(msgspec.json.encode(expected), type=Panel) == expected
        )


def test_a_no_without_words_keeps_its_refusal_inside_the_approval_sheet() -> None:
    refusal = Note(
        look="bad",
        icon="triangle-exclamation",
        word="Not done.",
        said="No needs your words: what should the criteria say? Nothing was recorded.",
    )
    raw = msgspec.json.encode(
        {
            "slug": STOCK.task.slug,
            "shows": "criteria",
            "criteria": {
                "approve": {
                    "label": "Approve the criteria",
                    "head": "The criteria wait for your yes",
                    "sheet": True,
                    "note": refusal,
                },
            },
        }
    )
    criteria = msgspec.json.decode(raw, type=Panel).criteria
    assert criteria and criteria.approve
    assert criteria.approve.sheet and criteria.approve.note == refusal
    assert criteria.note is None


@pytest.mark.parametrize(
    "views", [{}, {"tasks": columns.TASKS, "waits": waiting.WAITS}]
)
def test_a_workspace_page_requires_exactly_one_view(views: dict[str, object]) -> None:
    raw = msgspec.json.encode({"frame": frame.FRAME, **views})
    with pytest.raises(msgspec.ValidationError, match="view"):
        msgspec.json.decode(raw, type=Page)


def test_a_workspace_page_refuses_a_body_for_a_different_view() -> None:
    assert frame.FRAME.viewer.view == "tasks"
    raw = msgspec.json.encode({"frame": frame.FRAME, "waits": waiting.WAITS})
    with pytest.raises(msgspec.ValidationError, match="must match"):
        msgspec.json.decode(raw, type=Page)


def test_the_done_view_uses_the_older_tasks_body() -> None:
    viewer = msgspec.structs.replace(frame.FRAME.viewer, view="done")
    done = msgspec.structs.replace(frame.FRAME, viewer=viewer)
    older = Older(newer=Link(href=viewer.base, label="Newer tasks"))
    expected = Page(frame=done, older=older)
    assert msgspec.json.decode(msgspec.json.encode(expected), type=Page) == expected


def test_a_workspace_page_can_keep_a_panel_with_its_one_view() -> None:
    expected = Page(frame=frame.FRAME, tasks=columns.TASKS, panel=panel.MERGE_STEP)
    assert msgspec.json.decode(msgspec.json.encode(expected), type=Page) == expected


def test_a_native_task_page_needs_no_workspace_body() -> None:
    viewer = msgspec.structs.replace(frame.FRAME.viewer, native=True, task=panel.SLUG)
    native = msgspec.structs.replace(frame.FRAME, viewer=viewer)
    raw = msgspec.json.encode({"frame": native, "panel": panel.OPEN})
    page = msgspec.json.decode(raw, type=Page)
    assert page.panel == panel.OPEN and page.tasks is None


@pytest.mark.parametrize("native", [False, True], ids=("web", "native"))
def test_a_page_without_a_workspace_body_requires_both_native_and_a_panel(
    *, native: bool
) -> None:
    viewer = msgspec.structs.replace(frame.FRAME.viewer, native=native)
    bare = msgspec.structs.replace(frame.FRAME, viewer=viewer)
    page = {"frame": bare} if native else {"frame": bare, "panel": panel.OPEN}
    with pytest.raises(msgspec.ValidationError, match="view"):
        msgspec.json.decode(msgspec.json.encode(page), type=Page)
