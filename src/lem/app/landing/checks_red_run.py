"""One run of the check of the criteria: each side's worktree, its `checks.setup`, and each test,
on the branch and on the base with the test files laid over it (`criteria.cmd_red` on `main`).

Each command, and each git that may run a hook of the repository (`worktree add`, `checkout`),
starts in a process group of its own, which is stopped when it ends and when the run is cut off,
with its output in a file or nowhere: a process a command left behind would hold a pipe open. A
test of a suite in `checks.serial` runs under the repository's serial lock, through `lem serial`.
"""

import os
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.git_cli_shell import GIT, own
from lem.kernel import errors, procs
from lem.model.landing import checks_red
from lem.records.red import Inputs, Red, RedTest, SetupRun, WithoutTest

if TYPE_CHECKING:
    from lem.records.base import Moment

# How long a command gets after its term and after its kill, in seconds, and how long the serial
# wrapper gets after its term: its own stop gives its command a term, 3 s, a kill and 3 s more,
# and one second is left for its exit. A wrapper killed before its stop ends would leave a test
# that ignores a term running, with the lock free.
GRACE = 3.0
SERIAL_GRACE = 7.0
SHELL = "/bin/sh"
BRANCH = "branch"
BASE = "base"
CODE = "criteria"
# The tests and the setup runs of a run; the script file each test starts that a worktree
# lacked; and one side's exits of the tests, with what its worktree lacked.
type Tests = tuple[RedTest, ...]
type Setups = tuple[SetupRun, ...]
type Lacked = tuple[str | None, ...]
type Side = tuple[tuple[int, ...], Lacked]


def exit_of(
    argv: list[str],
    where: Path,
    output: procs.Output,
    env: procs.Environment,
    grace: float,
) -> int:
    """Run one command in a group of its own, its output to `output` or nowhere, and give its
    exit; the group is stopped after it, and when the run is cut off while it runs."""
    with ExitStack() as stack:
        sink = output or stack.enter_context(Path(os.devnull).open("wb"))
        proc = procs.start_group(argv, where, env, sink)
        stack.callback(procs.stop_group, proc, grace, GRACE, whole_group=False)
        return proc.wait()


def lacking(tests: Tests, place: Path) -> Lacked:
    """The script file each test starts that the worktree lacks, or None."""
    scripts = [checks_red.Command(test.command).script() for test in tests]
    there = [name is None or (place / name).is_file() for name in scripts]
    rows = zip(there, scripts, strict=True)
    return tuple(None if found else name for found, name in rows)


def outcome(test: RedTest, passed: int, failed: int, lacked: str | None) -> RedTest:
    """One test's outcome on both sides, and what went wrong with it."""
    problem = checks_red.problem_of(passed, failed, lacked)
    return msgspec.structs.replace(
        test, on_branch=passed, on_base=failed, problem=problem
    )


class Run(msgspec.Struct, frozen=True, kw_only=True):
    """What one run needs: the main checkout, its five inputs, each test as its outcome will
    name it, the criteria without one, their digest, the files laid over the base, and the
    files the branch changed."""

    checkout: Path
    found: Inputs
    tests: Tests
    without: tuple[WithoutTest, ...]
    digest: str
    laid: tuple[str, ...]
    changed: tuple[str, ...]

    def git(self, where: Path, *args: str) -> None:
        """A git that may run a hook, in a group of its own; what it says goes to a file, never
        a pipe, and a failure is refused in its words."""
        with tempfile.TemporaryFile() as output:
            argv = [GIT, "-C", str(where), *args]
            code = exit_of(argv, where, output, own(os.environ), GRACE)
            output.seek(0)
            words = output.read().decode(errors="replace").strip()
        if code:
            named = " ".join(args[:2])
            raise errors.Refusal(
                CODE,
                f"git {named} failed: {words}",
                "the owner reads git's words, puts the repository right, and runs the check "
                "again",
            )

    def test(self, command: str, where: Path) -> int:
        """Run one test through a shell, as the checks run; a test of a suite that needs the
        machine to itself runs under the serial lock, through `lem serial`."""
        if not checks_red.Command(command).needs_serial(self.found.serial):
            return exit_of([SHELL, "-c", command], where, None, os.environ, GRACE)
        repo = str(self.checkout)
        argv = [
            sys.executable,
            "-B",
            "-m",
            "lem",
            "--repo",
            repo,
            "serial",
            "--",
            command,
        ]
        return exit_of(argv, where, None, os.environ, SERIAL_GRACE)

    def setup(self, side: str, place: Path, setups: list[SetupRun]) -> None:
        """Run each command of `checks.setup` in a fresh worktree; one that fails is refused, as
        no test could run there."""
        for command in self.found.setup:
            code = exit_of([SHELL, "-c", command], place, None, os.environ, GRACE)
            setups.append(SetupRun(on=side, command=command, exit=code))
            if code:
                fresh = (
                    "a fresh worktree of the branch"
                    if side == BRANCH
                    else "a fresh worktree of the base commit, with the test files laid over it"
                )
                raise errors.Refusal(
                    CODE,
                    f"`{command}` of checks.setup failed in {fresh} (exit {code}), so no test "
                    "could run there",
                    "correct that command in .lem/settings.toml",
                )

    def side(self, side: str, place: Path, setups: list[SetupRun]) -> Side:
        """Make one side's worktree, set it up, and run each test there: their exits, and the
        script file each starts that the worktree lacked before any test ran there."""
        rev = self.found.tip if side == BRANCH else self.found.base
        self.git(self.checkout, "worktree", "add", "-q", "--detach", str(place), rev)
        if side == BASE and self.laid:
            self.git(place, "checkout", self.found.tip, "--", *self.laid)
        self.setup(side, place, setups)
        absent = lacking(self.tests, place)
        codes = tuple(self.test(test.command, place) for test in self.tests)
        return codes, absent

    def outcomes(self, places: tuple[Path, Path]) -> tuple[Tests, Setups]:
        """Run both sides, the branch first: each test's outcome, and each setup command's
        exit."""
        setups: list[SetupRun] = []
        green, _ = self.side(BRANCH, places[0], setups)
        red, absent = self.side(BASE, places[1], setups)
        found = map(outcome, self.tests, green, red, absent, strict=True)
        return tuple(found), tuple(setups)

    def red(self, now: Moment, tests: Tests, setups: Setups) -> Red:
        """The run as its record keeps it: it holds when no test has a problem. What the base
        run lacked is every file the branch changed that is not a named test file."""
        lacked = sorted(set(self.changed) - set(self.laid))
        return Red(
            ok=not any(test.problem for test in tests),
            at=now,
            digest=self.digest,
            inputs=self.found,
            tests=tests,
            without_a_test=self.without,
            run_without=tuple(lacked),
            setup=setups,
        )
