"""The plugin's folder and the folders under it that a module of Lem reads, from the one
place this package sits in it, `src/lem`: the board's assets, the templates, prompts and
stages of the skill `lem`, and the data of the skills Lem ships."""

from pathlib import Path

# this package, src/lem
PACKAGE = Path(__file__).resolve().parent
# the plugin's folder: what `lem version` calls its root
ROOT = PACKAGE.parents[1]
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
