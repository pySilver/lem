"""The board server as processes of their own, in the case's own home folder of Lem, on free
ports that are never the owner's, with a stand-in for the `tailscale` CLI and the board's
notifications recorded, never sent: the door opens and closes with its entry, a moved port and
a door that changes replace the server, a command's look starts one, `lem board` gives a task's
address and marks example tasks, the list of workspaces changes by hand, and a device's push is
recorded.

Each case holds the servers it starts: the foreground one by its `Popen`, a detached one by the
supervisor of `test_server_slice.py`, which signals a process only while its pid, start time and
command line still match.
"""

import json
import signal
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import httpx
import pytest

from fakes.command import LEM, lem
from fakes.records import record
from journeys.test_server_slice import (
    WAIT,
    Supervisor,
    facts_of,
    free_port,
    lem_home,
    listening,
    refusal_code,
    serving,
    workspace_at,
)
from lem.kernel import folders
from lem.store import places, tasks
from unit.board.service import tailscale_stand_in as stand_in

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fakes.command import Ran

APPLE = "https://web.push.apple.com/QGuQyavXutnMH"
FCM = "https://fcm.googleapis.com/fcm/send/abc"


@pytest.fixture
def supervisor() -> Iterator[Supervisor]:
    held = Supervisor()
    yield held
    held.end_all()
    assert held.running() == []


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    """The case's environment: a home folder of Lem of its own, LEM_SERVE=off, and the
    stand-in for the tailscale CLI."""
    config = tmp_path / "config"
    (config / "lem").mkdir(parents=True)
    cli = stand_in.made(tmp_path / "ts")
    return {
        **stand_in.environ(cli),
        "XDG_CONFIG_HOME": str(config),
        "LEM_SERVE": "off",
        "LEM_PUSH": "record",
    }


def machine(
    env: dict[str, str], port: int, door: int | None = None, *, opened: bool = True
) -> None:
    """The machine's `[serve]`: the port, and the door's port, open or closed."""
    lines = f"[serve]\nport = {port}\n"
    if door is not None:
        lines += f"tailscale = {str(opened).lower()}\ntailscale_port = {door}\n"
    home = folders.home_marked(lem_home(env))
    (home / "machine.toml").write_text(lines)


def result(ran: Ran) -> dict[str, Any]:
    found = ran.result()
    assert isinstance(found, dict), ran
    return cast("dict[str, Any]", found)


def test_the_door_lets_the_owner_in_publishes_its_entry_and_closes_with_it(
    tmp_path: Path, env: dict[str, str]
) -> None:
    repo = workspace_at(tmp_path / "repo")
    port, door = free_port(), free_port()
    machine(env, port, door)
    command = [LEM, "--repo", str(repo), "serve", "run"]
    with subprocess.Popen(
        command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as proc:
        try:
            facts = facts_of(port)
            assert facts["door"] == door
            assert facts["tailnet"] == f"https://{stand_in.NAME}:{door}/"
            assert facts["host"] == stand_in.NAME.split(".")[0]
            own = {
                "Host": f"{stand_in.NAME}:{door}",
                "Tailscale-User-Login": stand_in.LOGIN,
            }
            through = httpx.get(f"http://127.0.0.1:{door}/api/workspaces", headers=own)
            assert through.status_code == 200
            stranger = {**own, "Tailscale-User-Login": "peer@example.com"}
            assert (
                httpx.get(
                    f"http://127.0.0.1:{door}/api/workspaces", headers=stranger
                ).status_code
                == 403
            )
            stop = httpx.post(f"http://127.0.0.1:{door}/api/server/stop", headers=own)
            assert stop.status_code == 405
            calls = stand_in.calls(Path(env["LEM_TAILSCALE"]))
            assert f"serve --bg --https={door} http://127.0.0.1:{door}" in calls
            proc.send_signal(signal.SIGTERM)
            proc.communicate(timeout=WAIT)
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(WAIT)
    assert proc.returncode == 0
    assert not listening(door)
    closed = result(lem("serve", "door", "off", cwd=repo, env=env))
    assert closed["door"] == "off"
    assert closed["removed"] is True
    assert "tailscale = false" in (lem_home(env) / "machine.toml").read_text()
    assert f"serve --https={door} off" in stand_in.calls(Path(env["LEM_TAILSCALE"]))


def test_a_moved_port_and_an_opened_door_replace_the_server_and_one_serves_the_machine(
    tmp_path: Path, env: dict[str, str], supervisor: Supervisor
) -> None:
    repo = workspace_at(tmp_path / "repo")
    first, second, door = free_port(), free_port(), free_port()
    supervisor.ports.extend((first, second))
    machine(env, first)
    started = result(lem("serve", "ensure", cwd=repo, env=serving(env)))
    assert started["started"] is True
    machine(env, second, door, opened=False)
    moved = result(lem("serve", "ensure", cwd=repo, env=serving(env)))
    assert moved["started"] is True
    assert moved["pid"] != started["pid"]
    assert not listening(first)
    [one] = supervisor.running()
    assert one.pid == moved["pid"]
    opened = result(lem("serve", "door", "on", cwd=repo, env=serving(env)))
    assert opened["door"] == "on"
    assert opened["server"]["started"] is True
    assert opened["server"]["pid"] != moved["pid"]
    assert facts_of(second)["door"] is not None
    stopped = result(lem("serve", "stop", cwd=repo, env=serving(env)))
    assert stopped["stopped"] is True
    assert supervisor.ended_within(WAIT)


def test_an_invalid_unrelated_setting_refuses_the_door_change_before_any_stop(
    tmp_path: Path, env: dict[str, str], supervisor: Supervisor
) -> None:
    repo = workspace_at(tmp_path / "repo")
    port, door = free_port(), free_port()
    supervisor.ports.append(port)
    machine(env, port, door)
    started = result(lem("serve", "ensure", cwd=repo, env=serving(env)))
    settings = lem_home(env) / "machine.toml"
    invalid = settings.read_text() + '\n[load]\nstart = "fast"\n'
    settings.write_text(invalid)
    cli = Path(env["LEM_TAILSCALE"])
    before = stand_in.calls(cli)

    refused = lem("serve", "door", "off", cwd=repo, env=serving(env))

    assert refused.code == 1
    assert "load.start" in refused.stdout
    assert settings.read_text() == invalid
    assert stand_in.calls(cli) == before
    kept = facts_of(port)
    assert (kept["pid"], kept["door"]) == (started["pid"], door)


def test_a_command_starts_the_server_detached_when_none_lives_and_off_starts_none(
    tmp_path: Path, env: dict[str, str], supervisor: Supervisor
) -> None:
    repo = workspace_at(tmp_path / "repo")
    port = free_port()
    supervisor.ports.append(port)
    machine(env, port)
    lem("task", "list", cwd=repo, env=env)
    time.sleep(0.5)
    assert supervisor.running() == []
    lem("task", "list", cwd=repo, env=serving(env))
    facts = facts_of(port)
    assert facts["home"] == str(lem_home(env))
    served = json.loads((lem_home(env) / "serve.json").read_text())
    assert served["pid"] == facts["pid"]
    lem("task", "list", cwd=repo, env=serving(env))
    assert len(supervisor.running()) == 1


def test_lem_board_gives_a_tasks_address_and_marks_example_tasks_for_good(
    tmp_path: Path, env: dict[str, str], supervisor: Supervisor
) -> None:
    repo = workspace_at(tmp_path / "repo")
    state = places.state_of(repo)
    tasks.create(state, record("fix-the-login"))
    port = free_port()
    supervisor.ports.append(port)
    machine(env, port)
    board = result(
        lem("board", "--no-open", "--task", "fix-the-login", cwd=repo, env=serving(env))
    )
    host = facts_of(port)["host"]
    assert board["url"] == f"http://127.0.0.1:{port}/{host}/repo/tasks/fix-the-login"
    assert board["name"] == "Lem board · repo"
    missing = lem(
        "board", "--no-open", "--task", "no-such-task", cwd=repo, env=serving(env)
    )
    assert missing.code == 1
    assert "fix-the-login" in json.dumps(missing.envelope())
    unopened = lem("board", cwd=repo, env=serving(env))
    assert refusal_code(unopened) == "no-session"
    demo = workspace_at(tmp_path / "demo")
    shown = lem("board", "--no-open", "--demo", cwd=demo, env=serving(env))
    assert (places.state_of(demo) / "demo").is_file()
    assert shown.code == 1
    assert refusal_code(shown) == "not-listed"
    again = lem("board", "--no-open", cwd=demo, env=serving(env))
    assert (places.state_of(demo) / "demo").is_file()
    assert again.code == 1


def test_the_list_of_workspaces_changes_by_hand_and_lists_its_counts(
    tmp_path: Path, env: dict[str, str]
) -> None:
    repo = workspace_at(tmp_path / "repo")
    tasks.create(places.state_of(repo), record("fix-the-login", status="building"))
    added = result(lem("serve", "add", str(repo), cwd=tmp_path, env=env))
    assert added["workspaces"] == [str(repo.resolve())]
    [row] = cast(
        "list[dict[str, Any]]", lem("serve", "list", cwd=tmp_path, env=env).result()
    )
    assert (row["name"], row["building"]) == ("repo", 1)
    gone = result(lem("serve", "remove", str(repo), cwd=tmp_path, env=env))
    assert gone["workspaces"] == []
    refused = lem("serve", "remove", str(repo), cwd=tmp_path, env=env)
    assert refusal_code(refused) == "not-listed"


def test_all_devices_turned_on_through_the_server_get_a_recorded_push(
    tmp_path: Path, env: dict[str, str]
) -> None:
    repo = workspace_at(tmp_path / "repo")
    port = free_port()
    machine(env, port)
    command = [LEM, "--repo", str(repo), "serve", "run"]
    with subprocess.Popen(
        command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as proc:
        try:
            facts_of(port)
            base = f"http://127.0.0.1:{port}"
            page = {"Origin": base, "Sec-Fetch-Site": "same-origin"}
            for endpoint in (APPLE, FCM):
                body = {"endpoint": endpoint, "keys": {"p256dh": "k", "auth": "a"}}
                on = httpx.post(f"{base}/api/push/subscribe", json=body, headers=page)
                assert on.json()["on"] is True
            far = httpx.post(
                f"{base}/api/push/subscribe",
                json=body,
                headers={"Origin": "https://evil.example"},
            )
            assert far.status_code == 403
            devices = httpx.get(f"{base}/api/server").json()["push"]["devices"]
            assert len(devices) == 2
            assert all(device["device"] for device in devices)
            proc.send_signal(signal.SIGTERM)
            proc.communicate(timeout=WAIT)
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(WAIT)
    tested = result(lem("serve", "push-test", cwd=repo, env=env))
    assert tested["devices"] == 2
    assert [reply["status"] for reply in tested["results"]] == [201, 201]
    lines = (lem_home(env) / "push-record.jsonl").read_text().splitlines()
    assert sorted(json.loads(line)["endpoint"] for line in lines) == sorted(
        (APPLE, FCM)
    )
