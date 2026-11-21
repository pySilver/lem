---
decided: 2026-11-17
area: A request: its type, its track and its commands
---

# The size of a change decides its path

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

**The size of a change decides its path** (2026-11-17), under his "Lem should not make simple
things complicated, otherwise developers will get frustrated so often they will stop using
Lem" and, of a polish agent with nothing to do on a typo, "That is exactly one of the cases
that may frustrate the Developer" (2026-11-16). An audit that day walked ten everyday asks
through the stage files: a typo started 6 to 11 agents and took 15 to 32 minutes to its pull
request, a one-rule correction 6 agents and 15 to 25 minutes, against about 4 minutes measured
for a correction in the first flow, and a lead read about 18,500 words before it acted (the
times are unmeasured estimates built on the skill files' measurements; the words are `wc -w`
of the files a lead reads). So a small change, one plain change with one acceptance criterion in his own
sentence, no topic in reach and no question open, whatever its type, has one builder and no
lead: `prompts/small.md`, a brief complete in itself, and the builder's standing rules. It
commits no plan; its criterion is `criteria.md` in the task directory, approved in his name, with
its test line, and `criteria.py` and `land.py` read it there when the branch has no plan file,
for a small change only. A change that keeps behavior has `no test`; its builder runs the tests of the files it
changed and of their direct callers, and the checks run the whole suite one time. Before it commits, the builder reads its change against the topics and stops
with `the criteria wait for the owner: the small change is a full change` when it reaches one, needs
a second rule or a decision, lowers the bar or grew. Its landing is `start`, `base`, `checks`
(with `criteria.py red` once), one read by the review agent itself, and `propose` with a short
text; no polish pass at all, and its builder files what it sees outside the change. A small
change that is
careful after all (by the review's call or its edit of the settings) is not green and a person
merges it, since it skipped the interview, the read and the plan; one that lowers the bar is
refused by the checks. Lem says the type and the size, the branch, the criterion, what happens and what he must do
in one line before anything runs, and nothing repeats it. Counted from the text after the
change, a typo, a rename and a one-rule fix each start two agents (the builder and the review
agent), and the builder reads `prompts/small.md` and `agents/lem-builder.md`, 1,954 words
(`wc -w`: 775 and 1,179, at 15d5697, 2026-11-17).
