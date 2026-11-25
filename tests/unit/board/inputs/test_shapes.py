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
from lem.board.inputs.page import Page
from lem.board.inputs.parts import Input, When

# The walking skeleton's kanban, which `board-views` and `board-pages` leave for `tasks.py`.
SKELETON = "lem.board.inputs.kanban"


def structs() -> list[type[Input]]:
    """Every struct the inputs define, but the skeleton's."""
    found: list[type[Input]] = []
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


STRUCTS = structs()


def test_the_inputs_are_many_structs_each_a_section_or_a_part_of_one() -> None:
    assert len(STRUCTS) > 80


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
    assert len(schema["$defs"]) > 60


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
