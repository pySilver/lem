"""How many days the state folder keeps what Lem no longer needs, and the file that says it:
`state.keep_days` of the developer's own file over the team's, else Lem's default; or the
`--days N` of a dry run."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.settings.load import settings_of
from lem.settings.places import DEFAULT

if TYPE_CHECKING:
    from pathlib import Path

KEY = "state.keep_days"


def kept(checkout: Path, days: int | None, *, dry: bool) -> tuple[int, str]:
    """The days and where the number came from; `--days` goes with a dry run only."""
    if days is None:
        loaded = settings_of(checkout)
        return loaded.settings.state.keep_days, loaded.sources.get(KEY, DEFAULT)
    if not dry:
        raise Refusal(
            "days",
            f"--days goes with --dry-run only: a removal keeps what {KEY} says",
            f"lem settings set {KEY} N --local sets the number for this machine alone",
        )
    if days < 0:
        raise Refusal("days", f"--days {days} is no number of days", "give 0 or more")
    return days, f"--days {days}"
