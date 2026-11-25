"""Put local attachments into a question page so it can stand on its own."""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.ask import images, sourced

if TYPE_CHECKING:
    from lem.cli.ask.spec import Spec


def attach(node: object, base: Path) -> None:
    """Read the files of each block, at any depth in the spec."""
    if isinstance(node, list):
        for block in node:
            attach(block, base)
    if isinstance(node, dict):
        fill(node, base)
        for block in node.values():
            attach(block, base)


def fill(block: Spec, base: Path) -> None:
    """Read the code, markdown, chart, diff or image named by this block."""
    for kind in sourced.KINDS:
        ref = block.get(kind)
        if isinstance(ref, dict) and "file" in ref:
            sourced.fill(block, kind, ref, base)
    image = block.get("image")
    if isinstance(image, str) and not image.startswith(
        ("http://", "https://", "data:")
    ):
        path = Path(base, Path(image).expanduser())
        block["image"] = images.encoded(path)
