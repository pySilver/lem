---
decided: 2026-11-16
area: A request: its type, its track and its commands
---

# Whether a change is careful is inferred from what the owner said must not go wrong, never matched from a list of paths

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-18, [No word and no form of a Lem before is kept.](../../docs/rulings/no-word-and-no-form-of-a-lem-before-is-kept.md): "`project.py` refuses a settings file that still has the list": the refusal of a settings key that went is removed
- 2026-11-18, [A night ends as pull requests, and a task without the owner covers what a night was](a-night-ends-as-pull-requests-and-a-task-without-the-owner-covers-what-a-night-was.md): "`drafted`" among the states of a lead: the state `drafted` is gone

## As decided on 2026-11-16, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

**Whether a change is careful is inferred from what the owner said must not go wrong, never
matched from a list of paths**, after his question of 2026-11-16 in "What must not go wrong is
named by topic". A list of paths goes stale as the code moves, misses new code, is a second
thing to keep, and can be edited by the branch it guards. So `flow.careful` and `project.py
careful` are gone, and `project.py` refuses a settings file that still has the list, with the
sentence to write in its place. `flow.topics` is the one setting: sentences in the owner's
words, proposed at onboarding by one question, "what must never go wrong here?". Three agents
judge a change against them, and in doubt they say careful: Lem at the ask, from its words and
the scout's facts, in the first line it says to the developer, and an ask in reach of a topic
is never a small change; the lead at the plan, by a topic or a pattern other code will copy; and
the fresh agent that reviews the diff before the pull request, whose record holds `careful`
and `careful_why` and which runs the full set when it calls careful what the plan did not. The
last is the look that takes the place of the path list's floor: its judge did not build the
change. `land.py` enforces what the records say: a review record with no call is refused, a
request is careful when the plan (its `careful: yes` under its title, in any commit of the
branch), the owner's word in the brief or the newest answered review says so, and an agent
merges only a green request whose newest review said not careful. `careful.missed` is the
event for a careful call of the review that the plan did not make. The topics cannot be lifted
by the branch they guard: `project.py` reads the main checkout's settings (its working tree
while it is on the base branch, the base branch's commit while another branch is checked out
there, `committed_settings`), and in a task's worktree it takes `[flow]` and `[naps]` from there
too, so the landing, the lead, `decisions.py` (audit findings S1 and W2) and the review read
the main checkout's table, and `land.py` reads every setting from it
wherever it runs. A change whose diff edits
`.lem/project.toml`, in any table, is careful by the script: the one rule that is a match and
not a judgment, because the file is Lem's own. The same holds for a diff that puts the
machine's own `.lem/project.local.toml` into git (the second audit, N5). And a task in
`landing` or `open` takes no state of a lead (`queued`, `building`, `planned`, `ready`,
`drafted`): a lead that woke late wrote `ready` over an open task and its landing ran again
(N1). `ready --start-over` is the one way back, and only `land.py`'s messages name it.
