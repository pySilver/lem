"""Give the unit level a temporary home and report its cases to tests/all.sh.

Pytest uses the temporary home when it loads this file, and a unit file run by its path uses the caller's environment.
"""

import os
import shlex
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from textwrap import indent

import pytest

HERE = Path(__file__).resolve().parent
SETUP_PLUGIN = "lem-unit-setup"
MARKED_TO_FAIL = "a case marked to fail is no check"


def isolate(config: pytest.Config, root: Path | None) -> None:
    stack = ExitStack()
    config.add_cleanup(stack.close)
    if root is None:
        root = Path(
            stack.enter_context(tempfile.TemporaryDirectory(prefix="lem-unit-"))
        )
    patch = stack.enter_context(pytest.MonkeyPatch.context())
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


class UnitSetup:
    """One plugin for both the unit entry and direct runs of pytest."""

    __name__ = SETUP_PLUGIN

    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def pytest_addoption(self, parser: pytest.Parser) -> None:
        parser.addoption(
            "--lem-lines", action="store_true", help="print Lem's suite results"
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_load_initial_conftests(
        self, early_config: pytest.Config, args: list[str]
    ) -> None:
        # Only the entry registers this plugin before initial conftest discovery.
        # Give an entry with no paths the unit directory, even outside the checkout.
        paths = early_config.known_args_namespace.file_or_dir
        if not paths:
            paths.append(str(HERE))
            args.append(str(HERE))

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config: pytest.Config) -> None:
        isolate(config, self.root)
        if config.getoption("lem_lines"):
            if config.getoption("capture") != "fd" or config.getoption("runxfail"):
                raise pytest.UsageError(
                    "--lem-lines requires fd capture and normal xfail handling"
                )
            config.pluginmanager.set_blocked("terminal")
            # Pytest can still call the terminal's configure hook in this hook pass.
            config.pluginmanager.set_blocked("terminalreporter")
            full = (
                len(config.args) == 1
                and Path(config.args[0]).resolve() == HERE
                and not config.getoption("keyword")
                and not config.getoption("markexpr")
            )
            config.pluginmanager.register(Lines(full=full))

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
                f"{name} controls pytest plugins. Run .venv/bin/python -I -B tests/unit."
            )
    if not pluginmanager.has_plugin(SETUP_PLUGIN):
        pluginmanager.register(UnitSetup())


def case_name(item: pytest.Item) -> str:
    if isinstance(item, pytest.Function) and isinstance(
        item.instance, unittest.TestCase
    ):
        return item.instance.id()
    case = ".".join((item.path.stem, *item.id.names))
    return case if item.id.params is None else f"{case}[{item.id.params}]"


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
    """Count collected cases and give each completed case one result."""

    def __init__(self, *, full: bool) -> None:
        self.full = full
        self.names: dict[str, str] = {}
        self.marked: set[str] = set()
        self.results: set[str] = set()
        self.reports: dict[str, list[pytest.TestReport]] = {}
        self.deselected = 0
        self.failed = False
        self.problems: list[str] = []
        self.diagnostics: list[str] = []

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected += len(items)

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if not report.passed:
            self.problems.append(f"collection {report.outcome}: {report.nodeid}")
            self.diagnostics.append(report.longreprtext)
        self.diagnostics.extend(
            f"{label}\n{content}" for label, content in report.sections
        )

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        print(f"collected {len(session.items)}", flush=True)
        names: set[str] = set()
        for item in session.items:
            name = case_name(item)
            if item.nodeid in self.names or name in names:
                problem = f"duplicate case: {name}"
                self.problems.append(problem)
                raise session.Interrupted(problem)
            self.names[item.nodeid] = name
            names.add(name)
            if marked_to_fail(item):
                self.marked.add(item.nodeid)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if (
            isinstance(report, pytest.SubtestReport)
            and report.passed
            and not report.sections
            and not hasattr(report, "wasxfail")
        ):
            return
        self.reports.setdefault(report.nodeid, []).append(report)

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
        if nodeid in self.marked or bad:
            self.failed = True
            why = MARKED_TO_FAIL if nodeid in self.marked else reason(bad[0])
            print(f"FAIL {name}: {why}", flush=True)
        elif skips:
            print(f"SKIP {name}: {reason(skips[0])}", flush=True)
        else:
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

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        if self.full and not self.names:
            self.problems.append("the unit level collected no cases")
        if self.full and self.deselected:
            self.problems.append(f"the unit level deselected {self.deselected} cases")
        for nodeid in sorted(self.names.keys() - self.results):
            self.problems.append(f"no result: {self.names[nodeid]}")

        for detail in [*self.problems, *self.diagnostics]:
            if detail:
                print(indent(detail, "  "), flush=True)
        if session.exitstatus in (
            pytest.ExitCode.OK,
            pytest.ExitCode.NO_TESTS_COLLECTED,
        ):
            session.exitstatus = (
                pytest.ExitCode.TESTS_FAILED
                if self.failed or self.problems
                else pytest.ExitCode.OK
            )
