"""What Lem reads beside its settings, each in one place: Lem's own files in `.lem/`, the rules
for the code where Claude Code loads them by itself, the review tool's folder, and the backlog
where the agterm cookbook's recipe keeps it (the owner's note of 2026-11-18 on the plan of the
core and two modes); and the plans folder and the rulings file, which `[paths]` names. `lem path
NAME` answers for each, and `lem settings show` says whether each is there.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.settings.team import Paths

LEM = Path(".lem")
# Each place with no setting. `cast` is the personas folder, by the name `lem cast` gives it.
FIXED = (
    ("profile", LEM / "profile.md"),
    ("personas", LEM / "personas"),
    ("cast", LEM / "personas"),
    ("lessons", LEM / "lessons.md"),
    ("worktrees", LEM / "worktrees"),
    ("state", LEM / "state"),
    ("rules", Path(".claude") / "rules"),
    ("review", Path(".revmux")),
    ("backlog", Path("docs") / "backlog"),
)


class Placed(Frozen, frozen=True, kw_only=True):
    """One place: its absolute path, and whether it is there."""

    path: str
    exists: bool


def places_of(checkout: Path, paths: Paths) -> dict[str, Placed]:
    """Every place of `checkout`, the plans folder and the rulings file as `paths` names
    them."""
    root = checkout.resolve()
    every = (*FIXED, *chosen(paths))
    return {name: placed(root / relative) for name, relative in every}


def chosen(paths: Paths) -> tuple[tuple[str, Path], ...]:
    """The plans folder and the rulings file, as `[paths]` names them."""
    plans = Path(paths.plans)
    rulings = Path(paths.rulings)
    return (("plans", plans), ("rulings", rulings))


def placed(path: Path) -> Placed:
    """One place, and whether it is there."""
    return Placed(path=str(path), exists=path.exists())
