"""The entry's lines and exit status, run on a scratch copy of it with a small suite of probes:
one line for each case, a failed subtest fails its case, `os._exit` fails the run, the caller's
pytest and Lem variables never reach a case, and a selection that collects nothing fails."""

import os
import re
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest

from conftest import Lines
from fakes.repo import run_git

TESTS = Path(__file__).resolve().parents[2]
ROOT = TESTS.parent
ENTRY_FILES = ("__main__.py", "conftest.py", "levels.py", "gates.py")
CASES = """\
import os
import tempfile
import unittest

import pytest

assert os.environ["LEM_SERVE"] == "off"
assert tempfile.gettempdir() == os.environ["TMPDIR"]
for name in ("HOME", "XDG_CONFIG_HOME", "TMPDIR"):
    assert os.environ[name] != os.environ["CALLER_" + name]
for name in ("PYTHONPATH", "LEM_PLUGIN_ROOT", "AGTERM_SESSION_ID", "CLAUDE_PLUGIN_ROOT"):
    assert name not in os.environ, name

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
# The unit level runs on xdist's workers and the model level in one process: the protocol holds
# on both. A subtest's parameters cross from a worker as text.
LEVELS = ("unit", "model")


def probe_lines(level: str) -> list[str]:
    """The result line of each probe case, at `level`."""
    size = "'2'" if level == "unit" else "2"
    marked = "a case marked to fail is no check"
    return [
        f"FAIL {level}.test_probe.Cases.test_expected_failure: {marked}",
        f"FAIL {level}.test_probe.Cases.test_fail: AssertionError: call failed",
        f"ok   {level}.test_probe.Cases.test_pass",
        f"SKIP {level}.test_probe.Cases.test_skip: needs a device",
        (
            f"FAIL {level}.test_probe.Cases.test_subtests: "
            f"Cases.test_subtests (size={size}): AssertionError: child failed"
        ),
        f"FAIL {level}.test_probe.Cases.test_unexpected_success: {marked}",
        f"FAIL {level}.test_probe.test_setup_error: ValueError: bad setup",
        f"FAIL {level}.test_probe.test_teardown_error: ValueError: bad teardown",
        f"FAIL {level}.test_probe.test_marked_success: {marked}",
        f"FAIL {level}.test_probe.test_dynamic_xfail: {marked}",
        f"ok   {level}.test_probe.test_parameters[one]",
        f"ok   {level}.test_probe.test_parameters[two]",
    ]


def scratch(work: Path, level: str = "unit", **files: str) -> Path:
    """A checkout in `work` with a copy of the entry, the real .venv, and `files` in the
    folder of `level`; its folder of tests."""
    tests = work / "tests"
    (tests / level).mkdir(parents=True)
    for name in ENTRY_FILES:
        shutil.copy(TESTS / name, tests / name)
    shutil.copy(ROOT / "pyproject.toml", work / "pyproject.toml")
    (work / ".venv").symlink_to(ROOT / ".venv")
    for name, text in files.items():
        (tests / level / f"{name}.py").write_text(text)
    return tests


def run_entry(
    work: Path, *args: str, **caller: str
) -> subprocess.CompletedProcess[str]:
    """Run the scratch entry with the variables a caller's shell would hand it."""
    env = dict(os.environ)
    env.update(
        caller,
        LEM_SERVE="on",
        PYTHONPATH=str(work),
        LEM_PLUGIN_ROOT=str(work),
        AGTERM_SESSION_ID="a-session-of-the-owner",
        CLAUDE_PLUGIN_ROOT=str(work),
    )
    for name in ("HOME", "XDG_CONFIG_HOME", "TMPDIR"):
        folder = work / name
        folder.mkdir(exist_ok=True)
        env[name] = env["CALLER_" + name] = str(folder)
    return subprocess.run(
        [sys.executable, "-I", "-B", str(work / "tests"), *args],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def assert_results(
    ran: subprocess.CompletedProcess[str], code: int, *lines: str, ended: bool = True
) -> None:
    """The exit status, the collected line, the result lines in any order (xdist's workers
    finish in theirs), then only detail lines, and the total when pytest `ended`."""
    said = ran.stdout.splitlines()
    results = [
        line
        for line in said
        if line.startswith(("collected ", "ok ", "FAIL ", "SKIP "))
    ]
    got = (ran.returncode, results[:1], sorted(results[1:]))
    assert got == (code, list(lines[:1]), sorted(lines[1:])), ran.stdout + ran.stderr
    assert sorted(said[: len(lines)]) == sorted(lines)
    if ended:
        assert said[-1].startswith("total: "), said[-1]
        said.pop()
    for detail in said[len(lines) :]:
        assert not detail or detail.startswith("  "), detail


@pytest.mark.parametrize("level", LEVELS)
def test_each_case_has_one_line_and_the_exit_tells_whether_the_run_passed(
    tmp_path: Path, level: str
) -> None:
    scratch(tmp_path, level, test_probe=CASES)
    ran = run_entry(tmp_path, "--level", level, f"tests/{level}/test_probe.py")
    assert_results(ran, 1, "collected 12", *probe_lines(level))
    for detail in (
        "Captured stdout",
        "  ok   false result",
        "  collected 50",
        "  FAIL false result from a pass",
    ):
        assert detail in ran.stdout
    assert ran.stdout.splitlines()[-1] == (
        "total: collected 12, passed 3, skipped 1, failed 8"
    )


def test_individual_reports_choose_the_result() -> None:
    name = "unit.test_probe.Cases.test_one"
    for outcome, detail, expected in (
        ("passed", None, f"ok   {name}"),
        ("failed", "ValueError: bad call", f"FAIL {name}: ValueError: bad call"),
        ("skipped", ("test_probe.py", 1, "Skipped: off"), f"SKIP {name}: off"),
    ):
        with redirect_stdout(StringIO()) as output:
            lines = Lines(Path())
            report = pytest.TestReport(
                name, ("test_probe.py", 1, name), {}, outcome, detail, "call"
            )
            lines.say_result(name, name, [report])
        assert output.getvalue() == expected + "\n"
        assert lines.counts["FAIL"] == (outcome == "failed")


def test_collection_errors_prevent_cases_from_running(tmp_path: Path) -> None:
    tests = scratch(
        tmp_path,
        "model",
        test_import='raise ValueError("bad import")\n',
        test_generated=(
            "import unittest\n\n"
            "def load_tests(loader, tests, pattern):\n"
            '    def broken(): raise ValueError("generated case failed")\n'
            "    tests.addTest(unittest.FunctionTestCase(broken))\n"
            "    return tests\n"
        ),
        test_good="def test_pass():\n    pass\n",
    )
    shutil.copytree(tests / "model", tests / "unit")
    ran = run_entry(tmp_path, "--level", "model")
    assert_results(ran, 2, "collected 1")
    parallel = run_entry(tmp_path, "--level", "unit")
    assert parallel.returncode == 1
    assert parallel.stdout.count("collection failed: tests/unit/test_import.py") == 1
    for detail in (
        "collection failed: tests/model/test_import.py",
        "ValueError: bad import",
        "collection failed: tests/model/test_generated.py",
        "test_generated: convert load_tests to discoverable tests",
    ):
        assert detail in ran.stdout


def test_two_folders_may_each_hold_a_file_of_one_name(tmp_path: Path) -> None:
    tests = scratch(tmp_path)
    for folder in ("task", "landing"):
        (tests / "unit" / folder).mkdir()
        (tests / "unit" / folder / "test_store.py").write_text(
            "def test_pass():\n    pass\n"
        )
    assert_results(
        run_entry(tmp_path, "--level", "unit"),
        0,
        "collected 2",
        "ok   unit.landing.test_store.test_pass",
        "ok   unit.task.test_store.test_pass",
    )


def test_a_selection_that_collects_nothing_fails(tmp_path: Path) -> None:
    scratch(tmp_path, helper="VALUE = 1\n")
    ran = run_entry(tmp_path, "--level", "unit")
    assert_results(ran, 1, "collected 0")
    assert "the selection collected no cases" in ran.stdout


def test_cases_that_do_not_add_up_to_the_collected_fail_the_run() -> None:
    with redirect_stdout(StringIO()) as output:
        lines = Lines(Path())
        lines.names = {"a": "a", "b": "b"}
        lines.counts["ok"] = 1
        session = Mock(spec=pytest.Session, exitstatus=pytest.ExitCode.OK)
        lines.pytest_sessionfinish(session)
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert "1 passed and 0 skipped and 0 failed are not the 2 collected" in (
        output.getvalue()
    )


def test_module_cleanups_run_even_after_setup_or_teardown_fails(
    tmp_path: Path,
) -> None:
    files = {}
    for phase in ("setup", "teardown", "cleanup"):
        files[f"test_{phase}"] = (
            "import os\n"
            "import unittest\n"
            "from pathlib import Path\n\n"
            "def clean():\n"
            + (
                f'    assert (Path(os.environ["CALLER_HOME"]).parent / "{phase}_torn_down").exists()\n'
                if phase != "setup"
                else ""
            )
            + f'    (Path(os.environ["CALLER_HOME"]).parent / "{phase}").write_text("clean")\n'
            f'    raise ValueError("{phase} module cleanup failed")\n\n'
            "def setUpModule():\n"
            "    unittest.addModuleCleanup(clean)\n"
            + ('    raise ValueError("bad setup")\n' if phase == "setup" else "")
            + "\ndef tearDownModule():\n"
            f'    (Path(os.environ["CALLER_HOME"]).parent / "{phase}_torn_down").touch()\n'
            + ('    raise ValueError("bad teardown")\n' if phase == "teardown" else "")
            + "\nclass Sample(unittest.TestCase):\n"
            "    def test_pass(self): pass\n"
        )
    scratch(tmp_path, **files)
    ran = run_entry(tmp_path, "--level", "unit")
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert (
        "FAIL unit.test_cleanup.Sample.test_pass: ValueError: cleanup module cleanup failed"
        in ran.stdout
    )
    for phase in ("setup", "teardown", "cleanup"):
        assert (tmp_path / phase).read_text() == "clean"
        assert f"{phase} module cleanup failed" in ran.stdout
    assert not (tmp_path / "setup_torn_down").exists()
    assert (tmp_path / "teardown_torn_down").exists()


@pytest.mark.parametrize("level", LEVELS)
def test_a_hard_exit_cannot_pass_or_leave_its_temporary_folder(
    tmp_path: Path, level: str
) -> None:
    scratch(
        tmp_path,
        level,
        test_hard_exit=(
            "import os\n"
            "from pathlib import Path\n\n"
            "def test_exit():\n"
            '    (Path(os.environ["CALLER_HOME"]).parent / "temp_root").write_text(os.environ["TMPDIR"])\n'
            "    os._exit(0)\n"
        ),
    )
    ran = run_entry(tmp_path, "--level", level)
    if level == "unit":
        # Any of the four workers may take the case, so the line names the one that did.
        crashed = re.fullmatch(
            r"FAIL unit\.test_hard_exit\.test_exit: worker 'gw[0-3]' crashed while "
            r"running 'tests/unit/test_hard_exit\.py::test_exit'",
            ran.stdout.splitlines()[1],
        )
        assert crashed is not None, ran.stdout
        assert_results(ran, 1, "collected 1", crashed[0])
        assert ran.stdout.splitlines()[-1] == (
            "total: collected 1, passed 0, skipped 0, failed 1"
        )
    else:
        assert_results(ran, 1, "collected 1", ended=False)
        assert "the test process exited before pytest returned" in ran.stderr
    assert not Path((tmp_path / "temp_root").read_text()).parent.exists()


def test_the_entry_ignores_the_callers_pytest_variables(tmp_path: Path) -> None:
    scratch(
        tmp_path,
        test_environment=(
            "import os\n\n"
            "def test_pass():\n"
            '    assert "PYTEST_XDIST_AUTO_NUM_WORKERS" not in os.environ\n'
            "\ndef test_excluded():\n"
            '    raise AssertionError("the command selects only test_pass")\n'
        ),
    )
    assert_results(
        run_entry(
            tmp_path,
            "--level",
            "unit",
            "tests/unit/test_environment.py::test_pass",
            PYTEST_ADDOPTS="-p no_such_plugin_of_lem -k nothing_matches",
            PYTEST_PLUGINS="another_missing_plugin_of_lem",
            PYTEST_XDIST_AUTO_NUM_WORKERS="8",
        ),
        0,
        "collected 1",
        "ok   unit.test_environment.test_pass",
    )


def test_a_wrong_call_is_refused_before_pytest_starts(tmp_path: Path) -> None:
    scratch(tmp_path)
    for args, said in (
        (("--level", "everything"), "invalid choice"),
        (("--level", "gates", "tests/unit"), "takes no paths"),
        (("--level", "model"), "has no case yet"),
        ((), "the following arguments are required: --level"),
    ):
        ran = run_entry(tmp_path, *args)
        assert (ran.returncode, ran.stdout) == (2, ""), ran.stderr
        assert said in ran.stderr


def test_snapshots_create_writes_the_missing_values_through_the_entry(
    tmp_path: Path,
) -> None:
    tests = scratch(
        tmp_path,
        test_snap=(
            "from inline_snapshot import snapshot\n\n\n"
            "def test_value():\n    assert 1 + 1 == snapshot()\n"
        ),
    )
    missing = run_entry(tmp_path, "--level", "unit")
    assert_results(
        missing,
        1,
        "collected 1",
        "FAIL unit.test_snap.test_value: "
        "AssertionError: your snapshot is missing a value run pytest with "
        "--inline-snapshot=create",
    )
    created = run_entry(tmp_path, "--level", "unit", "--snapshots", "create")
    assert created.returncode == 1, created.stdout + created.stderr
    assert "snapshot(2)" in (tests / "unit" / "test_snap.py").read_text()
    assert_results(
        run_entry(tmp_path, "--level", "unit"),
        0,
        "collected 1",
        "ok   unit.test_snap.test_value",
    )


@pytest.mark.parametrize("level", LEVELS)
def test_a_test_case_imported_into_two_files_is_a_duplicate(
    tmp_path: Path, level: str
) -> None:
    tests = scratch(
        tmp_path,
        level,
        test_a="from fakes.shared_case import Shared\n",
        test_b="from fakes.shared_case import Shared\n",
    )
    (tests / "fakes").mkdir()
    (tests / "fakes" / "shared_case.py").write_text(
        "import unittest\n\nclass Shared(unittest.TestCase):\n    def test_pass(self): pass\n"
    )
    ran = run_entry(tmp_path, "--level", level)
    assert_results(
        ran,
        1,
        "collected 2",
        f"ok   {level}.test_a.Shared.test_pass",
        f"FAIL {level}.test_b.Shared.test_pass: Failed: duplicate case: "
        f"fakes.shared_case.Shared.test_pass is collected as "
        f"tests/{level}/test_a.py::Shared::test_pass too; import its module, not its class",
    )


def test_a_run_that_changes_the_checkouts_own_state_fails_and_names_what_changed(
    tmp_path: Path,
) -> None:
    tests = scratch(
        tmp_path,
        test_harm=(
            "import os\n"
            "from pathlib import Path\n\n"
            "def test_harm():\n"
            '    state = Path(os.environ["CALLER_HOME"]).parent / ".lem" / "state"\n'
            '    (state / "tasks" / "x").mkdir()\n'
            '    (state / "tasks" / "x" / "task.json").write_text("{}")\n'
        ),
    )
    run_git(tmp_path, "init", "--quiet")
    (tmp_path / ".lem" / "state" / "tasks" / "kept").mkdir(parents=True)
    assert tests.is_dir()
    ran = run_entry(tmp_path, "--level", "unit")
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert "ok   unit.test_harm.test_harm" in ran.stdout
    state = (tmp_path / ".lem" / "state").resolve()
    assert (
        f"FAIL the run changed the checkout's own Lem state {state}: added tasks/x, "
        "tasks/x/task.json; removed nothing"
    ) in ran.stderr
    (tmp_path / "tests" / "unit" / "test_harm.py").write_text(
        "def test_pass():\n    pass\n"
    )
    assert run_entry(tmp_path, "--level", "unit").returncode == 0
