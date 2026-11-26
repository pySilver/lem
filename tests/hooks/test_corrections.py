"""The `corrections` hook: on the machine's yes, in a repository that uses Lem, the owner's message
is claimed for one judgment, written as one correction (`records.corrections.Correction`, the keys
msgspec writes) into the queue's folder of the state, and handed to `lem corrections worker PATH`,
started detached. A hook registered twice judges each message once. With no yes, in a folder of
Lem 0.3, or from an app that cannot start its worker, it writes nothing.

The worker here is the stand-in `lem` of `claude_code.stand_in`: it writes down its call and the
correction it was given.
"""

import json
import os
import stat
import time
from pathlib import Path

import msgspec

from hooks.claude_code import (
    calls_of,
    files_of,
    hooked,
    launched,
    old_workspace,
    stand_in,
    workspace,
)
from lem.hooks import claims
from lem.kernel import folders
from lem.records.corrections import Correction

PROMPT = "never push without asking"
# The agent's newest text holds a line separator of Unicode, which is no line end of the
# transcript.
NEWEST = "I pushed the branch.\u2028Next: the review."


def yes_home(folder: Path) -> str:
    """A home folder of this Lem whose machine says yes to the queue; its XDG_CONFIG_HOME."""
    home = folder / "lem"
    home.mkdir(parents=True)
    (home / folders.MARKER).write_bytes(folders.FORM)
    (home / "machine.toml").write_text("[corrections]\ncollect = true\n")
    return str(folder)


def transcript(folder: Path) -> Path:
    """A Claude Code transcript whose agent spoke twice, the newest text last."""
    lines = [
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "First."}]},
        },
        {"type": "user", "message": {"content": "go on"}},
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": NEWEST},
                    {"type": "tool_use", "name": "Bash"},
                ]
            },
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "tool_use", "name": "Bash"}]},
        },
    ]
    path = folder / "c1.jsonl"
    path.write_text("".join(f"{json.dumps(line)}\n" for line in lines))
    return path


def typed(
    cwd: Path, session: str = "c1", prompt: str = PROMPT, talk: str = ""
) -> bytes:
    """A UserPromptSubmit event of the owner's message `prompt`."""
    event = {
        "hook_event_name": "UserPromptSubmit",
        "prompt": prompt,
        "cwd": str(cwd),
        "session_id": session,
        "transcript_path": talk,
    }
    return json.dumps(event).encode()


def worker_calls(lines: list[str]) -> list[str]:
    """The calls of the worker among the lines the stand-in wrote."""
    return [line for line in lines if line[:1].isalpha()]


def test_a_message_is_handed_to_the_worker_as_one_correction(tmp_path: Path) -> None:
    hook, calls = stand_in(tmp_path / "app")
    workspace(tmp_path / "repo")
    state = tmp_path / "repo" / ".lem" / "state"
    talk = transcript(tmp_path)
    ran = hooked(
        "corrections",
        typed(tmp_path / "repo", talk=str(talk)),
        LEM_HOOK_BIN=str(hook),
        XDG_CONFIG_HOME=yes_home(tmp_path / "config"),
    )
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    lines = calls_of(calls, 1)
    (call,) = worker_calls(lines)
    words, _, path = call.rpartition(" ")
    assert words == "corrections worker"
    assert Path(path).parent == state / "corrections-waiting"
    assert stat.S_IMODE(Path(path).stat().st_mode) == 0o600
    body = Path(path).read_bytes()
    correction = msgspec.json.decode(body, type=Correction)
    assert (correction.session, correction.owner, correction.previous) == (
        "c1",
        PROMPT,
        NEWEST,
    )
    assert correction.cwd == str((tmp_path / "repo").resolve())
    assert json.loads(msgspec.json.encode(correction)) == json.loads(body)


def test_the_hook_requires_a_team_file_in_the_worktree_where_the_owner_typed(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app")
    repo = tmp_path / "repo"
    workspace(repo)
    gitdir = repo / ".git" / "worktrees" / "older"
    gitdir.mkdir(parents=True)
    (gitdir / "commondir").write_text("../..\n")
    older = tmp_path / "older"
    (older / "sub").mkdir(parents=True)
    (older / ".git").write_text(f"gitdir: {gitdir}\n")
    state = repo / ".lem" / "state"
    environ = {
        "LEM_HOOK_BIN": str(hook),
        "XDG_CONFIG_HOME": yes_home(tmp_path / "config"),
    }

    ran = hooked("corrections", typed(older / "sub"), **environ)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert not (state / "corrections-waiting").exists()
    assert not calls.exists()

    (older / ".lem").mkdir()
    (older / ".lem" / "settings.toml").write_text("")
    hooked("corrections", typed(older / "sub"), **environ)
    (call,) = worker_calls(calls_of(calls, 1))
    path = Path(call.rpartition(" ")[2])
    assert path.parent == state / "corrections-waiting"
    assert msgspec.json.decode(path.read_bytes(), type=Correction).cwd == str(
        (older / "sub").resolve()
    )


def test_a_hook_registered_twice_judges_each_message_once(tmp_path: Path) -> None:
    hook, calls = stand_in(tmp_path / "app")
    workspace(tmp_path / "repo")
    home = yes_home(tmp_path / "config")
    copies = [
        launched(
            "corrections",
            typed(tmp_path / "repo"),
            LEM_HOOK_BIN=str(hook),
            XDG_CONFIG_HOME=home,
        )
        for _ in range(2)
    ]
    assert [copy.wait(timeout=30) for copy in copies] == [0, 0]
    # the same words in another session are another message
    hooked(
        "corrections",
        typed(tmp_path / "repo", session="c2"),
        LEM_HOOK_BIN=str(hook),
        XDG_CONFIG_HOME=home,
    )
    assert len(worker_calls(calls_of(calls, 2))) == 2
    time.sleep(0.5)
    assert len(worker_calls(calls.read_text().splitlines())) == 2
    waiting = tmp_path / "repo" / ".lem" / "state" / "corrections-waiting"
    sessions = sorted(
        json.loads(path.read_bytes())["session"] for path in waiting.iterdir()
    )
    assert sessions == ["c1", "c2"]


def test_a_claim_older_than_its_time_gives_way(tmp_path: Path) -> None:
    hook, calls = stand_in(tmp_path / "app")
    workspace(tmp_path / "repo")
    held = tmp_path / "repo" / ".lem" / "state" / claims.CLAIMS
    held.mkdir()
    old = held / claims.name_of("c1", PROMPT)
    old.touch()
    then = time.time() - claims.CLAIM_SECONDS - 1
    os.utime(old, (then, then))
    hooked(
        "corrections",
        typed(tmp_path / "repo"),
        LEM_HOOK_BIN=str(hook),
        XDG_CONFIG_HOME=yes_home(tmp_path / "config"),
    )
    assert len(worker_calls(calls_of(calls, 1))) == 1
    assert old.stat().st_mtime > then


def test_three_hook_calls_for_one_message_hand_it_on_once(tmp_path: Path) -> None:
    hook, calls = stand_in(tmp_path / "app")
    repo = tmp_path / "repo"
    workspace(repo)
    home = yes_home(tmp_path / "config")
    copies = [
        launched(
            "corrections",
            typed(repo),
            LEM_HOOK_BIN=str(hook),
            XDG_CONFIG_HOME=home,
        )
        for _ in range(3)
    ]
    assert [copy.wait(timeout=30) for copy in copies] == [0, 0, 0]
    assert len(worker_calls(calls_of(calls, 1))) == 1
    waiting = repo / ".lem" / "state" / "corrections-waiting"
    (path,) = waiting.glob("*.json")
    correction = msgspec.json.decode(path.read_bytes(), type=Correction)
    assert (correction.session, correction.owner) == ("c1", PROMPT)


def test_nothing_is_handed_on_without_the_machines_yes_or_where_lem_0_3_keeps_its_files(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app")
    repo = tmp_path / "repo"
    workspace(repo)
    old = old_workspace(tmp_path / "old")
    plain = tmp_path / "plain"
    (plain / ".git").mkdir(parents=True)
    yes = yes_home(tmp_path / "yes")
    no = tmp_path / "no" / "lem"
    no.mkdir(parents=True)
    (no / folders.MARKER).write_bytes(folders.FORM)
    (no / "machine.toml").write_text("[corrections]\ncollect = false\n")
    old_home = tmp_path / "old-home" / "lem"
    old_home.mkdir(parents=True)
    (old_home / "machine.toml").write_text("[corrections]\ncollect = true\n")
    before = files_of(tmp_path)
    cases = (
        (typed(repo), str(tmp_path / "none")),
        (typed(repo), str(no.parent)),
        (typed(repo), str(old_home.parent)),
        (typed(repo), "relative"),
        (typed(old), yes),
        (typed(plain), yes),
        (typed(repo, prompt="/lem status"), yes),
        (typed(repo, prompt="<command-name>/cost</command-name>"), yes),
        (typed(repo, prompt="  "), yes),
    )
    for event, home in cases:
        ran = hooked("corrections", event, LEM_HOOK_BIN=str(hook), XDG_CONFIG_HOME=home)
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), (event, home)
    assert files_of(tmp_path) == before
    # the one message that is handed on comes last: a hand-off above would be in the calls too
    hooked("corrections", typed(repo), LEM_HOOK_BIN=str(hook), XDG_CONFIG_HOME=yes)
    assert len(worker_calls(calls_of(calls, 1))) == 1
    time.sleep(0.5)
    assert len(worker_calls(calls.read_text().splitlines())) == 1


def test_the_repositorys_team_and_local_yes_do_not_start_the_hook_worker(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app")
    repo = tmp_path / "repo"
    workspace(repo)
    for name in ("settings.toml", "settings.local.toml"):
        (repo / ".lem" / name).write_text("[corrections]\ncollect = true\n")
    config = tmp_path / "config"
    home = config / "lem"
    home.mkdir(parents=True)
    (home / folders.MARKER).write_bytes(folders.FORM)
    (home / "machine.toml").write_text("")

    ran = hooked(
        "corrections", typed(repo), LEM_HOOK_BIN=str(hook), XDG_CONFIG_HOME=str(config)
    )

    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert not (repo / ".lem" / "state" / "corrections-waiting").exists()
    assert not calls.exists()


def test_an_empty_state_folder_is_marked_and_takes_the_message(tmp_path: Path) -> None:
    hook, calls = stand_in(tmp_path / "app")
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".lem" / "state").mkdir(parents=True)
    (repo / ".lem" / "settings.toml").write_text("")
    (repo / ".lem" / "state" / ".gitignore").write_text("*\n")
    hooked(
        "corrections",
        typed(repo),
        LEM_HOOK_BIN=str(hook),
        XDG_CONFIG_HOME=yes_home(tmp_path / "config"),
    )
    assert (repo / ".lem" / "state" / folders.MARKER).read_bytes() == folders.FORM
    assert len(worker_calls(calls_of(calls, 1))) == 1


def test_a_worker_that_cannot_start_leaves_no_words_and_no_claim(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app")
    # a `lem` that may be run but does not start: no line of a shell, no format of a program
    (tmp_path / "app" / "bin" / "lem").write_bytes(b"\x00\x01 not a program\n")
    workspace(tmp_path / "repo")
    state = tmp_path / "repo" / ".lem" / "state"
    ran = hooked(
        "corrections",
        typed(tmp_path / "repo"),
        LEM_HOOK_BIN=str(hook),
        XDG_CONFIG_HOME=yes_home(tmp_path / "config"),
    )
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert list((state / "corrections-waiting").iterdir()) == []
    assert list((state / claims.CLAIMS).iterdir()) == []
    (line,) = (state / "corrections.log").read_text().splitlines()
    assert json.loads(line)["error"] == "the hook could not hand the message on"
    assert PROMPT not in (state / "corrections.log").read_text()
    assert not calls.exists()


def test_with_no_command_of_the_app_nothing_is_claimed_or_written(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app")
    (tmp_path / "app" / "bin" / "lem").unlink()
    workspace(tmp_path / "repo")
    home = yes_home(tmp_path / "config")
    before = files_of(tmp_path)
    ran = hooked(
        "corrections",
        typed(tmp_path / "repo"),
        LEM_HOOK_BIN=str(hook),
        XDG_CONFIG_HOME=home,
    )
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert files_of(tmp_path) == before
    assert not calls.exists()


def test_a_machine_file_main_would_refuse_says_no(tmp_path: Path) -> None:
    hook, calls = stand_in(tmp_path / "app")
    workspace(tmp_path / "repo")
    for text in (
        "[corrections]\ncollect = true\nsend = true\n",
        "[corrections]\ncollect = true\n[nonsense]\nx = 1\n",
    ):
        home = tmp_path / "config" / text.split("\n")[-2].replace(" ", "")[:8] / "lem"
        home.mkdir(parents=True)
        (home / folders.MARKER).write_bytes(folders.FORM)
        (home / "machine.toml").write_text(text)
        hooked(
            "corrections",
            typed(tmp_path / "repo"),
            LEM_HOOK_BIN=str(hook),
            XDG_CONFIG_HOME=str(home.parent),
        )
    time.sleep(0.5)
    assert not worker_calls(calls.read_text().splitlines() if calls.exists() else [])
    assert not (tmp_path / "repo" / ".lem" / "state" / "corrections-waiting").exists()


def test_a_linked_folder_of_the_queue_takes_no_words_of_the_owner(
    tmp_path: Path,
) -> None:
    hook, calls = stand_in(tmp_path / "app")
    workspace(tmp_path / "repo")
    state = tmp_path / "repo" / ".lem" / "state"
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "waiting").mkdir(parents=True)
    (elsewhere / "claims").mkdir()
    (state / "corrections-waiting").symlink_to(elsewhere / "waiting")
    (state / "corrections-claims").symlink_to(elsewhere / "claims")
    ran = hooked(
        "corrections",
        typed(tmp_path / "repo"),
        LEM_HOOK_BIN=str(hook),
        XDG_CONFIG_HOME=yes_home(tmp_path / "config"),
    )
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    time.sleep(0.5)
    assert list((elsewhere / "waiting").iterdir()) == []
    assert list((elsewhere / "claims").iterdir()) == []
    assert not worker_calls(calls.read_text().splitlines() if calls.exists() else [])
