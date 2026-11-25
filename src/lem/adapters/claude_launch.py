"""The launch line of a task's session on Claude Code, for the `Harness` port on Claude Code
(`harness_claude`).

The line is `LEM_TASK=SLUG`, which the `session-start` hook reads, then
`CLAUDE_CODE_AUTO_COMPACT_WINDOW=N`, the number of tokens past which the session compacts itself
with the handoff's form, then `claude`, the seat's model and effort, `--plugin-dir` when the
project loads no installed plugin, and the first prompt, `Read BRIEF and follow it.`. Each word
is quoted for sh, zsh and fish alike: bare when it needs no quote, in double quotes when it holds
nothing those read inside them, so that the usual line stays readable in agterm's tree.

N is `[handoff] tokens` of the machine's `machine.toml` in Lem's home folder, else the owner's
number for every repository; 0 leaves the word out, and Claude Code compacts at its own
trigger. The step `settings` gives the machine's settings one reader; until then this one reads
the one key.
"""

import re
import shlex
import tomllib
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.harness import Seat

AGENT = "claude"
# A backslash or a line break: no quote carries it to every login shell (fish reads a
# backslash inside quotes as an escape).
UNQUOTABLE = re.compile(r"[\\\n]")
# What sh, zsh and fish read inside double quotes.
DOUBLE_QUOTED = re.compile(r"[\"$`\\]")
MACHINE = "machine.toml"
# The owner's number for all his repositories: "lets keep the limit at 600K for now (default
# settings)" (2026-11-21, on the shape of task 4).
TOKENS = 600_000
# Claude Code refuses a window under this number (`research-compaction.md` on `main`, read
# 2026-11-21).
FLOOR = 100_000
FIX = (
    f"the owner writes `tokens` of [handoff] in {MACHINE} as 0 (Claude Code's own trigger) "
    f"or a whole number of {FLOOR} or more"
)


class Handoff(msgspec.Struct, frozen=True, kw_only=True):
    """The machine's `[handoff]`: when a session compacts itself."""

    tokens: int = TOKENS


class Machine(msgspec.Struct, frozen=True, kw_only=True):
    """The one table of the machine's settings that the launch line reads."""

    handoff: Handoff = msgspec.field(default_factory=Handoff)


def shell_word(word: str) -> str:
    """`word` as one word of sh, zsh and fish alike; refused when no quote carries it."""
    if UNQUOTABLE.search(word):
        raise Refusal(
            "unquotable",
            f"{word!r} holds a backslash or a line break, which the launch line cannot "
            "carry to every login shell",
            "the owner moves the folder, or writes the seat, without them",
        )
    if shlex.quote(word) == word:
        return word
    return shlex.quote(word) if DOUBLE_QUOTED.search(word) else f'"{word}"'


def launch_words(
    seat: Seat, brief: Path, plugin: Path | None, tokens: int | None
) -> list[str]:
    """The words of the launch line, before their quotes."""
    slug = brief.parent.name
    words = [f"LEM_TASK={slug}"]
    if tokens is not None:
        words.append(f"CLAUDE_CODE_AUTO_COMPACT_WINDOW={tokens}")
    words.append(AGENT)
    if seat.model:
        words.extend(("--model", seat.model))
    if seat.effort:
        words.extend(("--effort", seat.effort))
    if plugin is not None:
        words.extend(("--plugin-dir", str(plugin)))
    words.append(f"Read {brief} and follow it.")
    return words


def compaction(home: Path) -> int | None:
    """The number a session compacts itself at, None for Claude Code's own trigger; a number
    Claude Code would refuse is refused."""
    path = home / MACHINE
    tokens = machine_of(path).handoff.tokens
    if not tokens:
        return None
    if tokens < FLOOR:
        raise Refusal(
            "handoff-tokens",
            f"[handoff] tokens in {path} is {tokens}, and Claude Code refuses a window "
            f"under {FLOOR}",
            FIX,
        )
    return tokens


def machine_of(path: Path) -> Machine:
    """The machine's settings in `path`, none when the file is not there; a file that does not
    read is refused."""
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        return Machine()
    try:
        return msgspec.convert(tomllib.loads(body.decode()), Machine)
    except (
        UnicodeDecodeError,
        tomllib.TOMLDecodeError,
        msgspec.ValidationError,
    ) as error:
        raise Refusal(
            "handoff-tokens",
            f"{path} does not read as the machine's settings: {error}",
            FIX,
        ) from error
