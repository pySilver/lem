"""Lem's settings rules, as calls of the functions that hold them: what a settings file may say, what
`lem project show` refuses in one, and what it reads from one. Each rule here takes the tables that
were read and returns the settings or refuses; which checkout and which commit supply the tables is a
fact only git shows, and tests/lem-settings.sh checks it in real repositories.

    python3 -B -m unittest discover -s tests/unit
"""

import os
import stat
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


def read(*lines: str, name: Path = FILE, tables: tuple[str, ...] = tuple(project.TABLES)) -> dict:
    """The tables of a settings file of these lines, as `load` reads them."""
    return project.settings_of("\n".join(lines) + "\n", name, tables)


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
        self.assertNames(message, str(FILE), "paths.styleguide", "valid: plans, plan_file, rulings, ruling_file")

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
        self.assertEqual(found["settings_from"], "this worktree's branch, with [flow] and [naps] from main@012345678")

    def test_the_branch_own_flow_is_still_checked(self):
        self.assertNames(self.refused(self.in_tree, read("[flow]", 'topics = "money"'), {}), "flow.topics")

    def test_a_wrong_naps_switch_on_the_base_names_the_base_commit(self):
        self.assertNames(self.refused(self.in_tree, {}, read("[naps]", 'on = "yes"')), "main:.lem/project.toml", "naps.on")


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

    def test_a_ruling_file_with_a_folder(self):
        message = self.refused_settings("[paths]", 'ruling_file = "decisions/<slug>.md"')
        self.assertNames(message, "paths.ruling_file", "with no folder in it", "paths.rulings names the folder")


class Tracker(Refuses):
    """No table is no tracker; a table has one key, its kind, and any other key is unknown."""

    def tracker(self, *lines: str) -> dict | None:
        return settings("[tracker]", *lines)["tracker"] if lines else settings()["tracker"]

    def test_the_tables_it_takes(self):
        self.assertIsNone(self.tracker())
        self.assertEqual(self.tracker('kind = "linear"'), {"kind": "linear"})

    def test_the_tables_it_refuses(self):
        for lines, names in (
            (('kind = "jira"',), ("tracker.kind", "'jira'", "linear")),
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


class Seats(Refuses):
    """A seat is one string, agent/model:effort: the effort, or the model and the effort, may be left out."""

    def test_each_seat_parsed(self):
        found = settings("[seats]", 'reviewer = "codex/gpt-6.1-sol:high"', 'planner = "claude/opus"', 'experts = ["claude/fable:high", "codex"]')["seats"]
        self.assertEqual(found["reviewer"], {"agent": "codex", "model": "gpt-6.1-sol", "effort": "high", "seat": "codex/gpt-6.1-sol:high"})
        self.assertEqual(found["planner"], {"agent": "claude", "model": "opus", "effort": None, "seat": "claude/opus"})
        self.assertEqual([(e["agent"], e["model"], e["effort"], e["place"]) for e in found["experts"]], [("claude", "fable", "high", "fable"), ("codex", None, None, "astra")])

    def test_the_merge_agents_seat_from_the_repository_the_machine_or_the_agent(self):
        machine = {"merger": "codex/gpt-6.2-sol:high"}
        raw = read("[seats]", 'merger = "claude/opus:high"')
        own = project.decide(ROOT, ROOT, raw, {}, raw, None, machine)["seats"]["merger"]
        self.assertEqual((own["agent"], own["model"], own["effort"], own["from"]), ("claude", "opus", "high", str(project.SETTINGS)))
        raw = read("[branch]", 'base = "master"')
        mine = project.decide(ROOT, ROOT, raw, {}, raw, None, machine)["seats"]["merger"]
        self.assertEqual((mine["agent"], mine["model"], mine["effort"]), ("codex", "gpt-6.2-sol", "high"))
        self.assertTrue(mine["from"].endswith("machine.toml"))
        bare = project.decide(ROOT, ROOT, raw, {}, raw, None, {})["seats"]["merger"]
        self.assertEqual((bare["agent"], bare["model"], bare["effort"], bare["from"]), ("claude", None, None, "the agent's own default"))

    def test_the_merge_agents_seat_the_machine_names_is_checked(self):
        raw = read("[branch]", 'base = "master"')
        message = self.refused(project.decide, ROOT, ROOT, raw, {}, raw, None, {"merger": "gemini/pro"})
        self.assertNames(message, "machine.toml: seats.merger", "the agent 'gemini' must be claude or codex")

    def test_a_seat_with_no_model(self):
        found = settings("[seats]", 'reviewer = "codex:high"')["seats"]["reviewer"]
        self.assertEqual((found["agent"], found["model"], found["effort"]), ("codex", None, "high"))

    def test_lem_defaults_with_no_seat(self):
        found = settings("[branch]", 'base = "master"')["seats"]
        self.assertEqual(found["reviewer"], {"agent": None, "model": None, "effort": None, "seat": None})
        self.assertEqual(found["planner"]["seat"], project.PLANNER)
        self.assertEqual([e["seat"] for e in found["experts"]], list(project.EXPERTS))

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
        name = Path(".lem/project.toml")
        for which, given, names in (
            ("reviewer", "", ("seats.reviewer is empty", project.SEAT_FORM)),
            ("reviewer", "codex /gpt", ("holds a space", project.SEAT_FORM)),
            ("reviewer", "gemini/pro:high", ("the agent 'gemini' must be claude or codex",)),
            ("reviewer", "codex/", ("names no model after the `/`",)),
            ("reviewer", "codex/gpt:", ("names no effort after the `:`",)),
            ("reviewer", "/gpt:high", ("names no agent before the `/`",)),
            ("reviewer", 3, ("seats.reviewer = 3", project.SEAT_FORM)),
            ("reviewer", "codex:high:max", ("seats.reviewer = 'codex:high:max' holds 2 `:`", "one at most")),
            ("planner", "codex/gpt:high", ("the agent 'codex' must be claude", "checked in Claude Code only")),
        ):
            with self.subTest(which=which, given=given):
                self.assertNames(self.refused(project.seat, {"seats": {which: given}}, name, which), str(name), *names)

    def test_a_seat_line_parse_seat_refuses(self):
        # the reviewer command's own word goes through the same parse
        message = self.refused(project.parse_seat, "claude/opus:high:max", "the reviewer", project.REVIEWERS, *project.SEATS["reviewer"][1:])
        self.assertNames(message, "the reviewer = 'claude/opus:high:max' holds 2 `:`")

    def test_the_experts_it_refuses(self):
        name = Path(".lem/project.toml")
        for given, names in (
            ([], ("seats.experts = []", "one or two seats")),
            (["claude", "codex", "claude/opus"], ("seats.experts", "one or two seats")),
            ("claude/fable", ("seats.experts = 'claude/fable'", "one or two seats")),
            (["claude/fable", "gemini"], ("seats.experts[1]", "the agent 'gemini' must be claude or codex")),
        ):
            with self.subTest(given=given):
                self.assertNames(self.refused(project.experts_of, {"seats": {"experts": given}}, name), str(name), *names)


if __name__ == "__main__":
    unittest.main()
