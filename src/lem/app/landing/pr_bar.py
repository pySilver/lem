"""The bar's edited tests and missing marks in the pull request's text."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.landing.checks import Checked, Edited, EditedKind

KINDS = ("test", "snapshot", "test configuration")


def named(edits: tuple[Edited, ...], kind: EditedKind) -> str:
    """The number and paths of the files of this kind."""
    paths = [one.path for one in edits if one.kind == kind]
    if not paths:
        return ""
    noun = kind if len(paths) == 1 else f"{kind}s"
    listed = ", ".join(f"`{path}`" for path in paths)
    return f"{len(paths)} existing {noun} ({listed})"


def edited(checked: Checked) -> Lines:
    """The types of existing tests the change edits, in one line."""
    grouped = (named(checked.edited, kind) for kind in KINDS)
    parts = tuple(filter(None, grouped))
    if not parts:
        return ()
    first = ", ".join(parts[:-1])
    last = parts[-1]
    listed = f"{first} and {last}" if first else last
    return (f"- the change edits {listed}",)


def lines(checked: Checked | None, *, full: bool) -> Lines:
    """What the bar read, with the kinds of file it cannot read on the standard track."""
    if checked is None:
        return ()
    found = edited(checked)
    if not full or not checked.not_covered:
        return found
    listed = ", ".join(checked.not_covered)
    return (
        *found,
        f"- the bar has no marks of its own for files of these kinds: {listed}",
    )
