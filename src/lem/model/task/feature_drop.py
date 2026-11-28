"""The drop of a feature, as it is printed and said (`docs/plans/2026-11-27-a-feature-in-parts.md`,
"The drop"): each part that had not ended was dropped with it, each open pull request stays open,
and the feature's branch keeps its commits on origin. Lem never deletes that branch: "A
destructive or outward step is never yours" (`skills/lem/SKILL.md`), so the line names the one
command that does, for the owner.
"""

from lem.records.base import Frozen


class PartDropped(Frozen, frozen=True, kw_only=True):
    """A part the drop of its feature dropped: the status it left, and the address of its
    pull request when it has one."""

    slug: str
    was: str
    pull: str | None = None


class FeatureDropped(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The feature, the status it left and the one it is in, each part dropped with it, the
    feature's own pull request, its branch, and the command that deletes the branch on
    origin."""

    slug: str
    was: str
    status: str
    parts: tuple[PartDropped, ...]
    pull: str | None = None
    branch: str | None = None
    delete: str | None = None


def part_line(feature: str, line: str) -> str:
    """The state line of a part the drop of `feature` drops, with the owner's reason."""
    return f"dropped with its feature {feature}: {line}"


def delete_of(branch: str | None) -> str | None:
    """The command that deletes the feature's branch on origin, or None with no branch."""
    return None if branch is None else f"git push origin --delete {branch}"


def pulls_said(dropped: FeatureDropped) -> str | None:
    """Each pull request that stays open, by its task, or None when there is none."""
    pulls = [(part.slug, part.pull) for part in dropped.parts]
    pulls.append((dropped.slug, dropped.pull))
    named = [f"{slug}: {pull}" for slug, pull in pulls if pull]
    if not named:
        return None
    each = "; ".join(named)
    return (
        f"these pull requests stay open, and closing them is the owner's call: {each}"
    )


def said(dropped: FeatureDropped) -> str:
    """The line for the owner."""
    slugs = ", ".join(part.slug for part in dropped.parts)
    with_parts = (
        f", and with it each part that had not ended: {slugs}"
        if slugs
        else "; each of its parts had ended already"
    )
    lines = [f"the feature {dropped.slug} is dropped{with_parts}"]
    pulls = pulls_said(dropped)
    if pulls is not None:
        lines.append(pulls)
    if dropped.delete is not None:
        lines.append(
            f"the branch {dropped.branch} keeps its commits on origin, and Lem never "
            f"deletes it: the owner deletes it with {dropped.delete}"
        )
    return "; ".join(lines)
