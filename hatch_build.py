"""The one part of Lem's build that pyproject.toml cannot say: what an editable install
of a checkout holds (`uv sync`, which makes .venv).

A wheel holds the plugin's files under `lem/data` (pyproject.toml, `force-include`), and
hatchling puts them into an editable install too, a copy in .venv that no edit of the
checkout reaches. An editable install takes none: its `paths.ROOT` is the checkout
itself, since `src/lem/data` is not there. It takes `checkout.pth` instead, which turns
bytecode off for every Python that starts from .venv: `.venv/bin/lem` imports `lem`
before a line of Lem's runs, and that import would write `src/lem/__pycache__` into the
checkout, where a check looks for it (tests/all.sh).
"""

from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CheckoutHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if version == "editable":
            build_data["force_include_editable"] = {"checkout.pth": "_lem_checkout.pth"}
