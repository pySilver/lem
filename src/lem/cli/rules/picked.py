"""Which rule files hold for a change: one match of its files against the scope of each rule
file in `.claude/rules`, for every reader of the rules."""

import re
from typing import TYPE_CHECKING, Literal

import msgspec

from lem.cli.rules.found import rule_files
from lem.cli.rules.globs import glob_patterns
from lem.cli.rules.scope import rule_scope
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings.placed import FIXED

if TYPE_CHECKING:
    from pathlib import Path

type Every = Literal["every path"]
type Scope = tuple[str, ...] | Every
# The patterns one glob's brace forms stand for.
type Forms = tuple[re.Pattern[str], ...]
# Paths of a change, or the globs of a rule.
type Names = tuple[str, ...]
# A glob that matched, and the file it matched.
type Hit = tuple[str, str]

EVERY: Every = "every path"


class Rule(Frozen, frozen=True, kw_only=True):
    """A rule file that holds: every path, or the globs that matched and the files they
    cover."""

    path: str = msgspec.field(name="file")
    scope: Scope
    covers: tuple[str, ...] = ()


class Picked(Frozen, frozen=True, kw_only=True):
    """The rules folder, whether it is there, the files of the change, and the rules that
    hold for them."""

    folder: str
    exists: bool
    files: tuple[str, ...]
    rules: tuple[Rule, ...]


def picked(root: Path, changed: tuple[str, ...]) -> Picked:
    """The rule files of the checkout `root` that hold for the files `changed`."""
    folder = root / dict(FIXED)["rules"]
    found = (rule_of(path, root, changed) for path in rule_files(folder))
    rules = tuple(rule for rule in found if rule is not None)
    return Picked(
        folder=str(folder), exists=folder.is_dir(), files=changed, rules=rules
    )


def rule_of(path: Path, root: Path, changed: tuple[str, ...]) -> Rule | None:
    """The rule file at `path` if it holds for a file of `changed`, else None."""
    inside = path.is_relative_to(root)
    shown = path.relative_to(root).as_posix() if inside else str(path)
    globs = rule_scope(path, shown)
    if globs is None:
        return Rule(path=str(path), scope=EVERY)
    hits = matched(globs, compiled(globs, shown), changed)
    return covering(path, hits) if hits else None


def matched(globs: Names, forms: tuple[Forms, ...], changed: Names) -> list[Hit]:
    """Each glob with each file of `changed` that one of its patterns matches whole."""
    return [
        (glob, name)
        for glob, patterns in zip(globs, forms, strict=True)
        for name in changed
        if any(pattern.fullmatch(name) for pattern in patterns)
    ]


def covering(path: Path, hits: list[Hit]) -> Rule:
    """The rule file at `path` with the globs that matched and the files they cover."""
    globs = tuple(sorted({glob for glob, _ in hits}))
    names = tuple(sorted({name for _, name in hits}))
    return Rule(path=str(path), scope=globs, covers=names)


def compiled(globs: tuple[str, ...], shown: str) -> tuple[Forms, ...]:
    """The patterns each glob stands for; a glob that does not read is refused."""
    try:
        return tuple(map(glob_patterns, globs))
    except re.error as error:
        raise Refusal(
            "rule-glob",
            f"{shown}: a glob of its `paths:` does not read as a pattern ({error})",
            "correct the glob: most likely a `[` with no `]`, or a range that runs "
            "backwards",
        ) from error
