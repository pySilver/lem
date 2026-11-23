"""Lem's settings rules, as calls of the functions that hold them: what a settings file may say, what
`lem project show` refuses in one, and what it reads from one. Each rule here takes the tables that
were read and returns the settings or refuses; which checkout and which commit supply the tables is a
fact only git shows, and tests/lem-settings.sh checks it in real repositories.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import io
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
import project  # noqa: E402

# A checkout that is not on disk: the rules resolve paths under it and find nothing there.
ROOT = Path("/lem-unit/repo")
FILE = ROOT / project.SETTINGS


def read(*lines: str, name: Path = FILE, place: str = "team") -> dict:
    """The tables of a settings file of these lines, as `load` reads them: the team's file, unless
    PLACE names the local file or the home folder's."""
    return project.settings_of("\n".join(lines) + "\n", name, place)


def settings(*lines: str, local: dict | None = None) -> dict:
    """The settings of a main checkout on its base branch whose file holds these lines."""
    raw = read(*lines)
    return project.decide(ROOT, ROOT, raw, local or {}, raw, None)


class Refuses(unittest.TestCase):
    """A helper: the message of the SettingsError a call raises."""

    def refused(self, call, *args) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            call(*args)
        return str(caught.exception)

    def refused_settings(self, *lines: str) -> str:
        return self.refused(settings, *lines)

    def assertNames(self, message: str, *parts: str) -> None:
        for part in parts:
            self.assertIn(part, message)


class UnknownNames(Refuses):
    """A table or a key that Lem does not know is refused with its name, the file and the names it knows."""

    def test_a_key_with_the_nearest_valid_one(self):
        self.assertNames(self.refused(read, "[branch]", 'base = "master"', 'lands = "agent"'), str(FILE), "branch.lands", "did you mean 'land'")

    def test_a_way_to_land_with_no_pull_request(self):
        self.assertNames(self.refused(read, "[branch]", 'propose = "merge"'), str(FILE), "unknown key branch.propose", "valid: base, land, history, protected")

    def test_a_table(self):
        self.assertNames(self.refused(read, "[gate]", 'commands = ["make test"]'), str(FILE), "unknown table [gate]")

    def test_a_key_of_flow_with_the_keys_it_knows(self):
        self.assertNames(self.refused(read, "[flow]", 'careful = ["app/outbox/*"]'), str(FILE), "flow.careful", "valid: topics")

    def test_a_key_of_paths_with_the_keys_it_knows(self):
        message = self.refused(read, "[paths]", 'styleguide = ".lem/styleguide"')
        self.assertNames(message, str(FILE), "paths.styleguide", "valid: plans, plan_file, rulings")

    def test_a_ruling_file_line_with_the_nearest_key_and_the_keys_it_knows(self):
        message = self.refused(read, "[paths]", 'rulings = "docs/rulings.md"', 'ruling_file = "<slug>.md"')
        self.assertNames(message, str(FILE), "unknown key paths.ruling_file", "did you mean 'plan_file'?", "valid: plans, plan_file, rulings")

    def test_a_file_that_does_not_parse(self):
        self.assertIn(str(FILE), self.refused(read, "not toml ["))

    def test_a_seat_written_as_a_table_with_the_seat_form(self):
        message = self.refused_settings("[seats.reviewer]", 'agent = "codex"', 'model = "gpt-6.1-sol"')
        self.assertNames(message, "seats.reviewer", project.SEAT_FORM)


class Values(Refuses):
    """A wrong value of a key is refused with the key and the values it may take."""

    def test_land(self):
        self.assertNames(self.refused_settings("[branch]", 'land = "robot"'), "branch.land", "agent, owner")

    def test_history(self):
        self.assertNames(self.refused_settings("[branch]", 'history = "rewrite"'), "branch.history", "keep, squash")

    def test_an_empty_base(self):
        self.assertNames(self.refused_settings("[branch]", 'base = ""'), "branch.base", "names no branch")

    def test_a_protected_base(self):
        self.assertNames(self.refused_settings("[branch]", 'base = "master"', 'protected = ["master"]'), "branch.base", "branch.protected")

    def test_commands_that_are_no_list(self):
        self.assertNames(self.refused_settings("[checks]", 'commands = "pytest"'), "checks.commands", "list of strings")

    def test_an_empty_command(self):
        self.assertNames(self.refused_settings("[checks]", 'commands = ["make test", " "]'), "checks.commands", "empty command")

    def test_an_empty_setup_command(self):
        self.assertNames(self.refused_settings("[checks]", 'setup = [""]'), "checks.setup", "empty command")

    def test_topics_that_are_no_list(self):
        self.assertNames(self.refused_settings("[flow]", 'topics = "money"'), "flow.topics", "list of strings")

    def test_a_branch_defaults_to_squash_and_the_merge_agent(self):
        found = settings("[branch]", 'base = "master"')
        self.assertEqual((found["branch"]["history"], found["branch"]["land"]), ("squash", "agent"))
        self.assertEqual(sorted(found["branch"]), ["base", "history", "land", "protected"])
        self.assertEqual(sorted(found["checks"]), ["commands", "serial", "setup"])

    def test_a_branch_keeps_its_commits_and_its_owner_merges_when_the_file_says_so(self):
        found = settings("[branch]", 'base = "master"', 'history = "keep"', 'land = "owner"')
        self.assertEqual((found["branch"]["history"], found["branch"]["land"]), ("keep", "owner"))

    def test_topics_are_the_owner_sentences(self):
        found = settings("[flow]", 'topics = ["a price a customer pays", "data that cannot be rebuilt"]')
        self.assertEqual(found["flow"], {"topics": ["a price a customer pays", "data that cannot be rebuilt"]})


class TaskWorktree(Refuses):
    """In a task's worktree the branch's own file is read, but what must never go wrong and the naps are the
    base branch's: a branch does not lift what guards it. Which checkout and commit supply each table is
    tests/lem-settings.sh's; this is what the rule does with them."""

    TREE = ROOT / ".lem" / "worktrees" / "lift"
    COMMITTED = {"branch": "main", "commit": "0123456789abcdef"}

    def in_tree(self, branch: dict, on_base: dict) -> dict:
        return project.decide(self.TREE, ROOT, branch, {}, on_base, self.COMMITTED)

    def test_the_flow_and_the_naps_come_from_the_base(self):
        found = self.in_tree(
            read("[branch]", 'base = "main"', 'land = "agent"', "[flow]", "topics = []", "[naps]", "on = true"),
            read("[branch]", 'base = "main"', "[flow]", 'topics = ["a customer is charged the wrong price"]'),
        )
        self.assertEqual((found["flow"]["topics"], found["naps"]["on"], found["branch"]["land"]), (["a customer is charged the wrong price"], False, "agent"))
        self.assertEqual(found["settings_from"], "this worktree's branch, with [flow], [naps] and [state] from main@012345678")

    def test_the_days_the_state_keeps_come_from_the_base(self):
        found = self.in_tree(read("[state]", "keep_days = 1"), read("[state]", "keep_days = 14"))
        self.assertEqual(found["state"], {"keep_days": 14, "from": str(project.SETTINGS)})
        self.assertEqual(self.in_tree(read("[state]", "keep_days = 1"), {})["state"], {"keep_days": project.KEEP_DAYS, "from": "Lem's default"})
        self.assertNames(self.refused(self.in_tree, read("[state]", "keep_days = 0"), {}), "state.keep_days")

    def test_the_machines_own_days_hold_in_a_task_worktree_too(self):
        # the main checkout's local file, as `load` reads it for a worktree as well
        local = read("[state]", "keep_days = 3", name=project.LOCAL, place="local")
        found = project.decide(self.TREE, ROOT, read("[state]", "keep_days = 1"), local, read("[state]", "keep_days = 14"), self.COMMITTED)
        self.assertEqual((found["state"], found["local"]["overrides"]), ({"keep_days": 3, "from": str(project.LOCAL)}, ["state.keep_days"]))

    def test_the_branch_own_flow_is_still_checked(self):
        self.assertNames(self.refused(self.in_tree, read("[flow]", 'topics = "money"'), {}), "flow.topics")

    def test_a_wrong_naps_switch_on_the_base_names_the_base_commit(self):
        self.assertNames(self.refused(self.in_tree, {}, read("[naps]", 'on = "yes"')), "main:.lem/settings.toml", "naps.on")


def local(*lines: str) -> dict:
    """The tables of this machine's own file of these lines, as `load` reads them."""
    return read(*lines, name=project.LOCAL, place="local")


class KeepDays(Refuses):
    """How long the state folder keeps what Lem no longer needs: one whole number of days of the project's
    file, 30 by default, and one machine's own file may set its own number, which wins on that machine."""

    def test_the_default_is_the_owners_thirty(self):
        self.assertEqual((settings()["state"], project.KEEP_DAYS), ({"keep_days": 30, "from": "Lem's default"}, 30))
        self.assertEqual(settings("[state]", "keep_days = 7")["state"], {"keep_days": 7, "from": str(project.SETTINGS)})

    def test_a_number_that_is_no_whole_number_of_days_is_refused_with_the_fix(self):
        for value in ("0", "-3", "7.5", '"7"', "true"):
            self.assertNames(self.refused_settings("[state]", f"keep_days = {value}"), str(project.SETTINGS), "state.keep_days",
                             "a whole number of days, 1 or more", "keep_days = 30")

    def test_another_key_is_refused_in_either_file(self):
        self.assertNames(self.refused(read, "[state]", "days = 7"), "unknown key state.days", "keep_days")
        self.assertNames(self.refused(local, "[state]", "days = 7"), str(project.LOCAL), "unknown key state.days", "keep_days")

    def test_the_machines_own_number_wins_lower_or_higher(self):
        for project_lines, own, kept in ((("[state]", "keep_days = 30"), 7, 7), (("[state]", "keep_days = 7"), 60, 60), ((), 14, 14)):
            with self.subTest(own=own):
                found = settings(*project_lines, local=local("[state]", f"keep_days = {own}"))
                self.assertEqual(found["state"], {"keep_days": kept, "from": str(project.LOCAL)})
                self.assertEqual(found["local"]["overrides"], ["state.keep_days"])

    def test_the_machines_file_without_the_key_leaves_the_projects_number(self):
        found = settings("[state]", "keep_days = 7", local=local("[naps]", "on = false"))
        self.assertEqual((found["state"], found["local"]["overrides"]), ({"keep_days": 7, "from": str(project.SETTINGS)}, []))

    def test_a_wrong_number_in_the_machines_file_is_refused_by_that_file(self):
        for value in ("0", "-3", "7.5", '"7"', "true"):
            with self.subTest(value=value):
                message = self.refused(lambda: settings("[state]", "keep_days = 7", local=local("[state]", f"keep_days = {value}")))
                self.assertNames(message, f"{project.LOCAL}: state.keep_days", "a whole number of days, 1 or more", "keep_days = 30",
                                 f"leave the line out for the number of {project.SETTINGS}")

    def test_the_template_writes_the_key_with_its_source(self):
        self.assertIn("[state]", project.TEMPLATE)
        self.assertIn("keep_days = 30", project.TEMPLATE)
        words = " ".join(project.TEMPLATE.replace("# ", "").split())
        self.assertIn("The default, 30, is the owner's word of 2026-11-21, and the two constants it replaces, which were guesses.", words)


class Paths(Refuses):
    """A folder of [paths] stays inside the repository and is no root; a file name is a pattern of Lem's tokens."""

    def test_a_folder_that_leaves_the_repository(self):
        self.assertNames(self.refused_settings("[paths]", 'plans = "../elsewhere"'), "paths.plans", "leaves the repository")
        self.assertNames(self.refused_settings("[paths]", 'rulings = "../decisions"'), "paths.rulings", "'../decisions'", "leaves the repository")

    def test_an_absolute_folder(self):
        self.assertNames(self.refused_settings("[paths]", 'plans = "/elsewhere"'), "paths.plans", "relative to the root")

    def test_a_folder_that_is_the_root(self):
        self.assertNames(self.refused_settings("[paths]", 'plans = ""'), "paths.plans", "names the root of the checkout")

    def test_a_plan_file_pattern_lem_cannot_use(self):
        for bad, names in (
            ("YYYY-MM-DD.md", "<slug> once"),
            ("plans/<slug>.md", "no folder in it"),
            ("<slug>.txt", "end with .md"),
            ("<slug>-<date>.md", "a token Lem does not know"),
            ("<slug>-<slug>.md", "<slug> once"),
            ("", "a file name in quotes"),
            ("YYYY-YYYY-<slug>.md", "YYYY twice"),
        ):
            with self.subTest(bad=bad):
                self.assertNames(self.refused_settings("[paths]", f'plan_file = "{bad}"'), "paths.plan_file", repr(bad), names)



class Rulings(Refuses):
    """The rulings are one markdown file, `docs/rulings.md` unless the settings say otherwise; a folder is refused."""

    def test_the_default_is_one_file_and_no_ruling_file(self):
        paths = settings()["paths"]
        self.assertEqual(sorted(paths), ["plan_file", "plans", "rulings"])
        self.assertEqual(paths["rulings"]["path"], str(ROOT / "docs/rulings.md"))
        self.assertEqual(settings("[paths]", 'rulings = "decisions/list.md"')["paths"]["rulings"]["path"], str(ROOT / "decisions/list.md"))

    def test_the_folder_form_names_the_list_file_and_the_example(self):
        for value in ("docs/rulings", "docs/rulings/", "docs/rulings.txt"):
            with self.subTest(value=value):
                message = self.refused_settings("[paths]", f'rulings = "{value}"')
                self.assertNames(message, f"paths.rulings = {value!r}", "names the list file", 'rulings = "docs/rulings.md"')

    def test_a_folder_with_a_markdown_name(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs" / "rulings.md").mkdir(parents=True)
            raw = read("[paths]", 'rulings = "docs/rulings.md"')
            message = self.refused(project.decide, root, root, raw, {}, raw, None)
            self.assertNames(message, "paths.rulings = 'docs/rulings.md' is a folder", "names the list file", 'rulings = "docs/rulings.md"')

    def test_the_template_writes_the_list_file_with_its_comment_and_no_ruling_file(self):
        written = project.TEMPLATE.format_map({**{key: "" for key in ("plans", "plan_file", "base", "reviewer", "planner", "experts")}, "rulings": project.PATHS["rulings"]})
        self.assertIn('rulings = "docs/rulings.md"', written.splitlines())
        words = " ".join(written.replace("# ", "").split())
        self.assertIn("the list of your product decisions, one bullet for each", words)
        self.assertNotIn("ruling_file", written)


class Tracker(Refuses):
    """No table is no tracker; a table has one key, its kind, and any other key is unknown."""

    def tracker(self, *lines: str) -> dict | None:
        return settings("[tracker]", *lines)["tracker"] if lines else settings()["tracker"]

    def test_the_tables_it_takes(self):
        self.assertIsNone(self.tracker())
        self.assertEqual(self.tracker('kind = "linear"'), {"kind": "linear"})
        # criterion 1 of github-issues-tracker: GitHub Issues with no other key, the repository being origin's
        self.assertEqual(self.tracker('kind = "github"'), {"kind": "github"})

    def test_the_tables_it_refuses(self):
        for lines, names in (
            (('kind = "jira"',), ("tracker.kind", "'jira'", "linear", "github")),
            (('kind = ""',), ("tracker.kind",)),
            ((), ("[tracker] needs kind",)),
        ):
            with self.subTest(lines=lines):
                self.assertNames(self.refused(settings, "[tracker]", *lines), *names)

    def test_a_key_that_went_is_unknown(self):
        # Lem keeps no reading of the table's older form: a file that still names a status or a server is refused like any unknown key
        for key in ('server = "linear"', 'moves = "lem"', 'started = "In Progress"', 'landed = "Done"'):
            with self.subTest(key=key):
                self.assertNames(self.refused_settings("[tracker]", 'kind = "linear"', key), str(FILE), f"unknown key tracker.{key.split()[0]}")


class Home(Refuses):
    """Each case runs with a folder of its own as XDG_CONFIG_HOME, so the home folder's files are that folder's and
    the home directory's are never read or written."""

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


class Seats(Home):
    """A seat is one string, agent/model:effort. The reviewer's, the defender's, each expert's and the fallback's
    is written whole; the merge agent's and a task session's may leave out the effort, or the model and the effort.
    Each seat comes from the first of four places: this machine's own file for the repository, the team's file,
    the home folder's settings.toml, then Lem's default."""

    def home(self, *lines: str) -> dict:
        """The tables of a home folder's settings.toml of these lines, as `load` reads them; no lines, no file."""
        file = project.lem_state.home_settings_file()
        if lines:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            file.unlink(missing_ok=True)
        return project.read_settings(file, Path(project.home_name()), "home")

    def seats(self, project_lines: tuple[str, ...] = (), local_lines: tuple[str, ...] = (), home: dict | None = None) -> dict:
        """The seats of a repository whose two files hold these lines, on a machine whose home folder's settings.toml is `home`."""
        raw = read(*project_lines)
        return project.decide(ROOT, ROOT, raw, local(*local_lines), raw, None, home or {})["seats"]

    def test_each_seat_parsed(self):
        found = settings("[seats]", 'reviewer = "codex/gpt-6.1-sol:high"', 'planner = "claude/opus:max"', 'experts = ["claude/fable:high", "codex/gpt-6.2-astra:xhigh"]')["seats"]
        self.assertEqual(found["reviewer"], {"agent": "codex", "model": "gpt-6.1-sol", "effort": "high", "seat": "codex/gpt-6.1-sol:high", "from": str(project.SETTINGS)})
        self.assertEqual(found["planner"], {"agent": "claude", "model": "opus", "effort": "max", "seat": "claude/opus:max", "from": str(project.SETTINGS)})
        self.assertEqual([(e["agent"], e["model"], e["effort"], e["place"]) for e in found["experts"]], [("claude", "fable", "high", "fable"), ("codex", "gpt-6.2-astra", "xhigh", "astra")])

    def test_each_of_the_three_is_refused_unless_whole(self):
        # the owner, 2026-11-18: "I think it should be explicitly `agent/model:effort` in all 3; not simply "claude" or "codex""
        for which, given, missing, example in (
            ("reviewer", "codex", "no model and no effort", project.REVIEWER_SEATS["codex"]),
            ("reviewer", "codex:high", "no model", project.REVIEWER_SEATS["codex"]),
            ("reviewer", "codex/gpt-6.2-sol", "no effort", project.REVIEWER_SEATS["codex"]),
            ("reviewer", "codex/", "no model and no effort", project.REVIEWER_SEATS["codex"]),
            ("reviewer", "codex/gpt:", "no effort", project.REVIEWER_SEATS["codex"]),
            ("planner", "claude", "no model and no effort", project.PLANNER),
            ("planner", "claude/opus", "no effort", project.PLANNER),
        ):
            for name in (FILE, ROOT / project.LOCAL):
                with self.subTest(which=which, given=given, name=name):
                    message = self.refused(project.seat, {"seats": {which: given}}, name, which)
                    self.assertEqual(message, f'{name}: seats.{which} = {given!r} names {missing}: it is one string, "agent/model:effort", written whole, as "{example}"')

    def test_each_expert_is_refused_unless_whole(self):
        for given, number, missing in ((["claude/fable:high", "codex"], 1, "no model and no effort"), (["claude/fable"], 0, "no effort")):
            with self.subTest(given=given):
                message = self.refused(project.experts_of, {"seats": {"experts": given}}, FILE)
                self.assertEqual(message, f'{FILE}: seats.experts[{number}] = {given[number]!r} names {missing}: it is one string, "agent/model:effort", written whole, as "{project.EXPERTS[number]}"')

    def test_set_refuses_a_seat_that_is_not_whole(self):
        message = self.refused(project.set_value, "local", "reviewer", "claude")
        self.assertEqual(message, f'set local reviewer: seats.reviewer = \'claude\' names no model and no effort: it is one string, "agent/model:effort", written whole, as "{project.REVIEWER_SEATS["codex"]}"')

    def test_a_wrong_agent_is_named_before_the_parts_it_leaves_out(self):
        message = self.refused(project.seat, {"seats": {"planner": "codex"}}, FILE, "planner")
        self.assertNames(message, "the agent 'codex' must be claude")

    def test_the_merge_agents_seat_from_the_repository_the_home_file_or_the_agent(self):
        home = {"seats": {"merger": "codex/gpt-6.2-sol:high"}}
        raw = read("[seats]", 'merger = "claude/opus:high"')
        own = project.decide(ROOT, ROOT, raw, {}, raw, None, home)["seats"]["merger"]
        self.assertEqual((own["agent"], own["model"], own["effort"], own["from"]), ("claude", "opus", "high", str(project.SETTINGS)))
        raw = read("[branch]", 'base = "master"')
        mine = project.decide(ROOT, ROOT, raw, {}, raw, None, home)["seats"]["merger"]
        self.assertEqual((mine["agent"], mine["model"], mine["effort"], mine["from"]), ("codex", "gpt-6.2-sol", "high", project.home_name()))
        self.assertTrue(mine["from"].endswith("lem/settings.toml"))
        bare = project.decide(ROOT, ROOT, raw, {}, raw, None, {})["seats"]["merger"]
        self.assertEqual((bare["agent"], bare["model"], bare["effort"], bare["from"]), ("claude", "opus", "high", "Lem's default"))

    def test_the_merge_agents_seat_the_home_file_names_is_checked(self):
        raw = read("[branch]", 'base = "master"')
        message = self.refused(project.decide, ROOT, ROOT, raw, {}, raw, None, {"seats": {"merger": "gemini/pro"}})
        self.assertNames(message, "lem/settings.toml: seats.merger", "the agent 'gemini' must be claude or codex")

    def test_the_merge_agents_and_the_sessions_seat_may_leave_out_a_part(self):
        found = settings("[seats]", 'merger = "codex:high"', 'session = "claude"')["seats"]
        self.assertEqual((found["merger"]["agent"], found["merger"]["model"], found["merger"]["effort"]), ("codex", None, "high"))
        self.assertEqual((found["session"]["agent"], found["session"]["model"], found["session"]["effort"]), ("claude", None, None))

    def test_lem_defaults_with_no_seat(self):
        found = settings("[branch]", 'base = "master"')["seats"]
        self.assertEqual(found["reviewer"], {"agent": "claude", "model": "opus", "effort": "high", "seat": "claude/opus:high", "from": "Lem's default"})
        self.assertEqual((found["planner"]["seat"], found["planner"]["from"]), (project.PLANNER, "Lem's default"))
        self.assertEqual([(e["seat"], e["from"]) for e in found["experts"]], [(one, "Lem's default") for one in project.EXPERTS])
        self.assertEqual(found["fallback"], {"agent": "claude", "model": "opus", "effort": "high", "seat": "claude/opus:high", "from": "Lem's default"})

    def test_a_repository_that_names_no_reviewer_takes_the_machines_then_lems(self):
        # criterion 1: the home folder's settings.toml names the reviewer, and notes-app names none in its two files
        notes_app = ("[branch]", 'base = "main"')
        reviewer = self.seats(notes_app, home=self.home("[seats]", 'reviewer = "codex/gpt-6.2-sol:high"'))["reviewer"]
        self.assertEqual((reviewer["seat"], reviewer["from"]), ("codex/gpt-6.2-sol:high", project.home_name()))
        # with no reviewer line in that file either, Lem's own
        reviewer = self.seats(notes_app, home=self.home())["reviewer"]
        self.assertEqual((reviewer["seat"], reviewer["from"]), ("claude/opus:high", "Lem's default"))

    def test_each_seat_from_each_of_the_four_places(self):
        for which, local_line, project_line, home_value in (
            ("reviewer", 'reviewer = "codex/l:high"', 'reviewer = "codex/p:high"', "codex/m:high"),
            ("planner", 'planner = "claude/l:high"', 'planner = "claude/p:high"', "claude/m:high"),
            ("merger", 'merger = "codex/l"', 'merger = "codex:high"', "codex/m:low"),
            ("session", 'session = "claude/l"', 'session = "claude:max"', "claude"),
        ):
            home = {"seats": {which: home_value}}
            for local_lines, project_lines, given, seat, place in (
                (("[seats]", local_line), ("[seats]", project_line), home, local_line.split('"')[1], str(project.LOCAL)),
                ((), ("[seats]", project_line), home, project_line.split('"')[1], str(project.SETTINGS)),
                ((), (), home, home_value, project.home_name()),
                ((), (), {}, project.DEFAULT_SEATS[which], "Lem's default"),
            ):
                with self.subTest(which=which, place=place):
                    found = self.seats(project_lines, local_lines, given)[which]
                    self.assertEqual((found["seat"], found["from"]), (seat, place))

    def test_the_experts_from_each_of_the_four_places(self):
        home = self.home("[seats]", 'experts = ["claude/m:high"]')
        for local_lines, project_lines, given, seats, place in (
            (("[seats]", 'experts = ["claude/l:high"]'), ("[seats]", 'experts = ["claude/p:high", "codex/p:high"]'), home, ["claude/l:high"], str(project.LOCAL)),
            ((), ("[seats]", 'experts = ["claude/p:high", "codex/p:high"]'), home, ["claude/p:high", "codex/p:high"], str(project.SETTINGS)),
            ((), (), home, ["claude/m:high"], project.home_name()),
            ((), (), {}, list(project.EXPERTS), "Lem's default"),
        ):
            with self.subTest(place=place):
                found = self.seats(project_lines, local_lines, given)["experts"]
                self.assertEqual([(e["seat"], e["from"]) for e in found], [(one, place) for one in seats])

    def test_the_fallback_from_each_of_the_four_places(self):
        # criterion 2: mybaze has no fallback line and the home folder's settings.toml has none, so it is Lem's claude/opus:high
        mybaze = ("[seats]", 'reviewer = "codex/gpt-6.2-sol:high"')
        found = self.seats(mybaze, home=self.home("[seats]", 'merger = "claude/opus:high"'))["fallback"]
        self.assertEqual((found["seat"], found["agent"], found["model"], found["effort"], found["from"]), ("claude/opus:high", "claude", "opus", "high", "Lem's default"))
        on = self.home("[seats]", 'fallback = "codex/m:high"')
        off = self.home("[seats]", "fallback = false")
        for local_lines, project_lines, given, seat, place in (
            (("[seats]", 'fallback = "claude/l:high"'), ("[seats]", "fallback = false"), off, "claude/l:high", str(project.LOCAL)),
            (("[seats]", "fallback = false"), ("[seats]", 'fallback = "claude/p:high"'), on, False, str(project.LOCAL)),
            ((), ("[seats]", "fallback = false"), on, False, str(project.SETTINGS)),
            ((), ("[seats]", 'fallback = "claude/p:high"'), off, "claude/p:high", str(project.SETTINGS)),
            ((), (), on, "codex/m:high", project.home_name()),
            ((), (), off, False, project.home_name()),
            ((), (), {}, project.FALLBACK, "Lem's default"),
        ):
            with self.subTest(seat=seat, place=place):
                found = self.seats(project_lines, local_lines, given)["fallback"]
                self.assertEqual((found["seat"], found["from"]), (seat, place))
                if seat is False:
                    self.assertEqual(found, {"seat": False, "from": place})

    def test_the_fallbacks_it_refuses(self):
        for given, names in (
            (True, ("seats.fallback = true is no seat", "or false, which turns the fallback off", 'Leave the line out for Lem\'s, "claude/opus:high"')),
            ("", ("seats.fallback is empty", "or false, which turns the fallback off")),
            ("claude", ("seats.fallback = 'claude' names no model and no effort", "written whole")),
            ("claude/opus", ("seats.fallback = 'claude/opus' names no effort",)),
            ("gemini/pro:high", ("the agent 'gemini' must be claude or codex",)),
            (3, ("seats.fallback = 3", project.SEAT_FORM)),
        ):
            for name in (FILE, ROOT / project.LOCAL, Path(project.home_name())):
                with self.subTest(given=given, name=name):
                    self.assertNames(self.refused(project.fallback_of, {"seats": {"fallback": given}}, name), str(name), *names)

    def test_a_wrong_fallback_after_the_first_place_is_still_refused(self):
        message = self.refused(self.seats, ("[seats]", "fallback = true"), ("[seats]", 'fallback = "claude/opus:high"'))
        self.assertNames(message, f"{project.SETTINGS}: seats.fallback = true is no seat")

    def test_the_home_file_takes_each_seat_and_the_fallback(self):
        home = self.home("[seats]", 'reviewer = "codex/gpt-6.2-sol:high"', 'planner = "claude/opus:high"', 'merger = "claude"', 'session = "claude:high"',
                         'experts = ["claude/fable:high"]', "fallback = false")
        found = self.seats(("[branch]", 'base = "main"'), (), home)
        self.assertEqual({which: (found[which]["seat"], found[which]["from"]) for which in ("reviewer", "planner", "merger", "session", "fallback")},
                         {"reviewer": ("codex/gpt-6.2-sol:high", project.home_name()), "planner": ("claude/opus:high", project.home_name()),
                          "merger": ("claude", project.home_name()), "session": ("claude:high", project.home_name()), "fallback": (False, project.home_name())})
        self.assertEqual([(e["seat"], e["from"]) for e in found["experts"]], [("claude/fable:high", project.home_name())])
        for lines, names in (
            (("[seats]", 'experts = "claude/fable:high"'), ("seats.experts", "must be a list of one or two seats")),
            (("[seats]", "fallback = 3"), ("seats.fallback = 3", project.SEAT_FORM)),
            (("[seats]", 'helper = "claude/opus:high"'), ("unknown key seats.helper", "reviewer, planner, merger, session, experts, fallback")),
        ):
            with self.subTest(lines=lines):
                message = self.refused(lambda: self.seats(("[branch]", 'base = "main"'), (), self.home(*lines)))
                self.assertNames(message, project.home_name(), *names)

    def test_a_seat_in_the_home_file_is_written_whole_as_in_the_repositorys_files(self):
        for which, given, names in (
            ("reviewer", "codex", ("seats.reviewer = 'codex' names no model and no effort", "written whole")),
            ("planner", "claude/opus", ("seats.planner = 'claude/opus' names no effort",)),
            ("planner", "codex/gpt:high", ("the agent 'codex' must be claude",)),
            ("experts", ["claude/fable"], ("seats.experts[0] = 'claude/fable' names no effort",)),
        ):
            with self.subTest(which=which, given=given):
                self.assertNames(self.refused(self.seats, ("[branch]", 'base = "main"'), (), {"seats": {which: given}}), f"{project.home_name()}: seats.{which}", *names)
        # the merge agent's and the session's seat may leave out a part there too
        found = self.seats(("[branch]", 'base = "main"'), (), {"seats": {"merger": "codex", "session": "claude:high"}})
        self.assertEqual((found["merger"]["agent"], found["merger"]["model"], found["session"]["effort"]), ("codex", None, "high"))

    def test_the_experts_and_the_session_keep_their_rules_whatever_the_fallback(self):
        # criterion 8: the fallback is one key of the reviewer, the planner and the merge agent; the experts keep
        # their rule that one answers alone where its agent is missing, and the session seat is Claude only
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.dict(os.environ, {"PATH": str(Path(folder) / "none")}):
                found = self.seats(("[seats]", 'fallback = "codex/gpt-6.2-sol:high"'), (), {"seats": {"experts": ["claude/fable:high", "codex/gpt-6.2-astra:high"]}})
        self.assertEqual([(e["seat"], e["here"]) for e in found["experts"]], [("claude/fable:high", True), ("codex/gpt-6.2-astra:high", False)])
        self.assertEqual((found["session"]["seat"], found["session"]["from"]), (project.SEAT_DEFAULT, "Lem's default"))
        self.assertNotIn("fallback", found["session"])
        message = self.refused(self.seats, ("[seats]", 'fallback = "codex/gpt-6.2-sol:high"'), (), {"seats": {"session": "codex:high"}})
        self.assertNames(message, "seats.session", "a task's session runs Claude Code only for now")

    def test_the_seats_leave_local_overrides_and_from_says_the_place(self):
        found = project.decide(ROOT, ROOT, read(), local("[seats]", 'reviewer = "claude/l:high"'), read(), None, {})
        self.assertEqual((found["seats"]["reviewer"]["from"], found["local"]["overrides"]), (str(project.LOCAL), []))

    def test_one_expert_answers_in_the_first_place(self):
        found = settings("[seats]", 'experts = ["codex/gpt-6.2-astra:high"]')["seats"]["experts"]
        self.assertEqual([(e["seat"], e["place"]) for e in found], [("codex/gpt-6.2-astra:high", "fable")])

    def test_an_expert_is_here_when_its_agent_is_on_the_machine(self):
        with tempfile.TemporaryDirectory() as folder:
            codex = Path(folder) / "codex"
            codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            codex.chmod(codex.stat().st_mode | stat.S_IXUSR)
            with mock.patch.dict(os.environ, {"PATH": folder}):
                with_codex = [(e["place"], e["here"]) for e in settings()["seats"]["experts"]]
            with mock.patch.dict(os.environ, {"PATH": str(Path(folder) / "none")}):
                without = [(e["place"], e["here"]) for e in settings()["seats"]["experts"]]
        self.assertEqual(with_codex, [("fable", True), ("astra", True)])
        self.assertEqual(without, [("fable", True), ("astra", False)])

    def test_the_seats_it_refuses(self):
        name = Path(".lem/settings.toml")
        for which, given, names in (
            ("reviewer", "", ("seats.reviewer is empty", project.SEAT_FORM)),
            ("reviewer", "codex /gpt", ("holds a space", project.SEAT_FORM)),
            ("reviewer", "gemini/pro:high", ("the agent 'gemini' must be claude or codex",)),
            ("reviewer", "/gpt:high", ("names no agent before the `/`",)),
            ("reviewer", 3, ("seats.reviewer = 3", project.SEAT_FORM)),
            ("reviewer", "codex:high:max", ("seats.reviewer = 'codex:high:max' holds 2 `:`", "one at most")),
            ("planner", "codex/gpt:high", ("the agent 'codex' must be claude", "checked in Claude Code only")),
            ("merger", "codex/", ("names no model after the `/`",)),
            ("merger", "codex/gpt:", ("names no effort after the `:`",)),
        ):
            with self.subTest(which=which, given=given):
                self.assertNames(self.refused(project.seat, {"seats": {which: given}}, name, which), str(name), *names)

    def test_a_seat_line_parse_seat_refuses(self):
        # the word `set` takes goes through the same parse
        message = self.refused(project.set_value, "global", "reviewer", "claude/opus:high:max")
        self.assertNames(message, "set global reviewer: seats.reviewer = 'claude/opus:high:max' holds 2 `:`")

    def test_the_experts_it_refuses(self):
        name = Path(".lem/settings.toml")
        for given, names in (
            ([], ("seats.experts = []", "one or two seats")),
            (["claude/fable:high", "codex/gpt:high", "claude/opus:high"], ("seats.experts", "one or two seats")),
            ("claude/fable:high", ("seats.experts = 'claude/fable:high'", "one or two seats")),
            (["claude/fable:high", "gemini/pro:high"], ("seats.experts[1]", "the agent 'gemini' must be claude or codex")),
        ):
            with self.subTest(given=given):
                self.assertNames(self.refused(project.experts_of, {"seats": {"experts": given}}, name), str(name), *names)


class SetSeat(Home):
    """`lem project set global|local NAME VALUE`: one line of `[seats]` in the home folder's settings.toml or in this
    machine's own file of the repository, with every other line of the file kept; nothing writes the team's file.
    Each case has a git repository of its own in a temporary folder, beside its own XDG_CONFIG_HOME."""

    def setUp(self):
        super().setUp()
        self.repo = Path(self.folder.name) / "notes-app"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        self.settings = self.repo / project.SETTINGS
        self.settings.parent.mkdir()
        self.settings.write_text('# the project\'s own\n[branch]\nbase = "main"\n', encoding="utf-8")
        self.home_file = project.lem_state.home_settings_file()
        self.local_file = self.repo / project.LOCAL

    def set(self, scope: str, name: str, value: str) -> dict:
        return project.cmd_set(self.repo, scope, name, [value])

    def write(self, file: Path, *lines: str) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_set_global_keeps_the_owners_comment_and_the_merger(self):
        # criterion 6, its four steps
        self.write(self.home_file, "# the Mac in the office", "[seats]", 'merger = "claude/opus:high"')
        said = self.set("global", "reviewer", "codex/gpt-6.2-sol:high")
        self.assertEqual(self.home_file.read_text(encoding="utf-8"),
                         '# the Mac in the office\n[seats]\nmerger = "claude/opus:high"\nreviewer = "codex/gpt-6.2-sol:high"\n')
        self.assertEqual((said["seat"]["seat"], said["seat"]["from"], said["file"]), ("codex/gpt-6.2-sol:high", project.home_name(), str(self.home_file)))
        self.assertEqual(said["said"], f"the reviewer here is codex/gpt-6.2-sol:high, from {project.home_name()}")
        back = self.set("global", "reviewer", "default")
        self.assertEqual(self.home_file.read_text(encoding="utf-8"), '# the Mac in the office\n[seats]\nmerger = "claude/opus:high"\n')
        self.assertEqual((back["seat"]["seat"], back["seat"]["from"], back["line"]), ("claude/opus:high", "Lem's default", None))

    def test_set_local_keeps_its_comment_and_its_state_table(self):
        self.write(self.local_file, "# mine, not committed", "[state]", "keep_days = 3", "", "[seats]", 'planner = "claude/opus:max"  # for long plans')
        said = self.set("local", "reviewer", "claude/opus:high")
        self.assertEqual(self.local_file.read_text(encoding="utf-8"),
                         '# mine, not committed\n[state]\nkeep_days = 3\n\n[seats]\nplanner = "claude/opus:max"  # for long plans\nreviewer = "claude/opus:high"\n')
        self.assertEqual((said["seat"]["seat"], said["seat"]["from"]), ("claude/opus:high", str(project.LOCAL)))
        # a line replaced keeps its own comment
        self.set("local", "planner", "claude/opus:high")
        self.assertIn('planner = "claude/opus:high"  # for long plans\n', self.local_file.read_text(encoding="utf-8"))
        self.set("local", "reviewer", "default")
        self.set("local", "planner", "default")
        self.assertEqual(self.local_file.read_text(encoding="utf-8"), "# mine, not committed\n[state]\nkeep_days = 3\n")

    def test_set_local_in_a_task_worktree_writes_the_main_checkout(self):
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "start"], check=True)
        tree = Path(self.folder.name) / "wt"
        subprocess.run(["git", "-C", str(self.repo), "worktree", "add", "-q", str(tree), "-b", "feat/x"], check=True)
        said = project.cmd_set(tree, "local", "reviewer", ["codex/gpt-6.2-sol:high"])
        self.assertEqual(said["file"], str(project.main_checkout(tree) / project.LOCAL))
        self.assertTrue(self.local_file.is_file())
        self.assertFalse((tree / project.LOCAL).exists())

    def test_a_new_file_and_default_on_its_last_line(self):
        said = self.set("local", "fallback", "false")
        self.assertEqual(said["line"], "fallback = false")
        self.assertEqual(said["seat"], {"seat": False, "from": str(project.LOCAL)})
        self.assertEqual(self.local_file.read_text(encoding="utf-8"), f"{project.SET_FIRST['local']}\n\n[seats]\nfallback = false\n")
        self.assertEqual(said["said"], "the fallback here is off, from .lem/settings.local.toml")
        self.set("local", "fallback", "default")
        self.assertFalse(self.local_file.exists())

    def test_a_file_with_a_comment_of_the_owners_stays_and_one_of_lems_lines_goes(self):
        # criterion 6: "Each other line and comment of that file stays as it was", with no table left too
        self.write(self.home_file, "# the Mac in the office", "[seats]", 'reviewer = "codex/gpt-6.2-sol:high"')
        self.set("global", "reviewer", "default")
        self.assertEqual(self.home_file.read_text(encoding="utf-8"), "# the Mac in the office\n")
        # a file of Lem's own first line and one line goes, in both scopes
        for scope, file in (("global", self.home_file), ("local", self.local_file)):
            with self.subTest(scope=scope):
                self.write(file, project.SET_FIRST[scope], "", "[seats]", 'reviewer = "codex/gpt-6.2-sol:high"')
                self.set(scope, "reviewer", "default")
                self.assertFalse(file.exists())

    def test_default_on_the_last_line_of_a_table(self):
        text = '[load]\nstart = 6\n\n[seats]\nreviewer = "codex/gpt-6.2-sol:high"\n\n[serve]\nport = 4500\n'
        self.assertEqual(project.lem_state.edited(text, "seats", "reviewer", None, "machine.toml"), "[load]\nstart = 6\n\n[serve]\nport = 4500\n")
        self.assertEqual(project.lem_state.edited('[load]\nstart = 6\n\n[seats]\nreviewer = "x/y:z"\n', "seats", "reviewer", None, "machine.toml"), "[load]\nstart = 6\n")

    def test_a_table_taken_out_keeps_the_comment_on_its_header(self):
        # criterion 6: "Each other line and comment of that file stays as it was", the comment after a header too
        text = '[load]\nstart = 4\n\n[seats] # office Mac\nreviewer = "codex/a:high"\n'
        self.assertEqual(project.lem_state.edited(text, "seats", "reviewer", None, "machine.toml"), "[load]\nstart = 4\n\n# office Mac\n")
        self.write(self.home_file, "[seats]  # office Mac", 'reviewer = "codex/gpt-6.2-sol:high"')
        self.set("global", "reviewer", "default")
        self.assertEqual(self.home_file.read_text(encoding="utf-8"), "# office Mac\n")

    def test_the_experts_are_written_as_a_list(self):
        said = self.set("global", "experts", "claude/fable:high,codex/gpt-6.2-astra:high")
        self.assertIn('experts = ["claude/fable:high", "codex/gpt-6.2-astra:high"]\n', self.home_file.read_text(encoding="utf-8"))
        self.assertEqual([(e["seat"], e["from"]) for e in said["seat"]], [("claude/fable:high", project.home_name()), ("codex/gpt-6.2-astra:high", project.home_name())])
        self.assertNames(self.refused(project.set_value, "global", "experts", "claude/a:high,claude/b:high,claude/c:high"), "names 3 seats", "one or two whole seats joined by a comma")
        self.assertNames(self.refused(project.set_value, "global", "experts", "claude/fable"), "set global experts: seats.experts[0] = 'claude/fable' names no effort")

    def test_a_key_in_another_form_is_refused_and_the_file_stays(self):
        for lines, name in (
            (("[seats]", "experts = [", '  "claude/fable:high",', "]"), "experts"),
            (('seats.reviewer = "codex/gpt-6.2-sol:high"',), "reviewer"),
            (('seats = {reviewer = "codex/gpt-6.2-sol:high"}',), "reviewer"),
        ):
            for value in ("claude/opus:high", "default"):
                with self.subTest(lines=lines, value=value):
                    self.write(self.home_file, *lines)
                    before = self.home_file.read_bytes()
                    message = self.refused(self.set, "global", name, value)
                    self.assertNames(message, str(self.home_file), f"write `{name}` on one line under `[seats]`")
                    self.assertEqual(self.home_file.read_bytes(), before)

    def test_a_wrong_file_is_refused_with_its_fix_and_stays(self):
        self.write(self.local_file, "[seats]", "planner = 42")
        self.assertNames(self.refused(self.set, "local", "reviewer", "claude/opus:high"), ".lem/settings.local.toml: seats.planner = 42 must be")
        self.assertEqual(self.local_file.read_text(encoding="utf-8"), "[seats]\nplanner = 42\n")
        self.write(self.home_file, "[seats]", 'planner = "codex/gpt-6.2-sol:high"')
        self.assertNames(self.refused(self.set, "global", "reviewer", "claude/opus:high"), "seats.planner", "the agent 'codex' must be claude")
        self.assertEqual(self.home_file.read_text(encoding="utf-8"), '[seats]\nplanner = "codex/gpt-6.2-sol:high"\n')
        self.write(self.home_file, "[state]", "keep_days = 3")
        self.assertNames(self.refused(self.set, "global", "reviewer", "claude/opus:high"), "[state] is not valid in this file")
        self.assertEqual(self.home_file.read_text(encoding="utf-8"), "[state]\nkeep_days = 3\n")
        # a repository whose settings do not load is refused before the home folder's file is written for every repository
        self.home_file.unlink()
        self.settings.write_text('[branch]\nbase = "main"\nland = "x"\n', encoding="utf-8")
        self.assertNames(self.refused(self.set, "global", "reviewer", "codex/gpt-6.2-sol:high"), "branch.land")
        self.assertFalse(self.home_file.exists())

    def test_false_is_for_the_fallback_only_and_every_seat_is_whole(self):
        for name in ("reviewer", "planner", "merger", "session", "experts"):
            with self.subTest(name=name):
                self.assertNames(self.refused(project.set_value, "global", name, "false"), f"set global {name}: false is for fallback only")
        # the merge agent's and the session's seat may leave out a part in a file, and `set` takes only a whole one
        for name, given in (("merger", "claude"), ("session", "claude:high")):
            with self.subTest(name=name):
                message = self.refused(project.set_value, "local", name, given)
                self.assertNames(message, f"seats.{name}", "written whole")
                # the example it names is one that `set` takes
                example = re.search(r'written whole, as "([^"]+)"', message).group(1)
                self.assertEqual(project.set_value("local", name, example), example)
        self.assertNames(self.refused(project.set_value, "local", "fallback", "true"), "seats.fallback = true is no seat")
        self.assertNames(self.refused(project.set_value, "local", "helper", "claude/opus:high"), "not 'helper'", "reviewer, planner, merger, session, experts, fallback")
        self.assertIsNone(project.set_value("local", "merger", "default"))

    def test_no_path_writes_the_repositorys_settings(self):
        before = self.settings.read_bytes()
        for scope in project.SCOPES:
            for name, value in (("reviewer", "codex/gpt-6.2-sol:high"), ("planner", "claude/opus:max"), ("merger", "codex/gpt-6.2-sol:high"),
                                ("session", "claude/opus:high"), ("experts", "claude/fable:high"), ("fallback", "false"), ("fallback", "default")):
                with self.subTest(scope=scope, name=name, value=value):
                    self.set(scope, name, value)
                    self.assertEqual(self.settings.read_bytes(), before)
        self.assertNames(self.refused(self.set, "project", "reviewer", "claude/opus:high"), "set takes global", "no command writes it")
        self.assertEqual(self.settings.read_bytes(), before)

    def test_reviewer_is_no_command(self):
        # criterion 7: `set local reviewer` does its work, and no alias is left
        out = io.StringIO()
        with contextlib.redirect_stderr(out), self.assertRaises(SystemExit) as stopped:
            project.main(["--repo", str(self.repo), "reviewer", "claude/opus:high"])
        self.assertEqual(stopped.exception.code, 2)
        self.assertIn("invalid choice: 'reviewer'", out.getvalue())
        self.assertFalse(hasattr(project, "cmd_reviewer"))
        self.assertFalse(self.local_file.exists())


if __name__ == "__main__":
    unittest.main()
