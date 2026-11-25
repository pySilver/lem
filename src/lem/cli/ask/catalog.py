"""The shipped templates and demos of the question page."""

from typing import TYPE_CHECKING

from lem.cli.ask import spec as specs
from lem.kernel import paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path


def folder(kind: str) -> Path:
    """The questions Lem ships for this use."""
    return paths.root() / "skills" / "lem-ask" / kind


def listing(kind: str) -> tuple[dict[str, str], ...]:
    """The names and descriptions of the question specs in a folder."""
    shipped = sorted(folder(kind).glob("*.json"))
    return tuple(
        {"name": path.stem, "about": description(path)}
        for path in shipped
        if not path.name.startswith(".")
    )


def demos(names: tuple[str, ...]) -> tuple[Path, ...]:
    """Every requested demo, in order, or a refusal that names the choices."""
    available = paths_by_name()
    wanted = names or tuple(available)
    unknown = tuple(name for name in wanted if name not in available)
    if unknown:
        raise unknown_names(unknown, tuple(available))
    return tuple(available[name] for name in wanted)


def unknown_names(unknown: tuple[str, ...], have: tuple[str, ...]) -> Refusal:
    """Name the demos the owner may choose."""
    missing = ", ".join(unknown)
    choices = ", ".join(have)
    return Refusal(
        "ask-demo", f"no question demo named {missing}", f"choose from: {choices}"
    )


def examples() -> tuple[dict[str, str], ...]:
    """The demos and templates that can be shown by name."""
    return tuple(
        {**entry, "folder": kind}
        for kind in ("demos", "templates")
        for entry in listing(kind)
    )


def description(path: Path) -> str:
    """What a shipped spec says it shows."""
    spec, _ = specs.load(str(path))
    return str(spec.get("_about", ""))


def paths_by_name() -> dict[str, Path]:
    """The installed path of every demo or template."""
    return {
        entry["name"]: folder(entry["folder"]) / f"{entry['name']}.json"
        for entry in examples()
    }
