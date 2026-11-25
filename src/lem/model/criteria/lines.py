"""A line under a criterion: a test, why it has none, a step of its case, or more of its text
(`criteria.parse` on `main`).

A test names its command and its files, each in backticks. A criterion with more than one
condition carries its case, numbered steps under its sentence and before its tests; a label
between two runs of it ("After:") is a line of its own, and a step written over two lines is one.
"""

import re

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.criterion import Criterion, CriterionTest

TEST = re.compile(r"^\s+-\s+test:\s+`([^`]+)`\s+in\s+(.+)$")
NO_TEST = re.compile(r"^\s+-\s+no test:\s+(.+)$")
FILES = re.compile(r"`([^`]+)`")
STEP = re.compile(r"^\s+\d+[.)]\s+\S")
CODE = "criteria-form"
UNDER = "under a criterion a line is - test: `COMMAND` in `FILE`, or - no test: REASON"


def tested(criterion: Criterion, command: str, named: str, where: str) -> Criterion:
    """The criterion with one more test; a test that names no file in backticks is
    refused."""
    files = tuple(FILES.findall(named))
    if not files:
        raise Refusal(
            CODE,
            f"{where}: a test names its command and its files in backticks",
            "write it as - test: `COMMAND` in `FILE`",
        )
    test = CriterionTest(command=command.strip(), files=files)
    return replace(criterion, tests=(*criterion.tests, test))


def worded(criterion: Criterion, line: str) -> Criterion:
    """The criterion with one more line of its words: a step of its case, a label between two
    runs of it, the rest of a step, or the rest of its sentence."""
    said = line.strip()
    case = criterion.case
    if STEP.match(line) or (case and said.endswith(":")):
        return replace(criterion, case=(*case, said))
    if case:
        last = " ".join((case[-1], said))
        return replace(criterion, case=(*case[:-1], last))
    return replace(criterion, text=f"{criterion.text} {said}")


def under(criterion: Criterion, line: str, where: str) -> Criterion:
    """The criterion with one more line under it; a list line of another form, and words after
    its tests, are refused with the line."""
    test, none = TEST.match(line), NO_TEST.match(line)
    if test:
        return tested(criterion, test[1], test[2], where)
    if none:
        return replace(criterion, no_test=none[1].strip())
    said = line.strip()
    if said.startswith("- "):
        raise Refusal(CODE, f"{where}: {said!r} is no line of a criterion", UNDER)
    if criterion.tests or criterion.no_test:
        raise Refusal(
            CODE,
            f"{where}: the text of a criterion comes before its tests, and {said!r} comes "
            "after them",
            "move the line above the criterion's tests",
        )
    return worded(criterion, line)
