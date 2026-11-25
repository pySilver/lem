"""The row of a project's personas: in a repository where Lem is set up, how many people a
panel asks, and a persona's file that no panel can read. Its need is `project`: it never fails
the machine check, and the onboarding that writes the personas is not stopped by their absence.
The panel's own cast reader (`lem cast show`, the step `addons-outside`) takes its place here
when it lands, as `doctor.project` on `main` asked the panel's script.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor.checkouts import main_checkout
from lem.cli.doctor.row import PROJECT, Row

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

README = "README.md"
PERSONAS = Path(".lem") / "personas"
TEAM = Path(".lem") / "settings.toml"


def personas_in(folder: Path) -> tuple[int, str | None]:
    """How many personas the cast folder holds (each Markdown file but its README), and the
    first one that does not read as UTF-8, which no panel can read either."""
    written = folder.glob("*.md")
    found = sorted(one for one in written if one.name != README)
    unread = next((one for one in found if not readable(one)), None)
    return len(found), (f"{unread.name} is not UTF-8 text" if unread else None)


def readable(path: Path) -> bool:
    """Whether a persona's file reads as UTF-8."""
    try:
        path.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return False
    return True


def persona_said(folder: Path) -> tuple[bool, str, str]:
    """Whether the cast holds a person, the row's detail, and the end of its fix."""
    count, unread = personas_in(folder)
    if unread:
        return False, f"{unread} ({folder})", f"; {unread}: save it as UTF-8"
    second = ": a panel needs a second person who would notice other things"
    said = f"{count} ({folder})"
    if count == 1:
        said = f"{said}{second}"
    return count > 0, said, ""


def persona_rows(look: Look) -> tuple[Row, ...]:
    """In a repository where Lem is set up: how many people a panel asks. The cast is the
    main checkout's, which a task's worktree older than the cast does not have."""
    root = main_checkout(look.folder)
    if root is None or not (root / TEAM).is_file():
        return ()
    found, detail, fix = persona_said(root / PERSONAS)
    return (
        Row(
            name="project personas",
            need=PROJECT,
            found=found,
            detail=detail,
            used_for=(
                "the people a panel asks before a hard question reaches the owner: every "
                "project of Lem has two or more"
            ),
            without_it=(
                "the project's setup is not finished and no panel can run; `/lem init` in "
                "this repository asks who a decision here affects and writes them, and "
                f"leaves the settings that are there as they are{fix}"
            ),
        ),
    )
