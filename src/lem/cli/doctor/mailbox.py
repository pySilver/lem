"""The mailbox waiter that brings a wake into an idle Claude Code session."""

import shlex
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.claude_plugin import claude_home, decoded
from lem.cli.doctor import tool_words
from lem.cli.doctor.tools import tool_row

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look
    from lem.cli.doctor.row import Row

EVENTS = ("SessionStart", "Stop", "UserPromptSubmit")


class Hook(msgspec.Struct, frozen=True):
    """The fields that make a command hook a mailbox waiter."""

    kind: str = msgspec.field(name="type")
    command: str = ""
    rewakes: bool = msgspec.field(default=False, name="asyncRewake")

    def waits(self) -> bool:
        """Whether this hook runs the waiter with Claude Code's wake enabled."""
        if self.kind != "command" or not self.rewakes:
            return False
        try:
            program, selector = shlex.split(self.command)
        except ValueError:
            return False
        return (
            Path(program).name == tool_words.MAILBOX.program
            and selector == "claude-hook"
        )


class HookGroup(msgspec.Struct, frozen=True):
    """The hooks under one matcher of a Claude Code event."""

    hooks: tuple[Hook, ...]


class Settings(msgspec.Struct, frozen=True):
    """The user settings of Claude Code, by the keys that control its hooks."""

    disabled: bool = msgspec.field(default=False, name="disableAllHooks")
    hooks: dict[str, tuple[HookGroup, ...]] = msgspec.field(default_factory=dict)

    def has_waiter(self, event: str) -> bool:
        """Whether the event has a mailbox waiter."""
        return any(
            hook.waits() for group in self.hooks.get(event, ()) for hook in group.hooks
        )


def mailbox_row(look: Look) -> Row:
    """Find the mailbox program and its waiter in the active user settings."""
    row = tool_row(look, tool_words.MAILBOX)
    if not row.found:
        return row
    path = claude_home({**look.environ, "HOME": str(look.home)}) / "settings.json"
    settings = decoded(path, Settings)
    if settings is None:
        return msgspec.structs.replace(row, found=False, detail=f"cannot read {path}")
    if settings.disabled:
        return msgspec.structs.replace(
            row, found=False, detail=f"disableAllHooks is true in {path}"
        )
    missing = ", ".join(event for event in EVENTS if not settings.has_waiter(event))
    if missing:
        return msgspec.structs.replace(
            row, found=False, detail=f"mailbox hook is missing for {missing} in {path}"
        )
    return row
