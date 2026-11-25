"""Which file `lem settings set` may write a table into: a table valid in the file of the call's
switch, and never the team's file, which is everybody's, edited by hand and committed."""

from lem.kernel.errors import Refusal
from lem.settings import places

# What a table only the team's file holds takes: the edit of that file by hand.
HAND = f"edit {places.TEAM} by hand and commit it: no command writes the team's file"


def writable(table: str, scope: places.Scope, named: str) -> None:
    """Refuse a table the file of `scope` may not hold; the team's file is edited by hand."""
    valid = places.valid(table)
    if scope in valid:
        return
    raise Refusal(
        "table-place", f"{named} may not hold [{table}]", where_written(valid)
    )


def where_written(valid: places.Scopes) -> str:
    """The flags that write a table valid in `valid`, or the edit by hand of the team's file."""
    flags = [f"--{one}" for one in valid if one != places.Scope.team]
    listed = " or ".join(flags)
    return f"write it with {listed}" if flags else HAND
