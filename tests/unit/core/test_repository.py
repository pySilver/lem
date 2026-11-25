"""The repository's own rules that core holds: the package's version is the plugin's, one
hatchling builds and checks it, CI starts by hand only, and no command leaves bytecode in the
checkout."""

import importlib.metadata
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from lem.kernel import release

ROOT = Path(__file__).resolve().parents[3]
BIN = Path(sys.executable).parent


def test_the_package_and_the_running_release_are_the_plugins_version() -> None:
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())[
        "version"
    ]
    assert importlib.metadata.version("lem") == plugin
    assert release.running() == plugin


def test_the_build_backend_and_the_dev_tools_name_one_hatchling() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    backend = [
        r for r in project["build-system"]["requires"] if r.startswith("hatchling")
    ]
    tools = [
        r for r in project["dependency-groups"]["dev"] if r.startswith("hatchling")
    ]
    assert backend == tools
    assert len(backend) == 1
    assert "==" in backend[0]


def test_ci_starts_by_hand_only() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    block = re.search(r"^on:\n((?:[ \t]+.*\n|\n)*)", workflow, re.MULTILINE)
    assert block is not None
    assert [line.strip() for line in block[1].splitlines() if line.strip()] == [
        "workflow_dispatch:"
    ]


def test_no_command_leaves_bytecode_in_the_checkout(tmp_path: Path) -> None:
    for command in (["lem", "help"], ["lem-hook"]):
        subprocess.run(
            [BIN / command[0], *command[1:]],
            cwd=tmp_path,
            capture_output=True,
            check=False,
            timeout=60,
        )
    subprocess.run(
        [sys.executable, "-c", "import lem.store.tasks, lem.app.wiring"],
        check=True,
        timeout=60,
    )
    left = sorted(
        str(found.relative_to(ROOT))
        for folder in ("src", "tests")
        for found in (ROOT / folder).rglob("__pycache__")
    )
    assert left == []
