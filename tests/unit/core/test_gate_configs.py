"""The gates' settings hold what the design asks: the model's rules import no os, subprocess,
socket or time, and the rest of the package may."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUFF = Path(sys.executable).parent / "ruff"


def findings(path: str, source: str) -> str:
    """What ruff says of `source` as if it were the file `path` of the checkout."""
    ran = subprocess.run(
        [RUFF, "check", "--output-format", "concise", "--stdin-filename", path, "-"],
        input=f'"""A probe."""\n\n{source}\n\nprint({source.rsplit(maxsplit=1)[-1]})\n',
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return ran.stdout


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "from os import path",
        "import subprocess",
        "import socket",
        "import time",
    ],
)
def test_the_models_rules_import_no_effect(source: str) -> None:
    assert "TID251" in findings("src/lem/model/task/probe.py", source)
    assert "TID251" not in findings("src/lem/store/probe.py", source)
