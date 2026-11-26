"""The rules of the check that each criterion's tests pass on the branch and fail on the base
(`model/landing/checks_red.py`): which test runs under the serial lock, which script file a test
starts, what went wrong with a test from its two exits, and the refusals of a run that may not
start or did not hold."""

from datetime import UTC, datetime

import pytest

from lem.model.landing import checks_red
from lem.records.criterion import Criterion, CriterionTest
from lem.records.red import Inputs, Red, RedTest, WithoutTest

TIP = "a" * 40
BASE = "b" * 40
FOUND = Inputs(tip=TIP, base=BASE)
MOMENT = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)
TESTED = Criterion(
    number=1,
    text="the login works",
    tests=(CriterionTest(command="sh tests/login.sh", files=("tests/login.sh",)),),
)
UNTESTED = Criterion(number=2, text="the README says so")
REASONED = Criterion(
    number=3, text="the colors stay", no_test="no test can see a color"
)


@pytest.mark.parametrize(
    ("command", "serial"),
    [
        ("npx playwright test", ("npx playwright",)),
        ("npx playwright test e2e/a.spec.ts", ("npx playwright",)),
        ("sh tests/e2e/export.sh", ("sh tests/e2e",)),
        ("sh tests/e2e/export.sh", ("sh tests/e2e/",)),
        ("sh tests/unit.sh", ("make e2e", "sh tests/unit.sh")),
        ("sh 'tests/e2e/a b.sh'", ("sh tests/e2e",)),
        ("pytest tests/unit", ("pytest",)),
        ("uv run pytest tests/cacheX/a.py", ("uv run pytest tests/cacheX/",)),
    ],
)
def test_a_test_needs_the_serial_lock_when_its_words_start_with_a_serial_line(
    command: str, serial: tuple[str, ...]
) -> None:
    assert checks_red.Command(command).needs_serial(serial)


@pytest.mark.parametrize(
    ("command", "serial"),
    [
        ("npx play test", ("npx playwright",)),
        ("npx playwright", ("npx play",)),
        ("sh tests/e2e-other/export.sh", ("sh tests/e2e",)),
        ("bash tests/e2e/export.sh", ("sh tests/e2e",)),
        ("sh", ("sh tests/e2e",)),
        ("sh 'tests/e2e/unclosed.sh", ("sh tests/e2e",)),
        ("sh tests/e2e/a.sh", ("sh 'tests/e2e",)),
        ("sh tests/e2e/a.sh", ("",)),
        ("sh tests/e2e/a.sh", ()),
    ],
)
def test_a_test_whose_words_start_with_no_serial_line_runs_without_the_lock(
    command: str, serial: tuple[str, ...]
) -> None:
    assert not checks_red.Command(command).needs_serial(serial)


@pytest.mark.parametrize(
    ("command", "script"),
    [
        ("sh tests/a.sh", "tests/a.sh"),
        ("/bin/bash -e tests/a.sh --flag", "tests/a.sh"),
        ("bash -o pipefail tests/a.sh", "tests/a.sh"),
        ("bash +o pipefail tests/a.sh", "tests/a.sh"),
        ("zsh -- -odd.sh", "-odd.sh"),
        ("sh -c 'exit 1'", None),
        ("sh -ec 'exit 1'", None),
        ("sh -", None),
        ("bash --login a.sh", None),
        ("sh -e", None),
        ("sh --", None),
        ("python3 -W", None),
        ("python3 tests/a.py", "tests/a.py"),
        ("python -I -B tests/a.py", "tests/a.py"),
        ("python3.14 -IB tests/a.py", "tests/a.py"),
        ("python3 -m pytest tests", None),
        ("python3 -Im pytest", None),
        ("python3 -c 'print(1)'", None),
        ("python3 -", None),
        ("python3 --version", None),
        ("python3 -W ignore tests/a.py", "tests/a.py"),
        ("python3 -Wignore::DeprecationWarning tests/a.py", "tests/a.py"),
        ("python3 -X dev tests/a.py", "tests/a.py"),
        ("python3 -IX dev tests/a.py", "tests/a.py"),
        ("python3 --check-hash-based-pycs never tests/a.py", "tests/a.py"),
        ("python3 -- tests/a.py", "tests/a.py"),
        ("pythonista a.py", None),
        ("node a.js", None),
        ("make test", None),
        ("", None),
        ("sh 'unclosed", None),
    ],
)
def test_the_script_file_a_shell_or_python_starts_is_named(
    command: str, script: str | None
) -> None:
    assert checks_red.Command(command).script() == script


@pytest.mark.parametrize(
    ("green", "red", "lacked", "start"),
    [
        (0, 1, None, None),
        (0, 2, None, None),
        (1, 1, None, "fails in a fresh worktree of the branch (exit 1)."),
        (0, 0, None, "passes on the base commit too, so it does not test the change"),
        (0, 127, None, "does not start on the base commit (exit 127), so"),
        (0, 126, None, "does not start on the base commit (exit 126), so"),
        (
            0,
            2,
            "tests/a.sh",
            (
                "does not start on the base commit (exit 2: its script file tests/a.sh is "
                "not on the base commit), so"
            ),
        ),
    ],
)
def test_a_test_holds_when_it_passes_on_the_branch_and_fails_where_it_started_on_the_base(
    green: int, red: int, lacked: str | None, start: str | None
) -> None:
    problem = checks_red.problem_of(green, red, lacked)
    if start is None:
        assert problem is None
    else:
        assert problem is not None
        assert problem.startswith(start)


def test_a_test_that_fails_on_the_branch_names_checks_setup() -> None:
    problem = checks_red.problem_of(1, 1, None)
    assert problem is not None
    assert problem == (
        "fails in a fresh worktree of the branch (exit 1). If it passes in the "
        "task's worktree, it needs something a fresh one lacks: put the commands that "
        "make it into checks.setup of .lem/settings.toml"
    )
    missing = checks_red.problem_of(0, 2, "tests/login.sh")
    assert missing == (
        "does not start on the base commit (exit 2: its script file tests/login.sh is not "
        "on the base commit), so its failure there proves nothing. If a file it needs is a "
        "helper of the test, name it among the criterion's files; if what is absent is the "
        "change itself, make the test fail on it and not stop before it"
    )


def test_the_tests_and_the_criteria_without_one_come_in_the_criteria_s_order() -> None:
    two = Criterion(
        number=4,
        text="both",
        tests=(
            CriterionTest(command="sh a.sh", files=("a.sh",)),
            CriterionTest(command="sh b.sh", files=("b.sh", "c.sh")),
        ),
    )
    tests = checks_red.tests_of((TESTED, REASONED, two))
    assert [(test.criterion, test.command, test.files) for test in tests] == [
        (1, "sh tests/login.sh", ("tests/login.sh",)),
        (4, "sh a.sh", ("a.sh",)),
        (4, "sh b.sh", ("b.sh", "c.sh")),
    ]
    assert all(test.on_branch is None and test.problem is None for test in tests)
    assert checks_red.without_of((TESTED, REASONED, two)) == (
        WithoutTest(criterion=3, why="no test can see a color"),
    )


def test_a_criterion_with_neither_a_test_nor_a_reason_is_refused() -> None:
    refusal = checks_red.precondition(
        (TESTED, UNTESTED), "", FOUND, "origin/main", fast=False
    )
    assert refusal is not None
    assert refusal.code == "criteria"
    assert refusal.why == (
        "criterion 2 names no test: every criterion is held by a test at the end of a build"
    )
    assert refusal.fix == (
        "add `- test: `COMMAND` in `FILE`` under it in the plan, or `- no test: "
        "REASON` when no test can hold it"
    )
    fast = checks_red.precondition((UNTESTED,), "", FOUND, "origin/main", fast=True)
    assert fast is not None
    assert fast.fix == (
        "add `- test: `COMMAND` in `FILE`` under it in the criteria.md of the task on the "
        "fast track, or `- no test: REASON` when no test can hold it"
    )


def test_changes_nobody_committed_are_refused() -> None:
    refusal = checks_red.precondition(
        (TESTED,), " M a.py", FOUND, "origin/main", fast=False
    )
    assert refusal is not None
    assert refusal.why == "the worktree has changes nobody committed:\n M a.py"
    assert refusal.code == "criteria"
    assert refusal.fix == (
        "commit them or remove them: this check runs what the branch holds, and they are not in it"
    )


def test_a_branch_with_no_commit_beyond_the_base_is_refused() -> None:
    same = Inputs(tip=TIP, base=TIP)
    refusal = checks_red.precondition((TESTED,), "", same, "origin/main", fast=False)
    assert refusal is not None
    assert refusal.code == "criteria"
    assert refusal.why == (
        "the branch has no commit beyond origin/main, so there is no change for a test to hold"
    )
    assert refusal.fix == "commit the change on the branch, then run the check again"


def test_a_run_that_may_start_is_not_refused() -> None:
    assert (
        checks_red.precondition((TESTED, REASONED), "", FOUND, "main", fast=False)
        is None
    )


def test_a_run_that_did_not_hold_is_refused_in_the_words_of_its_first_problem() -> None:
    held = RedTest(criterion=1, command="sh a.sh", on_branch=0, on_base=1)
    wrong = RedTest(
        criterion=2, command="sh b.sh", on_branch=0, on_base=0, problem="passes there"
    )
    later = RedTest(
        criterion=3, command="sh c.sh", on_branch=1, on_base=1, problem="later"
    )
    bad = Red(ok=False, at=MOMENT, digest="d", inputs=FOUND, tests=(held, wrong, later))
    refusal = checks_red.failed(bad)
    assert refusal is not None
    assert refusal.code == "criteria"
    assert refusal.why == "criterion 2: `sh b.sh` passes there"
    assert refusal.fix == (
        "a builder repairs the test or the plan, and runs the check again; the check is "
        "never edited to pass"
    )
    good = Red(ok=True, at=MOMENT, digest="d", inputs=FOUND, tests=(held,))
    assert checks_red.failed(good) is None
