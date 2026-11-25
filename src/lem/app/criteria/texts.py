"""A file of criteria, read once: its bytes, which a page's mark is of, and its text, with the
line ends a read in text mode gives from the same bytes."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria.read import Sheet, sheet_of

if TYPE_CHECKING:
    from pathlib import Path

FORM = "the criteria's form: lem criteria show --help"


def bytes_of(path: Path, what: str) -> bytes:
    """The bytes of `path`; refused when it is no file."""
    try:
        return path.read_bytes()
    except FileNotFoundError, IsADirectoryError:
        raise Refusal(
            "no-file", f"{path} is not a file", f"--file names {what}, in {FORM}"
        ) from None


def text_of(raw: bytes, path: Path) -> str:
    """The text of `raw`, the bytes of `path`; bytes that are no UTF-8 text are refused."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Refusal(
            "not-text",
            f"{path} is not UTF-8 text (byte {error.start} does not read)",
            "write it in UTF-8",
        ) from None
    return text.replace("\r\n", "\n").replace("\r", "\n")


def sheet_at(path: Path, what: str) -> Sheet:
    """The criteria of the file `path`."""
    text = text_of(bytes_of(path, what), path)
    return sheet_of(text, path.name)
