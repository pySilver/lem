"""The words of `lem land alike`, checked (`land.flag_line` and `land.cmd_alike` on `main`): the
finding's place and title, each one line, the title with a word for a file name, and the file
of its run, which reads and is not empty."""

from pathlib import Path

from lem.kernel.errors import Refusal
from lem.model.landing.item_names import slug_of
from lem.model.landing.items import Defect
from lem.records.base import Frozen

FIX = "lem land alike SLUG --where PLACE --title TITLE --what FILE, as prompts/small.md says"


class Finding(Frozen, frozen=True, kw_only=True):
    """The finding as `alike` names it back: its place and its title."""

    where: str
    title: str


def line_of(flag: str, text: str) -> str:
    """The text of a word that is one line, stripped; else refused."""
    kept = text.strip()
    if not kept or "\n" in kept:
        raise Refusal("line", f"{flag} is one line of text, and it is {text!r}", FIX)
    return kept


def run_of(what: str) -> str:
    """The run of the file `--what` names: what happens, with the input."""
    try:
        found = Path(what).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as error:
        why = f"--what names the file of the finding's run, and {what} does not read ({error})"
        raise Refusal("what", why, FIX) from error
    if not found:
        why = f"--what names the file of the finding's run, and {what} is empty"
        raise Refusal("what", why, FIX)
    return found


def defect_of(where: str, title: str, what: str) -> Defect:
    """The finding the words name, as a defect."""
    place, named = line_of("--where", where), line_of("--title", title)
    if not slug_of(named):
        why = f"--title is the finding's title, and {title!r} has no word for an item's file name"
        raise Refusal("title", why, FIX)
    return Defect(where=place, title=named, what=run_of(what))
