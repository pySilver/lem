"""The row for permission to read Lem's files outside Claude Code's working directories.

Briefs and stages name files under the root of `lem version` only, so one allow rule over that
root answers it for good. Under Homebrew the root is in a folder of the release
(`Cellar/lem/VERSION`), so the rule names `Cellar/lem` and an update keeps it. A `Read` rule
with `//` is an absolute path, and one with `~/` is from the home
(code.claude.com/docs/en/permissions, "How path patterns match", read through ctx7 on
2026-11-25); a folder of `additionalDirectories` is a working directory, which asks nothing.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor.checkouts import files_of, main_checkout, table_of
from lem.cli.doctor.row import OPTIONAL, Row
from lem.kernel import paths

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

ANY = "/**"
READ = re.compile(r"Read\((.+)\)")


def allowed_folder(look: Look) -> Path:
    """The folder the allow rule names: Homebrew's `Cellar/lem` over the root of a brewed
    app, else the root itself."""
    root = paths.root().resolve()
    cellars = (brew / "Cellar" / "lem" for brew in look.brews)
    return next((one for one in cellars if root.is_relative_to(one)), root)


def folder_of(pattern: str, home: Path) -> Path | None:
    """The folder a `Read` rule's pattern or a working directory covers: an absolute path
    (`//` in a rule), or one from the home (`~/`); None for any other form."""
    stem = pattern.removesuffix(ANY).removesuffix("/")
    if stem.startswith("~/"):
        return home / stem[2:]
    return Path(stem).resolve() if stem.startswith("/") else None


def as_list(found: object) -> list[str]:
    """The texts of a list of a settings file; none for anything else."""
    return [str(one) for one in found] if isinstance(found, list) else []


def covering(table: dict[str, object], home: Path) -> list[Path]:
    """The folders the `Read` allow rules and the working directories of one settings file
    cover."""
    permissions = table.get("permissions")
    if not isinstance(permissions, dict):
        return []
    rules = [READ.fullmatch(rule) for rule in as_list(permissions.get("allow"))]
    absolute = [
        matched[1].removeprefix("/")
        for matched in rules
        if matched and matched[1].startswith(("//", "~/"))
    ]
    added = as_list(permissions.get("additionalDirectories"))
    found = (folder_of(one, home) for one in (*absolute, *added))
    return [one for one in found if one is not None]


def allowing(look: Look, root: Path) -> Path | None:
    """The first settings file of Claude Code for the call's repository whose rules cover
    `root`."""
    for path in files_of(look.home, main_checkout(look.folder)):
        folders = covering(table_of(path), look.home)
        if any(root.is_relative_to(one) for one in folders):
            return path
    return None


def read_line(look: Look) -> str:
    """The exact permission to read Lem's own files."""
    folder = allowed_folder(look)
    return f"Read(/{folder}{ANY})"


def reads_row(look: Look) -> Row:
    """Whether a settings file of Claude Code allows the reads of Lem's files."""
    root = paths.root().resolve()
    held = allowing(look, root)
    user = look.home / ".claude" / "settings.json"
    detail = f"no allow rule covers {root}"
    if held is not None:
        detail = f"{held} allows the reads under {root}"
    return Row(
        name="reads of Lem's files",
        need=OPTIONAL,
        found=held is not None,
        detail=detail,
        used_for=(
            "the files of Lem that a stage and a brief name, under the root of `lem version`"
        ),
        without_it=(
            "Claude Code asks permission to read a Lem file outside the working directories. "
            "The owner can allow the read or put the line under "
            f'"permissions", "allow" in {user} once'
        ),
        line=read_line(look),
    )
