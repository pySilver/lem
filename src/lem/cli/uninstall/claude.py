"""Claude Code's installs of the plugin `lem@lem` and its declarations of the marketplace `lem`,
by scope, and the `claude plugin` calls that remove them.

The installs are Claude Code's list of installed plugins, which `claude_plugin` reads; a
declaration of the marketplace is `extraKnownMarketplaces.lem` of the scope's settings file, or
for the user also Claude Code's list of known marketplaces. A call for a project or a local scope
runs in that project's folder, and `marketplace remove` takes `--scope` (the help of Claude Code
2.1.332, read 2026-11-27). The plugin goes before the marketplace, and the marketplace only when
every install went.
"""

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.claude_plugin import PLUGIN, Installs, claude_home
from lem.cli.uninstall.rules import table
from lem.kernel import folders
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.cli.uninstall.report import Report

MARKET = "lem"
USER = "user"
PROJECT = "project"
LOCAL = "local"
PROJECTS = (PROJECT, LOCAL)
# How long one `claude plugin` call may take, in seconds. A guess.
WAIT = 120


class Scope(msgspec.Struct, frozen=True):
    """A scope of Claude Code and the folder its call runs in: the home for the user."""

    name: str
    folder: Path

    @property
    def said(self) -> str:
        """The scope in the owner's words."""
        return f"the {self.name} scope of {self.folder}"

    @property
    def settings(self) -> Path:
        """The settings file of a project's scope."""
        named = "settings.local.json" if self.name == LOCAL else "settings.json"
        return self.folder / ".claude" / named


type Scopes = tuple[Scope, ...]


def installs(home: Path) -> Scopes:
    """The scopes that install `lem@lem`, from Claude Code's list."""
    listed = claude_home(os.environ) / "plugins" / "installed_plugins.json"
    folders.inside_test_root(listed)
    try:
        found = msgspec.json.decode(listed.read_bytes(), type=Installs)
    except FileNotFoundError:
        return ()
    scopes = (
        Scope(one.scope, Path(one.project) if one.project else home)
        for one in found.plugins.get(PLUGIN, ())
        if one.scope
    )
    return tuple(dict.fromkeys(scopes))


def markets(home: Path, roots: tuple[Path, ...], plugins: Scopes) -> Scopes:
    """The scopes that declare the marketplace `lem`: the user's, and those of each
    repository of `roots` and each project of an install."""
    projects = (one.folder for one in plugins if one.name in PROJECTS)
    scopes = (
        Scope(name, root)
        for root in dict.fromkeys((*roots, *projects))
        for name in PROJECTS
    )
    found = tuple(scope for scope in scopes if declares(scope.settings))
    return (Scope(USER, home), *found) if user_declares() else found


def user_declares() -> bool:
    """Whether the user's settings or Claude Code's list of known marketplaces has `lem`."""
    claude = claude_home(os.environ)
    known = table(claude / "plugins" / "known_marketplaces.json")
    return MARKET in known or declares(claude / "settings.json")


def declares(path: Path) -> bool:
    """Whether a settings file declares the marketplace `lem`."""
    extra = table(path).get("extraKnownMarketplaces")
    return isinstance(extra, dict) and MARKET in extra


def removed(words: tuple[str, ...], scope: Scope, report: Report) -> None:
    """Run `claude WORDS --scope S` in the scope's folder; a project's tracked settings file
    changes, which the owner commits."""
    called = (*words, "--scope", scope.name)
    line = shlex.join(("claude", *called))
    with report.step(line, f"the owner runs {line} in {scope.folder}"):
        ran_in(scope.folder, called)
        name = words[-1]
        report.gone(f"{name} from {scope.said}")
        if scope.name == PROJECT:
            report.owner(f"commit the change of {scope.settings}")


def ran_in(folder: Path, words: tuple[str, ...]) -> None:
    """One `claude` call; refused when there is no `claude` or the call fails."""
    folders.inside_test_root(folder)
    program = shutil.which("claude")
    line = " ".join(("claude", *words))
    if program is None:
        raise Refusal(
            "uninstall-claude",
            f"there is no claude on the PATH to run {line}",
            "the owner puts Claude Code's claude on the PATH",
        )
    try:
        ran = subprocess.run(
            (program, *words),
            cwd=folder,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=WAIT,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise Refusal(
            "uninstall-claude",
            f"{line} did not end in {WAIT} s in {folder}",
            f"the owner runs {line} in {folder}",
        ) from error
    if ran.returncode:
        said = (ran.stderr or ran.stdout).decode(errors="replace").strip()
        raise Refusal(
            "uninstall-claude",
            f"{line} failed in {folder}: {said}",
            f"the owner reads what {line} says in {folder}",
        )
