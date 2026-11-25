"""The row of the plugin's hooks: the plugin's folder has `hooks/run` and a hooks file whose every
line starts a selector `lem-hook` knows, and the app's package has `lem-hook` whole.

`lem-hook` imports the standard library only (the design's part 5): its module, each module a
selector runs and each module of `lem.hooks` that one of them imports at its top, read and
parsed; an import at the top of any of them of a part of Lem outside `lem.hooks` is a hook that
pays for that part at each start. An import inside a function runs on that function's path
only. A hook that cannot start ends with nothing printed, so this row is where the owner learns
it.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.cli.doctor.hook_files import Broken, selectors_of
from lem.cli.doctor.hook_imports import HOOKS, problem_of, shown
from lem.cli.doctor.row import REQUIRED, Row
from lem.hooks import main

if TYPE_CHECKING:
    from pathlib import Path

ENTRY = f"{HOOKS}.main"
INSIDE = f"{HOOKS}."
type Names = list[str]
# Each selector of `lem-hook`, and the module that answers it.
MODULES = MappingProxyType(dict(main.SELECTORS))


def checked(package: Path, module: str) -> tuple[Names, Names]:
    """What is wrong with one module of the hooks, and the modules of `lem.hooks` it imports
    at its top."""
    problem, imported = problem_of(package, module)
    inside = [name for name in imported if name.startswith(INSIDE)]
    outside = ", ".join(name for name in imported if name not in inside)
    broken = [problem] if problem else []
    if outside:
        broken.append(
            f"{shown(module)} imports {outside} at its top, which every hook would pay at "
            "its start"
        )
    return broken, inside


def modules_of(package: Path, selectors: tuple[str, ...]) -> tuple[Names, Names]:
    """Each module of `lem.hooks` that `lem-hook` reaches for `selectors`, in order, and what
    is wrong."""
    reached = [ENTRY, *(MODULES[one] for one in selectors)]
    broken: Names = []
    for module in reached:
        wrong, inside = checked(package, module)
        broken += wrong
        reached += [name for name in inside if name not in reached]
    return reached, broken


def whole_said(selectors: tuple[str, ...], hooks_file: str, reached: Names) -> str:
    """The detail of whole hooks: the selectors, the hooks file and the modules."""
    started = ", ".join(selectors)
    modules = ", ".join(map(shown, reached))
    return f"{started} from {hooks_file}; {modules}"


def plugin_part(plugin: Path) -> tuple[tuple[str, ...], list[str], str]:
    """The selectors the plugin's hooks file starts, what is wrong with its files, and the
    hooks file's path."""
    broken = [] if (plugin / "hooks" / "run").is_file() else ["hooks/run is missing"]
    hooks_file = plugin / "hooks" / "hooks.json"
    try:
        selectors = selectors_of(hooks_file, tuple(MODULES))
    except Broken as error:
        return (), [*broken, str(error)], str(hooks_file)
    return selectors, broken, str(hooks_file)


def hook_modules_row(plugin: Path, package: Path) -> Row:
    """The row of the hooks of the plugin at `plugin` and the app's `package`."""
    selectors, broken, hooks_file = plugin_part(plugin)
    reached, wrong = modules_of(package, selectors)
    broken += wrong
    return Row(
        name="hook modules",
        need=REQUIRED,
        found=not broken,
        detail="; ".join(broken) or whole_said(selectors, hooks_file, reached),
        used_for=(
            "the hooks of the plugin: the correction hook, the start of the board server, the "
            "records of a task's session and lem-ask's status at a stop"
        ),
        without_it=(
            "a hook that cannot start does nothing and says nothing; when a file of the "
            "plugin is named, the owner installs the plugin again (`claude plugin update "
            "lem@lem`), and when a module is named, Lem's app again"
        ),
    )
