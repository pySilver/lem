"""Where Lem's files are (lem.paths): the data folder of an installed app, else the
checkout the package is part of, else one error that names both places. Each case runs
a copy of paths.py in a folder of its own, laid out as one of the three.

    .venv/bin/python -B -m unittest discover -s tests/unit -p test_paths.py
"""

import runpy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[2] / "src" / "lem" / "paths.py"


class Root(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="lem-paths-")).resolve()
        self.addCleanup(shutil.rmtree, self.home)

    def package(self, place: str) -> Path:
        """A copy of paths.py in the package folder PLACE under the case's home."""
        package = self.home / place
        package.mkdir(parents=True)
        shutil.copy(SOURCE, package / "paths.py")
        return package

    def test_an_installed_app_reads_its_own_data_folder(self) -> None:
        package = self.package("lib/python3.14/site-packages/lem")
        (package / "data" / "skills" / "lem").mkdir(parents=True)
        found = runpy.run_path(str(package / "paths.py"))
        self.assertEqual(found["ROOT"], package / "data")
        self.assertEqual(found["SKILL"], package / "data" / "skills" / "lem")

    def test_a_checkout_is_its_own_root_when_it_holds_the_skill(self) -> None:
        package = self.package("lem/src/lem")
        (self.home / "lem" / "skills" / "lem").mkdir(parents=True)
        (self.home / "lem" / "skills" / "lem" / "SKILL.md").write_text("# Lem\n")
        found = runpy.run_path(str(package / "paths.py"))
        self.assertEqual(found["ROOT"], self.home / "lem")
        self.assertEqual(found["CAST"], self.home / "lem/skills/lem-panel/cast")

    def test_neither_is_one_error_that_names_both_places(self) -> None:
        package = self.package("copy/src/lem")
        with self.assertRaises(SystemExit) as stopped:
            runpy.run_path(str(package / "paths.py"))
        said = str(stopped.exception.code)
        self.assertIn(str(package / "data"), said)
        self.assertIn(f"nor in {self.home / 'copy'},", said)
        self.assertTrue(said.endswith("the owner installs Lem again"), said)


if __name__ == "__main__":
    unittest.main()
