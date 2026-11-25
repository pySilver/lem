"""Which text of the team's file counts: the main checkout's working tree while it is on the
base branch, else the base branch's newest commit.

The developer's own edit in the main checkout is his act, and counts at once. Another branch
checked out there is no rule for the tasks that run (audit M-F5, 2026-11-17: `gh pr checkout 57`
in the main checkout changed `branch.land` and the topics for every task), so then the file is
read as the base has it, through the `Git` port's `show`. Before any commit of the base holds the
file (an onboarding), the working tree's counts. The branch the checkout is on and origin's
default branch are read from the files git keeps, with no git started, since every command reads
the settings.
"""

import os
import tomllib
from typing import TYPE_CHECKING

from lem.adapters.git_cli import GitCli
from lem.settings import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import GitPlaces

REF = "ref: refs/heads/"
ORIGIN = "ref: refs/remotes/origin/"


def symbolic(path: Path, prefix: str) -> str | None:
    """The branch a symbolic ref file names after `prefix`; None when it names none."""
    try:
        said = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return said.removeprefix(prefix) if said.startswith(prefix) else None


def named_base(body: bytes | None) -> str | None:
    """The `branch.base` a text of the team's file names; None when it names none or does
    not read, which the load refuses itself."""
    try:
        branch = tomllib.loads((body or b"").decode("utf-8")).get("branch", {})
    except tomllib.TOMLDecodeError, UnicodeDecodeError:
        return None
    base = branch.get("base") if isinstance(branch, dict) else None
    return base if isinstance(base, str) and base.strip() else None


def bases(checkout: Path, working: bytes | None) -> tuple[str, ...]:
    """The branches that may be the base: origin's default, then the one the working tree's
    file names, each once."""
    git = checkout / ".git"
    found = (symbolic(git / "refs/remotes/origin/HEAD", ORIGIN), named_base(working))
    return tuple(dict.fromkeys(branch for branch in found if branch))


def team_text(checkout: Path, git: GitPlaces | None = None) -> tuple[bytes | None, str]:
    """The text of the team's file that counts for `checkout`, None when there is none, and
    its name for a message: `.lem/settings.toml`, or `BASE:.lem/settings.toml`."""
    path = checkout / places.TEAM
    working = path.read_bytes() if path.is_file() else None
    own = places.TEAM.as_posix()
    head = symbolic(checkout / ".git" / "HEAD", REF)
    candidates = bases(checkout, working)
    if not candidates or head in candidates:
        return working, own
    shown = git or GitCli(environ=os.environ)
    for branch in candidates:
        body = shown.show(checkout, f"refs/heads/{branch}", own)
        if body is not None:
            return body, f"{branch}:{own}"
    return working, own
