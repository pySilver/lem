"""lem_files.py's rules: a file is written whole under a name of its own first, the
caller's name when it gives one, in a folder that is there unless the caller asks for
it; a JSON record has the one form of Lem's records; a held file holds its thread lock
and its lock file until the block ends, however it ends.

    python3 -B -m unittest discover -s tests/unit
"""

import fcntl
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import files as lem_files  # noqa: E402 - after the line that puts src on sys.path


class Whole(unittest.TestCase):
    def setUp(self) -> None:
        made = tempfile.TemporaryDirectory()
        self.addCleanup(made.cleanup)
        self.folder = Path(made.name)
        self.renamed: list[str] = []
        real = Path.replace

        def spy(path: Path, target: Path) -> Path:
            self.renamed.append(path.name)
            return real(path, target)

        patcher = mock.patch.object(Path, "replace", spy)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_text_goes_under_name_pid_new_first_and_nothing_is_left(self) -> None:
        file = self.folder / "pr.md"
        file.write_text("old", encoding="utf-8")
        lem_files.write_whole(file, "new é\n")
        self.assertEqual(file.read_text(encoding="utf-8"), "new é\n")
        self.assertEqual(self.renamed, [f"pr.md.{os.getpid()}.new"])
        self.assertEqual([p.name for p in self.folder.iterdir()], ["pr.md"])

    def test_a_name_of_the_callers_own_is_the_one_written_first(self) -> None:
        file = self.folder / "record.json"
        lem_files.write_whole(file, "x", fresh=self.folder / ".record.7")
        self.assertEqual(self.renamed, [".record.7"])
        self.assertEqual(file.read_text(encoding="utf-8"), "x")

    def test_a_folder_that_is_not_there_is_made_only_when_asked(self) -> None:
        file = self.folder / "night" / "2026-11-24.json"
        with self.assertRaises(FileNotFoundError):
            lem_files.write_whole(file, "x")
        self.assertFalse(file.parent.exists())
        lem_files.write_whole(file, "x", make_folder=True)
        self.assertEqual(file.read_text(encoding="utf-8"), "x")

    def test_a_record_is_json_with_two_spaces_its_characters_and_a_line_end(
        self,
    ) -> None:
        file = self.folder / "a" / "record.json"
        lem_files.write_json(
            file, {"said": "é", "n": [1]}, fresh=file.parent / ".r", make_folder=True
        )
        self.assertEqual(
            file.read_text(encoding="utf-8"),
            '{\n  "said": "é",\n  "n": [\n    1\n  ]\n}\n',
        )
        self.assertEqual(self.renamed, [".r"])


class Held(unittest.TestCase):
    def setUp(self) -> None:
        made = tempfile.TemporaryDirectory()
        self.addCleanup(made.cleanup)
        self.file = Path(made.name) / "home" / "push.lock"

    def free(self) -> bool:
        """Whether another holder could take the lock file now."""
        with self.file.open("a") as other:
            try:
                fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            fcntl.flock(other, fcntl.LOCK_UN)
            return True

    def test_both_locks_are_held_inside_and_free_after_and_the_folder_is_made(
        self,
    ) -> None:
        lock = threading.Lock()
        with lem_files.held(lock, self.file):
            self.assertTrue(lock.locked())
            self.assertFalse(self.free())
        self.assertFalse(lock.locked())
        self.assertTrue(self.free())

    def test_an_error_inside_frees_both(self) -> None:
        lock = threading.Lock()
        with self.assertRaises(KeyError), lem_files.held(lock, self.file):
            raise KeyError("x")
        self.assertFalse(lock.locked())
        self.assertTrue(self.free())


if __name__ == "__main__":
    unittest.main()
