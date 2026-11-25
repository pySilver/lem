"""A hook never fails a session: on bad input, for a selector of no handler, from a handler that
raises, and from an app whose own files are not whole, it exits 0 with nothing on stdout or
stderr, and a hook that wrote nothing leaves no file."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING

from hooks.claude_code import (
    BAD_INPUTS,
    GUI_PATH,
    HOOK,
    ROOT,
    SELECTORS,
    SLUG,
    files_of,
    hooked,
    started,
    workspace,
)
from lem.kernel import folders
from lem.store import sessions

if TYPE_CHECKING:
    from pathlib import Path

ENTRY = "from lem.hooks import main; main.main()"


def test_with_bad_stdin_every_selector_says_nothing_and_exits_0(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    for selector in SELECTORS:
        for stdin in BAD_INPUTS:
            ran = hooked(selector, stdin, CLAUDE_PROJECT_DIR=str(tmp_path / "repo"))
            assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), (
                selector,
                stdin,
            )
    assert sessions.read(folder) == ()


def entry(selector: str, stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    """Run `lem-hook SELECTOR` itself, with no wrapper to mask what it says."""
    return subprocess.run(
        [str(HOOK), selector],
        input=stdin,
        env={**os.environ, "PATH": GUI_PATH, "LEM_TASK": SLUG},
        cwd=tempfile.gettempdir(),
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_the_entry_itself_says_nothing_and_exits_0_on_any_input(tmp_path: Path) -> None:
    workspace(tmp_path / "repo")
    nul = json.dumps({"cwd": "/tmp/a\u0000b", "hook_event_name": "PreCompact"})
    inputs = (*BAD_INPUTS, nul.encode(), started(tmp_path / "repo\u0000x"))
    for selector in (*SELECTORS, "no-such-selector", "", "--help", "lem.hooks.session"):
        for stdin in inputs:
            ran = entry(selector, stdin)
            assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), (
                selector,
                stdin,
            )


def run_with(
    code: str, selector: str, stdin: bytes, **environ: str
) -> subprocess.CompletedProcess[bytes]:
    """Run `code`, then the hook's entry with `selector`, under this checkout's Python."""
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", f"{code}; {ENTRY}", selector],
        input=stdin,
        env={**os.environ, "PATH": GUI_PATH, **environ},
        cwd=tempfile.gettempdir(),
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_a_handlers_words_are_printed_only_when_it_ended_well() -> None:
    def handler(words: str) -> str:
        return (
            "import sys, types; module = types.ModuleType('lem.hooks.stop'); "
            f"module.answer = lambda environ, behind: {words}; "
            "sys.modules['lem.hooks.stop'] = module"
        )

    assert run_with(handler("'said'"), "stop", b"").stdout == b"said"
    for failing in ("1 / 0", "[][1]", "None.x", "int('x')", "open('/nowhere/x')"):
        ran = run_with(handler(failing), "stop", b"")
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), failing


def test_an_app_whose_files_are_not_whole_says_nothing_and_writes_nothing(
    tmp_path: Path,
) -> None:
    # a copy of the hooks beside no plugin files: the app cannot tell its version
    copy = tmp_path / "copy"
    shutil.copytree(
        ROOT / "src" / "lem" / "hooks",
        copy / "lem" / "hooks",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (copy / "lem" / "__init__.py").write_text("")
    (copy / "bin").mkdir()
    lem = copy / "bin" / "lem"
    lem.write_text(f"#!/bin/sh\ntouch '{tmp_path / 'ran'}'\n")
    lem.chmod(0o755)
    home = tmp_path / "config" / "lem"
    home.mkdir(parents=True)
    (home / folders.MARKER).write_bytes(folders.FORM)
    (home / "machine.toml").write_text("[corrections]\ncollect = true\n")
    workspace(tmp_path / "repo")
    before = files_of(tmp_path)
    code = (
        f"import sys; sys.path.insert(0, {str(copy)!r}); "
        f"sys.executable = {str(copy / 'bin' / 'python')!r}"
    )
    event = json.loads(started(tmp_path / "repo", "compact"))
    stdin = json.dumps({**event, "prompt": "never push without asking"}).encode()
    for selector in SELECTORS:
        ran = run_with(
            code,
            selector,
            stdin,
            LEM_TASK=SLUG,
            LEM_SERVE="",
            XDG_CONFIG_HOME=str(tmp_path / "config"),
            CLAUDE_ENV_FILE=str(tmp_path / "env"),
        )
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), selector
    assert files_of(tmp_path) == before
    assert not (tmp_path / "env").exists()
