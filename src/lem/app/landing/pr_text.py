"""The pull request's text in its plainest form: green or the reasons it is not, the criteria,
the checks, the review, what was seen outside the change, and the notes the agent wrote.

The text is a function of the record and the notes alone, so a proposal cut off and made again
writes the same bytes. The template, the decisions, the plan talk's counts and the persona read
are the step `land-propose`'s.
"""

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing.review import newest
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.criterion import Criterion
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

GREEN = (
    "**Green.** The checks passed, the review left no must-fix, and the criteria are "
    "the approved ones."
)
LEVELS = ("must-fix", "should", "nit")
CHECK = "- `{0.command}`: {0.last}"
SEEN = "- {0.finding}: {0.line}"
SHORT = 12


def criterion_lines(criterion: Criterion) -> list[str]:
    """A criterion, then its tests or why it has none."""
    lines = ["", f"{criterion.number}. {criterion.text}"]
    for test in criterion.tests:
        named = ", ".join(f"`{path}`" for path in test.files)
        command = test.command
        lines.append(f"   - test: `{command}` in {named}")
    if criterion.no_test:
        lines.append(f"   - no test: {criterion.no_test}")
    return lines


def tally(levels: tuple[str, ...], level: str) -> str:
    """How many findings of `level` there are, with the level."""
    number = levels.count(level)
    return f"{number} {level}"


def counted(review: Reviewed) -> str:
    """The review's line: its attempt, its kind, who answered, and its counts by level."""
    levels = tuple[str, ...](finding.level for finding in review.findings)
    counts = ", ".join(map(partial(tally, levels), LEVELS))
    answered = ", ".join(review.answered) or "nobody"
    kind = f"{review.kind}; answered: {answered}"
    return f"- attempt {review.attempt} ({kind}): {counts}"


def landing_lines(landing: Landing) -> list[str]:
    """The sections of the checks, the review, and what was seen outside the change."""
    checked = landing.checked
    lines = ["", "## Checks", ""]
    lines.extend(map(CHECK.format, checked.outcomes if checked else ()))
    last = newest(landing)
    lines.extend(("", "## Review", "", counted(last) if last else "- none"))
    if landing.filed:
        lines.extend(("", "## Seen outside the change", ""))
    lines.extend(map(SEEN.format, landing.filed))
    return lines


def notes_of(path: str) -> str:
    """The notes the agent wrote for the pull request, from their file."""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError as error:
        raise Refusal(
            "notes",
            f"the notes {path} cannot be read ({error.strerror})",
            "write the pull request's notes into that file, then propose again",
        ) from error


def body(record: Record, reasons: tuple[str, ...], notes: str) -> str:
    """The whole text of the pull request, with the notes of the file `notes`."""
    said = "; ".join(reasons)
    lines = [
        f"**Not green.** {said}." if reasons else GREEN,
        "",
        "## Acceptance criteria",
    ]
    for criterion in record.task.criteria.criteria:
        lines.extend(criterion_lines(criterion))
    lines.extend(landing_lines(record.landing or Landing()))
    lines.extend(("", "## Notes", "", notes_of(notes) or "none", ""))
    return "\n".join(lines)


def published(folder: Path, text: str) -> str:
    """Publish the text in the task's folder `folder`, at a path named by its digest, and
    give that path."""
    encoded = text.encode()
    short = files.digest(encoded)[:SHORT]
    named = f"pr-{short}.md"
    files.publish(folder / named, encoded)
    return named
