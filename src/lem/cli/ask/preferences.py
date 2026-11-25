"""The page's style, review, overlay size, and terminal choices."""

import json
from typing import TYPE_CHECKING

from lem.cli.ask.overlay import Display
from lem.cli.ask.spec import invalid, size_ok
from lem.kernel.errors import Refusal
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from lem.cli.ask.shown import Shown
    from lem.cli.ask.spec import Spec
    from lem.settings.shared import Ask

# Panel sizes and the narrow-case bounds are the display heuristics on main.
LARGE = 90
NARROW = 66
NORMAL = 78
NARROW_BYTES = 1500
NARROW_OPTIONS = 4
LARGE_QUESTIONS = 3
VISUAL = ('"preview"', '"mermaid"', '"chart"', '"image"', '"stats"', '"table"')


def defaults() -> Ask:
    """The settings of the owner, with the defaults in the settings schema."""
    loaded = settings_of(None)
    pref = loaded.settings.ask
    if not size_ok(pref.size):
        where = loaded.sources["ask.size"]
        raise Refusal(
            "settings",
            f"{where}: ask.size = {pref.size!r} is invalid",
            'give ask.size a percent from 1 to 100, "auto" or "full"',
        )
    return pref


def apply(spec: Spec, pref: Ask, call: Shown | None = None) -> None:
    """Apply explicit flags over the spec and the owner's defaults."""
    spec.setdefault("style", pref.style)
    spec.setdefault("review", pref.review)
    if call is not None and call.style is not None:
        spec["style"] = call.style
    if call is not None and call.review is not None:
        spec["review"] = call.review


def display(spec: Spec, pref: Ask, call: Shown) -> Display:
    """Choose the overlay size before local images and charts expand the spec."""
    default_size = spec.get("size", pref.size)
    size = default_size if call.size is None else call.size
    if not size_ok(size):
        raise invalid("size needs auto, full, or a percent from 1 to 100")
    if call.full or size == "full":
        percent = None
    else:
        percent = str(auto_size(spec) if size == "auto" else size)
    return Display(percent=percent, follow=call.follow, chromeless=call.chromeless)


def auto_size(spec: Spec) -> int:
    """A preview, diagram, comparison or several questions need a larger panel."""
    raw = json.dumps(spec)
    questions = spec.get("questions")
    shown = questions if isinstance(questions, list) else [spec]
    if any(mark in raw for mark in VISUAL) or large_questions(shown):
        return LARGE
    if (
        spec.get("width") == "narrow"
        and len(raw) < NARROW_BYTES
        and all(map(narrow, shown))
    ):
        return NARROW
    return NORMAL


def large_questions(shown: list[Spec]) -> bool:
    """Several questions or a comparison fill the wider panel."""
    return len(shown) >= LARGE_QUESTIONS or any(
        question.get("layout") == "compare" for question in shown
    )


def narrow(spec: Spec) -> bool:
    """A short list still fits in the narrow panel."""
    choices = spec.get("options")
    return not isinstance(choices, list) or len(choices) <= NARROW_OPTIONS
