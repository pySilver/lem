"""The words of the permission mode's row: the modes in which Claude Code asks nobody before a
command, what a builder in the background meets in each other mode, and the one line to change.
"""

from types import MappingProxyType

# `bypassPermissions` asks nothing, and `auto` has a model classifier decide.
SILENT = ("bypassPermissions", "auto")
WAITS = "so the task waits; at night nobody answers"
MEETS = MappingProxyType(
    {
        "default": (
            "each command the allow list does not hold asks for permission, and the question "
            f"comes up in the task's session, {WAITS}"
        ),
        "acceptEdits": (
            "an edit goes through, and each other command the allow list does not hold asks "
            f"for permission in the task's session, {WAITS}"
        ),
        "plan": "a builder can read and cannot edit or commit, so no task builds",
        "dontAsk": (
            "each command the allow list does not hold is refused with no question, so a "
            "builder stops at the first one"
        ),
    }
)
UNKNOWN = "a mode this check does not know; a builder may ask for permission in the task's session"
# A repository's settings cannot set auto, so the line names the user's own file.
TO_AUTO = (
    'Lem assumes auto mode: put "defaultMode": "auto" under "permissions" in your own '
    "~/.claude/settings.json, and start a new session"
)
