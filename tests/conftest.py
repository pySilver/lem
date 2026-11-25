"""Give every test run a home of its own, and report its cases one line each.

The entry (`tests/__main__.py`) registers `Setup` before pytest reads its arguments; a direct run of
pytest, and each worker of pytest-xdist, gets it from `pytest_addoption` below, with a temporary
folder of its own. The lines are the controller's: with xdist it reads the cases each worker
collected and the reports each worker sends, and a worker prints nothing.
"""

import os
import shlex
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING

import pytest

from levels import LEVELS

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

HERE = Path(__file__).resolve().parent
SETUP_PLUGIN = "lem-test-setup"
MARKED_TO_FAIL = "a case marked to fail is no check"
# The user property of a report whose case is marked to fail.
MARKED = "lem-marked-to-fail"
# xdist's report of a case whose worker died under it, which has no phase of its own.
CRASHED = "???"
# What a test must never inherit from the shell that started it: the owner's own Lem plugin
# (a version check against it stops every `lem`), and his terminal's session, which a test that
# reaches the real agtermctl would change.
CLEARED_PREFIXES = ("LEM_", "AGTERM_")
CLEARED_NAMES = ("PYTHONPATH", "CLAUDE_PLUGIN_ROOT", "CLAUDE_ENV_FILE")


def isolate(config: pytest.Config, root: Path | None) -> None:
    """Point HOME, XDG_CONFIG_HOME and TMPDIR into `root`, turn the board server off, and clear
    what the caller's shell would leak into a test."""
    stack = ExitStack()
    config.add_cleanup(stack.close)
    if root is None:
        root = Path(
            stack.enter_context(tempfile.TemporaryDirectory(prefix="lem-test-"))
        )
    patch = stack.enter_context(pytest.MonkeyPatch.context())
    for name in tuple(os.environ):
        if name.startswith(CLEARED_PREFIXES) or name in CLEARED_NAMES:
            patch.delenv(name)
    for variable, folder in (
        ("HOME", root / "home"),
        ("XDG_CONFIG_HOME", root / "config"),
        ("TMPDIR", root / "tmp"),
    ):
        folder.mkdir()
        patch.setenv(variable, str(folder))
    # tempfile may have cached the host's temp root before pytest loaded us.
    patch.setattr(tempfile, "tempdir", str(root / "tmp"))
    patch.setattr(sys, "dont_write_bytecode", True)
    patch.setenv("LEM_SERVE", "off")


class Setup:
    """One plugin for both the entry and direct runs of pytest."""

    __name__ = SETUP_PLUGIN

    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def pytest_addoption(self, parser: pytest.Parser) -> None:
        parser.addoption(
            "--lem-lines", action="store_true", help="print a line for each case"
        )
        parser.addoption(
            "--lem-level", choices=LEVELS, help="the level the entry runs (levels.py)"
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config: pytest.Config) -> None:
        isolate(config, self.root)
        if config.getoption("lem_lines") and not hasattr(config, "workerinput"):
            if config.getoption("capture") != "fd" or config.getoption("runxfail"):
                raise pytest.UsageError(
                    "--lem-lines requires fd capture and normal xfail handling"
                )
            # The terminal plugin stays, for the options other plugins read (inline-snapshot
            # reads --color); its reporter, which would print over the lines, is blocked.
            config.pluginmanager.set_blocked("terminalreporter")
            config.pluginmanager.register(Lines(config.rootpath))

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_makereport(
        self, item: pytest.Item, call: pytest.CallInfo[None]
    ) -> Generator[None, pytest.TestReport, pytest.TestReport]:
        # Marked where the item is, so the mark travels with the report to xdist's controller.
        report = yield
        if marked_to_fail(item):
            report.user_properties.append((MARKED, True))
        return report

    @pytest.fixture(scope="module", autouse=True)
    @staticmethod
    def unittest_module_cleanups(request: pytest.FixtureRequest) -> None:
        # Register before the module's xUnit fixture, so that this runs last even
        # when setUpModule fails and the xUnit fixture never reaches its yield.
        request.addfinalizer(unittest.doModuleCleanups)

    @pytest.hookimpl(tryfirst=True)
    def pytest_pycollect_makeitem(
        self, collector: pytest.Collector, name: str, obj: object
    ) -> None:
        if (
            isinstance(collector, pytest.Module)
            and name == "load_tests"
            and callable(obj)
        ):
            raise collector.CollectError(
                f"{collector.obj.__name__}: convert load_tests to discoverable tests"
            )


def pytest_addoption(pluginmanager: pytest.PytestPluginManager) -> None:
    # Pytest has processed plugin requests by the time it registers this conftest.
    addopts = shlex.split(os.environ.get("PYTEST_ADDOPTS", ""))
    for name, requests_plugin in (
        ("PYTEST_ADDOPTS", any(arg.startswith("-p") for arg in addopts)),
        ("PYTEST_PLUGINS", bool(os.environ.get("PYTEST_PLUGINS"))),
    ):
        if requests_plugin:
            raise pytest.UsageError(
                f"{name} controls pytest plugins. Run .venv/bin/python -I -B tests "
                "--level LEVEL."
            )
    if not pluginmanager.has_plugin(SETUP_PLUGIN):
        pluginmanager.register(Setup())


def dotted(path: Path) -> str:
    """A test file's name for its cases: its path from the tests' folder (or from the folder
    the run started in), with dots, so two folders may each hold a test_store.py."""
    for base in (HERE, Path.cwd()):
        if path.is_relative_to(base):
            return ".".join(path.relative_to(base).with_suffix("").parts)
    return path.stem


def case_name(rootdir: Path, nodeid: str) -> str:
    """`unit.core.test_store.Races.test_stale_expect`, and `[params]` for a parametrized one."""
    where, *names = nodeid.split("::")
    return ".".join((dotted(rootdir / where), *names))


def marked_to_fail(item: pytest.Item) -> bool:
    if item.get_closest_marker("xfail") is not None:
        return True
    return isinstance(item, pytest.Function) and any(
        getattr(obj, "__unittest_expecting_failure__", False)
        for obj in (item.obj, item.cls)
    )


def reason(report: pytest.TestReport) -> str:
    if hasattr(report, "wasxfail"):
        detail = MARKED_TO_FAIL
    elif report.skipped and isinstance(report.longrepr, tuple):
        detail = report.longrepr[2].removeprefix("Skipped: ")
    else:
        crash = getattr(report.longrepr, "reprcrash", None)
        detail = crash.message if crash else report.longreprtext
        lines = detail.strip().splitlines()
        if lines:
            detail = lines[0] if isinstance(report, pytest.SubtestReport) else lines[-1]
        else:
            detail = report.outcome
    if isinstance(report, pytest.SubtestReport):
        detail = f"{report.head_line}: {detail}"
    return r"\n".join(detail.splitlines())


class Lines:
    """Count the collected cases, give each one result line, and add them up at the end."""

    def __init__(self, rootdir: Path) -> None:
        self.rootdir = rootdir
        self.names: dict[str, str] = {}
        self.collections: list[tuple[str, ...]] = []
        self.results: set[str] = set()
        self.reports: dict[str, list[pytest.TestReport]] = {}
        self.counts = {"ok": 0, "SKIP": 0, "FAIL": 0}
        self.deselected = 0
        self.problems: list[str] = []
        self.diagnostics: list[str] = []

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected += len(items)

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        problem = f"collection {report.outcome}: {report.nodeid}"
        if not report.passed and problem not in self.problems:
            # xdist sends each worker's report of one module's failure
            self.problems.append(problem)
            self.diagnostics.append(report.longreprtext)
        self.diagnostics.extend(
            f"{label}\n{content}" for label, content in report.sections
        )

    def collected(self, nodeids: Sequence[str]) -> None:
        """Take the collected cases, once; with xdist, each worker's must be the same."""
        if self.collections:
            if tuple(nodeids) not in self.collections:
                self.problems.append("the workers collected different cases")
            return
        self.collections.append(tuple(nodeids))
        print(f"collected {len(nodeids)}", flush=True)
        names: set[str] = set()
        for nodeid in nodeids:
            name = case_name(self.rootdir, nodeid)
            if name in names:
                self.problems.append(f"duplicate case: {name}")
            self.names[nodeid] = name
            names.add(name)

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.collected([item.nodeid for item in session.items])

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(
        self, node: object, ids: Sequence[str]
    ) -> None:
        self.collected(ids)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if (
            isinstance(report, pytest.SubtestReport)
            and report.passed
            and not report.sections
            and not hasattr(report, "wasxfail")
        ):
            return
        if report.when == CRASHED:
            self.crashed(report)
            return
        self.reports.setdefault(report.nodeid, []).append(report)

    def crashed(self, report: pytest.TestReport) -> None:
        """The worker running a case died: the case fails, with xdist's words."""
        name = self.names.get(report.nodeid, report.nodeid)
        self.reports.pop(report.nodeid, None)
        self.results.add(report.nodeid)
        self.counts["FAIL"] += 1
        print(f"FAIL {name}: {reason(report)}", flush=True)

    def pytest_runtest_logfinish(self, nodeid: str) -> None:
        name = self.names.get(nodeid)
        reports = self.reports.pop(nodeid, [])
        if name is None or nodeid in self.results:
            self.problems.append(f"unexpected or repeated result: {nodeid}")
            return

        phases = [
            report for report in reports if not isinstance(report, pytest.SubtestReport)
        ]
        expected = (
            ["setup", "call", "teardown"]
            if phases and phases[0].passed
            else ["setup", "teardown"]
        )
        if [report.when for report in phases] != expected:
            self.problems.append(f"incomplete or repeated reports: {name}")
            return

        self.results.add(nodeid)
        self.say_result(nodeid, name, reports)

    def say_result(
        self, nodeid: str, name: str, reports: list[pytest.TestReport]
    ) -> None:
        bad = [
            report for report in reports if report.failed or hasattr(report, "wasxfail")
        ]
        skips = [report for report in reports if report.skipped]
        marked = any((MARKED, True) in report.user_properties for report in reports)
        if marked or bad:
            self.counts["FAIL"] += 1
            why = MARKED_TO_FAIL if marked else reason(bad[0])
            print(f"FAIL {name}: {why}", flush=True)
        elif skips:
            self.counts["SKIP"] += 1
            print(f"SKIP {name}: {reason(skips[0])}", flush=True)
        else:
            self.counts["ok"] += 1
            print(f"ok   {name}", flush=True)

        sections = dict.fromkeys(
            section for report in reports for section in report.sections
        )
        if not (bad or sections):
            return

        self.diagnostics.append(f"== {name}")
        for report in bad:
            title = (
                report.head_line
                if isinstance(report, pytest.SubtestReport)
                else report.when
            )
            if report.longreprtext:
                self.diagnostics.append(f"{title}\n{report.longreprtext}")
        self.diagnostics.extend(f"{label}\n{content}" for label, content in sections)

    def add_up(self) -> str:
        """The run's last line; a problem too when passed and skipped miss the collected."""
        collected = len(self.names)
        passed, skipped, failed = (self.counts[key] for key in ("ok", "SKIP", "FAIL"))
        if not collected:
            self.problems.append("the selection collected no cases")
        if passed + skipped + failed != collected:
            self.problems.append(
                f"{passed} passed and {skipped} skipped and {failed} failed "
                f"are not the {collected} collected"
            )
        return (
            f"total: collected {collected}, passed {passed}, skipped {skipped}, "
            f"failed {failed}"
        )

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        if self.deselected:
            self.problems.append(f"the run deselected {self.deselected} cases")
        for nodeid in sorted(self.names.keys() - self.results):
            self.problems.append(f"no result: {self.names[nodeid]}")
        total = self.add_up()

        for detail in [*self.problems, *self.diagnostics]:
            if detail:
                print(indent(detail, "  "), flush=True)
        print(total, flush=True)
        if session.exitstatus in (
            pytest.ExitCode.OK,
            pytest.ExitCode.NO_TESTS_COLLECTED,
        ):
            session.exitstatus = (
                pytest.ExitCode.TESTS_FAILED
                if self.counts["FAIL"] or self.problems
                else pytest.ExitCode.OK
            )
