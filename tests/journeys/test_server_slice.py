"""The board server as a process of its own, in the test's own home folder of Lem, on a free
port that is never the owner's: `lem serve run` serves the kanban and its stream and stops clean;
`lem serve ensure` starts one server and keeps it, and another install replaces it only at a
higher release; `lem serve stop` ends it; the owner's two ports are refused before anything
runs; and with a server of the release before this one in the home folder, every command leaves
it and every file of the home folder as they are.

Each case holds the servers it starts: the foreground one by its `Popen`, a detached one by a
supervisor that knows each by its pid, its start time and its command line (its port is the
case's own), registered from the process table and never from what a command printed, and that
signals a process only while all three still match.
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import httpx
import pytest

from fakes.command import LEM, Ran, lem
from fakes.records import record
from lem.board import machine, stream, watched
from lem.kernel import folders, release
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

ROOT = Path(__file__).resolve().parents[2]
WAIT = 20.0
SINCE = "data-stream-since-value="


def listening(port: int) -> bool:
    """Whether something takes connections on the port."""
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


@dataclass(frozen=True)
class Identity:
    """A process as the process table names it: its pid, its start and its command line."""

    pid: int
    started: str
    command: str


def table() -> list[Identity]:
    """Every process of the machine, from `ps`."""
    ran = subprocess.run(
        ["ps", "-A", "-o", "pid=,lstart=,command="],
        capture_output=True,
        text=True,
        check=True,
    )
    found = []
    for line in ran.stdout.splitlines():
        words = line.split(maxsplit=6)
        if len(words) == 7:
            found.append(Identity(int(words[0]), " ".join(words[1:6]), words[6]))
    return found


@dataclass
class Supervisor:
    """The detached servers of a case: those whose command serves one of its ports."""

    ports: list[int] = field(default_factory=list)
    known: dict[int, Identity] = field(default_factory=dict)

    def serves(self, identity: Identity) -> bool:
        return any(
            identity.command.endswith(f"serve run --port {port}") for port in self.ports
        )

    def running(self) -> list[Identity]:
        """The case's servers that run now, each registered as it is seen."""
        now = [identity for identity in table() if self.serves(identity)]
        for identity in now:
            self.known.setdefault(identity.pid, identity)
        return now

    def end_all(self) -> None:
        """Stop each server of the case that still runs as the same process."""
        self.running()
        for identity in self.known.values():
            for sign in (signal.SIGTERM, signal.SIGKILL):
                if not self.same(identity):
                    break
                os.kill(identity.pid, sign)
                deadline = time.monotonic() + WAIT
                while self.same(identity) and time.monotonic() < deadline:
                    time.sleep(0.1)

    def ended_within(self, seconds: float) -> bool:
        """Whether every server of the case ended within `seconds`: a server frees its port
        a moment before its process ends."""
        deadline = time.monotonic() + seconds
        while self.running() and time.monotonic() < deadline:
            time.sleep(0.1)
        return not self.running()

    @staticmethod
    def same(identity: Identity) -> bool:
        return identity in table()


@pytest.fixture
def supervisor() -> Iterator[Supervisor]:
    held = Supervisor()
    yield held
    held.end_all()
    assert held.running() == []


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


def facts_of(port: int) -> dict[str, Any]:
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
    tmp_path: Path, env: dict[str, str], free_port: Callable[[], int]
) -> None:
    repo = workspace_at(tmp_path / "repo")
    state = places.state_of(repo)
    tasks.create(state, record("fix-the-login"))
    port = free_port()
    command = [LEM, "--repo", str(repo), "serve", "run", "--port", str(port)]
    with subprocess.Popen(
        command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as proc:
        try:
            facts = facts_of(port)
            assert (facts["pid"], facts["home"]) == (proc.pid, str(lem_home(env)))
            served = json.loads((lem_home(env) / "serve.json").read_text())
            assert served["pid"] == proc.pid
            base = f"http://127.0.0.1:{port}/{facts['host']}/repo/"
            page = httpx.get(base)
            assert page.status_code == 200
            assert 'id="card-fix-the-login"' in page.text
            shown = page.text.split(SINCE, 1)[1].split('"')[1]
            head = httpx.head(f"{base}stream", timeout=WAIT)
            assert head.headers["content-type"].startswith("text/event-stream")
            with httpx.stream(
                "GET", f"{base}stream?rendered={shown}", timeout=httpx.Timeout(WAIT)
            ) as reply:
                lines = reply.iter_lines()
                tasks.create(state, record("add-a-flag"))
                told = next_refresh(lines)
                assert told == watched.look(state, lem_home(env)).version != shown
                assert 'id="card-add-a-flag"' in httpx.get(base).text
                proc.send_signal(signal.SIGTERM)
                # the stream ends when the server stops: else the read times out
                list(lines)
            out, err = proc.communicate(timeout=WAIT)
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(WAIT)
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


def result(ran: Ran) -> dict[str, Any]:
    found = ran.result()
    assert isinstance(found, dict), ran
    return cast("dict[str, Any]", found)


def test_serve_ensure_keeps_one_server_and_another_install_replaces_it_only_when_higher(
    tmp_path: Path,
    env: dict[str, str],
    supervisor: Supervisor,
    free_port: Callable[[], int],
) -> None:
    repo = workspace_at(tmp_path / "repo")
    port = free_port()
    supervisor.ports.append(port)
    (folders.home_marked(lem_home(env)) / "machine.toml").write_text(
        f"[serve]\nport = {port}\n"
    )
    first = result(lem("serve", "ensure", cwd=repo, env=serving(env)))
    assert (first["running"], first["started"]) == (True, True)
    [one] = supervisor.running()
    assert one.pid == first["pid"]
    again = result(lem("serve", "ensure", cwd=repo, env=serving(env)))
    assert (again["started"], again["pid"]) == (False, first["pid"])
    off = result(lem("serve", "ensure", cwd=repo, env=env))
    assert (off["started"], off["pid"]) == (False, first["pid"])
    assert "LEM_SERVE=off" in off["said"]
    board = result(lem("board", "--no-open", cwd=repo, env=serving(env)))
    assert board["url"] == f"http://127.0.0.1:{port}/{first['host']}/repo/"
    assert httpx.get(board["url"]).status_code == 200
    assert supervisor.running() == [one]

    same = ensured_by(make_install(tmp_path / "same", release.running()), repo, env)
    assert (same["started"], same["pid"]) == (False, first["pid"])
    assert same["said"] == "another install of Lem serves"
    newer = ensured_by(make_install(tmp_path / "newer", "99.0.0"), repo, env)
    assert newer["started"] is True
    package = (tmp_path / "newer" / "src" / "lem").resolve()
    assert newer["install"]["package"] == str(package)
    [replacing] = supervisor.running()
    assert replacing.pid == newer["pid"] != one.pid

    left = result(lem("serve", "stop", cwd=repo, env=serving(env)))
    assert left["stopped"] is False
    assert "another install of Lem serves: release 99.0.0" in left["said"]
    stopped = subprocess.run(
        [sys.executable, "-B", "-P", "-s", "-m", "lem", "serve", "stop"],
        cwd=repo,
        env={**serving(env), "PYTHONPATH": str(package.parent)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    said = json.loads(stopped.stdout)["result"]
    assert said == {"stopped": True, "pid": newer["pid"], "version": "99.0.0"}
    assert not listening(port)
    assert supervisor.ended_within(WAIT)
    none = result(lem("serve", "stop", cwd=repo, env=serving(env)))
    assert none["stopped"] is False


def refusal_code(ran: Ran) -> object:
    refusal = ran.envelope()["refusal"]
    assert isinstance(refusal, dict)
    return refusal["code"]


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


class Before(ThreadingHTTPServer):
    """A board server of the release before this one, in this test's process, as `main`'s
    `serve.py` answers `GET /api/server`; it records each request it gets."""

    def __init__(self, home: Path, port: int) -> None:
        super().__init__(("127.0.0.1", port), Answering)
        self.facts = {
            "pid": 77,
            "version": f"version {release.running()}",
            "install": {
                "version": release.running(),
                "commit": None,
                "package": "/opt/homebrew/Cellar/lem/0.3.1/libexec/lib/lem",
                "stamp": None,
            },
            "root": "/opt/homebrew/Cellar/lem/0.3.1/libexec/lib/lem/data",
            "config": str(home),
            "started": "2026-11-24T00:31:16Z",
            "port": port,
            "url": f"http://127.0.0.1:{port}/",
            "host": "this-mac",
            "aliases": [],
            "tailscale": None,
            "tailscale_port": None,
            "push": {"devices": 0},
        }
        self.seen: list[str] = []


class Answering(BaseHTTPRequestHandler):
    server_version = "lem-serve"

    @property
    def before(self) -> Before:
        return cast("Before", self.server)

    def do_GET(self) -> None:
        self.before.seen.append(f"GET {self.path}")
        body = json.dumps(self.before.facts).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        self.before.seen.append(f"POST {self.path}")
        self.send_response(202)
        self.send_header("Content-Length", "0")
        self.end_headers()


def files_of(*folders: Path) -> dict[str, bytes]:
    """Every file under the folders, by its path, with its bytes."""
    return {
        str(path): path.read_bytes()
        for folder in folders
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def test_a_server_of_the_release_before_keeps_its_port_and_every_file_of_its_home(
    tmp_path: Path,
    env: dict[str, str],
    supervisor: Supervisor,
    free_port: Callable[[], int],
) -> None:
    home = lem_home(env)
    repo = workspace_at(tmp_path / "repo")
    port, other = free_port(), free_port()
    supervisor.ports.extend((port, other))
    (home / "machine.toml").write_text(f"[serve]\nport = {port}\n")
    (home / "workspaces.json").write_text('[\n  "/Users/someone/project"\n]\n')
    (home / "serve.pid").write_text(f"77 {port}\n")
    (home / "serve.lock").write_text("")
    (home / "serve.log").write_text("a line of the server of the release before\n")
    kept = files_of(home, repo)
    calls = (
        (("serve", "ensure"), serving(env), None),
        (("serve", "ensure"), env, None),
        (("serve", "stop"), serving(env), None),
        (("serve", "stop"), env, None),
        (("serve", "run"), env, "other-install"),
        (("serve", "run", "--port", str(other)), env, "other-install"),
        (("board", "--no-open"), serving(env), "other-install"),
    )
    before = Before(home, port)
    thread = threading.Thread(target=before.serve_forever, daemon=True)
    thread.start()
    try:
        for words, environ, refused in calls:
            ran = lem(*words, cwd=repo, env=environ)
            if refused is None:
                said = result(ran)
                assert "release " + release.running() in said["said"], words
                assert said.get("started", False) is False
                assert said.get("stopped", False) is False
            else:
                assert (ran.code, refusal_code(ran)) == (1, refused), words
            assert files_of(home, repo) == kept, words
            assert not listening(other)
        asked = len(before.seen)
        ran = lem("board", "--no-open", cwd=repo, env=env)
        assert (ran.code, refusal_code(ran)) == (1, "no-server")
        assert len(before.seen) == asked
        assert files_of(home, repo) == kept
    finally:
        before.shutdown()
        before.server_close()
        thread.join()
    assert [seen for seen in before.seen if seen.startswith("POST")] == []
    assert supervisor.running() == []


def test_a_home_of_lem_0_3_with_nothing_serving_is_refused_and_kept_as_it_is(
    tmp_path: Path,
    env: dict[str, str],
    supervisor: Supervisor,
    free_port: Callable[[], int],
) -> None:
    home = lem_home(env)
    repo = workspace_at(tmp_path / "repo")
    port = free_port()
    other = free_port()
    supervisor.ports.extend((port, other))
    (home / "machine.toml").write_text(f"[serve]\nport = {port}\n")
    (home / "owner.jsonl").write_text('{"away": false, "at": "2026-11-24T00:00:00Z"}\n')
    (home / "serve.lock").write_text("")
    (home / "workspaces.json").write_text('[\n  "/Users/someone/project"\n]\n')
    kept = files_of(home, repo)
    for words in (
        ("serve", "run"),
        ("serve", "run", "--port", str(other)),
        ("serve", "ensure"),
        ("board", "--no-open"),
    ):
        ran = lem(*words, cwd=repo, env=serving(env))
        assert (ran.code, refusal_code(ran)) == (1, "old-state"), words
        assert files_of(home, repo) == kept, words
    stop = result(lem("serve", "stop", cwd=repo, env=serving(env)))
    assert stop == {"stopped": False, "said": f"no board server runs on port {port}"}
    assert files_of(home, repo) == kept
    assert not listening(port)
    assert not listening(other)
    assert supervisor.running() == []
