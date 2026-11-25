"""The one entry of Lem's tests: `.venv/bin/python -I -B tests --level LEVEL [PATHS...]`.

pytest runs in a child process, with no `PYTEST_*` variable and no PYTHONPATH: the owner's
shell sets `PYTEST_ADDOPTS=-p agterm_hud -p peer_planning_pytest`, PYTHONPATH and
PYTEST_XDIST_AUTO_NUM_WORKERS, and a runner that obeys them stops at once. The child writes a
mark when pytest returns, so a case that calls `os._exit` fails the run instead of passing it.
The levels and what each runs are in levels.py.
"""

import argparse
import os
import signal
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VENV = ROOT / ".venv"


def run_pytest(root: Path, args: list[str]) -> int:
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(HERE))
    for name in tuple(os.environ):
        if name.startswith("PYTEST_") or name == "PYTHONPATH":
            del os.environ[name]
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    import pytest

    from conftest import Setup

    code = pytest.main(
        [
            "-c",
            str(ROOT / "pyproject.toml"),
            "--lem-lines",
            *args,
        ],
        plugins=[Setup(root)],
    )
    (root / "completed").touch()
    return code


def run_in_child(args: list[str]) -> int:
    child: subprocess.Popen[bytes] | None = None
    terminated = False

    def terminate(signum: int, _frame: object) -> None:
        nonlocal terminated
        terminated = True
        if child is not None:
            # Popen.wait may hold its lock when this handler runs.
            with suppress(ProcessLookupError):
                os.kill(child.pid, signum)

    # The child stays in the caller's process group, so Ctrl-C reaches pytest.
    old_int = signal.signal(signal.SIGINT, lambda *_: None)
    old_term = signal.signal(signal.SIGTERM, terminate)
    try:
        with tempfile.TemporaryDirectory(prefix="lem-test-") as directory:
            root = Path(directory)
            command = [
                sys.executable,
                "-I",
                "-B",
                "-c",
                (
                    "import runpy, sys; from pathlib import Path; "
                    "run = runpy.run_path(sys.argv[1])['run_pytest']; "
                    "sys.exit(run(Path(sys.argv[2]), sys.argv[3:]))"
                ),
                str(HERE / "__main__.py"),
                str(root),
                *args,
            ]
            with subprocess.Popen(command) as child:
                if terminated:
                    terminate(signal.SIGTERM, None)
                code = child.wait()
            child = None
            if code == 0 and not (root / "completed").is_file():
                print("the test process exited before pytest returned", file=sys.stderr)
                return 1
    finally:
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)
    return 128 - code if code < 0 else code


def main() -> int:
    sys.path.insert(0, str(HERE))
    import levels

    parser = argparse.ArgumentParser(
        prog=".venv/bin/python -I -B tests",
        description="Run one level of Lem's tests, or the files of a level named.",
    )
    parser.add_argument("--level", required=True, choices=levels.LEVELS)
    parser.add_argument(
        "--snapshots",
        choices=("create", "fix"),
        help="let inline-snapshot write the values snapshot() lacks (create) or "
        "gets wrong (fix) into the test files; then run ruff format",
    )
    parser.add_argument("paths", nargs="*", help="files or folders of the level")
    called = parser.parse_args()
    if Path(sys.prefix).resolve() != VENV.resolve():
        print(
            f"FAIL the tests run on {VENV / 'bin' / 'python'}, not on "
            f"{sys.executable}: run uv sync --locked at the root of the checkout, then "
            ".venv/bin/python -I -B tests --level LEVEL"
        )
        return 1
    try:
        chosen = levels.selection(HERE, called.level, called.paths)
    except levels.WrongCall as wrong:
        parser.error(str(wrong))
    snapshots = [f"--inline-snapshot={called.snapshots}"] if called.snapshots else []
    with levels.lock_of(called.level):
        workers = levels.parallel(called.level, snapshots=bool(snapshots))
        state = levels.real_state(HERE)
        before = levels.listing(state)
        code = run_in_child(
            ["--lem-level", called.level, *workers, *snapshots, *chosen]
        )
    harm = levels.changed(state, before)
    if harm is not None:
        print(harm, file=sys.stderr)
        return code or 1
    return code


if __name__ == "__main__":
    sys.exit(main())
