---
ruled: 2026-11-18
area: The settings, the seats and the tracker
---

# Not every section of the settings stays

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-18, [`[checks]` keeps three keys, and `alone` is `serial`.](checks-keeps-three-keys-and-alone-is-serial.md): "`[checks]` stays with `commands`, `setup` and `alone`": `alone` is `serial`
- 2026-11-18, [Four places are settings](four-places-are-settings.md): "Lem's own files ... have one place each and no key": the rulings' place and file name are settings

## As ruled on 2026-11-18, changed in part since

His interview of 2026-11-17 and 2026-11-18 on what stays in Lem; a quote is his words. He asked
for it ("Lets have quick interview what should stay and what should leave the Lem plugin") after
he measured Lem against three sentences of his: "Good tools don't demand extra attention", "One
thing. Done well - Not an everything Companion. A useful tool that fits into an ordinary developer
day", "Best practices without confusion". `docs/plans/2026-11-18-core-and-two-modes.md` is the
build that follows.

**Not every section of the settings stays** (his note on the plan, 2026-11-18): "I also have
doubts all sections of the settings should stay ... paths.styleguide - is it really part of the
Lem or harness setup itself? paths.lessons vs paths.rules (wft? which is what? why?)
paths.backlog - coookbook covers this. [checks] - thats git hook job. [tools] - goes away?".
The answer is the session's, task 1b of the plan, which he passed with no note: the settings go
from 40 keys to 25; Lem's own files and the folders of other tools have one place each and no
key; the rules for the code are the harness's folder, and Lem only names the matching files to
the agents that load nothing by themselves; `[tools]` goes; and `[checks]` stays with
`commands`, `setup` and `alone`, because a test suite is no git hook's job and "green" must be
what a script saw. His two rulings that this reopens, on his own question: "A developer may ask
with a tool of their own" (`tools.ask`, `tools.annotate`) and the linked folders of an adopted
project (`init --existing link`).

## Replaced, not in force

### A developer may ask with a tool of their own

Ruled on 2026-11-14.

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

**A developer may ask with a tool of their own**: "We also need a way out, to let dev avoid
huddle if they prefer their own asker UI?", and of the key built from it, "I like your solution
for huddle, then name and the way out". The key was `tools.ask`, beside `tools.annotate`. He
let both go on 2026-11-18 ("[tools] - goes away?", his interview, below): Lem asks with its own
page, which needs agterm, and agterm is required.
