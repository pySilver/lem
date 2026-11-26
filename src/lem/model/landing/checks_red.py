"""The rules of the check that each criterion's tests pass on the branch and fail on the base
(`criteria.needs_serial`, `unstarted`, `shell_script`, `python_script` and `cmd_red` on `main`).

Which test runs under the serial lock and which script file it starts (`Command`), the tests and
the criteria without one, what went wrong with a test from its two exits, and the refusals of a
run that may not start or did not hold. The facts
come in as arguments: the app runs git and the tests.
"""

import contextlib
import re
import shlex
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.red import RedTest, WithoutTest

if TYPE_CHECKING:
    from collections.abc import Sequence

    from lem.records.criterion import Criterion
    from lem.records.red import Inputs, Red

# What one word of a program's arguments says of its script file: the next word is it, the next
# word is this option's operand, there is none (standard input, a command, a module), this word
# is an option on its own, or this word is it.
NEXT = "next"
SKIP = "skip"
NONE = "none"
ON = "on"
SCRIPT = "script"
# The acts that take the next word, and those after which the next word is read.
TAKE_NEXT = frozenset((NEXT, SKIP))
READ_ON = frozenset((SKIP, ON))
LONG = "--"
DASH = "-"
# The shells a test command may start a script with, by the name of the program.
SHELLS = frozenset(("sh", "bash", "dash", "ksh", "zsh"))
# Python, by the name of the program: `python`, `python3` and `python3.N`, which end with exit 2
# when their script file is not there (`python3 -I -B missing.py`, checked on 2026-11-21).
PYTHON = re.compile(r"python(3(\.\d+)?)?")
# The exits of a shell whose command could not start: found and not run, and not found.
NOT_STARTED = frozenset((126, 127))
CODE = "criteria"


@dataclass(frozen=True, kw_only=True, slots=True)
class Grammar:
    """How a program's arguments name the script file it runs: the marks of an option, the
    short options whose operand is a command or a module, the short options that take the rest
    of their word or the next one, and the words with a meaning of their own."""

    marks: tuple[str, ...]
    operand: frozenset[str]
    takes: str = ""
    exact: tuple[tuple[str, str], ...]

    def script(self, words: Sequence[str]) -> str | None:
        """The script file the arguments start, or None when they start none."""
        rest = iter(words)
        for word in rest:
            act = self.act(word)
            operand = next(rest, None) if act in TAKE_NEXT else None
            if act not in READ_ON:
                return {NEXT: operand, SCRIPT: word}.get(act)
        return None

    def act(self, word: str) -> str:
        """What one word says of the script file. Short options may share one word (`-IB`);
        the letters after one that takes an operand are that operand."""
        known = dict(self.exact).get(word)
        if known:
            return known
        if word.startswith(LONG):
            return NONE
        if not word.startswith(self.marks):
            return SCRIPT
        marks = [word.find(mark) for mark in self.takes]
        # An option starts with a sign, so its operand mark cannot be at index zero.
        found = [index for index in marks if index >= 0]  # pragma: no mutate
        # None and the length both slice to the end and leave no operand to take.
        cut = min(found, default=len(word))  # pragma: no mutate
        letters = set(word[1:cut])
        if word.startswith(DASH) and letters & self.operand:
            return NONE
        return SKIP if cut == len(word) - 1 else ON


SHELL_ARGS = Grammar(
    marks=(DASH, "+"),
    operand=frozenset("c"),
    exact=(
        ("-o", SKIP),
        ("+o", SKIP),
        (LONG, NEXT),
        (DASH, NONE),
        ("+", NONE),
    ),
)
PYTHON_ARGS = Grammar(
    marks=(DASH,),
    operand=frozenset("cm"),
    takes="WX",
    exact=((LONG, NEXT), ("--check-hash-based-pycs", SKIP), (DASH, NONE)),
)


@dataclass(frozen=True, slots=True)
class Command:
    """A line for the shell, a test's command or a line of `checks.serial`, read as its words."""

    line: str

    def words(self) -> list[str]:
        """The line's words as the shell splits them; none for a line it cannot split."""
        found: list[str] = []
        with contextlib.suppress(ValueError):
            found = shlex.split(self.line)
        return found

    def needs_serial(self, serial: Sequence[str]) -> bool:
        """Whether the test belongs to a suite that needs the machine to itself: its command
        starts with the words of one of `checks.serial` (`starts`)."""
        words = self.words()
        return any(Command(line).starts(words) for line in serial)

    def starts(self, words: Sequence[str]) -> bool:
        """Whether a command's words start with this line's words, the last of which may also
        be a folder of the test's path (`sh tests/e2e` holds `sh tests/e2e/export.sh`). Words,
        so that a test's own file after the suite's command still counts, and `npx playwright`
        never matches `npx play`."""
        own = self.words()
        if not own or len(words) < len(own):
            return False
        size = len(own) - 1
        word = words[size]
        folder = "".join((own[-1].rstrip("/"), "/"))
        inside = word == own[-1] or word.startswith(folder)
        return inside and words[:size] == own[:size]

    def script(self) -> str | None:
        """The script file the command starts a shell or Python on; None when it starts none.
        Its exit does not say whether the file was there: bash ends `sh FILE` with no FILE
        with 127, dash with 2, and Python with 2, which an assertion's exit may be too."""
        words = self.words()
        # With no words, neither fallback name matches a shell or Python.
        program = PurePosixPath(words[0]).name if words else ""  # pragma: no mutate
        if program in SHELLS:
            return SHELL_ARGS.script(words[1:])
        if PYTHON.fullmatch(program):
            return PYTHON_ARGS.script(words[1:])
        return None


def tests_of(criteria: Sequence[Criterion]) -> tuple[RedTest, ...]:
    """Each test of the criteria, in order, as its outcome will name it, before it ran."""
    return tuple(
        RedTest(criterion=each.number, command=test.command, files=test.files)
        for each in criteria
        for test in each.tests
    )


def without_of(criteria: Sequence[Criterion]) -> tuple[WithoutTest, ...]:
    """Each criterion that names no test, and why."""
    return tuple(
        WithoutTest(criterion=each.number, why=each.no_test)
        for each in criteria
        if each.no_test is not None
    )


def problem_of(green: int, red: int, lacked: str | None) -> str | None:
    """What went wrong with one test from its exit on the branch (`green`) and on the base
    (`red`), and the script file it starts that the base lacked; None when it holds."""
    if green:
        return (
            f"fails in a fresh worktree of the branch (exit {green}). If it passes in the "
            "task's worktree, it needs something a fresh one lacks: put the commands that "
            "make it into checks.setup of .lem/settings.toml"
        )
    if not red:
        return "passes on the base commit too, so it does not test the change"
    if red not in NOT_STARTED and lacked is None:
        return None
    missing = f": its script file {lacked} is not on the base commit" if lacked else ""
    return (
        f"does not start on the base commit (exit {red}{missing}), so its failure there "
        "proves nothing. If a file it needs is a helper of the test, name it among the "
        "criterion's files; if what is absent is the change itself, make the test fail on it "
        "and not stop before it"
    )


def precondition(
    criteria: Sequence[Criterion], dirty: str, found: Inputs, onto: str, *, fast: bool
) -> Refusal | None:
    """Why the run may not start: a criterion with neither a test nor a reason for none,
    changes nobody committed, or a branch with no commit beyond the base; None when it may."""
    untested = [each.number for each in criteria if not each.tests and not each.no_test]
    held_in = "the criteria.md of the task on the fast track" if fast else "the plan"
    if untested:
        return Refusal(
            CODE,
            f"criterion {untested[0]} names no test: every criterion is held by a test at "
            "the end of a build",
            f"add `- test: `COMMAND` in `FILE`` under it in {held_in}, or `- no test: "
            "REASON` when no test can hold it",
        )
    if dirty:
        return Refusal(
            CODE,
            f"the worktree has changes nobody committed:\n{dirty}",
            "commit them or remove them: this check runs what the branch holds, and they "
            "are not in it",
        )
    if found.base == found.tip:
        return Refusal(
            CODE,
            f"the branch has no commit beyond {onto}, so there is no change for a test to "
            "hold",
            "commit the change on the branch, then run the check again",
        )
    return None


def failed(red: Red) -> Refusal | None:
    """The refusal of a run that did not hold, in the words of its first test with a problem;
    None when it holds. A builder repairs the test or the plan: the check is never edited to
    pass."""
    bad = next((test for test in red.tests if test.problem), None)
    # The runner sets ok exactly when no test has a problem.
    if red.ok or bad is None:  # pragma: no mutate
        return None
    return Refusal(
        CODE,
        f"criterion {bad.criterion}: `{bad.command}` {bad.problem}",
        "a builder repairs the test or the plan, and runs the check again; the check is "
        "never edited to pass",
    )
