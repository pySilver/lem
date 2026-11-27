---
worth: later
where: skills/lem/stages/interview.md
added: 2026-11-24
---
# The interview grills every task the same way

The idea: a profile of the interview for each task, chosen when the shape starts, as the review
picks its profiles from the diff (`stages/land.md`, the review agent). The profile says which areas
the questions cover (the data, the person on the screen, a contract with another program, the
rollout) and how wide the shape goes: a few questions to confirm, or the wide check of a shape
nobody knows yet, with `lem-dialectic`, `lem-ask-expert` and the panel. Today step 2 of
`interview.md` loads `lem-interview-me` for every task, a generic method for an ask that does not
say for whom or why ("build me a dashboard"); it reads no `flow.topics`, no persona and no scout
fact before its first question.

The owner named the need on 2026-11-20, of the shape: "Sometimes full context is provided from
Ticket or Backlog Item and I just approve few steps. Sometimes its a wider discussion that requires
dialectic checks, research, experts and panel reviews. Specifically when we don't know what final
shape is preferred."

Much of it is there already. The track gives three depths: the fast track and a complete request
have no interview, and the standard track has one. The method's stop ("stop when you can write the
outcome and each rule without a guess") sets the length: the 30 `interview-notes.md` files in this
repository's state folder hold from 1 to 75 lines, 5 at the median (count of lines that are not
empty, 2026-11-24). What is not there: the areas are the same for every task, and the wide check
starts only from his words ("A helper starts from plain words", 2026-11-18).

No miss of the interview is on record. A criterion that the build changed is the trace of a miss,
and the build changed 8 criteria in 5 tasks (`kind: criterion` in `decisions.jsonl` of each task,
2026-11-17 to 2026-11-24). None goes back to a question the interview did not ask: 4 follow a base
that moved (a rename of the settings files, a release), and the others fix an example, a date, or
widen a criterion to its class. No breaker is on record.

Options:

- (a) Nothing now. Cost: none.
- (b) One paragraph in step 2 of `interview.md`: before the first question, say in one line which
  areas this ask needs, from the ask, the profile, `flow.topics` and the cast. When his answers
  leave two shapes open with no preference of his, one question offers the wide check as an option,
  so it still starts from his word. The same question may offer a throwaway prototype of each shape
  instead, on a branch that never lands (taken from SeeMasta on 2026-11-25 as part of this option). Cost: one line he reads per interview; no script, no key, no
  file of profiles. The fast track and a complete request read nothing new.
- (c) Profiles of the interview as files in `.lem/`, as the review tool's lenses are, with an agent
  that picks them per task. Cost: a new part of the settings, one more agent before the first
  question, and a template that `/lem init` fills.

Recommendation: (a) until a real task shows a miss, then (b). The unknown that settles it: one
interview whose missing area cost a round later (a criterion the build changed for it, a breaker, a
plan talk that went back to him, or his words "you did not ask about X"). (c) waits for (b) to show
that one line of areas is not enough.

Raised by the owner on 2026-11-24, as "dynamic grill-me profile for the task"; the reading above is
the maintaining session's, and his word corrects it.
