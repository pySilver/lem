"""Where the files that Lem reads are: the plugin's files (the board's assets, the
templates, prompts and stages of the skill `lem`, the data of the skills Lem ships, the
agents, the hooks and the manifest), from the one place this package sits.

An installed app holds them in its own package, under `lem/data`, at the names they have
in Lem's repository (pyproject.toml), and reads them there, never from the plugin that
Claude Code loaded: the texts an agent reads are the texts of the `lem` it runs. A
checkout (an editable install, or `src` on `sys.path` as the unit level has it) has no
such folder, and its root is the checkout itself, two folders above this package."""

from pathlib import Path

# this package: src/lem of a checkout, or lem in an installed app's site-packages
PACKAGE = Path(__file__).resolve().parent
# the plugin's files in an installed app
DATA = PACKAGE / "data"
# the checkout this package is part of, when it is one
CHECKOUT = PACKAGE.parents[1]


def root() -> Path:
    """DATA in an installed app; else CHECKOUT, when it holds the skill `lem`; else one
    error that names both places."""
    if DATA.is_dir():
        return DATA
    if (CHECKOUT / "skills" / "lem" / "SKILL.md").is_file():
        return CHECKOUT
    raise SystemExit(
        f"lem: Lem's files are neither in {DATA}, as in an installed Lem, nor in "
        f"{CHECKOUT}, as in a checkout of Lem's repository; the owner installs Lem "
        "again"
    )


# the folder of the plugin's files: what `lem version` calls its root
ROOT = root()
# the one entry, which runs the module a name stands for: `python -B MAIN NAME ARGS...`
MAIN = PACKAGE / "__main__.py"
# the command `lem`, which the plugin puts on the Bash tool's PATH
LEM = ROOT / "bin" / "lem"
SKILLS = ROOT / "skills"
# the skill `lem`: its stages, prompts and templates, and the board's assets
SKILL = SKILLS / "lem"
ASSETS = SKILL / "assets"
TEMPLATES = SKILL / "templates"
PROMPTS = SKILL / "prompts"
STAGES = SKILL / "stages"
# the skill `lem-ask`: its runtime, templates, demos and defaults
ASK = SKILLS / "lem-ask"
# the persona panel's built-in cast
CAST = SKILLS / "lem-panel" / "cast"
