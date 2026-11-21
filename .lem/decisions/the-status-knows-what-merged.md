---
decided: 2026-11-17
area: The review, the pull request and the merge
---

# The status knows what merged

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-18, [A night ends as pull requests, and a task without the owner covers what a night was](a-night-ends-as-pull-requests-and-a-task-without-the-owner-covers-what-a-night-was.md): "a report of that night or the one before that names a draft still `drafted`": the state `drafted` is gone
- 2026-11-20, [Each task lives in a session of its own, from its shape to its merge, and there is no Lem session.](../../docs/rulings/each-task-lives-in-a-session-of-its-own-from-its-shape-to-its-merge-and-there-is-no-lem-session.md): Lem's run of `land.py merged` before a status: the server takes it over (its note that starts "With Q11 as the new fact")

## As decided on 2026-11-17, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

**The status knows what merged** (2026-11-17). The audit found that only a landing ran `land.py
merged`, so a pull request he merged on the forge showed as open in the morning and a task
queued `after:` it waited with nobody to act (F2, W3). So before a status, and at each turn of
Lem's where it reads `decisions.py pending`, Lem runs `land.py merged` for each `open` task with
a pull request, takes the steps after a merge, and looks at the queue. The status changes what
already happened and nothing else. The night report rule read "newer than the last status
shown", which no file records; it is now a report of that night or the one before that names a
draft still `drafted`, which a fresh session can read from the files.
