"""The `serve` hook: when a Claude Code session starts or resumes in a repository that uses Lem, a
fresh clone with no state too, it starts `lem --repo CHECKOUT serve ensure` of its own app for the
session's main checkout, detached, its output in the server's log, and the session does not wait
for it; with
`LEM_SERVE=off`, outside a repository of Lem, or in a state folder of Lem 0.3 it starts nothing.

Every start here runs the stand-in `lem` of `claude_code.stand_in`, never Lem's own: the test
entry's `LEM_SERVE=off` is lifted only for a hook whose `lem` is the stand-in.
"""

import json
import time
from typing import TYPE_CHECKING

from hooks.claude_code import (
    calls_of,
    hooked,
    old_workspace,
    recorded,
    stand_in,
    workspace,
)

if TYPE_CHECKING:
    from pathlib import Path

# A start the hook waited for would take at least this long, in seconds: the stand-in `lem`
# sleeps that much before it writes its call.
SLOW = 3.0


def test_a_session_in_a_repository_of_lem_starts_the_server_detached(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app", delay=SLOW)
    workspace(tmp_path / "repo")
    began = time.monotonic()
    ran = hooked(
        "serve",
        json.dumps({"cwd": str(tmp_path / "repo"), "source": "startup"}).encode(),
        LEM_HOOK_BIN=str(hook),
        LEM_SERVE="",
    )
    took = time.monotonic() - began
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert took < SLOW
    due = f"--repo {(tmp_path / 'repo').resolve()} serve ensure"
    assert calls_of(calls, 1) == [due]


def test_no_server_starts_when_it_is_off_or_the_repository_is_no_lem_of_this_form(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app")
    workspace(tmp_path / "repo")
    plain = tmp_path / "plain"
    (plain / ".git").mkdir(parents=True)
    old = old_workspace(tmp_path / "old")
    cases = (
        (tmp_path / "repo", "off"),
        (plain, ""),
        (old, ""),
        (tmp_path / "nowhere", ""),
    )
    for folder, serve in cases:
        event = json.dumps({"cwd": str(folder), "source": "resume"}).encode()
        ran = hooked("serve", event, LEM_HOOK_BIN=str(hook), LEM_SERVE=serve)
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), folder
    # the one start that is due comes last: a start of a case above would be in the calls too
    event = json.dumps({"cwd": str(tmp_path / "repo"), "source": "resume"}).encode()
    hooked("serve", event, LEM_HOOK_BIN=str(hook), LEM_SERVE="")
    due = [f"--repo {(tmp_path / 'repo').resolve()} serve ensure"]
    assert calls_of(calls, 1) == due
    time.sleep(0.5)
    assert recorded(calls) == due


def test_the_childs_refusal_lands_in_the_servers_log_and_a_fresh_clone_starts_it(
    tmp_path: Path,
) -> None:
    said = '{"ok":false,"refusal":{"code":"workspaces-write"}}'
    hook, calls = stand_in(tmp_path / "app", printed=said)
    clone = tmp_path / "clone"
    (clone / ".git").mkdir(parents=True)
    (clone / ".lem").mkdir()
    (clone / ".lem" / "settings.toml").write_text("")
    config = tmp_path / "config"
    event = json.dumps({"cwd": str(clone), "source": "startup"}).encode()
    ran = hooked(
        "serve",
        event,
        LEM_HOOK_BIN=str(hook),
        LEM_SERVE="",
        XDG_CONFIG_HOME=str(config),
    )
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert calls_of(calls, 1) == [f"--repo {clone.resolve()} serve ensure"]
    log = config / "lem" / "serve.log"
    deadline = time.monotonic() + 10
    while said not in (log.read_text() if log.is_file() else ""):
        assert time.monotonic() < deadline, "the refusal never reached serve.log"
        time.sleep(0.05)
    assert (config / "lem" / "lem-state.json").is_file()
