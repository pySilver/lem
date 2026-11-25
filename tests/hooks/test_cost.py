"""What a hook costs a session's start: each selector imports only its allowed list of modules, and
takes at most 55 ms at p95 from the installed manifest line (the design's part 5, part 11 item 5),
measured on a quiet machine only."""

import json
import math
import os
import subprocess
import sys
import tempfile
import time
from typing import TYPE_CHECKING

import pytest

from hooks.claude_code import (
    GUI_PATH,
    ROOT,
    SELECTORS,
    SLUG,
    hooked,
    started,
    workspace,
)

if TYPE_CHECKING:
    from pathlib import Path

# The budget of one selector at p95, in milliseconds, and the runs it is read over.
BUDGET = 55.0
RUNS = 30
# The one-minute load average above which a time is no measure of the hook (the orchestrator's
# decision of 2026-11-25: several builders ran on this Mac, and the same code gave 44 ms at a
# load of 8 and 57 ms at a load of 10). The packaging trial's check P4 measures every selector
# on a quiet machine before the cutover, and is the binding number.
QUIET = 4.0


def imported(code: str, stdin: bytes, **environ: str) -> set[str]:
    """The modules that `python -c CODE` imports, from `-X importtime`. The hook is called
    through `main.run`, not its entry, whose `os._exit` would cut off the last lines."""
    ran = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", code],
        input=stdin,
        env={**os.environ, "PATH": GUI_PATH, **environ},
        cwd=tempfile.gettempdir(),
        capture_output=True,
        timeout=30,
        check=False,
    )
    lines = ran.stderr.decode().splitlines()
    rows = (
        line.rsplit("|", 1)[-1] for line in lines if line.startswith("import time:")
    )
    return {row.strip() for row in rows} - {"package"}


# What `json` brings with it on Python 3.14, which every hook that reads an event pays.
JSON = frozenset(
    (
        "json",
        "_json",
        "re",
        "_sre",
        "enum",
        "functools",
        "_functools",
        "collections",
        "_collections",
        "operator",
        "_operator",
        "keyword",
        "reprlib",
        "types",
        "_types",
        "copyreg",
        "itertools",
    )
)
# What each selector may import beyond Python's own start, by its top-level name: an import a
# later change adds (`pathlib`, `subprocess` on the common path, a library) fails here, on any
# machine and at any load, before it shows in the time of a hook.
ALLOWED = {
    "stop": frozenset(("importlib", "io", "select")),
    "session-start": frozenset(("importlib", "io", "select")) | JSON,
    "precompact": frozenset(("importlib", "io", "select")) | JSON,
    "serve": frozenset(("importlib", "io", "select")) | JSON,
    "corrections": frozenset(
        ("importlib", "io", "select", "tomllib", "datetime", "_datetime", "__future__")
    )
    | JSON,
}


@pytest.mark.parametrize("selector", SELECTORS)
def test_a_selector_imports_only_its_allowed_list(
    selector: str, tmp_path: Path
) -> None:
    workspace(tmp_path / "repo")
    event = json.loads(started(tmp_path / "repo"))
    stdin = json.dumps({**event, "prompt": "fix the login"}).encode()
    start = imported("pass", b"")
    call = f"import os; from lem.hooks import main; main.run({selector!r}, os.environ)"
    hook = imported(call, stdin, LEM_TASK=SLUG, CLAUDE_PLUGIN_ROOT=str(ROOT))
    added = hook - start
    outside = {name.split(".")[0] for name in added} - ALLOWED[selector] - {"lem"}
    lem = {name for name in added if name.split(".")[0] == "lem"}
    assert outside == set()
    assert lem <= {"lem", "lem.hooks"} | {
        name for name in lem if name.startswith("lem.hooks.")
    }
    assert "lem.hooks.main" in lem


def p95(selector: str, stdin: bytes) -> float:
    """The 95th percentile, in milliseconds, of `RUNS` runs of the manifest's line."""
    taken = []
    for _ in range(RUNS):
        began = time.perf_counter()
        hooked(selector, stdin)
        taken.append((time.perf_counter() - began) * 1000)
    taken.sort()
    return taken[math.ceil(0.95 * RUNS) - 1]


@pytest.mark.parametrize("selector", SELECTORS)
def test_a_selector_takes_at_most_55_ms_at_p95(selector: str, tmp_path: Path) -> None:
    load = os.getloadavg()[0]
    if load > QUIET:
        pytest.skip(f"load average {load:.1f} over {QUIET}: not measured")
    workspace(tmp_path / "repo")
    took = p95(selector, started(tmp_path / "repo"))
    assert took <= BUDGET, f"{selector}: p95 {took:.1f} ms over {RUNS} runs"


def test_a_session_that_is_no_tasks_reads_no_event_and_imports_no_json(
    tmp_path: Path,
) -> None:
    workspace(tmp_path / "repo")
    call = (
        "import os; from lem.hooks import main; main.run('session-start', os.environ)"
    )
    added = imported(
        call, started(tmp_path / "repo"), CLAUDE_PLUGIN_ROOT=str(ROOT)
    ) - imported("pass", b"")
    assert "json" not in added
    with_task = imported(
        call, started(tmp_path / "repo"), LEM_TASK=SLUG, CLAUDE_PLUGIN_ROOT=str(ROOT)
    )
    assert "json" in with_task
