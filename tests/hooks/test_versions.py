"""The plugin and the app as two versions, and another `lem` first on the PATH: `session-start`
says the one line for each, every other selector does nothing and says nothing, and the other
`lem` is compared by its identity and never run."""

import json
import shutil
from typing import TYPE_CHECKING

from hooks.claude_code import (
    GUI_PATH,
    HOOK,
    ROOT,
    SELECTORS,
    hooked,
    started,
    workspace,
)
from lem.store import sessions

if TYPE_CHECKING:
    from pathlib import Path


def plugin_of(folder: Path, manifest: str | None) -> Path:
    """A plugin's folder with its own launcher, and the manifest `manifest` when one is
    given."""
    (folder / "hooks").mkdir(parents=True)
    shutil.copy2(ROOT / "hooks" / "run", folder / "hooks" / "run")
    if manifest is not None:
        (folder / ".claude-plugin").mkdir()
        (folder / ".claude-plugin" / "plugin.json").write_text(manifest)
    return folder


def test_on_two_versions_only_session_start_says_the_line(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    plugin = plugin_of(tmp_path / "plugin", '{"version": "0.0.1"}')
    for selector in SELECTORS:
        ran = hooked(
            selector, started(tmp_path / "repo"), CLAUDE_PLUGIN_ROOT=str(plugin)
        )
        if selector != "session-start":
            assert (ran.returncode, ran.stdout) == (0, b""), selector
            continue
        said = json.loads(ran.stdout)
        assert said["systemMessage"].startswith(
            f"lem: Lem's plugin 0.0.1 ({plugin}) is behind Lem's app"
        )
    assert not (folder / sessions.SESSIONS).exists()


def test_with_one_version_the_handlers_run(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    plugin = plugin_of(
        tmp_path / "plugin", (ROOT / ".claude-plugin" / "plugin.json").read_text()
    )
    ran = hooked(
        "session-start", started(tmp_path / "repo"), CLAUDE_PLUGIN_ROOT=str(plugin)
    )
    assert (ran.returncode, ran.stdout) == (0, b"")
    assert len(sessions.read(folder)) == 1


def test_a_plugin_whose_manifest_does_not_read_is_named_with_its_fix(
    tmp_path: Path,
) -> None:
    workspace(tmp_path / "repo")
    plugin = plugin_of(tmp_path / "plugin", None)
    ran = hooked(
        "session-start", started(tmp_path / "repo"), CLAUDE_PLUGIN_ROOT=str(plugin)
    )
    said = json.loads(ran.stdout)["systemMessage"]
    assert said.startswith(
        "lem: Lem cannot tell whether Lem's plugin and Lem's app are two versions: the "
        f"plugin's manifest is unreadable ({plugin}/.claude-plugin/plugin.json"
    )
    assert said.endswith(
        "the owner installs Lem's plugin again and starts the session again"
    )


def test_another_lem_first_on_the_path_is_named_and_never_run(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    other = tmp_path / "old" / "lem"
    other.parent.mkdir()
    ran_mark = tmp_path / "ran"
    other.write_text(f"#!/bin/sh\ntouch {ran_mark}\n")
    other.chmod(0o755)
    ran = hooked(
        "session-start",
        started(tmp_path / "repo"),
        PATH=f"{other.parent}:{HOOK.parent}:{GUI_PATH}",
    )
    said = json.loads(ran.stdout)
    assert said["systemMessage"] == (
        f"lem: {other} comes first on PATH, and it is not Lem's command "
        f"{HOOK.parent / 'lem'}; the owner puts {HOOK.parent} before {other.parent} in "
        "his PATH"
    )
    assert not ran_mark.exists()
    # the task's session is still put on record beside the line
    assert len(sessions.read(folder)) == 1


def test_the_apps_own_lem_first_on_the_path_says_nothing(tmp_path: Path) -> None:
    workspace(tmp_path / "repo")
    ran = hooked(
        "session-start", started(tmp_path / "repo"), PATH=f"{HOOK.parent}:{GUI_PATH}"
    )
    assert (ran.returncode, ran.stdout) == (0, b"")
