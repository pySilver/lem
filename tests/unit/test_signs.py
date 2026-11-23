"""The signs of work of a task's Claude Code session (lem_signs.py), and what `lem session list` says of
them: the rule as a call of `read_signs` over the facts, the read of a transcript from its end, the
facts read from a Claude Code folder laid out as Claude Code 2.1.330 lays it out (2026-11-22), and a
fork of another task's session logged under the task's own session (6fe214ec, 2026-11-22).

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import importlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"
sys.path.insert(0, str(SCRIPTS))
lem_signs = importlib.import_module("lem_signs")
session = importlib.import_module("session")

SLUG = "merge-leaves-board-lock"
# the pane of the task's newest `session.open`, and the old pane before a restart
PANE, OLD = "902B55C6-AAAA-4BBB-8CCC-000000000001", "9F9C5C30-AAAA-4BBB-8CCC-000000000002"
FOLDER = "/Users/someone/.claude"
TRANSCRIPT = f"{FOLDER}/projects/-shop/f0410fb9.jsonl"
PID = 63868
SNAPSHOT_LINE = f"/bin/zsh -c source {FOLDER}/shell-snapshots/snapshot-zsh-1795367130285-3ryanb.sh 2>/dev/null || true && eval 'lem land check'"


# the task whose background host the fork of SLUG's session ran in (6fe214ec, 2026-11-22)
HOST = "board-card-search"


def record(claude: str = "f0410fb9", transcript: str = TRANSCRIPT, pane: str | None = PANE, task: str = SLUG) -> dict:
    found = {"ts": "2026-11-22T10:15:00Z", "event": "session.transcript", "task": task, "claude": claude, "transcript": transcript, "source": "startup"}
    if pane is not None:
        found["session"] = pane
    return found


def table(*children: str, parent: int = PID) -> str:
    rows = ["    1     0 /sbin/launchd", f"{parent} 70000 claude Read the session.md and follow it."]
    rows += [f"{50000 + i} {parent} {command}" for i, command in enumerate(children)]
    return "\n".join(rows) + "\n"


PROCESSES = {FOLDER: [{"pid": PID, "sessionId": "f0410fb9", "status": "idle"}, {"pid": 3785, "sessionId": "b8927615"}]}
FORK = f"{FOLDER}/projects/-shop/6fe214ec.jsonl"
FORK_PID = 64001


def launch(slug: str) -> str:
    """The first prompt `lem session open` gives the session of task SLUG (session.py `launch_line`)."""
    return f"Read /Users/someone/shop/.lem/state/tasks/{slug}/session.md and follow it."


class ReadSigns(unittest.TestCase):
    def signs(self, records=None, turns=None, processes=None, ps=None, pane=PANE) -> dict:
        return lem_signs.read_signs([record()] if records is None else records, pane,
                                    {TRANSCRIPT: ["2026-11-22T10:15:42Z"]} if turns is None else turns,
                                    PROCESSES if processes is None else processes, table() if ps is None else ps, SLUG, {})

    def test_a_transcript_alone_gives_its_newest_turn(self):
        self.assertEqual(self.signs(), {"sign": "2026-11-22T10:15:42Z", "shell": False, "signs": True})

    def test_a_newer_subagent_gives_the_sign(self):
        found = self.signs(turns={TRANSCRIPT: ["2026-11-22T10:15:42Z", "2026-11-22T10:40:05Z", None]})
        self.assertEqual(found["sign"], "2026-11-22T10:40:05Z")

    def test_a_bash_command_of_the_session_is_a_shell(self):
        # a foreground command and a background one (`run_in_background`) have the same form
        self.assertTrue(self.signs(ps=table(SNAPSHOT_LINE))["shell"])
        self.assertTrue(self.signs(ps=table("caffeinate -i -t 300", SNAPSHOT_LINE.replace("lem land check", "sleep 40")))["shell"])

    def test_a_hooks_process_and_caffeinate_are_no_shell(self):
        found = self.signs(ps=table("/usr/bin/python3 /Users/someone/.local/bin/mailbox-chat.py claude-hook", "caffeinate -i -t 300"))
        self.assertEqual((found["shell"], found["signs"]), (False, True))

    def test_a_shell_of_another_claude_is_not_this_sessions(self):
        self.assertFalse(self.signs(ps=table() + f"50100 3785 {SNAPSHOT_LINE}\n")["shell"])

    def test_no_record_gives_no_signs(self):
        self.assertEqual(self.signs(records=[], ps=table(SNAPSHOT_LINE)), {"sign": None, "shell": False, "signs": False})

    def test_the_old_panes_record_counts_for_no_session(self):
        # the old pane's `/clear`, or a background host that runs with another pane's environment
        old = record(claude="6fe214ec", transcript=f"{FOLDER}/projects/-shop/6fe214ec.jsonl", pane=OLD)
        found = self.signs(records=[old], turns={old["transcript"]: ["2026-11-22T11:50:00Z"]},
                           processes={FOLDER: [{"pid": PID, "sessionId": "6fe214ec"}]}, ps=table(SNAPSHOT_LINE))
        self.assertEqual(found, {"sign": None, "shell": False, "signs": False})
        both = self.signs(records=[record(), old], turns={TRANSCRIPT: ["2026-11-22T10:15:42Z"], old["transcript"]: ["2026-11-22T11:50:00Z"]})
        self.assertEqual(both["sign"], "2026-11-22T10:15:42Z")

    def test_the_session_is_matched_in_no_regard_to_case(self):
        self.assertTrue(self.signs(pane=PANE.lower())["signs"])

    def test_a_record_without_the_session_counts_for_none(self):
        self.assertFalse(self.signs(records=[record(pane=None)])["signs"])

    def test_a_record_with_no_process_file_gives_no_signs(self):
        found = self.signs(processes={FOLDER: [{"pid": 3785, "sessionId": "b8927615"}]}, ps=table(SNAPSHOT_LINE))
        self.assertEqual(found, {"sign": "2026-11-22T10:15:42Z", "shell": False, "signs": False})
        # the process file of the server's own folder is no file of the transcript's folder
        self.assertFalse(self.signs(processes={"/Users/someone/.claude-other": PROCESSES[FOLDER]})["signs"])

    def test_a_process_file_whose_pid_is_gone_gives_no_signs(self):
        self.assertFalse(self.signs(ps="    1     0 /sbin/launchd\n")["signs"])

    def test_a_process_table_that_could_not_be_read_gives_no_signs(self):
        self.assertFalse(lem_signs.read_signs([record()], PANE, {}, PROCESSES, None, SLUG, {})["signs"])

    def test_a_transcript_of_another_task_in_the_tasks_session_counts_for_none(self):
        # criterion 3: the own transcript's newest turn at 10:00, the fork of SLUG's session at 10:40, both under HOST's pane
        records = [record(task=HOST), record(claude="6fe214ec", transcript=FORK, task=HOST)]
        turns = {TRANSCRIPT: ["2026-11-22T10:00:00Z"], FORK: ["2026-11-22T10:40:00Z"]}
        processes = {FOLDER: [*PROCESSES[FOLDER], {"pid": FORK_PID, "sessionId": "6fe214ec"}]}
        ps = table() + f"{FORK_PID} 70000 claude\n50200 {FORK_PID} {SNAPSHOT_LINE}\n"
        found = lem_signs.read_signs(records, PANE, turns, processes, ps, HOST, {TRANSCRIPT: HOST, FORK: SLUG})
        self.assertEqual(found, {"sign": "2026-11-22T10:00:00Z", "shell": False, "signs": True})
        # a first prompt that names no task (a `/clear` in the pane) keeps the record's task
        self.assertEqual(lem_signs.read_signs(records, PANE, turns, processes, ps, HOST, {TRANSCRIPT: None, FORK: None})["sign"], "2026-11-22T10:40:00Z")
        # the fork alone is no record of the session: no sign, and its process is no evidence
        alone = lem_signs.read_signs(records[1:], PANE, turns, processes, ps, HOST, {FORK: SLUG})
        self.assertEqual(alone, {"sign": None, "shell": False, "signs": False})


class Transcript(unittest.TestCase):
    LINES = [
        {"type": "user", "timestamp": "2026-11-22T10:15:37.756Z"},
        {"type": "assistant", "timestamp": "2026-11-22T10:15:42.728Z", "message": {"content": [{"type": "text", "text": "x" * 300}]}},
        {"type": "system", "timestamp": "2026-11-22T10:15:43.321Z"},
        {"type": "attachment", "timestamp": "2026-11-22T10:45:48.831Z"},
        {"type": "continued-in", "timestamp": "2026-11-22T10:45:49.327Z"},
        # the owner's wake reached the parked pane: a record, and no turn (f0410fb9 of #37)
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-11-22T15:53:31.059Z"},
        {"type": "cost-state"},
    ]

    def test_a_queue_operation_after_the_newest_turn_moves_no_sign(self):
        lines = [json.dumps(line) for line in reversed(self.LINES)]
        self.assertEqual(lem_signs.newest_turn(lines), "2026-11-22T10:15:42Z")
        self.assertIsNone(lem_signs.newest_turn([json.dumps(line) for line in self.LINES[2:]]))

    def test_the_file_is_read_from_its_end_in_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "t.jsonl"
            path.write_text("half a line\n" + "".join(json.dumps(line) + "\n" for line in self.LINES), encoding="utf-8")
            for block in (7, 64, 100000):
                with self.subTest(block=block):
                    read = [line for line in lem_signs.tail_lines(path, block) if line]
                    self.assertEqual(read, list(reversed(path.read_bytes().split(b"\n")[:-1])))
                    self.assertEqual(lem_signs.newest_turn(lem_signs.tail_lines(path, block)), "2026-11-22T10:15:42Z")


def write(path: Path, *lines: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")


class Folder(unittest.TestCase):
    """The facts read from a Claude Code folder: `projects/NAME/ID.jsonl`, its `ID/subagents/`, and
    `sessions/PID.json`."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / "claude"
        self.transcript = self.folder / "projects" / "-shop" / "f0410fb9.jsonl"
        write(self.transcript, {"type": "user", "timestamp": "2026-11-22T10:15:37Z"}, {"type": "assistant", "timestamp": "2026-11-22T10:15:42Z"},
              {"type": "queue-operation", "timestamp": "2026-11-22T15:53:31Z"})
        write(self.folder / "sessions" / f"{PID}.json", {"pid": PID, "sessionId": "f0410fb9", "status": "idle"})
        (self.folder / "sessions" / "3785.json").parent.mkdir(parents=True, exist_ok=True)
        (self.folder / "sessions" / "3785.json").write_text("not json", encoding="utf-8")
        self.records = [record(transcript=str(self.transcript))]

    def tearDown(self):
        self.temp.cleanup()

    def test_the_transcript_its_subagents_and_its_process_file(self):
        ps = table(SNAPSHOT_LINE)
        self.assertEqual(lem_signs.signs_of(self.records, PANE, ps, SLUG), {"sign": "2026-11-22T10:15:42Z", "shell": True, "signs": True})
        subagents = self.transcript.with_suffix("") / "subagents"
        write(subagents / "agent-ae51df94.jsonl", {"type": "user", "isSidechain": True, "timestamp": "2026-11-22T10:50:00Z"})
        # the meta file beside it is no transcript
        write(subagents / "agent-ae51df94.meta.json", {"type": "user", "timestamp": "2026-11-22T12:00:00Z"})
        self.assertEqual(lem_signs.signs_of(self.records, PANE, table(), SLUG)["sign"], "2026-11-22T10:50:00Z")

    def test_a_transcript_that_is_gone_gives_no_sign(self):
        self.transcript.unlink()
        self.assertEqual(lem_signs.signs_of(self.records, PANE, table(), SLUG), {"sign": None, "shell": False, "signs": True})


# the process table with the fork's process, which runs a shell command: no sign of HOST's session either
FORK_PS = table() + f"{FORK_PID} 70000 claude\n50200 {FORK_PID} {SNAPSHOT_LINE}\n"


def two_transcripts(folder: Path) -> list[dict]:
    """In the Claude Code folder FOLDER, HOST's own transcript, its newest turn at 10:00, and a fork of
    SLUG's session at 10:40 that Claude Code's background host, started from HOST's pane, logged under
    HOST and HOST's pane: its first prompt is SLUG's launch line, copied from its parent (6fe214ec,
    2026-11-22). The two records, and a process file for each."""
    own, fork = folder / "projects" / "-shop" / "f0410fb9.jsonl", folder / "projects" / "-shop" / "6fe214ec.jsonl"
    meta = {"type": "user", "isMeta": True, "message": {"role": "user", "content": "<local-command-caveat>x</local-command-caveat>"}}
    write(own, {"type": "permission-mode"}, meta, {"type": "user", "message": {"role": "user", "content": launch(HOST)}, "timestamp": "2026-11-22T09:30:00Z"},
          {"type": "assistant", "timestamp": "2026-11-22T10:00:00Z"})
    write(fork, {"type": "permission-mode"}, meta,
          {"type": "user", "sessionKind": "bg", "message": {"role": "user", "content": launch(SLUG)}, "timestamp": "2026-11-22T01:33:27Z"},
          {"type": "assistant", "sessionKind": "bg", "timestamp": "2026-11-22T10:40:00Z"})
    write(folder / "sessions" / f"{PID}.json", {"pid": PID, "sessionId": "f0410fb9"})
    write(folder / "sessions" / f"{FORK_PID}.json", {"pid": FORK_PID, "sessionId": "6fe214ec"})
    return [record(transcript=str(own), task=HOST), record(claude="6fe214ec", transcript=str(fork), task=HOST)]


class Fork(unittest.TestCase):
    """The signs of HOST's session over `two_transcripts` on disk."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = two_transcripts(Path(self.temp.name) / "claude")
        self.own, self.fork = Path(self.records[0]["transcript"]), Path(self.records[1]["transcript"])
        self.ps = FORK_PS

    def tearDown(self):
        self.temp.cleanup()

    def test_the_signs_over_the_two_files_come_from_the_tasks_own_transcript(self):
        self.assertEqual(lem_signs.signs_of(self.records, PANE, self.ps, HOST), {"sign": "2026-11-22T10:00:00Z", "shell": False, "signs": True})
        facts = lem_signs.facts_of(self.records, PANE, self.ps, HOST)
        self.assertEqual(facts["named"], {str(self.own): HOST, str(self.fork): SLUG})
        # no turn of the fork is read
        self.assertEqual(facts["turns"], {str(self.own): ["2026-11-22T10:00:00Z"]})

    def test_the_transcript_of_a_record_of_an_old_pane_is_not_opened(self):
        old = record(claude="6fe214ec", transcript=str(self.fork), pane=OLD, task=HOST)
        with mock.patch.object(lem_signs.lem_tokens, "first_prompt", wraps=lem_signs.lem_tokens.first_prompt) as read:
            found = lem_signs.signs_of([self.records[0], old], PANE, self.ps, HOST)
        self.assertEqual([call.args for call in read.call_args_list], [(self.own,)])
        self.assertEqual(found["sign"], "2026-11-22T10:00:00Z")


class List(unittest.TestCase):
    """`lem session list` carries the signs on each entry, read for a live session only."""

    def listed(self, foreground: list | None, logged: list[dict], ps: str | None, task: str = SLUG, read: bool = False) -> dict:
        """The entry's signs, with the facts of the transcript at TRANSCRIPT, or with READ the facts read from
        the files the records name."""
        opened = {"ts": "2026-11-22T10:15:00Z", "event": "session.open", "task": task, "session": PANE, "name": task, "phase": "land", "why": "new"}
        nodes = [{"id": PANE, "name": task, "workspace": "W1", "foreground": foreground}]
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(session, "place", return_value={"session": "", "socket": "", "window": ""}))
            stack.enter_context(mock.patch.object(session, "tree", return_value=nodes))
            stack.enter_context(mock.patch.object(session.project, "events_named", side_effect=lambda root, *names: [e for e in [opened, *logged] if e["event"] in names]))
            stack.enter_context(mock.patch.object(session.project, "load", return_value={}))
            stack.enter_context(mock.patch.object(session.project, "read_tasks", return_value=[]))
            asked = stack.enter_context(mock.patch.object(session, "process_table", return_value=ps))
            if not read:
                stack.enter_context(mock.patch.object(session.lem_signs, "facts_of", side_effect=lambda records, pane, text, slug: {
                    "records": records, "session": pane, "turns": {TRANSCRIPT: ["2026-11-22T10:15:42Z"]}, "processes": PROCESSES, "table": text,
                    "slug": slug, "named": {}}))
            entry = session.cmd_list(Path("/lem-unit/repo"))[0]
        return {**{key: entry[key] for key in ("sign", "shell", "signs")}, "asked": asked.call_count}

    def test_a_live_sessions_entry_has_its_signs(self):
        self.assertEqual(self.listed(["claude"], [record()], table(SNAPSHOT_LINE)), {"sign": "2026-11-22T10:15:42Z", "shell": True, "signs": True, "asked": 1})

    def test_a_session_with_no_agent_or_no_record_reads_nothing(self):
        self.assertEqual(self.listed(["/bin/zsh"], [record()], table(SNAPSHOT_LINE)), {"sign": None, "shell": False, "signs": False, "asked": 0})
        self.assertEqual(self.listed(["claude"], [record(pane=OLD)], table(SNAPSHOT_LINE)), {"sign": None, "shell": False, "signs": False, "asked": 0})

    def test_a_process_table_that_does_not_read_gives_no_signs(self):
        self.assertEqual(self.listed(["claude"], [record()], None)["signs"], False)

    def test_a_fork_of_another_task_logged_under_the_session_gives_no_sign(self):
        # criterion 3, over the two files on disk and the real facts_of
        with tempfile.TemporaryDirectory() as folder:
            found = self.listed(["claude"], two_transcripts(Path(folder) / "claude"), FORK_PS, task=HOST, read=True)
        self.assertEqual(found, {"sign": "2026-11-22T10:00:00Z", "shell": False, "signs": True, "asked": 1})


if __name__ == "__main__":
    unittest.main()
