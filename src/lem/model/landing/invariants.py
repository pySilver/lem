"""The invariants checked before an effect (`landing.md` H).

1. A push or a merge names a tip that a passed run of the checks covers, with the check
   definitions as now (`merge_evidence.covered`, by the checks' own rule).
2. A merge goes into the task's base through its open pull request, at the proposed tip, on a
   base the checks or a safe read covered, with the merger's authority or the owner's word
   (`merge_evidence.py`, `merge.authority`); the destination the forge reports is checked after
   the merge (`target`).
3. A push carries its lease and a ref is deleted at the commit named (the adapters).
4. Nothing is pushed to, merged into or deleted from a protected branch (`protected`).
5. Green is one function (`green.py`).
6. No status leaves an ended state; after the end only the cleanup writes (`ended`).
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.landing.world import Rules

# The statuses that end a task (the design's part 3).
ENDED = frozenset(("landed", "answered", "dropped"))
# The landing's steps that may still run on a task that ended (H 6).
AFTER_END = frozenset(("merged", "clean"))


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


def target(destination: str, rules: Rules, url: str) -> Refusal | None:
    """Why a pull request that went, or goes, into `destination` is not the task's: its base
    on the forge is not the base of the settings (H 2)."""
    if destination == rules.base:
        return None
    return Refusal(
        "target",
        f"the pull request {url} goes into {destination} on GitHub, not into {rules.base}, "
        "the base of the task's settings: its base was changed there",
        f"the owner sets its base back to {rules.base} on GitHub, or drops the task, or a "
        f"new task brings the change onto {rules.base}",
    )


def ended(slug: str, status: str, step: str) -> Refusal | None:
    """Why `step` may not run on the task `slug` in `status`: after the end only the
    cleanup writes, and no status leaves an ended state (H 6)."""
    if status not in ENDED or step in AFTER_END:
        return None
    return Refusal(
        "status",
        f"{slug} is {status}: it ended, and only its cleanup runs now",
        f"lem land next {slug} names what is left",
    )
