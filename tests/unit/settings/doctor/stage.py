"""A machine for `lem doctor` in a test's own folder: a home, a PATH of stand-in programs,
Homebrew's prefixes, an app's Python and repositories made of the files git keeps.

No row of a test looks at the owner's home, his tools or his agterm: the look names this folder
for each. The connections a row may make are stand-ins: cronn's status records the port it was
asked for, and a joined machine's board answers from `boards`.
"""

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.cli.doctor.look import Look

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.cli.doctor.row import Row

EXECUTABLE = 0o755
MAILBOX_EVENTS = ("SessionStart", "Stop", "UserPromptSubmit")


@dataclass
class Stage:
    """A machine in `root`: its home, its PATH folder, its app and its Homebrew."""

    root: Path
    asked: list[int] = field(default_factory=list)
    answering: bool = False
    extra: dict[str, str] = field(default_factory=dict)
    boards: dict[str, tuple[bool | None, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Make the folders."""
        for folder in (self.home, self.bin, self.app / "bin", self.config, self.work):
            folder.mkdir(parents=True, exist_ok=True)

    @property
    def home(self) -> Path:
        """The user's home."""
        return self.root / "home"

    @property
    def config(self) -> Path:
        """XDG_CONFIG_HOME; Lem's home folder is `lem` in it."""
        return self.root / "config"

    @property
    def lem_home(self) -> Path:
        """Lem's home folder."""
        return self.config / "lem"

    @property
    def bin(self) -> Path:
        """The one folder of the PATH."""
        return self.root / "bin"

    @property
    def app(self) -> Path:
        """The app's environment: its Python and its commands are in `bin`."""
        return self.root / "app"

    @property
    def brew(self) -> Path:
        """A Homebrew prefix."""
        return self.root / "brew"

    @property
    def work(self) -> Path:
        """The folder of the call, in no repository."""
        return self.root / "work"

    def tool(self, name: str, said: str | None = None, code: int = 0) -> Path:
        """A stand-in program on the PATH that prints `said` and exits `code`."""
        return script(self.bin / name, said or f"{name} 1.0", code)

    def status(self, port: int) -> bool:
        """The stand-in of cronn's status: records the port, answers as told."""
        self.asked.append(port)
        return self.answering

    def peer_live(self, name: str, port: int) -> tuple[bool | None, str]:
        """The stand-in of a joined machine's board: whether its agterm runs Live sessions."""
        return self.boards.get(name, (None, f"no board answers at {name}:{port}"))

    def look(self, folder: Path | None = None, **environ: str) -> Look:
        """The look of a call from `folder` (the work folder when None)."""
        given = {
            "HOME": str(self.home),
            "PATH": str(self.bin),
            "XDG_CONFIG_HOME": str(self.config),
            **self.extra,
            **environ,
        }
        return Look(
            environ=given,
            home=self.home,
            folder=folder or self.work,
            executable=self.app / "bin" / "python",
            prefix=self.app,
            brews=(self.brew,),
            status=self.status,
            peer_live=self.peer_live,
        )

    def write(self, relative: str, text: str) -> Path:
        """A file under the root."""
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def plugins(self, listed: object) -> None:
        """Claude Code's list of installed plugins in the home, as JSON."""
        self.write("home/.claude/plugins/installed_plugins.json", json.dumps(listed))

    def mailbox_settings(
        self,
        relative: str = "home/.claude/settings.json",
        *,
        events: tuple[str, ...] = MAILBOX_EVENTS,
        hook_fields: Mapping[str, object] | None = None,
    ) -> Path:
        """The cookbook's mailbox hook in the user's Claude Code settings."""
        hook = {
            "type": "command",
            "command": "mailbox-chat.py claude-hook",
            "asyncRewake": True,
            **(hook_fields or {}),
        }
        return self.write(
            relative,
            json.dumps({"hooks": {event: [{"hooks": [hook]}] for event in events}}),
        )

    def repository(self, name: str = "repo", *, lem: bool = True) -> Path:
        """A main checkout: a `.git` folder, and Lem set up when `lem`."""
        checkout = self.root / name
        (checkout / ".git").mkdir(parents=True, exist_ok=True)
        if lem:
            (checkout / ".lem").mkdir(exist_ok=True)
            (checkout / ".lem" / "settings.toml").write_text("", encoding="utf-8")
        return checkout

    def worktree(self, checkout: Path, slug: str) -> Path:
        """A task's worktree of `checkout`, as git keeps it."""
        admin = checkout / ".git" / "worktrees" / slug
        admin.mkdir(parents=True, exist_ok=True)
        (admin / "commondir").write_text("../..\n", encoding="utf-8")
        tree = checkout / ".lem" / "worktrees" / slug
        tree.mkdir(parents=True, exist_ok=True)
        (tree / ".git").write_text(f"gitdir: {admin}\n", encoding="utf-8")
        return tree


def script(path: Path, said: str, code: int = 0) -> Path:
    """A shell script at `path` that prints `said` and exits `code`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\necho '{said}'\nexit {code}\n", encoding="utf-8")
    path.chmod(EXECUTABLE)
    return path


def named(rows: tuple[Row, ...], name: str) -> Row:
    """The one row called `name`."""
    found = [row for row in rows if row.name == name]
    assert len(found) == 1, (name, [row.name for row in rows])
    return found[0]


def names(rows: tuple[Row, ...]) -> list[str]:
    """The name of each row."""
    return [row.name for row in rows]
