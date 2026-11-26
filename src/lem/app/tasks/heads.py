"""The branch a task's worktree is cut on, and the branch one that is there is on
(`project.cmd_worktree` on `main`).

A branch the main checkout has already (a task whose worktree was removed) is taken as it is, with
no fetch. A new one is cut from origin's base after a fetch; when origin does not answer, from the
local base as it is now, which the command says. A worktree that is there must be on the task's
branch: the landing reads the branch its HEAD names.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.ports.git_facts import GitRefused

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.wiring import Ports

HEADS = "refs/heads/"
# A branch to cut, and the start it is cut from.
type Todo = tuple[str, str]


def text(path: Path) -> str:
    """A file git keeps, stripped; empty when it does not read."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def branch_on(worktree: Path) -> str | None:
    """The branch the worktree's HEAD names, read from the files git keeps; None when it is
    detached or does not read."""
    named = text(worktree / ".git").removeprefix("gitdir:").strip()
    if not named:
        return None
    ref = text(worktree / named / "HEAD").removeprefix("ref:").strip()
    return ref.removeprefix(HEADS) if ref.startswith(HEADS) else None


def on_branch(worktree: Path, branch: str) -> None:
    """Refuse a worktree that is there on another branch than the task's."""
    found = branch_on(worktree)
    if found == branch:
        return
    on = found or "no branch"
    raise Refusal(
        "worktree-branch",
        f"{worktree} is a worktree on {on}, not on {branch}: the task's worktree is the one "
        "on its branch",
        f"check it out on {branch}, or give --branch {on}",
    )


def taken_refusal(branch: str) -> Refusal:
    """The refusal of a new branch origin has, which no task here holds."""
    return Refusal(
        "branch-taken",
        f"origin has the branch {branch} already, and no task here holds it: somebody's "
        "work, or a task of another machine",
        "a task takes a branch of its own: add a word to the slug, or give another --branch",
    )


def fetched(given: Ports, checkout: Path, start: str) -> tuple[str, str | None]:
    """Fetch origin; with no answer, the local base in place of origin's, and the line that
    says so."""
    try:
        given.git.fetch(checkout)
    except Unanswered as error:
        local = start.removeprefix("origin/")
        said = error.said
        return (
            local,
            f"origin did not answer ({said}), so the branch starts from {local}",
        )
    return start, None


def cut(given: Ports, checkout: Path, path: Path, todo: Todo) -> str | None:
    """Add the worktree at `path` on the branch `todo` names, cut from its start (origin's
    base unless asked); give the line to say when origin did not answer."""
    branch, start = todo
    if given.git.tip(checkout, HEADS + branch) is not None:
        given.git.worktree_add(checkout, path, branch, branch)
        return None
    start, said = fetched(given, checkout, start)
    if said is None and given.git.remote_head(checkout, branch) is not None:
        raise taken_refusal(branch)
    given.git.worktree_add(checkout, path, branch, start)
    return said


def fresh(given: Ports, checkout: Path, todo: Todo) -> None:
    """Reserve a resume's own branch with Git's create-only operation."""
    branch, start = todo
    start, said = fetched(given, checkout, start)
    if said is None and given.git.remote_head(checkout, branch) is not None:
        raise taken_refusal(branch)
    made = given.git.branch_add(checkout, branch, start)
    if isinstance(made, GitRefused):
        error = made.said
        raise Refusal(
            "branch-taken",
            f"git could not make the resume's branch {branch} from {start}: {error}",
            "correct the Git error for that branch, then run the resume again",
        )
