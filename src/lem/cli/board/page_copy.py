"""A local page whose folder agterm refuses as its `--cwd`, the root or the owner's home
(`cwd must not be / or the home directory`, agterm's reference), opens from a copy in Lem's
folder of temporary pages (`cli/ask/temp_pages.py`), named by its stem and the digest of its
bytes; a page in any other folder opens where it is, with read access to the files beside it."""

from pathlib import Path

from lem.cli.ask import temp_pages
from lem.kernel import files

# The characters of the digest in the copy's name.
SHORT = 12


def openable(named: str) -> str:
    """The page to open for the file `named`: itself, or its copy when agterm refuses its
    folder; a path that is no file is given back as it is, for the board to refuse."""
    page = Path(named).resolve()
    if not page.is_file() or page.parent not in refused():
        return named
    body = page.read_bytes()
    folder = temp_pages.folder()
    folder.mkdir(mode=temp_pages.PRIVATE_MODE, exist_ok=True)
    short = files.digest(body)[:SHORT]
    copy = folder / f"{page.stem}-{short}{page.suffix}"
    files.publish(copy, body)
    return str(copy)


def refused() -> tuple[Path, Path]:
    """The folders agterm refuses as a page's `--cwd`: the root and the owner's home."""
    return Path("/"), Path.home().resolve()
