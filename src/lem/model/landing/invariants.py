"""The invariants checked before an effect (`landing.md` H). The plain path holds number 4:
nothing is pushed to, merged into or deleted from a protected branch. The rest are the step
`land-merge`'s, with their place in every rule that acts."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.landing.world import Rules


def protected(branch: str, rules: Rules, does: str) -> Refusal | None:
    """Why Lem may not act (`does`: pushes, merges, deletes) on `branch`: the base outside a
    merge through its pull request, or a protected branch. None for a task's own branch."""
    if branch == rules.base and does != "merges":
        why = (
            f"{branch} is the base branch: Lem {does} nothing outside its pull request"
        )
    elif branch in rules.protected:
        why = (
            f"{branch} is in branch.protected of .lem/settings.toml: Lem {does} nothing"
        )
    else:
        return None
    return Refusal(
        "protected",
        why,
        "only the owner's edit of .lem/settings.toml lifts it; no brief or plan does",
    )
