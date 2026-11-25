"""The rows of Lem's two halves on this machine: the app's version against the plugin's, and the
`lem` first on the PATH against the app's own command.

`lem` refuses every command but `help`, `version` and `doctor` when the plugin a session loaded
(`LEM_PLUGIN_ROOT`) and the app are two versions, so this row says both, with the line that names
the half behind (`lem.hooks.versions`). Outside such a session the plugin is the one Claude Code
has for this repository. A session's commands run the first `lem` on its PATH, so another `lem`
there (an old install, a checkout's) runs another Lem (`lem.hooks.other`).
"""

from typing import TYPE_CHECKING

from lem.cli.doctor.checkouts import main_checkout
from lem.cli.doctor.hook_bin import plugin_folder
from lem.cli.doctor.row import REQUIRED, Row
from lem.hooks import other, versions
from lem.kernel import paths

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look


def plugin_named(look: Look) -> tuple[str, str]:
    """The plugin's folder to compare, and where it comes from."""
    for name in ("LEM_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
        named = look.environ.get(name, "").strip()
        if named:
            return named, name
    folder = plugin_folder(look, main_checkout(look.folder))
    return str(folder), "the plugin Claude Code has for this repository"


def versions_row(look: Look) -> Row:
    """The app's version and the plugin's, and the line that names the half behind."""
    app = str(paths.root())
    plugin, source = plugin_named(look)
    behind = versions.behind(plugin, app)
    return Row(
        name="Lem's versions",
        need=REQUIRED,
        found=behind is None,
        detail=f"Lem's app {versions.version_of(app)} ({app}); Lem's plugin "
        f"{versions.version_of(plugin)} ({plugin}, {source})",
        used_for=(
            "every command of Lem but help, version and doctor: they refuse while the plugin "
            "and the app are two versions"
        ),
        without_it=behind,
    )


def lem_row(look: Look) -> Row:
    """Whether the first `lem` on the PATH is the app's own command."""
    own = str(look.executable.parent / "lem")
    first = look.which("lem")
    line = other.other_lem(look.environ.get("PATH", ""), own)
    detail = f"{first}, Lem's command beside its Python"
    if first is None:
        detail = "no lem on PATH"
    elif line is not None:
        detail = line.removeprefix("lem: ")
    return Row(
        name="lem on PATH",
        need=REQUIRED,
        found=first is not None and line is None,
        detail=detail,
        used_for=(
            "every `lem` line of a stage, a brief and a hook's words runs the first lem on "
            "the session's PATH"
        ),
        without_it=(
            "a session's `lem` lines reach no Lem, or another Lem than this one; the owner "
            f"puts the folder of {own}, or a folder with a link to it, first on his PATH"
        ),
    )
