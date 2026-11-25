"""The change's edits of Lem's own settings files, from the base to the tip, which make a request
careful by this code (`land.settings_edit` and `land.local_settings_edit` on `main`)."""

from typing import TYPE_CHECKING

from lem.model.landing import careful

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git


def text_of(found: bytes | None) -> str | None:
    """A file's bytes as text, or None where the commit has no such file."""
    if found is None:
        return None
    return found.decode("utf-8", errors="replace")


def seen(git: Git, worktree: Path, span: tuple[str, str], path: str) -> careful.Seen:
    """One settings file as the change has it, from the base to the tip."""
    before = git.show(worktree, span[0], path)
    after = git.show(worktree, span[1], path)
    touched = before != after
    return careful.Seen(touched=touched, base=text_of(before), tip=text_of(after))


def edits(git: Git, worktree: Path, span: tuple[str, str]) -> careful.Edits:
    """The change's edits of the team's settings file and of one machine's."""
    return careful.Edits(
        settings=seen(git, worktree, span, careful.SETTINGS_FILE),
        local=seen(git, worktree, span, careful.LOCAL_SETTINGS_FILE),
    )
