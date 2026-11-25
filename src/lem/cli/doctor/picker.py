"""The task picker's row: the agterm keymap line that runs the app's own `lem picker` with a
chord, and whether agterm's keymap holds it.

The keymap is agterm's file, so Lem only reads it, where agterm reads it by default. The line
names the app's command by a path an update keeps: Homebrew's `opt/lem/bin/lem` when the app's
environment is under it, else the `lem` beside the app's Python. A line of a Lem before the app,
an interpreter and a script of the marketplace clone, is named as one that no longer works.
"""

import itertools
import re
import shlex
from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor.row import OPTIONAL, Row

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

KEYMAP = Path(".config") / "agterm" / "keymap.conf"
CHORD = "ctrl+cmd+t"
OLD_LINE = re.compile(r"plugins/marketplaces/[^\s]*/(?:bin/lem\s+picker|picker\.py)\b")
USED_FOR = (
    "a chord in agterm that lists this repository's tasks, what waits for the owner first, "
    "and opens the board of the one picked"
)
NO_CHORD = "no chord lists the tasks, and `/lem status SLUG` opens a board. "


def stable_lem(look: Look) -> Path | None:
    """The path of this app's command `lem` that outlives an update, or None when the app has
    none beside its Python."""
    home = look.prefix.resolve()
    for brew in look.brews:
        opt = brew / "opt" / "lem"
        command = opt / "bin" / "lem"
        if command.is_file() and home.is_relative_to(opt.resolve()):
            return command
    own = look.executable.parent / "lem"
    return own.resolve() if own.is_file() else None


def names(word: str, home: Path, command: Path) -> bool:
    """Whether one word of a keymap line names the file `command`, by its path or from `~/`."""
    path = Path(word)
    if word.startswith("~/"):
        path = home / word[2:]
    if not path.is_absolute():
        return False
    try:
        return path == command or path.samefile(command)
    except OSError:
        return False


def keymap_runs(said: str, home: Path, command: Path) -> bool:
    """Whether the keymap line `said` runs `command picker`: a `command` line one of whose
    words names the file `command`, followed by `picker`."""
    if not said.lstrip().startswith("command"):
        return False
    try:
        words = shlex.split(said)
    except ValueError:
        words = said.split()
    pairs = itertools.pairwise(words)
    return any(
        after == "picker" and names(word, home, command) for word, after in pairs
    )


def keymap_detail(keymap: Path, lines: list[str], command: Path, *, held: bool) -> str:
    """What the keymap holds: the line, a line of a Lem before the app, or neither."""
    if held:
        return f"{keymap} holds the line"
    old = next((one for one in lines if OLD_LINE.search(one)), None)
    if old is None:
        return f"{keymap} has no line that runs {command} picker"
    return (
        f"{keymap} holds a line of a Lem before the app, which no longer works: "
        f"{old.strip()}; the owner puts this row's line in its place and runs "
        "`agtermctl keymap reload`"
    )


def picker_row(look: Look) -> Row:
    """The keymap line of the task picker for this machine, and whether the keymap holds it.
    Optional: nothing of Lem needs the chord, and `/lem status SLUG` opens the same board."""
    keymap = look.home / KEYMAP
    command = stable_lem(look)
    if command is None:
        return Row(
            name="task picker",
            need=OPTIONAL,
            found=False,
            detail=None,
            used_for=USED_FOR,
            without_it=(
                f"{NO_CHORD}Lem's app has no command `lem` beside its Python "
                f"{look.executable}, so no keymap line can name it: the owner installs Lem "
                "again"
            ),
        )
    try:
        lines = keymap.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lines = []
    held = any(keymap_runs(one, look.home, command) for one in lines)
    quoted = shlex.quote(str(command))
    return Row(
        name="task picker",
        need=OPTIONAL,
        found=held,
        detail=keymap_detail(keymap, lines, command, held=held),
        used_for=USED_FOR,
        without_it=(
            f"{NO_CHORD}The owner adds the line to {keymap} and runs `agtermctl keymap "
            f"reload`; {CHORD} is the chord unless he picks another. The line names "
            f"{command}, Lem's command by a path that an update of the app keeps"
        ),
        line=f'command "Lem tasks ›" {CHORD} --error-hud {quoted} picker',
    )
