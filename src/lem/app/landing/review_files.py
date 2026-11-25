"""The review agent's record as `--record` names it: the file, found from the working directory
or in the task's folder (`land.task_file` on `main`), and its JSON, decoded in the form
`prompts/review.md` gives, or refused with the key that is wrong."""

from pathlib import Path

import msgspec

from lem.kernel.errors import Refusal
from lem.model.landing import review_said

FORM = (
    "write the record as prompts/review.md, step 8, says: attempt, tip, kind, answered, and of "
    "ran, left_out, silent, bar, must_fix, should, nit, outside, careful and careful_why what "
    "applies"
)
WHERE = "--record names a file by its path, or by its path inside the task's folder"


def task_file(given: str, directory: Path) -> Path:
    """The file `--record` names: from the working directory (or absolute), else a relative
    path in the task's folder `directory`. Refused with each place it looked."""
    path = Path(given)
    first = path if path.is_absolute() else Path.cwd() / path
    if first.is_file():
        return first
    if path.is_absolute():
        raise Refusal("record-file", f"{given} is not a file", WHERE)
    second = directory / path
    if second.is_file():
        return second
    looked = f"the working directory ({first}) nor in the task's folder ({second})"
    raise Refusal("record-file", f"{given} is a file neither in {looked}", WHERE)


def said(path: Path) -> review_said.Said:
    """The review agent's record; a file that is not its JSON is refused with the key that is
    wrong."""
    try:
        return msgspec.json.decode(path.read_bytes(), type=review_said.Said)
    except (OSError, msgspec.DecodeError) as error:
        raise Refusal(
            "review-file", f"{path} is not the review's record: {error}", FORM
        ) from error
