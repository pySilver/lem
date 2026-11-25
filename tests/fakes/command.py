"""A command of Lem as every test runs it: the checkout's own `lem`, its exit code, and its
standard output read whole.

A dispatched command prints one JSON document, the envelope (`lem.kernel.envelope`). A test
reads it untyped: msgspec decodes no `Raw` that is one side of `Raw | None`, so `Envelope` cannot
be decoded with a result (`tests/unit/core/test_envelope.py`). The command runs with the test's
own environment, which the entry made: its own HOME, XDG_CONFIG_HOME and TMPDIR, and
LEM_SERVE=off.
"""

import subprocess
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

# The `lem` of the .venv this test runs on: the checkout's, installed editable.
LEM = f"{sys.prefix}/bin/lem"


@dataclass(frozen=True, kw_only=True)
class Ran:
    """A finished command: its arguments, exit code, standard output and errors."""

    args: tuple[str, ...]
    code: int
    stdout: str
    stderr: str

    def envelope(self) -> dict[str, object]:
        """The printed envelope, as JSON reads it; a test fails when the output is no one
        JSON object."""
        try:
            document = msgspec.json.decode(self.stdout)
        except msgspec.DecodeError:
            document = None
        if not isinstance(document, dict):
            raise AssertionError(
                f"lem {' '.join(self.args)} printed no JSON object (exit {self.code}):\n"
                f"{self.stdout}{self.stderr}"
            )
        return document

    def result(self) -> object:
        """The envelope's `result`; a test fails when it has none."""
        found = self.envelope()
        if "result" not in found:
            raise AssertionError(f"lem {' '.join(self.args)} gave no result: {found}")
        return found["result"]


def lem(
    *args: str,
    cwd: Path,
    stdin: str | None = None,
    env: Mapping[str, str] | None = None,
) -> Ran:
    """Run `lem ARGS` in `cwd`, with `stdin` as its input, and give what it did."""
    ran = subprocess.run(
        [LEM, *args],
        cwd=cwd,
        input=stdin,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return Ran(args=args, code=ran.returncode, stdout=ran.stdout, stderr=ran.stderr)
