"""The reviewer's guard, `harness/claude-code/reviewer-guard.json`: the settings a plan talk's
reviewer in Claude Code starts with (`harness/claude-code/second-opinion.md`)."""

import json

from lem.kernel import paths

GUARD = "skills/lem/harness/claude-code/reviewer-guard.json"


def test_the_reviewer_edits_no_file_and_writes_only_under_tmp_in_its_sandbox() -> None:
    guard = json.loads((paths.root() / GUARD).read_text(encoding="utf-8"))
    denied = set(guard["permissions"]["deny"])
    assert {"Edit", "Write", "NotebookEdit"} <= denied
    sandbox = guard["sandbox"]
    assert (sandbox["enabled"], sandbox["failIfUnavailable"]) == (True, True)
    assert sandbox["allowUnsandboxedCommands"] is False
    assert sandbox["filesystem"] == {"denyWrite": ["~"], "allowWrite": ["/private/tmp"]}
    say = "mailbox-chat.py say --file *"
    assert guard["permissions"]["allow"] == [f"Bash({say})"]
    assert sandbox["excludedCommands"] == [say]
