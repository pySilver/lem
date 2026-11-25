"""The form of `handoff.md`: its own line, its five parts, and what a refusal names."""

from datetime import UTC, datetime

import pytest

from lem.app.sessions import handoff
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


def test_a_handoff_in_its_form_says_its_phase_and_time() -> None:
    assert handoff.form(WHOLE, "gift-note") == handoff.Form(
        phase="build", written=datetime(2026, 11, 25, 10, 7, tzinfo=UTC)
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
        (WHOLE.replace("Land it.", "```\n## Not a heading\n```"), "## Next step"),
        ("", "a first line"),
    ],
)
def test_what_a_handoff_lacks_is_named(text: str, lacks: str) -> None:
    with pytest.raises(Refusal) as refused:
        handoff.form(text, "gift-note")
    assert refused.value.code == "handoff-form"
    assert lacks in refused.value.why
