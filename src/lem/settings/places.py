"""Where Lem's settings files are, and where each table that the fast track reads is valid
(`state.TABLE_PLACES` on `main`).

`[branch]` and `[checks]` guard the base, so only the team's file in git holds them: one
developer's local file cannot lift what guards the project. The step `settings` adds the home
file, the machine's file and the other tables.
"""

from pathlib import Path

LEM = Path(".lem")
TEAM = LEM / "settings.toml"
LOCAL = LEM / "settings.local.toml"
# The tables valid in the team's file only.
TEAM_ONLY = ("branch", "checks")
