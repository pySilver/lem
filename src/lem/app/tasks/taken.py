"""A new task's branch that origin has already, refused before the task's record is written
(`project.taken_on_remote` on `main`): somebody's work, or a task of another machine.

The name is the one `--branch` gives, else TYPE/SLUG for every type a task takes, since the type
comes with the read, after the open. Origin is asked once, by a fetch; one that does not answer
checks nothing, and the open says so in its line.
"""

from typing import TYPE_CHECKING

from lem.app.tasks import ports
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.store.places import Workspace

TYPES = ("feat", "fix", "docs", "refactor", "perf", "test", "chore", "question")


def names(slug: str, branch: str | None) -> tuple[str, ...]:
    """The branches a new task may take."""
    if branch is not None:
        return (branch,)
    return tuple(f"{kind}/{slug}" for kind in TYPES)


def checked(where: Workspace, slug: str, branch: str | None) -> str | None:
    """Refuse a branch origin has; give the line to say when origin did not answer."""
    git = ports.bound(where).git
    try:
        git.fetch(where.checkout)
    except Unanswered as error:
        said = error.said
        return f"origin did not answer ({said}), so nothing checked that {slug} has no branch there"
    there = [
        name for name in names(slug, branch) if git.remote_head(where.checkout, name)
    ]
    if not there:
        return None
    other = ", or give another --branch" if branch else ""
    raise Refusal(
        "branch-taken",
        f"origin has the branch {there[0]} already, and no task here holds it: somebody's "
        "work, or a task of another machine",
        f"a new task takes a branch of its own: add a word to the slug{other}",
    )
