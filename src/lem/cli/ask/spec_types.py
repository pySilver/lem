"""Fields the question page reads before it draws a spec."""

from typing import Literal

import msgspec


class Page(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    rename="camel",
    forbid_unknown_fields=True,
):
    """Fields of the whole page."""

    title: str = ""
    subtitle: str = ""
    source: str = ""
    context: object = None
    width: Literal["narrow"] | None = None
    submit_label: str = "Send"
    chat: bool = True
    script: str = ""
    style: Literal["refined", "minimal", "bold", "terminal"] = "refined"
    review: Literal["auto", "always", "never"] | bool = "auto"
    size: str | int = "auto"
    questions: list[dict[str, object]] | None = None


class Question(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """Fields of one question."""

    id: str | None = None
    header: str = ""
    prompt: str = ""
    hint: str = ""
    context: object = None
    body: object = None
    recommendation: str = ""
    mode: Literal["single", "multi", "text", "tune"] | None = None
    min: int = 0
    max: int | None = None
    layout: Literal["list", "grid", "compare", "inline"] | None = None
    columns: int | None = None
    expanded: bool = False
    optional: bool = False
    text: bool | dict[str, object] = True
    toggle: bool = True
    options: list[str | dict[str, object]] | None = None
    controls: list[dict[str, object]] | None = None
    preview: object = None
    baseline: str | bool = False


class Option(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """Fields of an option or a tune preset."""

    id: str | None = None
    label: str = ""
    subtitle: str = ""
    recommended: bool | str = False
    badge: str = ""
    tags: list[str] = msgspec.field(default_factory=list)
    pros: list[str] = msgspec.field(default_factory=list)
    cons: list[str] = msgspec.field(default_factory=list)
    detail: object = None
    preview: object = None
    default: bool = False
    selected: bool = False
    preset: dict[str, object] | None = msgspec.field(name="values", default=None)


class Control(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """Fields of a tune control."""

    id: str = ""
    label: str = ""
    type: Literal["range", "hue", "color", "select", "toggle"] = "range"
    min: int | float | None = None
    max: int | float | None = None
    step: int | float | None = None
    initial: object = msgspec.field(name="value", default=None)
    unit: str = ""
    options: list[str | int | float] | None = None
    on: object = None
    off: object = None
