"""Inbox rules and the real HTTP adapter, with a local wire stand-in."""

import json
from typing import TYPE_CHECKING

import httpx
import msgspec
import pytest

from fakes import records
from lem.addons.inbox import (
    body,
    client,
    door,
    link,
    note,
    payload,
    rules,
    source,
    store,
)
from lem.addons.inbox.delivery import Delivery
from lem.addons.inbox.messages import Door, Payload
from lem.addons.inbox.records import Entry, Look, Record, Wait
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.owner.looks import Look as TaskLook
from lem.model.owner.looks import Row, Session
from lem.records.holds import OwnerHold, ReleaseHold
from lem.store import guard

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.owner.looks import Kind
    from lem.records.base import Moment
    from lem.records.landing.merge import Refused
    from lem.records.landing.record import Landing
    from lem.records.record import Record as TaskRecord

OPEN = Door(
    running=True, url="http://127.0.0.1:19080", tailnet_url="https://phone.test.invalid"
)
CLOSED = msgspec.structs.replace(OPEN, tailnet_url=None, why="no tailnet address")
NOW = clock.now()
WAIT = Wait(
    key="breaker:shop",
    task="shop",
    kind="breaker",
    since=NOW,
    asks=True,
    session="first",
)
NOTE = Wait(key="session:shop", task="shop", kind="session", since=NOW)


def prepare(wait: Wait) -> Entry:
    """The exact body remains on disk when a request loses its response."""
    key = "stable-key"
    return Entry(
        wait=wait,
        key=key,
        payload=Payload(
            body="Read the case",
            idempotency_key=key,
            project_path="/synthetic",
            thread=wait.task,
            subject="Question for the owner",
        ),
    )


def seen(
    *waits: Wait,
    away: bool = True,
    opened: Door = OPEN,
    behind: frozenset[str] = frozenset(),
    held: frozenset[str] = frozenset(),
) -> Look:
    return Look(away=away, door=opened, waits=waits, behind=behind, held=held)


def receipt(document: dict[str, object], *, stream: bool = False) -> httpx.Response:
    reply = {"jsonrpc": "2.0", "id": 1, "result": document}
    if stream:
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            text=f"event: message\ndata: {json.dumps(reply)}\n\n",
        )
    return httpx.Response(200, json=reply)


def test_door_status_and_loopback_boundary(tmp_path: Path) -> None:
    assert door.read(msgspec.json.encode(OPEN)) == OPEN
    assert door.read(msgspec.json.encode(CLOSED)).why == "no tailnet address"
    assert door.read(b"unreadable").why == "failed"
    assert door.stopped(1, "").why == "not running"
    assert door.stopped(2, "").why == "not answering"
    for invalid in (
        "http://127.0.0.1:4536",
        "http://127.0.0.1:4537",
        "https://outside.invalid:19080",
        "http://user@127.0.0.1:19080",
    ):
        blocked = msgspec.structs.replace(OPEN, url=invalid)
        assert not door.read(msgspec.json.encode(blocked)).running
        with httpx.Client(
            transport=httpx.MockTransport(
                lambda request: pytest.fail("Unexpected request")
            )
        ) as http:
            service = client.Inbox(opened=blocked, cwd=tmp_path, http=http)
            pending = prepare(WAIT).payload
            assert pending is not None
            with pytest.raises(Refusal):
                service.send(pending, WAIT.session)


def test_away_gates_new_sends_and_preserves_held_entries() -> None:
    entry = prepare(WAIT)
    assert rules.decide(seen(WAIT), ()).send == (WAIT,)
    assert not rules.decide(seen(WAIT, away=False), ()).send
    assert not rules.decide(seen(WAIT, opened=CLOSED), ()).send
    assert not rules.decide(msgspec.structs.replace(seen(WAIT), known=False), ()).send
    for away in (True, False):
        assert (
            rules.decide(seen(away=away, held=frozenset((WAIT.key,))), (entry,))
            == rules.Actions()
        )
    assert rules.decide(seen(WAIT, opened=CLOSED), (entry,)) == rules.Actions()
    assert rules.decide(seen(WAIT, away=False), (entry,)).forget == (entry,)
    assert rules.decide(seen(WAIT), (entry,)).retry == (entry,)
    assert rules.decide(seen(), (entry,)).forget == (entry,)


def test_failed_send_retries_the_same_payload_and_wakes_once(tmp_path: Path) -> None:
    state = tmp_path / "state"
    guard.writable(state)
    requests: list[dict[str, object]] = []
    wakes: list[str] = []

    def wake(task: str) -> bool:
        wakes.append(task)
        return True

    def request(sent: httpx.Request) -> httpx.Response:
        document = json.loads(sent.content)
        assert sent.url.path == "/mcp" and sent.url.host == "127.0.0.1"
        assert document["method"] == "tools/call"
        assert document["params"]["name"] == "send_message"
        expected = document["params"]["arguments"]
        assert expected["agent_host"] == "claude-code"
        assert expected["agent_session"] == "first"
        assert expected["project_path"] == "/synthetic"
        assert expected["thread"] == "shop"
        assert store.read(state).entries[0].payload is not None
        requests.append(document)
        if len(requests) == 1:
            raise httpx.ReadTimeout("test")
        return receipt(
            {"structuredContent": {"message_id": "msg_1", "url": "/thread/1"}},
            stream=True,
        )

    with httpx.Client(transport=httpx.MockTransport(request)) as http:
        service = client.Inbox(opened=OPEN, cwd=tmp_path, http=http)
        first = Delivery(
            state=state,
            now=NOW,
            service=service,
            wake=wake,
            prepare=prepare,
            saved=Record(),
        )
        failed = first.run(seen(WAIT), {})
        assert failed.problem and failed.entries[0].payload is not None
        assert wakes == []
        second = Delivery(
            state=state,
            now=NOW,
            service=service,
            wake=wake,
            prepare=prepare,
            saved=store.read(state),
        )
        done = second.run(seen(WAIT), {})
        assert len(requests) == 2 and requests[0] == requests[1]
        assert done.entries[0].payload is None and done.entries[0].sent is not None
        assert done.problem is None
        assert second.run(seen(WAIT), {}) == done
    assert wakes == ["shop"]
    assert (
        link.shown(state, "shop", away=True).url
        == "https://phone.test.invalid/thread/1"
    )
    assert link.shown(state, "shop", away=False).url is None


def test_replaced_or_answered_questions_and_new_session_reply(tmp_path: Path) -> None:
    state = tmp_path / "state"
    guard.writable(state)
    calls: list[dict[str, object]] = []
    wakes: list[str] = []
    kind = "shape"

    def wake(task: str) -> bool:
        wakes.append(task)
        return True

    def request(sent: httpx.Request) -> httpx.Response:
        call = json.loads(sent.content)["params"]
        calls.append(call)
        if call["name"] == "read_thread":
            assert "agent_session" not in call["arguments"]
            assert call["_meta"]["ai.plannotator/inbox-peek"] is True
            return receipt(
                {
                    "structuredContent": {
                        "thread": {
                            "messages": [
                                {"id": "msg_1", "author": {"kind": "agent"}},
                                {"id": "reply", "author": {"kind": "person"}},
                                {"id": "agent", "author": {"kind": "agent"}},
                            ]
                        }
                    }
                }
            )
        if "supersedes" in call["arguments"]:
            assert call["arguments"]["agent_session"] == "first"
            assert call["arguments"]["reply_to"] == "msg_1"
            if kind == "shape":
                return receipt(
                    {
                        "isError": True,
                        "content": [{"text": "invalid_supersedes: wrong shape"}],
                    }
                )
            if kind == "answered":
                return receipt(
                    {
                        "isError": True,
                        "content": [
                            {
                                "text": "invalid_supersedes: supersedes msg_1: that message has no open questions."
                            }
                        ],
                    }
                )
        return receipt(
            {"structuredContent": {"message_id": "msg_1", "url": "/thread/1"}}
        )

    with httpx.Client(transport=httpx.MockTransport(request)) as http:
        service = client.Inbox(opened=OPEN, cwd=tmp_path, http=http)
        delivery = Delivery(
            state=state,
            now=NOW,
            service=service,
            wake=wake,
            prepare=prepare,
            saved=Record(),
        )
        delivery.run(seen(WAIT), {})
        replacement = msgspec.structs.replace(WAIT, session="second")
        new = delivery.run(seen(replacement, away=False), {"shop": "second"})
        assert new.entries[0].wait == WAIT and new.entries[0].woke == ("reply",)
        delivery.run(seen(replacement, away=False), {"shop": "second"})
        assert wakes == ["shop", "shop"]
        assert (
            delivery.run(seen(replacement, opened=CLOSED), {}).entries[0].wait == WAIT
        )
        refused = delivery.run(seen(replacement), {})
        assert refused.entries[0].wait == WAIT and refused.problem
        kind = "answered"
        removed = delivery.run(seen(away=False), {})
        assert not removed.entries and removed.problem is None
    sent = [call for call in calls if call["name"] == "send_message"]
    assert len(sent) == 3


def test_note_needs_no_agent_and_no_withdrawal(tmp_path: Path) -> None:
    state = tmp_path / "state"
    guard.writable(state)
    calls = []

    def request(sent: httpx.Request) -> httpx.Response:
        given = json.loads(sent.content)["params"]
        calls.append(given)
        assert "agent_session" not in given["arguments"]
        return receipt(
            {"structuredContent": {"message_id": "note", "url": "/thread/note"}}
        )

    with httpx.Client(transport=httpx.MockTransport(request)) as http:
        delivery = Delivery(
            state=state,
            now=NOW,
            service=client.Inbox(opened=OPEN, cwd=tmp_path, http=http),
            wake=lambda task: pytest.fail("A note must not wake a session"),
            prepare=prepare,
            saved=Record(),
        )
        assert delivery.run(seen(NOTE), {}).entries[0].sent
        assert not delivery.run(seen(away=False), {}).entries
        assert len(calls) == 1


def fact(kind: Kind, *, claude: str | None = "first") -> source.RowFacts:
    record = records.record("shop")
    task = msgspec.structs.replace(record.task, ask="Repair the export")
    row = Row(
        kind=kind,
        key=f"{kind}:shop",
        task="shop",
        since=NOW,
        why="The export is blocked",
    )
    return source.RowFacts(
        row=row,
        look=TaskLook(
            record=msgspec.structs.replace(record, task=task),
            session=Session(live=True, since=NOW),
        ),
        claude=claude,
        now=NOW,
    )


def test_question_and_note_words_and_the_link() -> None:
    for kind, expected in (
        ("breaker", ("Help", "Park", "Drop")),
        ("plan", ("Build", "Drop")),
        ("blocked", ("What should the session", "The export is blocked")),
        ("held", ("waits for the owner", "The export is blocked")),
    ):
        found = fact(kind)
        waiting = source.wait_of(found)
        assert waiting and waiting.session == "first"
        drafted = payload.message(
            waiting,
            found,
            "/repo",
            "https://board.test.invalid/task",
            payload.Material(plan="plan.md"),
        )
        assert drafted.payload
        assert all(word in drafted.payload.body for word in expected)
        assert "https://board.test.invalid/task" in drafted.payload.body
        assert drafted.payload.attachments == (("plan.md",) if kind == "plan" else ())
    assert source.wait_of(fact("breaker", claude=None)) is None
    gone = fact("stopped")
    assert "replacement" in note.note(gone)
    unread = msgspec.structs.replace(
        gone, row=msgspec.structs.replace(gone.row, unread=True)
    )
    assert "could not read" in note.note(unread)
    release = ReleaseHold(
        began="older", running="new", say="The owner must drop and resume", since=NOW
    )
    stopped = msgspec.structs.replace(
        fact("blocked"),
        row=msgspec.structs.replace(fact("blocked").row, say=release.say),
    )
    stop_wait = source.wait_of(stopped)
    assert stop_wait and stop_wait.session is None
    assert note.note(stopped) == release.say
    order = fact("held")
    task = msgspec.structs.replace(
        order.look.record.task,
        hold=OwnerHold(on="order", line="A predecessor is ambiguous", since=NOW),
    )
    ordering = msgspec.structs.replace(
        order,
        look=msgspec.structs.replace(
            order.look, record=msgspec.structs.replace(order.look.record, task=task)
        ),
    )
    assert "Which task should shop wait for?" in body.question(ordering, None)


def test_reviewed_merge_binds_the_question_to_the_full_commit() -> None:
    eligible = merge_case()
    tip = "b" * 40
    ready = source.wait_of(eligible)
    assert ready and ready.tip == tip and ready.session == "first"
    shown = body.question(eligible, None)
    for expected in (
        tip,
        "Check the labels.",
        "https://forge.test.invalid/pull/3",
        "- [ ] Merge",
        "- [ ] Not now",
    ):
        assert expected in shown
    landing = eligible.look.record.landing
    assert landing
    stale = with_landing(eligible, msgspec.structs.replace(landing, reads=()))
    asking = source.wait_of(stale)
    assert asking and not asking.session and not asking.asks


def test_held_keys_match_breakers_and_plans_while_a_session_works() -> None:
    from lem.addons.inbox import held
    from lem.app.owner import forge, looking
    from lem.records.holds import BreakerHold
    from lem.records.owner import Presence

    record = records.record(
        "shop", status="building", hold=BreakerHold(number=4, since=NOW)
    )
    plan = records.record(
        "site",
        status="planned",
        hold=OwnerHold(on="plan", line="Review the plan", since=NOW),
    )
    busy = Session(live=True, working=True, since=NOW)
    looked = looking.Looked(
        looks=(
            TaskLook(record=record, session=busy),
            TaskLook(record=plan, session=busy),
        ),
        presence=Presence(away=True),
        forge=forge.Look(),
    )
    assert held.keys(looked) == {"breaker:shop:4", "plan:site"}


def test_poll_isolated_per_workspace_and_skips_unknown_sessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lem.addons.inbox import schedule, workspace
    from lem.app.owner import forge, looking
    from lem.records.owner import Presence
    from lem.store.places import Workspace

    class Bound:
        """The duty's disposable owner view."""

    projects = tuple(
        Workspace(
            checkout=tmp_path / name,
            lem=tmp_path / name / ".lem",
            state=tmp_path / name / ".lem" / "state",
        )
        for name in ("first", "second")
    )
    monkeypatch.setattr(workspace.here, "bound", lambda folder: Bound())
    monkeypatch.setattr(
        workspace.looking,
        "looked",
        lambda called, now: looking.Looked(
            looks=(),
            presence=Presence(away=True),
            forge=forge.Look(),
            unknown="terminal unavailable",
        ),
    )
    monkeypatch.setattr(
        workspace.door,
        "status",
        lambda: pytest.fail("Unknown sessions must skip the Inbox"),
    )
    assert workspace.tick(projects[1], NOW, "https://board.test.invalid") == Record()
    assert not projects[1].state.exists()
    real_tick = workspace.tick

    def fail_first(target: Workspace, now: Moment, url: str) -> Record:
        if target.checkout == projects[0].checkout:
            raise Refusal("offline", "first checkout failed", "open the board")
        return real_tick(target, now, url)

    monkeypatch.setattr(schedule.workspace, "tick", fail_first)
    reports = []
    schedule.cycle(
        lambda: tuple(
            schedule.Target(where=target, url="https://board.test.invalid")
            for target in projects
        ),
        lambda name, why: reports.append((name, why)),
    )
    assert reports == [
        ("*", None),
        ("first", "first checkout failed"),
        ("second", None),
    ]


def test_an_idle_inbox_with_a_damaged_record_is_no_duty_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lem.addons.inbox import workspace
    from lem.app.owner import forge, looking
    from lem.records.owner import Presence
    from lem.store.places import Workspace

    target = Workspace(
        checkout=tmp_path,
        lem=tmp_path / ".lem",
        state=tmp_path / ".lem" / "state",
    )
    monkeypatch.setattr(workspace.here, "bound", lambda folder: object())

    def seen(*, away: bool) -> looking.Looked:
        return looking.Looked(
            looks=(),
            presence=Presence(away=away),
            forge=forge.Look(),
            unread=("Lem omitted tasks/broken/task.json: the record does not read.",),
        )

    monkeypatch.setattr(workspace.looking, "looked", lambda *_: seen(away=False))
    assert workspace.tick(target, NOW, "https://board.test.invalid") == Record()
    monkeypatch.setattr(workspace.looking, "looked", lambda *_: seen(away=True))
    with pytest.raises(Refusal) as refused:
        workspace.tick(target, NOW, "https://board.test.invalid")
    assert refused.value.code == "unread-task-record"


def test_board_only_rows_and_forked_sessions_do_not_receive_questions(
    tmp_path: Path,
) -> None:
    from fakes.forge import LocalForge
    from fakes.git import ModelGit
    from fakes.ports import fake_ports
    from lem.addons.inbox.live import claude_of
    from lem.app.sessions.here import Here
    from lem.records.sessions import SessionLine
    from lem.store import places, sessions

    state = tmp_path / ".lem" / "state"
    guard.writable(state)
    git = ModelGit(checkout=tmp_path)
    here = Here(
        where=places.Workspace(checkout=tmp_path, lem=state.parent, state=state),
        ports=fake_ports(git, LocalForge(remote=git)),
    )
    folder = here.folder("shop")
    folder.mkdir(parents=True)
    live = fact("breaker").look
    sessions.append(
        folder,
        SessionLine(
            at=NOW,
            source="startup",
            claude="live",
            transcript="/synthetic/live.jsonl",
            task="shop",
        ),
    )
    sessions.append(
        folder,
        SessionLine(
            at=NOW,
            source="fork",
            claude="fork",
            transcript="/synthetic/fork.jsonl",
            task="shop",
        ),
    )
    assert claude_of(here, live) == "live"
    assert live.session is not None
    deaf = msgspec.structs.replace(live.session, unanswered=True)
    assert claude_of(here, msgspec.structs.replace(live, session=deaf)) is None
    read = fact("review").row
    merge = fact("merge").row
    card = fact("card").row
    breaker = fact("breaker").row
    note_row = fact("session").row
    assert source.eligible_rows((read, merge, card, breaker)) == (merge, breaker)
    assert source.eligible_rows((read, merge, card, breaker, note_row)) == (note_row,)


def merge_case() -> source.RowFacts:
    from lem.records.landing.propose import MergeRead, Proposed
    from lem.records.landing.record import Landing, Pull

    found = fact("merge")
    tip, base = "b" * 40, "a" * 40
    proposal = Proposed(tip=tip, base=base, at=NOW, green=True, who_acts="owner")
    review = MergeRead(
        tip=tip,
        base=base,
        base_tree=base,
        verdict="call",
        why="Check the labels.",
        at=NOW,
    )
    landing = Landing(
        phase="open",
        proposed=proposal,
        reads=(review,),
        pull=Pull(
            number=3, title="Repair export", url="https://forge.test.invalid/pull/3"
        ),
    )
    record = found.look.record
    return with_record(
        found,
        msgspec.structs.replace(
            record,
            task=msgspec.structs.replace(record.task, status="open"),
            landing=landing,
        ),
    )


def with_record(found: source.RowFacts, record: TaskRecord) -> source.RowFacts:
    return msgspec.structs.replace(
        found, look=msgspec.structs.replace(found.look, record=record)
    )


def with_landing(found: source.RowFacts, landing: Landing) -> source.RowFacts:
    return with_record(
        found, msgspec.structs.replace(found.look.record, landing=landing)
    )


def forge_refusal(tip: str) -> Refused:
    from lem.records.landing.merge import Refused

    return Refused(
        tip=tip,
        source="github",
        kind="rule",
        by="owner",
        at=NOW,
        line="GitHub requires a second approval.",
    )


def merge_poll(
    found: source.RowFacts, saved: tuple[Entry, ...] = (), *, away: bool = True
) -> tuple[Wait, rules.Actions]:
    wait = source.wait_of(found)
    assert wait is not None
    return wait, rules.decide(seen(wait, away=away), saved)


def sent_wait(wait: Wait) -> Entry:
    from lem.addons.inbox.messages import Sent

    return Entry(wait=wait, key="stable-key", sent=Sent(message_id="old", url="/old"))


def test_new_review_on_same_tip_withdraws_and_replaces_the_question(
    tmp_path: Path,
) -> None:
    found = merge_case()
    original, _ = merge_poll(found)
    old = sent_wait(original)
    landing = found.look.record.landing
    assert landing
    refreshed = msgspec.structs.replace(
        landing.reads[0],
        base="c" * 40,
        base_tree="d" * 40,
        base_call="safe",
        why="Check the tax change.",
    )
    changed = with_landing(
        found, msgspec.structs.replace(landing, reads=(*landing.reads, refreshed))
    )
    updated, actions = merge_poll(changed, (old,))
    assert (updated.tip, updated.since, updated.session) == (
        original.tip,
        original.since,
        original.session,
    )
    assert actions.withdraw == (old,) and actions.send == (updated,)
    assert merge_poll(changed, (old,), away=False)[1].withdraw == (old,)
    calls: list[dict[str, object]] = []

    def send(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content)["params"]["arguments"])
        return receipt({"structuredContent": {"message_id": "new", "url": "/thread/1"}})

    guard.writable(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(send)) as http:
        delivery = Delivery(
            state=tmp_path,
            now=NOW,
            service=client.Inbox(opened=OPEN, cwd=tmp_path, http=http),
            wake=lambda task: True,
            prepare=lambda wait: payload.message(
                wait, changed, "/repo", "https://board.test.invalid", payload.Material()
            ),
            saved=Record(entries=(old,)),
        )
        assert delivery.run(seen(updated), {}).problem is None
    assert len(calls) == 2
    assert calls[0]["supersedes"] == ["old"]
    assert "Check the tax change." in str(calls[1]["body"])


def test_new_proposal_clears_the_previous_merge_refusal() -> None:
    from lem.app.landing import propose_made

    record = merge_case().look.record
    landing = record.landing
    assert landing and landing.proposed and landing.pull
    refused = forge_refusal(landing.proposed.tip)
    before = msgspec.structs.replace(
        record, landing=msgspec.structs.replace(landing, refused=refused)
    )
    made = msgspec.structs.replace(landing.proposed, tip="c" * 40)
    updated = propose_made.opened(before, made=made, pull=landing.pull)
    assert updated.landing and updated.landing.proposed == made
    assert updated.landing.refused is None


def test_stale_refusal_allows_a_question_and_current_refusal_explains_why() -> None:
    found = merge_case()
    landing = found.look.record.landing
    assert landing and landing.proposed
    stale = with_landing(
        found, msgspec.structs.replace(landing, refused=forge_refusal("c" * 40))
    )
    wait, _ = merge_poll(stale)
    assert wait.session == "first"
    assert "did not go through" not in note.merge_note(stale)
    refused = forge_refusal(landing.proposed.tip)
    current = with_landing(found, msgspec.structs.replace(landing, refused=refused))
    wait, _ = merge_poll(current)
    assert wait.session is None
    assert refused.line in note.merge_note(current)


def test_merge_polls_replace_the_tip_then_send_the_refusal_as_a_note() -> None:
    found = merge_case()
    original, _ = merge_poll(found)
    old = sent_wait(original)
    landing = found.look.record.landing
    assert landing and landing.proposed
    tip = "c" * 40
    next_landing = msgspec.structs.replace(
        landing,
        proposed=msgspec.structs.replace(landing.proposed, tip=tip),
        reads=(msgspec.structs.replace(landing.reads[0], tip=tip),),
    )
    updated, actions = merge_poll(with_landing(found, next_landing), (old,))
    assert updated.tip == tip and updated.session == old.wait.session
    assert actions.withdraw == (old,) and actions.send == (updated,)
    refused = forge_refusal(tip)
    stopped = with_landing(
        found, msgspec.structs.replace(next_landing, refused=refused)
    )
    replacement = sent_wait(updated)
    message, actions = merge_poll(stopped, (replacement,))
    assert actions.withdraw == (replacement,) and actions.send == (message,)
    assert message.session is None and not message.asks
    drafted = payload.message(
        message, stopped, "/repo", "https://board.test.invalid", payload.Material()
    )
    assert drafted.payload and refused.line in drafted.payload.body
    assert ":::question" not in drafted.payload.body


def test_poll_resumes_after_the_workspace_list_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import anyio

    from lem.addons.inbox import schedule
    from lem.board import workspaces
    from lem.store.places import Workspace

    path = tmp_path / workspaces.WORKSPACES
    path.write_text("{")
    reports: list[tuple[str, str | None]] = []
    visited: list[Workspace] = []
    project = Workspace(
        checkout=tmp_path / "shop", lem=tmp_path / "lem", state=tmp_path / "state"
    )
    target = schedule.Target(where=project, url="https://board.test.invalid")

    def targets() -> tuple[schedule.Target, ...]:
        return tuple(target for _ in workspaces.listed(tmp_path))

    def tick(where: Workspace, now: Moment, url: str) -> Record:
        visited.append(where)
        return Record()

    async def run() -> None:
        stopped = anyio.Event()

        def report(name: str, why: str | None) -> None:
            reports.append((name, why))
            if why:
                path.write_text('["/scratch/shop"]')
            elif name == "shop":
                anyio.from_thread.run_sync(stopped.set)

        with anyio.fail_after(3):
            await schedule.run(targets, report, stopped)

    monkeypatch.setattr(schedule, "INTERVAL", 0)
    monkeypatch.setattr(schedule.workspace, "tick", tick)
    anyio.run(run)
    assert visited == [project]
    assert reports[0][0] == "*" and "no list of workspaces" in (reports[0][1] or "")
    assert reports[1:] == [("*", None), ("shop", None)]


def test_breaker_question_includes_the_document_for_the_current_hold(
    tmp_path: Path,
) -> None:
    from fakes.forge import LocalForge
    from fakes.git import ModelGit
    from fakes.ports import fake_ports
    from lem.addons.inbox.prepare import prepare as draft
    from lem.app.sessions.here import Here
    from lem.records.decisions import Breaker
    from lem.records.holds import BreakerHold
    from lem.store.places import Workspace

    state = tmp_path / ".lem" / "state"
    git = ModelGit(checkout=tmp_path)
    here = Here(
        where=Workspace(checkout=tmp_path, lem=state.parent, state=state),
        ports=fake_ports(git, LocalForge(remote=git)),
    )
    folder = here.folder("shop")
    folder.mkdir(parents=True)
    old = Breaker(
        id=1,
        at=NOW,
        cause="criteria",
        what="Prior decision",
        document="breaker-1.md",
        handoff="handoff.md",
    )
    current = msgspec.structs.replace(
        old, id=2, what="Confirm the export", document="breaker-2.md"
    )
    (folder / old.document).write_text("Old plan")
    document = folder / current.document
    document.write_text(
        "## Confirm the export\n\nThe warehouse will lose its pending orders.",
        encoding="utf-8",
    )
    found = fact("breaker")
    record = found.look.record
    task = msgspec.structs.replace(
        record.task,
        decisions=(old, current),
        hold=BreakerHold(number=current.id, since=NOW),
    )
    updated = with_record(found, msgspec.structs.replace(record, task=task))
    wait = source.wait_of(updated)
    assert wait and wait.session
    sent = draft(here, "https://board.test.invalid", (updated,), wait)
    assert (
        sent.payload
        and "The warehouse will lose its pending orders." in sent.payload.body
    )
    assert "Old plan" not in sent.payload.body
    assert all(choice in sent.payload.body for choice in ("Help", "Park", "Drop"))
    document.write_bytes(b"\xff")
    fallback = draft(here, "https://board.test.invalid", (updated,), wait)
    assert fallback.payload and "Confirm the export" in fallback.payload.body
