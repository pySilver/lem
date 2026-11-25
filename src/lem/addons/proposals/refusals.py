"""The refusals the proposals share: a record that does not read, and a run or verdicts given
in another form."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

FORM = (
    "a JSON object with `date`, `kind` (night or retro), `runs` (each with `at`, `read` and "
    "the `proposals` it added), `proposals` (each with `number` from 1, `area`, `move`, "
    "`body`, `source` and `where`), `refuted` (`number`, `reason`, `day`), `passed` "
    "(`number`, `area`, `item`, `day`) and `dropped` (`number`, `text`, `said`, `day`, "
    "`item`)"
)


def unreadable(path: Path, why: str) -> Refusal:
    """The refusal of a record that does not read, with its form."""
    return Refusal(
        "proposals-record",
        f"{path}: {why}",
        f"correct the file by hand into the form of a record, {FORM}; only lem proposals "
        "writes one",
    )
