# When a lead stops

A builder's reply is the path of its report, and a small change's builder replies with the
report itself, which you write into `report.md`. The defender of a plan talk sends one message
that starts with `lem:` and names the task. Either is only a wake-up. The fact is the task's
newest state block: `lem project tasks`, then read the task's `report.md`.

A lead whose agent refused it the write of `report.md` says so in its state (`report in the
reply`), and its reply is the whole report. Write that text into `report.md` word for word, with
one line at the top that says who copied it and why. Change nothing in it. The harness file says
when this happens.

Act on the status. Each start of a lead below goes as `stages/start.md` says, and after each of
these comes "The queue", the last section of that file:

- **`queued`** with an `after:` line: the lead found at its plan that the task needs what that
  task changes, and the line before it says what. Nothing is owed now: the queue starts it when
  that task ends. Tell the owner in one line, with both tasks' asks.
- **`ready`**: the task joins the landing line. Run `stages/land.md` when no task is in
  `landing`; a `ready` task waits there in the order of its state's time.
- **`planned`**: the report says why the lead stopped at the plan.
  - *It needs a session* (`needs a session: careful`, or `needs a session: large` for a plan of
    more than three tasks): change the brief to `lead: session`, and start a lead. That opens
    the plan talk's companion, whose agent defends the plan against the reviewer in its other
    pane (`prompts/defender.md`): a builder has no pane for the reviewer.
  - *The talk is done* (`the plan talk is done`, after `lem: SLUG talk done`): read `talk` in
    `lem project tasks`, never the line's claim. A record there: close the companion
    (`open-task-session`), change the brief to `lead: builder`, and start a lead; the builder
    leads the build of the talked plan, one fresh builder for each of its tasks
    (`stages/plan.md`, step 3). Each choice the talk left open waits in `lem decisions pending`:
    ask it as `stages/choice.md` says. No record: the defender ended without its last step, so
    send it one message that says so, and close nothing.
  - *The owner asked for the plan only*: show the owner the plan through the settings'
    `tools.annotate`, and leave the task as it is until the owner says build or drop.
- **`held`**: the task waits for the owner on what is no decision with options; a decision of
  his never holds a task, since it is asked and waits its time while the work goes on
  (`stages/choice.md`). The state's line says which of four it is:
  - *the criteria wait for the owner*: a lead of a full change from a complete request whose
    criteria a persona doubted, or
    that met a rule it could not write without a guess, or whose request somebody else wrote,
    puts the criteria and the answers on top
    of its report. Put them to him as step 6 of `stages/interview.md` says,
    with the lead's read as the result on top, freeze his answer with step 7, and start a lead: it
    copies the approved criteria. A small change that its builder found to be a full change goes to
    him as `stages/new.md` says in "A small change", step 3;
  - *one more fact*: the investigation's, as `stages/investigate.md` says;
  - *a step that is his to do*, and no decision at all: a trust prompt of the reviewer's agent, a
    command an agent is refused. Tell the owner that step as it is, with where he does it; it
    needs no question gate and no panel. When he says it is done, start a lead:
    for a defender whose companion is still open that is one message to it, and otherwise a
    fresh lead that reads the state and goes on;
  - *choice N waits for the owner*: an irreversible step that every task left depends on. It is
    in `lem decisions pending` and asked as `stages/choice.md` says; start a lead after his answer.
- **`blocked`**: the report says what the lead could not settle and what it tried. A missing
  tool, a base branch that does not build, a conflict with another task: settle it, then start a
  lead. An approach that failed twice goes to a fresh builder with a different approach, as
  `stages/build.md` says: add one line to the brief, `do not repeat:` and what the report says
  the two tries assumed. When only the owner can settle it, it is a step that is his to do:
  write the state `held` with that step, and tell him where he does it.
- **`building`**, or no new state block: the lead ended without its last step. Start a lead;
  it reads the state and the report and goes on. After a second such stop, write `blocked` and
  tell the owner what the reply or the session's screen shows.
- **`landing`, `open`, `landed`, `answered` or `dropped`**: the task went on, or ended, without
  this lead, and the reply is a stale wake-up (a lead that finished after a later step, a
  message that came late). Do nothing for it: no state, no lead. An ended task stays ended,
  `lem project state` refuses a move out of `landed`, `answered` or `dropped` and a lead's state
  over a task in `landing` or `open`, and `may-start`
  refuses a lead for a task in `landing`, `open` or an ended state. New work for it is a new
  ask (`/lem new`), with a slug of its own.
