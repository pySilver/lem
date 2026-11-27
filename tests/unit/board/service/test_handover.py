"""A board server whose own install was replaced: its package folder or its Python's standard
library gone, another release or build written into it, or Homebrew's `opt/lem` moved to
another keg; the installed Lem's `lem` by a path an update keeps; the look that hands over once
for each reason, says once when no installed Lem is there, and says when the hand-over left the
server serving; the server's answer that says why; and `lem serve ensure`, which replaces such
a server whatever its release."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from fakes.records import MOMENT
from lem.board import ensure, handover, install, replaced
from lem.board.facts import Facts
from lem.board.install import BUILD_COMMIT
from lem.kernel import paths
from unit.board.service.given import made

if TYPE_CHECKING:
    from collections.abc import Mapping

    import pytest

STDLIB = handover.STDLIB
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
    assert replaced.replaced("1.0.0", "abc", package, STDLIB) is None
    plain = tmp_path / "uv" / "lem"
    (plain / MANIFEST).parent.mkdir(parents=True)
    (plain / MANIFEST).write_text('{"version": "1.0.0"}')
    assert replaced.replaced("1.0.0", None, plain, STDLIB) is None


def test_a_package_folder_an_update_removed_is_a_replaced_install(
    tmp_path: Path,
) -> None:
    gone = tmp_path / "brew" / "Cellar" / "lem" / "0.4.1" / SITE
    assert replaced.replaced("0.4.1", "abc", gone, STDLIB) == (
        f"its package folder {gone} is gone"
    )


def test_a_folder_without_lems_files_is_a_replaced_install(tmp_path: Path) -> None:
    package = tmp_path / "lem"
    package.mkdir()
    why = replaced.replaced("1.0.0", None, package, STDLIB)
    assert why is not None
    assert why.startswith("Lem's files are neither in")


def test_another_release_or_build_in_the_same_folder_is_a_replaced_install(
    tmp_path: Path,
) -> None:
    package = keg(tmp_path, "1.0.0", "def")
    assert replaced.replaced("0.9.0", "def", package, STDLIB) == (
        f"its package folder {package} holds Lem 1.0.0 now"
    )
    assert replaced.replaced("1.0.0", "abc", package, STDLIB) == (
        f"its package folder {package} holds the build def of Lem 1.0.0 now"
    )


def test_homebrews_opt_lem_on_another_keg_is_a_replaced_install(
    tmp_path: Path,
) -> None:
    package = keg(tmp_path, "0.4.1", "abc")
    keg(tmp_path, "0.4.2", "def")
    linked(tmp_path, "0.4.1")
    assert replaced.replaced("0.4.1", "abc", package, STDLIB) is None
    newer = linked(tmp_path, "0.4.2")
    opt = tmp_path.resolve() / "opt" / "lem"
    assert (
        replaced.replaced("0.4.1", "abc", package, STDLIB) == f"{opt} names {newer} now"
    )


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
        stdlib=STDLIB,
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


def test_a_python_whose_standard_library_an_update_removed_is_a_replaced_install(
    tmp_path: Path,
) -> None:
    package = keg(tmp_path, "0.4.2", "abc")
    gone = tmp_path / "python@3.14" / "3.14.10" / "lib" / "python3.14"
    assert replaced.replaced("0.4.2", "abc", package, gone) == (
        f"the standard library of its Python, {gone}, is gone"
    )


def served_from(package: Path, *, why: str | None = None) -> Facts:
    """A running server of this release from `package`, saying `why` it was replaced."""
    mine = install.install_of()
    return Facts(
        pid=1,
        port=4999,
        url="http://127.0.0.1:4999/",
        host="studio",
        install=msgspec.structs.replace(mine, package=str(package)),
        home="/nowhere",
        started=MOMENT,
        replaced=why,
    )


def test_ensure_replaces_a_server_of_a_replaced_install_whatever_its_release(
    tmp_path: Path,
) -> None:
    here = served_from(paths.PACKAGE.resolve())
    assert ensure.kept(here, None) is not None
    gone = served_from(tmp_path / "brew" / "Cellar" / "lem" / "0.4.2" / SITE)
    assert replaced.stale(gone) is not None
    assert ensure.kept(gone, None) is None
    said = "the standard library of its Python, /old/python3.14, is gone"
    told = served_from(paths.PACKAGE.resolve(), why=said)
    assert replaced.stale(told) == said
    assert ensure.kept(told, None) is None
    old = keg(tmp_path / "brew", "0.4.2", "abc")
    keg(tmp_path / "brew", "0.4.2_1", "abc")
    linked(tmp_path / "brew", "0.4.2")
    assert replaced.stale(served_from(old)) is None
    newer = linked(tmp_path / "brew", "0.4.2_1")
    opt = (tmp_path / "brew").resolve() / "opt" / "lem"
    assert replaced.stale(served_from(old)) == f"{opt} names {newer} now"


def test_the_servers_answer_says_why_its_install_was_replaced(
    tmp_path: Path,
) -> None:
    board = made(tmp_path, None)
    with board.main() as client:
        assert client.get("/api/server").json()["replaced"] is None
        board.app.state.handover.why = "its package folder /gone/lem is gone"
        assert client.get("/api/server").json()["replaced"] == (
            "its package folder /gone/lem is gone"
        )
