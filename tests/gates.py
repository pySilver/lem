"""The gates, a case for each tool: `--level gates` runs this file, and `--level full` too.

Each tool runs from the checkout's .venv at the version of uv.lock, over what pyproject.toml and
.flake8 name, and says nothing when the code holds. A gate whose inputs do not exist is a skip.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = Path(sys.executable).parent


def holds(*command: str | Path) -> None:
    """Run one tool at the root of the checkout; fail with what it said when it exits non-zero."""
    ran = subprocess.run(
        [str(part) for part in command],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if ran.returncode:
        pytest.fail(
            f"{ran.stdout}{ran.stderr}\n{Path(command[0]).name} exited {ran.returncode}",
            pytrace=False,
        )


def test_uv_lock_holds_what_pyproject_asks() -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("no uv on PATH: install uv (https://docs.astral.sh/uv/)")
    holds(uv, "lock", "--check", "--offline")


def test_ruff_format_gives_every_python_file_the_one_format() -> None:
    holds(BIN / "ruff", "format", "--check", "--quiet")


def test_ruff_check_finds_no_rule_broken() -> None:
    holds(BIN / "ruff", "check", "--quiet", "--output-format", "concise")


def test_pyrefly_finds_the_types_hold() -> None:
    holds(BIN / "pyrefly", "check", "--output-format", "min-text")


def test_wemake_holds_src_lem_to_its_limits() -> None:
    holds(BIN / "flake8", "src/lem")


def test_import_linter_holds_the_layers() -> None:
    holds(BIN / "lint-imports", "--no-cache")


def test_eslint_holds_the_javascript_to_its_style(pytestconfig: pytest.Config) -> None:
    if not (ROOT / "eslint.config.mjs").is_file():
        pytest.skip("no eslint.config.mjs: no JavaScript to hold")
    eslint = ROOT / "node_modules" / ".bin" / "eslint"
    if not eslint.is_file():
        # The orchestrator's decision: a full run holds the JavaScript; any other level skips
        # it by name, since the worktree of a step that owns no JavaScript has no node_modules.
        missing = f"no {eslint}: run npm ci at the root of the checkout"
        if pytestconfig.getoption("lem_level") == "full":
            pytest.fail(missing)
        pytest.skip(
            f"{missing}; a worktree of a step that owns no JavaScript has no node_modules, "
            "and a full run fails here"
        )
    holds(eslint, ".")
