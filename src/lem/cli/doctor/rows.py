"""Every row of `lem doctor`, in the order the owner reads them: the tools, the agents and their
skills, this machine's settings and board, the repository's rows, and Lem's own halves.

A part that is refused (a file of Lem's home folder that does not read, a home folder named by a
relative path) becomes its row, with the refusal's why and fix, and every other row still comes.
"""

from typing import TYPE_CHECKING

from lem.cli.doctor.machine_parts import MACHINE_PARTS
from lem.cli.doctor.row import Row
from lem.cli.doctor.tool_parts import TOOL_PARTS
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look
    from lem.cli.doctor.row import Part

REFUSED = "the check of this row, which could not read what it needs"


def guarded(part: Part, look: Look) -> tuple[Row, ...]:
    """The rows of one part; a refusal is its one row, with its why and its fix."""
    name, need, rows_of = part
    try:
        found = rows_of(look)
    except Refusal as refused:
        row = Row(
            name=name,
            need=need,
            found=False,
            detail=refused.why,
            used_for=REFUSED,
            without_it=refused.fix,
        )
        return (row,)
    return found if isinstance(found, tuple) else (found,)


def gathered(look: Look) -> tuple[Row, ...]:
    """Every row, each part guarded."""
    parts = (*TOOL_PARTS, *MACHINE_PARTS)
    return tuple(row for part in parts for row in guarded(part, look))
