"""`gathered`: the facts of a proposal that only git shows, and the agent's notes
(`model/landing/propose_facts.py`): the paths the branch changes against its merge base with
the base, Lem's settings as it changes them, the items it adds to the backlog with their head
at the tip, and which of the paths `propose` asks about the tip holds."""

from pathlib import Path
from typing import TYPE_CHECKING

import frontmatter

from lem.kernel.errors import Refusal
from lem.model.landing.propose_careful import LOCAL, TEAM
from lem.model.landing.propose_facts import BACKLOG, Facts, Filing, Settings
from lem.model.landing.propose_lines import named

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.ports.git import Git


def notes_of(path: str) -> str:
    """The notes the agent wrote for the pull request, from their file."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise Refusal(
            "notes",
            f"{path} is not a file of text ({error}); --notes names the notes of the pull "
            "request",
            "write the notes into that file, then lem land propose SLUG again",
        ) from error


def head_of(text: bytes, path: str) -> Filing:
    """An item's title (the first line after its head, a `# ` heading) and its `worth`."""
    post = frontmatter.loads(text.decode("utf-8", errors="replace"))
    first = next((line for line in post.content.splitlines() if line.strip()), "")
    title = first[2:].strip() if first.startswith("# ") else None
    worth = post.get("worth")
    return Filing(path=path, title=title, worth=str(worth) if worth else None)


def settings_of(git: Git, where: Path, commits: tuple[str, str]) -> Settings:
    """Lem's settings files at the merge base and at the tip."""
    since, tip = commits
    before, after = git.show(where, since, TEAM), git.show(where, tip, TEAM)
    local = (
        git.show(where, since, LOCAL) is not None,
        git.show(where, tip, LOCAL) is not None,
    )
    return Settings(
        before=before.decode("utf-8", errors="replace") if before is not None else None,
        after=after.decode("utf-8", errors="replace") if after is not None else None,
        local=local,
    )


def added(
    git: Git, where: Path, commits: tuple[str, str], paths: tuple[str, ...]
) -> tuple[Filing, ...]:
    """Each item the branch adds to the backlog folder, with its head at the tip."""
    since, tip = commits
    found: list[Filing] = []
    for path in paths:
        if (
            not path.startswith(f"{BACKLOG}/")
            or git.show(where, since, path) is not None
        ):
            continue
        text = git.show(where, tip, path)
        if text is not None:
            found.append(head_of(text, path))
    return tuple(found)


def gathered(context: Context, notes: str) -> Facts:
    """The facts of the proposal of the tip now, with the notes of the file `notes`."""
    git, world, where = context.ports.git, context.world, context.worktree
    tip = world.tip or world.base
    commits = (git.merge_base(where, world.base, tip) or world.base, tip)
    changed = git.diff_stat(where, *commits).paths
    text = notes_of(notes)
    landing = context.record.landing
    asked = {
        *named(text),
        *(found.path for found in (landing.filed if landing else ()) if found.path),
        *(
            (context.record.task.backlog_item,)
            if context.record.task.backlog_item
            else ()
        ),
    }
    return Facts(
        changed=changed,
        settings=settings_of(git, where, commits),
        added=added(git, where, commits, changed),
        in_tip=frozenset(
            path for path in asked if git.show(where, tip, path) is not None
        ),
        notes=text,
    )
