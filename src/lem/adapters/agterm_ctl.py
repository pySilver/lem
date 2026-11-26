"""agterm's command `agtermctl` for the `Terminal` port on agterm (`terminal_agterm`): one call.

`agtermctl` is the first on the PATH of the place's environment, never another: a test puts a
stand-in there. A call names the socket and the window of the session the command runs in
(`AGTERM_SOCKET` and `AGTERM_WINDOW_ID`, or agterm's older `AGT_` names), since agtermctl reads
neither from the environment; a line to a mailbox names no window, which a pane's id already
places. A call agterm refuses is `Unanswered`, with what it said.
"""

import os
import pwd
import shlex
import subprocess
from typing import TYPE_CHECKING

from lem.adapters import agterm_process
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping

TOOL = agterm_process.TOOL
SOCKETS = agterm_process.SOCKETS
# How long one call of agtermctl may take. A guess: it answers in milliseconds, and a stuck one
# must not hold a command; the picker waits for the owner, and takes no limit.
TIMEOUT = 30


def ctl(
    environ: Mapping[str, str],
    *words: str,
    window: bool = True,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `agtermctl WORDS` with the place's socket and window; `Unanswered` when it is not on
    the place's PATH or does not end in time. The caller reads its exit."""
    waits = None if stdin else TIMEOUT
    try:
        return agterm_process.run(
            environ, words, window=window, stdin=stdin, timeout=waits
        )
    except FileNotFoundError:
        raise Unanswered(TOOL, "not on the PATH: agterm's command line tool") from None
    except subprocess.TimeoutExpired:
        raise Unanswered(TOOL, f"{words[0]} gave no answer in {TIMEOUT} s") from None


def said(environ: Mapping[str, str], *words: str, window: bool = True) -> str:
    """What `agtermctl WORDS` printed; `Unanswered` when it exits other than 0."""
    ran = ctl(environ, *words, window=window)
    if ran.returncode:
        told = (ran.stderr or ran.stdout).strip()
        raise Unanswered(TOOL, told or f"exit {ran.returncode}")
    return ran.stdout


def login_line(command: tuple[str, ...]) -> str:
    """The command run by the owner's login shell, `SHELL -l -c 'COMMAND'`, so that his PATH
    finds the agent: each of `command` is a line of that shell, and they run joined by
    spaces."""
    shell = pwd.getpwuid(os.getuid()).pw_shell
    if not shell.startswith("/"):
        raise Refusal(
            "login-shell",
            "the owner's login shell is not known to the system: agterm needs it to find "
            "the agent",
            "the owner sets a login shell at an absolute path (chsh), then runs this again",
        )
    return shlex.join((shell, "-l", "-c", " ".join(command)))
