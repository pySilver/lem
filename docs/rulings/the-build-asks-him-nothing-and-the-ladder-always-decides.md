---
ruled: 2026-11-20
area: A decision without him: the ladder, the experts and the breaker
---

# The build asks him nothing, and the ladder always decides

His rulings of 2026-11-20 and 2026-11-21, while his interview redesigned how a task runs and the
board became a served app; a quote is his words. His answers Q7 to Q11 and notes P1 to P9 are in
`.lem/state/tasks/one-lem-parallel-landings/`, which git ignores. Where a note replaces an earlier
ruling, this is the ruling now.

The first three tasks of the redesign, in the order he agreed to (Q9, "Yes I agree"):

**The build asks him nothing, and the ladder always decides**: his "yes" to Q7, and "I'd rather
review the PR and request a fix then find a work blocked on some question that automated anwers
could answer right." A pick past the personas is logged with its story and makes the pull request
not green; `lem decisions` asks nothing, and his away status changes nothing in a build. This
replaces "Two experts answer a choice that waits for him" (2026-11-16) and, for a choice of the
build, "He says whether he is there" (2026-11-18), "Lem asks through its question page"
(2026-11-15), "A companion opens only when something waits for him" (2026-11-19) and "The plan
talk is a pair in a companion" (2026-11-16); of the session's decisions, "Every decision that is
the owner's takes one path" and the card in "The mode and the ladder are built in the smaller of
two designs".

## Replaced, not in force

### Two experts answer a choice that waits for him

Ruled on 2026-11-16.

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

**Two experts answer a choice that waits for him**: "also at Lem we will need a skill "ask
expert" which calls Fable subagent and GPT-6 Astra experts in background. This is good
solution / way out in a situation where human isn't here to answer the question and we need to
take a decision" (2026-11-16). On a page the same day he picked "At the start of every wait"
for when they come in: their two answers are on his card while he decides, their shared pick
is taken at the end of the wait (the recommended option when they split), and at once when he
is away. And he picked "Not green" for a choice they decided: one line of the pull request
names their pick and their reasons, and he reads it before he merges. A step that a later "no"
cannot reverse is never decided by the experts and waits for him; that one was kept without a
question and told to him on the page. The form is the session's design: the `lem-ask-expert`
skill, `decisions.py advise` and `settle --away`, and the harness's `ask-experts`.
