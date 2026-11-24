"""state.py's runner of git: `run_git` gives every exit back with what git said,
under the time limit and with the stdin its caller passes; `git` over it gives the
output of a run that went well and None for every other.

    python3 -B -m unittest discover -s tests/unit
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import state as lem_state

# the name git gives an empty file
EMPTY_BLOB = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


class RunGit(unittest.TestCase):
    def setUp(self) -> None:
        made = tempfile.TemporaryDirectory()
        self.addCleanup(made.cleanup)
        self.repo = Path(made.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def test_a_run_is_given_back_whole_and_a_failure_is_not_raised(self) -> None:
        ran = lem_state.run_git(self.repo, ["rev-parse", "--is-inside-work-tree"])
        self.assertEqual((ran.returncode, ran.stdout), (0, "true\n"))
        self.assertEqual(ran.args[:3], ["git", "-C", str(self.repo)])
        failed = lem_state.run_git(self.repo, ["rev-parse", "--verify", "nothing"])
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(failed.stderr)

    def test_a_closed_stdin_reads_as_empty(self) -> None:
        ran = lem_state.run_git(
            self.repo, ["hash-object", "--stdin"], stdin=subprocess.DEVNULL
        )
        self.assertEqual(ran.stdout.strip(), EMPTY_BLOB)

    def test_the_time_limit_is_raised_by_the_runner_and_none_by_git(self) -> None:
        with self.assertRaises(subprocess.TimeoutExpired):
            lem_state.run_git(self.repo, ["status"], 0.000001)
        self.assertIsNone(lem_state.git(self.repo, ["status"], 0.000001))

    def test_git_gives_the_output_or_none(self) -> None:
        self.assertEqual(
            lem_state.git(self.repo, ["rev-parse", "--is-inside-work-tree"], None),
            "true\n",
        )
        self.assertIsNone(lem_state.git(self.repo, ["rev-parse", "nothing"], None))
        self.assertIsNone(lem_state.git(self.repo / "gone", ["status"], None))


if __name__ == "__main__":
    unittest.main()
