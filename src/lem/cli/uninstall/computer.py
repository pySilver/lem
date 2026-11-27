"""This computer's board server, stopped as `lem serve stop` stops it, its tailnet door, closed
as `lem serve door off` closes it with no new start of the server, and Lem's folders.
"""

import os
import shutil
from typing import TYPE_CHECKING

from lem.board import machine, publish, stopping, tailnet, tailscale
from lem.kernel import folders
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.uninstall.report import Report

IGNORE = ".gitignore"


def stopped(report: Report) -> bool:
    """Stop the board server of this install; whether none runs now."""
    with report.step("the board server", "the owner runs lem serve stop"):
        said = stopping.stop(os.environ)
        if said.stopped:
            report.gone("the board server of this computer")
        elif said.pid is not None:
            raise Refusal(
                "uninstall-board",
                f"the board server still runs: {said.said}",
                "the owner runs lem serve stop of the install that serves",
            )
        return True
    return False


def door_closed(home: Path, report: Report) -> None:
    """Take Lem's entry out of `tailscale serve` while the machine's settings say the door is
    open; an entry of another target stays, refused."""
    with report.step("the tailnet door", "the owner runs lem serve door off"):
        settings = machine.settings(home)
        if not settings.tailscale:
            return
        cli = tailscale.needed(os.environ)
        port = machine.guarded(settings.tailscale_port, os.environ)
        name = tailnet.status(cli).me.name.rstrip(".")
        if publish.removed(cli, name, port):
            report.gone(f"the tailnet door on port {port}")


def removed(folder: Path, report: Report) -> None:
    """Remove one of Lem's folders, when it is there."""
    with report.step(str(folder), f"the owner removes {folder} by hand"):
        folders.inside_test_root(folder)
        if folder.exists():
            shutil.rmtree(folder)
            report.gone(str(folder))


def emptied(worktrees: Path) -> None:
    """Remove the worktrees' folder, which holds its ignore file only once every worktree
    went; refused, with nothing removed, while it holds anything else."""
    if not worktrees.exists():
        return
    names = (one.name for one in worktrees.iterdir())
    others = sorted(name for name in names if name != IGNORE)
    if others:
        held = ", ".join(others)
        raise Refusal(
            "uninstall-worktrees",
            f"{worktrees} still holds {held}",
            f"the owner moves or removes what {worktrees} holds",
        )
    shutil.rmtree(worktrees)
