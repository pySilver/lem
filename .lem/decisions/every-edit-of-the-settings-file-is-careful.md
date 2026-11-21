---
decided: 2026-11-17
area: A request: its type, its track and its commands
---

# Every edit of the settings file is careful

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**Every edit of the settings file is careful** (A1). The script guarded only `[flow]` and
`[gate]`, so a branch that changed `branch.land` from "owner" to "agent" in its own
`.lem/project.toml` got one read, no careful call and a green pull request, and the same held
for `[branch]`, `[corrections]`, `[seats]` and `[paths]`. A list of the tables that matter is a
second thing to keep and misses the next one. So `land.py` calls careful any diff that touches
the file, with that reason: the file is Lem's own and rarely edited, so the cost is a person's
merge of a rare change.
