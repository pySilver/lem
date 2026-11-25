"""The board server as a process of its own, in the test's own home folder of Lem, on a free
port that is never the owner's: `lem serve run` serves the kanban and its stream and stops clean;
`lem serve ensure` starts one server and keeps it, and another install replaces it only at a
higher release; `lem serve stop` ends it; the owner's two ports are refused before anything runs.

Every server a case starts is stopped by that case, and its pid is checked gone at the end.
"""

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import pytest

from fakes.command import LEM, Ran, lem
from fakes.records import record
from lem.board import machine, stream
from lem.kernel import release
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOT = Path(__file__).resolve().parents[2]
WAIT = 20.0
SINCE = re.compile(r'data-stream-since-value="([0-9a-f]+)"')


def free_port() -> int:
    """A port nothing listens on now, which is never one of the owner's."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    assert port not in {machine.PORT, machine.DOOR_PORT}
    return port


def listening(port: int) -> bool:
    """Whether something takes connections on the port."""
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def ended(pid: int) -> None:
    """Stop the server `pid` that a case started, when it still runs, and wait for its end."""
    assert pid != 3311, "the owner's server is never a test's"
    if not alive(pid):
        return
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + WAIT
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    if alive(pid):
        os.kill(pid, signal.SIGKILL)


@pytest.fixture
def servers() -> Iterator[list[int]]:
    """The pids of the servers a case started, each stopped at its end."""
    pids: list[int] = []
    yield pids
    for pid in pids:
        ended(pid)
    assert not [pid for pid in pids if alive(pid)]


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    """The case's environment: the entry's own HOME, a home folder of Lem of the case's own,
    and LEM_SERVE=off."""
    config = tmp_path / "config"
    (config / "lem").mkdir(parents=True)
    return {**os.environ, "XDG_CONFIG_HOME": str(config), "LEM_SERVE": "off"}


def lem_home(env: dict[str, str]) -> Path:
    return Path(env["XDG_CONFIG_HOME"]) / "lem"


def serving(env: dict[str, str]) -> dict[str, str]:
    """The environment of the one call that starts a server on purpose."""
    return {name: word for name, word in env.items() if name != "LEM_SERVE"}


def workspace_at(folder: Path) -> Path:
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem").mkdir()
    return folder


def facts_of(port: int) -> dict[str, object]:
    """What the server on the port says of itself, once it answers."""
    deadline = time.monotonic() + WAIT
    while True:
        try:
            return httpx.get(f"http://127.0.0.1:{port}/api/server").json()
        except httpx.TransportError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.1)


def next_refresh(lines: Iterator[str]) -> str:
    """The id of the stream's next refresh, past its pings."""
    fields: dict[str, str] = {}
    for line in lines:
        if line:
            name, _, word = line.partition(": ")
            fields[name] = word
            continue
        if fields.get("data") == stream.REFRESH:
            return fields["id"]
        fields = {}
    raise AssertionError("the stream ended with no refresh")


def test_serve_run_serves_the_kanban_and_its_stream_and_stops_clean(
    tmp_path: Path, env: dict[str, str], servers: list[int]
) -> None:
    repo = workspace_at(tmp_path / "repo")
    state = places.state_of(repo)
    tasks.create(state, record("fix-the-login"))
    port = free_port()
    command = [LEM, "--repo", str(repo), "serve", "run", "--port", str(port)]
    proc = subprocess.Popen(
        command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    servers.append(proc.pid)
    facts = facts_of(port)
    assert (facts["pid"], facts["home"]) == (proc.pid, str(lem_home(env)))
    served = json.loads((lem_home(env) / "serve.json").read_text())
    assert served["pid"] == proc.pid
    base = f"http://127.0.0.1:{port}/{facts['host']}/repo/"
    page = httpx.get(base)
    assert page.status_code == 200
    assert 'id="card-fix-the-login"' in page.text
    shown = SINCE.search(page.text)
    assert shown is not None
    timeout = httpx.Timeout(WAIT)
    with httpx.stream(
        "GET", f"{base}stream?rendered={shown[1]}", timeout=timeout
    ) as reply:
        assert reply.headers["content-type"].startswith("text/event-stream")
        lines = reply.iter_lines()
        tasks.create(state, record("add-a-flag"))
        told = next_refresh(lines)
        assert told == stream.version(state) != shown[1]
        assert 'id="card-add-a-flag"' in httpx.get(base).text
        proc.send_signal(signal.SIGTERM)
        # the stream ends when the server stops: else the read times out
        list(lines)
    out, err = proc.communicate(timeout=WAIT)
    assert proc.returncode == 0, err
    assert json.loads(out)["result"]["pid"] == proc.pid
    assert not (lem_home(env) / "serve.json").exists()
    assert not listening(port)


def make_install(folder: Path, version: str) -> Path:
    """Another install of Lem beside the checkout's: a copy of its package, its skill's
    folder, and a manifest of `version`; its `src` goes on PYTHONPATH."""
    shutil.copytree(
        ROOT / "src" / "lem",
        folder / "src" / "lem",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    skill = folder / "skills" / "lem"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("a copy of Lem for a test\n")
    (skill / "assets").symlink_to(ROOT / "skills" / "lem" / "assets")
    (folder / ".claude-plugin").mkdir()
    (folder / ".claude-plugin" / "plugin.json").write_text(
        f'{{"version": "{version}"}}'
    )
    return folder / "src"


def ensured_by(source: Path, repo: Path, env: dict[str, str]) -> dict[str, Any]:
    """`lem serve ensure` of the install whose package is in `source`."""
    ran = subprocess.run(
        [sys.executable, "-B", "-P", "-s", "-m", "lem", "serve", "ensure"],
        cwd=repo,
        env={**serving(env), "PYTHONPATH": str(source)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert ran.returncode == 0, ran.stdout + ran.stderr
    return json.loads(ran.stdout)["result"]


def test_serve_ensure_keeps_one_server_and_another_install_replaces_it_only_when_higher(
    tmp_path: Path, env: dict[str, str], servers: list[int]
) -> None:
    repo = workspace_at(tmp_path / "repo")
    port = free_port()
    (lem_home(env) / "machine.toml").write_text(f"[serve]\nport = {port}\n")
    first = lem("serve", "ensure", cwd=repo, env=serving(env)).result()
    assert isinstance(first, dict)
    servers.append(first["pid"])
    assert (first["running"], first["started"]) == (True, True)
    again = lem("serve", "ensure", cwd=repo, env=serving(env)).result()
    assert isinstance(again, dict)
    assert (again["started"], again["pid"]) == (False, first["pid"])
    off = lem("serve", "ensure", cwd=repo, env=env).result()
    assert isinstance(off, dict)
    assert (off["started"], off["pid"]) == (False, first["pid"])
    assert "LEM_SERVE=off" in off["said"]
    board = lem("board", "--no-open", cwd=repo, env=serving(env)).result()
    assert isinstance(board, dict)
    assert board["url"] == f"http://127.0.0.1:{port}/{first['host']}/repo/"
    assert httpx.get(board["url"]).status_code == 200

    same = ensured_by(make_install(tmp_path / "same", release.running()), repo, env)
    assert (same["started"], same["pid"]) == (False, first["pid"])
    assert same["said"] == "another install of Lem serves"
    newer = ensured_by(make_install(tmp_path / "newer", "99.0.0"), repo, env)
    servers.append(newer["pid"])
    assert newer["started"] is True
    assert newer["pid"] != first["pid"]
    assert newer["install"]["package"] == str(
        (tmp_path / "newer" / "src" / "lem").resolve()
    )
    assert not alive(first["pid"])

    stopped = lem("serve", "stop", cwd=repo, env=serving(env)).result()
    assert stopped == {"stopped": True, "pid": newer["pid"], "version": "99.0.0"}
    assert not listening(port)
    none = lem("serve", "stop", cwd=repo, env=serving(env)).result()
    assert isinstance(none, dict)
    assert none["stopped"] is False


@pytest.mark.parametrize("port", [machine.PORT, machine.DOOR_PORT])
def test_the_owners_ports_are_refused_before_anything_runs(
    tmp_path: Path, env: dict[str, str], port: int
) -> None:
    ran = lem("serve", "run", "--port", str(port), cwd=tmp_path, env=env)
    assert (ran.code, refusal_code(ran)) == (1, "owner-port")
    (lem_home(env) / "machine.toml").write_text(f"[serve]\nport = {port}\n")
    for words in (("serve", "ensure"), ("serve", "stop")):
        refused = lem(*words, cwd=tmp_path, env=serving(env))
        assert (refused.code, refusal_code(refused)) == (1, "owner-port")


def refusal_code(ran: Ran) -> object:
    refusal = ran.envelope()["refusal"]
    assert isinstance(refusal, dict)
    return refusal["code"]
