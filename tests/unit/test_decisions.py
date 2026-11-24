"""decisions.py's checks of a decision's story and chart, and of the circuit breaker,
each called in this process: which log needs its story, what a chart file may hold, the
breaker's two causes and the parts its document must have. The breaker's journey, from
its stop to a resumed task, is in tests/lem-decisions.sh."""

import argparse
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import cast

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import decisions

CASE = {
    "case": "1. Order 1042 has two notes.\n2. The export keeps one.",
    "case_was": "derived",
    "cause": "An order has one cell for its note.",
}
CHART = (
    'flowchart TD\n  A["An order with two notes"] --> B{"One cell?"}\n'
    '  B -->|"yes"| C["One note is lost"]'
)


class Record:
    """A task's record that keeps the lines `log` writes, without the commands that find
    a task."""

    repo = Path()
    # what a case sets, as `decisions.Task` has them
    status: str
    slug: str

    def __init__(self) -> None:
        self.written: list[dict] = []

    def add(self, make: Callable[[list[dict]], list[dict]]) -> list[dict]:
        self.written += make(self.written)
        return self.written[-1:]


def logged(**given: object) -> dict:
    args = {
        "what": "Two notes on one order",
        "chose": "both",
        "why": "nobody loses one",
        "by": "lead",
        "said": None,
        "undo": None,
        "option": None,
        "vote": None,
        "level": None,
        "unsettled": False,
        "case": None,
        "case_was": None,
        "cause": None,
        "chart": None,
        "breaker": None,
        "words": None,
        **given,
    }
    return decisions.cmd_log(
        cast("decisions.Task", Record()), argparse.Namespace(**args)
    )


class TheStory(unittest.TestCase):
    """An important log carries its story as a card does; a plain one of the
    lead may."""

    def test_an_important_log_without_its_story_is_refused(self) -> None:
        for given in (
            {"by": "dialectic"},
            {"by": "lead", "unsettled": True},
            {"by": "dialectic", "case": CASE["case"]},
        ):
            with (
                self.subTest(given=given),
                self.assertRaisesRegex(
                    decisions.DecisionError,
                    (
                        "is important, and carries its story .* this one has no "
                        "--case-was, no --cause|this one has no --case"
                    ),
                ),
            ):
                logged(**given)

    def test_an_important_log_keeps_its_story(self) -> None:
        line = logged(by="dialectic", **CASE)
        self.assertEqual(
            (line["case"], line["case_was"], line["cause"]),
            (CASE["case"], "derived", CASE["cause"]),
        )

    def test_a_plain_log_needs_none_and_takes_all_three_or_none(self) -> None:
        self.assertNotIn("case", logged())
        with self.assertRaisesRegex(
            decisions.DecisionError, "a story: .*this one has no --cause"
        ):
            logged(case=CASE["case"], case_was="derived")


class TheChart(unittest.TestCase):
    """A chart comes from a file, with or without its fence, and keeps its
    line breaks."""

    def file(self, text: str) -> str:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "chart.mmd"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_a_chart_keeps_its_lines_without_its_fence(self) -> None:
        self.assertEqual(
            decisions.chart(self.file(f"```mermaid\n{CHART}\n```\n")), CHART
        )
        self.assertEqual(logged(chart=self.file(CHART + "\n"))["chart"], CHART)

    def test_an_unquoted_text_of_a_flowchart_is_refused(self) -> None:
        for bare in (
            "A[An order] --> B",
            'A["x"] -->|yes| B["y"]',
            'A["x"] -- yes --> B["y"]',
        ):
            with (
                self.subTest(bare=bare),
                self.assertRaisesRegex(
                    decisions.DecisionError, "a text out of double quotes"
                ),
            ):
                decisions.chart(self.file(f"flowchart TD\n  {bare}\n"))

    def test_an_empty_a_long_and_an_unknown_chart_are_refused(self) -> None:
        for text, said in (
            ("```mermaid\n```\n", "holds no chart"),
            ("flowchart TD\n" + "  A --> B\n" * 600, "a record keeps 4000"),
            ("a list\n", "no chart type"),
        ):
            with (
                self.subTest(said=said),
                self.assertRaisesRegex(decisions.DecisionError, said),
            ):
                decisions.chart(self.file(text))

    def test_a_sequence_diagram_takes_no_quotes(self) -> None:
        self.assertTrue(
            decisions.chart(
                self.file("sequenceDiagram\n  The owner->>Lem: a question\n")
            ).startswith("sequenceDiagram")
        )


class TheBreaker(unittest.TestCase):
    """The breaker has two causes and no others, and its document has every part of
    the template."""

    TEMPLATE = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "lem"
        / "templates"
        / "breaker.md"
    )

    def test_two_causes_and_the_kind_of_an_irreversible_step(self) -> None:
        stub = argparse.Namespace(document=None)
        task = Record()
        task.status, task.slug = "building", "gift-note"
        with self.assertRaisesRegex(
            decisions.DecisionError, "--cause irreversible names its kind"
        ):
            decisions.cmd_breaker(
                cast("decisions.Task", task),
                argparse.Namespace(
                    **vars(stub), cause="irreversible", irreversible=None
                ),
            )
        with self.assertRaisesRegex(
            decisions.DecisionError, "--irreversible goes with --cause irreversible"
        ):
            decisions.cmd_breaker(
                cast("decisions.Task", task),
                argparse.Namespace(**vars(stub), cause="criteria", irreversible="data"),
            )
        task.status = "landing"
        with self.assertRaisesRegex(
            decisions.DecisionError, "no breaker stops a landing"
        ):
            decisions.cmd_breaker(
                cast("decisions.Task", task),
                argparse.Namespace(**vars(stub), cause="criteria", irreversible=None),
            )
        # an overrun is no cause: the parser takes the two causes only
        self.assertEqual(set(decisions.CAUSES), {"irreversible", "criteria"})

    def test_the_template_has_every_part(self) -> None:
        self.assertTrue(
            decisions.breaker_document(self.TEMPLATE).startswith(
                "WHAT STOPPED THE BUILD"
            )
        )

    def test_a_document_without_a_part_names_each_it_lacks(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        bare = Path(folder.name) / "breaker.md"
        text = self.TEMPLATE.read_text(encoding="utf-8")
        # a bare question: the title and the options, and no story, cause, chart
        # or assumptions
        bare.write_text(
            text.split("## Today and after")[0]
            + "## The options"
            + text.split("## The options")[1].split("## The recommendation")[0],
            encoding="utf-8",
        )
        with self.assertRaises(decisions.DecisionError) as caught:
            decisions.breaker_document(bare)
        said = str(caught.exception)
        for part in (
            "## Today and after",
            "## The case",
            "## The root cause",
            "## The recommendation",
            "## The assumptions",
        ):
            self.assertIn(part, said)
        self.assertNotIn("## The options (", said)
        # a case with no chart is no case
        bare.write_text(text.replace("```mermaid", "```text"), encoding="utf-8")
        with self.assertRaisesRegex(
            decisions.DecisionError,
            r"## The case \(the case that broke, in numbered steps, with its chart",
        ):
            decisions.breaker_document(bare)

    def test_a_part_s_heading_inside_a_code_fence_is_a_line_of_its_part(
        self,
    ) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        fenced = Path(folder.name) / "breaker.md"
        text = self.TEMPLATE.read_text(encoding="utf-8")
        # the real assumptions are gone, and the root cause shows a sample of a
        # document that has them
        sample = "```markdown\n# A sample\n\n## The assumptions\n\n- one\n```\n"
        fenced.write_text(
            sample
            + text.split("## The assumptions")[0].replace(
                "## The options", f"{sample}\n## The options"
            ),
            encoding="utf-8",
        )
        with self.assertRaises(decisions.DecisionError) as caught:
            decisions.breaker_document(fenced)
        self.assertIn("## The assumptions", str(caught.exception))
        # the title is the first heading outside a fence
        fenced.write_text(sample + text, encoding="utf-8")
        self.assertTrue(
            decisions.breaker_document(fenced).startswith("WHAT STOPPED THE BUILD")
        )

    def test_his_help_on_a_breaker_is_the_owners(self) -> None:
        with self.assertRaisesRegex(
            decisions.DecisionError, "--breaker and --words are the owner's"
        ):
            logged(breaker=1)


class TheRecord(unittest.TestCase):
    """A task's `decisions.jsonl`, read back with words that hold the characters
    str.splitlines breaks at."""

    def test_a_decision_whose_words_hold_a_line_separator(self) -> None:
        import json

        words = "a\N{LINE SEPARATOR}b\N{PARAGRAPH SEPARATOR}c\x85d"
        with tempfile.TemporaryDirectory() as folder:
            task = object.__new__(decisions.Task)
            task.file = Path(folder) / "decisions.jsonl"
            task.file.write_text(
                json.dumps({"kind": "taken", "id": 1, "why": words}, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(task.lines(), [{"kind": "taken", "id": 1, "why": words}])


if __name__ == "__main__":
    unittest.main()
