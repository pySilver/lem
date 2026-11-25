"""The `Terminal` port on agterm, through its command `agtermctl` (the design's part 4).

A session Lem opens is made with `--no-select`, so it never takes the focus, and goes after the
last session of its workspace, so the one the owner keeps first stays first. Its command runs in
the owner's login shell, so that his PATH finds the agent. A workspace not named is the one of
the session the command runs in (`AGTERM_SESSION_ID`), else agterm's own choice. A list agterm
does not give is `Unreadable`; any other call it refuses is `Unanswered`, which names what it
said.

`agtermctl` is the first on the PATH of the place's environment, never another: a test puts a
stand-in there. `show` and `picker` are not built in this slice, and say so by name.
"""

import json
import os
import pwd
import shlex
import subprocess
from typing import TYPE_CHECKING

from lem.kernel.errors import Fault, Refusal
from lem.ports.faults import Unanswered
from lem.ports.terminal import Mark, Opening, Pane, ShowMode, Unreadable

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.ports.place import Place

TOOL = "agtermctl"
SESSION = "session"
TARGET = "--target"
TREE = ("tree", "--json")
# How long one call of agtermctl may take. A guess: it answers in milliseconds, and a stuck one
# must not hold a command.
TIMEOUT = 30
# agterm's status glyph for each mark of the port (`session status`).
GLYPHS = (
    ("working", "active"),
    ("waiting", "blocked"),
    ("done", "completed"),
    ("stopped", "blocked"),
    ("none", "idle"),
)


def ctl(environ: Mapping[str, str], *words: str) -> str:
    """What `agtermctl WORDS` printed, with the place's socket; `Unanswered` when it is not on
    the place's PATH or exits other than 0."""
    socket = environ.get("AGTERM_SOCKET")
    sockets = ("--socket", socket) if socket else ()
    try:
        ran = subprocess.run(
            [TOOL, *words, *sockets],
            env=dict(environ),
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        raise Unanswered(TOOL, "not on the PATH: agterm's command line tool") from None
    if ran.returncode:
        said = (ran.stderr or ran.stdout).strip() or f"exit {ran.returncode}"
        raise Unanswered(TOOL, said)
    return ran.stdout


def panes_of(printed: str) -> tuple[Pane, ...]:
    """The sessions of `agtermctl tree --json`, each with its workspace's id; `Unanswered`
    when it printed no tree."""
    try:
        spaces = json.loads(printed)["result"]["tree"]["workspaces"]
    except (ValueError, KeyError, TypeError) as error:
        raise Unanswered(TOOL, f"tree --json printed no tree ({error})") from error
    return tuple(
        Pane(
            id=str(node["id"]),
            name=str(node.get("name") or ""),
            cwd=node.get("cwd"),
            workspace=str(space["id"]),
            selected=bool(node.get("active")),
        )
        for space in spaces
        for node in space.get("sessions", ())
    )


def login_line(command: tuple[str, ...]) -> str:
    """The command run by the owner's login shell, `SHELL -l -c 'COMMAND'`: each of `command`
    is a line of that shell, and they run joined by spaces."""
    shell = pwd.getpwuid(os.getuid()).pw_shell
    if not shell.startswith("/"):
        raise Refusal(
            "login-shell",
            "the owner's login shell is not known to the system: agterm needs it to find "
            "the agent",
            "the owner sets a login shell at an absolute path (chsh), then runs this again",
        )
    return shlex.join((shell, "-l", "-c", " ".join(command)))


class AgtermSessions:
    """The sessions: list, open, close, a line to one, its mark."""

    def __init__(self, environ: Mapping[str, str]) -> None:
        """Keep the environment the command started with: its PATH, socket and session."""
        self.environ = environ

    def known(self, session: str) -> Pane:
        """The session `session`, or `Unanswered` for one that is gone."""
        listed = panes_of(ctl(self.environ, *TREE))
        found = next((pane for pane in listed if pane.id == session), None)
        if found is None:
            raise Unanswered(TOOL, f"no session {session}")
        return found

    def sessions(self) -> tuple[Pane, ...] | Unreadable:
        """Every session of agterm, or why it could not be read."""
        try:
            return panes_of(ctl(self.environ, *TREE))
        except Unanswered as unanswered:
            return Unreadable(why=unanswered.said)

    def close(self, session: str, *, when_unselected: bool) -> None:
        """Close the session with agterm's undo, but one the owner looks at when told so."""
        if when_unselected and self.known(session).selected:
            return
        self.known(session)
        ctl(self.environ, SESSION, "close", TARGET, session, "--undoable")

    def tell(self, session: str, line: str) -> None:
        """Send `line` to the session's left pane, as mail that waits for its turn's end."""
        self.known(session)
        ctl(self.environ, "msg", "send", line, "--to", f"{session}:left")

    def mark(self, session: str, status: Mark) -> None:
        """Set the session's glyph in agterm's sidebar."""
        self.known(session)
        glyph = dict(GLYPHS)[status]
        ctl(self.environ, SESSION, "status", glyph, TARGET, session)


class AgtermTerminal(AgtermSessions):
    """The whole port; what this slice does not build says so by name."""

    def open(self, opening: Opening) -> str:
        """Open the session with no focus, after the last one of its workspace; its id."""
        place = self.place_of(opening)
        made = ctl(
            self.environ,
            SESSION,
            "new",
            *place,
            "--cwd",
            opening.cwd,
            "--name",
            opening.name,
            "--no-select",
            "--command",
            login_line(opening.command),
            "--json",
        )
        return made_id(made)

    def place_of(self, opening: Opening) -> tuple[str, ...]:
        """Where the new session goes: beside its parent, else after the last session of its
        workspace, else of the workspace of the session this command runs in, else where
        agterm puts a new one. The new session is the last call: nothing more is asked of
        agterm between its making and its record."""
        if opening.companion_of is not None:
            self.known(opening.companion_of)
            return ("--parent", opening.companion_of)
        listed = panes_of(ctl(self.environ, *TREE))
        workspace = opening.workspace or self.callers_workspace(listed)
        if workspace is None:
            return ()
        return ("--workspace", workspace, *self.after_last(listed, workspace))

    def callers_workspace(self, listed: tuple[Pane, ...]) -> str | None:
        """The workspace of the session this command runs in, or None outside agterm."""
        caller = self.environ.get("AGTERM_SESSION_ID", "")
        return next((pane.workspace for pane in listed if pane.id == caller), None)

    def after_last(self, listed: tuple[Pane, ...], workspace: str) -> tuple[str, ...]:
        """`--after` the last session of `workspace`, or nothing for an empty one."""
        ids = [pane.id for pane in listed if pane.workspace == workspace]
        return ("--after", ids[-1]) if ids else ()

    def show(self, session: str, url: str, mode: ShowMode) -> None:
        """Not built in this slice."""
        raise Fault(
            "show: the agterm adapter's slice does not build it; the step sessions does"
        )

    def select(self, session: str) -> None:
        """Select the session: the owner's own act only."""
        self.known(session)
        ctl(self.environ, SESSION, "select", TARGET, session)

    def picker(self, rows: tuple[str, ...], cwd: Path) -> str | None:
        """Not built in this slice."""
        raise Fault(
            "picker: the agterm adapter's slice does not build it; the step addons-flow does"
        )


def made_id(printed: str) -> str:
    """The id of the session `session new --json` made."""
    try:
        return str(json.loads(printed)["result"]["id"])
    except (ValueError, KeyError, TypeError) as error:
        raise Unanswered(
            TOOL, f"session new printed no session id ({error})"
        ) from error


def bind(place: Place) -> AgtermTerminal:
    """The terminal of the place's environment."""
    return AgtermTerminal(place.environ)
