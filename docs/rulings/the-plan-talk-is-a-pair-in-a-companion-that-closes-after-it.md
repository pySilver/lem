---
ruled: 2026-11-16
area: The plan, the build and the tests
---

# The plan talk is a pair in a companion that closes after it

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-17, [A seat is written `agent/model:effort`](a-seat-is-written-agent-model-effort.md): the seat "`[seats.planner]` (only `claude`, with a model and an effort)" is one value in that form, `seats.planner = "claude/opus:high"`, and its agent is still only `claude` (`docs/settings.md`)
- 2026-11-19, [A companion opens only when something waits for him, and closes when he answered.](each-task-lives-in-a-session-of-its-own-from-its-shape-to-its-merge-and-there-is-no-lem-session.md): "Since 2026-11-19 (below)": the card of a talk's choice opens in that choice's own companion, not in the plan talk's
- 2026-11-20, [The build asks him nothing, and the ladder always decides](the-build-asks-him-nothing-and-the-ladder-always-decides.md): for a choice of the talk: the build asks him nothing, and the ladder always decides
- 2026-11-20, [Each task lives in a session of its own, from its shape to its merge, and there is no Lem session.](each-task-lives-in-a-session-of-its-own-from-its-shape-to-its-merge-and-there-is-no-lem-session.md): the companion: the talk is a companion of the task's session, where it was a companion of Lem's session, and the companion of a choice's card is gone (its note that starts "With Q11 as the new fact")

## As ruled on 2026-11-16, changed in part since

His ruling of 2026-11-16. It is reopened only by asking him. A quote is his words.

**The plan talk is a pair in a companion that closes after it**: "for such review we need a
pair setup, so Lem (or Lead?) should open a companion where two agents of specific models and
efforts have a chat about the plan under some rules that disallow endless discussion. This is
the oppsite than calling fresh context all the time + gives a visibility if Owner want to have
a look. Companion is closed once discussion is done" (2026-11-16). The form is the session's
design, which he answered with "Good design!": Lem opens the companion when a builder stops at
a careful or large plan, and closes it when the task's event log holds the talk's
`plan.talk`; its left agent is the plan's defender (`prompts/defender.md`), on the seat
`[seats.planner]` (only `claude`, with a model and an effort), and builds nothing; the build
goes to a builder lead, one fresh builder per task; and a Fable second opinion's check for a
layer of patches, which he asked for in "Sometimes the fix in the plan, even during discussion
is just another layer of patching. It stays ugly but in a different way. And due to cap and
rules it goes that way. So we need a critical look whether fix is good or just another layer":
a repair that adds a mechanism names the decision it sits on, the reviewer says `at the cause`
or `layer over D`, a layer over a decision with no cite closes as a design choice, and
`plan.talk` counts `root`, `layer` and `shared`. He agreed with the check and asked: "One
question - whether it will catch an issue where fix should be applied at root level (whatever
it calls) and that change would trigger number of other issues (sign that such change is
probably not the best solution)" (2026-11-16). What answers it is the session's design: each
issue the reviewer finds in a changed decision is a hold of the same question, so such a
question closes as a design choice, and the card compares the kept decision and its mechanisms
with the reversed one, its tasks, its acceptance criteria and each issue raised against it.
Since 2026-11-19 (below) the card of a talk's choice opens in no plan talk's companion: the
defender tells Lem `lem: SLUG choice N waits`, Lem opens that choice's own companion
(`SLUG · choice N`), and gives the defender his answer as one message. The talk stays a
companion of Lem's session with the reviewer in its split pane, as before.
