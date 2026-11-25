"""Which text of the team's file counts: the main checkout's working tree while it is on the
base branch, else the base branch's newest commit.

The developer's own edit in the main checkout is his act, and counts at once. Another branch
checked out there is no rule for the tasks that run (audit M-F5, 2026-11-17: `gh pr checkout 57`
in the main checkout changed `branch.land` and the topics for every task), so then the file is
read as the base has it, through the `Git` port's `show`. The base is the one the committed file
names, read first from origin's default branch, so that a branch checked out there cannot name
itself the base (`project.committed_settings` on `main`). Before any commit of the base holds the
file (an onboarding), the working tree's counts. The branch the checkout is on and origin's
default branch are read from the files git keeps, with no git started, since every command reads
the settings.
"""

import os
import re
import tomllib
from typing import TYPE_CHECKING

from lem.adapters.git_cli import GitCli
from lem.kernel.errors import Refusal
from lem.settings import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import GitFacts

REF = "ref: refs/heads/"
ORIGIN = "ref: refs/remotes/origin/"
OWN = places.TEAM.as_posix()
HEADS = "refs/heads/"
# The digits of a commit that a name shows.
SHORT = 9
# The name of the base's committed file: BASE@COMMIT:.lem/settings.toml.
READ_FROM = re.compile(rf"(\S+)@[0-9a-f]*:{re.escape(OWN)}")


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
    text = (body or b"").decode("utf-8", errors="replace")
    try:
        branch = tomllib.loads(text).get("branch", {})
    except tomllib.TOMLDecodeError:
        return None
    base = branch.get("base") if isinstance(branch, dict) else None
    return base if isinstance(base, str) and base.strip() else None


def bases(checkout: Path, working: bytes | None) -> tuple[str, ...]:
    """The branches that may be the base: origin's default, then the one the working tree's
    file names, each once."""
    git = checkout / ".git"
    found = (symbolic(git / "refs/remotes/origin/HEAD", ORIGIN), named_base(working))
    return tuple(dict.fromkeys(branch for branch in found if branch))


def team_text(checkout: Path, git: GitFacts | None = None) -> tuple[bytes | None, str]:
    """The text of the team's file that counts for `checkout`, None when there is none, and
    its name: `.lem/settings.toml`, or `BASE@COMMIT:.lem/settings.toml` for the base's."""
    path = checkout / places.TEAM
    working = path.read_bytes() if path.is_file() else None
    candidates = bases(checkout, working)
    if not candidates:
        return working, OWN
    found = committed(checkout, candidates, git or GitCli(environ=os.environ))
    head = symbolic(checkout / ".git" / "HEAD", REF)
    if found is None or head == branch_of(found[1]):
        return working, OWN
    return found


def committed(
    checkout: Path, candidates: tuple[str, ...], git: GitFacts
) -> tuple[bytes, str] | None:
    """The team's file as the base has it: the first of `candidates` whose newest commit holds
    the file, followed to the base that file names; None when no candidate holds it (an
    onboarding)."""
    for start in candidates:
        body = git.show(checkout, f"{HEADS}{start}", OWN)
        if body is not None:
            return followed(checkout, (start, body), git)
    return None


def followed(
    checkout: Path, found: tuple[str, bytes], git: GitFacts
) -> tuple[bytes, str]:
    """The file of the base that the file `found` (its branch, its bytes) names; refused when
    that base holds none, since the base's own file is the one Lem reads."""
    start, body = found
    named = named_base(body) or start
    if named != start:
        body = git.show(checkout, f"{HEADS}{named}", OWN)
    if body is None:
        raise Refusal(
            "settings-base",
            f"{start}:{OWN} names {named!r} as branch.base, and {named} holds no {OWN}",
            f"commit {OWN} on {named}, or name the base that holds it in {start}'s file",
        )
    tip = git.tip(checkout, f"{HEADS}{named}") or ""
    short = tip[:SHORT]
    return body, f"{named}@{short}:{OWN}"


def branch_of(said: str) -> str | None:
    """The base a name of the team's file, or a refusal that opens with it, says the file was
    read from; None for the working tree's."""
    found = READ_FROM.match(said)
    return found[1] if found else None
