"""A task's own session (session.py) and its two hooks (session_hook.py), as calls of the functions
that hold the rules: the phase from the state, the handoff's form, the launch line with the seat and
`[handoff] tokens`, and the hooks with and without `LEM_TASK`. What agterm does with a session is in
tests/lem-session.sh, with a stand-in for agtermctl.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"
sys.path.insert(0, str(SCRIPTS))
lem_state = importlib.import_module("lem_state")
project = importlib.import_module("project")
session = importlib.import_module("session")
session_hook = importlib.import_module("session_hook")

ROOT = Path("/lem-unit/repo")
SLUG = "gift-note"
HANDOFF = """task: gift-note · from shape · written: 2026-11-21T10:05Z

<!-- a comment the check leaves out -->

## Settled

- the criteria, approved (`criteria.json`)

## Open

none

## Next step

The lead plans the export's column.

## Failed

- none

## Changed files

- `docs/plans/2026-11-21-gift-note.md`: added, not committed
- src/export.py: changed in 1a2b3c4
"""


class Machine(unittest.TestCase):
    """Each case runs with a folder of its own as XDG_CONFIG_HOME: the home directory's file is never read."""

    def setUp(self):
        self.kept = os.environ.get("XDG_CONFIG_HOME")
        self.folder = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self.folder.name

    def tearDown(self):
        if self.kept is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.kept
        self.folder.cleanup()

    def written(self, text: str) -> None:
        file = lem_state.machine_file()
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")


class Tokens(Machine):
    def test_absent_is_lems_number_and_zero_sets_nothing(self):
        self.assertEqual(lem_state.handoff_tokens(), 600_000)
        self.written("[handoff]\ntokens = 0\n")
        self.assertIsNone(lem_state.handoff_tokens())
        self.written("[handoff]\ntokens = 250000\n")
        self.assertEqual(lem_state.handoff_tokens(), 250_000)

    def test_under_the_floor_a_negative_a_bool_and_a_float_are_refused(self):
        for value, says in (("99999", "100000 or more"), ("-1", "100000 or more"), ("true", "of the wrong type"), ("150000.5", "of the wrong type")):
            with self.subTest(value=value):
                self.written(f"[handoff]\ntokens = {value}\n")
                with self.assertRaises(lem_state.StateError) as raised:
                    lem_state.handoff_tokens()
                self.assertIn(says, str(raised.exception))
                self.assertIn("lem project handoff --tokens N", str(raised.exception))

    def test_the_command_writes_the_number_and_default_takes_it_out_keeping_the_other_tables(self):
        self.written("[load]\nstart = 6\n")
        self.assertEqual(project.cmd_handoff("300000")["tokens"], 300_000)
        self.assertEqual(lem_state.machine_table("load"), {"start": 6})
        shown = project.cmd_handoff(None)
        self.assertEqual((shown["tokens"], shown["default"], shown["said"]), (300_000, False, "handoff tokens: 300000 (set here)"))
        self.assertIsNone(project.cmd_handoff("0")["tokens"])
        back = project.cmd_handoff("default")
        self.assertEqual((back["tokens"], back["default"], back["said"]), (600_000, True, "handoff tokens: 600000 (default)"))
        for wrong in ("99999", "-5", "lots", "1e6"):
            with self.subTest(wrong=wrong), self.assertRaises(project.SettingsError):
                project.cmd_handoff(wrong)


class Seat(Machine):
    """`seats.session` takes the three sources of the merge agent's seat."""

    def decided(self, lines: list[str], machine: dict) -> dict:
        raw = project.settings_of("\n".join(lines) + "\n", ROOT / project.SETTINGS, tuple(project.TABLES))
        return project.decide(ROOT, ROOT, raw, {}, raw, None, machine)["seats"]["session"]

    def test_the_repository_the_machine_or_the_agent(self):
        own = self.decided(["[seats]", 'session = "claude/m1:high"'], {"session": "claude/m2"})
        self.assertEqual((own["model"], own["effort"], own["from"]), ("m1", "high", str(project.SETTINGS)))
        mine = self.decided(["[branch]", 'base = "main"'], {"session": "claude/m2"})
        self.assertEqual((mine["model"], mine["effort"]), ("m2", None))
        self.assertTrue(mine["from"].endswith("machine.toml"))
        bare = self.decided(["[branch]", 'base = "main"'], {})
        self.assertEqual((bare["agent"], bare["model"], bare["effort"], bare["from"]), ("claude", "opus", "high", "Lem's default"))

    def test_only_claude_sits_there(self):
        with self.assertRaises(project.SettingsError) as raised:
            self.decided(["[seats]", 'session = "codex:high"'], {})
        self.assertIn("a task's session runs Claude Code only for now", str(raised.exception))

    def test_the_machine_file_takes_the_key(self):
        self.written('[seats]\nsession = "claude:high"\n')
        self.assertEqual(lem_state.machine_table("seats"), {"session": "claude:high"})


class Phase(unittest.TestCase):
    def test_the_phase_comes_from_the_state(self):
        cases = [
            ((None, None, None, False), "shape"),
            (("held", "the interview waits for the owner", "standard", False), "shape"),
            (("held", "the criteria wait for the owner's yes", "standard", True), "shape"),
            (("held", "the criteria wait for the owner: the small change is a full change", "standard", True), "shape"),
            (("held", "breaker 2 waits for the owner", "standard", True), "build"),
            (("building", "lead: builder", "standard", True), "build"),
            (("planned", "the plan is committed", "standard", True), "build"),
            (("blocked", "the base is red", "standard", True), "build"),
            (("building", "small change: one builder", "fast", True), "fast"),
            (("open", "proposed", "fast", True), "fast"),
            (("landed", "merged", "fast", True), "fast"),
            (("ready", "the report is written", "standard", True), "land"),
            (("landing", "the checks run", "standard", True), "land"),
            (("open", "proposed", "standard", True), "land"),
            (("landed", "merged", "standard", True), "land"),
        ]
        for facts, phase in cases:
            with self.subTest(facts=facts):
                self.assertEqual(session.phase_of(SLUG, *facts, ""), phase)

    def test_a_task_queued_in_the_shape_goes_on_in_the_shape(self):
        # queued at step 7 of "The request": no lead ran, so its session takes step 8 there
        state = ('2026-11-21T10:01Z queued: the owner\'s order: "After coupon: unit cases"\nafter: coupon\nthen: the interview\n\n'
                 "2026-11-21T10:00Z held: the interview waits for the owner\ntype: test, because w")
        self.assertEqual(session.phase_of(SLUG, "queued", "the owner's order: \"After coupon: unit cases\"", "standard", False, state), "shape")
        need = "2026-11-21T10:00Z queued: needs the export's column\nafter: coupon\ninvestigation: bug"
        self.assertEqual(session.phase_of(SLUG, "queued", "needs the export's column", None, False, need), "shape")

    def test_a_task_its_lead_queued_goes_on_in_the_build(self):
        # a `lead:` line in any block, the first line's text or a line under it
        for older in ("2026-11-21T10:00Z building: lead: builder", "2026-11-21T10:00Z building: the plan starts\nlead: builder"):
            with self.subTest(older=older):
                state = f"2026-11-21T10:30Z queued: needs the export's column\nafter: coupon\n\n{older}"
                self.assertEqual(session.phase_of(SLUG, "queued", "needs the export's column", "standard", True, state), "build")

    def test_a_task_that_gets_no_session(self):
        for facts, says in ((("parked", "put aside", "standard", True), "is parked"), (("landed", "merged", "standard", False), "landed and cleaned"),
                            (("dropped", "nobody builds it", "standard", True), "is dropped"), (("answered", "the answer", None, False), "is answered")):
            with self.subTest(facts=facts), self.assertRaises(session.SessionError) as raised:
                session.phase_of(SLUG, *facts, "")
            self.assertIn(says, str(raised.exception))

    def test_a_queued_task_waits_for_its_after_task_until_that_one_ended(self):
        queued = {"slug": SLUG, "status": "queued", "state": "2026-11-21T10:00Z queued: needs the column\nafter: coupon"}
        self.assertEqual(session.queued_behind(queued, [queued, {"slug": "coupon", "status": "open"}]), "coupon")
        self.assertIsNone(session.queued_behind(queued, [queued, {"slug": "coupon", "status": "landed"}]))
        self.assertIsNone(session.queued_behind(queued, [queued, {"slug": "coupon", "status": "answered"}]))

    def test_a_task_queued_behind_a_dropped_task_waits_for_the_owners_word(self):
        queued = {"slug": "export-notes-in-order", "status": "queued",
                  "state": "2026-11-22T10:00Z queued: needs the gift note\nafter: gift-note-in-export"}
        dropped = {"slug": "gift-note-in-export", "status": "dropped"}
        self.assertEqual(session.queued_behind(queued, [queued, dropped]), "gift-note-in-export")
        said = session.behind_refusal("export-notes-in-order", "gift-note-in-export", "dropped")
        self.assertIn("'gift-note-in-export', which was dropped: it waits for the owner's word, which starts it or drops it", said)
        self.assertIn("lem project may-start export-notes-in-order", said)
        # his "start export-notes-in-order now" writes it queued again without the `after:` line
        started = dict(queued, state="2026-11-22T11:00Z queued: the owner's order was removed: \"start export-notes-in-order now\"\n\n" + queued["state"])
        self.assertIsNone(session.queued_behind(started, [started, dropped]))

    def test_the_after_line_is_read_from_every_line_its_first_too(self):
        # as `may-start` and the board read it: a block whose first line is `after: coupon`
        first = {"slug": SLUG, "status": "queued", "state": "2026-11-21T10:00Z queued: after: coupon\ntype: fix, because x\nthen: the fast track"}
        self.assertEqual(session.queued_behind(first, [first, {"slug": "coupon", "status": "building"}]), "coupon")
        nodes = [{"workspace": "W-coupon"}, {"workspace": "W-other"}]
        opens = {"coupon": {"workspace": "W-coupon", "ts": "2026-11-21T09:00:00Z"}, "other": {"workspace": "W-other", "ts": "2026-11-21T09:30:00Z"}}
        with mock.patch.object(session, "node_of", return_value=None):
            self.assertEqual(session.workspace_for(SLUG, first, opens, nodes, ""), "W-coupon")
        self.assertIsNone(session.after_of({"slug": SLUG, "status": "queued", "state": "2026-11-21T10:00Z queued: needs the column"}))


    def test_the_phase_that_ends_is_the_states_and_not_the_one_the_session_opened_in(self):
        def block(status: str, text: str) -> dict:
            return {"status": status, "text": text}
        # a session that opened for the shape and led the task through the build hands off from the build
        led = [block("building", "lead: builder"), block("building", "task 2 of 2"), block("ready", "the report is written")]
        self.assertEqual(session.phase_left(SLUG, led, "standard", "land", "shape", ""), "build")
        # a session that wrote the build's first block hands off from the phase it opened in
        self.assertEqual(session.phase_left(SLUG, [block("building", "lead: builder")], "standard", "build", "shape", ""), "shape")
        # a session that wrote nothing since it opened: its own phase, so `next` refuses while the state gives it
        self.assertEqual(session.phase_left(SLUG, [], "standard", "build", "build", ""), "build")
        # a park in between gives no phase
        self.assertEqual(session.phase_left(SLUG, [block("building", "x"), block("parked", "aside"), block("ready", "y")], "standard", "land", "build", ""), "build")
        # a queued block is the shape's when no lead ran for the task, and the build's when one did
        queued = [block("queued", "needs the column")]
        self.assertEqual(session.phase_left(SLUG, queued, "standard", "land", "build", ""), "shape")
        self.assertEqual(session.phase_left(SLUG, queued, "standard", "land", "shape", "2026-11-21T10:00Z building: lead: builder"), "build")

class FirstLine(unittest.TestCase):
    """`wait --first-line`: the task's first line for the session where the owner typed the request,
    or null with the reason."""

    def state(self, status: str, text: str, *lines: str, **more) -> dict:
        return {"event": "task.state", "task": SLUG, "status": status, "text": text, "lines": list(lines), **more}

    def test_the_line_in_the_form_for_another_session(self):
        said = self.state("building", "small change: one builder", "type: fix, because x", say="fix: x.", say_named="gift-note · fix: x.")
        asked = self.state("held", "the request waits for one answer")
        self.assertEqual(session.first_line_end(SLUG, [asked, said], False), {"task": SLUG, "say": "gift-note · fix: x.", "gone": False})
        # the one question of the request has no type and no line: the wait goes on
        self.assertIsNone(session.first_line_end(SLUG, [asked], False))
        self.assertIsNone(session.first_line_end(SLUG, [], False))

    def test_a_block_no_line_will_follow(self):
        typed = self.state("building", "small change: one builder", "type: docs, because a line")
        night = session.first_line_end(SLUG, [typed], True)
        self.assertEqual((night["say"], night["gone"]), (None, False))
        self.assertIn("a task of the night", night["why"])
        self.assertIn("has no line", session.first_line_end(SLUG, [typed], False)["why"])
        # the hold of an order that named no task: his answer brings the line, in the task's own session
        held = session.first_line_end(SLUG, [self.state("held", 'the order waits for the owner: "After the gift note"', "type: feat, because x")], False)
        self.assertEqual((held["say"], held["gone"]), (None, False))
        self.assertIn(f"{SLUG} is held: the order waits for the owner", held["why"])
        self.assertIn("comes with his answer", held["why"])
        for status in ("dropped", "answered", "landed", "parked"):
            ended = session.first_line_end(SLUG, [self.state("held", "the request waits for one answer"), self.state(status, "the owner dropped it")], False)
            self.assertEqual(ended["say"], None, status)
            self.assertIn(f"{SLUG} is {status} before its first line", ended["why"])

    def run_wait(self, records: list[dict], gone: dict | None, bound: float) -> dict:
        with mock.patch.object(session, "place", return_value={"session": "", "socket": "", "window": ""}), \
             mock.patch.object(session, "gone_session", return_value=gone), \
             mock.patch.object(project, "task_directory", return_value=Path("/lem-unit/task")), \
             mock.patch.object(project, "events_named", side_effect=lambda root, *names: [r for r in records if r["event"] in names]):
            return session.cmd_first_line(ROOT, SLUG, 0.01, bound)

    def test_a_gone_session_and_the_bound(self):
        gone = self.run_wait([], {"session": "S-9", "name": SLUG}, 60)
        self.assertEqual((gone["say"], gone["gone"], gone["session"]), (None, True, "S-9"))
        self.assertIn(f"`lem session open {SLUG} --why dead`", gone["why"])
        late = self.run_wait([self.state("held", "the request waits for one answer")], None, 0.05)
        self.assertEqual((late["say"], late["gone"]), (None, False))
        self.assertIn(f"no first line of {SLUG} came in", late["why"])
        self.assertEqual(session.FIRST_LINE_BOUND, 600)
        said = self.run_wait([self.state("held", "the interview waits", "type: feat, because y", say="feat.", say_named="gift-note · feat.")], None, 60)
        self.assertEqual(said["say"], "gift-note · feat.")


class Close(unittest.TestCase):
    OPENS = [{"event": "session.open", "task": SLUG, "session": "S-1"}, {"event": "session.open", "task": "other-task", "session": "S-7"},
             {"event": "session.open", "task": SLUG, "session": "S-2"}]

    def close(self, session_id: str) -> tuple[dict, list]:
        closed = []
        with mock.patch.object(session, "place", return_value={"session": "", "socket": "", "window": ""}), \
             mock.patch.object(session, "tree", return_value={}), \
             mock.patch.object(session, "node_of", return_value={"name": "x", "active": False}), \
             mock.patch.object(session, "ctl", side_effect=lambda where, *args: closed.append(args)), \
             mock.patch.object(project, "append_event"), \
             mock.patch.object(project, "task_directory", return_value=Path("/lem-unit/task")), \
             mock.patch.object(project, "events_named", side_effect=lambda root, *names: [r for r in self.OPENS if r["event"] in names]):
            return session.cmd_close(ROOT, SLUG, session_id, "handoff", False, 0.01), closed

    def test_a_close_by_id_closes_only_a_session_of_that_task(self):
        with self.assertRaises(session.SessionError) as raised:
            self.close("S-7")
        self.assertIn("S-7 is no session of gift-note", str(raised.exception))
        self.assertIn("other-task", str(raised.exception))
        with self.assertRaises(session.SessionError):
            self.close("S-404")
        # an older session of the same task is its own: a handoff closes its predecessor, in any case of the id
        done, closed = self.close("s-1")
        self.assertTrue(done["closed"])
        self.assertEqual(closed, [("session", "close", "--target", "s-1", "--undoable")])


class Agent(unittest.TestCase):
    def test_an_agent_in_the_left_pane(self):
        self.assertTrue(session.agent_runs({"foreground": ["/usr/local/bin/claude", "--resume", "x"]}))
        self.assertTrue(session.agent_runs({"foreground": ["node", "/opt/lib/claude"]}))
        self.assertFalse(session.agent_runs({"foreground": ["/opt/homebrew/bin/fish"], "realized": True}))
        self.assertFalse(session.agent_runs({"realized": True}))
        self.assertIsNone(session.agent_runs({"realized": False}))

    def test_the_launch_lines_shell_runs_the_agent_in_its_command(self):
        # agterm's tree for a live task session that Claude Code held idle (lem-scratch, 2026-11-21)
        ground = ["/opt/homebrew/bin/fish", "-l", "-c", "LEM_TASK=profile-names-working-days CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude --model opus --effort high \"Read /x/session.md and follow it.\""]
        self.assertTrue(session.agent_runs({"foreground": ground, "realized": True}))
        now = datetime(2026, 11, 21, 10, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(session.live({"foreground": ground}, {"ts": "2026-11-21T08:00:00Z"}, now))
        # the line launch_line builds reads the same way
        line = session.launch_line("/bin/zsh", SLUG, Path("/r/session.md"), 600_000, {"agent": "claude", "model": None, "effort": None})
        self.assertTrue(session.agent_runs({"foreground": shlex.split(line)}))

    def test_a_shell_whose_command_is_no_agent_or_cannot_be_read(self):
        self.assertFalse(session.agent_runs({"foreground": ["/bin/zsh", "-l"], "realized": True}))
        self.assertFalse(session.agent_runs({"foreground": ["/bin/sh", "-c", "LEM_TASK=x htop"]}))
        self.assertFalse(session.agent_runs({"foreground": ["/bin/sh", "-c", "echo claude"]}))
        # an unclosed quote: a plain word that is an agent's file still counts, and none does not
        self.assertTrue(session.agent_runs({"foreground": ["/bin/sh", "-c", "LEM_TASK=x claude \"Read"]}))
        self.assertFalse(session.agent_runs({"foreground": ["/bin/sh", "-c", "LEM_TASK=x htop \"Read"]}))

    def test_a_session_counts_while_its_agent_starts(self):
        now = datetime(2026, 11, 21, 10, 0, 0, tzinfo=timezone.utc)
        opened = {"ts": (now - timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        shell = {"foreground": ["/bin/zsh"]}
        self.assertTrue(session.live(shell, opened, now))
        self.assertFalse(session.live(shell, opened, now + timedelta(seconds=session.STARTING)))
        self.assertFalse(session.live(None, opened, now))


class Launch(unittest.TestCase):
    BRIEF = Path("/lem-unit/repo/.lem/state/tasks/gift-note/session.md")

    def test_the_line_holds_the_task_the_number_and_the_seat_only_where_named(self):
        line = session.launch_line("/bin/zsh", SLUG, self.BRIEF, 600_000, {"agent": "claude", "model": None, "effort": None})
        self.assertEqual(line, f"/bin/zsh -l -c 'LEM_TASK={SLUG} CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude \"Read {self.BRIEF} and follow it.\"'")
        seated = session.launch_line("/bin/zsh", SLUG, self.BRIEF, None, {"agent": "claude", "model": "m1", "effort": "high"})
        self.assertIn(f"'LEM_TASK={SLUG} claude --model m1 --effort high \"Read", seated)
        self.assertNotIn("CLAUDE_CODE_AUTO_COMPACT_WINDOW", seated)

    def test_a_lem_that_is_not_the_installed_plugin_names_its_folder(self):
        home = {"CLAUDE_CONFIG_DIR": "/lem-unit/claude"}
        self.assertIsNone(session.plugin_dir(Path("/lem-unit/claude/plugins/cache/lem/lem/1.2.0"), home))
        self.assertEqual(session.plugin_dir(Path("/lem-unit/clones/lem"), home), "/lem-unit/clones/lem")
        line = session.launch_line("/bin/zsh", SLUG, self.BRIEF, None, {}, "/lem-unit/clones/lem")
        self.assertIn(' claude --plugin-dir /lem-unit/clones/lem "Read ', line)
        self.assertNotIn("--plugin-dir", session.launch_line("/bin/zsh", SLUG, self.BRIEF, None, {}, None))

    def test_a_path_the_line_cannot_carry_is_refused(self):
        # fish reads a backslash inside single quotes as an escape, so no quoting carries one to every shell
        with self.assertRaises(session.SessionError) as raised:
            session.launch_line("/bin/zsh", SLUG, Path("/tmp/o\\neil/session.md"), None, {})
        self.assertIn("move the checkout to a path without them", str(raised.exception))

    # the shells that may read the line: agterm's outer level, and the owner's login shell inside it
    SHELLS = {"bash": ["--norc", "--noprofile", "-c"], "zsh": ["-f", "-c"], "fish": ["--no-config", "-c"]}

    def through_each_shell(self, seat: dict, folder: str) -> None:
        """Run the launch line through each shell this machine has, at both of its levels, with a
        stand-in for the login shell that says its argv and a stand-in claude that says its own."""
        import shutil
        root = Path(tempfile.mkdtemp(prefix="lem-launch-"))
        self.addCleanup(shutil.rmtree, root)
        tools = root / "bin"
        tools.mkdir()
        for name in ("claude", "outer"):
            (tools / name).write_text(f"#!{sys.executable}\nimport json, os, sys\nprint(json.dumps([os.environ.get('LEM_TASK'), *sys.argv[1:]]))\n")
            (tools / name).chmod(0o755)
        brief = root / folder / ".lem" / "state" / "tasks" / SLUG / "session.md"
        plugin = str(root / folder / "lem")
        shells = {name: (found, flags) for name, flags in self.SHELLS.items() if (found := shutil.which(name))}
        self.assertIn("bash", shells, "bash is on every machine the launch line runs on")
        line = session.launch_line(str(tools / "outer"), SLUG, brief, None, seat, plugin)
        env = {"PATH": f"{tools}:/usr/bin:/bin", "HOME": str(root)}
        wanted = [SLUG] + [word for flag in ("model", "effort") if seat.get(flag) for word in (f"--{flag}", seat[flag])]
        wanted += ["--plugin-dir", plugin, f"Read {brief} and follow it."]
        for outer, (path, flags) in shells.items():
            said = subprocess.run([path, *flags, line], capture_output=True, text=True, env=env, cwd=root, check=False)
            self.assertEqual((said.returncode, said.stderr), (0, ""), f"{outer} at the outer level")
            got = json.loads(said.stdout)
            self.assertEqual(got[1:], shlex.split(line)[1:], f"{outer} reads the outer level as the POSIX tokenizer does")
            self.assertEqual(got[1:3], ["-l", "-c"])
            for inner, (inner_path, inner_flags) in shells.items():
                ran = subprocess.run([inner_path, *inner_flags, got[3]], capture_output=True, text=True, env=env, cwd=root, check=False)
                self.assertEqual((ran.returncode, ran.stderr), (0, ""), f"{inner} inside {outer}")
                self.assertEqual(json.loads(ran.stdout), wanted, f"{inner} inside {outer}")
        self.assertTrue(session.agent_runs({"foreground": ["/bin/zsh", "-l", "-c", shlex.split(line)[3]]}))

    def test_a_model_with_brackets_reaches_the_agent_whole_in_every_login_shell(self):
        # zsh, the default login shell of macOS, stops a bare `opus[1m]` with "no matches found"
        self.through_each_shell({"agent": "claude", "model": "opus[1m]", "effort": "high"}, "repo")

    def test_a_checkout_path_with_an_apostrophe_and_a_space_reaches_the_agent_whole(self):
        self.through_each_shell({"agent": "claude", "model": "opus", "effort": None}, "o'neil's work")


class Handoff(unittest.TestCase):
    def test_a_handoff_in_its_form(self):
        found = session.handoff_form(HANDOFF, SLUG)
        self.assertEqual((found["from"], found["written"]), ("shape", "2026-11-21T10:05Z"))
        self.assertEqual(found["changed"], [{"path": "docs/plans/2026-11-21-gift-note.md", "status": "added, not committed"},
                                            {"path": "src/export.py", "status": "changed in 1a2b3c4"}])
        none = HANDOFF.split("## Changed files")[0] + "## Changed files\n\nnone\n"
        self.assertEqual(session.handoff_form(none, SLUG)["changed"], [])

    def test_the_template_reads_as_a_form_once_filled(self):
        template = (SCRIPTS.parent / "templates" / "handoff.md").read_text(encoding="utf-8")
        filled = template.replace("SLUG", SLUG).replace("PHASE", "build").replace("YYYY-MM-DDTHH:MMZ", "2026-11-21T10:05Z")
        self.assertEqual(session.handoff_form(filled, SLUG)["changed"], [{"path": "PATH/FROM/THE/ROOT", "status": "STATUS"}])

    def test_each_missing_part_is_named(self):
        cases = [
            (HANDOFF.replace("task: gift-note · from shape", "task: gift-note · from talk"), "a phase is one of"),
            (HANDOFF.replace("task: gift-note", "task: coupon"), "names the task 'coupon'"),
            ("## Settled\n\n- x\n", "a first line `task: gift-note · from PHASE"),
            (HANDOFF.replace("## Failed\n\n- none\n", ""), "## Failed"),
            (HANDOFF.replace("## Open\n\nnone\n", "## Open\n\n"), "## Open"),
            (HANDOFF + "- the export, somewhere\n", "a path and a status on each line of ## Changed files"),
        ]
        for text, says in cases:
            with self.subTest(says=says), self.assertRaises(session.SessionError) as raised:
                session.handoff_form(text, SLUG)
            self.assertIn(says, str(raised.exception))
            self.assertIn("templates/handoff.md", str(raised.exception))


class Hooks(unittest.TestCase):
    """The hooks as Claude Code starts them, in a throwaway repository: silent with exit 0 outside a task session."""

    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.repo = Path(cls.folder.name) / "shop"
        subprocess.run(["git", "init", "-q", str(cls.repo)], check=True)
        state = cls.repo / ".lem" / "state"
        directory = state / "tasks" / SLUG
        directory.mkdir(parents=True)
        (directory / "state.md").write_text("2026-11-21T10:06Z building: lead: builder\ntype: feat, because the export gets a column\n\n"
                                            "2026-11-21T09:00Z held: the interview waits for the owner\n", encoding="utf-8")
        (directory / "handoff.md").write_text(HANDOFF, encoding="utf-8")
        (state / "events.jsonl").write_text(json.dumps({"ts": "2026-11-21T10:07:00Z", "event": "session.open", "task": SLUG, "phase": "build"}) + "\n", encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def hook(self, event: dict, task: str | None = SLUG) -> subprocess.CompletedProcess:
        env = {key: value for key, value in os.environ.items() if key != "LEM_TASK"}
        if task:
            env["LEM_TASK"] = task
        return subprocess.run([sys.executable, "-B", str(SCRIPTS / "session_hook.py")], input=json.dumps({"cwd": str(self.repo), **event}),
                              capture_output=True, text=True, env=env, check=False)

    def test_without_a_task_each_hook_is_silent(self):
        for event in ({"hook_event_name": "PreCompact", "trigger": "auto"}, {"hook_event_name": "SessionStart", "source": "compact"}):
            for task in (None, "no-such-task", "Not A Slug"):
                with self.subTest(event=event["hook_event_name"], task=task):
                    ran = self.hook(event, task)
                    self.assertEqual((ran.returncode, ran.stdout, ran.stderr), (0, "", ""))

    def test_the_summary_gets_the_handoffs_form(self):
        ran = self.hook({"hook_event_name": "PreCompact", "trigger": "auto"})
        self.assertEqual(ran.returncode, 0)
        self.assertEqual(ran.stdout.strip(), session_hook.instructions(SLUG, "build"))
        self.assertIn("task gift-note, phase build, under five headings: Settled; Open; Next step; Failed; Changed files", ran.stdout)

    def test_after_a_compaction_the_state_and_the_handoff_come_back(self):
        ran = self.hook({"hook_event_name": "SessionStart", "source": "compact"})
        self.assertEqual(ran.returncode, 0)
        self.assertIn(session_hook.TRUTH, ran.stdout)
        self.assertIn("2026-11-21T10:06Z building: lead: builder\ntype: feat, because the export gets a column\n", ran.stdout)
        self.assertNotIn("the interview waits", ran.stdout)
        self.assertIn("## handoff.md, written 20", ran.stdout)
        self.assertIn("The lead plans the export's column.", ran.stdout)
        started = self.hook({"hook_event_name": "SessionStart", "source": "startup"})
        self.assertEqual((started.returncode, started.stdout), (0, ""))

    def test_each_claude_session_of_the_task_is_logged_once(self):
        log = self.repo / ".lem" / "state" / "events.jsonl"
        before = log.read_text(encoding="utf-8")
        event = {"hook_event_name": "SessionStart", "source": "startup", "session_id": "c0ffee-1", "transcript_path": "/x/projects/-shop/c0ffee-1.jsonl"}
        try:
            for _ in range(2):
                ran = self.hook(event)
                self.assertEqual((ran.returncode, ran.stdout), (0, ""))
            self.hook({**event, "source": "compact"})
            self.hook({"hook_event_name": "SessionStart", "source": "startup"}, task="no-such-task")
            records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()[len(before.splitlines()):]]
            self.assertEqual([(r["event"], r["task"], r["claude"], r["transcript"], r["source"]) for r in records],
                             [("session.transcript", SLUG, "c0ffee-1", "/x/projects/-shop/c0ffee-1.jsonl", "startup")])
        finally:
            log.write_text(before, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
