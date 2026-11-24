"""lem_python.find(), the search for a Python of 3.11 or newer that `bin/lem` and the
plugin's hooks make when the first `python3` is older, over stand-in folders of a PATH.
A stand-in `python3` says its version as Python would; a `python3.N` is known by its
name and never started. And what a hook's process loads when python.py starts it.

    python3 -B -m unittest discover -s tests/unit
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import python as lem_python


class Find(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="lem-python-"))
        self.addCleanup(shutil.rmtree, self.home)

    def stand_in(self, folder: str, name: str, says: str = "3 9") -> str:
        """An executable NAME in FOLDER under the test's home that prints SAYS, as
        `python3 -c` would."""
        path = self.home / folder / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"#!/bin/sh\necho {says}\n", encoding="utf-8")
        path.chmod(0o755)
        return str(path)

    def path(self, *folders: str) -> str:
        return os.pathsep.join(str(self.home / folder) for folder in folders)

    def test_an_old_python3_gives_way_to_the_newest_python3_n_on_the_path(self) -> None:
        self.stand_in("a", "python3")
        self.stand_in("a", "python3.12")
        newest = self.stand_in(
            "b", "python3.31"
        )  # no upper end: a minor version newer than this file is taken
        self.stand_in("b", "python3.10")
        self.assertEqual(lem_python.find(self.path("a", "b"), fallbacks=()), newest)

    def test_a_python3_new_enough_comes_first_unless_the_caller_is_it(self) -> None:
        first = self.stand_in("a", "python3", says="3 13")
        named = self.stand_in("a", "python3.12")
        self.assertEqual(lem_python.find(self.path("a"), fallbacks=()), first)
        self.assertEqual(
            lem_python.find(self.path("a"), python3=False, fallbacks=()), named
        )

    def test_nothing_new_enough_is_none_and_a_fallback_is_asked_its_version(
        self,
    ) -> None:
        self.stand_in("a", "python3")
        self.stand_in("a", "python3.10")
        old = self.stand_in("brew", "python3", says="3 10")
        self.assertIsNone(lem_python.find(self.path("a"), fallbacks=(old,), uv=()))
        new = self.stand_in("local", "python3", says="3 11")
        self.assertEqual(
            lem_python.find(self.path("a"), fallbacks=(old, new), uv=()), new
        )

    def test_uv_is_asked_last_for_a_python_it_already_has_and_never_to_download_one(
        self,
    ) -> None:
        self.stand_in("a", "python3")
        managed = self.stand_in("uv-home", "python3", says="3 12")
        asked = self.home / "asked"
        uv = self.stand_in("tools", "uv", says=f'{managed}; echo "$@" > {asked}')
        self.assertEqual(
            lem_python.find(self.path("a", "tools"), fallbacks=(), uv=()), managed
        )
        self.assertEqual(
            asked.read_text().split(),
            ["python", "find", "--no-project", "--no-python-downloads", ">=3.11"],
        )
        self.assertEqual(
            lem_python.find(self.path("a"), fallbacks=(), uv=(uv,)), managed
        )  # uv off the PATH, at its usual place
        old = self.stand_in("uv-home", "python3", says="3 10")
        self.assertIsNone(
            lem_python.find(self.path("a", "tools"), fallbacks=(), uv=())
        )  # what uv names is asked its version
        self.assertEqual(old, managed)


class HookStart(unittest.TestCase):
    """The process that runs a hook through python.py, as the newer Python runs it after
    an old python3 found it, loads no module that the hook's own module does not: no
    more than the hook's script loaded when it was started by its path."""

    SRC = Path(__file__).resolve().parents[2] / "src"
    HOOKS = (
        ("corrections", ["hook"], {}, {"prompt": "hello there", "session_id": "S1"}),
        ("serve_hook", [], {}, {"hook_event_name": "SessionStart"}),
        ("session_hook", [], {}, {"hook_event_name": "SessionStart"}),
        (
            "session_hook",
            [],
            {"LEM_TASK": "gift-note"},
            {"hook_event_name": "PreCompact"},
        ),
    )

    def loaded(self, argv: list[str], task: dict, event: dict) -> tuple[set, str, int]:
        """The modules a run of ARGV under this Python loads, from -X importtime, its
        stdout and its exit status, in a folder of no repository with a home of its
        own."""
        home = tempfile.mkdtemp(prefix="lem-hook-")
        self.addCleanup(shutil.rmtree, home)
        ran = subprocess.run(
            [sys.executable, "-B", "-X", "importtime", *argv],
            input=json.dumps({**event, "cwd": home}),
            capture_output=True,
            text=True,
            cwd=home,
            env={
                "PATH": os.environ.get("PATH", ""),
                "HOME": home,
                "XDG_CONFIG_HOME": str(Path(home) / "config"),
                "LEM_SERVE": "off",
                **task,
            },
            timeout=30,
            check=False,
        )
        names = {
            line.rsplit("|", 1)[1].strip()
            for line in ran.stderr.splitlines()
            if line.startswith("import time:") and "|" in line
        }
        return names - {"imported package"}, ran.stdout, ran.returncode

    def test_python_py_loads_nothing_on_its_way_to_the_hooks_module(self) -> None:
        for name, args, task, event in self.HOOKS:
            with self.subTest(hook=name, task=task):
                started, said, status = self.loaded(
                    [str(self.SRC / "lem" / "python.py"), name, *args], task, event
                )
                alone, _, _ = self.loaded(
                    [
                        "-c",
                        (
                            "import sys; sys.path[0] = sys.argv.pop(1); "
                            f"from lem import {name}; {name}.main()"
                        ),
                        str(self.SRC),
                        *args,
                    ],
                    task,
                    event,
                )
                self.assertEqual((said, status), ("", 0))
                self.assertEqual(started - alone, set())


class FolderNotWhole(unittest.TestCase):
    """A hook of `hooks/hooks.json` in a copy of the plugin's package that is not whole:
    its own module file is gone, or `state.py`, which the correction hook imports at its
    top. The hook ends as it does on a machine with no Python: nothing printed, exit 0."""

    SRC = Path(__file__).resolve().parents[2] / "src"
    HOOKS = (
        ("corrections", ["hook"], {"prompt": "hello there", "session_id": "S1"}),
        ("serve_hook", [], {"hook_event_name": "SessionStart"}),
        ("session_hook", [], {"hook_event_name": "SessionStart"}),
    )

    def runs(self, python: str) -> None:
        """Each hook under PYTHON, in a copy without its module and one without
        state.py. A `python3.N` of this Python stands first on PATH, so that an old
        PYTHON finds it."""
        home = Path(tempfile.mkdtemp(prefix="lem-unwhole-"))
        self.addCleanup(shutil.rmtree, home)
        newer = home / "bin" / f"python3.{sys.version_info[1]}"
        newer.parent.mkdir()
        newer.symlink_to(os.path.realpath(sys.executable))
        for name, args, event in self.HOOKS:
            for gone in (f"{name}.py", "state.py"):
                with self.subTest(hook=name, gone=gone):
                    copy = home / f"{name}-{gone}" / "src"
                    shutil.copytree(
                        self.SRC / "lem",
                        copy / "lem",
                        ignore=shutil.ignore_patterns("__pycache__"),
                    )
                    (copy / "lem" / gone).unlink()
                    ran = subprocess.run(
                        [python, "-B", str(copy / "lem" / "python.py"), name, *args],
                        input=json.dumps({**event, "cwd": str(home)}),
                        capture_output=True,
                        text=True,
                        cwd=home,
                        env={
                            "PATH": f"{newer.parent}{os.pathsep}/usr/bin:/bin",
                            "HOME": str(home),
                            "XDG_CONFIG_HOME": str(home / "config"),
                            "LEM_SERVE": "off",
                        },
                        timeout=30,
                        check=False,
                    )
                    self.assertEqual(
                        (ran.stdout, ran.stderr, ran.returncode), ("", "", 0)
                    )

    def test_a_hook_whose_files_are_gone_prints_nothing_and_exits_0(self) -> None:
        self.runs(sys.executable)

    def test_so_it_does_under_an_old_python3_that_finds_a_newer_one(self) -> None:
        old = "/usr/bin/python3"
        if not lem_python.runnable(old) or (lem_python.version(old) or (0, 0)) >= (
            lem_python.FLOOR
        ):
            self.skipTest(f"no python3 older than 3.11 at {old}")
        self.runs(old)


if __name__ == "__main__":
    unittest.main()
