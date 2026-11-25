"""What a command of the tree answers until the step of the rebuild that builds it."""

from lem.kernel.errors import Refusal

NOT_BUILT = "not-built"
DESIGN = "docs/plans/2026-11-25-lem-built-again.md"


def not_built(command: str, step: str) -> Refusal:
    """The refusal of `lem COMMAND`, which names the step that builds it."""
    return Refusal(
        NOT_BUILT,
        f"`lem {command}` is not built yet: Lem is built again, one step at a time",
        f"the step `{step}` builds it ({DESIGN}, part 9)",
    )
