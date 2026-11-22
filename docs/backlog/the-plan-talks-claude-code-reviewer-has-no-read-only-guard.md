---
worth: later
where: skills/lem/harness/claude-code/second-opinion.md
added: 2026-11-22
---
# The plan talk's Claude Code reviewer has no read-only guard

The harness calls the `second-opinion` capability read-only (`harness/README.md`). The Codex
reviewer's launch line in `second-opinion.md`, step 2, now carries a permission profile that reads
everything and writes only its mailbox reply file. The Claude Code line,
`claude --model "MODEL" --effort "EFFORT" --append-system-prompt "$(cat "PATH/prompts/reviewer.md")" "You are the reviewer. Wait for the first message."`,
carries no such guard: the reviewer starts with the permissions of the developer's own Claude Code
settings in the main checkout, and only its brief keeps it from editing the plan there. A run, from
reading (not run): a careful plan's talk with `seats.reviewer = "claude/opus:high"`; the reviewer
finds a wrong path in the plan and fixes the file itself, in the main checkout where every task's
worktree lives. The task `plan-reviewer-read-only` left this seat out (its plan's decision 5),
because Claude Code's guard needs its own probe: which flag or settings line refuses an edit and
still lets the reviewer write the file that `mailbox-chat.py say --file` sends, tried in one real
talk in agterm.
