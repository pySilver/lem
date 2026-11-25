"""The app binds each port to its adapter, and tests can supply their own ports."""

import dataclasses
import importlib
import types
from typing import TYPE_CHECKING

import pytest

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.terminal import FakeTerminal
from lem.app import binding, wiring
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path


def place(tmp_path: Path) -> Place:
    """A place in `tmp_path`."""
    return Place(checkout=tmp_path, home=tmp_path / "home", environ={})


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


def test_a_missing_dependency_faults_at_binding(
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


def test_a_commands_ports_are_bound_for_its_checkout_its_home_and_its_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    places: list[Place] = []
    module = types.SimpleNamespace(bind=places.append)
    real = importlib.import_module

    def found(name: str) -> object:
        return module if name == "lem.adapters.terminal_agterm" else real(name)

    monkeypatch.setattr(importlib, "import_module", found)
    environ = {"XDG_CONFIG_HOME": str(tmp_path / "config")}
    binding.bound_for(tmp_path, environ)
    assert places == [
        Place(checkout=tmp_path, home=tmp_path / "config" / "lem", environ=environ)
    ]
