"""One settings file read and checked: UTF-8 TOML, each table in a file where it is valid, each
key one its table knows, each value of its type.

Every refusal names the file and the fix: a table in the wrong file names the file where it is
valid, an unknown table or key names the nearest valid one, and a wrong value names what the
field takes (its description in the struct).
"""

import difflib
import re
import tomllib
from typing import TYPE_CHECKING

import msgspec
from msgspec import inspect

from lem.kernel.errors import Refusal
from lem.settings import places

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

type Tables = dict[str, object]
# Where a value of a refusal stands, as msgspec says it: `$.branch.base`, `$.seats.experts[0]`.
AT = re.compile(r" - at `\$\.([A-Za-z0-9_.-]+)")


def tables_of(text: str, name: str) -> Tables:
    """The tables of one file's text; a text that is not TOML is refused with its line."""
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise Refusal(
            "settings-toml",
            f"{name} is not TOML: {error}",
            f"correct {name}, then run the command again",
        ) from error


def decoded(body: bytes | None, name: str) -> Tables:
    """The tables of one file's bytes; none for no file, and a text that is not UTF-8 is
    refused: read as the locale's, a file would mean something else on another machine."""
    if body is None:
        return {}
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Refusal(
            "settings-toml",
            f"{name} is not UTF-8 text (byte {error.start} does not read)",
            f"save {name} as UTF-8",
        ) from error
    return tables_of(text, name)


def read(path: Path, name: str) -> Tables:
    """The tables of the file at `path`; none when it is not there."""
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise Refusal(
            "settings-toml",
            f"{name} cannot be read ({error.strerror})",
            f"make {name} readable, or remove it",
        ) from error
    return decoded(body, name)


def nearest(word: str, valid: tuple[str, ...]) -> str:
    """The valid word nearest to `word`, and every valid one."""
    close = difflib.get_close_matches(word, valid, n=1)
    listed = ", ".join(valid)
    return f"did you mean {close[0]}? valid: {listed}" if close else f"valid: {listed}"


def placed(raw: Tables, own: places.File, named: Callable[[places.File], str]) -> None:
    """Refuse a table Lem does not know, and one whose place is another file."""
    for table in raw:
        valid = places.valid(table)
        if not valid:
            raise Refusal(
                "settings-key",
                f"{named(own)}: [{table}] is no table of Lem's",
                nearest(table, places.NAMES),
            )
        if own not in valid:
            where = " or ".join(named(one) for one in places.ORDER if one in valid)
            raise Refusal(
                "table-place",
                f"{named(own)}: [{table}] is not valid in this file",
                f"move [{table}] to {where}",
            )


def keyed(raw: Tables, shape: type[msgspec.Struct], name: str) -> None:
    """Refuse a key a table does not know, with the nearest one it knows."""
    tables = {field.name: field.type for field in msgspec.structs.fields(shape)}
    for table, body in raw.items():
        kind = tables.get(table)
        if not isinstance(body, dict) or not isinstance(kind, type):
            continue
        known = tuple(field.name for field in msgspec.structs.fields(kind))
        unknown = [key for key in body if key not in known]
        if unknown:
            raise Refusal(
                "settings-key",
                f"{name}: {table}.{unknown[0]} is no key of [{table}]",
                nearest(unknown[0], known),
            )


def described(shape: type, where: str) -> str | None:
    """The description of the field at `where` (`branch.base`) of `shape`, the fix of a
    refusal of its value."""
    info: inspect.Type = inspect.type_info(shape)
    said = None
    for part in where.split("."):
        while isinstance(info, inspect.Metadata | inspect.UnionType):
            info = info.type if isinstance(info, inspect.Metadata) else info.types[0]
        fields = info.fields if isinstance(info, inspect.StructType) else ()
        found = next((field for field in fields if field.name == part), None)
        if found is None:
            return said
        info = found.type
        extra = info.extra_json_schema if isinstance(info, inspect.Metadata) else None
        said = (extra or {}).get("description", said)
    return said


def converted[Shape](raw: Mapping[str, object], shape: type[Shape], name: str) -> Shape:
    """The tables of one file as `shape`; a wrong value is refused with what it takes."""
    try:
        return msgspec.convert(raw, shape)
    except msgspec.ValidationError as error:
        found = AT.search(str(error))
        fix = described(shape, found[1]) if found else None
        raise Refusal(
            "settings",
            f"{name}: {error}",
            fix or "correct the line as docs/settings.md says",
        ) from error
