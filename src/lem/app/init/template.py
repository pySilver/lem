"""The text of `.lem/settings.toml` as `lem init` writes it: every key of the team's file, each
with the comment that says what it does, the seats whole, and the keys a team rarely sets left
as comments (docs/settings.md is the reference)."""

import string

import msgspec

TEMPLATE = string.Template(
    """\
# What Lem reads in this repository: the team's settings, in git. `lem settings show` prints
# every value in force with the file it comes from. Your own settings for this repository alone
# go in .lem/settings.local.toml, which git does not track and which wins here; yours for every
# repository go in ~/.config/lem/settings.toml. `lem settings set KEY VALUE --local` or `--home`
# writes one of them; no command writes this file.

[paths]
# The folder of the plans, relative to the root of the checkout. Lem's own files are in .lem/,
# the rules for the code in .claude/rules, the review tool's folder is .revmux and the backlog is
# docs/backlog: each has that one place, and no line here.
plans = "docs/plans"
# The name of a plan's file in the plans folder: YYYY, MM and DD are the day the plan was
# written, <slug> is the task's.
plan_file = "YYYY-MM-DD-<slug>.md"
# The rulings file: the list of your product decisions, one bullet for each, which outlive a
# task. A bullet is `- **The rule in one sentence.** (YYYY-MM-DD)` under the `##` heading of its
# group. The file comes with the first ruling.
rulings = "docs/rulings.md"

[branch]
# The branch a task starts from and lands on.
$base
# Who merges a task's pull request. A fresh merge agent reads each proposed task and writes its
# review either way. "agent": it merges a green request that is not careful, and calls the owner
# for every other one. "owner": it never merges, and the owner merges each one after its review.
# Lem pushes each task's branch and opens its pull request on GitHub without asking: these
# settings are the owner's word for exactly that.
land = "agent"
# What lands: "squash" lands one commit for the whole task, "keep" lands the branch's commits.
history = "squash"
# Branches nothing lands on and nothing is pushed to through Lem, whoever asks.
protected = []

[checks]
# During the build, each builder runs only the tests of its own change. Before the pull request,
# Lem runs these commands one time, at the root of the task's worktree: the whole suite. A linter
# and a type checker belong in a git hook, which runs at each commit; a test suite belongs here,
# since a hook must be fast and "green" must be what Lem saw.
commands = []
# What a new worktree needs before its tests can run: install the packages, copy an environment
# file ("uv sync", "npm ci"). Lem runs these one time in each worktree it makes for a task, and
# in the two worktrees of the check that each criterion's tests fail on the base commit.
setup = []
# The tests that two tasks cannot run at the same time: an end-to-end suite that uses fixed
# ports, one database or a browser. They run after `commands`, one at a time for all tasks,
# under one lock for the repository, and a builder runs a test of such a suite through
# `lem serial -- COMMAND`. Keep them out of `commands`.
serial = []

[flow]
# What must never go wrong in this project, each as one sentence in the owner's words: "a
# customer is charged the wrong amount", "data that cannot be rebuilt is lost", "someone signs
# in as another user". No code matches these and no list of paths stands in for them: Lem reads
# the ask against each, the lead its plan, and the agent that reviews the diff the change
# itself, and a change in reach of one takes the careful flow. This table is read from the main
# checkout, so a branch cannot lift what guards it.
topics = []

[seats]
# Who sits where, each as "agent/model:effort". The reviewer, the planner, each expert and the
# fallback are written whole. A part left out of the merger or the session ("claude",
# "claude:high") takes that agent's own default. Each seat comes from the first file that names
# it: .lem/settings.local.toml, this file, ~/.config/lem/settings.toml, then Lem's own,
# "claude/opus:high" for each seat but the experts.
# The reviewer, on the agent "claude" or "codex", which talks the plan of a careful or large
# task through with its defender.
reviewer = "$reviewer"
# The defender of a careful or large plan in its talk with the reviewer: only "claude" for now.
planner = "claude/opus:high"
# The merge agent, which reads each proposed task and merges it or calls the owner: "claude" or
# "codex", read-only.
# merger = "agent/model:effort"
# The agent of each task's own session in agterm: "claude" only for now.
# session = "agent/model:effort"
# The experts, the last level of the ladder of a decision in doubt: two model families, so that
# their agreement is worth more than two of one. Where the machine has one of their agents, that
# expert answers alone.
experts = [$experts]
# The seat that stands in for the reviewer, the planner or the merge agent when its agent gives
# an error, so that the task goes on and the pull request says so. false turns it off: the task
# then waits for the owner. Left out, it is "claude/opus:high".
# fallback = "agent/model:effort"

# The tracker a task's ask may come from: "linear" or "github". Leave it out when the project
# has none.
# [tracker]
# kind = "linear"

[state]
# How many days Lem keeps what it no longer needs in .lem/state/, the folder git never sees:
# every file of a task that ended and that nothing happened in for that many days but its small
# record. `lem prune --dry-run --days 7` shows what 7 would remove. The default, 30, is the
# owner's word of 2026-11-21. One person with less free disk, or more, sets a number for their
# machine alone with `lem settings set state.keep_days N --local`.
keep_days = 30

[naps]
# Now and then, when a task has ended or Lem waits for the owner, a fresh agent reads the recent
# tasks, dreams, and writes the dream down for the retro. It costs an agent's session of some
# minutes, a few times a day, and nobody has shown that it helps.
on = false

[jev]
# Before a pull request, Lem asks the Jev decision model about each defect outside a task that an
# agent calls under the bar, and which items of the backlog may hold the same one. Each question
# sends the finding's place, title and text to the model's provider, with the key JEV_API_KEY of
# the machine that lands; with no key, nothing is sent. false sends nothing from this repository.
findings = true
"""
)
# The reviewer's seat for each answer to "does the machine have Codex": two model families
# disagree more usefully than one family twice (the owner, 2026-11-18).
REVIEWERS = (("yes", "codex/gpt-6.2-sol:high"), ("no", "claude/opus:high"))
EXPERTS = ("claude/fable:high", "codex/gpt-6.2-astra:high")


def reviewer_of(codex: str) -> str:
    """The reviewer's seat on a machine with Codex (`yes`) or without."""
    return next(seat for answer, seat in REVIEWERS if answer == codex)


def written(base: str | None, codex: str) -> str:
    """The text for the base branch `base`, on a machine with Codex (`yes`) or without."""
    experts = (seat for seat in EXPERTS if codex == "yes" or seat.startswith("claude"))
    listed = ", ".join(map(quoted_of, experts))
    reviewer = reviewer_of(codex)
    base_line = "" if base is None else f"base = {quoted_of(base)}"
    return TEMPLATE.substitute(base=base_line, reviewer=reviewer, experts=listed)


def quoted_of(word: str) -> str:
    """A word as a TOML string, its quotes and backslashes escaped."""
    return msgspec.json.encode(word).decode()
