"""`gathered`: the facts of a proposal that only git shows, and the agent's notes
(`model/landing/propose_facts.py`): the paths the branch changes against its merge base with
the base, Lem's settings as it changes them, the items it adds to the backlog, and which of the
paths `propose` asks about the tip holds."""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.app.landing import propose_items
from lem.kernel.errors import Refusal
from lem.model.landing.propose_careful import LOCAL, TEAM
from lem.model.landing.propose_facts import Facts, Settings
from lem.model.landing.propose_lines import named

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.ports.git import Git
    from lem.records.record import Record


def notes_of(path: str) -> str:
    """The notes the agent wrote for the pull request, from their file."""
    try:
        return Path(path).read_text(encoding=propose_items.UTF8)
    except (OSError, UnicodeDecodeError) as error:
        raise Refusal(
            "notes",
            f"{path} is not a file of text ({error}); --notes names the notes of the pull "
            "request",
            "write the notes into that file, then lem land propose SLUG again",
        ) from error


def tracked(git: Git, where: Path, commit: str) -> bool:
    """Whether one machine's own settings file is in the commit."""
    return git.show(where, commit, LOCAL) is not None


def settings_of(git: Git, where: Path, commits: tuple[str, str]) -> Settings:
    """Lem's settings files at the merge base and at the tip."""
    since, tip = commits
    local = (tracked(git, where, since), tracked(git, where, tip))
    before = propose_items.text(git.show(where, since, TEAM))
    after = propose_items.text(git.show(where, tip, TEAM))
    return Settings(before=before, after=after, local=local)


def asked(record: Record, notes: str) -> set[str]:
    """The paths whose place in the tip `propose` asks about: the items the notes name, the
    items findings were filed as, and the task's own item."""
    landing, own = record.landing, record.task.backlog_item
    filed = landing.filed if landing else ()
    paths = {found.path for found in filed if found.path}
    if own:
        paths.add(own)
    return paths | set(named(notes))


def gathered(context: Context, notes: str) -> Facts:
    """The facts of the proposal of the tip now, with the notes of the file `notes`."""
    git, where = context.ports.git, context.worktree
    commits = span(context)
    changed = git.diff_stat(where, *commits).paths
    written = notes_of(notes)
    return Facts(
        changed=changed,
        settings=settings_of(git, where, commits),
        added=propose_items.added(git, where, commits, changed),
        in_tip=propose_items.held(
            git, where, commits[1], asked(context.record, written)
        ),
        notes=written,
    )


def span(context: Context) -> tuple[str, str]:
    """The branch's merge base with origin's base, and its tip."""
    git, world = context.ports.git, context.world
    tip = world.tip or world.base
    since = git.merge_base(context.worktree, world.base, tip)
    return (since or world.base, tip)
