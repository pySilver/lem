"""The two facts of the repository `lem init` needs from git: where origin is, and its default
branch.

A task ends as a pull request on GitHub, the one way Lem lands (the owner's GitHub notes,
2026-11-20: "we can assume that we fully use Github"), so an origin elsewhere is refused and a
repository with no origin yet is told to add one before its first landing. The `Git` port has
no fact of origin's address, so this module asks git itself until it has
(`notes/settings.md`); origin's default branch is read from the file git keeps.
"""

import re
import subprocess
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.settings.base import ORIGIN, symbolic

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

GITHUB = re.compile(r"(https://|ssh://git@|git@)github\.com[:/]")
# A look at git's own configuration takes far less than this (unmeasured estimate).
TIMEOUT = 30


def origin_url(checkout: Path, environ: Mapping[str, str]) -> str | None:
    """The address of origin, None when the repository has none."""
    ran = subprocess.run(
        ["git", "-C", str(checkout), "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        env=dict(environ),
        timeout=TIMEOUT,
        check=False,
    )
    return ran.stdout.strip() or None


def on_github(url: str | None) -> None:
    """Refuse an origin that is not on GitHub."""
    if url and not GITHUB.match(url):
        raise Refusal(
            "not-github",
            f"origin is {url}, and Lem lands through GitHub pull requests only",
            "point origin at the repository on GitHub "
            "(git remote set-url origin git@github.com:OWNER/REPO.git), then run init again",
        )


def default_branch(checkout: Path) -> str | None:
    """Origin's default branch, as git's `origin/HEAD` names it; None when it names none."""
    head = checkout / ".git" / "refs/remotes/origin/HEAD"
    return symbolic(head, ORIGIN)
