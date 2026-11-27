"""The repository row for the settings file that only onboarding imports."""

from typing import TYPE_CHECKING

from lem.cli.doctor.checkouts import main_checkout
from lem.cli.doctor.row import PROJECT, Row
from lem.settings.places import LEGACY_TEAM, TEAM

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

NAME = "settings of Lem 0.3"


def settings_rows(look: Look) -> tuple[Row, ...]:
    """Name the old file in the checkout that `lem init` writes, without opening it."""
    checkout = main_checkout(look.folder)
    if checkout is None:
        return ()
    old = checkout / LEGACY_TEAM
    if not (old.exists() or old.is_symlink()):
        return ()
    return (
        Row(
            name=NAME,
            need=PROJECT,
            found=False,
            detail=f"{old} is here. Lem does not read it as settings.",
            used_for=f"{TEAM} holds the team's settings.",
            without_it=(
                f"The owner can run `/lem init` to take its values as defaults in {TEAM}. "
                "A value already in that file stays."
            ),
        ),
    )
