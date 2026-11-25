"""`Ports`: a test builds them from its fakes; the app binds each port to its adapter, and a
port whose adapter is not built refuses every call."""

import dataclasses
import importlib
import types
from typing import TYPE_CHECKING, cast

import pytest

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.terminal import FakeTerminal
from lem.app import wiring
from lem.kernel.errors import Fault
from lem.ports.judge import Defect
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git
    from lem.ports.judge import Judge


def place(tmp_path: Path) -> Place:
    """A place in `tmp_path`."""
    return Place(checkout=tmp_path, home=tmp_path / "home", environ={})


def test_a_port_with_no_adapter_refuses_every_call_by_name(tmp_path: Path) -> None:
    # A module name no step builds, so that the case holds whichever adapters exist.
    unbuilt = wiring.adapter("lem.adapters.never_built", place(tmp_path))
    assert isinstance(unbuilt, wiring.Unbound)
    with pytest.raises(
        Fault, match=r"tip: the port's adapter lem\.adapters\.never_built is not built"
    ):
        cast("Git", unbuilt).tip(tmp_path, "HEAD")
    with pytest.raises(
        Fault, match=r"over_bar: the port's adapter lem\.adapters\.never_built"
    ):
        cast("Judge", unbuilt).over_bar(Defect(where="w", title="t", what="x"))


def test_an_adapter_that_exists_is_bound_to_the_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    made = FakeTerminal()
    module = types.SimpleNamespace(bind=lambda where: (made, where)[0])
    real = importlib.import_module

    def found(name: str) -> object:
        return module if name == "lem.adapters.terminal_agterm" else real(name)

    monkeypatch.setattr(importlib, "import_module", found)
    assert wiring.bound(place(tmp_path)).terminal is made


def test_a_module_an_adapter_needs_and_lacks_is_no_silent_unbound(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def broken(name: str) -> object:
        raise ModuleNotFoundError("No module named 'psutil'", name="psutil")

    monkeypatch.setattr(importlib, "import_module", broken)
    with pytest.raises(ModuleNotFoundError, match="psutil"):
        wiring.bound(place(tmp_path))


def test_a_test_builds_the_ports_from_its_fakes_and_replaces_one(
    tmp_path: Path,
) -> None:
    git = ModelGit.init(tmp_path / "checkout", {"README.md": b"one\n"})
    ports = fake_ports(git, LocalForge(remote=git))
    assert ports.git is git
    other = FakeTerminal()
    assert dataclasses.replace(ports, terminal=other).terminal is other
