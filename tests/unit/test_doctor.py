"""doctor.py's rules that take facts: the row for a repository whose installed Lem is other code than
the board server runs.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
doctor = importlib.import_module("doctor")


def install(project: str | None, version: str, scope: str = "project") -> dict:
    return {"key": "lem@lem", "scope": scope if project else "user", "project": project, "version": version, "folder": None}


def identity(entry: dict) -> str:
    return f"version {entry['version']}"


class Installs(unittest.TestCase):
    def test_a_repository_whose_install_is_other_code_gets_a_row_with_the_two_lines(self):
        rows = doctor.install_rows("version 0.1.2", ["/r/shop", "/r/notes", "/r/bare"], [install("/r/shop", "0.1.1"), install("/r/notes", "0.1.2")], identity)
        self.assertEqual([row["name"] for row in rows], ["installed Lem: shop"])
        self.assertEqual(rows[0]["lines"], ["cd /r/shop && claude plugin update lem@lem --scope project", "lem serve --ensure"])
        self.assertIn("/r/shop has version 0.1.1 of lem@lem installed for the project, and the board server runs version 0.1.2; the install is the older", rows[0]["detail"])
        self.assertEqual((rows[0]["need"], rows[0]["found"]), ("optional", False))

    def test_an_install_for_the_user_counts_where_the_repository_has_none_of_its_own(self):
        rows = doctor.install_rows("version 0.1.1", ["/r/shop"], [install(None, "0.1.2")], identity)
        self.assertIn("--scope user", rows[0]["line"])
        self.assertIn("the server is the older", rows[0]["detail"])
        self.assertEqual(doctor.install_rows("commit abc", ["/r/shop"], [install(None, "0.1.2")], identity)[0]["detail"].rsplit("; ", 1)[1],
                         "which is the newer is not known")


if __name__ == "__main__":
    unittest.main()
