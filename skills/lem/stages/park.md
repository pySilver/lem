# `park`, `resume`

Read when the owner puts a task aside, `/lem park [task]`, or goes back to one, `/lem resume
[task]`, or says the same in plain words ("put the gift note aside", "let's go back to the gift
note"). Parking is one of his three answers to a breaker, with his help and `/lem drop`: "abandon /
return the task and keep the context or help" (2026-11-20). Which task: as `stages/correct.md` says
under "Which task", and a breaker that waits is the likely one.

## park

A task that no agent works on is parked: one that waits for him (a breaker, criteria for his yes,
a step of his), one blocked, and one `planned` or `queued`. Its status, its worktree, its branch
and its files stay; the hold `parked` stands in place of the hold it had, and it leaves "Waits for
you".

```bash
lem task park SLUG --why "HIS REASON, IN HIS WORDS, OR: the owner parked it"
```

`lem task park` refuses a task whose lead or investigator works now (park it once it stops, or
drop it), one with its landing, and an ended one. Say in one line that the task is parked, since
when (`lem task show SLUG`), and
that `/lem resume SLUG` brings it back. Then its session closes: typed in the task's own session,
as its last act (`prompts/session.md`, "The end"); typed elsewhere, `lem session close SLUG --why
owner`. A parked task gets no lead, takes no state of a lead that woke late, and waits for nobody.

## resume

```bash
lem task resume SLUG
```

- **A parked task** is the same task again, with the hold it had before the park, in its own
  worktree: a breaker's wait, criteria for his yes, a step of his. Then `lem session open SLUG --why owner`: its session
  reads the record, `handoff.md` and the breaker's document (`breaker-N.md`), so the talk goes on
  where it stopped.
  A parked task begun two releases back stops at its resume with the message of its release stop:
  it comes back only as a new request, after `/lem drop SLUG` and a resume of the dropped task.
- **A dropped task** stays dropped. The command opens a new task from it, with the next free
  number, `SLUG-2` (then `-3`): its branch `TYPE/SLUG-2` is cut from the tip of the old branch, so
  the commits come with it; its task directory gets the old one's request, criteria, handoff and
  breaker document, and a brief whose `task`, `branch`, `worktree` and `task directory` lines are
  its own; its record keeps the release the old one began on and names the old slug
  (`resumed_from`); its worktree is made; and its hold is the breaker that waited, with the line
  `resumed from SLUG, which was dropped`. Then
  its session opens as for a parked task, with the new slug. A dropped task with no breaker that waits, and no release stop, has
  no talk to go back to, and the command says that a new ask does it; a dropped task resumed once is not
  resumed again (the command names the task it went on in). Nor is a dropped task whose journal
  `lem prune` folded into one summary entry past `state.keep_days`: its approved criteria, the
  personas' read and its decisions went with it, so the command refuses before it makes
  anything, and its message ends with the line of the new ask, `/lem` and the dropped task's ask
  (`ask.txt`), which you give the owner. The plan comes with the branch under
  the old slug's name: `lem task plan-file SLUG-2` gives it as `found`, and `lem criteria show
  SLUG-2` reads it, until its lead writes a plan of the new name.
- **A dropped task the release stop blocked** (dropped from the hold `release`) needs no
  breaker and no `handoff.md`: it goes on as a new request on this release, `SLUG-2`. Its
  branch `TYPE/SLUG-2` is cut from the branch the stop named, with the type of that branch's name;
  when git no longer has that branch, or the stop named none, the result gives `branch` null and
  the missing name as `missing`, and the new task starts from the base. Its task directory gets the
  notes (its Markdown documents, each breaker's document, `media/` and the ticket's files) and the
  ask; its record is new, on this release, and names the old slug (`resumed_from`), with nothing
  of the old record and no worktree: those are a release two back's. Then run the `next` its result names, `lem session open SLUG-2
  --why new`: the new session takes the shape anew from the notes (`stages/new.md`, "The
  request"), and the owner approves the criteria once more.

Say its `say` in one line: what came back, and the session where he talks it through.
