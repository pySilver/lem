"""The `Terminal` port on agterm, through its command `agtermctl` (the design's part 4).

A session Lem opens is made with `--no-select`, so it never takes the focus, and goes after the
last session of its workspace in the one `session new` (`--after` that session, whose workspace
it takes; agterm refuses `--after` beside `--workspace`, so an empty workspace is named alone),
so the one the owner keeps first stays first and nothing more is asked of agterm between a
session's making and its record. Its command
runs in the owner's login shell, so that his PATH finds the agent. A workspace not named is
agterm's own choice: the use case names one (`app/sessions/placing.py`). A page is shown as a
companion of the session or in its overlay, never by selecting it; only the owner's own act
selects a session. The picker waits for the owner's answer and gives the row he chose.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.agterm_ctl import SOCKETS, TOOL, ctl, login_line, said
from lem.adapters.agterm_sessions import SESSION, TARGET, AgtermLooks
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.ports.place import Place
    from lem.ports.terminal import Opening, PickRow, ShowMode

# The flags of `session overlay open` for each way the port shows a page: a page companion
# beside the session, its overlay, or an overlay whose page may leave the site it opened.
SHOWN = (
    ("companion", ("--companion",)),
    ("overlay", ()),
    ("browser", ("--browse", "--navigation")),
)
# The scheme of a page that is a local file: agterm shows it with `--html`, and takes `--url` for an
# http or https address only (`--url must be an absolute http or https URL`, lem.log of
# 2026-11-27).
LOCAL_SCHEME = "file:"
# The exit of `agtermctl pick` when the owner closes the picker (`picker.CLOSED` on `main`).
CLOSED = 2
# The session a command runs in, as agterm names it in each pane's environment: its own name,
# then its older one.
CALLERS = ("AGTERM_SESSION_ID", "AGT_SESSION_ID")


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
            return ("--parent", self.node(opening.companion_of).id)
        space = opening.workspace
        if space is None:
            return ()
        ids = [node.id for node in self.nodes() if node.workspace == space]
        return ("--after", ids[-1]) if ids else ("--workspace", space)

    def show(self, session: str, url: str, mode: ShowMode) -> None:
        """Show the page at `url` for the session, with no change of what the owner looks at."""
        target = self.node(session).id
        flags = dict(SHOWN)[mode]
        said(
            self.environ,
            SESSION,
            "overlay",
            "open",
            *page_words(url),
            "--js",
            *flags,
            TARGET,
            target,
        )

    def select(self, session: str) -> None:
        """Select the session: the owner's own act only."""
        target = self.node(session).id
        said(self.environ, SESSION, "select", TARGET, target)

    def here(self) -> str | None:
        """The session the command runs in, from its pane's environment; None outside agterm."""
        named = (self.environ.get(name, "") for name in CALLERS)
        return next((one for one in named if one), None)

    def picker(self, rows: tuple[PickRow, ...], cwd: Path) -> str | None:
        """The id the owner picked in agterm's picker, or None when he closed it."""
        callers = (self.environ.get(name, "").strip() for name in CALLERS)
        sockets = (self.environ.get(name) for name in SOCKETS)
        if not any(callers) or not any(sockets):
            raise Unanswered(TOOL, "the owner opens the picker from an agterm session")
        ran = ctl(
            self.environ,
            "pick",
            "--prompt",
            "Open the board of a task",
            stdin=msgspec.json.encode(rows).decode(),
        )
        if ran.returncode == CLOSED:
            return None
        if ran.returncode:
            told = (ran.stderr or ran.stdout).strip() or f"exit {ran.returncode}"
            raise Unanswered(TOOL, told)
        return picked(ran.stdout, rows)


def page_words(url: str) -> tuple[str, ...]:
    """The words of `session overlay open` that name the page at `url`: a local file by its
    path, with read access to its folder, so that it reads the `lem.css` and `lem.js` beside
    it; any other page, the board server's, by its address, with agterm's saved store of
    cookies, so that the board's folded columns outlive a relaunch of agterm."""
    if not url.startswith(LOCAL_SCHEME):
        return ("--url", url, "--persistent")
    page = Path.from_uri(url)
    return ("--html", str(page), "--cwd", str(page.parent))


def made_id(printed: str, call: str) -> str:
    """The id of the session `call` made, from its `--json` answer."""
    try:
        return str(json.loads(printed)["result"]["id"])
    except (ValueError, KeyError, TypeError) as error:
        raise Unanswered(TOOL, f"{call} printed no session id ({error})") from error


def picked(printed: str, rows: tuple[PickRow, ...]) -> str | None:
    """The row of the picker's answer, None for any answer but a pick; `Unanswered` for an
    answer that is no JSON or names no row."""
    try:
        answer = json.loads(printed)
    except ValueError as error:
        raise Unanswered(TOOL, f"pick printed no JSON ({error})") from error
    if not isinstance(answer, dict) or answer.get("result") != "picked":
        return None
    chosen = str(answer.get("id", ""))
    if not any(row.row_id == chosen for row in rows):
        raise Unanswered(TOOL, f"pick answered a row it was not given: {chosen!r}")
    return chosen


def bind(place: Place) -> AgtermTerminal:
    """The terminal of the place's environment."""
    return AgtermTerminal(place.environ)
