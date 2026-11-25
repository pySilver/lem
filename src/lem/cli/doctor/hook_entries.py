"""The entries of the correction hook in Claude Code's settings files, and how each comes out.

The hook in any form added by hand: the plugin's line, whose core is
`"$CLAUDE_PLUGIN_ROOT/hooks/run" corrections`, or the app's entry itself, `lem-hook corrections`.
No command of Lem's writes a settings file, so each entry comes out by hand; one in the
repository's shared settings is a change to commit too.
"""

import json
import re
from typing import TYPE_CHECKING

from lem.cli.doctor.checkouts import files_of, table_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.doctor.look import Look

FORM = re.compile(r"(?:hooks/run|lem-hook)['\"]?\s+corrections\b")

type Hook = dict[str, object]
# A place that registers the hook, and how it comes out of there.
type Removal = tuple[str, str]


def hook_entries(path: Path) -> list[Hook]:
    """Each entry of the correction hook among the `UserPromptSubmit` hooks of a settings
    file."""
    hooks = table_of(path).get("hooks")
    groups = hooks.get("UserPromptSubmit") if isinstance(hooks, dict) else None
    found: list[Hook] = []
    for group in groups if isinstance(groups, list) else []:
        inner = group.get("hooks") if isinstance(group, dict) else None
        found += [one for one in inner or [] if isinstance(one, dict)]
    return [hook for hook in found if is_correction(hook)]


def is_correction(hook: Hook) -> bool:
    """Whether one hook's command starts the correction hook."""
    command = str(hook.get("command", ""))
    return FORM.search(command) is not None


def removal(hook: Hook, path: Path, *, shared: bool) -> str:
    """How one entry comes out of the file at `path`: the owner deletes that object from its
    `UserPromptSubmit` hooks, and nothing else; in the repository's shared settings he commits
    that too."""
    entry = json.dumps(hook, ensure_ascii=False)
    commit = ", and commit that" if shared else ""
    return f"delete the entry {entry} from the UserPromptSubmit hooks of {path} by hand{commit}"


def removals(look: Look, root: Path | None) -> list[Removal]:
    """How each entry of the hook in a settings file for the repository `root` (None: outside
    one) comes out: the user's file first, then the repository's local and shared ones."""
    found = files_of(look.home, root)
    shared = found[1] if root else None
    ordered = (found[-1], *found[:-1])
    return [
        (str(path), removal(hook, path, shared=path == shared))
        for path in ordered
        for hook in hook_entries(path)
    ]
