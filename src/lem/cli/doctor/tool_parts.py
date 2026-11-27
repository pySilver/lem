"""The parts of `lem doctor` that look for a program, an agent or a skill, in the order the
owner reads them."""

from functools import partial
from typing import TYPE_CHECKING

from lem.cli.doctor import agents, skill_words, tool_words
from lem.cli.doctor.jev_row import jev_row
from lem.cli.doctor.mailbox import mailbox_row
from lem.cli.doctor.row import OPTIONAL, RECOMMENDED, REQUIRED
from lem.cli.doctor.skills import skill_row
from lem.cli.doctor.tools import cronn_row, gh_row, python_row, tool_row

if TYPE_CHECKING:
    from lem.cli.doctor.row import Part


def tooled(tool: tool_words.Tool) -> Part:
    """The part of one program on PATH."""
    return (tool.name, tool.need, partial(tool_row, tool=tool))


def skilled(skill: skill_words.Skill) -> Part:
    """The part of one skill."""
    return (f"{skill.name} skill", skill.need, partial(skill_row, skill=skill))


TOOL_PARTS: tuple[Part, ...] = (
    ("python3", REQUIRED, python_row),
    tooled(tool_words.GIT),
    tooled(tool_words.REVMUX),
    skilled(skill_words.REVMUX),
    ("agterm", REQUIRED, agents.agterm_rows),
    ("gh", REQUIRED, gh_row),
    skilled(skill_words.WEBREV),
    skilled(skill_words.AGDOC),
    skilled(skill_words.BACKLOG),
    tooled(tool_words.PLANNOTATOR_TUI),
    tooled(tool_words.PLANNOTATOR),
    ("Jev key", OPTIONAL, jev_row),
    ("codex", RECOMMENDED, agents.codex_rows),
    ("claude", REQUIRED, agents.claude_rows),
    (tool_words.MAILBOX.name, tool_words.MAILBOX.need, mailbox_row),
    skilled(skill_words.MAILBOX),
    ("cronn", REQUIRED, cronn_row),
)
