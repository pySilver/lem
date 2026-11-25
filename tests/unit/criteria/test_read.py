"""The criteria section, read: its Size line, its numbered criteria, the steps of a case, a
chart, the tests, How it works, and each line that is not of the form, refused with its place."""

import pytest

from lem.kernel.errors import Refusal
from lem.model.criteria import digest
from lem.model.criteria.read import sheet_of

CASE = """# Refunds

## Acceptance criteria

Size: full, because a refund changes the invoice and the credit notes.

1. A refund lowers the invoice's total, and never below 0:
    1. Invoice 1042 is 100 EUR.
    2. A refund of 130 EUR comes in.
    3. The invoice shows 0, and a credit note holds the other 30 EUR.
    ```mermaid
    flowchart TD
      A["A refund comes in"] --> B{"Larger than the total?"}
    ```
    - test: `python3 -m unittest tests.test_refund` in `tests/test_refund.py`
2. A note goes with each refund.
   - no test: the note is a sentence of the README.

## How it works

```mermaid
flowchart LR
  A["Refund"] --> B["Invoice"]
```

## Tasks
"""


def refused(text: str) -> Refusal:
    with pytest.raises(Refusal) as caught:
        sheet_of(text, "plan.md")
    return caught.value


def test_the_steps_and_a_chart_at_four_spaces() -> None:
    sheet = sheet_of(CASE, "plan.md")
    first, second = sheet.criteria
    assert sheet.size == "full"
    assert sheet.why == "a refund changes the invoice and the credit notes."
    assert first.text == "A refund lowers the invoice's total, and never below 0:"
    assert first.case == (
        "1. Invoice 1042 is 100 EUR.",
        "2. A refund of 130 EUR comes in.",
        "3. The invoice shows 0, and a credit note holds the other 30 EUR.",
    )
    assert first.chart == (
        'flowchart TD\n  A["A refund comes in"] --> B{"Larger than the total?"}'
    )
    assert [test.files for test in first.tests] == [("tests/test_refund.py",)]
    assert second.no_test == "the note is a sentence of the README."


def test_how_it_works_is_read_and_is_no_criterion() -> None:
    sheet = sheet_of(CASE, "plan.md")
    assert len(sheet.criteria) == 2
    assert sheet.how == '```mermaid\nflowchart LR\n  A["Refund"] --> B["Invoice"]\n```'


def test_a_second_chart_under_one_criterion_is_refused() -> None:
    twice = CASE.replace(
        "    - test:",
        '    ```mermaid\n    flowchart TD\n      A["x"]\n    ```\n    - test:',
    )
    assert "has a chart already" in refused(twice).why


def test_a_heading_inside_a_code_block_is_an_example() -> None:
    shown = "```\n## Acceptance criteria\n\nSize: small, because x.\n```\n\n" + CASE
    assert len(sheet_of(shown, "plan.md").criteria) == 2


def test_each_line_of_another_form_is_refused_with_its_place() -> None:
    assert "plan.md:4" in refused("# x\n\n## Acceptance criteria\nSize: huge, x\n").why
    out_of_order = "## Acceptance criteria\n\nSize: full, because x.\n\n2. A rule.\n"
    assert "is not criterion 1" in refused(out_of_order).why
    dashed = (
        "## Acceptance criteria\nSize: full, because x.\n1. A rule.\n   - tset: y\n"
    )
    assert "is no line of a criterion" in refused(dashed).why
    after = CASE.replace("2. A note", "   more words\n2. A note")
    assert "comes before its tests" in refused(after).why
    unnamed = "## Acceptance criteria\nSize: full, because x.\n1. A rule.\n   - test: `x` in y\n"
    assert "names its command and its files" in refused(unnamed).why
    assert "has no `## Acceptance criteria`" in refused("# a plan\n").why
    assert (
        "holds no criterion"
        in refused("## Acceptance criteria\nSize: full, because x.\n").why
    )


def test_a_fast_track_has_one_criterion_and_a_criterion_one_of_test_and_none() -> None:
    two = "## Acceptance criteria\nSize: small, because x.\n1. One.\n2. Two.\n"
    assert "has one criterion" in refused(two).why
    both = CASE.replace(
        "   - no test: the note", "   - test: `t` in `t.py`\n   - no test: the note"
    )
    assert "names a test and says that it has none" in refused(both).why


def test_a_step_changes_the_criterion_and_a_chart_changes_nothing_that_is_marked() -> (
    None
):
    sheet = sheet_of(CASE, "plan.md")
    stepped = sheet_of(CASE.replace("130 EUR", "131 EUR"), "plan.md")
    uncharted = sheet_of(CASE.replace('"A refund comes in"', '"In"'), "plan.md")
    assert digest.of_texts(sheet.size, sheet.criteria) != digest.of_texts(
        stepped.size, stepped.criteria
    )
    assert digest.of_texts(sheet.size, sheet.criteria) == digest.of_texts(
        uncharted.size, uncharted.criteria
    )
    assert sheet.digest == uncharted.digest
    assert sheet.digest != stepped.digest


def test_steps_read_as_the_text_they_were_and_a_line_break_is_no_change() -> None:
    sheet = sheet_of(CASE, "plan.md")
    broken = sheet_of(
        CASE.replace("and never below 0:", "and never\n   below 0:"), "plan.md"
    )
    assert (
        digest.whole(sheet.criteria[0]).splitlines()[1] == "1. Invoice 1042 is 100 EUR."
    )
    assert digest.of_texts(sheet.size, sheet.criteria) == digest.of_texts(
        broken.size, broken.criteria
    )


def test_a_step_over_two_lines_and_a_label_between_two_runs() -> None:
    text = (
        "## Acceptance criteria\nSize: full, because x.\n1. A rule:\n   1. One\n"
        "      and its rest.\n   After:\n   2. Two.\n"
    )
    assert sheet_of(text, "plan.md").criteria[0].case == (
        "1. One and its rest.",
        "After:",
        "2. Two.",
    )
