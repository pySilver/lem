"""corrections.py's rules that read a file and return a result, each called in this
process. The hook, the queue and the review are facts of real runs,
in tests/lem-machine.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import ast
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import corrections, paths, project
from lem import state as lem_state


def said(text: str) -> dict:
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


class LastAgentText(unittest.TestCase):
    """The newest text an agent wrote, from a Claude Code transcript, one JSON record
    a line."""

    def test_a_text_that_holds_a_line_separator_is_the_newest_text(self) -> None:
        # Claude Code's JSON keeps U+2028 and U+2029 as they are inside a string
        newest = "first a\N{LINE SEPARATOR}b\N{PARAGRAPH SEPARATOR}c\x85d"
        with tempfile.TemporaryDirectory() as folder:
            transcript = Path(folder) / "session.jsonl"
            transcript.write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False) + "\n"
                    for record in (said("older"), said(newest))
                ),
                encoding="utf-8",
            )
            self.assertEqual(corrections.last_agent_text(str(transcript)), newest)


class ProposedLesson(unittest.TestCase):
    """A retro changes no file: a lesson it finds goes into a proposal of its day, and
    its group is recorded `proposed`, with the file the proposal would change and the
    proposal's name, so that `lessons` gives it as a lesson in no file yet
    (stages/learn.md, "The correction queue")."""

    LESSON = "A night names the item it left out and why (retro of 2026-11-24 #3)."
    TARGET = "skills/lem/stages/night.md"

    def test_record_takes_the_verdict_proposed(self) -> None:
        args = corrections.arguments().parse_args(
            [
                "record",
                "1a2b3c4d",
                "--decision",
                "lesson",
                "--verdict",
                "proposed",
                "--target",
                self.TARGET,
                "--lesson",
                self.LESSON,
            ]
        )
        self.assertEqual(
            (args.verdict, args.target, args.lesson),
            ("proposed", self.TARGET, self.LESSON),
        )

    def test_lessons_gives_a_proposed_lesson_with_its_verdict_and_its_target(
        self,
    ) -> None:
        owner = "you left out the item again and did not say why"
        with tempfile.TemporaryDirectory() as folder:
            where = Path(folder)
            (where / "corrections.jsonl").write_text(
                json.dumps(
                    {
                        "ts": "2026-11-24T06:10:00Z",
                        "session": "s-1",
                        "owner": owner,
                        "previous": "",
                        "p_lesson": 0.8,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            gid = corrections.group_id(owner)
            with mock.patch("sys.stdout", new=io.StringIO()):
                corrections.cmd_record(
                    where, gid, "lesson", "proposed", self.TARGET, self.LESSON
                )
            with mock.patch("sys.stdout", new=io.StringIO()) as out:
                corrections.cmd_lessons(where)
            rows = json.loads(out.getvalue())
            self.assertEqual(
                [(r["lesson"], r["target"], r["verdict"], r["days"]) for r in rows],
                [(self.LESSON, self.TARGET, "proposed", ["2026-11-24"])],
            )
            self.assertEqual(corrections.unreviewed(where), {})


class TheMachinesSwitch(unittest.TestCase):
    """Whether the hook sends: `collect = true` under `[corrections]` in `machine.toml`,
    and a repository with `.lem/settings.toml` (criteria 5 and 6 of
    one-home-folder-for-lem). Each case has its own home folder, as XDG_CONFIG_HOME, and
    its own repository, whose top git names through `corrections.git`."""

    def setUp(self) -> None:
        self.kept = os.environ.get("XDG_CONFIG_HOME")
        self.folder = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = str(Path(self.folder.name) / "config")
        self.repo = Path(self.folder.name) / "repo"
        (self.repo / ".lem").mkdir(parents=True)
        (self.repo / lem_state.TEAM_SETTINGS).write_text(
            '[branch]\nbase = "main"\n', encoding="utf-8"
        )

    def tearDown(self) -> None:
        if self.kept is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.kept
        self.folder.cleanup()

    def machine(self, data: bytes) -> None:
        file = lem_state.machine_file()
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)

    def collects(self) -> bool:
        with mock.patch.object(corrections, "git", return_value=str(self.repo)):
            return corrections.collects(str(self.repo))

    def test_the_machines_yes_sends_in_a_repository_that_uses_lem(self) -> None:
        self.machine(b"[load]\nstart = 4\n\n[corrections]\ncollect = true\n")
        self.assertTrue(self.collects())

    def test_a_machine_with_no_line_or_a_no_sends_nothing_and_asks_git_nothing(
        self,
    ) -> None:
        for data in (
            None,
            b"[load]\nstart = 4\n",
            b"[corrections]\n",
            b"[corrections]\ncollect = false\n",
        ):
            with self.subTest(data=data):
                if data is None:
                    lem_state.machine_file().unlink(missing_ok=True)
                else:
                    self.machine(data)
                with mock.patch.object(
                    corrections,
                    "git",
                    side_effect=AssertionError(
                        "a machine that says no costs no git call"
                    ),
                ):
                    self.assertFalse(corrections.collects(str(self.repo)))

    def test_a_machine_file_that_does_not_read_or_holds_what_is_not_valid_there_sends_nothing(
        self,
    ) -> None:
        for data in (
            b"not toml [\n",
            b"[corrections]\ncollect = true\n# caf\xe9\n",
            b'[corrections]\ncollect = "yes"\n',
            b'[corrections]\ncollect = true\n\n[seats]\nmerger = "claude"\n',
            b"[corrections]\ncollect = true\nsend = true\n",
        ):
            with self.subTest(data=data):
                self.machine(data)
                self.assertFalse(self.collects())

    def test_a_relative_config_home_sends_nothing(self) -> None:
        self.machine(b"[corrections]\ncollect = true\n")
        os.environ["XDG_CONFIG_HOME"] = "config"
        self.assertFalse(self.collects())

    def test_a_repository_that_does_not_use_lem_gets_nothing_sent(self) -> None:
        self.machine(b"[corrections]\ncollect = true\n")
        (self.repo / lem_state.TEAM_SETTINGS).rename(
            self.repo / ".lem" / "project.toml"
        )
        self.assertFalse(self.collects())
        with mock.patch.object(corrections, "git", return_value=None):
            self.assertFalse(corrections.collects(str(self.repo)))

    def test_the_repositorys_own_yes_sends_nothing(self) -> None:
        (self.repo / lem_state.TEAM_SETTINGS).write_text(
            "[corrections]\ncollect = true\n", encoding="utf-8"
        )
        (self.repo / lem_state.LOCAL_SETTINGS).write_text(
            "[corrections]\ncollect = true\n", encoding="utf-8"
        )
        self.assertFalse(self.collects())

    def test_show_gives_the_switch_from_the_machines_file_or_lems_default(self) -> None:
        def corrections_of(machine: dict) -> dict:
            return project.decide(self.repo, self.repo, {}, {}, {}, None, {}, machine)[
                "corrections"
            ]

        self.assertEqual(
            corrections_of({}), {"collect": False, "from": project.DEFAULT_FROM}
        )
        self.assertEqual(
            corrections_of({"corrections": {}}),
            {"collect": False, "from": project.DEFAULT_FROM},
        )
        shown = lem_state.shown(lem_state.machine_file())
        self.assertEqual(
            corrections_of({"corrections": {"collect": False}}),
            {"collect": False, "from": shown},
        )
        self.assertEqual(
            corrections_of({"corrections": {"collect": True}}),
            {"collect": True, "from": shown},
        )

    def test_the_command_writes_the_line_and_keeps_the_other_tables(self) -> None:
        self.machine(b"[load]\nstart = 4\n\n[serve]\nport = 4500\n")
        with contextlib.redirect_stdout(io.StringIO()) as said_no:
            corrections.cmd_collect("no")
        self.assertEqual(
            json.loads(said_no.getvalue()),
            {"collect": False, "file": str(lem_state.machine_file())},
        )
        self.assertEqual(
            lem_state.machine_tables(),
            {
                "load": {"start": 4},
                "serve": {"port": 4500},
                "corrections": {"collect": False},
            },
        )
        with contextlib.redirect_stdout(io.StringIO()):
            corrections.cmd_collect("yes")
        self.assertEqual(lem_state.machine_table("corrections"), {"collect": True})
        self.assertEqual(lem_state.machine_table("serve"), {"port": 4500})

    def test_the_command_refuses_a_file_it_cannot_keep_and_leaves_it(self) -> None:
        self.machine(b"not toml [\n")
        with self.assertRaises(corrections.QueueError) as raised:
            corrections.cmd_collect("yes")
        self.assertIn(
            f"{lem_state.machine_file()} does not read as TOML", str(raised.exception)
        )
        self.assertEqual(lem_state.machine_file().read_bytes(), b"not toml [\n")

    def test_a_home_folder_that_cannot_be_written_is_refused_with_its_fix(self) -> None:
        # a file where the home folder's parent should be: the write fails for root too,
        # which a folder with no write bit does not stop
        Path(os.environ["XDG_CONFIG_HOME"]).write_text("", encoding="utf-8")
        with self.assertRaises(corrections.QueueError) as raised:
            corrections.cmd_collect("no")
        self.assertIn(
            f"{lem_state.machine_file()} was not written (Not a directory)",
            str(raised.exception),
        )
        self.assertIn("make its folder writable", str(raised.exception))


class Calls(ast.NodeVisitor):
    """Each name a function calls, as `module.name(...)` or `name(...)`, under the
    outermost function of the file that holds the call."""

    function: str | None

    def __init__(self, file: str, found: dict) -> None:
        self.file, self.found, self.function = file, found, None

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        outer = self.function
        self.function = outer or node.name
        self.generic_visit(node)
        self.function = outer

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815 - ast.NodeVisitor looks it up by this name

    def visit_Call(self, node: ast.Call) -> None:
        called = (
            node.func.attr
            if isinstance(node.func, ast.Attribute)
            else node.func.id
            if isinstance(node.func, ast.Name)
            else None
        )
        if called and self.function:
            self.found.setdefault(called, set()).add((self.file, self.function))
        self.generic_visit(node)


CALLS: dict = {}


def calls_of(name: str) -> set:
    """Each (file, function) of Lem's package, every module of it, and `bin/lem`, that
    calls `name`."""
    if not CALLS:
        for file in [
            *sorted((paths.PACKAGE).glob("*.py")),
            paths.ROOT / "bin" / "lem",
        ]:
            Calls(file.name, CALLS).visit(ast.parse(file.read_text(encoding="utf-8")))
    return CALLS.get(name, set())


class TheHomeFoldersWriters(unittest.TestCase):
    """Every writer of `machine.toml` is a command the owner runs, and so is the one
    writer of the home folder's `settings.toml`, `lem project set global` (criterion 7
    of one-home-folder-for-lem, and criterion 6 of seat-defaults-and-fallback): no hook
    and no update of the plugin writes either. A new writer fails here, and is added on
    purpose. That the hooks write neither file when they run is checked
    in tests/lem-machine.sh."""

    def test_the_writers_of_the_machines_file_are_the_owners_commands(self) -> None:
        # write_held is write_machine for a caller that holds the lock already
        self.assertEqual(
            (calls_of("write_machine") | calls_of("write_held"))
            - {("state.py", "write_machine")},
            {
                ("project.py", "cmd_load"),
                ("project.py", "cmd_handoff"),
                ("serve.py", "configure"),
                ("peers.py", "join"),
                ("peers.py", "leave"),
                ("corrections.py", "cmd_collect"),
            },
        )

    def test_the_home_settings_file_is_written_by_set_global_alone(self) -> None:
        self.assertEqual(
            calls_of("home_settings_file"),
            {
                ("project.py", "home_name"),
                ("project.py", "load"),
                ("state.py", "place_name"),
                ("project.py", "cmd_set"),
            },
        )
        self.assertEqual(
            calls_of("write_edits") - {("state.py", "write_edits")},
            {("project.py", "cmd_set")},
        )

    def test_the_hooks_reach_no_writer(self) -> None:
        # the plugin's hooks are these four modules, each the first word after the
        # launcher's path; the board server's starts `serve.py --ensure`, which writes
        # no setting
        hooks = json.loads(
            (paths.ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8")
        )["hooks"]
        scripts = {
            hook["command"].split('"')[-1].split()[0] + ".py"
            for entries in hooks.values()
            for entry in entries
            for hook in entry["hooks"]
        }
        self.assertEqual(
            scripts, {"corrections.py", "serve_hook.py", "session_hook.py", "ask.py"}
        )
        self.assertIn(
            '"--ensure"]', (paths.PACKAGE / "serve_hook.py").read_text(encoding="utf-8")
        )
        writers = calls_of("write_machine") | calls_of("write_held")
        for hook in (
            ("serve_hook.py", "main"),
            ("session_hook.py", "main"),
            ("ask.py", "hook_stop"),
            ("serve.py", "ensure"),
            ("corrections.py", "cmd_hook"),
            ("corrections.py", "cmd_worker"),
        ):
            with self.subTest(hook=hook):
                self.assertNotIn(hook, writers)


if __name__ == "__main__":
    unittest.main()
