"""A release names one number in three places: the `version` of `.claude-plugin/plugin.json`, and the
`version` and the `ref` of the `lem` entry of `.claude-plugin/marketplace.json`, whose source is the
GitHub repository at the tag `vNUMBER`. An install and an update take the plugin from that source, so
they get the commit of the release tag and never the head of `main`.

A task keeps the release it began on (lem_release.py): the rule that a command for a task of this
release or the one before goes on, and one for a task two releases back stops with the message of
criterion 4; the mark a task's open writes, from Claude Code's list of installs; and the check each
command runs, which logs the stop once and lets a command that ends the task go on.

    python3 -B -m unittest discover -s tests/unit -p test_release.py
"""

import importlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "skills" / "lem" / "scripts"))
lem_release = importlib.import_module("lem_release")
# The repository every install of the `lem` entry takes the plugin from.
REPO = "pySilver/lem"


def release_places(plugin: dict, market: dict) -> list[tuple[str, str]]:
    """Each place of the two manifests that does not name the release of `plugin.json`, as (the place,
    what is wrong there and what it expects). Empty when the three places name one release."""
    number = plugin.get("version")
    if not isinstance(number, str) or not re.fullmatch(r"\d+\.\d+\.\d+", number):
        return [
            (
                "plugin.json version",
                f'plugin.json\'s version is {number!r}, and a release names three numbers, as "0.4.0"',
            )
        ]
    tag = f"v{number}"
    entries = [
        entry
        for entry in market.get("plugins") or []
        if isinstance(entry, dict) and entry.get("name") == "lem"
    ]
    if len(entries) != 1:
        return [
            (
                "marketplace.json plugins",
                f"marketplace.json has {len(entries)} entries named lem, and it needs one, at the release {tag}",
            )
        ]
    entry = entries[0]
    found = []
    source = entry.get("source")
    want = {"source": "github", "repo": REPO, "ref": tag}
    if (
        not isinstance(source, dict)
        or source.get("source") != "github"
        or source.get("repo") != REPO
    ):
        found.append(
            (
                "lem entry source",
                f"the lem entry's source is {json.dumps(source)}, and plugin.json's version {number} expects {json.dumps(want)}",
            )
        )
    elif "ref" not in source:
        found.append(
            (
                "lem entry ref",
                f'the lem entry\'s source has no ref, and plugin.json\'s version {number} expects "ref": "{tag}"',
            )
        )
    elif source["ref"] != tag:
        found.append(
            (
                "lem entry ref",
                f"the lem entry's ref is {json.dumps(source['ref'])}, and plugin.json's version {number} expects \"{tag}\"",
            )
        )
    if entry.get("version") != number:
        found.append(
            (
                "lem entry version",
                f"the lem entry's version is {json.dumps(entry.get('version'))}, and plugin.json's version {number} expects \"{number}\"",
            )
        )
    return found


def manifests(
    number: str = "0.4.0",
    ref: str | None = "v0.4.0",
    version: str | None = "0.4.0",
    source: object = None,
) -> tuple[dict, dict]:
    """A plugin.json of NUMBER and a marketplace.json whose lem entry has REF and VERSION (left out when None)."""
    if source is None:
        source = {
            "source": "github",
            "repo": REPO,
            **({"ref": ref} if ref is not None else {}),
        }
    entry = {
        "name": "lem",
        "source": source,
        "description": "Lem.",
        **({"version": version} if version is not None else {}),
    }
    return {"name": "lem", "version": number}, {"name": "lem", "plugins": [entry]}


class Places(unittest.TestCase):
    def test_three_places_that_name_one_release_pass(self) -> None:
        self.assertEqual(release_places(*manifests()), [])

    def test_a_ref_of_the_release_before_fails_and_names_the_ref_and_the_number_it_expects(
        self,
    ) -> None:
        self.assertEqual(
            release_places(*manifests(ref="v0.3.0")),
            [
                (
                    "lem entry ref",
                    'the lem entry\'s ref is "v0.3.0", and plugin.json\'s version 0.4.0 expects "v0.4.0"',
                )
            ],
        )

    def test_an_entry_version_of_another_release_fails(self) -> None:
        self.assertEqual(
            release_places(*manifests(version="0.3.0")),
            [
                (
                    "lem entry version",
                    'the lem entry\'s version is "0.3.0", and plugin.json\'s version 0.4.0 expects "0.4.0"',
                )
            ],
        )
        self.assertEqual(
            [place for place, _ in release_places(*manifests(version=None))],
            ["lem entry version"],
        )

    def test_an_entry_with_no_ref_fails(self) -> None:
        self.assertEqual(
            release_places(*manifests(ref=None)),
            [
                (
                    "lem entry ref",
                    'the lem entry\'s source has no ref, and plugin.json\'s version 0.4.0 expects "ref": "v0.4.0"',
                )
            ],
        )

    def test_a_source_that_is_not_the_github_repository_fails(self) -> None:
        for source in (
            "./",
            {"source": "github", "repo": "someone/lem", "ref": "v0.4.0"},
            {"source": "url", "url": f"https://github.com/{REPO}.git", "ref": "v0.4.0"},
        ):
            with self.subTest(source=source):
                found = release_places(*manifests(source=source))
                self.assertEqual([place for place, _ in found], ["lem entry source"])
                self.assertIn(
                    'expects {"source": "github", "repo": "pySilver/lem", "ref": "v0.4.0"}',
                    found[0][1],
                )

    def test_a_plugin_version_that_is_no_release_fails(self) -> None:
        self.assertEqual(
            [place for place, _ in release_places({"name": "lem"}, manifests()[1])],
            ["plugin.json version"],
        )


class Repository(unittest.TestCase):
    def read(self) -> tuple[dict, dict]:
        folder = ROOT / ".claude-plugin"
        return (
            json.loads((folder / "plugin.json").read_text(encoding="utf-8")),
            json.loads((folder / "marketplace.json").read_text(encoding="utf-8")),
        )

    def test_the_lem_entry_takes_the_plugin_from_the_release_tag_and_not_from_main(
        self,
    ) -> None:
        plugin, market = self.read()
        entry = next(entry for entry in market["plugins"] if entry["name"] == "lem")
        self.assertEqual(
            entry["source"],
            {"source": "github", "repo": REPO, "ref": f"v{plugin['version']}"},
        )

    def test_the_repository_names_one_release_in_three_places(self) -> None:
        self.assertEqual(release_places(*self.read()), [])


# Criterion 4's message, word for word, for invoice-totals begun on 0.2.0 under 0.4.0, whose release before is 0.3.0.
OLD_STOP = (
    "invoice-totals began on Lem 0.2.0, and Lem 0.4.0 reads only tasks begun on 0.3.0 or 0.4.0. Your branch and its commits stay. "
    "/lem drop invoice-totals, then /lem resume invoice-totals, starts a new task on 0.4.0 from that branch and from the notes the task left."
)


class Rule(unittest.TestCase):
    def test_a_task_with_no_mark_counts_as_begun_on_the_release_before_marks_and_goes_on(
        self,
    ) -> None:
        self.assertEqual(lem_release.UNMARKED, "0.3.1")
        self.assertIsNone(
            lem_release.stop("invoice-totals", lem_release.UNMARKED, "0.4.0", "0.3.1")
        )
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(lem_release.began_on(Path(folder)), "0.3.1")

    def test_a_task_of_this_release_or_of_the_release_before_goes_on(self) -> None:
        self.assertIsNone(lem_release.stop("invoice-totals", "0.4.0", "0.4.0", "0.3.0"))
        self.assertIsNone(lem_release.stop("invoice-totals", "0.3.0", "0.4.0", "0.3.0"))

    def test_a_task_two_releases_back_stops_with_the_message_of_criterion_4(
        self,
    ) -> None:
        self.assertEqual(
            lem_release.stop("invoice-totals", "0.2.0", "0.4.0", "0.3.0"),
            {"kind": "old", "say": OLD_STOP},
        )

    def test_a_task_of_a_newer_release_stops_and_names_the_update(self) -> None:
        found = lem_release.stop("invoice-totals", "0.5.0", "0.4.0", "0.3.0")
        self.assertEqual(found["kind"], "new")
        self.assertIn("/plugin marketplace update lem", found["say"])
        self.assertTrue(
            found["say"].startswith(
                "invoice-totals began on Lem 0.5.0, which is newer than this Lem, 0.4.0"
            )
        )

    def test_versions_compare_as_numbers_part_by_part(self) -> None:
        self.assertEqual(lem_release.stop("t", "0.9.0", "0.10.0", "0.9.0"), None)
        self.assertEqual(
            lem_release.stop("t", "0.8.9", "0.10.0", "0.9.0")["kind"], "old"
        )
        self.assertEqual(
            lem_release.stop("t", "0.10.1", "0.10.0", "0.9.0")["kind"], "new"
        )


def installs(*entries: dict) -> dict:
    return {
        "version": 2,
        "plugins": {
            "lem@lem": list(entries),
            "other@lem": [{"scope": "user", "version": "9.0.0"}],
        },
    }


class Mark(unittest.TestCase):
    """The mark a task's open writes: the release its project's sessions load, never newer than this Lem."""

    MAIN = "/lem-unit/shop"

    def test_the_projects_own_install_comes_first(self) -> None:
        listed = installs(
            {"scope": "user", "version": "0.4.0"},
            {"scope": "project", "projectPath": self.MAIN, "version": "0.3.0"},
            {"scope": "project", "projectPath": "/lem-unit/api", "version": "0.2.0"},
        )
        self.assertEqual(lem_release.chosen(listed, self.MAIN, "0.4.0"), "0.3.0")

    def test_else_the_users_install(self) -> None:
        listed = installs(
            {"scope": "user", "version": "0.3.0"},
            {"scope": "project", "projectPath": "/lem-unit/api", "version": "0.2.0"},
        )
        self.assertEqual(lem_release.chosen(listed, self.MAIN, "0.4.0"), "0.3.0")

    def test_else_the_running_lems_own(self) -> None:
        for listed in (
            None,
            {},
            installs(
                {"scope": "project", "projectPath": "/lem-unit/api", "version": "0.2.0"}
            ),
            installs({"scope": "user", "version": "next"}),
        ):
            with self.subTest(listed=listed):
                self.assertEqual(
                    lem_release.chosen(listed, self.MAIN, "0.4.0"), "0.4.0"
                )

    def test_never_newer_than_the_running_lem(self) -> None:
        listed = installs(
            {"scope": "project", "projectPath": self.MAIN, "version": "0.5.0"}
        )
        self.assertEqual(lem_release.chosen(listed, self.MAIN, "0.4.0"), "0.4.0")


class Check(unittest.TestCase):
    """The check each command runs, in a state folder of a throwaway main checkout."""

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.main = Path(self.folder.name).resolve() / "shop"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.main)], check=True)
        self.state = self.main / ".lem" / "state"
        self.task = self.state / "tasks" / "invoice-totals"
        self.task.mkdir(parents=True)
        self.version = mock.patch.object(lem_release, "running", lambda: "0.4.0")
        self.before = mock.patch.object(lem_release, "BEFORE", "0.3.0")
        self.version.start()
        self.before.start()

    def tearDown(self) -> None:
        self.version.stop()
        self.before.stop()
        self.folder.cleanup()

    def events(self) -> list[dict]:
        log = self.state / "events.jsonl"
        return (
            [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            if log.is_file()
            else []
        )

    def test_a_task_of_the_release_before_goes_on_and_logs_nothing(self) -> None:
        (self.task / "release.txt").write_text("0.3.0\n", encoding="utf-8")
        self.assertIsNone(lem_release.check(self.task))
        self.assertEqual(self.events(), [])

    def test_a_task_two_releases_back_stops_and_logs_the_stop_once(self) -> None:
        (self.task / "release.txt").write_text("0.2.0\n", encoding="utf-8")
        self.assertEqual(lem_release.check(self.task), OLD_STOP)
        self.assertEqual(lem_release.check(self.task), OLD_STOP)
        logged = self.events()
        self.assertEqual(
            [
                (e["event"], e["task"], e["began"], e["running"], e["branch"], e["say"])
                for e in logged
            ],
            [("release.stop", "invoice-totals", "0.2.0", "0.4.0", None, OLD_STOP)],
        )

    def test_a_command_that_ends_the_task_logs_the_same_stop_and_goes_on(self) -> None:
        (self.task / "release.txt").write_text("0.2.0\n", encoding="utf-8")
        self.assertIsNone(lem_release.check(self.task, passes=True))
        self.assertEqual([e["say"] for e in self.events()], [OLD_STOP])
        self.assertEqual(lem_release.check(self.task), OLD_STOP)
        self.assertEqual(len(self.events()), 1)

    def test_the_resume_after_the_drop_logs_no_second_stop_and_a_state_of_work_after_a_stop_logs_one(
        self,
    ) -> None:
        (self.task / "release.txt").write_text("0.2.0\n", encoding="utf-8")
        log = self.state / "events.jsonl"

        def state(status: str) -> None:
            with log.open("a", encoding="utf-8") as out:
                out.write(
                    json.dumps(
                        {
                            "ts": "2026-11-23T12:00:00Z",
                            "event": "task.state",
                            "task": "invoice-totals",
                            "status": status,
                        }
                    )
                    + "\n"
                )

        # the drop passes and logs the stop, then writes its state; the resume of the dropped task passes too
        self.assertIsNone(lem_release.check(self.task, passes=True))
        state("dropped")
        self.assertIsNone(lem_release.check(self.task, passes=True))
        self.assertEqual(
            [e["event"] for e in self.events()], ["release.stop", "task.state"]
        )
        # a state of work after the stop (written by another Lem) leaves it standing no more
        state("building")
        self.assertEqual(lem_release.check(self.task), OLD_STOP)
        self.assertEqual(
            [e["event"] for e in self.events()],
            ["release.stop", "task.state", "task.state", "release.stop"],
        )

    def test_a_task_of_a_newer_release_stops_and_writes_nothing(self) -> None:
        (self.task / "release.txt").write_text("0.5.0\n", encoding="utf-8")
        for passes in (False, True):
            self.assertIn(
                "/plugin marketplace update lem",
                lem_release.check(self.task, passes=passes),
            )
        self.assertEqual(self.events(), [])

    def test_the_stop_names_the_branch_git_keeps_for_the_tasks_worktree(self) -> None:
        (self.task / "release.txt").write_text("0.2.0\n", encoding="utf-8")
        subprocess.run(
            [
                "git",
                "-C",
                str(self.main),
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@t",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "base",
            ],
            check=True,
        )
        tree = self.main / ".lem" / "worktrees" / "invoice-totals"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.main),
                "worktree",
                "add",
                "-q",
                "-b",
                "fix/invoice-totals",
                str(tree),
            ],
            check=True,
        )
        # a worktree folder removed by hand: git keeps its entry until a prune
        subprocess.run(["rm", "-rf", str(tree)], check=True)
        lem_release.check(self.task)
        self.assertEqual(self.events()[-1]["branch"], "fix/invoice-totals")

    def test_the_stop_names_the_branch_a_rebase_runs_on_in_the_tasks_worktree(
        self,
    ) -> None:
        (self.task / "release.txt").write_text("0.2.0\n", encoding="utf-8")
        subprocess.run(
            [
                "git",
                "-C",
                str(self.main),
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@t",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "base",
            ],
            check=True,
        )
        tree = self.main / ".lem" / "worktrees" / "invoice-totals"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.main),
                "worktree",
                "add",
                "-q",
                "-b",
                "fix/invoice-totals",
                str(tree),
            ],
            check=True,
        )
        # a rebase that stopped on a conflict: the head is detached, and git keeps the branch in head-name
        subprocess.run(
            ["git", "-C", str(tree), "checkout", "-q", "--detach"], check=True
        )
        admin = Path(
            subprocess.run(
                ["git", "-C", str(tree), "rev-parse", "--absolute-git-dir"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        (admin / "rebase-merge").mkdir()
        (admin / "rebase-merge" / "head-name").write_text(
            "refs/heads/fix/invoice-totals\n", encoding="utf-8"
        )
        lem_release.check(self.task)
        self.assertEqual(self.events()[-1]["branch"], "fix/invoice-totals")

    def test_a_task_that_is_not_there_yet_is_no_stop(self) -> None:
        self.assertIsNone(lem_release.check(self.state / "tasks" / "new-task"))

    def test_a_pass_holds_for_the_commands_of_one_command_and_for_no_command_after_it(
        self,
    ) -> None:
        (self.task / "release.txt").write_text("0.2.0\n", encoding="utf-8")

        @lem_release.one_command
        def ending() -> str | None:
            self.assertIsNone(lem_release.check(self.task, passes=True))
            # a command it runs in this process for the same task (`lem project log` in `lem land merged`)
            return nested()

        @lem_release.one_command
        def nested() -> str | None:
            return lem_release.check(self.task)

        self.assertIsNone(ending())
        self.assertEqual(nested(), OLD_STOP)
        self.assertEqual(lem_release.check(self.task), OLD_STOP)


class Before(unittest.TestCase):
    def test_the_release_before_is_older_than_plugin_json(self) -> None:
        version = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )["version"]
        self.assertEqual(lem_release.running(), version)
        self.assertLess(
            lem_release.numbers(lem_release.BEFORE), lem_release.numbers(version)
        )


if __name__ == "__main__":
    unittest.main()
