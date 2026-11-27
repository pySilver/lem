"""The jump to a task's session of a joined machine: the choice of the row this Mac's agterm already
holds, the check of the session id, each failure's refusal with its fix, the notice of a group not
whole, one jump at a time, and the act on the board of the Mac where the owner works, with the
joined board a stand-in transport."""

import asyncio
import subprocess
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import httpx
import msgspec
import pytest
from starlette.applications import Starlette
from starlette.requests import Request

from lem.adapters import agterm_remote, agterm_reply
from lem.adapters.agterm_group_forms import Attached, Group, Member, Reply
from lem.adapters.agterm_remote_forms import Listing, Moded
from lem.adapters.agterm_reply import error_of, refused_by
from lem.adapters.agterm_tree import Node
from lem.addons.peers import (
    agterm_said,
    attach_guard,
    attaching,
    group_said,
    jump,
    origin,
    registry,
    requests,
    routes,
    table,
)
from lem.board import prefs
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

PEER = "mini"
PORT = 19037
LOCAL = "http://127.0.0.1:4636"
SENT = {"origin": LOCAL, "sec-fetch-site": "same-origin"}
SESSION = "6F1C2A30-0000-4000-8000-000000000007"
JUMP = f"/{PEER}/shop/agterm/{SESSION}"
# The workspace of a case whose read of the records stands in.
NO_SPACE = cast("Workspace", SimpleNamespace())


def test_a_row_attached_from_the_session_is_chosen_and_any_other_is_not() -> None:
    assert attaching.from_session(
        Node(id="R-2", remote_host="Mini", remote_session=SESSION.lower()),
        PEER,
        SESSION,
    )
    assert not attaching.from_session(Node(id="L-1", name="notes"), PEER, SESSION)
    other = Node(id="R-1", remote_host="other", remote_session=SESSION)
    assert not attaching.from_session(other, PEER, SESSION)
    later = Node(id="R-3", remote_host=PEER, remote_session=SESSION[:-1] + "8")
    assert not attaching.from_session(later, PEER, SESSION)


def test_a_row_from_the_machine_that_names_no_origin_is_refused() -> None:
    with pytest.raises(Refusal) as caught:
        attaching.from_session(Node(id="R-9", remote_host=PEER), PEER, SESSION)
    assert caught.value.code == "agterm-old" and "0.42.0" in caught.value.why
    assert caught.value.fix == "on this Mac, the owner updates agterm"


@pytest.mark.parametrize(
    "given",
    [
        "-oProxyCommand=touch",
        "S-7",
        SESSION + "0",
        " " + SESSION,
        SESSION.replace("-", "_"),
        "",
    ],
    ids=("option", "short", "long", "space", "underscore", "empty"),
)
def test_only_a_full_agterm_id_passes_the_check(given: str) -> None:
    with pytest.raises(Refusal) as caught:
        agterm_said.checked_id(given)
    assert caught.value.code == "session-id"
    assert agterm_said.checked_id(SESSION.lower()) == SESSION.lower()


@pytest.mark.parametrize(
    ("said", "code", "refused"),
    [
        ("sh: agtermctl: command not found", 1, "peer-agtermctl"),
        ("", 127, "peer-agtermctl"),
        ("ssh: Could not resolve hostname mini: nodename nor servname", 1, "peer-ssh"),
        ("ssh: connect to host mini port 22: Connection refused", 255, "peer-ssh"),
        ("kex_exchange_identification: Connection reset by peer", 1, "peer-ssh"),
        ("zmx is unavailable in this instance", 1, "peer-agterm-live"),
        (
            "the remote agterm is too old to report its zmx endpoint",
            1,
            "peer-agterm-old",
        ),
        ("the remote did not return a readable session list", 1, "peer-agterm-old"),
        ("Error: Unexpected argument 'tree'", 1, "peer-agterm-old"),
        ("something new", 1, "peer-agterm"),
    ],
    ids=(
        "no-cli",
        "exit-127",
        "no-host",
        "refused",
        "reset",
        "not-live",
        "old",
        "unread",
        "usage",
        "other",
    ),
)
def test_each_answer_of_the_far_mac_is_a_refusal_with_its_fix(
    said: str, code: int, refused: str
) -> None:
    found = agterm_said.far(PEER, "mini", said, code)
    assert found.code == refused
    assert found.fix
    if refused == "peer-ssh":
        assert "ssh mini true" in found.fix
        assert "`Host mini` alias in ~/.ssh/config" in found.fix
    if refused == "peer-agterm-live":
        assert "On mini".lower() in found.fix.lower()
        assert "this Mac's agterm needs no Live sessions" in found.why


def ran(code: int, out: str = "", err: str = "") -> subprocess.CompletedProcess[str]:
    """A call of agtermctl that ended with `code`."""
    return subprocess.CompletedProcess(["agtermctl"], code, out, err)


def test_agtermctls_own_reply_and_its_parser_are_told_apart() -> None:
    replied = refused_by(
        ran(1, '{"ok":false,"error":"no attachable session X on mini"}')
    )
    assert (replied.said, replied.usage) == ("no attachable session X on mini", False)
    parser = refused_by(ran(64, err="Error: Unknown option '--companions'\nUsage: ..."))
    assert parser.usage and parser.said.startswith("Error: Unknown option")
    assert error_of('{"ok":true,"result":{}}') is None
    assert error_of("not json") is None


def test_agterms_real_restore_reply_and_a_list_without_sessions() -> None:
    owner = (
        '{"result":{"restore":{"restartRequired":false,"configured":"rerun",'
        '"requestedAtLaunch":"rerun","active":"rerun"}},"ok":true}'
    )
    assert msgspec.json.decode(owner, type=Moded).found.restore.active == "rerun"
    with pytest.raises(Unanswered, match="zmx tree printed no answer of its form"):
        agterm_reply.decoded(
            '{"result":{"remote":{"host":"mini"}}}', Listing, "zmx tree"
        )


def stood_in(monkeypatch: pytest.MonkeyPatch, said: str, code: int) -> None:
    """agterm's attach refuses with `said` and `code`, from agtermctl's own parser when 64."""

    def attach(environ: object, host: str, session: str) -> Reply:
        raise refused_by(ran(code, err=said) if code == 64 else ran(code, said))

    monkeypatch.setattr(agterm_remote, "attach", attach)


@pytest.mark.parametrize(
    ("said", "code", "refused"),
    [
        ("Error: Unknown option '--companions'", 64, "agterm-old"),
        (
            '{"ok":false,"error":"the running app is too old for group attach"}',
            1,
            "agterm-old",
        ),
        (
            '{"ok":false,"error":"no attachable session X on mini"}',
            1,
            "peer-session-gone",
        ),
        ('{"ok":false,"error":"ssh: Connection reset by peer"}', 1, "peer-ssh"),
    ],
    ids=("old-cli", "old-app", "gone-between", "reset"),
)
def test_each_refusal_of_the_attach_names_its_fix(
    monkeypatch: pytest.MonkeyPatch, said: str, code: int, refused: str
) -> None:
    stood_in(monkeypatch, said, code)
    with pytest.raises(Refusal) as caught:
        attaching.attach({}, PEER, PEER, SESSION)
    assert caught.value.code == refused


def test_a_group_not_whole_gets_a_notice_and_a_whole_one_none() -> None:
    whole = Reply(
        found=Attached(
            id="R-1", group=Group(companions=(Member(origin="C", id="R-2"),))
        )
    )
    assert group_said.opened(PEER, whole).notice is None
    kept = Reply(
        ok=False,
        error="kept refund (R-1) and 0 companion(s); not attached: talk (unavailable on mini)",
        found=Attached(
            id="R-1", group=Group(companions=(Member(origin="C", error="x"),))
        ),
    )
    said = group_said.notice_of(PEER, kept) or ""
    assert "Not attached: C" in said and "talk (unavailable on mini)" in said
    unknown = Reply(found=Attached(id="R-1", group=Group(known=False)))
    assert "does not say which companions" in (
        group_said.notice_of(PEER, unknown) or ""
    )


def test_one_jump_at_a_time_for_each_session(monkeypatch: pytest.MonkeyPatch) -> None:
    guard = attach_guard.Guard()
    held: list[bool] = []

    def stand_in(
        environ: object, peer: str, host: str, session: str
    ) -> group_said.Shown:
        held.append(guard.of(host.upper(), session.lower()).locked())
        return group_said.Shown(said="x")

    monkeypatch.setattr(attaching, "shown", stand_in)
    guard.shown({}, (PEER, PEER, SESSION))
    assert held == [True]
    assert guard.of(PEER, SESSION) is guard.of("MINI", SESSION.lower())
    assert guard.of(PEER, SESSION) is not guard.of("other", SESSION)
    assert not guard.of(PEER, SESSION).locked()


def board(
    tmp_path: Path, answer: httpx.MockTransport, door: int | None = None
) -> Starlette:
    """The routes of the peers on the board of `alpha`, with `mini` joined."""
    home = tmp_path / "alpha"
    table.change(home, PEER, PORT)
    made = Starlette(routes=list(routes.ROUTES))
    made.state.home = home
    made.state.facts = SimpleNamespace(host="alpha", door=door)
    made.state.environ = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    made.state.peer_own_rows = lambda request: ()

    async def address(host: str, port: int) -> str:
        assert (host, port) == (PEER, PORT)
        return "https://mini.test.invalid:19037"

    made.state.peer_registry = registry.Registry(
        home=home, own="alpha", address=address, transport=answer
    )
    return made


def posted(app: Starlette, path: str = JUMP, **headers: str) -> httpx.Response:
    """The page's POST to the board of this Mac."""

    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=LOCAL) as client:
            return await client.post(path, headers={**SENT, **headers})

    return asyncio.run(run())


def replies(
    status: int, reply: dict[str, object] | None, body: bytes = b"Not Found"
) -> httpx.MockTransport:
    """The joined board's answer to the read of the session: JSON of `reply`, else `body`."""

    def answer(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET" and request.url.path == JUMP
        assert request.headers[requests.HOP] == "1"
        if reply:
            return httpx.Response(status, json=reply)
        return httpx.Response(status, content=body)

    return httpx.MockTransport(answer)


def origin_says(status: int, **reply: object) -> httpx.MockTransport:
    """The joined board's JSON answer `reply`, or a text one when there is none."""
    return replies(status, reply or None)


def recorded(
    monkeypatch: pytest.MonkeyPatch, shown: group_said.Shown
) -> list[tuple[str, ...]]:
    """The steps in this Mac's agterm stand in: each call's peer, host and session."""
    calls: list[tuple[str, ...]] = []

    def stand_in(
        environ: object, peer: str, host: str, session: str
    ) -> group_said.Shown:
        calls.append((peer, host, session))
        return shown

    monkeypatch.setattr(attaching, "shown", stand_in)
    return calls


def test_the_act_reads_the_session_and_attaches_by_the_tailnet_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = recorded(monkeypatch, group_said.Shown(said=group_said.SWITCHED))
    app = board(tmp_path, origin_says(200, session=SESSION.lower(), live=True))
    found = posted(app)
    assert found.json() == {"done": True, "said": "Switched to the session."}
    assert calls == [(PEER, PEER, SESSION)]


def test_a_notice_comes_back_beside_the_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorded(monkeypatch, group_said.Shown(said="Opened.", notice="Not attached: C."))
    app = board(tmp_path, origin_says(200, session=SESSION, live=True))
    assert posted(app).json() == {
        "done": True,
        "said": "Opened.",
        "notice": "Not attached: C.",
    }


def said_of(found: httpx.Response) -> str:
    """The line the page shows beside its button, for a refused jump."""
    assert found.status_code == 422, found.text
    assert found.json()["done"] is False
    return found.json()["said"]


def test_a_reply_that_names_another_session_is_refused_before_any_agterm_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = recorded(monkeypatch, group_said.Shown(said="x"))
    other = "6F1C2A30-0000-4000-8000-000000000008"
    said = said_of(posted(board(tmp_path, origin_says(200, session=other, live=True))))
    assert f"it named the session '{other}', not {SESSION}" in said
    assert calls == []


def test_a_session_that_is_no_agterm_id_is_refused_before_any_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = recorded(monkeypatch, group_said.Shown(said="x"))

    def never(request: httpx.Request) -> httpx.Response:
        raise AssertionError(request.url)

    app = board(tmp_path, httpx.MockTransport(never))
    said = said_of(posted(app, f"/{PEER}/shop/agterm/-oProxyCommand=x"))
    assert "is no agterm session id" in said and calls == []


def test_a_far_agterm_outside_live_sessions_is_refused_before_any_ssh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = recorded(monkeypatch, group_said.Shown(said="x"))
    said = said_of(
        posted(board(tmp_path, origin_says(200, session=SESSION, live=False)))
    )
    assert "the agterm on mini does not run Live sessions" in said
    assert "on mini, the owner sets" in said and calls == []


def test_a_gone_session_on_an_agterm_that_did_not_say_its_mode_names_both(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def gone(environ: object, peer: str, host: str, session: str) -> group_said.Shown:
        raise agterm_said.gone(peer, session)

    monkeypatch.setattr(attaching, "shown", gone)
    unsure = origin_says(200, session=SESSION, live=None, said="agterm does not answer")
    said = said_of(posted(board(tmp_path, unsure)))
    assert "is gone on mini, or the agterm on mini does not run Live sessions" in said
    assert "(it did not say: agterm does not answer)" in said


@pytest.mark.parametrize(
    ("status", "reply", "words"),
    [
        (404, {"code": "gone", "why": "no task"}, "the session 6F1C2A30"),
        (
            409,
            {
                "code": "records",
                "why": "task.json does not read",
                "fix": "the owner restores it",
            },
            "cannot tell the task's session: task.json does not read; on mini, the owner restores it",
        ),
        (403, None, "refused the read (403); the owner checks that mini and this Mac"),
        (500, None, "failed on the read (500); the owner reads lem.log"),
        (404, None, "does not tell its agterm's sessions (it answered 404)"),
        (405, None, "the owner updates Lem on mini"),
    ],
    ids=("gone", "record", "login", "fault", "old-404", "old-405"),
)
def test_each_answer_of_the_joined_board_is_its_own_refusal(
    tmp_path: Path, status: int, reply: dict[str, str] | None, words: str
) -> None:
    answer = replies(status, dict(reply) if reply else None)
    assert words in said_of(posted(board(tmp_path, answer)))


def test_a_reply_past_the_json_limit_is_not_read_whole(tmp_path: Path) -> None:
    huge = b"x" * (requests.JSON_CAP + 10)
    for status in (200, 500):
        said = said_of(
            posted(board(tmp_path / str(status), replies(status, None, huge)))
        )
        assert "exceeds the board's JSON limit" in said


def test_a_joined_board_that_does_not_answer_is_named(tmp_path: Path) -> None:
    def asleep(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("no answer", request=request)

    said = said_of(posted(board(tmp_path, httpx.MockTransport(asleep))))
    assert "the board of mini did not answer: no answer" in said
    assert "lem serve peers" in said


def test_no_jump_through_the_door_or_from_another_site(tmp_path: Path) -> None:
    never = origin_says(500)
    through = posted(board(tmp_path / "door", never, door=4636))
    assert through.status_code == 403 and "the phone has no agterm" in through.text
    elsewhere = posted(board(tmp_path / "site", never), origin="https://else.invalid")
    assert elsewhere.status_code == 403


def test_a_read_of_the_same_address_passes_to_the_joined_machine(
    tmp_path: Path,
) -> None:
    def page(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/workspaces":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={"session": SESSION, "live": True})

    app = board(tmp_path, httpx.MockTransport(page))

    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=LOCAL) as client:
            return await client.get(JUMP)

    assert asyncio.run(run()).json() == {"session": SESSION, "live": True}
    assert posted(app, f"/elsewhere/shop/agterm/{SESSION}").status_code == 405


def request_of(**headers: str) -> Request:
    """A request to the board's main listener on port 4636."""
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/mini/shop/",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "client": ("127.0.0.1", 50000),
            "server": ("127.0.0.1", 4636),
            "app": SimpleNamespace(
                state=SimpleNamespace(facts=SimpleNamespace(door=4637))
            ),
        }
    )


def test_a_relayed_page_draws_the_jump_only_for_the_relaying_macs_own_page() -> None:
    marked = prefs.asker_of(request_of(**{"Lem-Hop": "1", "Lem-Agterm": "1"}))
    assert (marked.local, marked.may_act) == (True, False)
    plain = prefs.asker_of(request_of(**{"Lem-Hop": "1"}))
    assert (plain.local, plain.may_act) == (False, False)
    sent = requests.outgoing({}, (), here=True)
    assert sent[requests.HERE] == "1"
    assert requests.HERE not in requests.outgoing({"lem-agterm": "1"}, ())


def test_the_board_says_why_then_the_fix() -> None:
    assert jump.line_of(agterm_said.gone(PEER, "S-7")) == (
        "the session S-7 of the task is gone on mini; "
        "the owner opens a session of the task again from the board of mini."
    )


def test_the_relay_marks_a_page_read_on_this_mac_and_not_one_through_the_door(
    tmp_path: Path,
) -> None:
    marks: list[str | None] = []

    def page(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/workspaces":
            return httpx.Response(200, json=[])
        marks.append(request.headers.get(requests.HERE))
        return httpx.Response(200, text="the page")

    for door in (None, 4636):
        app = board(tmp_path / str(door), httpx.MockTransport(page), door=door)

        async def run(made: Starlette = app) -> httpx.Response:
            transport = httpx.ASGITransport(app=made)
            async with httpx.AsyncClient(transport=transport, base_url=LOCAL) as client:
                return await client.get("/mini/shop/")

        assert asyncio.run(run()).text == "the page"
    assert marks == ["1", None]


def test_the_joined_board_passes_its_record_repair_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unread(space: object, session: str) -> str | None:
        raise Refusal("records", "task.json does not read", "the owner restores it")

    monkeypatch.setattr(origin.jump, "named", unread)
    told = origin.found(NO_SPACE, SESSION, {})
    assert told == origin.Told(
        code="records", why="task.json does not read", fix="the owner restores it"
    )
    monkeypatch.setattr(origin.jump, "named", lambda space, session: None)
    assert origin.found(NO_SPACE, SESSION, {}) == origin.Told(
        code=origin.GONE, why="That is no session of this workspace's tasks."
    )
