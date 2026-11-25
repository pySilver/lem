"""Where an agent finds a skill by its name: in a skills folder of this repository or of the
home, installed as a plugin of Claude Code of that name, carried by an installed plugin of
another name (`tracking:backlog` carries `backlog`), or, where Claude Code's list does not read,
in its folder of plugins with the skill in it.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor import plugins
from lem.cli.doctor.checkouts import roots
from lem.cli.doctor.row import Row

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look
    from lem.cli.doctor.skill_words import Skill

SKILLS = "skills"
# Where each agent keeps a user's skills.
HOMES = (
    Path(".claude") / SKILLS,
    Path(".agents") / SKILLS,
    Path(".codex") / SKILLS,
    Path(".config") / "opencode" / SKILLS,
)
SKILL = "SKILL.md"
CACHE = Path(".claude") / "plugins" / "cache"


def in_folders(name: str, bases: tuple[Path, ...]) -> str | None:
    """The first skills folder of `bases` that holds the skill `name`."""
    for base in bases:
        for home in HOMES:
            place = base / home / name
            if (place / SKILL).is_file():
                return str(place)
    return None


def carries(install: plugins.Install, name: str) -> bool:
    """Whether the folder of `install` holds the skill `name`."""
    if not install.folder:
        return False
    return (Path(install.folder) / SKILLS / name / SKILL).is_file()


def in_plugins(name: str, look: Look, found: tuple[Path, ...]) -> str | None:
    """`the plugin KEY` when an install this repository gets is the plugin `name`, else
    `the skill PLUGIN:NAME` when one carries the skill in its folder."""
    reached = plugins.reaching(plugins.installs(look.home), found)
    same = [one.key for one in reached if one.name == name]
    if same:
        return f"the plugin {same[0]}"
    carrying = [one.name for one in reached if carries(one, name)]
    return f"the skill {carrying[0]}:{name}" if carrying else None


def in_cache(name: str, home: Path) -> str | None:
    """The folder of the skill `name` in Claude Code's folder of plugins, under a plugin of
    that name."""
    cache = home / CACHE
    if not cache.is_dir():
        return None
    pattern = f"*/{name}/*/**/{SKILLS}/{name}/{SKILL}"
    found = sorted(cache.glob(pattern))
    return str(found[0].parent) if found else None


def skill_row(look: Look, skill: Skill) -> Row:
    """The row of `skill`: where an agent finds it, if anywhere."""
    here = roots(look.folder)
    found = (
        in_folders(skill.name, (*here, look.home))
        or in_plugins(skill.name, look, here)
        or in_cache(skill.name, look.home)
    )
    return Row(
        name=f"{skill.name} skill",
        need=skill.need,
        found=found is not None,
        detail=found,
        used_for=skill.used_for,
        without_it=skill.without_it,
        guide=skill.guide,
    )
