---
ruled: 2026-11-19
area: The plan, the build and the tests
---

# The tests are chosen by what can fail, and a task is quick.

His notes of 2026-11-19, in the session, on the Linear page and in the interview on his away
status; a quote is his words.

**The tests are chosen by what can fail, and a task is quick.** Of three builders that took 49,
99 and 115 minutes the day before: "Why the hell it takes so long!?", "thats still enormous
amount of time for the skill repository! what those tests doing so long?", and "I demand quick
tasks run". He had an Opus subagent and Codex Astra asked two times what the tests of such a
repository should look like. Their answers agree, and the session took them: a rule that takes
facts and returns a result is a unit case, a call of its function (`tests/unit/`); a fact only
git can show is a check in a real repository; a journey is run once, not once for each input.
The loop of "Checks" is the other half: half of a builder's time had been test runs that the
session's own briefs asked for. A cache of git's answers inside one process (`perf/ask-once`)
was built that night and not taken: a Fable second opinion, Opus and Astra all said that a stale
answer in the code that merges costs more than the 0.1 s it gives a developer.
