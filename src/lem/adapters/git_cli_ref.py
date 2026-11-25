"""A reset holds the checked ref while Git updates the index and worktree."""

import select
import subprocess
from typing import TYPE_CHECKING

from lem.adapters.git_cli_shell import GIT, TIMEOUT, all_words, last_words, own
from lem.ports.faults import Unanswered
from lem.ports.git_facts import GitRefused

if TYPE_CHECKING:
    from pathlib import Path

    from lem.adapters.git_cli_shell import Shell


def reset_under_lock(
    shell: Shell, where: Path, target: str, expect: str
) -> str | GitRefused:
    """Lock HEAD at `expect` before changing anything, then publish `target`."""
    command = [GIT, "-C", str(where), "update-ref", "-m", "lem reset", "--stdin"]
    try:
        with subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=own(shell.environ),
            text=True,
        ) as proc:
            return reset_transaction(shell, where, proc, target, expect)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Unanswered(GIT, str(error)) from error


def acknowledged(proc: subprocess.Popen[str], command: str, reply: str) -> bool:
    """Send one step in the transaction and wait for Git's acknowledgement."""
    if proc.stdin is None or proc.stdout is None:
        raise Unanswered(GIT, "the ref transaction has no pipes")
    proc.stdin.write(command)
    proc.stdin.flush()
    ready, _, _ = select.select([proc.stdout], [], [], TIMEOUT)
    if not ready:
        raise subprocess.TimeoutExpired(proc.args, TIMEOUT)
    return proc.stdout.readline() == reply


def reset_transaction(
    shell: Shell, where: Path, proc: subprocess.Popen[str], target: str, expect: str
) -> str | GitRefused:
    """Release the ref lock if a Git call fails to answer or Lem is interrupted."""
    try:
        return reset_prepared(shell, where, proc, target, expect)
    except BaseException:
        proc.terminate()
        raise


def reset_prepared(
    shell: Shell, where: Path, proc: subprocess.Popen[str], target: str, expect: str
) -> str | GitRefused:
    """Use Git's two-tree worktree update while the ref transaction is prepared."""
    updates = f"update HEAD {target} {expect}\nupdate ORIG_HEAD {expect}\nprepare\n"
    if not (
        acknowledged(proc, "start\n", "start: ok\n")
        and acknowledged(proc, updates, "prepare: ok\n")
    ):
        _, said = proc.communicate(timeout=TIMEOUT)
        return GitRefused(said=all_words(said))
    ran = shell.tried(where, "read-tree", "-m", "-u", expect, target)
    _, said = proc.communicate(
        "abort\n" if ran.returncode else "commit\n", timeout=TIMEOUT
    )
    if ran.returncode:
        return GitRefused(said=last_words(ran))
    if proc.returncode:
        return GitRefused(said=all_words(said))
    return target
