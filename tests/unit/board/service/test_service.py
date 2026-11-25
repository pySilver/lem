"""The rules of the board service that read no network: the machine's names, the tailscale CLI a
home may run, the door's entry in `tailscale serve`, the replace rule with the door, the look
before a command, the board's cookie, the list of workspaces by hand, `lem board`'s words, the
session a server leaves, and the stream's poll."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING
from urllib.parse import quote

import anyio
import msgspec
import pytest

from fakes.records import record
from fakes.terminal import FakeTerminal
from lem.board import (
    companion,
    editing,
    install,
    look,
    machine,
    opening,
    prefs,
    publish,
    stream,
    tailnet,
    tailscale,
    workspaces,
)
from lem.board import counts as counts_module
from lem.cli.board.command import Call, checked
from lem.kernel.errors import Refusal
from lem.ports.terminal import Pane
from lem.store import places, tasks
from unit.board.service import tailscale_stand_in as stand_in
from unit.board.service.given import workspace_at

if TYPE_CHECKING:
    from lem.board.facts import Install
from lem.board.counts import Counts


def test_the_tailnet_name_is_the_address_and_the_short_host_name_its_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(machine.socket, "gethostname", lambda: "Studio.local")
    assert machine.names_of("mac-mini.tail1.ts.net") == ("mac-mini", ("studio",))
    assert machine.names_of("studio.tail1.ts.net") == ("studio", ())


def test_with_no_tailnet_the_short_host_name_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(machine.socket, "gethostname", lambda: "My Mac.local")
    assert machine.names_of(None) == ("my-mac", ())
    assert workspaces.word("Lem Scratch!") == "lem-scratch"


def test_a_home_that_is_not_the_owners_runs_no_tailscale_cli_but_the_one_named(
    tmp_path: Path,
) -> None:
    assert not machine.owners_home(os.environ)
    assert tailscale.cli(os.environ) is None
    with pytest.raises(Refusal) as refused:
        tailscale.needed(os.environ)
    assert refused.value.code == "no-tailscale"
    cli = stand_in.made(tmp_path / "ts")
    assert tailscale.cli(stand_in.environ(cli)) == str(cli)
    assert tailnet.name_of(os.environ) is None


def test_the_door_reads_the_macs_name_and_the_owners_login_and_refuses_what_it_lacks(
    tmp_path: Path,
) -> None:
    cli = stand_in.made(tmp_path / "ts")
    assert tailnet.facts(tailnet.status(str(cli))) == (stand_in.NAME, stand_in.LOGIN)
    assert tailnet.name_of(stand_in.environ(cli)) == stand_in.NAME
    for changes in (
        {"BackendState": "Stopped"},
        {"Self": {"DNSName": "x.ts.net.", "UserID": 7, "Tags": ["tag:server"]}},
        {"CertDomains": None},
        {"User": {}},
    ):
        lacking = stand_in.made(tmp_path / str(len(changes)) / "ts", **changes)
        with pytest.raises(Refusal) as refused:
            tailnet.facts(tailnet.status(str(lacking)))
        assert refused.value.code == "tailnet", changes


def test_the_door_is_published_once_kept_after_and_only_lems_entry_is_taken_out(
    tmp_path: Path,
) -> None:
    cli = str(stand_in.made(tmp_path / "ts"))
    assert publish.publish(cli, stand_in.NAME, 4998) == "published"
    assert publish.publish(cli, stand_in.NAME, 4998) == "kept"
    assert publish.target(cli, stand_in.NAME, 4998)[1] == "http://127.0.0.1:4998"
    assert publish.removed(cli, stand_in.NAME, 4998) is True
    assert publish.removed(cli, stand_in.NAME, 4998) is False
    calls = stand_in.calls(Path(cli))
    assert "serve --bg --https=4998 http://127.0.0.1:4998" in calls
    assert "serve --https=4998 off" in calls


def test_a_port_another_entry_or_funnel_holds_is_refused_never_taken(
    tmp_path: Path,
) -> None:
    cli = stand_in.made(tmp_path / "ts")
    other = {
        "TCP": {"4998": {}},
        "Web": {
            f"{stand_in.NAME}:4998": {
                "Handlers": {"/": {"Proxy": "http://127.0.0.1:9000"}}
            }
        },
    }
    (cli.parent / "served.json").write_text(msgspec.json.encode(other).decode())
    with pytest.raises(Refusal):
        publish.publish(str(cli), stand_in.NAME, 4998)
    with pytest.raises(Refusal):
        publish.removed(str(cli), stand_in.NAME, 4998)
    funnel = {**other, "AllowFunnel": {f"{stand_in.NAME}:4998": True}}
    (cli.parent / "served.json").write_text(msgspec.json.encode(funnel).decode())
    with pytest.raises(Refusal) as refused:
        publish.publish(str(cli), stand_in.NAME, 4998)
    assert "Funnel" in refused.value.why
    assert not any("--bg" in call for call in stand_in.calls(cli))


def install_of(**changes: object) -> Install:
    mine = install.install_of()
    return msgspec.structs.replace(mine, **changes)


@pytest.mark.parametrize(
    ("theirs", "differ", "replaced"),
    [
        ({}, False, False),
        ({}, True, True),
        ({"stamp": 1}, False, True),
        ({"commit": "abc"}, False, True),
        ({"package": "/elsewhere/lem", "version": "0.0.1"}, False, True),
        ({"package": "/elsewhere/lem", "version": "99.0.0"}, False, False),
        ({"package": "/elsewhere/lem"}, True, False),
    ],
)
def test_the_replace_rule_with_the_door(
    theirs: dict[str, object], *, differ: bool, replaced: bool
) -> None:
    mine = install.install_of()
    assert (
        install.replaces(mine, install_of(**theirs), settings_differ=differ) is replaced
    )


def test_the_names_that_take_no_look_and_the_look_off(tmp_path: Path) -> None:
    for word in ("serve", "board", "doctor", "ask", "jev", "help", "version"):
        assert not look.wanted(word, {})
    assert look.wanted("task", {})
    assert look.wanted(None, {})
    assert not look.wanted("task", {"LEM_SERVE": "off"})


def test_a_server_lives_only_where_its_file_names_a_live_process(
    tmp_path: Path,
) -> None:
    assert not look.lives(tmp_path)
    (tmp_path / look.SERVE).write_text('{"pid": 0}')
    assert not look.lives(tmp_path)
    (tmp_path / look.SERVE).write_text("not json")
    assert not look.lives(tmp_path)
    (tmp_path / look.SERVE).write_text(f'{{"pid": {os.getpid()}}}')
    assert look.lives(tmp_path)
    ended = subprocess.Popen([sys.executable, "-c", "pass"])
    ended.wait()
    (tmp_path / look.SERVE).write_text(f'{{"pid": {ended.pid}}}')
    assert not look.lives(tmp_path)


def test_the_look_starts_ensure_under_the_commands_own_python_detached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started: list[dict[str, object]] = []

    def popen(argv: list[str], **given: object) -> None:
        started.append({"argv": argv, **given})

    monkeypatch.setattr(look.subprocess, "Popen", popen)
    environ = {"XDG_CONFIG_HOME": str(tmp_path)}
    look.looked("task", environ)
    [one] = started
    assert one["argv"] == [
        sys.executable,
        "-B",
        "-P",
        "-s",
        "-m",
        "lem",
        "serve",
        "ensure",
    ]
    assert one["start_new_session"] is True
    assert (tmp_path / "lem" / look.LOG).exists()
    look.looked("serve", environ)
    look.looked("task", {**environ, "LEM_SERVE": "off"})
    assert len(started) == 1


def test_a_cookie_nested_past_the_limit_is_no_preference_and_each_part_is_checked() -> (
    None
):
    deep = "[" * 10_000 + "]" * 10_000
    assert prefs.prefs_of(f"lem_board={deep}") == prefs.Prefs()
    told = '{"folded":["you","nope"],"rail":true,"pw":200,"full":true,"head":1}'
    found = prefs.prefs_of(f"lem_board={quote(told)}")
    assert found == prefs.Prefs(folded=("you",), rail=True, full=True)
    assert prefs.prefs_of(f"lem_board={quote('{"pw":800}')}").pw == 800
    assert prefs.prefs_of("other=1") == prefs.Prefs()
    assert prefs.prefs_of(None) == prefs.Prefs()


def test_a_workspace_goes_on_the_list_once_from_a_worktree_and_examples_stay_out(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    checkout = workspace_at(tmp_path / "shop")
    assert workspaces.noted(home, checkout) is not None
    assert workspaces.noted(home, checkout) is not None
    assert workspaces.listed(home) == (str(checkout.resolve()),)
    demo = workspace_at(tmp_path / "demo")
    (places.state_of(demo) / workspaces.DEMO).write_text("examples")
    workspaces.noted(home, demo)
    assert len(workspaces.listed(home)) == 1
    added = editing.added(home, demo)
    assert added.changed
    assert len(added.workspaces) == 2


def test_the_list_by_hand_refuses_a_checkout_with_no_lem_and_one_not_listed(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    bare = tmp_path / "bare"
    (bare / ".git").mkdir(parents=True)
    with pytest.raises(Refusal):
        editing.added(home, bare)
    shop = workspace_at(tmp_path / "shop")
    with pytest.raises(Refusal) as refused:
        editing.removed(home, shop)
    assert refused.value.code == "not-listed"
    editing.added(home, shop)
    gone = editing.removed(home, shop)
    assert gone.workspaces == ()


@pytest.mark.parametrize(
    "call",
    [
        Call(page="x.html", task="fix-the-login"),
        Call(page="x.html", no_open=True),
        Call(page="x.html", demo=True),
        Call(name="board"),
        Call(follow=True),
    ],
)
def test_lem_boards_words_that_do_not_go_together_are_refused(call: Call) -> None:
    with pytest.raises(Refusal):
        checked(call)


def test_a_server_leaves_the_session_it_was_started_from() -> None:
    environ = {
        "AGTERM_SESSION_ID": "S1",
        "AGT_SOCKET": "/tmp/x",
        "LEM_TASK": "fix-the-login",
        "PATH": "/usr/bin",
    }
    opening.detached(environ)
    assert environ == {"PATH": "/usr/bin"}


async def first_refresh(state: Path, home: Path, change: Path) -> str | None:
    """The stream's first message after a file is written a moment after it opens."""
    events = stream.events(
        state,
        rendered=stream.version(state),
        missed=False,
        home=home,
        task="fix-the-login",
    )

    async def write() -> None:
        await anyio.sleep(0.3)
        await anyio.Path(change).write_text("changed")

    try:
        async with anyio.create_task_group() as group:
            group.start_soon(write)
            with anyio.fail_after(10):
                event = await anext(events)
    finally:
        await events.aclose()
    return event.id


@pytest.mark.parametrize("which", ["owner.json", "settings", "demo", "artifact"])
def test_the_stream_polls_the_files_the_pages_read_beside_the_records(
    tmp_path: Path, which: str
) -> None:
    checkout = workspace_at(tmp_path / "shop")
    state = places.state_of(checkout)
    tasks.create(state, record("fix-the-login"))
    home = tmp_path / "home"
    home.mkdir()
    change = {
        "owner.json": home / "owner.json",
        "settings": checkout / ".lem" / "settings.local.toml",
        "demo": state / "demo",
        "artifact": state / "tasks" / "fix-the-login" / "report.md",
    }[which]
    told = anyio.run(first_refresh, state, home, change)
    assert told == stream.version(state)


def test_a_page_of_lem_to_read_opens_as_a_companion_of_the_session_never_over_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    terminal = FakeTerminal(panes={"S1": Pane(id="S1", name="task")}, caller="S1")
    monkeypatch.setattr(
        companion.wiring, "bound", lambda place: SimpleNamespace(terminal=terminal)
    )
    page = tmp_path / "handover.html"
    page.write_text("<p>read me</p>")
    opened = companion.page_opened(tmp_path, str(page), None)
    assert (opened.name, opened.beside) == ("handover", "S1")
    assert terminal.shown == [("S1", page.as_uri(), "companion")]
    text = tmp_path / "notes.md"
    text.write_text("# notes")
    with pytest.raises(Refusal):
        companion.page_opened(tmp_path, str(text), None)
    terminal.caller = None
    with pytest.raises(Refusal) as refused:
        companion.page_opened(tmp_path, str(page), "Hand-over")
    assert refused.value.code == "no-session"


def test_a_workspaces_counts_are_kept_a_while_and_counted_now_for_its_own_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    checkout = workspace_at(tmp_path / "shop")
    workspaces.noted(home, checkout)
    state = places.state_of(checkout)
    counts = Counts()
    [first] = counts.rows(home, "studio")
    assert first.building == 0
    tasks.create(state, record("fix-the-login", status="building"))
    [kept] = counts.rows(home, "studio")
    assert kept.building == 0
    [fresh] = counts.rows(home, "studio", fresh="shop")
    assert fresh.building == 1
    clock = iter([10_000.0, 10_000.0])
    monkeypatch.setattr(counts_module.time, "monotonic", lambda: next(clock))
    shutil.rmtree(checkout / ".lem")
    assert counts.rows(home, "studio") == ()


def test_a_quiet_stream_sends_a_ping_of_its_own_that_turbo_does_not_render() -> None:
    ping = stream.pinged()
    assert (ping.event, ping.data) == ("ping", "ping")
    assert stream.refresh("v1").event is None
