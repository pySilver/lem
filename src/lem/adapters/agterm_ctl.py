"""agterm's command `agtermctl` for the `Terminal` port on agterm (`terminal_agterm`): one call,
and what its tree and its new session say.

`agtermctl` is the first on the PATH of the place's environment, never another: a test puts a
stand-in there. A call names the socket and the window of the session the command runs in
(`AGTERM_SOCKET` and `AGTERM_WINDOW_ID`, or agterm's older `AGT_` names), since agtermctl reads
neither from the environment; a line to a mailbox names no window, which a pane's id already
places. A call agterm refuses is `Unanswered`, with what it said.
"""

import json
import os
import pwd
import shlex
import subprocess
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.ports.terminal import Pane

if TYPE_CHECKING:
    from collections.abc import Mapping

TOOL = "agtermctl"
# How long one call of agtermctl may take. A guess: it answers in milliseconds, and a stuck one
# must not hold a command; the picker waits for the owner, and takes no limit.
TIMEOUT = 30
# The variables agterm gives a session's commands, its own names first.
SOCKETS = ("AGTERM_SOCKET", "AGT_SOCKET")
WINDOWS = ("AGTERM_WINDOW_ID", "AGT_WINDOW_ID")
CALLERS = ("AGTERM_SESSION_ID", "AGT_SESSION_ID")

type Node = dict[str, object]


def named(environ: Mapping[str, str], names: tuple[str, ...]) -> str:
    """The first of the variables `names` that `environ` sets, else an empty text."""
    return next((environ[name] for name in names if environ.get(name)), "")


def ctl(
    environ: Mapping[str, str],
    *words: str,
    window: bool = True,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `agtermctl WORDS` with the place's socket and window; `Unanswered` when it is not on
    the place's PATH or does not end in time. The caller reads its exit."""
    socket = named(environ, SOCKETS)
    shown = named(environ, WINDOWS) if window else ""
    extra = (*(("--socket", socket) if socket else ()), *(("--window", shown) if shown else ()))
    try:
        return subprocess.run(
            [TOOL, *words, *extra],
            env=dict(environ),
            input=stdin,
            capture_output=True,
            text=True,
            timeout=None if stdin is not None else TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        raise Unanswered(TOOL, "not on the PATH: agterm's command line tool") from None
    except subprocess.TimeoutExpired:
        raise Unanswered(TOOL, f"{words[0]} gave no answer in {TIMEOUT} s") from None


def said(environ: Mapping[str, str], *words: str, window: bool = True) -> str:
    """What `agtermctl WORDS` printed; `Unanswered` when it exits other than 0."""
    ran = ctl(environ, *words, window=window)
    if ran.returncode:
        told = (ran.stderr or ran.stdout).strip() or f"exit {ran.returncode}"
        raise Unanswered(TOOL, told)
    return ran.stdout


def nodes_of(printed: str) -> tuple[Node, ...]:
    """The sessions of `agtermctl tree --json`, each with its workspace's id under
    `workspace`; `Unanswered` when it printed no tree."""
    try:
        spaces = json.loads(printed)["result"]["tree"]["workspaces"]
        return tuple(
            {**node, "workspace": str(space["id"])}
            for space in spaces
            for node in space.get("sessions", ())
        )
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise Unanswered(TOOL, f"tree --json printed no tree ({error})") from error


def pane_of(node: Node) -> Pane:
    """A session of the tree as the port gives it."""
    cwd = node.get("cwd")
    return Pane(
        id=str(node["id"]),
        name=str(node.get("name") or ""),
        cwd=cwd if isinstance(cwd, str) else None,
        workspace=str(node["workspace"]),
        selected=bool(node.get("active")),
    )


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
