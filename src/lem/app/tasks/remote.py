"""Fetch the task's origin, and give the reason when the task goes on without it."""

from typing import TYPE_CHECKING

from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git


def fetch_warning(git: Git, checkout: Path) -> str | None:
    """Skip the fetch when the checkout names no origin."""
    if git.origin_url(checkout) is None:
        return (
            "This repository has no Git remote named origin. "
            "The owner can add it with git remote add origin URL."
        )
    try:
        git.fetch(checkout)
    except Unanswered as error:
        said = error.said
        return f"origin did not answer ({said})."
    return None
