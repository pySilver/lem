"""The lines of a change and of its plan that the bar reads (`bar.py`): each file's hunks of
`git diff -U0 -M` with the assertions and coverage thresholds its lines took or gave, and the
reasons of the plan's `## The bar`, read past its fenced code blocks.

The criteria's fence scanner keeps headings in code blocks out of the plan's reasons.
"""

import codecs
import re
from collections import defaultdict
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria import fences
from lem.model.landing.bar_marks import DOCS, TEST_CONFIG

if TYPE_CHECKING:
    from lem.model.landing.bar_marks import Hunk

# A coverage threshold, as a runner's settings or a command line write it: its name and
# its number. The bar is lower when a number of one name went down, or the name is gone,
# anywhere in those files.
THRESHOLD = re.compile(
    r"(fail_under|fail-under|cov-fail-under)[\s\"']*[=:\s][\s\"']*([0-9]+(?:\.[0-9]+)?)|[\"']?\b(lines|branches|functions|statements)[\"']?\s*:\s*([0-9]+(?:\.[0-9]+)?)"
)
# The forge's workflows: a coverage threshold on a command line there counts, and an
# edit of one is an edit of a test configuration.
WORKFLOW = re.compile(r"(^|/)\.github/workflows/[^/]+\.ya?ml$")
# An assertion, as far as a line shows one: the word a test framework uses for it.
ASSERTS = re.compile(r"\b(assert|expect)", re.IGNORECASE)
# A test file, by its place or its name.
TEST_FILE = re.compile(
    r"(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]*$|_test\.[A-Za-z0-9]+$|\.(test|spec)\.[A-Za-z0-9]+$"
)
# The languages that keep unit tests in the module they test: there every file's
# assertions count.
INLINE_TESTS = (".rs",)
# A hunk's header in `git diff`: where it starts, and how many lines went and came,
# each count 1 when git leaves it out
HUNK = re.compile(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")
# The plan's section of the reasons, and one reason there: `- PATH: REASON`.
SECTION = re.compile(r"(?ms)^##\s+The bar\s*$(.*?)(?=^##\s|\Z)")
REASON = re.compile(r"(?m)^-\s+`?([^`:\n]+?)`?:\s+(\S.*)$")
ADDED = "+"
SIGNS = ("-", ADDED)

# A coverage threshold's number, with the file that holds it.
type Number = tuple[float, str]
# A threshold's numbers on the lines that went, and on those that came.
type Numbers = tuple[list[Number], list[Number]]
# A file of the diff by its path, None for a document, with its hunks.
type Changed = tuple[str | None, list[Hunk]]


def hunk_size(header: str) -> list[int]:
    """How many lines of a hunk went and came, from its HEADER (`@@ -1,2 +1,0 @@`); none for
    a header that is not one of a two-sided diff."""
    found = HUNK.match(header)
    if not found:
        return [0, 0]
    counts = found.groups()
    return [1 if count is None else int(count) for count in counts]


def judged(
    name: str,
    went: list[Number],
    came: list[Number],
) -> tuple[str, str] | None:
    """The file and the words of a coverage threshold NAME that went down or is gone, from its
    numbers on the lines that WENT and CAME; None when it held."""
    if not went:
        return None
    before, where = max(went)
    after = min(came)[0] if came else None
    if after is None:
        return where, f"{name} ({before:g}) is gone"
    if after < before:
        return where, f"{name} went from {before:g} to {after:g}"
    return None


class Walk:
    """One pass over `git diff -U0 -M`: each file's hunks, the lines that went and came of
    each, and the assertions and coverage thresholds its lines took or gave."""

    def __init__(self, diff: str) -> None:
        """Walk DIFF once, line by line."""
        self.files: list[Changed] = []
        # the file at hand, none before the first header
        # A git hunk always follows both file headers, which set these two fields.
        self.current: Changed = (None, [])  # pragma: no mutate
        self.old = ""  # pragma: no mutate
        # the lines of the hunk still to come, those that went and those that came, by its
        # `@@` header: a line inside a hunk is never a file's header, also a removed line
        # whose text starts with `-- ` (`--- ` in the diff, a removed SQL comment)
        self.due = [0, 0]
        # each test file's assertions that went, less those that came
        self.asserts: defaultdict[str, int] = defaultdict(int)
        # each coverage threshold's numbers before and after, whatever file of a runner's
        # settings holds it
        self.thresholds: defaultdict[str, Numbers] = defaultdict(lambda: ([], []))
        for line in diff.splitlines():
            self.read(line)

    def read(self, line: str) -> None:
        """Take one LINE of the diff: a line of a hunk, or a header."""
        sign = line[:1]
        came = sign == ADDED
        if sign in SIGNS and self.due[came] > 0:
            self.due[came] -= 1
            self.keep(line)
        elif line.startswith("@@"):
            self.due = hunk_size(line)
            self.current[1].append(([], []))
        else:
            self.header(line)

    def header(self, line: str) -> None:
        """Take a LINE outside a hunk: a file's header."""
        if line.startswith("--- "):
            self.old = path_of(line, "a/")
        elif line.startswith("+++ "):
            path = path_of(line, "b/") or self.old
            # A document may quote a mark, the plan's own reason for one too.
            document = PurePosixPath(path).suffix.lower() in DOCS
            self.current = (None if document else path, [])
            self.files.append(self.current)

    def keep(self, line: str) -> None:
        """Keep a LINE of a hunk in its file's last hunk, and count what it says."""
        path, hunks = self.current
        if not path:
            return
        if hunks:
            came = line.startswith(ADDED)
            hunks[-1][came].append(line[1:])
        self.count(path, line)
        self.tested(path, line)

    def count(self, path: str, line: str) -> None:
        """Count the coverage thresholds of a LINE of PATH's hunk, in a runner's or a
        workflow's settings."""
        if not (TEST_CONFIG.search(path) or WORKFLOW.search(path)):
            return
        came = line.startswith(ADDED)
        for found in THRESHOLD.finditer(line[1:]):
            name = found.group(1) or found.group(3)
            number = float(found.group(2) or found.group(4))
            self.thresholds[name][came].append((number, path))

    def tested(self, path: str, line: str) -> None:
        """Count the assertions of a LINE of PATH's hunk, in a test file or a module of a
        language that keeps its tests there."""
        suffix = PurePosixPath(path).suffix.lower()
        tests = TEST_FILE.search(path) or suffix in INLINE_TESTS
        if tests and ASSERTS.search(line[1:]):
            self.asserts[path] += -1 if line.startswith(ADDED) else 1

    def lowered(self) -> list[tuple[str, str]]:
        """Each test file with fewer assertions, then each coverage threshold that went down
        or is gone (`judged`), with the words that say so."""
        fewer = [
            (path, f"{count} assertion(s) fewer")
            for path, count in sorted(self.asserts.items())
            if count > 0
        ]
        said = [
            judged(
                name,
                *self.thresholds[name],
            )
            for name in sorted(self.thresholds)
        ]
        return [*fewer, *(one for one in said if one)]


def path_of(header: str, side: str) -> str:
    """The path of a git patch header, or empty for /dev/null."""
    field, _, _ = header[4:].partition("\t")
    if field == "/dev/null":
        return ""
    if field.startswith('"'):
        quoted = field[1:-1]
        raw, _ = codecs.escape_decode(quoted.encode())
        field = raw.decode(errors="surrogateescape")
    return field.removeprefix(side)


def blanked(lines: list[str], where: str) -> str:
    """The plan with its code blocks blank, or the landing's refusal of an open fence."""
    try:
        inside = fences.fenced(lines, where)
    except Refusal as error:
        raise Refusal("fence", error.why, error.fix) from error
    return "".join(
        "\n" if index in inside else f"{line}\n" for index, line in enumerate(lines)
    )


def reasons_of(plan: str, where: str) -> dict[str, str]:
    """Each file's reason for a lowered bar, from the `## The bar` section of the PLAN, whose
    file is WHERE, as `- PATH: REASON`, read past its code blocks; none when the
    plan has no such section."""
    text = blanked(plan.splitlines(), where)
    section = SECTION.search(text)
    if not section:
        return {}
    return {
        found.group(1).strip(): found.group(2).strip()
        for found in REASON.finditer(section.group(1))
    }
