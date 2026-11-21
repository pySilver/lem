---
ruled: 2026-11-18
area: What Lem is, and who it is for
---

# Three more commands are no commands of his, and two recipes of the agterm cookbook become required

His interview of 2026-11-17 and 2026-11-18 on what stays in Lem; a quote is his words. He asked
for it ("Lets have quick interview what should stay and what should leave the Lem plugin") after
he measured Lem against three sentences of his: "Good tools don't demand extra attention", "One
thing. Done well - Not an everything Companion. A useful tool that fits into an ordinary developer
day", "Best practices without confusion". `docs/plans/2026-11-18-core-and-two-modes.md` is the
build that follows.

**Three more commands are no commands of his, and two recipes of the agterm cookbook become
required** (his note on the plan, 2026-11-18): "`/lem ask` is suppossed to be called
automatically, just like `huddle` today. `/webrev` becomes a required reciepie. (no need for
`/lem annotate`) `/backlog` becomes a required reciepie. from
https://github.com/umputun/agterm/tree/master/cookbook/backlog-picker (I don't recall why I
wanted my own)". Why he had wanted his own, from his ruling of 2026-11-15 above: three stages
live on the backlog (the night picks from it, a landing files into it, a request starts from
it). Those stages need the item format, which is the recipe's own (`docs/backlog/<slug>.md`
with `worth`, `where`, `added`; read in its README on 2026-11-18), not the skill. So the
`lem-backlog` skill leaves, the stage texts say the format, and the board's Backlog tab stays
(his "Backlog tab - I like this idea"). The recipe's skill tells an agent never to commit an
item on its own; Lem's builders load no such skill and file on the task's branch, as he ruled.

## Replaced, not in force

- Decided on 2026-11-14 and 2026-11-15, replaced by this one, with its text in its own file: [`/lem annotate FILE` is the owner's verb for marking up](../../.lem/decisions/lem-annotate-file-is-the-owners-verb-for-marking-up.md)

### `/lem ask` with no question takes the agent's last question

Ruled on 2026-11-17.

His review of the README and the docs on 2026-11-17, 27 notes; a quote is his words. Where a note
replaces an earlier ruling, this is the ruling now.

**`/lem ask` with no question takes the agent's last question**: "Can we use `/lem ask
<question>` whithout question in a situations when Agent gave us a question in terminal and
our intent is to have a rich contextual question instead?"
