"""The mailbox recipe's hook declarations in the files of agterm and Codex."""

import shlex
import tomllib
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from pathlib import Path


class StartHook(msgspec.Struct, frozen=True):
    """The command of a Codex SessionStart hook, if it has one."""

    kind: str = msgspec.field(name="type", default="")
    command: str = ""


class StartGroup(msgspec.Struct, frozen=True):
    """The hooks Codex can run for a SessionStart matcher."""

    hooks: tuple[StartHook, ...] = ()


type Events = dict[str, tuple[StartGroup, ...]]


def matches(command: str, selector: str, programs: set[str]) -> bool:
    """The recipe's command and selector, with the quoting read by the shell."""
    try:
        program, action = shlex.split(command, comments=True)
    except ValueError:
        return False
    return program in programs and action == selector


def start_groups(path: Path) -> tuple[StartGroup, ...]:
    """The groups of the SessionStart event in Codex's configuration."""
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    events = msgspec.convert(config.get("hooks", {}), Events)
    return events.get("SessionStart", ())


def start_hook(path: Path, program: Path) -> bool:
    """Codex's SessionStart has the hook that registers the pane's thread."""
    try:
        groups = start_groups(path)
    except OSError, ValueError:
        return False
    return any(
        hook.kind == "command"
        and matches(hook.command, "codex-hook", {program.name, str(program)})
        for group in groups
        for hook in group.hooks
    )


def message_hook(path: Path, program: Path) -> bool:
    """agterm runs the recipe on mail, with the script's full path."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError, UnicodeError:
        return False
    hooks = [line.split(maxsplit=2) for line in lines]
    return any(
        words[:2] == ["on", "message"]
        and bool(words[2:])
        and matches(words[2], "agterm-hook", {str(program)})
        for words in hooks
    )
