"""lem_python.find(), the search for a Python of 3.14 or newer that the plugin's hooks
make when the first `python3` is older, over stand-in folders of a PATH.
A stand-in `python3` says its version as Python would; a `python3.N` is known by its
name and never started. And what a hook's process loads when python.py starts it.

    .venv/bin/python -B -m unittest discover -s tests/unit
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
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
        self.stand_in("a", "python3.15")
        newest = self.stand_in(
            "b", "python3.31"
        )  # no upper end: a minor version newer than this file is taken
        self.stand_in("b", "python3.13")
        self.assertEqual(lem_python.find(self.path("a", "b"), fallbacks=()), newest)

    def test_a_python3_new_enough_comes_first_unless_the_caller_is_it(self) -> None:
        first = self.stand_in("a", "python3", says="3 16")
        named = self.stand_in("a", "python3.15")
        self.assertEqual(lem_python.find(self.path("a"), fallbacks=()), first)
        self.assertEqual(
            lem_python.find(self.path("a"), python3=False, fallbacks=()), named
        )

    def test_nothing_new_enough_is_none_and_a_fallback_is_asked_its_version(
        self,
    ) -> None:
        self.stand_in("a", "python3")
        self.stand_in("a", "python3.13")
        old = self.stand_in("brew", "python3", says="3 13")
        self.assertIsNone(lem_python.find(self.path("a"), fallbacks=(old,), uv=()))
        new = self.stand_in("local", "python3", says="3 14")
        self.assertEqual(
            lem_python.find(self.path("a"), fallbacks=(old, new), uv=()), new
        )

    def test_uv_is_asked_last_for_a_python_it_already_has_and_never_to_download_one(
        self,
    ) -> None:
        self.stand_in("a", "python3")
        managed = self.stand_in("uv-home", "python3", says="3 15")
        asked = self.home / "asked"
        uv = self.stand_in("tools", "uv", says=f'{managed}; echo "$@" > {asked}')
        self.assertEqual(
            lem_python.find(self.path("a", "tools"), fallbacks=(), uv=()), managed
        )
        self.assertEqual(
            asked.read_text().split(),
            ["python", "find", "--no-project", "--no-python-downloads", ">=3.14"],
        )
        self.assertEqual(
            lem_python.find(self.path("a"), fallbacks=(), uv=(uv,)), managed
        )  # uv off the PATH, at its usual place
        old = self.stand_in("uv-home", "python3", says="3 13")
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
        ("ask", ["hook-stop"], {}, {"hook_event_name": "Stop"}),
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
            # a file that is gone, and state.py that cannot be read (mode 0, the
            # review of 2026-11-24: its import raised PermissionError)
            for gone, unreadable in (
                (f"{name}.py", False),
                ("state.py", False),
                ("state.py", True),
            ):
                with self.subTest(hook=name, gone=gone, unreadable=unreadable):
                    copy = home / f"{name}-{gone}-{unreadable}" / "src"
                    shutil.copytree(
                        self.SRC / "lem",
                        copy / "lem",
                        ignore=shutil.ignore_patterns("__pycache__"),
                    )
                    if unreadable:
                        (copy / "lem" / gone).chmod(0)
                        self.addCleanup((copy / "lem" / gone).chmod, 0o644)
                    else:
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
            self.skipTest(f"no python3 older than 3.14 at {old}")
        self.runs(old)


class AskStopHook(unittest.TestCase):
    """The plugin's Stop hook, `python.py ask hook-stop`, which runs at the end of every
    turn of every session: what its process loads with no question page open, and that
    it stays silent and ends on its own when agtermctl hangs or cannot start, with a
    stand-in agtermctl for agterm."""

    SRC = Path(__file__).resolve().parents[2] / "src"
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
        """Run the hook through python.py with -X importtime, in a session S1 whose
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
                str(self.SRC / "lem" / "python.py"),
                "ask",
                "hook-stop",
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
        main = str(self.SRC / "lem" / "python.py")
        for words, given in (
            (
                ["ask", "q", "Continue?", "yes", "no", "--no-status", "--timeout", "0"],
                "",
            ),
            (["ask", "hook-stop"], json.dumps({"hook_event_name": "Stop"})),
        ):
            subprocess.run(
                [sys.executable, "-B", main, *words],
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
        main = str(self.SRC / "lem" / "python.py")
        sent = []
        for words, given in (
            (["ask", "q", "Continue?", "yes", "no", "--no-wait"], ""),
            (["ask", "wait", "P1", "--no-status", "--timeout", "0"], ""),
            (["ask", "hook-stop"], json.dumps({"hook_event_name": "Stop"})),
        ):
            subprocess.run(
                [sys.executable, "-B", main, *words],
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
            [
                sys.executable,
                "-B",
                str(self.SRC / "lem" / "python.py"),
                "ask",
                "hook-stop",
            ],
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
