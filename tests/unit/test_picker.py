"""The task picker (picker.py), as calls of the functions that hold its rules: the state of a task in
the board's words. What agterm does with the picker is in tests/lem-picker.sh, with a stand-in for
agtermctl.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"
sys.path.insert(0, str(SCRIPTS))
picker = importlib.import_module("picker")


class StateWords(unittest.TestCase):
    def test_an_investigation_line_counts_on_any_line_of_the_newest_block(self):
        second = {"status": "building", "state": "2026-11-21T10:00Z building: an investigator reproduces the bug\ninvestigation: bug"}
        first = {"status": "building", "state": "2026-11-21T10:00Z building: investigation: question\ntype: question, because a report"}
        self.assertEqual(picker.state_words(second, None), picker.INVESTIGATING)
        self.assertEqual(picker.state_words(first, None), picker.INVESTIGATING)

    def test_a_lead_that_builds_is_no_investigation(self):
        task = {"status": "building", "state": "2026-11-21T10:00Z building: lead: builder\ntask 1 of 3"}
        self.assertEqual(picker.state_words(task, None), picker.WORDS["building"])
        self.assertEqual(picker.state_words({"status": "building", "state": None}, None), picker.WORDS["building"])


if __name__ == "__main__":
    unittest.main()
