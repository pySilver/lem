"""The items `file` writes, and their commits, one for each review round, in a worktree that was
clean (`land.cmd_file` on `main`). A commit hook of the project may refuse the message, which
has Lem's form: the items stay written and staged, a builder commits them in the project's form,
and the next run finds each item by its defect."""

import shlex
from typing import TYPE_CHECKING

from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.ports.git_facts import GitRefused

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.filing_place import Write


def hook_refused(
    context: Context, number: int, paths: tuple[str, ...], said: str
) -> Refusal:
    """The refusal of a commit the project's hook refused, with its words."""
    slug = context.record.task.slug
    retry = shlex.join(
        ("git", "-C", str(context.worktree), "commit", "-m", "MESSAGE", "--", *paths)
    )
    return Refusal(
        "commit",
        f"the commit of the backlog items of review round {number} was refused, most likely "
        f"by a commit hook of the project: {said}",
        f"the items are written and staged. A builder runs `{retry}` with a message in the "
        f"form the hook asks for, never with --no-verify. Then `lem land file {slug}` "
        "finds each item by its defect",
    )


def wrote(context: Context, writes: tuple[Write, ...]) -> tuple[str, ...]:
    """Write each item into the worktree; the paths written."""
    for pending in writes:
        path = context.worktree / pending.path
        path.parent.mkdir(parents=True, exist_ok=True)
        files.write_whole(path, pending.text.encode())
    return tuple(each.path for each in writes)


def commit_round(context: Context, writes: tuple[Write, ...], number: int) -> None:
    """Commit one review round's items alone; a refusal of git's is refused in its words."""
    slug = context.record.task.slug
    paths = tuple(write.path for write in writes if write.round == number)
    message = f"docs(backlog): what review round {number} saw outside {slug}"
    made = context.ports.git.commit(context.worktree, message, paths)
    if isinstance(made, GitRefused):
        raise hook_refused(context, number, paths, made.said)


def committed(context: Context, writes: tuple[Write, ...]) -> tuple[str, ...]:
    """Write and commit the items, one commit per review round, and give their paths."""
    written = wrote(context, writes)
    for number in sorted({each.round for each in writes}):
        commit_round(context, writes, number)
    return written
