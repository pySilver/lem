"""The rows about the repository of the call, which never fail the check: the permission mode a
builder meets there, Lem's plugin installed for the user, and the project's personas."""

import json
from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.personas import persona_rows
from lem.cli.doctor.project_rows import mode_rows, scope_rows
from lem.cli.doctor.row import reported
from unit.settings.doctor.stage import Stage

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine of its own for each case."""
    return Stage(tmp_path)


def mode(stage: Stage, relative: str, said: str) -> Path:
    """A settings file of Claude Code that names the permission mode `said`."""
    return stage.write(relative, json.dumps({"permissions": {"defaultMode": said}}))


def test_lem_assumes_auto_mode_and_a_mode_counts_from_the_nearest_file(
    stage: Stage,
) -> None:
    assert mode_rows(stage.look()) == ()
    repo = stage.repository()
    (row,) = mode_rows(stage.look(repo))
    assert (row.need, row.found, row.detail) == (
        "project",
        False,
        "default: no settings file names one",
    )
    assert row.used_for.startswith("Lem assumes that Claude Code runs in auto mode")
    said = row.without_it or ""
    assert 'put "defaultMode": "auto" under "permissions"' in said
    assert "at night nobody answers" in said
    user = mode(stage, "home/.claude/settings.json", "acceptEdits")
    assert mode_rows(stage.look(repo))[0].detail == f"acceptEdits, from {user}"
    shared = mode(stage, "repo/.claude/settings.json", "plan")
    (planned,) = mode_rows(stage.look(repo))
    assert planned.detail == f"plan, from {shared}"
    assert (planned.without_it or "").startswith("a builder can read and cannot edit")
    local = mode(stage, "repo/.claude/settings.local.json", "dontAsk")
    assert mode_rows(stage.look(repo))[0].detail == f"dontAsk, from {local}"


def test_auto_and_bypass_count_from_the_users_settings_only(stage: Stage) -> None:
    repo = stage.repository()
    mode(stage, "repo/.claude/settings.local.json", "auto")
    mode(stage, "repo/.claude/settings.json", "bypassPermissions")
    assert mode_rows(stage.look(repo))[0].found is False
    user = mode(stage, "home/.claude/settings.json", "auto")
    (row,) = mode_rows(stage.look(repo))
    assert (row.found, row.detail) == (True, f"auto, from {user}")
    assert (row.without_it or "").startswith("a builder asks nobody; the classifier")
    mode(stage, "home/.claude/settings.json", "bypassPermissions")
    assert mode_rows(stage.look(repo))[0].without_it == "a builder asks nobody"
    mode(stage, "home/.claude/settings.json", "someday")
    assert "a mode this check does not know" in (
        mode_rows(stage.look(repo))[0].without_it or ""
    )
    assert reported(mode_rows(stage.look(repo))).ok


def test_lems_plugin_for_the_user_gets_a_row_with_the_two_commands_and_for_a_project_none(
    stage: Stage,
) -> None:
    repo = stage.repository()
    stage.plugins(
        {"plugins": {"lem@lem": [{"scope": "project", "projectPath": str(repo)}]}}
    )
    assert scope_rows(stage.look()) == ()
    stage.plugins({"plugins": {"lem@lem": [{"scope": "user"}]}})
    (row,) = scope_rows(stage.look())
    assert (row.name, row.need, row.found) == ("lem plugin scope", "project", False)
    assert row.detail == (
        "lem@lem is installed for the user, so every repository on this machine loads it"
    )
    said = row.without_it or ""
    assert "costs about a tenth of a second a message" in said
    assert "`claude plugin uninstall lem@lem --scope user`" in said
    assert "`claude plugin install lem@lem --scope project`" in said


def test_a_lem_repository_with_no_personas_or_one_gets_its_row_and_no_other_place_does(
    stage: Stage,
) -> None:
    assert persona_rows(stage.look()) == ()
    plain = stage.repository("plain", lem=False)
    assert persona_rows(stage.look(plain)) == ()
    repo = stage.repository()
    (none,) = persona_rows(stage.look(repo))
    assert (none.need, none.found) == ("project", False)
    assert "`/lem init`" in (none.without_it or "")
    stage.write("repo/.lem/personas/shopper.md", "x")
    stage.write("repo/.lem/personas/README.md", "x")
    (one,) = persona_rows(stage.look(repo))
    assert one.found
    assert (one.detail or "").endswith(
        ": a panel needs a second person who would notice other things"
    )
    stage.write("repo/.lem/personas/clerk.md", "x")
    tree = stage.worktree(repo, "gift-note")
    (two,) = persona_rows(stage.look(tree))
    assert two.detail == f"2 ({repo.resolve() / '.lem' / 'personas'})"
    assert reported((none, one, two)).ok


def test_a_persona_that_does_not_read_is_named_with_its_fix(stage: Stage) -> None:
    repo = stage.repository()
    stage.write("repo/.lem/personas/clerk.md", "x")
    bad = repo / ".lem" / "personas" / "shopper.md"
    bad.write_bytes(b"\xff\xfe a person\n")
    (row,) = persona_rows(stage.look(repo))
    assert row.found is False
    assert "shopper.md is not UTF-8" in (row.detail or "")
    assert "save it as UTF-8" in (row.without_it or "")
