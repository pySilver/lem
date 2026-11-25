"""The launch line of a task's session on Claude Code, for the `Harness` port on Claude Code
(`harness_claude`).

The line is `LEM_TASK=SLUG`, which the `session-start` hook reads, then
`CLAUDE_CODE_AUTO_COMPACT_WINDOW=N`, the number of tokens past which the session compacts itself
with the handoff's form, then `claude`, the seat's model and effort, `--plugin-dir` when the
project loads no installed plugin, and the first prompt, `Read BRIEF and follow it.`. Each word
is quoted for sh, zsh and fish alike: bare when it needs no quote, in double quotes when it holds
nothing those read inside them, so that the usual line stays readable in agterm's tree.

N is `[handoff] tokens` of the machine's `machine.toml` in Lem's home folder, else the owner's
number for every repository, as `lem.settings.load.machine_of` reads and checks it; 0 leaves the
word out, and Claude Code compacts at its own trigger.
"""

import re
import shlex
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.settings.load import machine_of

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.ports.harness import Seat

AGENT = "claude"
# A backslash or a line break: no quote carries it to every login shell (fish reads a
# backslash inside quotes as an escape).
UNQUOTABLE = re.compile(r"[\\\n]")
# What sh, zsh and fish read inside double quotes.
DOUBLE_QUOTED = re.compile(r"[\"$`\\]")


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


def compaction(home: Path, environ: Mapping[str, str]) -> int | None:
    """The number a session compacts itself at, `handoff.tokens` of the machine's file in
    Lem's home folder `home`; None for Claude Code's own trigger. The settings refuse a number
    Claude Code would refuse."""
    tokens = machine_of(home, environ).handoff.tokens
    return tokens or None
