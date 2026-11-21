---
ruled: 2026-11-19
area: A task's session, and whether he is there
---

# His away status is one mark of the machine, and a night task always runs without him

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-20, [Each task lives in a session of its own, from its shape to its merge, and there is no Lem session.](each-task-lives-in-a-session-of-its-own-from-its-shape-to-its-merge-and-there-is-no-lem-session.md): "Lem's session in each repository keeps one watch of it": the watch is the shape's session's (the note at line 924)

## As ruled on 2026-11-19, changed in part since

His notes of 2026-11-19, in the session, on the Linear page and in the interview on his away
status; a quote is his words.

**His away status is one mark of the machine, and a night task always runs without him** (his
interview of 2026-11-19, `docs/plans/2026-11-19-away-for-the-whole-machine.md`). To "Is the
machine's mark the only mark?" he answered "y". Of the night: "Night run is an exceptional
unattented type of run and should not be affected by the state of my availability. It should
always run unattended. Even when I'm up at night and doing something in other sessions." Of the
place: "I belive something should live in `~/.config/lem` to support that". So `/lem im-away` and
`/lem im-back`, typed in any repository, hold in every repository on the machine, no repository
has a status of its own, and his `back` never ends a night task's time without him. The form is
the session's: `owner.jsonl` in `$XDG_CONFIG_HOME/lem`, or in `~/.config/lem` when the variable
is unset (a relative value is refused), one line appended for each away and each back and none
removed, so that another repository still reads the span of a task that ran without him; Lem's
session in each repository keeps one watch of it (`lem project owner watch`) and acts on its end
as on his word there, and the session of a night keeps none; the board reads `owner.js`, a copy
in the state folder; and every test suite sets `XDG_CONFIG_HOME` under its own folder. Each
repository's Lem still runs only its own tasks and reads one more fact, the mark: that is how
the change keeps "One Lem for one repository".
