"""lem-hook, the one entry of the plugin's hooks (`lem.hooks`): what each selector's
process loads, that a hook never fails a session, in a package that is not whole too,
and the Stop hook's runs with a stand-in agtermctl.

    .venv/bin/python -B -m unittest discover -s tests/unit
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import typing
import unittest
from pathlib import Path
from unittest import mock

if typing.TYPE_CHECKING:
    from collections.abc import Callable

sys.dont_write_bytecode = True
SRC = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC))
from lem import hooks

# What the console script `lem-hook` runs (pyproject.toml), with SRC, or the copy named
# by the next argument, first on sys.path.
ENTRY = (
    "import sys; sys.path.insert(0, sys.argv.pop(1)); from lem.hooks import cli; cli()"
)
# Each selector's handler as its module ran it alone before lem-hook: its import and
# its call.
ALONE = {
    "corrections": ("corrections", "cmd_hook"),
    "serve": ("serve_hook", "main"),
    "session-start": ("session_hook", "main"),
    "precompact": ("session_hook", "main"),
    "stop": ("ask", "hook_stop"),
}


def isolated(home: Path, **more: str) -> dict:
    """The environment of a hook in a home of its own, with no board server, and a PATH
    with no `lem`, whose SessionStart hook would name one that is not this app's."""
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / "config"),
        "TMPDIR": str(home),
        "LEM_SERVE": "off",
        **more,
    }


class HookStart(unittest.TestCase):
    """The process of each selector loads no module that its handler's own module does
    not, but `lem.hooks` itself: no more than the hook's module loaded when it ran
    alone."""

    HOOKS = (
        ("corrections", {}, {"prompt": "hello there", "session_id": "S1"}),
        ("serve", {}, {"hook_event_name": "SessionStart"}),
        ("session-start", {}, {"hook_event_name": "SessionStart"}),
        (
            "precompact",
            {"LEM_TASK": "gift-note"},
            {"hook_event_name": "PreCompact"},
        ),
        ("stop", {}, {"hook_event_name": "Stop"}),
    )

    def loaded(self, argv: list[str], task: dict, event: dict) -> tuple[set, str, int]:
        """The modules a run of ARGV under this Python loads, from -X importtime, its
        stdout and its exit status, in a folder of no repository with a home of its
        own."""
        home = Path(tempfile.mkdtemp(prefix="lem-hook-"))
        self.addCleanup(shutil.rmtree, home)
        ran = subprocess.run(
            [sys.executable, "-B", "-X", "importtime", *argv],
            input=json.dumps({**event, "cwd": str(home)}),
            capture_output=True,
            text=True,
            cwd=home,
            # the plugin of this checkout, one version with the app: the check of
            # the two versions is part of each start
            env=isolated(home, CLAUDE_PLUGIN_ROOT=str(SRC.parent), **task),
            timeout=30,
            check=False,
        )
        names = {
            line.rsplit("|", 1)[1].strip()
            for line in ran.stderr.splitlines()
            if line.startswith("import time:") and "|" in line
        }
        return names - {"imported package"}, ran.stdout, ran.returncode

    def test_lem_hook_loads_nothing_on_its_way_to_the_handler(self) -> None:
        self.assertEqual(hooks.HANDLERS, ALONE)
        for selector, task, event in self.HOOKS:
            with self.subTest(selector=selector, task=task):
                started, said, status = self.loaded(
                    ["-c", ENTRY, str(SRC), selector], task, event
                )
                module, function = ALONE[selector]
                alone, _, _ = self.loaded(
                    [
                        "-c",
                        (
                            "import sys; sys.path.insert(0, sys.argv.pop(1)); "
                            f"from lem import {module}; {module}.{function}()"
                        ),
                        str(SRC),
                    ],
                    task,
                    event,
                )
                self.assertEqual((said, status), ("", 0))
                self.assertEqual(started - alone, {"lem.hooks"})


class NeverFails(unittest.TestCase):
    """A hook ends with exit 0 and nothing on stdout or stderr, whatever goes wrong: a
    selector of no handler, a handler that raises or exits other than 0, a copy of the
    package that is not whole. A handler's output is printed when it ended well."""

    def run_entry(
        self, src: Path, selector: str, event: dict, home: Path, **more: str
    ) -> tuple[str, str, int]:
        ran = subprocess.run(
            [sys.executable, "-B", "-c", ENTRY, str(src), selector],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=home,
            env=isolated(home, **more),
            timeout=30,
            check=False,
        )
        return ran.stdout, ran.stderr, ran.returncode

    def home(self) -> Path:
        home = Path(tempfile.mkdtemp(prefix="lem-never-"))
        self.addCleanup(shutil.rmtree, home)
        return home

    def test_a_selector_of_no_handler_and_none_at_all_say_nothing(self) -> None:
        home = self.home()
        for selector in ("", "session_hook", "corrections hook", "--help"):
            with self.subTest(selector=selector):
                self.assertEqual(self.run_entry(SRC, selector, {}, home), ("", "", 0))

    def test_a_handler_is_held_and_its_output_printed_only_when_it_ended_well(
        self,
    ) -> None:
        def speaks() -> None:
            print("context")
            print("noise", file=sys.stderr)

        def fails() -> None:
            print("half")
            raise RuntimeError("broken")

        def exits(code: int | str | None) -> Callable[[], None]:
            def handler() -> None:
                print("said")
                sys.exit(code)

            return handler

        self.assertEqual(hooks.held(speaks), "context\n")
        self.assertIsNone(hooks.held(fails))
        self.assertEqual(hooks.held(exits(0)), "said\n")
        self.assertEqual(hooks.held(exits(None)), "said\n")
        self.assertIsNone(hooks.held(exits(2)))
        self.assertIsNone(hooks.held(exits("a message")))

    def copy(self, home: Path, gone: str, *, unreadable: bool = False) -> Path:
        """A copy of the package beside no skills folder, so that `paths` stops, with
        the module GONE removed, or made unreadable."""
        copy = Path(tempfile.mkdtemp(prefix="copy-", dir=home))
        shutil.copytree(
            SRC / "lem", copy / "lem", ignore=shutil.ignore_patterns("__pycache__")
        )
        if gone:
            if unreadable:
                (copy / "lem" / gone).chmod(0)
                self.addCleanup((copy / "lem" / gone).chmod, 0o644)
            else:
                (copy / "lem" / gone).unlink()
        return copy

    def test_a_package_that_is_not_whole_says_nothing(self) -> None:
        home = self.home()
        for selector, module in (
            ("corrections", "corrections.py"),
            ("serve", "serve_hook.py"),
            ("session-start", "session_hook.py"),
            ("precompact", "session_hook.py"),
            ("stop", "ask.py"),
        ):
            for gone, unreadable in (
                ("", False),
                (module, False),
                ("state.py", False),
                ("state.py", True),
            ):
                with self.subTest(selector=selector, gone=gone, unreadable=unreadable):
                    copy = self.copy(home, gone, unreadable=unreadable)
                    self.assertEqual(
                        self.run_entry(
                            copy,
                            selector,
                            {"hook_event_name": "Stop", "cwd": str(home)},
                            home,
                            LEM_TASK="gift-note",
                        ),
                        ("", "", 0),
                    )

    def test_the_correction_hook_of_a_package_not_whole_leaves_no_file_behind(
        self,
    ) -> None:
        # the review of 2026-11-25, finding 2: with the machine's yes, in a repository
        # that uses Lem, `paths` stopped after the hook wrote the owner's words into a
        # file and claimed the message, and both stayed
        home = self.home()
        repo = home / "repo"
        (repo / ".lem").mkdir(parents=True)
        (repo / ".lem" / "settings.toml").write_text("", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (home / "config" / "lem").mkdir(parents=True)
        (home / "config" / "lem" / "machine.toml").write_text(
            "[corrections]\ncollect = true\n", encoding="utf-8"
        )
        said = self.run_entry(
            self.copy(home, ""),
            "corrections",
            {
                "prompt": "never push without asking",
                "cwd": str(repo),
                "session_id": "S1",
            },
            home,
            GIT_CONFIG_GLOBAL="/dev/null",
            GIT_CONFIG_NOSYSTEM="1",
        )
        self.assertEqual(said, ("", "", 0))
        self.assertEqual(
            sorted(path.name for path in home.glob("lem-correction-*")), []
        )
        claims = repo / ".lem" / "state" / "corrections-claims"
        self.assertEqual(sorted(claims.glob("*")) if claims.is_dir() else [], [])


class TwoVersions(unittest.TestCase):
    """The plugin Claude Code loaded and the app, each with a version in
    `.claude-plugin/plugin.json`: the one line that names the one that is behind, and
    what each selector does then."""

    def half(self, version: str | None, *, text: str | None = None) -> str:
        """A folder with a manifest of VERSION (TEXT as the file when given; no file
        when both are None)."""
        folder = Path(tempfile.mkdtemp(prefix="lem-half-"))
        self.addCleanup(shutil.rmtree, folder)
        (folder / ".claude-plugin").mkdir()
        if text is None and version is not None:
            text = json.dumps({"name": "lem", "version": version}, indent=2) + "\n"
        if text is not None:
            (folder / ".claude-plugin" / "plugin.json").write_text(
                text, encoding="utf-8"
            )
        return str(folder)

    def test_equal_versions_say_nothing(self) -> None:
        self.assertIsNone(hooks.version_line(self.half("0.3.1"), self.half("0.3.1")))
        # the same version in other bytes is the same version
        self.assertIsNone(
            hooks.version_line(
                self.half(None, text='{"version": "0.3.1", "name": "lem"}'),
                self.half("0.3.1"),
            )
        )

    def test_the_line_names_the_one_that_is_behind_and_its_update(self) -> None:
        old, new = self.half("0.3.1"), self.half("0.4.0")
        self.assertEqual(
            hooks.version_line(old, new),
            f"lem: Lem's plugin 0.3.1 ({old}) is behind Lem's app 0.4.0; the owner "
            "runs `claude plugin update lem@lem` and starts the session again",
        )
        self.assertEqual(
            hooks.version_line(new, old),
            f"lem: Lem's app 0.3.1 ({old}) is behind Lem's plugin 0.4.0; the owner "
            "runs `brew upgrade pySilver/tap/lem` and starts the session again",
        )
        # 0.10 is newer than 0.9, by numbers
        self.assertIn(
            "Lem's plugin 0.9.0",
            hooks.version_line(self.half("0.9.0"), self.half("0.10.0")) or "",
        )
        # a version that is not numbers has no order: both commands
        said = hooks.version_line(self.half("trial"), self.half("0.3.1")) or ""
        self.assertIn("are two versions", said)
        self.assertIn("`brew upgrade pySilver/tap/lem` and `claude plugin", said)

    def test_a_manifest_that_does_not_read_is_named_by_its_file(self) -> None:
        app = self.half("0.3.1")
        gone = self.half(None)
        self.assertEqual(
            hooks.version_line(gone, app),
            f"lem: {gone}/.claude-plugin/plugin.json does not read (No such file or "
            "directory), so Lem cannot tell whether its plugin and its app are one "
            "version; the owner installs Lem's plugin again",
        )
        self.assertIn(
            f"{gone}/.claude-plugin/plugin.json does not read",
            hooks.version_line(app, gone) or "",
        )
        self.assertTrue(
            (hooks.version_line(app, gone) or "").endswith("installs Lem again")
        )
        broken = self.half(None, text="{")
        self.assertEqual(
            hooks.version_line(broken, app),
            f"lem: {broken}/.claude-plugin/plugin.json names no version, so Lem "
            "cannot tell whether its plugin and its app are one version; the owner "
            "installs that half again",
        )

    def test_the_app_root_is_paths_root(self) -> None:
        from lem import paths

        self.assertEqual(hooks.app_root(), str(paths.ROOT))

    def selected(self, selector: str, plugin: str, env_file: str = "") -> tuple:
        """What run(SELECTOR) prints with CLAUDE_PLUGIN_ROOT at PLUGIN, and whether
        it called its handler, which prints `handled`."""
        called = []

        def handled() -> None:
            called.append(selector)
            print("handled")

        with (
            mock.patch.object(hooks, "handler", lambda _: handled),
            mock.patch.dict(
                os.environ,
                {
                    "CLAUDE_PLUGIN_ROOT": plugin,
                    "CLAUDE_ENV_FILE": env_file,
                    # no `lem` on it, so that the one line said is the versions'
                    "PATH": "",
                },
            ),
        ):
            return hooks.run(selector), called

    def test_with_two_versions_only_session_start_says_so(self) -> None:
        old = self.half("0.0.1")
        for selector in ("corrections", "serve", "precompact", "stop"):
            with self.subTest(selector=selector):
                self.assertEqual(self.selected(selector, old), ("", []))
        said, called = self.selected("session-start", old)
        self.assertEqual(called, [])
        self.assertEqual(
            json.loads(said),
            {"systemMessage": hooks.version_line(old, hooks.app_root() or "")},
        )
        self.assertTrue(said.endswith("\n"))

    def test_with_one_version_each_handler_runs(self) -> None:
        same = hooks.app_root() or ""
        for selector in hooks.HANDLERS:
            with self.subTest(selector=selector):
                self.assertEqual(
                    self.selected(selector, same), ("handled\n", [selector])
                )

    def test_session_start_keeps_the_plugins_folder_for_the_sessions_commands(
        self,
    ) -> None:
        folder = Path(tempfile.mkdtemp(prefix="lem-env-"))
        self.addCleanup(shutil.rmtree, folder)
        env_file = folder / "env.sh"
        env_file.write_text("export OTHER=1\n", encoding="utf-8")
        plugin = folder / "it's a plugin"
        shutil.copytree(
            Path(hooks.app_root() or "") / ".claude-plugin", plugin / ".claude-plugin"
        )
        self.selected("session-start", str(plugin), str(env_file))
        self.selected("stop", str(plugin), str(env_file))
        written = env_file.read_text(encoding="utf-8")
        self.assertEqual(
            written,
            "export OTHER=1\nexport LEM_PLUGIN_ROOT='" + str(folder) + "/it'\\''s a "
            "plugin'\n",
        )
        # the line is shell: it gives the variable the folder as it is
        said = subprocess.run(
            ["/bin/sh", "-c", f'. {env_file}; printf %s "$LEM_PLUGIN_ROOT"'],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(said.stdout, str(plugin))
        # no file named, or one that cannot be written: no line, and the hook goes on
        self.assertEqual(
            self.selected("session-start", str(plugin))[1], ["session-start"]
        )
        self.assertEqual(
            self.selected("session-start", str(plugin), str(folder / "no" / "env"))[1],
            ["session-start"],
        )

    def test_the_command_stops_with_the_same_line(self) -> None:
        from lem import __main__ as entry

        old = self.half("0.0.1")
        with (
            mock.patch.dict(os.environ, {"LEM_PLUGIN_ROOT": old}),
            self.assertRaises(SystemExit) as stopped,
        ):
            entry.same_plugin()
        self.assertEqual(
            stopped.exception.code, hooks.version_line(old, hooks.app_root() or "")
        )
        for plugin in ("", hooks.app_root() or ""):
            with mock.patch.dict(os.environ, {"LEM_PLUGIN_ROOT": plugin}):
                self.assertIsNone(entry.same_plugin())
        self.assertEqual(entry.NO_PLUGIN_CHECK, ("doctor",))


class AnotherLem(unittest.TestCase):
    """The first `lem` on the SessionStart hook's PATH against the app's own command, by
    file identity, never run: one line when it is another file, none when no `lem` is
    on PATH or it is the app's."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="lem-path-"))
        self.addCleanup(shutil.rmtree, self.root)
        self.own = self.command("app/libexec/bin", "#!/bin/sh\necho app\n")

    def command(self, folder: str, text: str, *, mode: int = 0o755) -> str:
        path = self.root / folder / "lem"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        path.chmod(mode)
        return str(path)

    def link(self, folder: str, target: str) -> str:
        path = self.root / folder / "lem"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
        return str(path)

    def search(self, *folders: str) -> str:
        return os.pathsep.join(str(self.root / folder) for folder in folders)

    def test_no_lem_or_the_apps_own_says_nothing(self) -> None:
        (self.root / "empty").mkdir()
        linked = self.link("brew/bin", self.own)
        self.assertIsNone(hooks.other_lem(self.search("empty"), self.own))
        self.assertIsNone(hooks.other_lem("", self.own))
        self.assertIsNone(hooks.other_lem(self.search("app/libexec/bin"), self.own))
        # Homebrew's link to the app is the app
        self.assertIsNone(hooks.other_lem(self.search("empty", "brew/bin"), self.own))
        self.assertTrue(Path(linked).is_symlink())
        # a file that cannot run is no command
        self.command("plain", "not a program", mode=0o644)
        self.assertIsNone(hooks.other_lem(self.search("plain", "brew/bin"), self.own))

    def test_another_lem_first_is_named_with_the_folder_to_put_before_it(self) -> None:
        other = self.command("tools", "#!/bin/sh\necho other\n")
        self.link("brew/bin", self.own)
        self.assertEqual(
            hooks.other_lem(self.search("tools", "brew/bin"), self.own),
            f"lem: {other} comes first on PATH, and it is not Lem's command "
            f"{self.own}; the owner puts {self.root / 'brew/bin'} before "
            f"{self.root / 'tools'} in his PATH",
        )
        # the app not on PATH: its own folder
        self.assertIn(
            f"the owner puts {self.root / 'app/libexec/bin'} before",
            hooks.other_lem(self.search("tools"), self.own) or "",
        )
        # a copy of the same bytes is another file
        copy = self.command("copy", "#!/bin/sh\necho app\n")
        self.assertIn(
            f"lem: {copy} comes first",
            hooks.other_lem(self.search("copy", "brew/bin"), self.own) or "",
        )

    def test_an_app_with_no_command_says_nothing(self) -> None:
        self.command("tools", "#!/bin/sh\n")
        self.assertIsNone(
            hooks.other_lem(self.search("tools"), str(self.root / "gone" / "lem"))
        )

    def test_session_start_says_it_and_keeps_the_tasks_context(self) -> None:
        other = self.command("tools", "#!/bin/sh\n")

        def handled() -> None:
            print("the task's context")

        def silent() -> None:
            pass

        for work, wanted in ((handled, "the task's context\n"), (silent, None)):
            with (
                self.subTest(work=work.__name__),
                mock.patch.object(hooks, "handler", lambda _, work=work: work),
                mock.patch.object(hooks, "own_command", lambda: self.own),
                mock.patch.dict(
                    os.environ,
                    {
                        "PATH": self.search("tools"),
                        "CLAUDE_PLUGIN_ROOT": hooks.app_root() or "",
                        "CLAUDE_ENV_FILE": "",
                    },
                ),
            ):
                said = json.loads(hooks.run("session-start"))
                self.assertTrue(said["systemMessage"].startswith(f"lem: {other} "))
                self.assertEqual(
                    said.get("hookSpecificOutput"),
                    {
                        "hookEventName": "SessionStart",
                        "additionalContext": wanted,
                    }
                    if wanted
                    else None,
                )
                # the other hooks never say it
                self.assertNotIn("systemMessage", hooks.run("precompact"))


class AskStopHook(unittest.TestCase):
    """The plugin's Stop hook, `lem-hook stop`, which runs at the end of every turn of
    every session: what its process loads with no question page open, and that
    it stays silent and ends on its own when agtermctl hangs or cannot start, with a
    stand-in agtermctl for agterm."""

    # What only the page server, the browser fallback, the mermaid download, an
    # embedded image and the command line of `lem ask` use.
    NOT_FOR_THE_HOOK = frozenset(
        {
            "argparse",
            "base64",
            "hashlib",
            "http.client",
            "http.server",
            "mimetypes",
            "secrets",
            "socketserver",
            "urllib.request",
            "webbrowser",
        }
    )
    NO_PAGE = (
        'echo \'{"ok": true, "result": {"tree": {"workspaces": [{"sessions": '
        '[{"id": "S1", "status": "active", "htmlOverlays": []}]}]}}}\'\n'
    )

    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="lem-stop-"))
        self.addCleanup(shutil.rmtree, self.home)

    def run_hook(
        self, standin: str | None, limit: float = 30
    ) -> tuple[set, str, str, int, float]:
        """Run the hook through lem-hook with -X importtime, in a session S1 whose
        agtermctl is a shell script of the body STANDIN (no agterm when None): the
        modules it loaded, its stdout, its stderr without the import lines, its exit
        status and its seconds."""
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / "config"),
            "TMPDIR": str(self.home),
            "LEM_SERVE": "off",
        }
        if standin is not None:
            ctl = self.home / "agtermctl"
            ctl.write_text("#!/bin/sh\n" + standin, encoding="utf-8")
            ctl.chmod(0o755)
            env.update(AGTERM_ENABLED="1", AGTERM_SESSION_ID="S1", AGTERMCTL=str(ctl))
        started = time.monotonic()
        ran = subprocess.run(
            [
                sys.executable,
                "-B",
                "-X",
                "importtime",
                "-c",
                ENTRY,
                str(SRC),
                "stop",
            ],
            input=json.dumps({"hook_event_name": "Stop"}),
            capture_output=True,
            text=True,
            cwd=self.home,
            env=env,
            timeout=limit,
            check=False,
        )
        seconds = time.monotonic() - started
        lines = ran.stderr.splitlines()
        names = {
            line.rsplit("|", 1)[1].strip()
            for line in lines
            if line.startswith("import time:") and "|" in line
        }
        said = "\n".join(line for line in lines if not line.startswith("import time:"))
        return names, ran.stdout, said, ran.returncode, seconds

    def test_with_no_page_open_it_loads_nothing_of_the_page_server(self) -> None:
        for case, standin in (("outside agterm", None), ("no page", self.NO_PAGE)):
            with self.subTest(case=case):
                loaded, out, said, status, _ = self.run_hook(standin)
                self.assertEqual((out, said, status), ("", "", 0))
                self.assertEqual(loaded & self.NOT_FOR_THE_HOOK, set())

    def test_an_agtermctl_that_hangs_ends_the_hook_silent_and_leaves_no_process(
        self,
    ) -> None:
        marker = str(self.home / "hangs")
        _, out, said, status, seconds = self.run_hook(
            f"exec {sys.executable} -c 'import time; time.sleep(60)' {marker}\n"
        )
        self.assertEqual((out, said, status), ("", "", 0))
        self.assertLess(seconds, 10)
        left = subprocess.run(
            ["pgrep", "-f", marker], capture_output=True, text=True, check=False
        )
        self.assertEqual(left.stdout, "")

    @staticmethod
    def entry(words: list[str]) -> list[str]:
        """The arguments of Python that run WORDS: the hook `stop` through lem-hook,
        else `lem WORDS` through the package's entry."""
        if words == ["stop"]:
            return ["-c", ENTRY, str(SRC), "stop"]
        return [str(SRC / "lem" / "__main__.py"), *words]

    def env(self, standin: str) -> dict:
        """The environment of a session S1 whose agtermctl is a shell script of the body
        STANDIN."""
        ctl = self.home / "agtermctl"
        ctl.write_text("#!/bin/sh\n" + standin, encoding="utf-8")
        ctl.chmod(0o755)
        return {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / "config"),
            "TMPDIR": str(self.home),
            "LEM_SERVE": "off",
            "AGTERM_ENABLED": "1",
            "AGTERM_SESSION_ID": "S1",
            "AGTERMCTL": str(ctl),
        }

    def one_page(self, calls: Path) -> dict:
        """The environment of a session S1 whose stand-in agtermctl writes each call
        into CALLS, opens one page P1 and shows it in the tree while it stays
        unanswered."""
        shown = self.home / "shown"
        return self.env(
            f'echo "$*" >> "{calls}"\n'
            'case "$1 $2 $3" in\n'
            '"session overlay open")\n'
            '  while [ $# -gt 0 ]; do [ "$1" = --html ] && echo "$2" > '
            f'"{shown}"; shift; done\n'
            '  echo \'{"ok": true, "result": {"pageID": "P1"}}\' ;;\n'
            "tree*)\n"
            '  printf \'{"ok": true, "result": {"tree": {"workspaces": [{"sessions": '
            '[{"id": "S1", "status": "active", "htmlOverlays": [{"id": "P1", '
            f'"file": "%s"}}]}}]}}]}}}}}}\\n\' "$(cat "{shown}")" ;;\n'
            '*) echo \'{"ok": true, "result": {"pageOutcome": '
            '{"pageID": "P1", "outcome": "pending"}}}\' ;;\n'
            "esac\n"
        )

    def test_a_page_opened_with_no_status_keeps_its_choice_at_the_stop(self) -> None:
        # the review's run of 2026-11-24: `lem ask q 'Continue?' yes no --no-status
        # --timeout 0` leaves its page open and sets no status; the Stop hook then
        # sets none either
        calls = self.home / "calls"
        env = self.one_page(calls)
        for words, given in (
            (
                ["ask", "q", "Continue?", "yes", "no", "--no-status", "--timeout", "0"],
                "",
            ),
            (["stop"], json.dumps({"hook_event_name": "Stop"})),
        ):
            subprocess.run(
                [sys.executable, "-B", *self.entry(words)],
                input=given,
                capture_output=True,
                text=True,
                cwd=self.home,
                env=env,
                timeout=30,
                check=False,
            )
        said = calls.read_text(encoding="utf-8").splitlines()
        self.assertTrue(any(line.startswith("tree") for line in said), said)
        self.assertEqual(
            [line for line in said if line.startswith("session status")], []
        )

    def test_a_wait_with_no_status_holds_for_a_page_opened_without_it(self) -> None:
        # the page opens with the status left to `lem ask`, and the caller's last word,
        # `lem ask wait P1 --no-status`, asks for none: the wait sent none, and the
        # Stop hook sent `blocked --auto-reset` for the page all the same
        calls = self.home / "calls"
        env = self.one_page(calls)
        sent = []
        for words, given in (
            (["ask", "q", "Continue?", "yes", "no", "--no-wait"], ""),
            (["ask", "wait", "P1", "--no-status", "--timeout", "0"], ""),
            (["stop"], json.dumps({"hook_event_name": "Stop"})),
        ):
            subprocess.run(
                [sys.executable, "-B", *self.entry(words)],
                input=given,
                capture_output=True,
                text=True,
                cwd=self.home,
                env=env,
                timeout=30,
                check=False,
            )
            said = calls.read_text(encoding="utf-8").splitlines()
            calls.write_text("", encoding="utf-8")
            sent.append([line for line in said if line.startswith("session status")])
        self.assertEqual(sent, [[], [], []])

    def test_a_stdin_that_stays_open_does_not_keep_the_hook_alive(self) -> None:
        # the review's run of 2026-11-24: the Stop JSON through a pipe that stays open
        with subprocess.Popen(
            [sys.executable, "-B", "-c", ENTRY, str(SRC), "stop"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.home,
            env=self.env(self.NO_PAGE),
        ) as hook:
            stdin = hook.stdin
            if stdin is None:
                self.fail("the hook has no pipe for its input")
            stdin.write(json.dumps({"hook_event_name": "Stop"}).encode())
            stdin.flush()
            try:
                status = hook.wait(timeout=10)
            except subprocess.TimeoutExpired:
                hook.kill()
                hook.wait()
                status = None
            stdin.close()
            out = hook.stdout.read() if hook.stdout else b""
        self.assertEqual((status, out), (0, b""))

    def test_a_status_call_that_cannot_start_prints_nothing(self) -> None:
        # the tree shows a page of lem-ask twice; after the second look the stand-in
        # can no longer be started, so the hook's status call fails
        page = self.home / "lem-ask" / "p.html"
        count = self.home / "looks"
        _, out, said, status, _ = self.run_hook(
            f'echo x >> "{count}"\n'
            f'[ "$(wc -l < "{count}")" -ge 2 ] && chmod -x "$0"\n'
            'echo \'{"ok": true, "result": {"tree": {"workspaces": [{"sessions": '
            f'[{{"id": "S1", "status": "active", "htmlOverlays": [{{"id": "P1", '
            f'"file": "{page}"}}]}}]}}]}}}}}}\'\n'
        )
        self.assertEqual(count.read_text().count("x"), 2)
        self.assertEqual((out, said, status), ("", "", 0))


if __name__ == "__main__":
    unittest.main()
