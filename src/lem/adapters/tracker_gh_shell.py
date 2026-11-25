"""How the GitHub tracker runs `gh`: one process for each call, in the main checkout, with no
prompt, and every call of an issue naming origin's repository with `--repo OWNER/REPO`, read from
`remote.origin.url`, so a fork whose `gh` default is its upstream still reads its own issues.

The flags were read from gh's `--help` in gh 2.101.0 (2026-09-15), on 2026-11-22.
"""

import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.adapters.forge_gh_shell import TIMEOUT, cleaned, last_words
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

GH = "gh"
# Origin on GitHub, in the three forms git takes, as OWNER/REPO.
ORIGIN = re.compile(
    r"(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)"
    r"(?P<repo>[^/\s:]+/[^/\s]+?)(?:\.git)?/?"
)
INSTALL = (
    "install GitHub's command gh (https://cli.github.com), then sign it in with "
    "gh auth login"
)
SET_ORIGIN = "git remote set-url origin https://github.com/OWNER/REPO.git"


def origin_of(url: str) -> str | None:
    """`OWNER/REPO` of an origin's address on GitHub, or None."""
    found = ORIGIN.fullmatch(url)
    return found["repo"] if found else None


@dataclass(frozen=True, kw_only=True)
class GhRun:
    """The main checkout `gh` runs in, and the environment of the call."""

    checkout: Path
    environ: Mapping[str, str]

    def where(self) -> str | None:
        """The path of `gh` on the call's PATH, or None."""
        return shutil.which(GH, path=self.environ.get("PATH"))

    def tried(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        """`gh ARGS` in the main checkout, whatever its exit code; refused when no gh is on
        PATH."""
        found = self.where()
        if found is None:
            raise Refusal(
                "no-gh", "gh is not on PATH", f"{INSTALL}, then run this again"
            )
        environ = {**cleaned(self.environ), "GH_PROMPT_DISABLED": "1"}
        try:
            return subprocess.run(
                [found, *args],
                cwd=self.checkout,
                capture_output=True,
                text=True,
                input=stdin,
                env=environ,
                timeout=TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Unanswered(GH, str(error)) from error

    def said(self, *args: str, stdin: str = "") -> str:
        """The output of `gh ARGS`; a failure is `Unanswered` with gh's last words."""
        ran = self.tried(*args, stdin=stdin)
        if ran.returncode:
            raise Unanswered(GH, last_words(ran))
        return ran.stdout

    def origin_url(self) -> str:
        """The address `remote.origin.url` names, or an empty text."""
        ran = subprocess.run(
            ["git", "-C", str(self.checkout), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            env=cleaned(self.environ),
            check=False,
        )
        return ran.stdout.strip()

    def origin(self) -> str:
        """`OWNER/REPO` of origin; refused with no origin, or one that is not on GitHub."""
        url = self.origin_url()
        if not url:
            raise Refusal(
                "no-origin",
                "this repository has no origin, and Lem reads the issues of origin's "
                "repository on GitHub",
                "add it (git remote add origin https://github.com/OWNER/REPO.git), "
                "then run this again",
            )
        repo = origin_of(url)
        if repo is None:
            raise Refusal(
                "not-github",
                f"origin is {url}, which is not a repository on GitHub, and Lem reads "
                "the issues of origin",
                f"point origin at the repository on GitHub ({SET_ORIGIN}), then run "
                "this again",
            )
        return repo
