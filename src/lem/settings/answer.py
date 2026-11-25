"""What `lem settings set` answers: the file it wrote, the line, and the value then in force
with the file it comes from, which may be a nearer file than the one written."""

from typing import TYPE_CHECKING

import msgspec

from lem.records.base import Frozen
from lem.settings import places

if TYPE_CHECKING:
    from lem.settings.edit import Edit
    from lem.settings.load import Loaded
    from lem.settings.reading import Where


class Set(Frozen, frozen=True, kw_only=True):
    """What `set` wrote: the file, the key, its line or None when it went, and the value then
    in force with the file it comes from."""

    path: str = msgspec.field(name="file")
    key: str
    line: str | None = None
    in_force: object = msgspec.field(default=None, name="value")
    source: str = msgspec.field(name="from")
    said: str


def line_of(change: Edit) -> str | None:
    """The line the edit wrote, as TOML has it; None when it took the line out."""
    if change.given is None:
        return None
    written = msgspec.json.encode(change.given).decode()
    return f"{change.key} = {written}"


def said_of(key: str, source: str, change: Edit, where: Where) -> str:
    """The line for the owner: the file the value in force comes from, and how it stands to
    the file written."""
    named = where.named(change.scope)
    if change.given is None:
        return f"{key} is from {source}; {named} names none"
    if source == named:
        return f"{key} is from {source}"
    return f"{key} is from {source}, which comes before {named}"


def answer(change: Edit, key: str, where: Where, loaded: Loaded) -> Set:
    """The answer of `set` after the edit `change` of `key`, from the settings `loaded` that
    were checked before the write."""
    tables = msgspec.to_builtins(loaded.settings)
    source = loaded.sources.get(key, places.DEFAULT)
    return Set(
        path=str(change.path),
        key=key,
        line=line_of(change),
        in_force=(tables.get(change.table) or {}).get(change.key),
        source=source,
        said=said_of(key, source, change, where),
    )
