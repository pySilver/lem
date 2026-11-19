"""land.py's rules that take facts and return a result, each called in this process.

What only git can show stays in the blocks of tests/, which run the real commands in throwaway
repositories; here a rule gets the text git gave and is asked for its result.
"""

import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
land = importlib.import_module("land")

# One defect outside the change, as a review's record names it.
DEFECT = {"where": "src/json.py:parse", "title": "Empty input crashes the parser", "what": "parse with an empty string raises IndexError, on the base commit too."}


class DefectsOutside(unittest.TestCase):
    """`land.defects_of`: the defects a review's record names outside the change."""

    def refusal(self, value: object) -> str:
        with self.assertRaises(land.LandError) as raised:
            land.defects_of(value)
        return str(raised.exception)

    def test_a_count_is_refused(self) -> None:
        said = self.refusal(2)
        self.assertIn("`outside` is the list", said)
        self.assertIn('"where"', said)

    def test_a_defect_with_only_its_place_is_refused(self) -> None:
        said = self.refusal([{"where": "app.txt"}])
        self.assertIn("`outside` is the list", said)
        self.assertIn('"title"', said)

    def test_zero_is_no_defect_and_nothing_to_file(self) -> None:
        self.assertEqual(land.defects_of(0), [])
        self.assertEqual(land.to_file([{"round": 1, "answered": True, "outside": land.defects_of(0)}]), [])

    def test_a_named_defect_is_kept_and_waits_to_be_filed(self) -> None:
        padded = {key: f" {text} " for key, text in DEFECT.items()}
        self.assertEqual(land.defects_of([padded]), [DEFECT])
        self.assertEqual(land.to_file([{"round": 2, "answered": True, "outside": [DEFECT]}]), [{"round": 2, **DEFECT}])


if __name__ == "__main__":
    unittest.main()
