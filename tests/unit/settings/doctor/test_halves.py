"""The rows of Lem's own halves and folders: the app's version against the plugin's, the `lem`
first on the PATH, the one question about reads outside the working directories, and the folders
of the Lem before."""

import json
from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.app_rows import lem_row, versions_row
from lem.cli.doctor.old_forms import old_forms_row
from lem.cli.doctor.reads import reads_row
from lem.hooks import versions
from lem.kernel import folders, paths
from unit.settings.doctor.stage import Stage, script

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine of its own for each case."""
    return Stage(tmp_path)


def manifest(stage: Stage, version: str) -> Path:
    """A plugin's folder whose manifest names `version`."""
    folder = stage.root / f"plugin-{version}"
    stage.write(
        f"plugin-{version}/.claude-plugin/plugin.json", json.dumps({"version": version})
    )
    return folder


def test_the_versions_row_says_both_halves_and_the_one_behind(stage: Stage) -> None:
    app = str(paths.root())
    mine = versions.version_of(app)
    same = versions_row(stage.look())
    assert (same.need, same.found, same.without_it) == ("required", True, None)
    assert same.detail == (
        f"Lem's app {mine} ({app}); Lem's plugin {mine} ({app}, the plugin Claude Code has "
        "for this repository)"
    )
    newer = manifest(stage, "999.0.0")
    behind = versions_row(stage.look(LEM_PLUGIN_ROOT=str(newer)))
    assert behind.found is False
    assert f"Lem's plugin 999.0.0 ({newer}, LEM_PLUGIN_ROOT)" in (behind.detail or "")
    assert "is behind Lem's plugin 999.0.0" in (behind.without_it or "")
    older = manifest(stage, "0.0.1")
    flagged = versions_row(stage.look(CLAUDE_PLUGIN_ROOT=str(older)))
    assert "Lem's plugin 0.0.1" in (flagged.without_it or "")


def test_the_lem_first_on_the_path_is_the_apps_own_command(stage: Stage) -> None:
    absent = lem_row(stage.look())
    assert (absent.need, absent.found, absent.detail) == (
        "required",
        False,
        "no lem on PATH",
    )
    own = script(stage.app / "bin" / "lem", "x")
    (stage.bin / "lem").symlink_to(own)
    assert lem_row(stage.look()).found
    (stage.bin / "lem").unlink()
    other = script(stage.bin / "lem", "x")
    row = lem_row(stage.look(PATH=f"{stage.bin}:{stage.app / 'bin'}"))
    assert row.found is False
    assert row.detail == (
        f"{other} comes first on PATH, and it is not Lem's command {own}; the owner puts "
        f"{stage.app / 'bin'} before {stage.bin} in his PATH"
    )


def test_the_reads_of_lems_files_name_the_question_and_its_allow_rule(
    stage: Stage,
) -> None:
    root = paths.root().resolve()
    row = reads_row(stage.look())
    assert (row.need, row.found, row.line) == ("optional", False, f"Read(/{root}/**)")
    assert "asks permission to read a Lem file outside the working directories" in (
        row.without_it or ""
    )
    user = stage.write(
        "home/.claude/settings.json",
        json.dumps({"permissions": {"allow": [f"Read(/{root.parent}/**)"]}}),
    )
    held = reads_row(stage.look())
    assert (held.found, held.detail) == (True, f"{user} allows the reads under {root}")
    stage.write(
        "home/.claude/settings.json",
        json.dumps({"permissions": {"allow": [f"Read({root}/**)", "Bash(lem *)"]}}),
    )
    assert not reads_row(stage.look()).found
    stage.write(
        "home/.claude/settings.json",
        json.dumps({"permissions": {"additionalDirectories": [str(root)]}}),
    )
    assert reads_row(stage.look()).found


def test_a_folder_of_the_lem_before_is_named_with_the_cutover(stage: Stage) -> None:
    row = old_forms_row(stage.look())
    assert (row.need, row.found, row.without_it) == ("required", True, None)
    stage.write("config/lem/owner.jsonl", "{}\n")
    repo = stage.repository()
    stage.write("repo/.lem/state/events.jsonl", "{}\n")
    old = old_forms_row(stage.look(repo))
    assert old.found is False
    assert old.detail == f"{stage.lem_home}, {repo.resolve() / '.lem' / 'state'}"
    assert "the owner's cutover" in (old.without_it or "")
    (stage.lem_home / folders.MARKER).write_bytes(folders.FORM)
    listed = stage.repository("listed")
    stage.write("listed/.lem/state/tasks/x/notes.md", "x")
    stage.write("config/lem/workspaces.json", json.dumps([str(listed)]))
    assert old_forms_row(stage.look()).detail == str(
        listed.resolve() / ".lem" / "state"
    )
    assert not (repo / ".lem" / "state" / folders.MARKER).exists()
