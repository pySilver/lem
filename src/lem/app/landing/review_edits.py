"""The change's edits of Lem's own settings files, from the base to the tip, which make a request
careful by this code (`land.settings_edit` and `land.local_settings_edit` on `main`)."""

from typing import TYPE_CHECKING

from lem.model.landing import careful

type Span = tuple[str, str]
type Paths = tuple[str, ...]

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git


NAMES = frozenset((careful.SETTINGS_FILE, careful.LOCAL_SETTINGS_FILE))


def text_of(found: bytes | None) -> str | None:
    """A file's bytes as text, or None where the commit has no such file."""
    if found is None:
        return None
    return found.decode("utf-8", errors="replace")


def seen(git: Git, worktree: Path, span: tuple[str, str], path: str) -> careful.Seen:
    """One settings file as the change has it, from the base to the tip."""
    before = git.show(worktree, span[0], path)
    after = git.show(worktree, span[1], path)
    return careful.Seen(touched=True, base=text_of(before), tip=text_of(after))


def edits(git: Git, worktree: Path, span: Span, paths: Paths) -> careful.Edits:
    """The change's edits of the team's settings file and of one machine's: each file the
    diff names (`paths`), its mode alone too (`land.settings_edit` reads the changed paths
    on `main`)."""
    untouched = careful.Seen()
    names = (careful.SETTINGS_FILE, careful.LOCAL_SETTINGS_FILE)
    settings, local = (
        seen(git, worktree, span, name) if name in paths else untouched
        for name in names
    )
    return careful.Edits(settings=settings, local=local)
