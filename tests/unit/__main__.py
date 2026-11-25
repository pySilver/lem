"""Run the unit level with the line protocol of tests/all.sh.

Use `.venv/bin/python -I -B tests/unit [SELECTOR]` for isolated runs, because a unit file run by its path uses the caller's environment.
"""

import os
import signal
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VENV = ROOT / ".venv"


def run_pytest(root: Path, args: list[str]) -> int:
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(HERE))
    for name in tuple(os.environ):
        if name.startswith("PYTEST_"):
            del os.environ[name]
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    import pytest

    from conftest import UnitSetup

    code = pytest.main(
        [
            "-c",
            str(ROOT / "pyproject.toml"),
            "-p",
            "no:terminal",
            "--lem-lines",
            *args,
        ],
        plugins=[UnitSetup(root)],
    )
    (root / "completed").touch()
    return code


def run_in_child() -> int:
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
        with tempfile.TemporaryDirectory(prefix="lem-unit-") as directory:
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
                *sys.argv[1:],
            ]
            with subprocess.Popen(command) as child:
                if terminated:
                    terminate(signal.SIGTERM, None)
                code = child.wait()
            child = None
            if code == 0 and not (root / "completed").is_file():
                print("the unit process exited before pytest returned", file=sys.stderr)
                return 1
    finally:
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)
    return 128 - code if code < 0 else code


def main() -> int:
    if Path(sys.prefix).resolve() != VENV.resolve():
        print(
            f"FAIL the unit level runs on {VENV / 'bin' / 'python'}, not on "
            f"{sys.executable}: run uv sync at the root of the checkout, then "
            ".venv/bin/python -I -B tests/unit"
        )
        return 1

    return run_in_child()


if __name__ == "__main__":
    sys.exit(main())
