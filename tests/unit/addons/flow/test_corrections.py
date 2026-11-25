"""The correction queue: the worker on the correction the hook writes, the machine's switch, and
what a retro reads and records (`main`: tests/unit/test_corrections.py and tests/lem-machine.sh,
`corrections.py`).

The waiting correction is written by the hook's own writer (`lem.hooks.handoff.correction`, the
bytes tests/hooks/test_corrections.py checks), and Jev is a stand-in transport of `httpx`.
"""

import ast
import inspect
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import click
import httpx
import msgspec
import pytest

from fakes.command import lem
from lem.adapters import judge_jev_ask
from lem.addons.corrections import groups, listing, question, queue, reviewing, worker
from lem.cli.corrections import record as record_command
from lem.cli.words import choice
from lem.hooks import handoff
from lem.kernel import folders
from lem.kernel.errors import Refusal
from lem.records.corrections import Correction
from unit.task.spaces import refusal, result, rows, workspace

if TYPE_CHECKING:
    from collections.abc import Callable

NOW = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)
PROMPT = "never push without asking"
HOOKS = Path(__file__).resolve().parents[4] / "src" / "lem" / "hooks"


class Jev:
    """A stand-in for Jev: each request it was sent, and the score it gives."""

    def __init__(self, score: float | None) -> None:
        self.score = score
        self.sent: list[dict[str, object]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.sent.append(body)
        if self.score is None:
            return httpx.Response(500)
        answer = {"lesson": {"type": "noul", "noul": self.score}}
        return httpx.Response(200, json={"answers": answer})

    def asker(self, key: str | None = "a-key") -> judge_jev_ask.Asker:
        transport = httpx.MockTransport(self)
        return judge_jev_ask.Asker(
            key=key, url="https://jev", model="m", transport=transport
        )


def home(
    folder: Path, machine: str | None = "[corrections]\ncollect = true\n"
) -> dict[str, str]:
    """A home folder of this Lem with the machine file `machine`; its environment."""
    made = folder / "lem"
    made.mkdir(parents=True)
    (made / folders.MARKER).write_bytes(folders.FORM)
    if machine is not None:
        (made / "machine.toml").write_text(machine)
    return {"XDG_CONFIG_HOME": str(folder), "HOME": str(folder)}


def waiting(state: Path, prompt: str = PROMPT, session: str = "c1") -> Path:
    """The correction the hook writes into the waiting folder."""
    folder = state / queue.WAITING
    folder.mkdir(exist_ok=True)
    path = folder / f"{len(list(folder.iterdir()))}-1.json"
    path.write_bytes(handoff.correction(session, str(state.parents[1]), prompt, ""))
    return path


def entry(owner: str, session: str, at: str) -> Correction:
    """A queued correction of `owner`'s words."""
    moment = datetime.fromisoformat(at)
    return Correction(
        at=moment,
        session=session,
        cwd="/repo",
        owner=owner,
        previous="Done.",
        p_lesson=0.5,
    )


def queued(state: Path, *entries: Correction) -> None:
    for one in entries:
        queue.appended(state / queue.QUEUE, one)


def test_a_lesson_the_hook_handed_on_is_queued_with_jevs_probability(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path / "repo").state
    path = waiting(state)
    jev = Jev(0.8)
    done = worker.worked(path, home(tmp_path / "config"), NOW, jev.asker())
    assert (done.queued, done.p_lesson) == (True, 0.8)
    assert not path.exists()
    (one,) = queue.lines(state / queue.QUEUE, Correction)
    assert (one.owner, one.p_lesson, one.previous) == (PROMPT, 0.8, handoff.NO_PREVIOUS)
    (sent,) = jev.sent
    assert sent["state"] == {
        "the agent's last message": handoff.NO_PREVIOUS,
        "the owner's reply": PROMPT,
    }
    assert oct((state / queue.QUEUE).stat().st_mode & 0o777) == "0o600"


def test_a_low_score_queues_nothing_and_a_message_too_long_for_jev_is_queued_unjudged(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path / "repo").state
    environ = home(tmp_path / "config")
    low = worker.worked(waiting(state), environ, NOW, Jev(0.1).asker())
    assert (low.queued, low.p_lesson) == (False, 0.1)
    long_one = Jev(0.9)
    told = worker.worked(waiting(state, "x " * 20_000), environ, NOW, long_one.asker())
    assert (told.queued, told.why) == (True, worker.TOO_LONG)
    assert long_one.sent == []
    (one,) = queue.lines(state / queue.QUEUE, Correction)
    assert (one.p_lesson, one.why) == (None, "too long for Jev")


def test_a_failure_of_jev_is_a_line_of_the_log_and_the_list_counts_it_first(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path / "repo").state
    environ = home(tmp_path / "config")
    worker.worked(waiting(state), environ, NOW, Jev(None).asker())
    worker.worked(waiting(state), environ, NOW, Jev(0.9).asker(key=None))
    handoff.logged(str(state), "c1", ("note", "the hook could not claim the message"))
    found = listing.listed(state, collect=True)
    assert found.failures.count == 2
    assert found.failures.newest is not None
    assert found.failures.newest.error == "jev gave no answer: no key"
    assert PROMPT not in (state / queue.LOG).read_text()
    assert found.groups == ()


@pytest.mark.parametrize("status", [401, 503])
def test_the_correction_log_keeps_jevs_http_status(tmp_path: Path, status: int) -> None:
    state = workspace(tmp_path / "repo").state
    environ = home(tmp_path / "config")
    transport = httpx.MockTransport(lambda _: httpx.Response(status, text=PROMPT))
    asker = judge_jev_ask.Asker(
        key="a-key", url="https://jev", model="m", transport=transport
    )
    worked = worker.worked(waiting(state), environ, NOW, asker)
    assert not worked.queued
    found = listing.listed(state, collect=True)
    assert found.failures.newest is not None
    error = found.failures.newest.error
    assert error is not None
    assert f"HTTP {status}" in error
    assert PROMPT not in (state / queue.LOG).read_text()


def test_with_no_yes_of_the_machine_nothing_is_sent_and_the_words_leave_no_file(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path / "repo").state
    old = tmp_path / "old" / "lem"
    old.mkdir(parents=True)
    (old / "machine.toml").write_text("[corrections]\ncollect = true\n")
    homes = (
        home(tmp_path / "none", None),
        home(tmp_path / "no", "[corrections]\ncollect = false\n"),
        home(tmp_path / "bad", "[corrections]\ncollect = true\nsend = true\n"),
        home(tmp_path / "broken", "[corrections"),
        {"XDG_CONFIG_HOME": str(old.parent)},
        {"XDG_CONFIG_HOME": "relative"},
    )
    jev = Jev(0.9)
    for environ in homes:
        path = waiting(state)
        done = worker.worked(path, environ, NOW, jev.asker())
        assert (done.queued, done.why) == (False, "the machine says no to the queue")
        assert not path.exists()
    assert jev.sent == []
    assert not (state / queue.QUEUE).exists()


def test_the_repositorys_own_yes_sends_nothing(tmp_path: Path) -> None:
    settings = '[branch]\nbase = "main"\n[corrections]\ncollect = true\n'
    where = workspace(tmp_path / "repo", settings=settings)
    jev = Jev(0.9)
    done = worker.worked(
        waiting(where.state), home(tmp_path / "config", None), NOW, jev.asker()
    )
    assert done.queued is False
    assert jev.sent == []
    refused = refusal(lem("corrections", "list", cwd=where.checkout))
    assert "corrections" in refused["why"]


def test_a_waiting_correction_is_discarded_when_the_team_file_is_gone(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path / "repo")
    path = waiting(where.state)
    (where.lem / "settings.toml").unlink()
    jev = Jev(0.99)
    worked = worker.worked(path, home(tmp_path / "config"), NOW, jev.asker())
    assert not worked.queued
    assert not jev.sent
    assert not path.exists()
    assert not (where.state / queue.QUEUE).exists()


@pytest.mark.parametrize("team_exists", [False, True])
def test_the_worker_checks_the_origin_worktree_before_it_sends(
    tmp_path: Path, *, team_exists: bool
) -> None:
    where = workspace(tmp_path / "repo")
    gitdir = where.checkout / ".git" / "worktrees" / "older"
    gitdir.mkdir(parents=True)
    (gitdir / "commondir").write_text("../..\n")
    older = tmp_path / "older"
    (older / "sub").mkdir(parents=True)
    (older / ".git").write_text(f"gitdir: {gitdir}\n")
    (older / ".lem").mkdir()
    team = older / ".lem" / "settings.toml"
    team.write_text("")
    path = waiting(where.state)
    path.write_bytes(handoff.correction("c1", str(older / "sub"), PROMPT, ""))
    if not team_exists:
        team.unlink()

    jev = Jev(0.99)
    done = worker.worked(path, home(tmp_path / "config"), NOW, jev.asker())
    assert done.queued is team_exists
    assert bool(jev.sent) is team_exists
    assert not path.exists()


@pytest.mark.parametrize(
    ("override", "elapsed", "timeout"), [(None, 30, 120.0), ("180", 150, 180.0)]
)
def test_a_slow_correction_uses_the_jev_timeout_and_keeps_its_lesson(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: str | None,
    elapsed: int,
    timeout: float,
) -> None:
    state = workspace(tmp_path / "repo").state
    environ = {**home(tmp_path / "config"), "JEV_API_KEY": "stand-in"}
    if override is not None:
        environ["JEV_TIMEOUT"] = override
    jev = Jev(0.9)
    ticks = iter((0, elapsed))
    monkeypatch.setattr(
        judge_jev_ask, "time", SimpleNamespace(monotonic=lambda: next(ticks))
    )

    def send(request: httpx.Request) -> httpx.Response:
        assert request.extensions["timeout"]["read"] == timeout
        return jev(request)

    bound = question.asker_of(environ)
    assert isinstance(bound, judge_jev_ask.Asker)
    asker = replace(bound, transport=httpx.MockTransport(send))
    done = worker.worked(waiting(state), environ, NOW, asker)
    assert (done.queued, done.p_lesson) == (True, 0.9)
    assert len(queue.lines(state / queue.QUEUE, Correction)) == 1


def test_the_correction_command_uses_the_review_types_and_choices() -> None:
    annotations = inspect.get_annotations(record_command.Call, eval_str=True)
    assert annotations["decision"] is reviewing.Decision
    assert annotations["verdict"] is reviewing.Verdict
    params = {
        param.name: param.type.choices
        for param in record_command.COMMAND.params
        if isinstance(param.type, click.Choice)
    }
    assert params == {
        "decision": choice(reviewing.Decision).choices,
        "verdict": choice(reviewing.Verdict).choices,
    }


def test_a_file_outside_the_waiting_folder_is_neither_read_nor_removed(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path / "repo").state
    stray = state / "notes.json"
    stray.write_text("{}")
    with pytest.raises(Refusal) as caught:
        worker.worked(stray, home(tmp_path / "config"), NOW, Jev(0.9).asker())
    assert caught.value.code == "not-waiting"
    assert stray.is_file()


@pytest.mark.parametrize("redirected", [False, True])
def test_the_worker_refuses_waiting_files_outside_the_workspace_queue(
    tmp_path: Path, *, redirected: bool
) -> None:
    where = workspace(tmp_path / "repo")
    archive = where.lem / "archive"
    archive.mkdir()
    stray = waiting(archive)
    path = stray
    if redirected:
        (where.state / queue.WAITING).symlink_to(stray.parent, target_is_directory=True)
        path = where.state / queue.WAITING / stray.name
    jev = Jev(0.9)
    with pytest.raises(Refusal) as caught:
        worker.worked(path, home(tmp_path / "config"), NOW, jev.asker())
    assert caught.value.code == "not-waiting"
    assert stray.is_file()
    assert not jev.sent


def test_one_sentence_from_two_sessions_is_one_group_most_sessions_first(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    queued(
        where.state,
        entry("Run the checks first.", "s1", "2026-11-24T09:00:00Z"),
        entry("Run the  checks\nfirst.", "s2", "2026-11-25T09:00:00Z"),
        entry("Ask before you push.", "s3", "2026-11-23T09:00:00Z"),
    )
    found = result(lem("corrections", "list", cwd=tmp_path))
    assert found["collect"] is False
    assert [(one["entries"], one["sessions"]) for one in found["groups"]] == [
        (2, 2),
        (1, 1),
    ]
    first = found["groups"][0]
    assert first["id"] == groups.group_id("Run the checks first.")
    assert first["days"] == ["2026-11-24", "2026-11-25"]
    assert found["entries"] == 3
    shown = rows(lem("corrections", "show", first["id"], cwd=tmp_path))
    assert [one["session"] for one in shown] == ["s1", "s2"]
    assert (
        refusal(lem("corrections", "show", "nogroup", cwd=tmp_path))["code"]
        == "no-group"
    )


def test_two_messages_of_one_second_in_one_session_are_two_entries(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    queued(
        where.state,
        entry("Say what is next.", "s1", "2026-11-24T09:00:00Z"),
        entry("Say what is next.", "s1", "2026-11-24T09:00:00Z"),
        entry("Keep it short.", "s1", "2026-11-24T09:00:00Z"),
    )
    gid = groups.group_id("Keep it short.")
    recorded = result(
        lem(
            "corrections",
            "record",
            gid,
            "--decision",
            "not_lesson",
            "--verdict",
            "unasked",
            cwd=tmp_path,
        )
    )
    assert recorded == {
        "group": gid,
        "entries": 1,
        "decision": "not_lesson",
        "verdict": "unasked",
    }
    left = result(lem("corrections", "list", cwd=tmp_path))
    assert [(one["entries"], one["sessions"]) for one in left["groups"]] == [(2, 1)]


def test_a_recorded_group_leaves_the_list_and_lessons_gives_its_sentence_and_target(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    queued(
        where.state,
        entry("Run the checks first.", "s1", "2026-11-24T09:00:00Z"),
        entry("Run the checks first.", "s2", "2026-11-25T09:00:00Z"),
    )
    gid = groups.group_id("Run the checks first.")
    lesson = "Run the project's checks before a pull request (retro of 2026-11-25 #1)"
    words = ("--decision", "lesson", "--verdict", "proposed", "--target", "AGENTS.md")
    result(lem("corrections", "record", gid, *words, "--lesson", lesson, cwd=tmp_path))
    assert result(lem("corrections", "list", cwd=tmp_path))["groups"] == []
    assert rows(lem("corrections", "lessons", cwd=tmp_path)) == [
        {
            "lesson": lesson,
            "target": "AGENTS.md",
            "verdict": "proposed",
            "entries": 2,
            "days": ["2026-11-24", "2026-11-25"],
        }
    ]


def test_a_lesson_without_its_sentence_or_its_file_and_an_unknown_group_are_refused(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    queued(where.state, entry("Run the checks first.", "s1", "2026-11-24T09:00:00Z"))
    gid = groups.group_id("Run the checks first.")
    lesson = ("--decision", "lesson", "--verdict", "accepted")

    def code(*words: str) -> str:
        return refusal(lem("corrections", "record", *words, cwd=tmp_path))["code"]

    assert code(gid, *lesson, "--target", "AGENTS.md") == "lesson-words"
    assert code(gid, *lesson, "--lesson", "Run them.") == "lesson-target"
    assert (
        code("nogroup", "--decision", "not_lesson", "--verdict", "unasked")
        == "no-group"
    )
    assert not (where.state / queue.REVIEWS).exists()


def test_a_cut_off_line_and_a_line_that_is_not_utf8_are_named_and_bad_settings_stop_list(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    queued(where.state, entry("Run the checks first.", "s1", "2026-11-24T09:00:00Z"))
    path = where.state / queue.QUEUE
    with path.open("ab") as stream:
        stream.write(b'{"at": "2026-11-24T09:0')
    cut = refusal(lem("corrections", "list", cwd=tmp_path))
    assert (cut["code"], f"{path}:2" in cut["why"]) == ("queue-line", True)
    path.write_bytes(b"\xff\xfe\n")
    assert f"{path}:1" in refusal(lem("corrections", "list", cwd=tmp_path))["why"]
    (tmp_path / ".lem" / "settings.toml").write_text("[branch")
    assert refusal(lem("corrections", "list", cwd=tmp_path))["code"] == "settings-toml"


def test_the_switch_is_the_machines_written_by_settings_set_and_shown_with_its_file(
    tmp_path: Path,
) -> None:
    workspace(tmp_path)
    machine = Path(
        home(tmp_path / "config", "[load]\nstart = 12.0\n")["XDG_CONFIG_HOME"]
    )
    environ = {**dict(__import__("os").environ), "XDG_CONFIG_HOME": str(machine)}
    shown = result(lem("settings", "show", cwd=tmp_path, env=environ))
    assert "corrections" in json.dumps(shown)
    result(
        lem(
            "settings",
            "set",
            "corrections.collect",
            "yes",
            "--machine",
            cwd=tmp_path,
            env=environ,
        )
    )
    text = (machine / "lem" / "machine.toml").read_text()
    assert "start = 12.0" in text
    assert "collect = true" in text
    assert (
        result(lem("corrections", "list", cwd=tmp_path, env=environ))["collect"] is True
    )
    assert "collect" not in lem("corrections", "--help", cwd=tmp_path).stdout


def imported(path: Path) -> set[str]:
    """The modules a file imports."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_the_hooks_reach_no_writer_of_lems_home(tmp_path: Path) -> None:
    lems = {
        name
        for path in HOOKS.glob("*.py")
        for name in imported(path)
        if name.split(".")[0] == "lem"
    }
    assert lems <= {"lem.hooks"} | {
        name for name in lems if name.startswith("lem.hooks.")
    }
    assert not any(name.startswith(("lem.settings", "lem.store")) for name in lems)
    assert tmp_path.is_dir()


def test_the_corrections_waiting_file_and_the_queue_hold_the_same_record(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path / "repo").state
    path = waiting(state, session="c9")
    body: Callable[[], bytes] = path.read_bytes
    correction = msgspec.json.decode(body(), type=Correction)
    worker.worked(path, home(tmp_path / "config"), NOW, Jev(0.5).asker())
    (one,) = queue.lines(state / queue.QUEUE, Correction)
    assert msgspec.structs.replace(one, p_lesson=None) == correction
