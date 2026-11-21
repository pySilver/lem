"""criteria.py's reading of a plan's criteria, each called in this process: a criterion's case and its
chart, the plan's `## How it works`, and which of them the digests mark."""

import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
criteria = importlib.import_module("criteria")

PLAN = """## Acceptance criteria

Size: full, because a refund has two outcomes.

1. A refund lowers the invoice's total, and never below 0:
   1. Invoice 1042 is 100 EUR.
   2. A refund of 130 EUR comes in.
   3. The invoice shows 0, and a credit
      note holds the other 30 EUR.
    ```mermaid
    flowchart TD
      A["A refund comes in"] --> B{"Larger than the total?"}
        B -->|"yes"| C["The total shows 0"]
    ```
   - test: `sh tests/refund.sh` in `tests/refund.sh`
2. The invoice keeps its number.

## How it works

The refund, from its arrival to the invoice:

```mermaid
flowchart LR
  A["A refund"] --> B["The invoice"]
```

## Tasks

1. The refund.
"""


class CaseAndChart(unittest.TestCase):
    """A criterion's steps stay lines of their own and its chart is its own, at any indent."""

    def test_the_steps_and_a_chart_at_four_spaces(self) -> None:
        first, second = criteria.parse(PLAN, "plan.md")["criteria"]
        self.assertEqual(first["text"], "A refund lowers the invoice's total, and never below 0:")
        self.assertEqual(first["case"], ["1. Invoice 1042 is 100 EUR.", "2. A refund of 130 EUR comes in.", "3. The invoice shows 0, and a credit note holds the other 30 EUR."])
        self.assertEqual(first["chart"], 'flowchart TD\n  A["A refund comes in"] --> B{"Larger than the total?"}\n    B -->|"yes"| C["The total shows 0"]')
        self.assertNotIn("mermaid", first["text"])
        self.assertEqual([test["command"] for test in first["tests"]], ["sh tests/refund.sh"])
        self.assertEqual((second["case"], second["chart"]), ([], None))

    def test_how_it_works_is_read_and_is_no_criterion(self) -> None:
        read = criteria.parse(PLAN, "plan.md")
        self.assertEqual(len(read["criteria"]), 2)
        self.assertTrue(read["how"].startswith("The refund, from its arrival to the invoice:\n\n```mermaid\nflowchart LR"))

    def test_a_second_chart_under_one_criterion_is_refused(self) -> None:
        twice = PLAN.replace("   - test:", "   ```mermaid\n   flowchart TD\n     A[\"x\"]\n   ```\n   - test:")
        with self.assertRaisesRegex(criteria.CriteriaError, "plan.md:15: criterion 1 has a chart already"):
            criteria.parse(twice, "plan.md")


class Digests(unittest.TestCase):
    """The case is a part of what the owner approved, and the chart is not: a change of a step changes
    the criterion and both digests, a change of the chart changes neither."""

    @staticmethod
    def marks(plan: str) -> tuple[str, str, list[str]]:
        read = criteria.parse(plan, "plan.md")
        wholes = [criteria.whole(criterion) for criterion in read["criteria"]]
        return read["digest"], criteria.text_digest(read["size"], wholes), wholes

    def test_a_step_changes_the_criterion(self) -> None:
        digest, text, wholes = self.marks(PLAN)
        moved, moved_text, moved_wholes = self.marks(PLAN.replace("130 EUR", "150 EUR"))
        self.assertNotEqual(digest, moved)
        self.assertNotEqual(text, moved_text)
        self.assertNotEqual(wholes[0].split(), moved_wholes[0].split())

    def test_a_chart_changes_nothing_that_is_marked(self) -> None:
        drawn = PLAN.replace('C["The total shows 0"]', 'C["The total reads 0"]').replace('B["The invoice"]', 'B["An invoice"]')
        self.assertEqual(self.marks(PLAN), self.marks(drawn))

    def test_steps_read_as_the_text_they_were(self) -> None:
        """A case written before the steps were lines of their own read as one text: the same digest."""
        _, text, _ = self.marks(PLAN)
        read = criteria.parse(PLAN, "plan.md")
        joined = [" ".join(criteria.whole(criterion).split()) for criterion in read["criteria"]]
        self.assertEqual(text, criteria.text_digest("full", joined))


if __name__ == "__main__":
    unittest.main()
