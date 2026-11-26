"""`gathered`: the facts of a proposal that only git shows, and the agent's notes
(`model/landing/propose_facts.py`): the paths the branch changes against its merge base with
the base, Lem's settings as it changes them, the items it adds to the backlog, and which of the
paths `propose` asks about the tip holds."""

from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import backlog, bar_range, propose_items
from lem.kernel.errors import Refusal
from lem.model.landing.careful import LOCAL_SETTINGS_FILE, SETTINGS_FILE
from lem.model.landing.propose_facts import Facts, Settings
from lem.model.landing.propose_lines import named

PATH = attrgetter("path")

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
    return git.show(where, commit, LOCAL_SETTINGS_FILE) is not None


def settings_of(git: Git, where: Path, commits: tuple[str, str]) -> Settings:
    """Lem's settings files at the merge base and at the tip."""
    since, tip = commits
    local = (tracked(git, where, since), tracked(git, where, tip))
    before = propose_items.text(git.show(where, since, SETTINGS_FILE))
    after = propose_items.text(git.show(where, tip, SETTINGS_FILE))
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
    commits = span(context)
    written = notes_of(notes)
    paths = asked(context.record, written)
    heads = propose_items.held(context.ports.git, context.worktree, commits[1], paths)
    facts = replace(
        branch(context, commits),
        heads=heads,
        notes=written,
        bar_read=bar_range.saved(context, commits),
    )
    return replace(facts, in_tip=frozenset(map(PATH, heads)))


def branch(context: Context, commits: tuple[str, str]) -> Facts:
    """What the branch changes against its merge base: its paths, Lem's settings and the
    items it adds."""
    git, where = context.ports.git, context.worktree
    changed = git.diff_stat(where, *commits).paths
    added = propose_items.added(git, where, commits, changed)
    under = (
        backlog.read_at(git, where, commits[1], filing.path)
        for filing in added
        if filing.worth == "no"
    )
    return Facts(
        changed=changed,
        settings=settings_of(git, where, commits),
        added=added,
        under=tuple(filter(None, under)),
    )


def span(context: Context) -> tuple[str, str]:
    """The branch's merge base with origin's base, and its tip."""
    git, world = context.ports.git, context.world
    tip = world.tip or world.base
    since = git.merge_base(context.worktree, world.base, tip)
    return (since or world.base, tip)
