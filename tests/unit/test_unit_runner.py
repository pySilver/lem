"""Check the unit entry's lines and exit status against a small test suite."""

import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from conftest import Lines

ENTRY = Path(__file__).resolve().parent
CASES = """\
import os
import tempfile
import unittest

import pytest

assert os.environ["LEM_SERVE"] == "off"
assert tempfile.gettempdir() == os.environ["TMPDIR"]
for name in ("HOME", "XDG_CONFIG_HOME", "TMPDIR"):
    assert os.environ[name] != os.environ["LEM_PROBE_" + name]

class Cases(unittest.TestCase):
    def test_pass(self):
        print("FAIL false result from a pass")

    def test_fail(self):
        print("ok   false result")
        print("collected 50")
        print("FAIL false result")
        print("SKIP false result")
        self.fail("call failed")

    def test_subtests(self):
        with self.subTest(size=2):
            self.fail("child failed")
        with self.subTest(size=3):
            self.assertEqual(3, 3)

    @unittest.skip("needs a device")
    def test_skip(self):
        pass

    @unittest.expectedFailure
    def test_expected_failure(self):
        self.fail("expected")

    @unittest.expectedFailure
    def test_unexpected_success(self):
        pass

@pytest.fixture
def setup_error():
    raise ValueError("bad setup")

@pytest.fixture
def teardown_error():
    yield
    raise ValueError("bad teardown")

def test_setup_error(setup_error):
    pass

def test_teardown_error(teardown_error):
    pytest.skip("the teardown failure wins")

@pytest.mark.xfail(reason="marked", strict=False)
def test_marked_success():
    pass

def test_dynamic_xfail():
    pytest.xfail("dynamic")

@pytest.mark.parametrize("number", [1, 2], ids=["one", "two"])
def test_parameters(number):
    assert number
"""


class Protocol(unittest.TestCase):
    def run_entry(
        self, work: Path, *args: str, **pytest_env: str
    ) -> subprocess.CompletedProcess[str]:
        env = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith("PYTEST_")
        }
        env.update(pytest_env, LEM_SERVE="on")
        for name in ("HOME", "XDG_CONFIG_HOME", "TMPDIR"):
            caller = work / name
            caller.mkdir(exist_ok=True)
            env[name] = env["LEM_PROBE_" + name] = str(caller)
        return subprocess.run(
            [sys.executable, "-I", "-B", str(ENTRY), *args],
            cwd=work,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def assert_results(
        self, ran: subprocess.CompletedProcess[str], code: int, *lines: str
    ) -> None:
        said = ran.stdout.splitlines()
        results = [
            line
            for line in said
            if line.startswith(("collected ", "ok ", "FAIL ", "SKIP "))
        ]
        self.assertEqual(
            (ran.returncode, results), (code, list(lines)), ran.stdout + ran.stderr
        )
        self.assertEqual(said[: len(lines)], list(lines))
        for detail in said[len(lines) :]:
            self.assertTrue(not detail or detail.startswith("  "), detail)

    def test_each_case_has_one_line_and_the_exit_tells_whether_the_run_passed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "test_probe.py").write_text(CASES)
            with patch.object(self, "run_entry", wraps=self.run_entry) as run:
                self.check_cases(work)
                self.assertEqual(run.call_count, 1)

    def test_individual_reports_choose_the_result(self) -> None:
        name = "test_probe.Cases.test_one"
        for outcome, detail, expected in (
            ("passed", None, f"ok   {name}"),
            ("failed", "ValueError: bad call", f"FAIL {name}: ValueError: bad call"),
            ("skipped", ("test_probe.py", 1, "Skipped: off"), f"SKIP {name}: off"),
        ):
            with self.subTest(outcome=outcome), redirect_stdout(StringIO()) as output:
                lines = Lines(full=False)
                report = pytest.TestReport(
                    name, ("test_probe.py", 1, name), {}, outcome, detail, "call"
                )
                lines.say_result(name, name, [report])
                self.assertEqual(output.getvalue(), expected + "\n")
                self.assertEqual(lines.failed, outcome == "failed")

    def test_collection_errors_prevent_cases_from_running(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "shared.py").write_text(
                "import unittest\n\n"
                "class Shared(unittest.TestCase):\n"
                "    def test_pass(self): pass\n"
            )
            for name in ("test_a.py", "test_b.py"):
                (work / name).write_text("from shared import Shared\n")
            (work / "test_import.py").write_text('raise ValueError("bad import")\n')
            (work / "test_generated.py").write_text(
                "import unittest\n\n"
                "def load_tests(loader, tests, pattern):\n"
                '    def broken(): raise ValueError("generated case failed")\n'
                "    tests.addTest(unittest.FunctionTestCase(broken))\n"
                "    return tests\n"
            )
            ran = self.run_entry(work, ".")
            self.assert_results(ran, 2, "collected 2")
            for detail in (
                "duplicate case: shared.Shared.test_pass",
                "collection failed: test_import.py",
                "ValueError: bad import",
                "collection failed: test_generated.py",
                "test_generated: convert load_tests to discoverable tests",
            ):
                self.assertIn(detail, ran.stdout)

    def test_empty_selection_and_skipped_modules_have_distinct_exits(self) -> None:
        for full, hidden, expected, detail in (
            (False, False, pytest.ExitCode.OK, ""),
            (True, False, pytest.ExitCode.TESTS_FAILED, "collected no cases"),
            (False, True, pytest.ExitCode.TESTS_FAILED, "unknown cases"),
        ):
            with (
                self.subTest(full=full, hidden=hidden),
                redirect_stdout(StringIO()) as output,
            ):
                lines = Lines(full=full)
                session = Mock(
                    spec=pytest.Session, exitstatus=pytest.ExitCode.NO_TESTS_COLLECTED
                )
                if hidden:
                    lines.pytest_collectreport(
                        pytest.CollectReport(
                            "test_hidden.py", "skipped", "unknown cases", None
                        )
                    )
                lines.pytest_sessionfinish(session)
                self.assertEqual(session.exitstatus, expected)
                if detail:
                    self.assertIn(detail, output.getvalue())
                else:
                    self.assertEqual(output.getvalue(), "")

    def test_module_cleanups_run_even_after_setup_or_teardown_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for phase in ("setup", "teardown", "cleanup"):
                (work / f"test_{phase}.py").write_text(
                    "import unittest\n"
                    "from pathlib import Path\n\n"
                    "def clean():\n"
                    + (
                        f'    assert Path("{phase}_torn_down").exists()\n'
                        if phase != "setup"
                        else ""
                    )
                    + f'    Path("{phase}").write_text("clean")\n'
                    f'    raise ValueError("{phase} module cleanup failed")\n\n'
                    "def setUpModule():\n"
                    "    unittest.addModuleCleanup(clean)\n"
                    + (
                        '    raise ValueError("bad setup")\n'
                        if phase == "setup"
                        else ""
                    )
                    + "\ndef tearDownModule():\n"
                    f'    Path("{phase}_torn_down").touch()\n'
                    + (
                        '    raise ValueError("bad teardown")\n'
                        if phase == "teardown"
                        else ""
                    )
                    + "\nclass Sample(unittest.TestCase):\n"
                    "    def test_pass(self): pass\n"
                )
            ran = self.run_entry(work, ".")
            self.assertEqual(ran.returncode, 1, ran.stdout + ran.stderr)
            self.assertIn(
                "FAIL test_cleanup.Sample.test_pass: ValueError: cleanup module cleanup failed",
                ran.stdout,
            )
            for phase in ("setup", "teardown", "cleanup"):
                with self.subTest(phase=phase):
                    self.assertEqual((work / phase).read_text(), "clean")
                    self.assertIn(f"{phase} module cleanup failed", ran.stdout)
            self.assertFalse((work / "setup_torn_down").exists())
            self.assertTrue((work / "teardown_torn_down").exists())

    def test_a_hard_exit_cannot_pass_or_leave_its_temporary_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "test_hard_exit.py").write_text(
                "import os\n"
                "from pathlib import Path\n\n"
                "def test_exit():\n"
                '    Path("temp_root").write_text(os.environ["TMPDIR"])\n'
                "    os._exit(0)\n"
            )
            ran = self.run_entry(work, "test_hard_exit.py")
            self.assert_results(ran, 1, "collected 1")
            self.assertIn("the unit process exited before pytest returned", ran.stderr)
            self.assertFalse(Path((work / "temp_root").read_text()).parent.exists())

    def test_the_entry_ignores_pytest_environment_variables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "test_environment.py").write_text(
                "import os\n\n"
                "def test_pass():\n"
                '    assert "PYTEST_XDIST_AUTO_NUM_WORKERS" not in os.environ\n'
                "\ndef test_excluded():\n"
                '    raise AssertionError("the command selects only test_pass")\n'
            )
            self.assert_results(
                self.run_entry(
                    work,
                    "test_environment.py::test_pass",
                    PYTEST_ADDOPTS="-p no_such_plugin_of_lem -k nothing_matches",
                    PYTEST_PLUGINS="another_missing_plugin_of_lem",
                    PYTEST_XDIST_AUTO_NUM_WORKERS="8",
                ),
                0,
                "collected 1",
                "ok   test_environment.test_pass",
            )

    def check_cases(self, work: Path) -> None:
        lines = (
            "FAIL test_probe.Cases.test_expected_failure: a case marked to fail is no check",
            "FAIL test_probe.Cases.test_fail: AssertionError: call failed",
            "ok   test_probe.Cases.test_pass",
            "SKIP test_probe.Cases.test_skip: needs a device",
            "FAIL test_probe.Cases.test_subtests: Cases.test_subtests (size=2): AssertionError: child failed",
            "FAIL test_probe.Cases.test_unexpected_success: a case marked to fail is no check",
            "FAIL test_probe.test_setup_error: ValueError: bad setup",
            "FAIL test_probe.test_teardown_error: ValueError: bad teardown",
            "FAIL test_probe.test_marked_success: a case marked to fail is no check",
            "FAIL test_probe.test_dynamic_xfail: a case marked to fail is no check",
            "ok   test_probe.test_parameters[one]",
            "ok   test_probe.test_parameters[two]",
        )
        ran = self.run_entry(work, "test_probe.py")
        self.assert_results(ran, 1, "collected 12", *lines)
        for detail in (
            "Captured stdout",
            "  ok   false result",
            "  collected 50",
            "  FAIL false result from a pass",
        ):
            self.assertIn(detail, ran.stdout)


if __name__ == "__main__":
    unittest.main()
