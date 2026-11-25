"""The marks of the bar on the lines a change added, and which of them are new (`bar.py`).

A mark counts when the line it stands on did not have it: an old mark cancels a new one only on
its own line (`new_marks`), and a line that only moved, or got another space, keeps its marks. A
mark is the same one only with the same own text (`marks_of`): `noqa: F401` that becomes `noqa`
or `noqa: F401, E501` is a wider suppression, and a new one, while a mark put beside it leaves its
text as it was. Each file's hunks, the lines that went and came of each, are read together, as a
line may move from one hunk to another.
"""

import re
from collections import Counter, deque
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Container, Iterable, Iterator, Mapping, Sequence

# A document may quote a mark of the bar, the plan's own reason for one too: no mark is
# looked for in these.
DOCS = (".md", ".rst", ".adoc")
# The marks by which a change lowers the bar, for the languages whose tools read them.
# Chosen by the session that built this check (2026-11-15) from those tools' own syntax,
# and the focus marks of JavaScript's runners (`.only`, `fit`, `fdescribe`), which run
# one test alone and so leave the others out, after an audit of the bar (2026-11-17);
# not measured. A mark that a call's "(" follows is looked for with that "(" and named
# without it, so a refusal says `it.only`, never `it.only(`. The marks of a test that
# runs again until it passes came after a probe of the bar passed eight ways of
# weakening a test unseen (audit T-F2, 2026-11-17). Of Python, every comment that
# ruff and pyrefly obey to hide a finding came when those tools came to Lem's own code
# (2026-11-24), each form as the docs of ruff 0.17.3 and the `--help` of pyrefly 1.5.0
# give it, and as ruff 0.17.6 and pyrefly 1.5.0 obeyed it in a throwaway file: ruff's
# `noqa`, `ignore`, `disable` and `file-ignore`, isort's `skip_file`, `off` and `skip`,
# the formatter's `fmt: off`, `fmt: skip` and `yapf: disable`; pyrefly's own, and the
# other checkers' it obeys with `permissive-ignores` or with no settings file. Each
# with the tool's own rule of case: `noqa` in any case, the rest in lower case. Left
# out: the comment that ends a range (`enable`, `on`), as its start counts, and
# `isort: split`, which hid no finding of I001 in that file. Each takes the forms its
# tool obeys, as ruff 0.17.6 and pyrefly 1.5.0 obeyed them on 2026-11-24: ruff's
# `isort: skip` or `isort:skip` anywhere in a comment (`# keep first isort:skip`,
# `# isort: skipped`), and no other mark with a `-` or a word character after it
# (`# fmt: off-topic`, `# mypy: ignore-missing-imports`, `# type: ignored`), but
# `pyre-ignore-all-errors`, which pyrefly obeys as the start of a longer word. A focus
# or skip mark of one word (`fit`, `xit`) is a call of the runner's global function, and
# after a dot it is a method of that name (`this.fit()`, `a.fit(` in mermaid.min.js),
# which no runner's docs write as a mark (Jasmine, Mocha, Jest, Vitest and Playwright,
# read 2026-11-24); a mark of the form `test.describe.only(` is Playwright's own, and
# counts after a dot.
BAR_MARKS = MappingProxyType(
    {
        (".py",): (
            r"#\s*(?i:noqa)(?![-\w])",
            r"#\s*type:\s*ignore(?![-\w])",
            r"#\s*pyright:\s*ignore(?![-\w])",
            r"#\s*pyrefly:\s*ignore(?:-errors)?(?![-\w])",
            r"#\s*ty:\s*ignore(?![-\w])",
            r"#\s*(?:ruff|flake8)\s*:\s*(?i:noqa)(?![-\w])",
            r"#\s*ruff\s*:\s*(?:disable|file-ignore|ignore)(?=\s*\[)",
            r"#[^#\n]*?isort: ?skip\w*",
            r"#\s*(?:ruff:\s*)?isort:\s*off(?![-\w])",
            r"#\s*fmt:\s*(?:off|skip)(?![-\w])",
            r"#\s*yapf:\s*disable(?![-\w])",
            r"#\s*pyre-(?:ignore-all-errors|(?:ignore|fixme)(?![-\w]))",
            r"#\s*pyre:\s*ignore(?![-\w])",
            r"#\s*mypy:\s*ignore(?:-errors)?(?![-\w])",
            r"#\s*zuban:\s*ignore(?![-\w])",
            r"#\s*pylint:\s*disable",
            r"#\s*nosec",
            r"\bpytest\.mark\.(skip|xfail)",
            r"\bunittest\.skip",
            r"\bpytest\.skip(?=\()",
            r"\bpytest\.mark\.(flaky|retry)\b",
            r"^\s*@flaky\b",
        ),
        (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"): (
            r"eslint-disable",
            r"@ts-ignore",
            r"@ts-expect-error",
            r"@ts-nocheck",
            r"\b(it|test|describe)\.(skip|todo|only)(?=\()",
            r"(?<!\.)\bx(it|test|describe)(?=\()",
            r"(?<!\.)\bf(it|describe)(?=\()",
            r"\bjest\.retryTimes(?=\()",
            r"\bthis\.retries(?=\()",
        ),
        (".go",): (r"//\s*nolint", r"\bt\.Skip(f|Now)?(?=\()"),
        (".rs",): (r"#!?\[allow\(", r"#\[ignore\b"),
        (".java", ".kt"): (r"@Disabled", r"@Ignore", r"@SuppressWarnings"),
        (".sh", ".bash"): (r"#\s*shellcheck\s+disable",),
    }
)
# The settings files of a test runner or of coverage, by name: their marks leave tests
# out, or run a failing test again until it passes, for the whole suite at once.
TEST_CONFIG = re.compile(
    r"(^|/)(pyproject\.toml|setup\.cfg|pytest\.ini|tox\.ini|package\.json|\.coveragerc|\.nycrc(\.json|\.ya?ml)?|(jest|vitest)\.config\.[A-Za-z0-9.]+)$"
)
TEST_CONFIG_MARKS = (
    r"--deselect\b",
    r"-k[\s=]+[\"']?not\b",
    r"--ignore(-glob)?\b",
    r"\btestPathIgnorePatterns\b",
    r"(--)?\breruns\b",
    r"\bretries\b",
    r"\bretryTimes\b",
    r"\bflaky\b",
)

# The lines that went and the lines that came, of one hunk.
type Hunk = tuple[list[str], list[str]]
# A mark on a line, with its own text.
type Hit = tuple[re.Match[str], str]
# The marks of each line of one side of a hunk, and of each side of each hunk of a file.
type Side = list[list[Hit]]
type Found = list[list[Side]]
# A line of a file's diff: its hunk and its place there.
type Place = tuple[int, int]
type Line = tuple[Place, str, list[Hit]]
type Compiled = list[re.Pattern[str]]
type Patterns = Sequence[re.Pattern[str]]


def patterns(path: str, kinds: Mapping[str, str]) -> tuple[Compiled, Compiled]:
    """The marks of the code and of a runner's settings that PATH is read with, by its suffix,
    or for a file with none by its kind in KINDS; none for a document, whose PATH is ""."""
    suffix = PurePosixPath(path).suffix.lower() or kinds.get(path, "")
    marks = [
        re.compile(mark)
        for suffixes, found in BAR_MARKS.items()
        if path and suffix in suffixes
        for mark in found
    ]
    settings = [
        re.compile(mark)
        for mark in TEST_CONFIG_MARKS
        if path and TEST_CONFIG.search(path)
    ]
    return marks, settings


def code_of(line: str, hits: Sequence[Hit] = ()) -> str:
    """The words of LINE before its first mark of HITS, each space one: the line's code, by
    which a line that lost or got a mark is the same line."""
    first = min((hit.start() for hit, _ in hits), default=None)
    return " ".join(line[:first].split())


def own_texts(text: str, hits: Sequence[re.Match[str]]) -> list[Hit]:
    """Each mark of HITS, in their order on a line's TEXT, with its own text: from its start
    to the start of the next mark that starts after it, or to the line's end, each space one.
    The marks are walked once, from the last: a bundle's one line may hold thousands."""
    own: list[Hit] = []
    # the end of the mark at hand: the start of the next mark that starts after it, as
    # marks that start at one place share it
    following = len(text)
    after = following
    for hit in reversed(hits):
        start = hit.start()
        if start < after:
            following = after
        own.append((hit, code_of(text[start:following])))
        after = start
    own.reverse()
    return own


def marks_of(text: str, marks: Patterns, settings: Patterns) -> list[Hit]:
    """Each mark of a line's TEXT with its own text, by which an old mark is told from a new
    one. A mark of the code (MARKS) counts each time it stands on the line, and its own text
    runs from it to the next such mark, or to the line's end (`own_texts`): a mark put beside
    an old one leaves the old one's text as it was, and a rule list that grew changes it. A
    mark of a runner's settings (SETTINGS) counts once for each kind, with the text to the
    line's end, as its tokens share a line by the settings' syntax, and a new one of the same
    kind changes that text."""
    hits = sorted(
        (found for mark in marks for found in mark.finditer(text)),
        key=lambda found: found.start(),
    )
    searched = (mark.search(text) for mark in settings)
    tails = [own_texts(text, [hit])[0] for hit in searched if hit]
    return [*own_texts(text, hits), *tails]


class Pairs:
    """Which removed line each added line of a file is the same line as, each by its hunk and
    its place there, from the file's hunks and the marks found on each line: a line that
    moved, with the same words, from anywhere in the file; then, in its hunk, a line that kept
    its code, the words before its first mark (an import whose suppression went); then the
    rest of its hunk in their order, as git lists a hunk's lines that changed. Each removed
    line is one added line's at most."""

    def __init__(self, hunks: Sequence[Hunk], found: Found) -> None:
        """Keep the file's hunks and the marks on each line, and pair its lines."""
        self.hunks = hunks
        self.found = found
        self.everywhere = range(len(hunks))
        self.pairs: dict[Place, Place] = {}
        self.used: set[Place] = set()
        self.moved()
        for hunk_at in self.everywhere:
            self.kept(hunk_at)
            self.rest(hunk_at)

    def lines(
        self, side: int, hunks: Iterable[int], skip: Container[Place] = ()
    ) -> Iterator[Line]:
        """Each line of SIDE (0 the lines that went, 1 those that came) of the hunks HUNKS
        that is not in SKIP, with its place and its marks."""
        for hunk_at in hunks:
            found = self.found[hunk_at][side]
            for at, line in enumerate(self.hunks[hunk_at][side]):
                place = (hunk_at, at)
                if place not in skip:
                    yield place, line, found[at]

    def before(self, place: Place) -> list[Hit]:
        """The marks of the removed line that the added line at PLACE is the same line as;
        none for a line that is none's."""
        was = self.pairs.get(place)
        if was is None:
            return []
        hunk_at, at = was
        return self.found[hunk_at][0][at]

    def moved(self) -> None:
        """Pair each added line with a removed line of the same words, from anywhere in the
        file."""
        spare: dict[str, deque[Place]] = {}
        for place, line, _ in self.lines(0, self.everywhere):
            spare.setdefault(code_of(line), deque()).append(place)
        for place, line, _ in self.lines(1, self.everywhere):
            left = spare.get(code_of(line))
            if left:
                self.pairs[place] = left.popleft()
        self.used.update(self.pairs.values())

    def kept(self, hunk_at: int) -> None:
        """In the hunk HUNK_AT, pair each added line with no pair yet with a removed line, not
        used, that kept its code."""
        spare: dict[str, deque[Place]] = {}
        for place, line, hits in self.lines(0, (hunk_at,), self.used):
            spare.setdefault(code_of(line, hits), deque()).append(place)
        for place, line, hits in self.lines(1, (hunk_at,), self.pairs):
            left = spare.get(code_of(line, hits))
            if left:
                self.pairs[place] = left.popleft()
                self.used.add(self.pairs[place])

    def rest(self, hunk_at: int) -> None:
        """In the hunk HUNK_AT, pair each added line with no pair yet with the next removed
        line, not used, in the hunk's order."""
        gone = self.lines(0, (hunk_at,), self.used)
        left = deque(place for place, _, _ in gone)
        for place, _, _ in self.lines(1, (hunk_at,), self.pairs):
            if left:
                self.pairs[place] = left.popleft()
                self.used.add(self.pairs[place])


def fresh(previous: Sequence[Hit], hits: Sequence[Hit]) -> list[re.Match[str]]:
    """The marks of HITS, an added line's, that no mark of the same own text of PREVIOUS, the
    marks of the removed line it is the same line as, stands for."""
    left = Counter((hit.re.pattern, own) for hit, own in previous)
    new: list[re.Match[str]] = []
    for hit, own in hits:
        if left[hit.re.pattern, own]:
            left[hit.re.pattern, own] -= 1
        else:
            new.append(hit)
    return new


def new_marks(hunks: Sequence[Hunk], marks: Patterns, settings: Patterns) -> list[Hit]:
    """Each mark of a file's added lines that no old mark of the same line stands for, with
    its added line, from the file's HUNKS of `git diff -U0` and its MARKS and SETTINGS
    (`marks_of`). An old mark cancels a new one of the same own text only on the line it
    stood on (`Pairs`): an old mark anywhere else in the file stands for none, so a
    suppression taken off one line and put on another is a new one."""
    if not (marks or settings):
        return []
    found = [
        [[marks_of(line, marks, settings) for line in side] for side in hunk]
        for hunk in hunks
    ]
    pairs = Pairs(hunks, found)
    return [
        (hit, line)
        for place, line, hits in pairs.lines(1, pairs.everywhere)
        for hit in fresh(pairs.before(place), hits)
    ]
