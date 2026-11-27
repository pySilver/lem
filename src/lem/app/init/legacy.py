"""Carry the old repository's settings into the team's draft, and name each key left out."""

from typing import TYPE_CHECKING

import tomlkit

from lem.app.init import origin, template
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings import described, files, places
from lem.settings.team import Team

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

DROPPED = "dropped"


class Migration(Frozen, frozen=True, kw_only=True):
    """The old keys copied, superseded by a current choice, or without a place."""

    imported: tuple[str, ...]
    kept: tuple[str, ...]
    dropped: tuple[str, ...]

    @classmethod
    def counted(cls, outcomes: list[tuple[str, str]]) -> Migration:
        """Group the old keys by what happened to them."""
        groups: dict[str, list[str]] = {"imported": [], "kept": [], DROPPED: []}
        for key, status in outcomes:
            groups[status].append(key)
        return cls(
            imported=tuple(sorted(groups["imported"])),
            kept=tuple(sorted(groups["kept"])),
            dropped=tuple(sorted(groups[DROPPED])),
        )


def initial(path: Path, codex: str) -> tuple[TOMLDocument, set[str]]:
    """The draft and the values that the current file already holds, if any."""
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        return tomlkit.parse(template.written(None, codex)), set()
    tables = files.decoded(body, str(path))
    files.converted(tables, Team, str(path))
    return tomlkit.parse(body.decode("utf-8")), keys_in(tables)


def old_tables(path: Path) -> files.Tables:
    """The old file must be a regular file before init reads or removes it."""
    if path.is_symlink() or not path.is_file():
        raise Refusal(
            "settings-toml",
            f"{path} is not a regular file",
            f"put the old settings in a regular file at {path} and run lem init again",
        )
    return files.read(path, str(path))


def carry(
    doc: TOMLDocument, table: str, given: object, keep: set[str]
) -> list[tuple[str, str]]:
    """Carry one table's known keys, with a current value ahead of an old one."""
    known = described.keys_of(Team, table)
    if not isinstance(given, dict):
        if known:
            files.converted({table: given}, Team, places.LEGACY_TEAM.as_posix())
        return [(table, DROPPED)]
    if not known and not given:
        return [(table, DROPPED)]
    outcomes = []
    for key, entry in given.items():
        name = f"{table}.{key}"
        if name in keep:
            outcomes.append((name, "kept"))
        elif key in known:
            doc.setdefault(table, tomlkit.table())[key] = entry
            outcomes.append((name, "imported"))
        else:
            outcomes.append((name, DROPPED))
    return outcomes


def keys_in(existing: files.Tables) -> set[str]:
    """Keys already chosen by the owner in the current file."""
    keep: set[str] = set()
    for table, entries in existing.items():
        if isinstance(entries, dict):
            keep.update(f"{table}.{key}" for key in entries)
    return keep


def default_base(doc: TOMLDocument, checkout: Path) -> None:
    """Use origin's default only if neither file nor the call names a base."""
    branch = doc.setdefault("branch", tomlkit.table())
    if "base" not in branch:
        branch["base"] = origin.base_of(checkout, None)


def migrated(
    path: Path, old: Path, base: str | None, codex: str
) -> tuple[str, Migration]:
    """The text with the old defaults and the account of where each old key went."""
    doc, keep = initial(path, codex)
    if base and "branch.base" not in keep:
        doc.setdefault("branch", tomlkit.table())["base"] = base
        keep.add("branch.base")
    outcomes = []
    for table, given in old_tables(old).items():
        outcomes.extend(carry(doc, table, given, keep))
    default_base(doc, path.parent.parent)
    return tomlkit.dumps(doc), Migration.counted(outcomes)
