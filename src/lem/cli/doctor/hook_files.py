"""The plugin's side of its hooks: `hooks/hooks.json`, each of whose lines starts `hooks/run` with
a selector `lem-hook` knows, in the one form `/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" SELECTOR
2>/dev/null || :`.

A file that is not there, that does not read, that reads another way than a table of hooks, or
that has a line of another form, is a broken plugin, named with what is wrong.
"""

import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

LINE = re.compile(
    r'/bin/sh "\$CLAUDE_PLUGIN_ROOT/hooks/run" ([a-z-]+) 2>/dev/null \|\| :'
)


def named(path: Path) -> str:
    """A file of the plugin as `hooks/hooks.json`."""
    folder = path.parent.name
    return f"{folder}/{path.name}"


class Broken(ValueError):
    """A file of the plugin that is not whole, and what is wrong with it."""


def commands_of(manifest: object) -> list[str] | None:
    """The command of each hook of a hooks file, as Claude Code reads it: `{"hooks": {EVENT:
    [{"hooks": [{"command": ...}]}]}}`; None for another shape."""
    table = manifest.get("hooks") if isinstance(manifest, dict) else None
    if not isinstance(table, dict):
        return None
    groups = [entry for group in table.values() for entry in as_list(group)]
    hooks = [hook for entry in groups for hook in as_list(hooks_of(entry))]
    tables = [hook for hook in hooks if isinstance(hook, dict)]
    if len(tables) != len(hooks):
        return None
    return [str(hook.get("command") or "") for hook in tables]


def as_list(found: object) -> list[object]:
    """`found` when it is a list, else one entry that is no table, which no reader takes."""
    return found if isinstance(found, list) else [None]


def hooks_of(entry: object) -> object:
    """The hooks of one entry of an event."""
    return entry.get("hooks") if isinstance(entry, dict) else None


def manifest_of(path: Path) -> object:
    """The JSON a hooks file holds; refused when it is not there or does not read."""
    shown = named(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Broken(f"{shown} is missing") from None
    except OSError as error:
        raise Broken(f"{shown} cannot be read ({error.strerror})") from None
    except ValueError as error:
        line = getattr(error, "lineno", None)
        at = "" if line is None else f" (line {line})"
        raise Broken(f"{shown} is not JSON{at}") from None


def selectors_of(path: Path, known: tuple[str, ...]) -> tuple[str, ...]:
    """The selectors of `lem-hook` the hooks file at `path` starts, each once in their order;
    `known` are the selectors `lem-hook` has."""
    shown = named(path)
    commands = commands_of(manifest_of(path))
    if commands is None:
        raise Broken(f"{shown} is not a table of hooks")
    found: list[str] = []
    for command in commands:
        matched = LINE.fullmatch(command)
        if matched is None or matched[1] not in known:
            raise Broken(
                f"{shown} has a line that is not Lem's: {command!r}, which no lem-hook runs"
            )
        if matched[1] not in found:
            found.append(matched[1])
    return tuple(found)
