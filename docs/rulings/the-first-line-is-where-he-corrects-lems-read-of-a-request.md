---
ruled: 2026-11-18
area: A request: its type, its track and its commands
---

# The first line is where he corrects Lem's read of a request

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-18, [The commands of his status and of a task are `/lem im-away`, `/lem im-back`, `/lem be-careful [task]`, `/lem standard-track [task]` and `/lem drop [task]`.](the-commands-of-his-status-and-of-a-task-are-lem-im-away-lem-im-back-lem-be-careful-task-lem-standard-track-task-and-lem-drop-task.md): "`/lem careful`, `/lem standard`, `/lem drop`": the commands are `/lem be-careful`, `/lem standard-track` and `/lem drop`

## As ruled on 2026-11-18, changed in part since

His interview of 2026-11-17 and 2026-11-18 on what stays in Lem; a quote is his words. He asked
for it ("Lets have quick interview what should stay and what should leave the Lem plugin") after
he measured Lem against three sentences of his: "Good tools don't demand extra attention", "One
thing. Done well - Not an everything Companion. A useful tool that fits into an ordinary developer
day", "Best practices without confusion". `docs/plans/2026-11-18-core-and-two-modes.md` is the
build that follows.

**The first line is where he corrects Lem's read of a request** (the same notes): of the row
`"full", "careful" or "drop"`, "I see why want it, but I cant imagine this being clear to
developer. Maybe it should be a quiz with assumption at the beginning. During the execution, we
cannot switch from short path to full, it's too late. But we can drop the plan. I'm not sure we
can swith to careful execution, probably not?". The session answered that the first
line is that quiz with its assumption taken, and that it adds no question; he wrote back: "I
think confirmation step (when confused) should be add. When its clear - we go without it. I
understand that it breaks contract, but isn't it a right thing?" So a clear read asks nothing,
and a read that Lem cannot settle (the size, the type, careful) asks one line in the terminal
with its guess, before any agent starts; while he is away Lem asks nothing and takes the safer
read. Of "careful until the merge": "Still, weird interface. Maybe it should be something like
a command that would affect the plan, and even when plan is already completed it will do the
right thing, for example it will run the proper review", and of "drop": "but still - Lem
should understand what plan is affected the current one or something else". So the three are
commands that take a task, `/lem careful`, `/lem standard`, `/lem drop` (`stages/correct.md`): a
task with an open pull request that is called careful goes through the full review again;
`standard` holds until a task on the fast track is proposed; and Lem asks which task when more than one
could be meant.
