"""One settings file read and checked: UTF-8 TOML, each table in a file where it is valid, each
key one its table knows, each value of its type.

Every refusal names the file and the fix: a table in the wrong file names the file where it is
valid, an unknown table or key names the nearest valid one, and a wrong value names what the
field takes (its description in the struct, `described.py`).
"""

import difflib
import re
import tomllib
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.settings import described, places

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

type Tables = dict[str, object]
type Namer = Callable[[places.Scope], str]
# Where a value of a refusal stands, as msgspec says it: `$.branch.base`, `$.seats.experts[0]`.
AT = re.compile(r" - at `\$\.([A-Za-z0-9_.\[\]-]+)")
# A key the table must hold, as msgspec says it.
MISSING = re.compile(r"missing required field `([^`]+)`")
TOML = "settings-toml"


def decoded(body: bytes | None, name: str) -> Tables:
    """The tables of one file's bytes; none for no file. A text that is not UTF-8 is refused:
    read as the locale's, a file would mean something else on another machine."""
    if body is None:
        return {}
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Refusal(
            TOML,
            f"{name} is not UTF-8 text (byte {error.start} does not read)",
            f"save {name} as UTF-8",
        ) from error
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise Refusal(
            TOML, f"{name} is not TOML: {error}", f"correct {name}, then run it again"
        ) from error


def read(path: Path, name: str) -> Tables:
    """The tables of the file at `path`; none when it is not there."""
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise Refusal(
            TOML,
            f"{name} cannot be read ({error.strerror})",
            f"make {name} readable, or remove it",
        ) from error
    return decoded(body, name)


def nearest(word: str, valid: tuple[str, ...]) -> str:
    """The valid word nearest to `word`, and every valid one."""
    close = difflib.get_close_matches(word, valid, n=1)
    listed = ", ".join(valid)
    return f"did you mean {close[0]}? valid: {listed}" if close else f"valid: {listed}"


def placed(raw: Tables, own: places.Scope, named: Namer) -> None:
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
            where = " or ".join(
                named(scope) for scope in places.ORDER if scope in valid
            )
            raise Refusal(
                "table-place",
                f"{named(own)}: [{table}] is not valid in this file",
                f"move [{table}] to {where}",
            )


def keyed(raw: Tables, shape: type, name: str) -> None:
    """Refuse a key a table does not know, with the nearest one it knows."""
    for table, body in raw.items():
        known = described.keys_of(shape, table)
        given = body if isinstance(body, dict) and known else {}
        unknown = [key for key in given if key not in known]
        if unknown:
            raise Refusal(
                "settings-key",
                f"{name}: {table}.{unknown[0]} is no key of [{table}]",
                nearest(unknown[0], known),
            )


def converted[Shape](raw: Mapping[str, object], shape: type[Shape], name: str) -> Shape:
    """The tables of one file as `shape`; a wrong value is refused with what it takes."""
    try:
        return msgspec.convert(raw, shape)
    except msgspec.ValidationError as error:
        raise Refusal(
            "settings",
            f"{name}: {error}",
            fix_of(shape, str(error)) or "correct the line as docs/settings.md says",
        ) from error


def fix_of(shape: type, said: str) -> str | None:
    """The fix of msgspec's refusal `said` of a value of `shape`: what the key takes."""
    searched = (AT.search(said), MISSING.search(said))
    parts = [found[1] for found in searched if found]
    return described.fix_of(shape, ".".join(parts)) if parts else None
