"""doctor.py's rules that take facts: the row for a repository whose installed Lem is
other code than the board server runs, the task picker's keymap line and which lines of
a keymap run it, and the tier of each tool, which the table of docs/install.md says
in words.

    .venv/bin/python -B -m unittest discover -s tests/unit
"""

import ast
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lem import doctor

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


class HookEntries(unittest.TestCase):
    """Which entries of a settings file's `UserPromptSubmit` hooks are the correction
    hook: the plugin's line, the app's entry, and nothing else."""

    PLUGIN = '/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" corrections 2>/dev/null || :'

    def entries(self, *commands: str) -> list[str]:
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "settings.json"
            hooks = [{"type": "command", "command": line} for line in commands]
            file.write_text(
                json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": hooks}]}}),
                encoding="utf-8",
            )
            return [hook["command"] for hook in doctor.hook_entries(file)]

    def test_the_plugins_line_and_the_apps_entry_are_the_hook(self) -> None:
        lines = [
            self.PLUGIN,
            "sh /Users/o/lem/hooks/run corrections",
            "/opt/homebrew/opt/lem/libexec/bin/lem-hook corrections",
            "LEM_JEV=/x/jev lem-hook corrections",
        ]
        self.assertEqual(self.entries(*lines), lines)

    def test_another_selector_or_an_old_line_is_not(self) -> None:
        self.assertEqual(
            self.entries(
                '/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" serve 2>/dev/null || :',
                "lem-hook session-start",
                "lem corrections list",
                "lem-hook correctionsx",
                # the lines before the app, which no install has: no reader of them
                'python3 "${CLAUDE_PLUGIN_ROOT}/src/lem/python.py" corrections hook',
                "python3 /elsewhere/corrections.py hook",
            ),
            [],
        )


class HookModules(unittest.TestCase):
    """The row of the plugin's hooks: a hook that cannot start ends with nothing
    printed (`lem.hooks`), so this row is where the owner learns it. The review of
    2026-11-24, and the plugin's `hooks/run` since the hooks start the app."""

    PACKAGE = ROOT / "src" / "lem"
    HANDLED = ("hooks", "serve_hook", "session_hook", "ask")

    def test_the_plugin_and_the_app_of_this_repository_are_whole(self) -> None:
        row = doctor.hook_modules(ROOT, self.PACKAGE)
        self.assertEqual(
            (row["name"], row["need"], row["found"]), ("hook modules", "required", True)
        )
        self.assertTrue(
            row["detail"].startswith(
                "corrections, serve, session-start, precompact, stop from "
            ),
            row["detail"],
        )
        for name in ("hooks.py", "corrections.py", "serve_hook.py", "session_hook.py"):
            self.assertIn(name, row["detail"])

    def plugin(self, folder: str, manifest: str | None, *, run: bool = True) -> Path:
        """A plugin's folder in FOLDER whose hooks file holds MANIFEST (none when None),
        with `hooks/run` unless RUN is false."""
        root = Path(folder) / "plugin"
        (root / "hooks").mkdir(parents=True)
        if manifest is not None:
            (root / "hooks" / "hooks.json").write_text(manifest, encoding="utf-8")
        if run:
            (root / "hooks" / "run").write_text("exit 0\n", encoding="utf-8")
        return root

    def package(self, folder: str) -> Path:
        """An app's package in FOLDER with each module the hooks start whole, and
        `corrections.py` importing `state.py`, which is not there."""
        package = Path(folder) / "app" / "lem"
        package.mkdir(parents=True)
        for name in self.HANDLED:
            (package / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
        (package / "corrections.py").write_text(
            "import json\n\nfrom lem import state as lem_state\n\n\n"
            "def later() -> None:\n    from lem import project\n",
            encoding="utf-8",
        )
        return package

    def lines(self) -> str:
        return (ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8")

    def test_a_module_that_is_gone_or_does_not_compile_is_named_with_the_fix(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            package = self.package(folder)
            (package / "corrections.py").unlink()
            (package / "serve_hook.py").write_text("def (:\n", encoding="utf-8")
            row = doctor.hook_modules(self.plugin(folder, self.lines()), package)
        self.assertFalse(row["found"])
        self.assertEqual(
            row["detail"],
            "corrections.py is missing; serve_hook.py does not compile (line 1)",
        )
        self.assertIn("Lem's app again", row["without_it"])

    def test_a_hooks_file_that_is_gone_or_reads_another_way_is_a_failing_row(
        self,
    ) -> None:
        # the review of 2026-11-24 on 233a4728: each gave `found` true, and the last
        # raised AttributeError
        line = '/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" {} 2>/dev/null || :'
        for manifest, said in (
            (None, "hooks/hooks.json is missing"),
            ("{", "hooks/hooks.json is not JSON (line 1)"),
            ('{"hooks": ["Stop"]}', "hooks/hooks.json is not a table of hooks"),
            ("[]", "hooks/hooks.json is not a table of hooks"),
            (
                '{"hooks": {"Stop": [{"hooks": "x"}]}}',
                "hooks/hooks.json is not a table of hooks",
            ),
            # a line of another form, the line before the app among them, and a
            # selector lem-hook does not know
            (
                json.dumps(
                    {"hooks": {"Stop": [{"hooks": [{"command": "python3 x.py stop"}]}]}}
                ),
                (
                    "hooks/hooks.json has a line that is not Lem's: 'python3 x.py "
                    "stop', which no lem-hook runs"
                ),
            ),
            (
                json.dumps(
                    {
                        "hooks": {
                            "Stop": [{"hooks": [{"command": line.format("sleep")}]}]
                        }
                    }
                ),
                (
                    "hooks/hooks.json has a line that is not Lem's: "
                    f"{line.format('sleep')!r}, which no lem-hook runs"
                ),
            ),
        ):
            with (
                self.subTest(manifest=manifest),
                tempfile.TemporaryDirectory() as folder,
            ):
                package = self.package(folder)
                (package / "state.py").write_text("x = 1\n", encoding="utf-8")
                row = doctor.hook_modules(self.plugin(folder, manifest), package)
                self.assertEqual((row["found"], row["detail"]), (False, said))
                self.assertIn("installs the plugin again", row["without_it"])

    def test_a_plugin_with_no_hooks_run_is_a_failing_row(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            package = self.package(folder)
            (package / "state.py").write_text("x = 1\n", encoding="utf-8")
            row = doctor.hook_modules(
                self.plugin(folder, self.lines(), run=False), package
            )
        self.assertEqual((row["found"], row["detail"]), (False, "hooks/run is missing"))

    def test_a_hooks_py_that_imports_the_package_at_its_top_is_a_failing_row(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            package = self.package(folder)
            (package / "state.py").write_text("x = 1\n", encoding="utf-8")
            (package / "hooks.py").write_text(
                "from lem import project\n", encoding="utf-8"
            )
            (package / "project.py").write_text("x = 1\n", encoding="utf-8")
            row = doctor.hook_modules(self.plugin(folder, self.lines()), package)
        self.assertFalse(row["found"])
        self.assertEqual(
            row["detail"],
            "hooks.py imports project at its top, which every hook would pay at its "
            "start",
        )

    def test_a_module_that_a_hooks_module_imports_at_its_top_is_checked(
        self,
    ) -> None:
        # the review of 2026-11-24: with `state.py` gone, which corrections.py imports
        # at its top, the row was whole and the hook ended with nothing printed
        with tempfile.TemporaryDirectory() as folder:
            package = self.package(folder)
            plugin = self.plugin(folder, self.lines())
            row = doctor.hook_modules(plugin, package)
            self.assertEqual(
                (row["found"], row["detail"]), (False, "state.py is missing")
            )
            # an import inside a function is the hook's later path, which its own
            # call reports
            (package / "state.py").write_text("x = 1\n", encoding="utf-8")
            row = doctor.hook_modules(plugin, package)
        self.assertTrue(row["found"])
        self.assertIn("state.py", row["detail"])
        self.assertNotIn("project.py", row["detail"])


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
    """The task picker's line names the app's command by the path an update keeps,
    Homebrew's `opt/lem/bin/lem` when the app is under it, else the `lem` beside the
    app's Python; a line of a Lem before the app is one that no longer works."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="lem-keymap-")).resolve()
        self.addCleanup(shutil.rmtree, self.root)

    def app(self, folder: str) -> Path:
        """An app's environment at FOLDER: its `bin/python` and `bin/lem`."""
        env = self.root / folder
        (env / "bin").mkdir(parents=True)
        for name in ("python", "lem"):
            (env / "bin" / name).write_text("#!/bin/sh\n", encoding="utf-8")
            (env / "bin" / name).chmod(0o755)
        return env

    def test_homebrews_opt_path_when_the_app_is_under_it(self) -> None:
        brew = self.root / "homebrew"
        env = self.app("homebrew/Cellar/lem/0.4.0/libexec")
        (brew / "Cellar" / "lem" / "0.4.0" / "bin").mkdir()
        (brew / "Cellar" / "lem" / "0.4.0" / "bin" / "lem").symlink_to(
            env / "bin" / "lem"
        )
        (brew / "opt").mkdir()
        (brew / "opt" / "lem").symlink_to(brew / "Cellar" / "lem" / "0.4.0")
        self.assertEqual(
            doctor.stable_lem(str(env / "bin" / "python"), str(env), (brew,)),
            brew / "opt" / "lem" / "bin" / "lem",
        )
        # an app elsewhere, a checkout's .venv or a uv tool: the lem beside its
        # Python, resolved
        venv = self.app("checkout/.venv")
        self.assertEqual(
            doctor.stable_lem(str(venv / "bin" / "python"), str(venv), (brew,)),
            venv / "bin" / "lem",
        )
        # no lem beside the Python: no line
        (venv / "bin" / "lem").unlink()
        self.assertIsNone(
            doctor.stable_lem(str(venv / "bin" / "python"), str(venv), (brew,))
        )

    def test_a_line_runs_the_command_by_its_path_a_link_or_from_home(self) -> None:
        env = self.app("app")
        command = env / "bin" / "lem"
        (self.root / "bin").mkdir()
        (self.root / "bin" / "lem").symlink_to(command)
        for said in (
            f'command "Lem tasks ›" ctrl+cmd+t --error-hud {command} picker',
            f"command Lem  ctrl+cmd+t  {self.root / 'bin' / 'lem'} picker",
            "command Lem ctrl+cmd+t ~/app/bin/lem picker",
        ):
            with self.subTest(said=said):
                self.assertTrue(doctor.keymap_runs(said, self.root, command))
        for said in (
            f"command Board ctrl+cmd+b {command} serve --ensure",
            f"# command Lem ctrl+cmd+t {command} picker",
            f"keybind ctrl+t {command} picker",
            "command Lem ctrl+cmd+t ~/elsewhere/lem picker",
            f"command Lem ctrl+cmd+t {command}",
        ):
            with self.subTest(said=said):
                self.assertFalse(doctor.keymap_runs(said, self.root, command))

    def row(self, keymap: str | None, command: Path | None) -> dict:
        home = self.root / "home"
        (home / ".config" / "agterm").mkdir(parents=True, exist_ok=True)
        file = home / ".config" / "agterm" / "keymap.conf"
        file.unlink(missing_ok=True)
        if keymap is not None:
            file.write_text(keymap + "\n", encoding="utf-8")
        with (
            mock.patch.dict(os.environ, {"HOME": str(home)}),
            mock.patch.object(doctor, "stable_lem", lambda: command),
        ):
            return doctor.picker()

    def test_the_row_gives_the_line_and_names_an_old_line_that_no_longer_works(
        self,
    ) -> None:
        command = self.app("app") / "bin" / "lem"
        line = f'command "Lem tasks ›" ctrl+cmd+t --error-hud {command} picker'
        absent = self.row(None, command)
        self.assertEqual((absent["found"], absent["line"]), (False, line))
        current = self.row(line, command)
        self.assertEqual(
            (current["found"], current["detail"].rsplit(" ", 3)[1:]),
            (True, ["holds", "the", "line"]),
        )
        for old in (
            (
                "command Lem ctrl+cmd+t /usr/bin/python3 "
                "~/.claude/plugins/marketplaces/lem/skills/lem/scripts/picker.py"
            ),
            (
                'command "Lem tasks ›" ctrl+cmd+t --error-hud /opt/homebrew/bin/'
                "python3 /Users/o/.claude/plugins/marketplaces/lem/bin/lem picker"
            ),
        ):
            with self.subTest(old=old):
                row = self.row(old, command)
                self.assertFalse(row["found"])
                self.assertEqual(row["line"], line)
                self.assertIn(
                    "holds a line of a Lem before the app, which no longer works: "
                    + old,
                    row["detail"],
                )
                self.assertIn(
                    "the owner puts this row's line in its place and runs "
                    "`agtermctl keymap reload`",
                    row["detail"],
                )
        none = self.row(None, None)
        self.assertEqual((none["found"], none["line"]), (False, None))
        self.assertIn("the owner installs Lem again", none["without_it"])


class PluginFolder(unittest.TestCase):
    """The plugin whose files the row of the hooks reads: Lem's install for the
    repository, else for the user, when it is on; else the app's own data."""

    def test_the_install_for_the_repository_then_for_the_user_else_the_apps(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder).resolve()
            repo = home / "repo"
            mine, users = home / "cache" / "project", home / "cache" / "user"
            for made in (repo, mine, users):
                made.mkdir(parents=True)
            (home / ".claude" / "plugins").mkdir(parents=True)

            def listed(*entries: dict) -> Path:
                (home / ".claude" / "plugins" / "installed_plugins.json").write_text(
                    json.dumps({"version": 2, "plugins": {"lem@lem": list(entries)}}),
                    encoding="utf-8",
                )
                return doctor.plugin_folder(home, repo)

            project = {
                "scope": "project",
                "projectPath": str(repo),
                "installPath": str(mine),
            }
            user = {"scope": "user", "installPath": str(users)}
            self.assertEqual(listed(user, project), mine)
            self.assertEqual(listed(user), users)
            self.assertEqual(listed(), doctor.paths.ROOT)
            # a folder that is not there, or an install the settings switch off
            self.assertEqual(
                listed({**user, "installPath": str(home / "gone")}), doctor.paths.ROOT
            )
            (repo / ".claude").mkdir()
            (repo / ".claude" / "settings.local.json").write_text(
                json.dumps({"enabledPlugins": {"lem@lem": False}}), encoding="utf-8"
            )
            self.assertEqual(listed(project), doctor.paths.ROOT)


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
