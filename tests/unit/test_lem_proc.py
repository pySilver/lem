"""lem_proc.py's rules: the stop of a process group sends a term, then a kill to what
is left; waiting for the whole group, a group that ends within its grace gets no kill;
waiting for the first process only, what it left gets the kill as soon as it ended; a
group that is gone ends the stop.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import importlib
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
lem_proc = importlib.import_module("lem_proc")

# A leader that says a term and ends at once, and a process it leaves in its group,
# which says a term and ends WAIT seconds later, or ignores it when WAIT is "never".
GROUP = """
(trap 'echo child-term >> "$1"; [ "$2" = never ] || { sleep "$2"; echo child-done >> "$1"; exit 0; }' TERM
 echo child-ready >> "$1"; while :; do sleep 0.02; done) &
trap 'echo leader-term >> "$1"; [ "$3" = stays ] || exit 0' TERM
echo leader-ready >> "$1"
while :; do sleep 0.02; done
"""


class Stop(unittest.TestCase):
    def setUp(self) -> None:
        made = tempfile.TemporaryDirectory()
        self.addCleanup(made.cleanup)
        self.log = Path(made.name) / "said"

    def group(self, wait: str, leader: str = "ends") -> subprocess.Popen:
        proc = subprocess.Popen(
            ["bash", "-c", GROUP, "group", str(self.log), wait, leader],
            start_new_session=True,
        )
        self.addCleanup(self.end, proc)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            said = self.said()
            if "leader-ready" in said and "child-ready" in said:
                return proc
            time.sleep(0.02)
        raise self.failureException("the group never got ready")

    @staticmethod
    def end(proc: subprocess.Popen) -> None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()

    def said(self) -> list[str]:
        return self.log.read_text().split() if self.log.exists() else []

    @staticmethod
    def gone(proc: subprocess.Popen) -> bool:
        """Whether no process of the group is left, given a second for a kill sent
        to land: a killed process of the group is the system's to reap."""
        deadline = time.monotonic() + 1
        while True:
            try:
                os.killpg(proc.pid, 0)
            except (ProcessLookupError, PermissionError):
                return True
            if time.monotonic() > deadline:
                return False
            time.sleep(0.02)

    def test_the_whole_group_that_ends_in_its_grace_gets_no_kill(self) -> None:
        proc = self.group("0.2")
        lem_proc.stop_group(proc, 3, 3, whole_group=True)
        self.assertIn("child-done", self.said())
        self.assertEqual(proc.returncode, 0)

    def test_the_whole_group_left_after_its_grace_gets_the_kill(self) -> None:
        proc = self.group("never")
        began = time.monotonic()
        lem_proc.stop_group(proc, 0.4, 3, whole_group=True)
        self.assertGreaterEqual(time.monotonic() - began, 0.4)
        self.assertIn("child-term", self.said())
        self.assertTrue(self.gone(proc))

    def test_what_the_first_process_left_gets_the_kill_when_it_ended(self) -> None:
        proc = self.group("5")
        began = time.monotonic()
        lem_proc.stop_group(proc, 3, 3, whole_group=False)
        self.assertLess(time.monotonic() - began, 5)
        self.assertNotIn("child-done", self.said())
        self.assertTrue(self.gone(proc))

    def test_a_first_process_that_stays_gets_the_kill_after_its_grace(self) -> None:
        proc = self.group("0", leader="stays")
        lem_proc.stop_group(proc, 0.4, 3, whole_group=False)
        self.assertEqual(proc.returncode, -9)
        self.assertTrue(self.gone(proc))

    def test_a_group_that_is_gone_ends_the_stop(self) -> None:
        proc = self.group("0")
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        self.assertTrue(self.gone(proc))
        for whole in (True, False):
            lem_proc.stop_group(proc, 3, 3, whole_group=whole)
        self.assertEqual(proc.returncode, -9)


if __name__ == "__main__":
    unittest.main()
