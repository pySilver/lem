"""The task picker's line names the app's command by the path an update keeps: Homebrew's
`opt/lem/bin/lem` when the app is under it, else the `lem` beside the app's Python; a line of a
Lem before the app is one that no longer works."""

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.picker import keymap_runs, picker_row, stable_lem
from unit.settings.doctor.stage import Stage, script

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine of its own for each case."""
    return Stage(tmp_path.resolve())


def app(stage: Stage, folder: str) -> Path:
    """An app's environment at `folder`: its `bin/python` and `bin/lem`."""
    env = stage.root / folder
    for name in ("python", "lem"):
        script(env / "bin" / name, "x")
    return env


def test_homebrews_opt_path_when_the_app_is_under_it(stage: Stage) -> None:
    env = app(stage, "brew/Cellar/lem/0.4.0/libexec")
    cellar = stage.brew / "Cellar" / "lem" / "0.4.0"
    (cellar / "bin").mkdir()
    (cellar / "bin" / "lem").symlink_to(env / "bin" / "lem")
    (stage.brew / "opt").mkdir()
    (stage.brew / "opt" / "lem").symlink_to(cellar)
    look = stage.look()
    brewed = replace(look, executable=env / "bin" / "python", prefix=env)
    assert stable_lem(brewed) == stage.brew / "opt" / "lem" / "bin" / "lem"
    venv = app(stage, "checkout/.venv")
    elsewhere = replace(look, executable=venv / "bin" / "python", prefix=venv)
    assert stable_lem(elsewhere) == venv / "bin" / "lem"
    (venv / "bin" / "lem").unlink()
    assert stable_lem(elsewhere) is None


def test_a_line_runs_the_command_by_its_path_a_link_or_from_home(stage: Stage) -> None:
    command = app(stage, "app") / "bin" / "lem"
    (stage.root / "links").mkdir()
    (stage.root / "links" / "lem").symlink_to(command)
    for said in (
        f'command "Lem tasks ›" ctrl+cmd+t --error-hud {command} picker',
        f"command Lem  ctrl+cmd+t  {stage.root / 'links' / 'lem'} picker",
        "command Lem ctrl+cmd+t ~/app/bin/lem picker",
    ):
        assert keymap_runs(said, stage.root, command), said
    for said in (
        f"command Board ctrl+cmd+b {command} serve ensure",
        f"# command Lem ctrl+cmd+t {command} picker",
        f"keybind ctrl+t {command} picker",
        "command Lem ctrl+cmd+t ~/elsewhere/lem picker",
        f"command Lem ctrl+cmd+t {command}",
    ):
        assert not keymap_runs(said, stage.root, command), said


def test_the_row_gives_the_line_and_names_an_old_line_that_no_longer_works(
    stage: Stage,
) -> None:
    command = app(stage, "app") / "bin" / "lem"
    line = f'command "Lem tasks ›" ctrl+cmd+t --error-hud {command.resolve()} picker'
    absent = picker_row(stage.look())
    assert (absent.need, absent.found, absent.line) == ("optional", False, line)
    keymap = stage.home / ".config" / "agterm" / "keymap.conf"
    keymap.parent.mkdir(parents=True)
    keymap.write_text(f"{line}\n", encoding="utf-8")
    held = picker_row(stage.look())
    assert (held.found, held.detail) == (True, f"{keymap} holds the line")
    for old in (
        (
            "command Lem ctrl+cmd+t /usr/bin/python3 "
            "~/.claude/plugins/marketplaces/lem/skills/lem/scripts/picker.py"
        ),
        (
            'command "Lem tasks ›" ctrl+cmd+t --error-hud /opt/homebrew/bin/python3 '
            "/Users/o/.claude/plugins/marketplaces/lem/bin/lem picker"
        ),
    ):
        keymap.write_text(f"{old}\n", encoding="utf-8")
        row = picker_row(stage.look())
        assert (row.found, row.line) == (False, line)
        assert row.detail is not None
        assert (
            f"holds a line of a Lem before the app, which no longer works: {old}"
            in (row.detail)
        )
        assert "`agtermctl keymap reload`" in row.detail
    (stage.app / "bin" / "lem").unlink()
    none = picker_row(stage.look())
    assert (none.found, none.line) == (False, None)
    assert "the owner installs Lem again" in (none.without_it or "")
