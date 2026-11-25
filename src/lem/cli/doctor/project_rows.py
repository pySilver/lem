"""The rows about the repository the check runs in, which never fail the check: the permission
mode a builder meets there, Lem's plugin when it is installed for the user and so loads in every
repository, and the project's personas.

Lem assumes that Claude Code runs in auto mode (the owner, 2026-11-18: "we assume that automode is
used in codex and claude code"). `bypassPermissions` and `auto` take effect from the user's
settings only, never from a repository's (code.claude.com/docs/en/settings-reference,
`permissions.defaultMode`, read through ctx7 on 2026-11-17).
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor import plugins
from lem.cli.doctor.checkouts import files_of, roots, table_of
from lem.cli.doctor.mode_words import MEETS, SILENT, TO_AUTO, UNKNOWN
from lem.cli.doctor.row import PROJECT, Row

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

TEAM = Path(".lem") / "settings.toml"


def mode_of(home: Path, root: Path) -> tuple[str, Path | None]:
    """The mode a new session starts in, in the repository `root`, and the file that says
    it."""
    user = files_of(home, None)[0]
    for path in files_of(home, root):
        permissions = table_of(path).get("permissions")
        said = permissions.get("defaultMode") if isinstance(permissions, dict) else None
        if isinstance(said, str) and (said not in SILENT or path == user):
            return said, path
    return "default", None


def meets_said(mode: str) -> str:
    """What a builder in the background meets in `mode`, and the line to change."""
    if mode == "auto":
        return (
            "a builder asks nobody; the classifier may still refuse a step, which the owner "
            "then runs himself"
        )
    if mode in SILENT:
        return "a builder asks nobody"
    meets = MEETS.get(mode, UNKNOWN)
    return (
        f"{meets}. {TO_AUTO}. Until then, the allow rules that /lem init offers for "
        ".claude/settings.local.json hold Lem's commands, git's and the checks'"
    )


def mode_rows(look: Look) -> tuple[Row, ...]:
    """The permission mode a builder in the background meets in this repository; no row
    outside one."""
    here = roots(look.folder)
    if not here:
        return ()
    mode, source = mode_of(look.home, here[0])
    detail = (
        f"{mode}, from {source}" if source else "default: no settings file names one"
    )
    return (
        Row(
            name="permission mode",
            need=PROJECT,
            found=mode in SILENT,
            detail=detail,
            used_for=(
                "Lem assumes that Claude Code runs in auto mode: the builders and the leads "
                "run in the background, and a permission prompt stops the task until someone "
                "answers in the task's session"
            ),
            without_it=meets_said(mode),
        ),
    )


def scope_rows(look: Look) -> tuple[Row, ...]:
    """A row when Lem's plugin is installed for the user, and so loads in every repository of
    the machine; none otherwise."""
    users = [
        one
        for one in plugins.installs(look.home)
        if one.name == "lem" and not one.project
    ]
    if not users:
        return ()
    key = users[0].key
    return (
        Row(
            name="lem plugin scope",
            need=PROJECT,
            found=False,
            detail=f"{key} is installed for the user, so every repository on this machine "
            "loads it",
            used_for=(
                "Lem's skills, its builder and its correction hook, which belong to the "
                "repositories that use Lem"
            ),
            without_it=(
                "the skills and the hook load in every repository; the hook in a repository with "
                "no .lem/settings.toml writes nothing and costs about a tenth of a second a "
                "message (a median of 99.4 ms over 20 runs, Python 3.15.2, one Mac, 2026-11-17). "
                f"`claude plugin uninstall {key} --scope user` removes that install; then "
                f"`claude plugin install {key} --scope project` in each repository that uses Lem"
            ),
        ),
    )
