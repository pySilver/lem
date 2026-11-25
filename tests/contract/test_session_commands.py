"""A task's session through the command `lem` and the plugin's hook, on the stand-in for
`agtermctl`: open with no focus, the `session-start` hook of the session it
started, its signs in `lem session list`, and its close."""

import json
import os
import subprocess
import sys
from pathlib import Path

from contract.agterm_standin import install
from fakes.command import lem
from fakes.records import record
from lem.kernel import paths
from lem.store import places, tasks

SLUG = "gift-note"
ROOT = Path(__file__).resolve().parents[2]
MINE = {"id": "S-MINE", "name": "main", "workspace": "W-MINE"}


def test_a_session_opens_starts_shows_its_signs_and_closes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".lem").mkdir()
    state = places.state_of(repo)
    tasks.create(state, record(SLUG, status="shaping"))
    standin = install(tmp_path / "agterm", [MINE])
    # only the stand-ins and the system's folders on the PATH, and no agterm of the owner's
    inherited = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("AGTERM_", "CLAUDE_"))
    }
    env = {**inherited, **standin.environ(AGTERM_SESSION_ID="S-MINE")}

    first = lem("session", "open", SLUG, "--why", "new", cwd=repo, env=env)
    assert first.code == 0, first.stdout
    opened = first.envelope()
    assert opened["result"] == {
        "task": SLUG,
        "session": "S-1",
        "name": SLUG,
        "phase": "shape",
        "already": False,
        "workspace": "W-MINE",
    }
    assert opened["next"] == {
        "do": "run",
        "command": f"lem session wait {SLUG} --first-line",
    }
    assert opened["say"] == (
        f"{SLUG} is open in its own session `{SLUG}`, phase shape, at the end of the "
        "workspace"
    )
    command = standin.sessions()[-1]["command"]
    brief = state / "tasks" / SLUG / "session.md"
    assert isinstance(command, str)
    assert f"LEM_TASK={SLUG} CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude " in command
    assert f"--model opus --effort high --plugin-dir {paths.root()} " in command
    assert f"Read {brief} and follow it." in command
    again = lem("session", "open", SLUG, cwd=repo, env=env).result()
    assert isinstance(again, dict)
    assert (again["session"], again["already"]) == ("S-1", True)

    # Claude Code's folder: the transcript, and the process file of a live pid (this test's
    # own), so that the session's signs read
    transcript = tmp_path / "claude" / "projects" / "repo" / "c1.jsonl"
    transcript.parent.mkdir(parents=True)
    process = tmp_path / "claude" / "sessions" / f"{os.getpid()}.json"
    process.parent.mkdir()
    process.write_text(json.dumps({"pid": os.getpid(), "sessionId": "c1"}))
    lines = [
        {"type": "user", "message": {"content": f"Read {brief} and follow it."}},
        {
            "type": "assistant",
            "timestamp": "2026-11-25T10:05:00Z",
            "message": {"stop_reason": "end_turn", "content": []},
        },
    ]
    transcript.write_text("".join(f"{json.dumps(line)}\n" for line in lines))
    event = {
        "session_id": "c1",
        "transcript_path": str(transcript),
        "source": "startup",
        "cwd": str(repo),
        "hook_event_name": "SessionStart",
    }
    hook_env = {
        **env,
        "CLAUDE_PLUGIN_ROOT": str(ROOT),
        "LEM_HOOK_BIN": str(Path(sys.prefix) / "bin" / "lem-hook"),
        "LEM_TASK": SLUG,
        "AGTERM_SESSION_ID": "S-1",
    }
    subprocess.run(
        ["/bin/sh", f"{ROOT}/hooks/run", "session-start"],
        cwd=tmp_path,
        input=json.dumps(event).encode(),
        env=hook_env,
        check=True,
        timeout=30,
    )
    listed = lem("session", "list", cwd=repo, env=env).result()
    assert isinstance(listed, list)
    assert [
        (entry["task"], entry["live"], entry["phase"], entry["turn"], entry["sign"])
        for entry in listed
    ] == [(SLUG, True, "shape", "ended", "2026-11-25T10:05:00Z")]

    closed = lem("session", "close", SLUG, "--why", "ended", cwd=repo, env=env)
    assert closed.result() == {
        "task": SLUG,
        "session": "S-1",
        "why": "ended",
        "closed": True,
        "woken": False,
    }
    assert [node["id"] for node in standin.sessions()] == ["S-MINE"]
    after = lem("session", "list", cwd=repo, env=env).result()
    assert isinstance(after, list)
    assert [(entry["live"], entry["closed"]) for entry in after] == [(False, "ended")]
    assert not [call for call in standin.calls() if "select" in call]


def test_the_commands_refuse_a_state_folder_of_lem_0_3_and_change_nothing(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".lem" / "state" / "tasks" / SLUG).mkdir(parents=True)
    (repo / ".lem" / "state" / "events.jsonl").write_text('{"event": "task.state"}\n')
    (repo / ".lem" / "state" / "tasks" / SLUG / "state.md").write_text("building\n")
    standin = install(tmp_path / "agterm", [MINE])
    env = {
        **{
            name: value
            for name, value in os.environ.items()
            if not name.startswith(("AGTERM_", "CLAUDE_"))
        },
        **standin.environ(AGTERM_SESSION_ID="S-MINE"),
    }
    before = {
        str(path): path.read_bytes() for path in repo.rglob("*") if path.is_file()
    }
    for words in (
        ("open", SLUG, "--why", "new"),
        ("next", SLUG),
        ("close", SLUG, "--why", "ended"),
        ("list",),
    ):
        ran = lem("session", *words, cwd=repo, env=env)
        assert ran.code == 1, (words, ran.stdout, ran.stderr)
        refusal = ran.envelope()["refusal"]
        assert isinstance(refusal, dict)
        assert refusal["code"] == "old-state", words
    after = {str(path): path.read_bytes() for path in repo.rglob("*") if path.is_file()}
    assert after == before
    assert not [call for call in standin.calls() if call[:2] == ["session", "new"]]


def test_the_plan_talks_pair_reads_the_folder_the_launch_line_names(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".lem").mkdir()
    places.state_of(repo)
    config = tmp_path / "claude-config"
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(config)}
    given = lem("--repo", str(repo), "session", "plugin-dir", cwd=tmp_path, env=env)
    assert given.result() == {"plugin_dir": str(paths.root())}
    listed = {"plugins": {"lem@lem": [{"scope": "user"}]}}
    (config / "plugins").mkdir(parents=True)
    (config / "plugins" / "installed_plugins.json").write_text(json.dumps(listed))
    installed = lem("--repo", str(repo), "session", "plugin-dir", cwd=tmp_path, env=env)
    assert installed.result() == {"plugin_dir": None}
