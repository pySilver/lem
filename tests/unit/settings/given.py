"""A checkout and a home folder for the cases of the settings: the four files written as a case
names them, and the environment that points at the home."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.kernel import folders
from lem.settings import load
from lem.settings.places import HOME, LOCAL, MACHINE, TEAM

if TYPE_CHECKING:
    from pathlib import Path

    from lem.settings.load import Loaded


@dataclass(frozen=True, kw_only=True)
class Given:
    """A main checkout on `main` (its `.git` as git keeps it), and Lem's home folder."""

    root: Path

    @property
    def checkout(self) -> Path:
        return self.root / "checkout"

    @property
    def home(self) -> Path:
        return self.root / "config" / "lem"

    @property
    def environ(self) -> dict[str, str]:
        return {
            "HOME": str(self.root),
            "XDG_CONFIG_HOME": str(self.root / "config"),
            "PATH": str(self.root / "bin"),
        }

    def write(
        self,
        team: str | None = None,
        local: str | None = None,
        home: str | None = None,
        machine: str | None = None,
    ) -> Given:
        """Write each file the case names; `team` "" is an empty team's file."""
        if home is not None or machine is not None:
            folders.home_marked(self.home)
        git = self.checkout / ".git"
        git.mkdir(parents=True, exist_ok=True)
        (git / "HEAD").write_text("ref: refs/heads/main\n")
        for path, text in (
            (self.checkout / TEAM, team),
            (self.checkout / LOCAL, local),
            (self.home / HOME, home),
            (self.home / MACHINE, machine),
        ):
            if text is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
        return self

    def loaded(self) -> Loaded:
        """The settings in force for the checkout."""
        return load.settings_of(self.checkout, self.environ)


def given(root: Path, **files: str) -> Given:
    """A checkout with a team's file (empty unless named) and the other files named."""
    return Given(root=root).write(**({"team": ""} | files))


def slug(value: object) -> str:
    """A case's id of one parameter: its words in lower case, joined by hyphens."""
    words = re.findall(r"[a-z0-9]+", str(value).lower())
    return "-".join(words)[:40]
