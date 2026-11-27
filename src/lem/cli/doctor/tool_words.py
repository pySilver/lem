"""The words of each row of a program on PATH: its name, its need, what Lem uses it for, what
happens without it, the program the check looks for, the arguments that print its version, and
the guide to install it by.

The needs are the owner's: agterm, the mailbox chat and revmux stay required; cronn is required,
and Codex is highly recommended (2026-11-18). A recommended tool is one Lem does not bring and a
developer is better off with: its row has its guide, and Lem installs it only on his yes.
"""

import msgspec

from lem.cli.doctor.row import OPTIONAL, RECOMMENDED, REQUIRED, Need

VERSION = ("--version",)
# The guides of the recipes of the agterm cookbook that Lem needs or recommends, and never
# copies in.
COOKBOOK = "https://github.com/umputun/agterm/tree/master/cookbook/"


class Tool(msgspec.Struct, frozen=True, kw_only=True):
    """A program on PATH, and the words of its row."""

    name: str
    need: Need
    used_for: str
    without_it: str
    program: str
    probe: tuple[str, ...] = VERSION
    guide: str | None = None


GIT = Tool(
    name="git",
    need=REQUIRED,
    used_for="worktrees, branches and the task state directory",
    without_it="nothing runs",
    program="git",
)
REVMUX = Tool(
    name="revmux",
    need=REQUIRED,
    used_for=(
        "the review rounds before the pull request, with the project's profiles and lenses"
    ),
    without_it=(
        "only one read can review a change: a careful or large request, or one after a "
        "must-fix, needs a round at the least, and it is not proposed"
    ),
    program="revmux",
)
AGTERM = Tool(
    name="agterm",
    need=REQUIRED,
    used_for=(
        "a session for each task, the reviewer's pane, pages for the owner, and the "
        "companion of a plan talk"
    ),
    without_it="`/lem` stops at once: Lem runs inside agterm only",
    program="agtermctl",
)
# Required: a task lands only through a GitHub pull request, which `gh` opens and merges (the
# owner's ruling "GitHub pull requests are the one way to land").
GH = Tool(
    name="gh",
    need=REQUIRED,
    used_for=(
        "the pull request of each task, the board's look at the open ones, and the issues "
        "of a GitHub tracker"
    ),
    without_it=(
        "no task lands: `lem land propose` and the board's look at GitHub stop and say so; "
        "install the GitHub CLI and run `gh auth login`"
    ),
    program="gh",
)
PLANNOTATOR_TUI = Tool(
    name="plannotator-tui",
    need=RECOMMENDED,
    used_for=(
        "the owner marks up what a pane printed, or an agent's newest reply, from two "
        "agterm chords"
    ),
    without_it="no stage needs it",
    program="plannotator-tui",
    guide=f"{COOKBOOK}annotate-in-plannotator-tui",
)
# The Inbox of what waits for the owner while he is away: without it nothing is sent there,
# and no step of a task fails.
PLANNOTATOR = Tool(
    name="plannotator",
    need=OPTIONAL,
    used_for=(
        "the Plannotator Inbox carries what waits for the owner while he is away, to his "
        "phone too, and brings his answer back into the task's session"
    ),
    without_it=(
        "nothing goes to the Plannotator Inbox. While the owner is away, items wait in "
        "the task's session and on the board. The task page on the phone says why it "
        "has no Inbox link"
    ),
    program="plannotator",
    guide="https://plannotator.ai/inbox/",
)
CLAUDE = Tool(
    name="claude",
    need=REQUIRED,
    used_for="the agent that runs `/lem`, and a reviewer of the same family",
    without_it=(
        "nothing runs `/lem`: Claude Code is the one agent Lem has a harness file for"
    ),
    program="claude",
)
CODEX = Tool(
    name="codex",
    need=RECOMMENDED,
    used_for=(
        "a reviewer of another model family, the second expert of the ladder, and half of "
        "each persona panel"
    ),
    without_it=(
        "highly recommended, since without it Claude reviews the work of Claude: the "
        "reviewer is a second Claude; an expert whose seat names codex (by default the "
        "second of seats.experts, the newest Astra of OpenAI) does not answer, so the one "
        "expert that can answer, the newest Fable of Anthropic by default, answers alone "
        "and its pick settles a decision the experts take, and the pull "
        "request is not green for such a decision; a persona panel has the answers of one "
        "model family, so a split between two is not seen"
    ),
    program="codex",
    guide="https://github.com/openai/codex",
)
MAILBOX = Tool(
    name="mailbox-chat",
    need=REQUIRED,
    used_for=(
        "the wake-up of a task's idle session by the board's server (a merge, a conflict, "
        "its turn in the queue) rests on its waiter, the owner's hook; and the messages "
        "between the defender and the reviewer of a plan talk"
    ),
    without_it=(
        "an idle task session never hears a merge or a conflict, and the two agents of a "
        "plan talk cannot talk without mailbox-chat.py on PATH. The owner installs "
        "agterm's two-agent mailbox chat recipe and adds the command hook "
        "`mailbox-chat.py claude-hook` with `asyncRewake: true` to SessionStart, Stop "
        "and UserPromptSubmit in the Claude Code user settings. Leave hooks enabled."
    ),
    program="mailbox-chat.py",
    probe=(),
    guide=f"{COOKBOOK}two-agent-mailbox-chat#setup",
)
CRONN = Tool(
    name="cronn",
    need=REQUIRED,
    used_for="a scheduled retro and a night run",
    without_it=(
        "no retro and no night run starts by itself, so the corrections wait unread; "
        "install it from https://cronn.umputun.dev (a Homebrew formula and an agent that "
        "starts at login)"
    ),
    program="cronn",
    probe=(),
)
