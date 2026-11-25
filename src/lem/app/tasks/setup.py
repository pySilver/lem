"""`checks.setup` in a worktree just made, so that its tests can run (`project.worktree_setup` on
`main`): without it a fast-track task whose builder runs no test reaches the checks with no
packages, and the checks fail on what the change did not cause (a probe on 2026-11-18:
`setup = ["npm ci"]`, a README fix, and the checks red on a missing package).

Each command runs in the project's own shell line, its output into `setup.log` of the task's
folder. A command that fails stops the rest and is refused with its exit; the worktree stays.
"""

import os
from typing import TYPE_CHECKING

from lem.kernel import procs
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

type Commands = tuple[str, ...]

LOG = "setup.log"
SHELL = "/bin/sh"


class Ran(Frozen, frozen=True, kw_only=True):
    """One command of the setup and its exit."""

    command: str
    exit: int


def ran(command: str, worktree: Path, log: Path) -> Ran:
    """Run one command of the setup in `worktree`, its output appended to `log`."""
    with log.open("ab") as out:
        out.write(f"$ {command}\n".encode())
        out.flush()
        argv = [SHELL, "-c", command]
        proc = procs.start_group(argv, worktree, os.environ, out)
        code = proc.wait()
    return Ran(command=command, exit=code)


def set_up(commands: Commands, worktree: Path, folder: Path) -> tuple[Ran, ...]:
    """Run `commands` one by one in `worktree`; refused at the first that fails."""
    log = folder / LOG
    log.write_bytes(b"")
    done: list[Ran] = []
    for command in commands:
        one = ran(command, worktree, log)
        done.append(one)
        if one.exit != 0:
            raise Refusal(
                "setup",
                f"`{command}` of checks.setup failed in the new worktree {worktree} (exit "
                f"{one.exit}; its output is in {log}), so its tests cannot run; the "
                "worktree stays",
                "correct the command in .lem/settings.toml, then run it there by hand",
            )
    return tuple(done)
