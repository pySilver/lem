"""The four files of Lem's settings, as calls of the functions that hold their rules: where each table is
valid (`lem_state.TABLE_PLACES`), which file wins for a setting more than one may hold (`project.decide`),
and how `machine.toml` is written (`lem_state.write_machine`). Which checkout supplies a repository's two
files is a fact only git shows, and tests/lem-settings.sh checks it with `lem project show`.

    python3 -B -m unittest discover -s tests/unit
"""

import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
import lem_state  # noqa: E402
import project  # noqa: E402

ROOT = Path("/lem-unit/repo")


class Home(unittest.TestCase):
    """Each case runs with a folder of its own as XDG_CONFIG_HOME: the home directory's files are never read."""

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

    def written(self, text: str) -> Path:
        file = lem_state.machine_file()
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        return file

    def refused(self, call, *args) -> str:
        with self.assertRaises((project.SettingsError, lem_state.StateError)) as caught:
            call(*args)
        return str(caught.exception)


def read(place: str, *lines: str) -> dict:
    return project.settings_of("\n".join(lines) + "\n", Path(place), place)


class Places(Home):
    """A table in a file where it is not valid is refused, and the refusal names the file where it is
    (criteria 3 and 4 of one-home-folder-for-lem)."""

    def test_what_guards_a_team_is_valid_in_the_teams_file_only(self):
        for table, line in (("flow", "topics = []"), ("checks", "commands = []"), ("branch", 'base = "main"'), ("paths", 'plans = "docs/plans"'),
                            ("tracker", 'kind = "linear"')):
            self.assertEqual(read("team", f"[{table}]", line), {table: tomllike(line)})
            for place in ("home", "local"):
                with self.subTest(table=table, place=place):
                    message = self.refused(read, place, f"[{table}]", line)
                    self.assertIn(f"{place}: [{table}] is not valid in this file: its place is .lem/settings.toml; move the table there", message)

    def test_keep_days_is_a_repositorys_and_refused_in_the_home_file(self):
        self.assertEqual(read("team", "[state]", "keep_days = 7"), {"state": {"keep_days": 7}})
        self.assertEqual(read("local", "[state]", "keep_days = 3"), {"state": {"keep_days": 3}})
        message = self.refused(read, "home", "[state]", "keep_days = 3")
        self.assertIn("[state] is not valid in this file: its place is .lem/settings.toml or .lem/settings.local.toml", message)

    def test_the_home_file_holds_the_merge_agent_and_the_session_of_the_seats(self):
        self.assertEqual(read("home", "[seats]", 'merger = "claude/opus:high"', 'session = "claude"'), {"seats": {"merger": "claude/opus:high", "session": "claude"}})
        for key in ("reviewer", "planner", "experts"):
            with self.subTest(key=key):
                message = self.refused(read, "home", "[seats]", f'{key} = "claude/opus:high"')
                self.assertIn(f"seats.{key} is not valid in this file, which holds only merger and session of [seats]: its place is .lem/settings.toml or .lem/settings.local.toml", message)

    def test_the_question_pages_defaults_are_the_home_files_only(self):
        self.assertEqual(read("home", "[ask]", 'style = "minimal"'), {"ask": {"style": "minimal"}})
        self.assertIn("unknown key ask.colour", self.refused(read, "home", "[ask]", 'colour = "red"'))
        for place in ("team", "local"):
            with self.subTest(place=place):
                self.assertIn(f"[ask] is not valid in this file: its place is {project.home_name()}", self.refused(read, place, "[ask]", 'style = "minimal"'))

    def test_what_is_true_for_the_whole_machine_is_its_files_only(self):
        for table, line in (("load", "start = 4"), ("serve", "port = 4500"), ("peers", "mini = 4600"), ("handoff", "tokens = 0"), ("corrections", "collect = false")):
            for place in ("home", "team", "local"):
                with self.subTest(table=table, place=place):
                    self.assertIn(f"[{table}] is not valid in this file: its place is {lem_state.shown(lem_state.machine_file())}", self.refused(read, place, f"[{table}]", line))

    def test_the_machines_file_refuses_the_seats_and_names_the_home_settings(self):
        file = self.written('[load]\nstart = 4\n\n[seats]\nmerger = "claude/opus:high"\n')
        for call in (lem_state.machine_tables, lem_state.load_start, lem_state.handoff_tokens):
            with self.subTest(call=call.__name__):
                message = self.refused(call)
                self.assertIn(f"{file}: [seats] is not valid in this file: its place is {lem_state.shown(lem_state.home_settings_file())}", message)

    def test_a_name_of_the_home_folder_is_written_from_the_home_directory(self):
        self.assertEqual(lem_state.shown(Path.home() / ".config" / "lem" / "settings.toml"), "~/.config/lem/settings.toml")
        self.assertEqual(lem_state.shown(Path("/elsewhere/lem/settings.toml")), "/elsewhere/lem/settings.toml")


def tomllike(line: str) -> dict:
    import tomllib
    return tomllib.loads(line)


class Nearest(Home):
    """For a setting more than one file may hold, the nearest file that holds it wins, and `from` names it
    (criterion 2 of one-home-folder-for-lem)."""

    def decided(self, team: tuple = (), local: tuple = (), home: tuple = ()) -> dict:
        raw = read("team", *team)
        return project.decide(ROOT, ROOT, raw, read("local", *local), raw, None, read("home", *home))

    def merger(self, **files) -> tuple:
        found = self.decided(**files)["seats"]["merger"]
        return found["seat"], found["from"]

    def test_the_merge_agent_from_the_local_the_team_the_home_file_or_lem(self):
        home = ("[seats]", 'merger = "claude/opus:high"')
        team = ("[seats]", 'merger = "codex/gpt-6.2-sol:high"')
        local = ("[seats]", 'merger = "claude/fable:high"')
        self.assertEqual(self.merger(home=home, team=team), ("codex/gpt-6.2-sol:high", ".lem/settings.toml"))
        self.assertEqual(self.merger(home=home, team=team, local=local), ("claude/fable:high", ".lem/settings.local.toml"))
        self.assertEqual(self.merger(home=home), ("claude/opus:high", project.home_name()))
        self.assertEqual(self.merger(), ("claude/opus:high", "Lem's default"))

    def test_each_seat_and_each_expert_names_its_file(self):
        found = self.decided(team=("[seats]", 'reviewer = "codex/gpt-6.2-sol:high"'), local=("[seats]", 'planner = "claude/fable:high"'),
                             home=("[seats]", 'session = "claude:high"'))["seats"]
        self.assertEqual({which: found[which]["from"] for which in ("reviewer", "planner", "merger", "session")},
                         {"reviewer": ".lem/settings.toml", "planner": ".lem/settings.local.toml", "merger": "Lem's default", "session": project.home_name()})
        self.assertEqual({expert["from"] for expert in found["experts"]}, {"Lem's default"})
        mine = self.decided(team=("[seats]", 'experts = ["claude/opus:high"]'), local=("[seats]", 'experts = ["claude/fable:high"]'))["seats"]["experts"]
        self.assertEqual([(expert["seat"], expert["from"]) for expert in mine], [("claude/fable:high", ".lem/settings.local.toml")])

    def test_the_naps_and_the_days_name_their_file(self):
        found = self.decided()
        self.assertEqual((found["naps"], found["state"]), ({"on": False, "from": "Lem's default"}, {"keep_days": 30, "from": "Lem's default"}))
        found = self.decided(team=("[naps]", "on = true", "[state]", "keep_days = 7"))
        self.assertEqual((found["naps"], found["state"]), ({"on": True, "from": ".lem/settings.toml"}, {"keep_days": 7, "from": ".lem/settings.toml"}))
        found = self.decided(team=("[naps]", "on = true", "[state]", "keep_days = 7"), local=("[naps]", "on = false", "[state]", "keep_days = 3"))
        self.assertEqual((found["naps"], found["state"]), ({"on": False, "from": ".lem/settings.local.toml"}, {"keep_days": 3, "from": ".lem/settings.local.toml"}))
        self.assertEqual(found["local"]["overrides"], ["naps.on", "state.keep_days"])


class MachineFile(Home):
    """`write_machine` keeps every table of `machine.toml`, the correction queue's too, writes over nothing
    it cannot keep, and holds the file's lock from its read to its rename (criterion 3)."""

    def test_it_keeps_the_corrections_when_it_writes_another_table(self):
        self.written("[corrections]\ncollect = false\n\n[serve]\nport = 4500\n")
        lem_state.write_machine("load", {"start": 12})
        self.assertEqual(lem_state.machine_tables(), {"load": {"start": 12}, "serve": {"port": 4500}, "corrections": {"collect": False}})
        self.assertEqual(lem_state.machine_table("corrections"), {"collect": False})

    def test_a_file_with_the_seats_stays_as_it_is_and_the_refusal_names_their_place(self):
        text = '[load]\nstart = 4\n\n[seats]\nmerger = "claude/opus:high"\n'
        file = self.written(text)
        message = self.refused(lem_state.write_machine, "load", {"start": 12})
        self.assertIn(f"{file}: [seats] is not valid in this file: its place is {lem_state.shown(lem_state.home_settings_file())}", message)
        self.assertEqual(file.read_text(encoding="utf-8"), text)

    def test_a_file_that_does_not_read_stays_as_it_is_and_the_refusal_names_it(self):
        for text, says in (("[load\nstart = 4\n", "does not read as TOML"), ("[colours]\nmain = 1\n", "[colours] is no table of Lem's"),
                           ("[load]\nbegin = 4\n", "load.begin"), ("[corrections]\ncollect = 1\n", "corrections.collect")):
            with self.subTest(text=text):
                file = self.written(text)
                message = self.refused(lem_state.write_machine, "serve", {"port": 4500})
                self.assertIn(str(file), message)
                self.assertIn(says, message)
                self.assertEqual(file.read_text(encoding="utf-8"), text)

    def test_the_last_table_out_takes_the_file(self):
        self.written("[handoff]\ntokens = 0\n")
        lem_state.write_machine("handoff", None)
        self.assertFalse(lem_state.machine_file().exists())

    def test_a_second_writer_waits_for_the_lock_and_keeps_the_first_ones_table(self):
        self.written("[serve]\nport = 4500\n")
        done = threading.Event()

        def second():
            lem_state.write_machine("handoff", {"tokens": 0})
            done.set()

        with lem_state.machine_lock():
            writer = threading.Thread(target=second)
            writer.start()
            # time for the second writer to reach its read; with the lock, whatever the timing, it reads only
            # after this holder wrote, and keeps the table this holder added
            time.sleep(0.3)
            self.assertFalse(done.is_set())
            lem_state.machine_file().write_text("[serve]\nport = 4500\n\n[load]\nstart = 6\n", encoding="utf-8")
        writer.join(10)
        self.assertTrue((lem_state.config() / lem_state.MACHINE_LOCK).is_file())
        self.assertEqual(lem_state.machine_tables(), {"serve": {"port": 4500}, "load": {"start": 6}, "handoff": {"tokens": 0}})


if __name__ == "__main__":
    unittest.main()
