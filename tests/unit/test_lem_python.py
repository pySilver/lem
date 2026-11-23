"""lem_python.find(), the search for a Python of 3.11 or newer that `bin/lem` and the
plugin's hooks make when the first `python3` is older, over stand-in folders of a PATH.
A stand-in `python3` says its version as Python would; a `python3.N` is known by its
name and never started.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
lem_python = importlib.import_module("lem_python")


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


if __name__ == "__main__":
    unittest.main()
