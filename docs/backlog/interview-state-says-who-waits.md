---
worth: yes
where: skills/lem/stages/interview.md
added: 2026-11-19
---
# The board says the interview waits for the owner after his last answer

A task with an interview writes one state, `held` with `the interview waits for the owner`, before
its first question (`stages/new.md`, step 4), and the next state comes after his yes to the
criteria. While the personas read the criteria, the board and `lem project waiting` leave the task
out of what waits for him, from the log (`reading_of` in `lem_board_model.py`: a
`criteria.read.start` after the held block with no `criteria.read` after it). Two moments of the
interview are still listed as his, because no event tells them:

- after his last answer, while the scout still reads (step 4 waits for the scout's report): the log
  has `scout.start` with no `scout`, but while the scout reads a question may still wait for him,
  and nothing says the questions ended;
- after the scout's report, while Lem writes the criteria (steps 3 and 4).

The case, 2026-11-19 in Lem's own repository: a second Lem session ran the interviews of
`landing-in-the-background` and `interview-in-a-companion`. At 17:03 local time the personas read
the criteria of the first, and the owner had nothing to answer; the board listed both under what
waits for him. He wrote: "I'm lost. I see that landing task is waiting for me and I cannot reach
it's question anywhere", and later "board seems to be bullshitting me". That moment, the read, is
the one the board now tells.

What it would take: an event at the end of the questions (step 3, when `task.md` is written again),
in a fixed form of `STARTS` in `project.py`, and `reading_of` taking the time from it to
`criteria.read.start` as Lem's too. The question of step 5, "Skip the persona read? (y/n)", comes in
that time and is his: it needs an event of its own, or it moves before the end of the questions.
The time card's interview span (`time_of`) would then end at the new event too.

A third moment has the same wrong row, and no event tells it either: while the owner is away, an
interview goes on without him, with Lem's guesses (`stages/away.md`), and the state stays `held`
with `the interview waits for the owner`. The board has his away status (`m.away`), but no event
says when the task's own session took that status up, so the row cannot tell an interview that
goes on without him from one that waits for his answer. Seen by the builder of the read's fix,
2026-11-21.
