"""The form of `handoff.md`: its own line, its five parts, and what a refusal names."""

from datetime import UTC, datetime

import pytest

from lem.app.sessions import handoff
from lem.app.sessions.handoff_parts import Changed
from lem.kernel.errors import Refusal

WHOLE = """task: gift-note · from build · written: 2026-11-25T10:07Z

## Settled

- the plan, docs/plans/x.md

## Open

none

## Next step

Land it.

## Failed

none

## Changed files

- `src/export.py`: committed in abc1234
"""


def test_a_handoff_in_its_form_says_its_phase_time_and_changed_files() -> None:
    assert handoff.form(WHOLE, "gift-note") == handoff.Form(
        task="gift-note",
        phase="build",
        written=datetime(2026, 11, 25, 10, 7, tzinfo=UTC),
        changed=(Changed(path="src/export.py", status="committed in abc1234"),),
    )
    commented = f"<!-- lem: old form -->\n{WHOLE}".replace(
        "## Open\n", "## Open\n<!-- what is open -->\n"
    )
    assert handoff.form(commented, "gift-note").phase == "build"


@pytest.mark.parametrize(
    ("text", "lacks"),
    [
        (WHOLE.replace("## Next step\n\nLand it.", "## Next step\n"), "## Next step"),
        (WHOLE.replace("## Failed", "## Failures"), "## Failed"),
        (WHOLE.replace("gift-note", "other-task"), "a first line"),
        (WHOLE.replace("from build", "from lunch"), "a first line"),
        (WHOLE.replace("## Failed", "```\n## Failed\n```"), "## Failed"),
        (WHOLE.replace("10:07Z", "10:07Z").replace("11-25", "02-31"), "a first line"),
        ("", "a first line"),
    ],
)
def test_what_a_handoff_lacks_is_named(text: str, lacks: str) -> None:
    with pytest.raises(Refusal) as refused:
        handoff.form(text, "gift-note")
    assert refused.value.code == "handoff-form"
    assert lacks in refused.value.why


def test_a_code_block_is_words_of_its_part_and_never_a_heading() -> None:
    fenced = WHOLE.replace("Land it.", "```\n## Not a heading\n```")
    assert handoff.form(fenced, "gift-note").phase == "build"
    longer = WHOLE.replace("Land it.", "````\n```\n## Not a heading\n```\n````")
    assert handoff.form(longer, "gift-note").phase == "build"


def test_a_code_block_that_never_closes_is_refused() -> None:
    with pytest.raises(Refusal) as refused:
        handoff.form(WHOLE.replace("Land it.", "```\nLand it."), "gift-note")
    assert refused.value.code == "handoff-form"
    assert "never closes" in refused.value.why


@pytest.mark.parametrize(
    ("changed", "found"),
    [
        ("none", ()),
        ("- none.", ()),
        (
            "- src/a.py: new\n* `b c.py`: changed",
            (("src/a.py", "new"), ("b c.py", "changed")),
        ),
    ],
)
def test_the_changed_files_are_a_path_and_a_status_a_line_or_none(
    changed: str, found: tuple[tuple[str, str], ...]
) -> None:
    text = WHOLE.replace("- `src/export.py`: committed in abc1234", changed)
    form = handoff.form(text, "gift-note")
    assert tuple((one.path, one.status) for one in form.changed) == found


def test_a_changed_file_with_no_status_is_named_in_the_refusal() -> None:
    text = WHOLE.replace(
        "- `src/export.py`: committed in abc1234", "- src/a.py\n- b.py: new"
    )
    with pytest.raises(Refusal, match=r"these lines have none: '- src/a\.py'"):
        handoff.form(text, "gift-note")
