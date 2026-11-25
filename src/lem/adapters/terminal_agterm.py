"""The `Terminal` port on agterm, through its command `agtermctl` (the design's part 4).

A session Lem opens is made with `--no-select`, so it never takes the focus, and goes after the
last session of its workspace in the one `session new`, so the one the owner keeps first stays
first and nothing more is asked of agterm between a session's making and its record. Its command
runs in the owner's login shell, so that his PATH finds the agent. A workspace not named is
agterm's own choice: the use case names one (`app/sessions/placing.py`). A page is shown as a
companion of the session or in its overlay, never by selecting it; only the owner's own act
selects a session. The picker waits for the owner's answer and gives the row he chose.
"""

import json
from typing import TYPE_CHECKING

from lem.adapters.agterm_ctl import TOOL, ctl, login_line, nodes_of, said
from lem.adapters.agterm_sessions import SESSION, TARGET, TREE, AgtermLooks
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.place import Place
    from lem.ports.terminal import Opening, ShowMode

# The flags of `session overlay open` for each way the port shows a page: a page companion
# beside the session, its overlay, or an overlay whose page may leave the site it opened.
SHOWN = (
    ("companion", ("--companion",)),
    ("overlay", ()),
    ("browser", ("--browse", "--navigation")),
)
# The exit of `agtermctl pick` when the owner closes the picker (`picker.CLOSED` on `main`).
CLOSED = 2


class AgtermTerminal(AgtermLooks):
    """The whole port, and the looks beside it."""

    def open(self, opening: Opening) -> str:
        """Open the session with no focus, after the last one of its workspace; its id."""
        made = said(
            self.environ,
            SESSION,
            "new",
            *self.place_of(opening),
            "--cwd",
            opening.cwd,
            "--name",
            opening.name,
            "--no-select",
            "--command",
            login_line(opening.command),
            "--json",
        )
        return made_id(made, "session new")

    def place_of(self, opening: Opening) -> tuple[str, ...]:
        """Where the new session goes: beside its parent, else after the last session of the
        workspace named, else where agterm puts a new one."""
        if opening.companion_of is not None:
            parent = str(self.node(opening.companion_of)["id"])
            return ("--parent", parent)
        if opening.workspace is None:
            return ()
        nodes = nodes_of(said(self.environ, *TREE))
        ids = [str(node["id"]) for node in nodes if node["workspace"] == opening.workspace]
        after = ("--after", ids[-1]) if ids else ()
        return ("--workspace", opening.workspace, *after)

    def show(self, session: str, url: str, mode: ShowMode) -> None:
        """Show the page at `url` for the session, with no change of what the owner looks at."""
        target = str(self.node(session)["id"])
        flags = dict(SHOWN)[mode]
        said(self.environ, SESSION, "overlay", "open", "--url", url, "--js", *flags, TARGET, target)

    def select(self, session: str) -> None:
        """Select the session: the owner's own act only."""
        target = str(self.node(session)["id"])
        said(self.environ, SESSION, "select", TARGET, target)

    def picker(self, rows: tuple[str, ...], cwd: Path) -> str | None:
        """The row the owner picked in agterm's picker, or None when he closed it."""
        ran = ctl(self.environ, "pick", "--prompt", "Open the board of a task", stdin="\n".join(rows))
        if ran.returncode == CLOSED:
            return None
        if ran.returncode:
            told = (ran.stderr or ran.stdout).strip() or f"exit {ran.returncode}"
            raise Unanswered(TOOL, told)
        return picked(ran.stdout, rows)


def made_id(printed: str, call: str) -> str:
    """The id of the session `call` made, from its `--json` answer."""
    try:
        return str(json.loads(printed)["result"]["id"])
    except (ValueError, KeyError, TypeError) as error:
        raise Unanswered(TOOL, f"{call} printed no session id ({error})") from error


def picked(printed: str, rows: tuple[str, ...]) -> str | None:
    """The row of the picker's answer, None for any answer but a pick; `Unanswered` for an
    answer that is no JSON or names no row."""
    try:
        answer = json.loads(printed)
    except ValueError as error:
        raise Unanswered(TOOL, f"pick printed no JSON ({error})") from error
    if not isinstance(answer, dict) or answer.get("result") != "picked":
        return None
    chosen = str(answer.get("id", ""))
    if chosen not in rows:
        raise Unanswered(TOOL, f"pick answered a row it was not given: {chosen!r}")
    return chosen


def bind(place: Place) -> AgtermTerminal:
    """The terminal of the place's environment."""
    return AgtermTerminal(place.environ)
