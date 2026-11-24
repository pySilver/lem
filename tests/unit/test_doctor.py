"""doctor.py's rules that take facts: the row for a repository whose installed Lem is
other code than the board server runs, the task picker's keymap line and which lines of
a keymap run it, and the tier of each tool, which the table of docs/install.md says
in words.

    python3 -B -m unittest discover -s tests/unit
"""

import ast
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lem import doctor  # noqa: E402 - after the line that puts src on sys.path

# Each row of the machine check that the table of docs/install.md lists, with the words
# of the one table row that names it.
IN_TABLE = {
    "agterm": "[agterm]",
    "agterm skill": "[agterm]",
    "claude": "[Claude Code]",
    "git": "git, and Python",
    "python3": "Python 3.11",
    "revmux": "[revmux]",
    "revmux skill": "[revmux]",
    "cronn": "[cronn]",
    "mailbox-chat": "the mailbox chat",
    "mailbox-chat skill": "the mailbox chat",
    "webrev skill": "webrev",
    "backlog skill": "the backlog recipe",
    "agdoc skill": "agdoc",
    "codex": "[Codex]",
    "plannotator": "[Plannotator]",
    "Jev key": "JEV_API_KEY",
}
# A table row whose word and the check's tier do not agree, and why it is not
# settled here.
UNSETTLED = {
    "the [GitHub CLI]": (
        "gh: the check's row is optional (a machine may hold repositories that do not "
        "land on GitHub), and the table lists it with no word, as needed; "
        "which is right waits for the maintaining session (2026-11-21)"
    ),
}


def install(project: str | None, version: str, scope: str = "project") -> dict:
    return {
        "key": "lem@lem",
        "scope": scope if project else "user",
        "project": project,
        "version": version,
        "folder": None,
    }


def identity(entry: dict) -> str:
    return f"version {entry['version']}"


class Installs(unittest.TestCase):
    def test_a_repository_whose_install_is_other_code_gets_a_row_with_the_two_lines(
        self,
    ) -> None:
        rows = doctor.install_rows(
            "version 0.1.2",
            ["/r/shop", "/r/notes", "/r/bare"],
            [install("/r/shop", "0.1.1"), install("/r/notes", "0.1.2")],
            identity,
        )
        self.assertEqual([row["name"] for row in rows], ["installed Lem: shop"])
        self.assertEqual(
            rows[0]["lines"],
            [
                "cd /r/shop && claude plugin update lem@lem --scope project",
                "lem serve --ensure",
            ],
        )
        self.assertIn(
            (
                "/r/shop has version 0.1.1 of lem@lem installed for the project, and "
                "the board server runs version 0.1.2; the install is the older"
            ),
            rows[0]["detail"],
        )
        self.assertEqual((rows[0]["need"], rows[0]["found"]), ("optional", False))

    def test_an_install_for_the_user_counts_where_the_repository_has_none_of_its_own(
        self,
    ) -> None:
        rows = doctor.install_rows(
            "version 0.1.1", ["/r/shop"], [install(None, "0.1.2")], identity
        )
        self.assertIn("--scope user", rows[0]["line"])
        self.assertIn("the server is the older", rows[0]["detail"])
        self.assertEqual(
            doctor.install_rows(
                "commit abc", ["/r/shop"], [install(None, "0.1.2")], identity
            )[0]["detail"].rsplit("; ", 1)[1],
            "which is the newer is not known",
        )


def tiers() -> dict[str, set[str]]:
    """The tier each row of doctor.py is written with, read from its source: a call of
    `tool(NAME, NEED, ...)`, a call of `skill(NAME, ..., need=NEED)` (required when not
    given), and a row written as a dict with a "name" and a "need". A row that changes
    its tier by a fact of the repository (the Jev key where the correction queue is on)
    is read in the tier it is written with first."""
    found: dict[str, set[str]] = {}
    for node in ast.walk(
        ast.parse((ROOT / "src" / "lem" / "doctor.py").read_text(encoding="utf-8"))
    ):
        name = need = None
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            if (
                node.func.id == "tool"
                and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant)
            ):
                name, need = node.args[0].value, node.args[1].value
            elif node.func.id == "skill":
                given = [
                    word.value.value
                    for word in node.keywords
                    if word.arg == "need" and isinstance(word.value, ast.Constant)
                ]
                name, need = f"{node.args[0].value} skill", (given or ["required"])[0]
        elif isinstance(node, ast.Dict):
            pairs = {
                key.value: value.value
                for key, value in zip(node.keys, node.values, strict=True)
                if isinstance(key, ast.Constant) and isinstance(value, ast.Constant)
            }
            name, need = pairs.get("name"), pairs.get("need")
        if isinstance(name, str) and isinstance(need, str):
            found.setdefault(name, set()).add(need)
    return found


def table() -> list[tuple[str, str]]:
    """Each row of the table under "What you need" in docs/install.md: its first cell,
    and the word for its tier, `required` when the cell has none."""
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    rows = re.search(
        r"^\| Tool \| Lem uses it for \|\n\| --- \| --- \|\n((?:\|.*\n)+)",
        text,
        re.MULTILINE,
    )
    if not rows:
        return []
    out = []
    for line in rows[1].splitlines():
        cell = line.split(" | ")[0].lstrip("| ")
        word = re.search(r":\s*(optional|highly recommended|recommended)$", cell)
        out.append(
            (
                cell,
                "recommended"
                if word and word[1] == "highly recommended"
                else word[1]
                if word
                else "required",
            )
        )
    return out


class Plannotator(unittest.TestCase):
    """The Inbox of the owner's away (away-questions-reach-phone, criterion 7): a
    recommended tool, which fails no check where it is absent."""

    def row(self, path: str | None, said: str | None) -> dict:
        with (
            mock.patch.object(
                doctor.shutil,
                "which",
                lambda binary: path if binary == "plannotator" else None,
            ),
            mock.patch.object(
                doctor,
                "version",
                lambda command: said if command == [path, "--version"] else None,
            ),
        ):
            return doctor.plannotator()

    def test_the_row_is_recommended_with_its_guide_and_names_the_version_found(
        self,
    ) -> None:
        found = self.row("/opt/bin/plannotator", "plannotator 0.29.0")
        self.assertEqual(
            (found["name"], found["need"], found["found"], found["detail"]),
            ("plannotator", "recommended", True, "plannotator 0.29.0"),
        )
        self.assertEqual(found["guide"], "https://github.com/backnotprop/plannotator")
        self.assertIn("while he is away", found["used_for"])
        self.assertEqual(tiers()["plannotator"], {"recommended"})

    def test_without_it_the_row_says_that_nothing_goes_to_the_inbox(self) -> None:
        absent = self.row(None, None)
        self.assertEqual(
            (absent["need"], absent["found"], absent["detail"]),
            ("recommended", False, None),
        )
        self.assertTrue(absent["without_it"].startswith("nothing goes to the Inbox"))


class Keymap(unittest.TestCase):
    """The task picker's line names the marketplace clone's `bin/lem picker`, which runs
    the newest installed release; an older line that names the clone's `picker.py` still
    counts as there."""

    HOME = Path("/Users/ana")
    CLONE = HOME / ".claude" / "plugins" / "marketplaces" / "lem"
    SCRIPTS = (
        CLONE / "bin" / "lem",
        CLONE / "skills" / "lem" / "scripts" / "picker.py",
    )

    def runs(self, said: str) -> Path | None:
        return doctor.keymap_runs(said, self.HOME, self.SCRIPTS)

    def test_a_line_names_the_command_or_the_older_script_by_its_path_or_from_home(
        self,
    ) -> None:
        command, script = self.SCRIPTS
        self.assertEqual(
            self.runs(
                'command "Lem tasks ›" ctrl+cmd+t --error-hud '
                f"/opt/homebrew/bin/python3 {command} picker"
            ),
            command,
        )
        self.assertEqual(
            self.runs(
                'command "Lem tasks ›"  ctrl+cmd+t  --error-hud '
                "/opt/homebrew/bin/python3 ~/.claude/plugins/marketplaces/lem/bin/lem "
                "picker"
            ),
            command,
        )
        # the form of the line the doctor printed before, as a Mac's keymap holds
        # it (2026-11-23)
        self.assertEqual(
            self.runs(
                'command "Lem tasks ›"  ctrl+cmd+t  --error-hud '
                "/opt/homebrew/bin/python3 "
                "~/.claude/plugins/marketplaces/lem/skills/lem/scripts/picker.py"
            ),
            script,
        )
        self.assertEqual(
            self.runs(
                f"command 'Lem tasks' ctrl+cmd+t /usr/bin/python3 {script} --repo /r"
            ),
            script,
        )

    def test_a_line_that_runs_something_else_is_not_the_pickers(self) -> None:
        command, script = self.SCRIPTS
        for said in (
            f"command Board ctrl+cmd+b {command} serve --ensure",
            f"# command Lem ctrl+cmd+t {script}",
            f"keybind ctrl+t {script}",
            "command Lem ctrl+cmd+t ~/elsewhere/skills/lem/scripts/picker.py",
            f"command Lem ctrl+cmd+t {command}",
        ):
            with self.subTest(said=said):
                self.assertIsNone(self.runs(said))

    def row(self, keymap: str | None) -> dict:
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            clone = home / ".claude" / "plugins" / "marketplaces" / "lem"
            (clone / "bin").mkdir(parents=True)
            (clone / "bin" / "lem").write_text("", encoding="utf-8")
            (home / ".claude" / "plugins" / "known_marketplaces.json").write_text(
                json.dumps({"lem": {"installLocation": str(clone)}}), encoding="utf-8"
            )
            (home / ".claude" / "plugins" / "installed_plugins.json").write_text(
                json.dumps(
                    {
                        "version": 2,
                        "plugins": {
                            "lem@lem": [
                                {
                                    "scope": "user",
                                    "installPath": str(home / "cache"),
                                    "version": "0.3.0",
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            if keymap is not None:
                (home / ".config" / "agterm").mkdir(parents=True)
                (home / ".config" / "agterm" / "keymap.conf").write_text(
                    keymap.replace("HOME", str(home)) + "\n", encoding="utf-8"
                )
            with mock.patch.dict(os.environ, {"HOME": str(home)}):
                found = doctor.picker()
            return {**found, "line": found["line"].replace(str(home), "HOME")}

    def test_the_row_gives_the_line_of_the_clones_command_and_counts_an_older_line_as_there(
        self,
    ) -> None:
        absent = self.row(None)
        self.assertFalse(absent["found"])
        self.assertTrue(
            absent["line"].endswith(
                " HOME/.claude/plugins/marketplaces/lem/bin/lem picker"
            ),
            absent["line"],
        )
        current = self.row(
            "command Lem ctrl+cmd+t /usr/bin/python3 "
            "HOME/.claude/plugins/marketplaces/lem/bin/lem picker"
        )
        self.assertEqual(
            (current["found"], current["detail"].rsplit(" ", 3)[1:]),
            (True, ["holds", "the", "line"]),
        )
        older = self.row(
            "command Lem ctrl+cmd+t /usr/bin/python3 "
            "~/.claude/plugins/marketplaces/lem/skills/lem/scripts/picker.py"
        )
        self.assertTrue(older["found"])
        self.assertIn(
            (
                "an older form that still works; the line in its current form, to put "
                "in its place when the owner likes, is this row's line"
            ),
            older["detail"],
        )
        self.assertEqual(older["line"], absent["line"])


class Tiers(unittest.TestCase):
    def test_the_install_guide_says_each_tools_tier_as_the_machine_check_has_it(
        self,
    ) -> None:
        rows, written = table(), tiers()
        self.assertTrue(rows, 'docs/install.md has no table under "What you need"')
        for name, words in IN_TABLE.items():
            with self.subTest(row=name):
                named = [(cell, tier) for cell, tier in rows if words in cell]
                self.assertEqual(
                    len(named), 1, f"one row of the install table names {words!r}"
                )
                self.assertEqual(
                    written.get(name),
                    {named[0][1]},
                    (
                        f"doctor.py writes {name} as {written.get(name)}, and "
                        f"docs/install.md says {named[0][1]}"
                    ),
                )
        for cell, _ in rows:
            with self.subTest(cell=cell[:40]):
                self.assertTrue(
                    any(words in cell for words in [*IN_TABLE.values(), *UNSETTLED]),
                    f"no row of the check is bound to the install table's {cell!r}",
                )


if __name__ == "__main__":
    unittest.main()
