"""The unit level as a suite of tests/all.sh: `.venv/bin/python -B tests/unit`.

It runs what `.venv/bin/python -B -m unittest discover -s tests/unit` runs, on the app's
own Python, the checkout's .venv that `uv sync` makes, and refuses another, and prints it in the form every
suite prints (tests/checks.sh): `collected N`, then one line for each case, `ok   ID`, `FAIL ID: WHY`
or `SKIP ID: WHY`, then the traceback of each case that failed. One unittest case is one check. The
exit is 1 when a case failed or the lines do not add up to the cases collected: a case whose
subtest failed prints no line of its own, so its count does not add up.
"""

import sys
import unittest
from pathlib import Path
from types import TracebackType

HERE = Path(__file__).resolve().parent
# the checkout's .venv, the one Python the unit level runs on
VENV = HERE.parents[1] / ".venv"
# what unittest hands a result for a case that failed: sys.exc_info()'s form
ExcInfo = (
    tuple[type[BaseException], BaseException, TracebackType] | tuple[None, None, None]
)


class Lines(unittest.TestResult):
    """A result that prints one line for each case as it ends."""

    def __init__(self) -> None:
        super().__init__()
        self.printed = 0

    def say(self, line: str) -> None:
        print(line, flush=True)
        self.printed += 1

    def addSuccess(self, test: unittest.TestCase) -> None:  # noqa: N802 - unittest's name
        super().addSuccess(test)
        self.say(f"ok   {test.id()}")

    def addFailure(self, test: unittest.TestCase, err: ExcInfo) -> None:  # noqa: N802 - unittest's name
        super().addFailure(test, err)
        self.say(f"FAIL {test.id()}: {self.failures[-1][1].strip().splitlines()[-1]}")

    def addError(self, test: unittest.TestCase, err: ExcInfo) -> None:  # noqa: N802 - unittest's name
        super().addError(test, err)
        self.say(f"FAIL {test.id()}: {self.errors[-1][1].strip().splitlines()[-1]}")

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:  # noqa: N802 - unittest's name
        super().addSkip(test, reason)
        self.say(f"SKIP {test.id()}: {reason}")

    def addExpectedFailure(self, test: unittest.TestCase, err: ExcInfo) -> None:  # noqa: N802 - unittest's name
        super().addExpectedFailure(test, err)
        self.say(f"FAIL {test.id()}: a case marked to fail is no check")

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:  # noqa: N802 - unittest's name
        super().addUnexpectedSuccess(test)
        self.say(f"FAIL {test.id()}: a case marked to fail is no check")


def main() -> int:
    if Path(sys.prefix).resolve() != VENV.resolve():
        print(
            f"FAIL the unit level runs on {VENV / 'bin' / 'python'}, not on "
            f"{sys.executable}: run uv sync at the root of the checkout, then "
            ".venv/bin/python -B tests/unit"
        )
        return 1
    # the test files set it too, but only after their own import, which would leave
    # their cache
    sys.dont_write_bytecode = True
    suite = unittest.defaultTestLoader.discover(str(HERE), top_level_dir=str(HERE))
    collected = suite.countTestCases()
    print(f"collected {collected}", flush=True)
    result = Lines()
    suite.run(result)
    for test, trace in [*result.failures, *result.errors]:
        print(f"\n== {test.id()}\n{trace}")
    return 0 if result.wasSuccessful() and result.printed == collected else 1


if __name__ == "__main__":
    sys.exit(main())
