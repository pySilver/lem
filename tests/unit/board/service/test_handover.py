"""A board server whose own install was replaced: its package folder gone, another release or
build written into it, or Homebrew's `opt/lem` moved to another keg; the installed Lem's `lem`
by a path an update keeps; and the look that hands over once for each reason, says once when no
installed Lem is there, and says when the hand-over left the server serving."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from lem.board import handover, replaced
from lem.board.install import BUILD_COMMIT

if TYPE_CHECKING:
    from collections.abc import Mapping

    import pytest

SITE = Path("libexec") / "lib" / "python3.14" / "site-packages" / "lem"
MANIFEST = Path("data") / ".claude-plugin" / "plugin.json"


def keg(brew: Path, version: str, commit: str | None = None) -> Path:
    """The package folder of Homebrew's keg of Lem `version` under the prefix `brew`."""
    package = brew / "Cellar" / "lem" / version / SITE
    (package / MANIFEST).parent.mkdir(parents=True)
    (package / MANIFEST).write_text(f'{{"version": "{version}"}}')
    if commit is not None:
        (package / BUILD_COMMIT).write_text(f"{commit}\n")
    return package.resolve()


def linked(brew: Path, version: str) -> Path:
    """Point Homebrew's `opt/lem` at the keg of `version`, with its `bin/lem`."""
    target = brew / "Cellar" / "lem" / version
    command = target / "bin" / "lem"
    command.parent.mkdir(parents=True, exist_ok=True)
    command.write_text("#!/bin/sh\n")
    command.chmod(0o755)
    opt = brew / "opt" / "lem"
    opt.parent.mkdir(exist_ok=True)
    if opt.is_symlink():
        opt.unlink()
    opt.symlink_to(target)
    return target.resolve()


def test_an_install_that_is_still_the_installed_one_is_not_replaced(
    tmp_path: Path,
) -> None:
    package = keg(tmp_path, "1.0.0", "abc")
    linked(tmp_path, "1.0.0")
    assert replaced.replaced("1.0.0", "abc", package) is None
    plain = tmp_path / "uv" / "lem"
    (plain / MANIFEST).parent.mkdir(parents=True)
    (plain / MANIFEST).write_text('{"version": "1.0.0"}')
    assert replaced.replaced("1.0.0", None, plain) is None


def test_a_package_folder_an_update_removed_is_a_replaced_install(
    tmp_path: Path,
) -> None:
    gone = tmp_path / "brew" / "Cellar" / "lem" / "0.4.1" / SITE
    assert replaced.replaced("0.4.1", "abc", gone) == (
        f"its package folder {gone} is gone"
    )


def test_a_folder_without_lems_files_is_a_replaced_install(tmp_path: Path) -> None:
    package = tmp_path / "lem"
    package.mkdir()
    why = replaced.replaced("1.0.0", None, package)
    assert why is not None
    assert why.startswith("Lem's files are neither in")


def test_another_release_or_build_in_the_same_folder_is_a_replaced_install(
    tmp_path: Path,
) -> None:
    package = keg(tmp_path, "1.0.0", "def")
    assert replaced.replaced("0.9.0", "def", package) == (
        f"its package folder {package} holds Lem 1.0.0 now"
    )
    assert replaced.replaced("1.0.0", "abc", package) == (
        f"its package folder {package} holds the build def of Lem 1.0.0 now"
    )


def test_homebrews_opt_lem_on_another_keg_is_a_replaced_install(
    tmp_path: Path,
) -> None:
    package = keg(tmp_path, "0.4.1", "abc")
    keg(tmp_path, "0.4.2", "def")
    linked(tmp_path, "0.4.1")
    assert replaced.replaced("0.4.1", "abc", package) is None
    newer = linked(tmp_path, "0.4.2")
    opt = tmp_path.resolve() / "opt" / "lem"
    assert replaced.replaced("0.4.1", "abc", package) == f"{opt} names {newer} now"


def test_the_installed_lem_is_homebrews_opt_for_a_keg_else_beside_the_python(
    tmp_path: Path,
) -> None:
    package = tmp_path / "brew" / "Cellar" / "lem" / "0.4.1" / SITE
    python = Path("/opt/homebrew/Cellar/lem/0.4.1/libexec/bin/python")
    assert replaced.successor(package, python) == (
        tmp_path / "brew" / "opt" / "lem" / "bin" / "lem"
    )
    tool = Path("/Users/me/.local/share/uv/tools/lem/bin/python")
    assert replaced.successor(tmp_path / "uv" / "lem", tool) == tool.parent / "lem"


@dataclass
class Child:
    """A stand-in for the `ensure` the look starts: its status once it ended."""

    code: int | None = None

    def poll(self) -> int | None:
        return self.code


@dataclass
class Launches:
    """The `ensure` calls the look made, each with its environment."""

    calls: list[tuple[Path, Mapping[str, str]]]
    child: Child


def launches(monkeypatch: pytest.MonkeyPatch) -> Launches:
    """Record each start of `ensure` instead of starting it."""
    held = Launches(calls=[], child=Child())

    def launched(command: Path, home: Path, environ: Mapping[str, str]) -> Child:
        held.calls.append((command, environ))
        return held.child

    monkeypatch.setattr(handover, "launched", launched)
    return held


def watcher_of(tmp_path: Path, package: Path) -> handover.Handover:
    """The look of a server of Lem 0.4.1 from `package`."""
    return handover.Handover(
        version="0.4.1",
        commit="abc",
        package=package,
        executable=Path("/nowhere/bin/python"),
        home=tmp_path / "home",
        environ={"PYTHONPATH": str(package.parent)},
    )


def test_the_look_says_once_when_no_installed_lem_is_there_then_hands_over_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    held = launches(monkeypatch)
    package = keg(tmp_path, "0.4.1", "abc")
    looks = watcher_of(tmp_path, package)
    looks.look()
    assert held.calls == []
    assert capsys.readouterr().err == ""

    (package / MANIFEST).unlink()
    (package / MANIFEST).parent.rmdir()
    (package / "data").rmdir()
    for _ in range(2):
        looks.look()
    err = capsys.readouterr().err
    command = tmp_path.resolve() / "opt" / "lem" / "bin" / "lem"
    assert err.count(f"No installed Lem is at {command}") == 1
    assert "keeps serving what it can" in err
    assert held.calls == []

    linked(tmp_path, "0.4.2")
    looks.look()
    looks.look()
    [(started, environ)] = held.calls
    assert started == command
    assert environ is looks.environ
    assert "It hands over to" in capsys.readouterr().err

    held.child.code = 0
    looks.look()
    looks.look()
    assert len(held.calls) == 1
    assert capsys.readouterr().err == (
        "lem serve: the hand-over ended with status 0, and this server still serves: "
        "the lines before this one say why\n"
    )
