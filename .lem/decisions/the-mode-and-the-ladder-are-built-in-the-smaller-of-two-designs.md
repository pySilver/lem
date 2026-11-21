---
decided: 2026-11-18
area: A decision without him: the ladder, the experts and the breaker
---

# The mode and the ladder are built in the smaller of two designs

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-20, [The build asks him nothing, and the ladder always decides](../../docs/rulings/the-build-asks-him-nothing-and-the-ladder-always-decides.md): "the card": the build asks him nothing, and the ladder always decides
- 2026-11-20, [A fresh merge agent reads every proposed task, and merges it or calls him](../../docs/rulings/a-fresh-merge-agent-reads-every-proposed-task-and-merges-it-or-calls-him.md): "an agent never merges while a task runs alone": the merge agent reads every proposed task and merges it or calls him

## As decided on 2026-11-18, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**The mode and the ladder are built in the smaller of two designs** (2026-11-18). A first
design of the plan's tasks 2 and 3 added six `lem decisions` commands, forms for what agents
answer, a script that checked the lines a dialectic agent cites, and about 300 script lines
(its own estimate). A Fable second opinion, asked before any builder started: "The ladder half
is a state machine with parsers that no act of Lem's needs, and three of its rules fail toward
settled", for one a persona's objection that the script could not parse was dropped and the
rest then settled the decision green. So the rules of the ladder are one stage text that the
lead applies, since the lead reads the code, and the script checks one thing only: two persona
votes or more, all for the option taken. A count moves into a script when a real run shows a
lead that records a level wrongly, and only that count.
`docs/plans/2026-11-18-core-and-two-modes/mode-and-ladder.md` is the design. It corrects two
sentences of the plan the owner passed, both told to him: a task that ran without him is not
green only when something of his was decided without him, and an agent never merges while a
task runs alone; and with him a decision that the gate or the personas settled gets no card,
while Lem says each decision once in the conversation, for his "Sometimes I would love to know
the decisions taken before implementation".
