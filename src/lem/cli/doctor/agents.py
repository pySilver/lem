"""The rows of the agents and the terminal: agterm with its skill and the task picker, Claude
Code with Lem's builder, and Codex with the persona definition a panel needs there.

A row that only a machine with its tool needs comes only with that tool: no agterm skill without
agterm, no builder without Claude Code, no persona definition without Codex.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.cli.doctor import plugins, tool_words
from lem.cli.doctor.checkouts import roots
from lem.cli.doctor.picker import picker_row
from lem.cli.doctor.row import OPTIONAL, REQUIRED, Row
from lem.cli.doctor.skills import HOMES, SKILL
from lem.cli.doctor.tools import tool_row

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

# A project's own builder, which Claude Code takes before the plugin's.
BUILDER = Path(".claude") / "agents" / "lem-builder.md"
PLUGIN_BUILDER = Path("agents") / "lem-builder.md"
PERSONA = Path(".codex") / "agents" / "persona.toml"
BUILDER_FIX = (
    "Claude Code has no agent of that name and Lem starts no builder; install Lem's plugin "
    "in this repository: `claude plugin marketplace add pySilver/lem --scope project`, then "
    "`claude plugin install lem@lem --scope project`. A session that loaded the plugin by a "
    "flag (`claude --plugin-dir DIR`) has the builder as lem:lem-builder all the same: this "
    "check finds such a plugin only through CLAUDE_PLUGIN_ROOT, and this command did not "
    "get it"
)


def agterm_rows(look: Look) -> tuple[Row, ...]:
    """agterm, whether this is one of its sessions, its skill and the task picker."""
    session = bool(look.environ.get("AGTERM_SESSION_ID"))
    row = msgspec.structs.replace(tool_row(look, tool_words.AGTERM), in_session=session)
    if not row.found:
        return (row,)
    homes = [look.home / home / "agterm" for home in HOMES]
    held = [str(home) for home in homes if (home / SKILL).is_file()]
    skill = Row(
        name="agterm skill",
        need=REQUIRED,
        found=bool(held),
        detail=", ".join(held) or None,
        used_for="how an agent drives agterm: overlays, sessions, panes",
        without_it=(
            "an agent has agterm and does not know its commands; install it from agterm's "
            "Help menu"
        ),
    )
    return (row, skill, picker_row(look))


def own_builder(found: tuple[Path, ...]) -> str | None:
    """A project's own builder: this checkout's, or the main checkout's when git does not
    track it."""
    for root in found:
        if (root / BUILDER).is_file():
            return str(root / BUILDER)
    return None


def builder_at(look: Look, found: tuple[Path, ...]) -> str | None:
    """Where Claude Code finds Lem's builder: a project's own, the plugin installed for the
    user or this repository, or a plugin a flag loaded for this session, which is in no list
    and names its folder in CLAUDE_PLUGIN_ROOT."""
    own = own_builder(found)
    if own is not None:
        return own
    reached = plugins.reaching(plugins.installs(look.home), found)
    lems = [install.key for install in reached if install.name == "lem"]
    if lems:
        return f"lem:lem-builder, from the plugin {lems[0]}"
    session = look.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if session and (Path(session) / PLUGIN_BUILDER).is_file():
        return f"lem:lem-builder, from the plugin loaded for this session ({session})"
    return None


def claude_rows(look: Look) -> tuple[Row, ...]:
    """Claude Code, and Lem's builder in it."""
    row = tool_row(look, tool_words.CLAUDE)
    if not row.found:
        return (row,)
    found = builder_at(look, roots(look.folder))
    builder = Row(
        name="lem-builder agent",
        need=REQUIRED,
        found=found is not None,
        detail=found,
        used_for="the builder Lem starts for each task of a plan in Claude Code",
        without_it=BUILDER_FIX,
    )
    return (row, builder)


def codex_rows(look: Look) -> tuple[Row, ...]:
    """Codex, and the persona definition a panel's second half needs in it."""
    row = tool_row(look, tool_words.CODEX)
    if not row.found:
        return (row,)
    path = look.home / PERSONA
    held = path.is_file()
    persona = Row(
        name="codex persona agent",
        need=OPTIONAL,
        found=held,
        detail=str(path) if held else None,
        used_for=(
            "the second half of a persona panel: each persona answered by the other model "
            "family"
        ),
        without_it=(
            "a panel has the answers of one model family, so a split between two is not "
            f"seen; the lem-panel skill says what {path} holds"
        ),
    )
    return (row, persona)
