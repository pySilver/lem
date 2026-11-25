"""The rows of the plugin's hooks: the hooks file and `hooks/run` of the plugin Claude Code has,
the modules of `lem-hook` in the app, `hooks/run`'s look for `lem-hook`, and the correction hook
registered in more than one place."""

import json
from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.correction_hook import correction_hook_rows
from lem.cli.doctor.hook_bin import lem_hook_row, plugin_folder
from lem.cli.doctor.hook_entries import hook_entries
from lem.cli.doctor.hook_modules import hook_modules_row
from lem.kernel import paths
from unit.settings.doctor.stage import Stage, script

if TYPE_CHECKING:
    from pathlib import Path

PLUGIN_LINE = '/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" {} 2>/dev/null || :'
SELECTED = ("main", "corrections", "serve", "session", "precompact", "stop")


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine of its own for each case."""
    return Stage(tmp_path)


def plugin(stage: Stage, manifest: str | None, *, run: bool = True) -> Path:
    """A plugin's folder whose hooks file holds `manifest` (none when None), with
    `hooks/run` unless `run` is false."""
    folder = stage.root / "plugin"
    (folder / "hooks").mkdir(parents=True)
    if manifest is not None:
        (folder / "hooks" / "hooks.json").write_text(manifest, encoding="utf-8")
    if run:
        (folder / "hooks" / "run").write_text("exit 0\n", encoding="utf-8")
    return folder


def package(stage: Stage) -> Path:
    """An app's package with each module `lem-hook` runs whole, and `corrections.py`
    importing `lem.hooks.raw`, which is not there."""
    folder = stage.root / "app" / "lem"
    (folder / "hooks").mkdir(parents=True)
    for name in SELECTED:
        (folder / "hooks" / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
    (folder / "hooks" / "corrections.py").write_text(
        "import json\n\nfrom lem.hooks import raw\n\n\n"
        "def later() -> None:\n    from lem import store\n",
        encoding="utf-8",
    )
    return folder


def lines() -> str:
    """The hooks file of this repository."""
    return (paths.root() / "hooks" / "hooks.json").read_text(encoding="utf-8")


def test_the_plugin_and_the_app_of_this_repository_are_whole() -> None:
    row = hook_modules_row(paths.root(), paths.PACKAGE)
    assert (row.name, row.need, row.found) == ("hook modules", "required", True)
    assert (row.detail or "").startswith(
        "corrections, serve, session-start, precompact, stop from "
    )
    for name in ("hooks/main.py", "hooks/corrections.py", "hooks/session.py"):
        assert name in (row.detail or "")


def test_a_module_that_is_gone_or_does_not_compile_is_named_with_the_fix(
    stage: Stage,
) -> None:
    app = package(stage)
    (app / "hooks" / "raw.py").write_text("x = 1\n", encoding="utf-8")
    (app / "hooks" / "corrections.py").unlink()
    (app / "hooks" / "serve.py").write_text("def (:\n", encoding="utf-8")
    row = hook_modules_row(plugin(stage, lines()), app)
    assert row.found is False
    assert row.detail == (
        "hooks/corrections.py is missing; hooks/serve.py does not compile (line 1)"
    )
    assert "Lem's app again" in (row.without_it or "")


@pytest.mark.parametrize(
    ("manifest", "said"),
    [
        (None, "hooks/hooks.json is missing"),
        ("{", "hooks/hooks.json is not JSON (line 1)"),
        ('{"hooks": ["Stop"]}', "hooks/hooks.json is not a table of hooks"),
        ("[]", "hooks/hooks.json is not a table of hooks"),
        (
            '{"hooks": {"Stop": [{"hooks": "x"}]}}',
            "hooks/hooks.json is not a table of hooks",
        ),
        (
            json.dumps(
                {"hooks": {"Stop": [{"hooks": [{"command": "python3 x.py stop"}]}]}}
            ),
            (
                "hooks/hooks.json has a line that is not Lem's: 'python3 x.py stop', which no "
                "lem-hook runs"
            ),
        ),
        (
            json.dumps(
                {
                    "hooks": {
                        "Stop": [{"hooks": [{"command": PLUGIN_LINE.format("sleep")}]}]
                    }
                }
            ),
            (
                "hooks/hooks.json has a line that is not Lem's: "
                f"{PLUGIN_LINE.format('sleep')!r}, which no lem-hook runs"
            ),
        ),
    ],
    ids=[
        "gone",
        "not-json",
        "a-list",
        "no-table",
        "no-hooks",
        "another-line",
        "a-selector",
    ],
)
def test_a_hooks_file_that_is_gone_or_reads_another_way_is_a_failing_row(
    stage: Stage, manifest: str | None, said: str
) -> None:
    app = package(stage)
    (app / "hooks" / "raw.py").write_text("x = 1\n", encoding="utf-8")
    row = hook_modules_row(plugin(stage, manifest), app)
    assert (row.found, row.detail) == (False, said)
    assert "installs the plugin again" in (row.without_it or "")


def test_a_plugin_with_no_hooks_run_is_a_failing_row(stage: Stage) -> None:
    app = package(stage)
    (app / "hooks" / "raw.py").write_text("x = 1\n", encoding="utf-8")
    row = hook_modules_row(plugin(stage, lines(), run=False), app)
    assert (row.found, row.detail) == (False, "hooks/run is missing")


def test_a_hook_module_that_imports_lem_outside_its_hooks_at_its_top_is_a_failing_row(
    stage: Stage,
) -> None:
    app = package(stage)
    (app / "hooks" / "raw.py").write_text("x = 1\n", encoding="utf-8")
    (app / "hooks" / "main.py").write_text("from lem import store\n", encoding="utf-8")
    row = hook_modules_row(plugin(stage, lines()), app)
    assert (row.found, row.detail) == (
        False,
        "hooks/main.py imports lem.store at its top, which every hook would pay at its start",
    )


def test_a_module_that_a_hook_module_imports_at_its_top_is_checked(
    stage: Stage,
) -> None:
    app = package(stage)
    folder = plugin(stage, lines())
    row = hook_modules_row(folder, app)
    assert (row.found, row.detail) == (False, "hooks/raw.py is missing")
    (app / "hooks" / "raw.py").write_text("x = 1\n", encoding="utf-8")
    row = hook_modules_row(folder, app)
    assert row.found
    assert "hooks/raw.py" in (row.detail or "")
    assert "store" not in (row.detail or "")


def test_the_plugin_is_the_install_for_the_repository_then_for_the_user_else_the_apps(
    stage: Stage,
) -> None:
    repo = stage.repository(lem=False)
    mine, users = stage.root / "cache" / "project", stage.root / "cache" / "user"
    mine.mkdir(parents=True)
    users.mkdir(parents=True)
    project = {"scope": "project", "projectPath": str(repo), "installPath": str(mine)}
    user = {"scope": "user", "installPath": str(users)}
    look = stage.look(repo)
    for listed, folder in (
        ([user, project], mine),
        ([user], users),
        ([], paths.root()),
        ([{**user, "installPath": str(stage.root / "gone")}], paths.root()),
    ):
        stage.plugins({"version": 2, "plugins": {"lem@lem": listed}})
        assert plugin_folder(look, repo) == folder
    stage.write(
        "repo/.claude/settings.local.json",
        json.dumps({"enabledPlugins": {"lem@lem": False}}),
    )
    stage.plugins({"plugins": {"lem@lem": [project]}})
    assert plugin_folder(look, repo) == paths.root()


def test_hooks_run_finds_lem_hook_where_it_looks_and_nowhere_else(stage: Stage) -> None:
    absent = lem_hook_row(stage.look())
    assert (absent.need, absent.found) == ("required", False)
    assert str(stage.brew / "opt" / "lem" / "libexec" / "bin" / "lem-hook") in (
        absent.detail or ""
    )
    script(stage.bin / "lem-hook", "x")
    assert not lem_hook_row(stage.look()).found
    tool = script(stage.home / ".local" / "bin" / "lem-hook", "x")
    assert (
        lem_hook_row(stage.look()).detail
        == f"{tool}, not this app's {stage.app}/bin/lem-hook"
    )
    own = script(stage.app / "bin" / "lem-hook", "x")
    brewed = stage.brew / "opt" / "lem" / "libexec" / "bin" / "lem-hook"
    brewed.parent.mkdir(parents=True)
    brewed.symlink_to(own)
    assert lem_hook_row(stage.look()).detail == f"{brewed}, this app's"
    assert lem_hook_row(stage.look(LEM_HOOK_BIN=str(tool))).detail == (
        f"{tool}, not this app's {stage.app}/bin/lem-hook"
    )
    assert not lem_hook_row(stage.look(LEM_HOOK_BIN="bin/lem-hook")).found


def settings(stage: Stage, relative: str, *commands: str) -> Path:
    """A settings file of Claude Code whose `UserPromptSubmit` hooks run `commands`."""
    hooks = [{"type": "command", "command": line} for line in commands]
    return stage.write(
        relative, json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": hooks}]}})
    )


def test_the_plugins_line_and_the_apps_entry_are_the_correction_hook(
    stage: Stage,
) -> None:
    said = [
        PLUGIN_LINE.format("corrections"),
        "sh /Users/o/lem/hooks/run corrections",
        "/opt/homebrew/opt/lem/libexec/bin/lem-hook corrections",
        "LEM_JEV=/x/jev lem-hook corrections",
    ]
    path = settings(stage, "a.json", *said)
    assert [hook["command"] for hook in hook_entries(path)] == said


def test_another_selector_or_an_old_line_is_not_the_correction_hook(
    stage: Stage,
) -> None:
    path = settings(
        stage,
        "a.json",
        PLUGIN_LINE.format("serve"),
        "lem-hook session-start",
        "lem corrections list",
        "lem-hook correctionsx",
        'python3 "${CLAUDE_PLUGIN_ROOT}/src/lem/python.py" corrections hook',
        "python3 /elsewhere/corrections.py hook",
    )
    assert hook_entries(path) == []


def test_a_settings_file_that_also_holds_the_hook_beside_lems_plugin_is_named(
    stage: Stage,
) -> None:
    repo = stage.repository()
    stage.plugins(
        {"plugins": {"lem@lem": [{"scope": "project", "projectPath": str(repo)}]}}
    )
    assert correction_hook_rows(stage.look(repo)) == ()
    shared = settings(stage, "repo/.claude/settings.json", "lem-hook corrections")
    (row,) = correction_hook_rows(stage.look(repo))
    assert (row.need, row.found) == ("project", False)
    assert row.detail == (
        f"registered 2 times for this repository: {shared}, the plugin lem@lem"
    )
    said = row.without_it or ""
    assert said.startswith("Claude Code starts the hook once for each place")
    assert "The plugin brings the hook, so remove each other place" in said
    assert '{"type": "command", "command": "lem-hook corrections"}' in said
    assert "by hand, and commit that" in said
    assert "uninstall" not in said
    stage.write(
        "repo/.claude/settings.local.json",
        json.dumps({"enabledPlugins": {"lem@lem": False}}),
    )
    assert correction_hook_rows(stage.look(repo)) == ()


def test_with_no_plugin_the_hook_in_two_settings_files_is_named_with_the_plugin(
    stage: Stage,
) -> None:
    repo = stage.repository()
    user = settings(
        stage, "home/.claude/settings.json", PLUGIN_LINE.format("corrections")
    )
    local = settings(stage, "repo/.claude/settings.local.json", "lem-hook corrections")
    (row,) = correction_hook_rows(stage.look(repo))
    assert row.detail == f"registered 2 times for this repository: {user}, {local}"
    said = row.without_it or ""
    assert (
        "The hook comes with Lem's plugin: install it, and remove each of these" in said
    )
    assert f"{user}: delete the entry" in said
    assert f"{local}: delete the entry" in said
    assert "commit" not in said
