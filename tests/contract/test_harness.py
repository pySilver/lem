"""The Claude Code adapter against the `Harness` contract, and each of its rules: the launch line
and the plugin's folder, the transcripts that count for a task, the signs of one transcript and
the tokens of a task.

Every case reads transcripts, process files and Claude Code's own files that it writes itself, a
process table it gives the adapter, and a stand-in script named `claude`: never the owner's
Claude Code. The one case on the machine's process table reads the test's own processes only.
The forms are the ones `signs.py` and `tokens.py` on `main` read on the owner's Mac (Claude Code
2.1.294 to 2.1.330, 2026-11-21 to 23): a fork of one task's session logged under another
(6fe214ec, 2026-11-22), a reply written as one record a block.
"""

import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

from contract.suites.outside import HarnessContract
from lem.adapters import claude_processes, claude_transcript, harness_claude
from lem.kernel.errors import Refusal
from lem.ports.harness import Missing, Seat, Signs, Tokens, Transcript
from lem.ports.place import Place
from lem.records.sessions import SessionLine
from lem.store import guard, sessions

AT = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)
SLUG = "merge-leaves-board-lock"
# The task whose background host the fork of SLUG's session ran in (6fe214ec, 2026-11-22).
HOST = "board-card-search"
PID = 63868
SNAPSHOT_LINE = (
    "/bin/zsh -c source /Users/someone/.claude/shell-snapshots/snapshot-zsh-1795367130285-"
    "3ryanb.sh 2>/dev/null || true && eval 'lem land check'"
)


@dataclass
class FakeTable:
    """A process table the test gives: the children's command lines of each live pid."""

    rows: dict[int, tuple[str, ...]] = field(default_factory=dict)

    def children(self, pid: int) -> tuple[str, ...] | None:
        return self.rows.get(pid)


class UnreadTable:
    """A process table that does not read."""

    def children(self, pid: int) -> tuple[str, ...] | None:
        return None


def place(checkout: Path, path: str = "/usr/bin:/bin", **environ: str) -> Place:
    """The adapter's place for the workspace `checkout`, with a home of its own for Claude
    Code's files."""
    given = {"PATH": path, "HOME": str(checkout / "user"), **environ}
    return Place(checkout=checkout, home=checkout / "home", environ=given)


def bound(
    checkout: Path,
    table: claude_processes.Table | None = None,
    environ: dict[str, str] | None = None,
) -> harness_claude.ClaudeHarness:
    """The adapter for the workspace `checkout`, with the process table `table` and Claude
    Code's folder of `environ`."""
    return harness_claude.ClaudeHarness(
        place(checkout, **(environ or {})), table or FakeTable({PID: ()})
    )


class TestClaudeHarness(HarnessContract):
    @pytest.fixture(autouse=True)
    def checkout(self, tmp_path: Path) -> None:
        self.folder = tmp_path

    def harness(self) -> harness_claude.ClaudeHarness:
        return harness_claude.bind(place(self.folder))


def write(path: Path, *records: object) -> str:
    """A transcript of `records`, one a line: a text is a line as it is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = (each if isinstance(each, str) else json.dumps(each) for each in records)
    path.write_text("".join(f"{line}\n" for line in lines))
    return str(path)


def prompt(text: object, at: str = "2026-11-25T10:00:00Z", **flags: object) -> dict:
    """A user record of `text`."""
    return {"type": "user", "timestamp": at, "message": {"content": text}, **flags}


def reply(
    reason: str | None = "end_turn",
    *tools: str,
    at: str = "2026-11-25T10:05:00Z",
    **flags: object,
) -> dict:
    """An assistant record that stopped for `reason`, with a call of each of `tools`."""
    parts = [{"type": "tool_use", "name": tool} for tool in tools]
    message = {"stop_reason": reason, "content": parts}
    return {"type": "assistant", "timestamp": at, "message": message, **flags}


def spent(
    message: str, given: int, said: int, read: int = 0, wrote: int = 0
) -> dict[str, object]:
    """An assistant record of the reply `message` with its usage."""
    usage = {
        "input_tokens": given,
        "output_tokens": said,
        "cache_read_input_tokens": read,
        "cache_creation_input_tokens": wrote,
        "output_tokens_details": {"thinking_tokens": 1},
        "service_tier": "standard",
    }
    return {"type": "assistant", "message": {"id": message, "usage": usage}}


def launch(state: Path, slug: str) -> str:
    """The first prompt the launch line gives the session of the task `slug`."""
    return f"Read {state}/tasks/{slug}/session.md and follow it."


def logged(state: Path, slug: str, path: str, claude: str, minute: int) -> None:
    """The line `session-start` appends for a session of `slug`, started at `minute`."""
    guard.writable(state)
    folder = state / "tasks" / slug
    folder.mkdir(parents=True, exist_ok=True)
    at = AT.replace(minute=minute)
    line = SessionLine(
        at=at, source="startup", claude=claude, transcript=path, task=slug
    )
    sessions.append(folder, line)


# ---- the launch line and the plugin's folder ----


def launch_line(
    brief: Path, seat: Seat, plugin: Path | None, environ: dict[str, str] | None = None
) -> list[str]:
    """The words a login shell reads in the launch line."""
    harness = bound(brief.parent, environ=environ)
    said = harness.launch(seat, str(brief), brief.parent, plugin)
    return shlex.split(said)


def test_the_launch_line_names_the_task_the_compaction_the_seat_the_plugin_and_the_brief(
    tmp_path: Path,
) -> None:
    brief = (
        tmp_path / "my repo" / ".lem" / "state" / "tasks" / "gift-note" / "session.md"
    )
    seat = Seat(agent="claude", model="opus[1m]", effort="high")
    plugin = tmp_path / "Lem's data"
    assert launch_line(brief, seat, plugin) == [
        "LEM_TASK=gift-note",
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000",
        "claude",
        "--model",
        "opus[1m]",
        "--effort",
        "high",
        "--plugin-dir",
        str(plugin),
        f"Read {brief} and follow it.",
    ]
    said = bound(tmp_path).launch(Seat(agent="claude"), str(brief), tmp_path, None)
    assert said == (
        "LEM_TASK=gift-note CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude "
        f'"Read {brief} and follow it."'
    )
    with pytest.raises(Refusal, match="backslash or a line break"):
        launch_line(tmp_path / "a\\b" / "x" / "session.md", Seat(agent="claude"), None)


def machine(tmp_path: Path, text: str) -> Path:
    """The brief of a task in the workspace `tmp_path`, whose machine's settings are `text`."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    (home / "machine.toml").write_text(text)
    return tmp_path / ".lem" / "state" / "tasks" / "gift-note" / "session.md"


def compaction_word(tmp_path: Path) -> list[str]:
    """The compaction word of the launch line of the workspace `tmp_path`."""
    brief = tmp_path / ".lem" / "state" / "tasks" / "gift-note" / "session.md"
    harness = bound(tmp_path)
    words = shlex.split(
        harness.launch(Seat(agent="claude"), str(brief), tmp_path, None)
    )
    return [word for word in words if word.startswith("CLAUDE_CODE_AUTO_COMPACT")]


def test_the_compaction_number_is_the_machines_and_zero_leaves_it_out(
    tmp_path: Path,
) -> None:
    machine(tmp_path, "[load]\nstart = 40\n")
    assert compaction_word(tmp_path) == ["CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000"]
    machine(tmp_path, "[handoff]\ntokens = 250_000\n")
    assert compaction_word(tmp_path) == ["CLAUDE_CODE_AUTO_COMPACT_WINDOW=250000"]
    machine(tmp_path, "[handoff]\ntokens = 0\n")
    assert compaction_word(tmp_path) == []


def test_a_compaction_number_claude_code_would_refuse_is_refused(
    tmp_path: Path,
) -> None:
    for text in (
        "[handoff]\ntokens = 99_999\n",
        "[handoff]\ntokens = -1\n",
        "[handoff]\ntokens = true\n",
        "[handoff]\ntokens = 2.5e5\n",
        "[handoff\n",
    ):
        machine(tmp_path, text)
        with pytest.raises(Refusal) as refused:
            compaction_word(tmp_path)
        # the machine's file is read and checked by the settings (`settings.load.machine_of`)
        assert refused.value.code in {"settings", "settings-toml"}, text
        if refused.value.code == "settings":
            assert "0 (Claude Code's own trigger)" in refused.value.fix


def claude_files(
    tmp_path: Path, *installs: dict[str, str], **settings: dict[str, object]
) -> dict[str, str]:
    """Claude Code's folder with the installs of Lem's plugin and the user's settings; the
    environment that names it."""
    folder = tmp_path / "claude-config"
    (folder / "plugins").mkdir(parents=True, exist_ok=True)
    listed = {"version": 2, "plugins": {"lem@lem": list(installs)}}
    (folder / "plugins" / "installed_plugins.json").write_text(json.dumps(listed))
    (folder / "settings.json").write_text(json.dumps(settings))
    return {"CLAUDE_CONFIG_DIR": str(folder)}


def project_settings(checkout: Path, name: str, *, on: bool) -> None:
    """The checkout's settings file `name`, which turns Lem's plugin on or off."""
    folder = checkout / ".claude"
    folder.mkdir(exist_ok=True)
    said = {"enabledPlugins": {"lem@lem": on, "other@market": False}}
    (folder / name).write_text(json.dumps(said))


def test_the_plugin_folder_is_given_only_where_the_project_loads_no_installed_plugin(
    tmp_path: Path,
) -> None:
    checkout, root = tmp_path / "shop", tmp_path / "lem-data"
    checkout.mkdir()
    (tmp_path / "link").symlink_to(checkout)
    assert bound(checkout).plugin_folder(root) == root
    user = claude_files(tmp_path, {"scope": "user"})
    assert bound(checkout, environ=user).plugin_folder(root) is None
    other = claude_files(tmp_path, {"scope": "project", "projectPath": str(tmp_path)})
    assert bound(checkout, environ=other).plugin_folder(root) == root
    here = claude_files(
        tmp_path, {"scope": "local", "projectPath": str(tmp_path / "link")}
    )
    assert bound(checkout, environ=here).plugin_folder(root) is None
    project_settings(checkout, "settings.json", on=False)
    assert bound(checkout, environ=here).plugin_folder(root) == root
    project_settings(checkout, "settings.local.json", on=True)
    assert bound(checkout, environ=here).plugin_folder(root) is None
    off = claude_files(
        tmp_path, {"scope": "managed"}, enabledPlugins={"lem@lem": False}
    )
    assert bound(tmp_path / "elsewhere", environ=off).plugin_folder(root) == root
    (tmp_path / "claude-config" / "plugins" / "installed_plugins.json").write_text("{")
    assert bound(checkout, environ=off).plugin_folder(root) == root


def test_the_launch_line_has_no_plugin_dir_where_the_project_loads_the_installed_plugin(
    tmp_path: Path,
) -> None:
    brief = tmp_path / ".lem" / "state" / "tasks" / "gift-note" / "session.md"
    user = claude_files(tmp_path, {"scope": "user"})
    words = launch_line(brief, Seat(agent="claude"), tmp_path / "lem-data", user)
    assert "--plugin-dir" not in words


def test_claude_is_available_when_it_is_on_the_path(tmp_path: Path) -> None:
    standin = tmp_path / "bin" / "claude"
    standin.parent.mkdir()
    standin.write_text("#!/bin/sh\nexit 0\n")
    standin.chmod(0o755)
    seat = Seat(agent="claude")
    assert bound(tmp_path).available(seat) == Missing(
        error="missing", said="no claude on the PATH"
    )
    on_path = harness_claude.bind(place(tmp_path, f"{standin.parent}:/usr/bin:/bin"))
    assert on_path.available(seat) is None
    assert bound(tmp_path).available(Seat(agent="codex")) is not None


# ---- the transcripts of a task ----


def test_a_transcript_counts_for_the_task_its_first_prompt_names(
    tmp_path: Path,
) -> None:
    state = tmp_path / ".lem" / "state"
    brief = launch(state, "gift-note")
    own = write(tmp_path / "c" / "own.jsonl", {"type": "summary"}, prompt(brief))
    fork = write(tmp_path / "c" / "fork.jsonl", prompt(brief))
    cleared = write(tmp_path / "c" / "cleared.jsonl", prompt("go on with the column"))
    logged(state, "gift-note", own, "c1", 1)
    logged(state, "gift-note", own, "c1", 2)
    logged(state, "board-search", fork, "c2", 3)
    logged(state, "board-search", cleared, "c3", 4)
    logged(state, "gift-note", str(tmp_path / "gone.jsonl"), "c4", 5)
    harness = bound(tmp_path)
    assert [found.claude for found in harness.transcripts("gift-note")] == [
        "c1",
        "c2",
        "c4",
    ]
    assert harness.transcripts("board-search") == (
        Transcript(path=cleared, claude="c3"),
    )


def test_the_first_prompt_reads_past_a_bad_time_and_takes_text_blocks_only(
    tmp_path: Path,
) -> None:
    state = tmp_path / ".lem" / "state"
    brief = launch(state, "gift-note")
    timed = write(
        tmp_path / "c" / "timed.jsonl", prompt(brief, "not a time"), prompt("go on")
    )
    blocks = [{"type": "text", "text": brief}, {"type": "image", "source": {}}]
    pictured = write(tmp_path / "c" / "pictured.jsonl", prompt(blocks))
    logged(state, "board-search", timed, "c1", 1)
    logged(state, "board-search", pictured, "c2", 2)
    harness = bound(tmp_path)
    assert [one.claude for one in harness.transcripts("gift-note")] == ["c1"]
    assert [one.claude for one in harness.transcripts("board-search")] == ["c2"]


# The records Claude Code writes before a session's first prompt, and a meta prompt, as 6fe214ec
# has them.
HEAD = (
    {"type": "ai-title"},
    {"type": "permission-mode"},
    {"type": "queue-operation"},
    prompt("<local-command-caveat>x</local-command-caveat>", isMeta=True),
)


def test_a_fork_logged_under_another_task_counts_for_the_task_its_first_prompt_names_once(
    tmp_path: Path,
) -> None:
    state, projects = tmp_path / ".lem" / "state", tmp_path / "projects" / "-shop"
    search = write(
        projects / "search.jsonl",
        *HEAD,
        prompt(launch(state, HOST)),
        spent("a1", 1, 10),
    )
    merge = write(
        projects / "merge.jsonl",
        *HEAD,
        prompt(launch(state, SLUG)),
        spent("b1", 1, 200),
    )
    # The fork copies its parent's first prompt, and the hook in the host of HOST's pane
    # logged it there.
    fork = write(
        projects / "6fe214ec.jsonl",
        *HEAD,
        prompt(launch(state, SLUG), sessionKind="bg"),
        spent("f1", 1, 3000),
        spent("f1", 1, 3000),
    )
    logged(state, HOST, search, "search", 1)
    logged(state, SLUG, merge, "merge", 2)
    logged(state, HOST, fork, "6fe214ec", 3)
    harness = bound(tmp_path)
    assert [one.path for one in harness.transcripts(HOST)] == [search]
    merged = harness.transcripts(SLUG)
    assert [one.path for one in merged] == [merge, fork]
    assert (harness.tokens(harness.transcripts(HOST)).output, len(merged)) == (10, 2)
    assert harness.tokens(merged) == Tokens(input=2, output=3200, sessions=2)


def test_a_transcript_whose_first_prompt_names_no_task_counts_for_its_lines_task(
    tmp_path: Path,
) -> None:
    state, projects = tmp_path / ".lem" / "state", tmp_path / "projects" / "-shop"
    # The owner's /clear in the pane of gift-note: the new transcript starts with his words.
    cleared = write(
        projects / "cleared.jsonl",
        *HEAD,
        prompt("now make the note shorter"),
        spent("c1", 1, 7),
    )
    # A launch line's path among other words names no task.
    pasted = write(
        projects / "pasted.jsonl",
        prompt(f"look at {launch(state, HOST)} and tell me"),
        spent("p1", 1, 5),
    )
    # Beside them, a fork of HOST logged under gift-note, which counts for none of its.
    fork = write(
        projects / "fork.jsonl",
        prompt(launch(state, HOST), sessionKind="bg"),
        spent("f1", 1, 900),
    )
    logged(state, "gift-note", cleared, "cleared", 1)
    logged(state, "gift-note", fork, "fork", 2)
    logged(state, "gift-note", pasted, "pasted", 3)
    harness = bound(tmp_path)
    mine = harness.transcripts("gift-note")
    assert [one.path for one in mine] == [cleared, pasted]
    assert [one.path for one in harness.transcripts(HOST)] == [fork]
    assert harness.tokens(mine).output == 12


def test_a_transcript_that_is_gone_is_missing_for_its_lines_task_only(
    tmp_path: Path,
) -> None:
    state = tmp_path / ".lem" / "state"
    gone = str(tmp_path / "projects" / "-shop" / "gone.jsonl")
    logged(state, "gift-note", gone, "gone", 1)
    harness = bound(tmp_path)
    mine = harness.transcripts("gift-note")
    assert mine == (Transcript(path=gone, claude="gone"),)
    assert harness.tokens(mine) == Tokens(missing=1)
    assert harness.transcripts(HOST) == ()


def test_a_fork_logged_under_a_task_that_ended_counts_for_the_open_task_its_first_prompt_names(
    tmp_path: Path,
) -> None:
    # The task HOST landed; its sessions file stays when the prune folds its journal (the
    # design's part 3, "Retention"), so the fork it holds still counts for SLUG.
    state, projects = tmp_path / ".lem" / "state", tmp_path / "projects" / "-shop"
    own = write(projects / "search.jsonl", prompt(launch(state, HOST)))
    merge = write(projects / "merge.jsonl", prompt(launch(state, SLUG)))
    fork = write(
        projects / "6fe214ec.jsonl",
        prompt(launch(state, SLUG), sessionKind="bg"),
        spent("f1", 1, 3000),
    )
    logged(state, HOST, own, "search", 1)
    logged(state, HOST, fork, "6fe214ec", 2)
    logged(state, SLUG, merge, "merge", 3)
    harness = bound(tmp_path)
    assert [one.path for one in harness.transcripts(SLUG)] == [fork, merge]
    assert harness.tokens(harness.transcripts(SLUG)).output == 3000
    assert [one.path for one in harness.transcripts(HOST)] == [own]


def test_the_first_prompt_names_a_task_only_when_it_is_a_launch_line_whole(
    tmp_path: Path,
) -> None:
    def named(text: str) -> str | None:
        return claude_transcript.task_named(
            Path(write(tmp_path / "t.jsonl", prompt(text)))
        )

    state = tmp_path / "my shop" / ".lem" / "state"
    assert named(launch(state, SLUG)) == SLUG
    # The launch line of a task that ended names it still: the rule reads no state.
    assert named(launch(state, "old-task")) == "old-task"
    for text in (
        "",
        "now make the note shorter",
        launch(state, "gift-note") + " Then stop.",
        "Please " + launch(state, "gift-note"),
        "Read /Users/dev/shop/tasks/gift-note/session.md and follow it.",
        launch(state, "Gift_Note"),
    ):
        assert named(text) is None, text


def test_the_first_prompt_is_the_first_user_record_that_is_not_meta(
    tmp_path: Path,
) -> None:
    brief = launch(tmp_path / ".lem" / "state", SLUG)
    path = tmp_path / "t.jsonl"
    write(
        path, *HEAD, "{half", prompt([{"type": "text", "text": brief}]), prompt("later")
    )
    assert claude_transcript.task_named(path) == SLUG
    image = {"type": "image", "source": {}}
    write(path, prompt([image, {"type": "text", "text": brief}]))
    assert claude_transcript.task_named(path) is None
    write(path, *HEAD, prompt("later"), prompt(brief))
    assert claude_transcript.task_named(path) is None
    assert claude_transcript.task_named(tmp_path / "gone.jsonl") is None


def test_a_path_whose_name_holds_a_line_separator_still_names_the_transcript(
    tmp_path: Path,
) -> None:
    # A folder's name may hold the characters str.splitlines breaks at, and the sessions file
    # keeps them as they are.
    state, projects = tmp_path / ".lem" / "state", tmp_path / "projects" / "-shop"
    kept = write(projects / "aaa.jsonl", spent("m1", 1, 2))
    odd = str(projects / "a\N{LINE SEPARATOR}b\N{PARAGRAPH SEPARATOR}c\x85d.jsonl")
    logged(state, "gift-note", kept, "aaa", 1)
    logged(state, "gift-note", odd, "bbb", 2)
    found = bound(tmp_path).transcripts("gift-note")
    assert [one.path for one in found] == [kept, odd]


# ---- the tokens of a task ----


def test_each_reply_counts_once_with_its_subagents(tmp_path: Path) -> None:
    projects = tmp_path / "projects" / "-shop"
    # One reply written as two records (two blocks), a user record, a line that does not
    # read, a line of JSON that is no record, and a line with no time.
    first = write(
        projects / "aaa.jsonl",
        prompt("go"),
        spent("m1", 3, 100, 1000, 50),
        spent("m1", 3, 100, 1000, 50),
        spent("m2", 2, 10),
        "{half",
        "[]",
        "",
    )
    subagents = projects / "aaa" / "subagents"
    write(
        subagents / "agent-a1.jsonl",
        spent("s1", 5, 20, 7, 9),
        spent("s1", 5, 20, 7, 9),
    )
    (subagents / "agent-a1.meta.json").write_text('{"agentType": "lem:lem-builder"}')
    second = write(projects / "bbb.jsonl", spent("m3", 1, 1))
    found = bound(tmp_path).tokens(
        (Transcript(path=first, claude="aaa"), Transcript(path=second, claude="bbb"))
    )
    assert found == Tokens(
        input=11,
        output=131,
        cache_read=1007,
        cache_write=59,
        sessions=2,
        subagents=1,
        unread=1,
    )


def test_a_transcript_that_is_gone_is_counted_as_missing(tmp_path: Path) -> None:
    kept = write(tmp_path / "projects" / "-shop" / "aaa.jsonl", spent("m1", 1, 2))
    gone = str(tmp_path / "projects" / "-shop" / "gone.jsonl")
    found = bound(tmp_path).tokens(
        (Transcript(path=kept, claude="aaa"), Transcript(path=gone, claude="gone"))
    )
    assert (found.output, found.sessions, found.missing) == (2, 1, 1)


# ---- the signs of one transcript ----


@dataclass
class Folder:
    """A Claude Code folder laid out as Claude Code 2.1.330 lays it out (2026-11-22): a
    transcript `projects/-shop/ID.jsonl`, its `ID/subagents/`, and `sessions/PID.json`."""

    root: Path

    def transcript(self, claude: str, *records: object) -> Transcript:
        path = write(self.root / "projects" / "-shop" / f"{claude}.jsonl", *records)
        return Transcript(path=path, claude=claude)

    def process(self, pid: int, claude: str) -> None:
        write(self.root / "sessions" / f"{pid}.json", {"pid": pid, "sessionId": claude})

    def subagent(self, transcript: Transcript, name: str, *records: object) -> None:
        folder = Path(transcript.path).with_suffix("") / "subagents"
        write(folder / f"{name}.jsonl", *records)


@pytest.fixture
def claude(tmp_path: Path) -> Folder:
    """A Claude Code folder with the process file of the session `f0410fb9` at PID, another
    session's, and one that does not read."""
    folder = Folder(tmp_path / "claude")
    folder.process(PID, "f0410fb9")
    folder.process(3785, "b8927615")
    (folder.root / "sessions" / "3786.json").write_text("not json")
    return folder


def own(claude: Folder, *newest: object) -> Transcript:
    """The session's transcript: a prompt, a reply that ended at 10:15:42, then `newest`."""
    return claude.transcript(
        "f0410fb9",
        prompt("go", "2026-11-22T10:15:37.756Z"),
        reply(at="2026-11-22T10:15:42.728Z"),
        *newest,
    )


def signs(
    transcript: Transcript,
    *children: str,
    table: claude_processes.Table | None = None,
) -> Signs:
    """The signs of `transcript`, with `children` the commands its process at PID runs, or
    with the process table `table`."""
    harness = bound(Path(transcript.path).parent, table or FakeTable({PID: children}))
    return harness.signs(transcript)


ENDED_AT = datetime(2026, 11, 22, 10, 15, 42, tzinfo=UTC)


def test_a_transcript_alone_gives_its_newest_turn(claude: Folder) -> None:
    # A message that reaches a parked pane writes a record and runs no turn.
    queued = {"type": "queue-operation", "timestamp": "2026-11-22T15:53:31Z"}
    assert signs(own(claude, queued)) == Signs(sign=ENDED_AT, turn="ended")


def test_a_newer_subagent_gives_the_sign_and_never_the_turn(claude: Folder) -> None:
    transcript = own(claude)
    claude.subagent(
        transcript,
        "agent-ae51df94",
        prompt("look", "2026-11-22T10:50:00Z", isSidechain=True),
        reply("tool_use", "Read", at="2026-11-22T10:51:00Z", isSidechain=True),
    )
    # The meta file beside it is no transcript.
    meta = (
        Path(transcript.path).with_suffix("") / "subagents" / "agent-ae51df94.meta.json"
    )
    write(meta, prompt("x", "2026-11-22T12:00:00Z"))
    newer = datetime(2026, 11, 22, 10, 51, tzinfo=UTC)
    assert signs(transcript) == Signs(sign=newer, turn="ended")
    # beside the port: the main thread's own newest sign, which picks a session's turn
    looks = harness_claude.bind(place(Path(transcript.path).parent))
    assert looks.main_sign(transcript) == ENDED_AT


def test_a_bash_command_of_the_session_is_a_shell(claude: Folder) -> None:
    # A foreground command and a background one (`run_in_background`) have the same form.
    transcript = own(claude)
    assert signs(transcript, SNAPSHOT_LINE).shell
    sleeping = SNAPSHOT_LINE.replace("lem land check", "sleep 40")
    assert signs(transcript, "caffeinate -i -t 300", sleeping).shell


def test_a_hooks_process_and_caffeinate_are_no_shell(claude: Folder) -> None:
    hook = "/usr/bin/python3 /Users/someone/.local/bin/mailbox-chat.py claude-hook"
    found = signs(own(claude), hook, "caffeinate -i -t 300")
    assert found == Signs(sign=ENDED_AT, shell=False, turn="ended")


def test_a_shell_of_another_claude_is_not_this_sessions(claude: Folder) -> None:
    table = FakeTable({PID: (), 3785: (SNAPSHOT_LINE,)})
    assert not signs(own(claude), table=table).shell


def test_a_record_with_no_process_file_gives_no_signs(claude: Folder) -> None:
    other = claude.transcript("b0000001", prompt("go"), reply())
    last = datetime(2026, 11, 25, 10, 5, tzinfo=UTC)
    assert signs(other, SNAPSHOT_LINE) == Signs(sign=last, read=False)
    # The process file of another Claude Code folder is no file of the transcript's folder.
    elsewhere = Folder(claude.root.parent / "claude-other")
    elsewhere.process(PID, "a0000002")
    moved = claude.transcript("a0000002", prompt("go"), reply())
    assert signs(moved, SNAPSHOT_LINE) == Signs(sign=last, read=False)
    # A transcript outside the form `FOLDER/projects/NAME/ID.jsonl` has no folder.
    assert signs(Transcript(path="/t.jsonl", claude="f0410fb9")) == Signs(read=False)


def test_a_process_file_whose_pid_is_gone_gives_no_signs(claude: Folder) -> None:
    assert signs(own(claude), table=FakeTable({1: ("/sbin/launchd",)})) == Signs(
        sign=ENDED_AT, read=False
    )


def test_a_process_table_that_could_not_be_read_gives_no_signs(claude: Folder) -> None:
    found = signs(own(claude), table=UnreadTable())
    assert (found.read, found.shell, found.turn) == (False, False, None)
    assert found.sign == ENDED_AT


def test_no_turn_when_the_signs_do_not_read_or_no_record_decides(
    claude: Folder,
) -> None:
    running = own(claude, reply("tool_use", "Bash", at="2026-11-22T10:16:00Z"))
    assert signs(running).turn == "runs"
    assert signs(running, table=FakeTable()).turn is None
    undecided = claude.transcript(
        "f0410fb9", {"type": "permission-mode"}, reply(None), {"type": "attachment"}
    )
    assert signs(undecided) == Signs(sign=datetime(2026, 11, 25, 10, 5, tzinfo=UTC))


def test_a_transcript_that_is_gone_gives_no_sign_and_no_turn(claude: Folder) -> None:
    transcript = own(claude)
    Path(transcript.path).unlink()
    assert signs(transcript, SNAPSHOT_LINE) == Signs(shell=True)


def test_the_transcript_its_subagents_and_its_process_file(claude: Folder) -> None:
    transcript = own(
        claude, {"type": "queue-operation", "timestamp": "2026-11-22T15:53Z"}
    )
    assert signs(transcript, SNAPSHOT_LINE) == Signs(
        sign=ENDED_AT, shell=True, turn="ended"
    )
    claude.subagent(
        transcript,
        "agent-ae51df94",
        prompt("x", "2026-11-22T10:50:00Z", isSidechain=True),
    )
    later = datetime(2026, 11, 22, 10, 50, tzinfo=UTC)
    assert signs(transcript) == Signs(sign=later, shell=False, turn="ended")


def test_a_fork_of_another_task_logged_under_the_task_gives_no_sign_of_the_task(
    tmp_path: Path, claude: Folder
) -> None:
    # HOST's own transcript ends at 10:00 on a reply with no stop, so its prompt decides; a
    # fork of SLUG's session, logged under HOST, runs a shell command at 10:40.
    state = tmp_path / ".lem" / "state"
    host = claude.transcript(
        "f0410fb9",
        prompt(launch(state, HOST), "2026-11-22T09:30:00Z"),
        {"type": "assistant", "timestamp": "2026-11-22T10:00:00Z"},
    )
    fork = claude.transcript(
        "6fe214ec",
        prompt(launch(state, SLUG), "2026-11-22T01:33:27Z", sessionKind="bg"),
        {"type": "assistant", "timestamp": "2026-11-22T10:40:00Z", "sessionKind": "bg"},
    )
    claude.process(64001, "6fe214ec")
    logged(state, HOST, host.path, host.claude, 1)
    logged(state, HOST, fork.path, fork.claude, 2)
    table = FakeTable({PID: (), 64001: (SNAPSHOT_LINE,)})
    harness = harness_claude.ClaudeHarness(place(tmp_path), table)
    assert harness.transcripts(HOST) == (host,)
    hosts = [harness.signs(one) for one in harness.transcripts(HOST)]
    at_ten = datetime(2026, 11, 22, 10, 0, tzinfo=UTC)
    assert hosts == [Signs(sign=at_ten, shell=False, turn="runs")]
    # The fork alone is no transcript of HOST.
    (state / "tasks" / HOST / "sessions.jsonl").unlink()
    logged(state, HOST, fork.path, fork.claude, 3)
    assert harness.transcripts(HOST) == ()


def test_the_machines_process_table_gives_the_children_of_a_live_process(
    tmp_path: Path,
) -> None:
    # The test's own process stands for the session's Claude Code, and a child it starts for
    # a command of the Bash tool: no other process decides the case.
    mark = "shell-snapshots/snapshot-lem-test"
    folder = Folder(tmp_path / "claude")
    folder.process(os.getpid(), "c0ffee00")
    transcript = folder.transcript("c0ffee00", prompt("go"), reply())
    child = subprocess.Popen(["/bin/sh", "-c", f"sleep 30; : {mark}"])
    try:
        found = claude_processes.Machine().children(os.getpid())
        read = harness_claude.bind(place(tmp_path)).signs(transcript)
    finally:
        child.terminate()
        child.wait()
    assert any(mark in line for line in found or ())
    assert read == Signs(
        sign=datetime(2026, 11, 25, 10, 5, tzinfo=UTC), shell=True, turn="ended"
    )
    assert claude_processes.Machine().children(child.pid) is None
