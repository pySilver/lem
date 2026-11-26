"""The bar: where a change lowers it, from what git gave, and the checks' refusal of a bar lowered
with no reason.

A change lowers the bar with a new mark that hides a finding or leaves a test out
(`bar_marks.py`), with fewer assertions in a test file, with a coverage threshold that went down
or is gone, and with a test file it deletes or moves out of the tests. The plan gives a reason
for each file under `## The bar`; the fast track has no plan, and gives none.
"""

import re
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing.bar_lines import TEST_FILE, WORKFLOW, Walk, reasons_of
from lem.model.landing.bar_marks import (
    BAR_MARKS,
    DOCS,
    TEST_CONFIG,
    new_marks,
    patterns,
)
from lem.records.base import Frozen
from lem.records.landing.checks import Edited

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from lem.records.landing.checks import EditedKind

# The characters kept from a line that shows a mark of the bar.
BAR_LINE_LENGTH = 160
# A file with no suffix is read with the marks of the language its first line names
# (`#!`), as ruff checks such a file of Python when a project names it in its
# `extend-include` and ShellCheck reads a shell script by its `#!`: each interpreter
# here with the suffix whose marks it takes. Another
# interpreter, or no `#!`, takes no marks, as a file with no suffix took none before.
SHEBANG = MappingProxyType(
    {
        "python": ".py",
        **dict.fromkeys(("sh", "bash", "dash", "ksh"), ".sh"),
    }
)
# The bytes of a file's first line that are read for its `#!`: an interpreter's path
# and name fit in it, and a built file of one long line is never read whole.
SHEBANG_READ = 256
# An option or a setting of `env` (`-S`, `PYTHONPATH=src`), which names no interpreter.
OPTION = re.compile(r"^-|=")
# A version after a Python's name (`python3.11`).
PYTHON_VERSION = re.compile(r"(?<=^python)[0-9.]+$")
# A file a test compares its output with, written once and read by the test.
SNAPSHOT = re.compile(r"(^|/)__snapshots__/|\.snap$|\.ambr$|\.approved\.[A-Za-z0-9]+$")
# Files that are neither code nor documentation: no language's marks apply, and none
# is missed.
DATA_SUFFIXES = (
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".lock",
    ".cfg",
    ".ini",
    ".csv",
    ".tsv",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".html",
    ".css",
    ".xml",
    "",
)
# The suffixes the bar misses no mark of: those it has marks for, documents and data.
UNMISSED = frozenset(
    {suffix for suffixes in BAR_MARKS for suffix in suffixes} | {*DOCS, *DATA_SUFFIXES}
)
# The lowered bars a refusal names, the first of them: the length of the text, not a
# measurement.
NAMED = 5


class Mark(Frozen, frozen=True, kw_only=True):
    """One place where the change lowers the bar: its file, what lowers it, the line that
    shows it, and the plan's reason, or None."""

    path: str
    what: str
    line: str = ""
    reason: str | None = None


class BarRead(Frozen, frozen=True, kw_only=True):
    """The bar as the change leaves it: where it lowers the bar, the kinds of file the bar has
    no marks for, and the tests, snapshots and settings it edits."""

    lowered: tuple[Mark, ...] = ()
    not_covered: tuple[str, ...] = ()
    edited: tuple[Edited, ...] = ()


class Lowered:
    """Where a change lowers the bar, in the order a refusal names them: each new mark, each
    test file with fewer assertions, each coverage threshold that went down, each test file
    deleted or moved out of the tests; and the tests, snapshots and settings it edits, from
    the rows of `git diff --name-status -M`."""

    def __init__(
        self, walk: Walk, rows: Sequence[str], files: Mapping[str, str]
    ) -> None:
        """Read the WALK of the diff, then each of ROWS; FILES gives a file with no suffix
        its kind (`patterns`)."""
        self.marks = self.marked(walk, files)
        self.marks += [
            Mark(
                path=path,
                what=what,
            )
            for path, what in walk.lowered()
        ]
        self.edited: list[Edited] = []
        for row in rows:
            self.read(*row.split("\t"))

    def marked(self, walk: Walk, files: Mapping[str, str]) -> list[Mark]:
        """Each new mark of the code or of a runner's settings, with the line it stands on."""
        return [
            Mark(
                path=path,
                what=hit.group(0),
                line=line.strip()[:BAR_LINE_LENGTH],
            )
            for path, hunks in walk.files
            if path is not None
            for hit, line in new_marks(hunks, *patterns(path, files))
        ]

    def read(self, status: str, before: str, *moved: str) -> None:
        """Read one row: its STATUS, the path BEFORE and, for a move, the path it MOVED to."""
        now = moved[0] if moved else before
        # a test file that moved out of the tests is one the tests no longer run, as a
        # deleted one
        out = status.startswith("R") and not TEST_FILE.search(now)
        if TEST_FILE.search(before) and (status == "D" or out):
            self.removed(status, before, now)
        kind = edited_kind(now)
        if kind and self.edits(status):
            self.edited.append(Edited(path=now, kind=kind))

    def removed(self, status: str, before: str, now: str) -> None:
        """The test file BEFORE is deleted, or moved out of the tests to NOW: one bar lowered,
        in place of the others of its path."""
        if status == "D":
            what = "a test file is deleted"
        else:
            what = f"a test file is moved out of the tests, to {now}"
        self.marks = [mark for mark in self.marks if mark.path != before]
        self.marks.append(Mark(path=before, what=what))

    def edits(self, status: str) -> bool:
        """Whether a row of STATUS edits a file that was there: a change, or a move with one."""
        renamed = status.startswith("R") and status != "R100"
        return status == "M" or renamed


def edited_kind(now: str) -> EditedKind | None:
    """Which file a reviewer reads first the file NOW is, or None."""
    if SNAPSHOT.search(now):
        return "snapshot"
    if TEST_CONFIG.search(now) or WORKFLOW.search(now):
        return "test configuration"
    if TEST_FILE.search(now):
        return "test"
    return None


def shebang_suffix(line: str) -> str:
    """The suffix whose marks a file with no suffix is read with, from its first LINE: the
    interpreter its `#!` names, also through `env` and its options and settings
    (`#!/usr/bin/env -S python3 -I`), by `SHEBANG`, with a version after a Python's name
    (`python3.11`); "" for no `#!` and for another interpreter."""
    words = line.removeprefix("#!").split() if line.startswith("#!") else []
    if words and PurePosixPath(words[0]).name == "env":
        words = [word for word in words[1:] if not OPTION.search(word)]
    if not words:
        return ""
    name = PurePosixPath(words[0]).name
    return SHEBANG.get(PYTHON_VERSION.sub("", name), "")


def bar_of(
    diff: str,
    rows: Sequence[str],
    plan: str,
    files: Mapping[str, str],
    *,
    where: str,
) -> BarRead:
    """The bar's result from what git gave: DIFF is `git diff -U0 -M`, ROWS the lines of `git
    diff --name-status -M`, FILES every changed path with the suffix whose marks a file with
    no suffix is read with (`shebang_suffix`), else ""; PLAN is the plan's text, or "" when
    there is none, and WHERE its file."""
    reasons = reasons_of(plan, where)
    found = Lowered(Walk(diff), rows, files)
    suffixes = {PurePosixPath(one).suffix.lower() for one in files}
    return BarRead(
        lowered=tuple(
            replace(mark, reason=reasons.get(mark.path)) for mark in found.marks
        ),
        not_covered=tuple(sorted(suffixes - UNMISSED)),
        edited=tuple(sorted(found.edited, key=lambda edit: edit.path)),
    )


def refusal(lowered: Sequence[Mark], *, small: bool) -> Refusal | None:
    """The checks' refusal of a bar LOWERED with no reason, or None. The fast track (SMALL)
    gives no reason: it has no plan, and a lowered bar never takes the fast track."""
    unexplained = [mark for mark in lowered if not mark.reason]
    if not unexplained:
        return None
    shown = unexplained[:NAMED]
    named = "; ".join(
        (f"{mark.path} ({mark.what})" for mark in shown),
    )
    if small:
        return Refusal(
            "bar",
            f"a task on the fast track does not lower the bar: {named}",
            "take the mark out; when the change needs it, it takes the standard track, and "
            "Lem tells the owner so and takes that track, whose plan gives the reason under "
            "`## The bar`",
        )
    return Refusal(
        "bar",
        f"the change lowers the bar with no reason given: {named}",
        "take the mark out, or give the reason in the task's plan under `## The bar` as "
        "`- PATH: REASON`, where the one who reads the change sees it",
    )
