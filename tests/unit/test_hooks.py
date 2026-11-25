"""lem-hook, the one entry of the plugin's hooks (`lem.hooks`): what each selector's
process loads, and that a hook never fails a session, in a package that is not whole
too.

    .venv/bin/python -B -m unittest discover -s tests/unit
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import typing
import unittest
from pathlib import Path

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
    """The environment of a hook in a home of its own, with no board server."""
    return {
        "PATH": os.environ.get("PATH", ""),
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
            env=isolated(home, **task),
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


if __name__ == "__main__":
    unittest.main()
