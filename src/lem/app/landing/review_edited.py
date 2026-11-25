"""The existing tests, snapshots and test configurations a change edits, which the reviewer
reads first against the criteria (`bar.edited` of `land.check_bar` on `main`, prompt step 5).

A stand-in until `Checked` keeps the bar's `edited` list, which the step `land-checks` computes
with the bar (`notes/land-review.md`): a file is edited when the base and the tip both have it,
and its kind is told by its place and name as `main`'s patterns tell it.
"""

import re
from typing import TYPE_CHECKING, Literal

from lem.records.base import Frozen

type Span = tuple[str, str]
type Paths = tuple[str, ...]

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git

type Kind = Literal["snapshot", "test configuration", "test"]
SNAPSHOT = re.compile(r"(^|/)__snapshots__/|\.snap$|\.ambr$|\.approved\.[A-Za-z0-9]+$")
TEST_CONFIG = re.compile(
    r"(^|/)(pyproject\.toml|setup\.cfg|pytest\.ini|tox\.ini|package\.json|\.coveragerc"
    r"|\.nycrc(\.json|\.ya?ml)?|(jest|vitest)\.config\.[A-Za-z0-9.]+)$"
    r"|(^|/)\.github/workflows/[^/]+\.ya?ml$"
)
TEST_FILE = re.compile(
    r"(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]*$|_test\.[A-Za-z0-9]+$"
    r"|\.(test|spec)\.[A-Za-z0-9]+$"
)
type Told = tuple[tuple[re.Pattern[str], Kind], ...]
KINDS: Told = (
    (SNAPSHOT, "snapshot"),
    (TEST_CONFIG, "test configuration"),
    (TEST_FILE, "test"),
)


class Edited(Frozen, frozen=True, kw_only=True):
    """An existing file of the tests that the change edits, and its kind."""

    path: str
    kind: Kind


def kind_of(path: str) -> Kind | None:
    """The kind of a file of the tests, by its place and name; None for another file."""
    found = (kind for pattern, kind in KINDS if pattern.search(path))
    return next(found, None)


def edited(git: Git, worktree: Path, span: Span, paths: Paths) -> tuple[Edited, ...]:
    """Each file of the tests among the change's `paths` that the base and the tip both have."""
    found: list[Edited] = []
    for path in sorted(paths):
        kind = kind_of(path)
        if kind is not None and both_have(git, worktree, span, path):
            found.append(Edited(path=path, kind=kind))
    return tuple(found)


def both_have(git: Git, worktree: Path, span: tuple[str, str], path: str) -> bool:
    """Whether the base and the tip both have the file."""
    return all(git.show(worktree, rev, path) is not None for rev in span)
