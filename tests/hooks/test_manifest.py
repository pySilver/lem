"""The plugin's two hook files: `hooks/hooks.json` registers each selector on its event, and
`hooks/run` finds the app, passes its output on only when it exited 0, and says nothing with no
app."""

import subprocess
from typing import TYPE_CHECKING

from hooks.claude_code import (
    LINES,
    SELECTORS,
    claude_environ,
    hooked,
    manifest,
    started,
    workspace,
)
from lem.store import sessions

if TYPE_CHECKING:
    from pathlib import Path

LINE = '/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" {} 2>/dev/null || :'


def test_the_manifest_registers_each_selector_on_its_event_matcher_and_flags() -> None:
    registered = sorted(
        (
            event,
            group.get("matcher"),
            hook["command"],
            hook.get("timeout"),
            hook.get("async", False),
        )
        for event, groups in manifest().items()
        for group in groups
        for hook in group["hooks"]
    )
    assert registered == sorted(
        [
            ("PreCompact", "auto|manual", LINE.format("precompact"), 5, False),
            ("SessionStart", "startup|resume", LINE.format("serve"), 5, False),
            (
                "SessionStart",
                "startup|resume|clear|compact|fork",
                LINE.format("session-start"),
                5,
                False,
            ),
            ("Stop", None, LINE.format("stop"), None, True),
            ("UserPromptSubmit", None, LINE.format("corrections"), 10, False),
        ]
    )


def test_with_no_app_every_selector_says_nothing_and_exits_0(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    for selector in SELECTORS:
        ran = hooked(
            selector,
            started(tmp_path / "repo"),
            LEM_HOOK_BIN=str(tmp_path / "missing" / "lem-hook"),
            CLAUDE_ENV_FILE=str(tmp_path / "env"),
        )
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), selector
    assert not (folder / sessions.SESSIONS).exists()
    assert not (tmp_path / "env").exists()


def app(folder: Path, body: str) -> Path:
    """A stand-in `lem-hook` in `folder` that runs the shell lines `body`."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "lem-hook"
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(0o755)
    return path


def test_the_output_is_passed_on_only_when_the_app_exited_0(tmp_path: Path) -> None:
    said = app(tmp_path / "said", 'echo "context of $1"')
    failed = app(tmp_path / "failed", "echo half; echo noise >&2; exit 3")
    ran = hooked("session-start", b"{}", LEM_HOOK_BIN=str(said))
    assert (ran.returncode, ran.stdout, ran.stderr) == (
        0,
        b"context of session-start\n",
        b"",
    )
    ran = hooked("session-start", b"{}", LEM_HOOK_BIN=str(failed))
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")


def test_a_relative_lem_hook_bin_is_never_run(tmp_path: Path) -> None:
    mark = tmp_path / "ran"
    app(tmp_path / "bin", f"touch '{mark}'; echo ran")
    for named in ("bin/lem-hook", "./bin/lem-hook"):
        ran = subprocess.run(
            ["/bin/sh", "-c", LINES["stop"]],
            input=b"{}",
            env=claude_environ({"LEM_HOOK_BIN": named}),
            cwd=tmp_path,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), named
    assert not mark.exists()
