# The circuit breaker

Read by a lead, or a plan talk's defender, when the breaker trips, and at no other time. The build
asks the owner nothing: the ladder decides every choice (`stages/ladder.md`), its pick is taken, and
he reads it at the pull request. "I'd rather review the PR and request a fix then find a work
blocked on some question that automated anwers could answer right" (the owner, 2026-11-20). Only
the breaker stops a task, and only that task: the other tasks build on.

## When it trips

Two causes, and no others:

- **`irreversible`**: the next step cannot be reversed by a later "no", of one of four kinds: it
  destroys or rewrites data outside the worktree (`data`); it writes to a system outside the
  repository beyond what the settings already allow, such as the tracker's ticket (`system`); it
  sends something to a person (`person`); it spends money (`money`). No level of the ladder takes
  such a step.
- **`criteria`**: no option of the ladder keeps the outcome the owner approved. A pick that changes
  the RULE of an approved criterion is such a case. A pick that changes only its example is a
  criterion change with its record (`stages/build.md`, "A choice in the build"), and the pull
  request is not green for it.

A task that takes three hours where one was expected meets neither, and goes on: the review
document shows its time ("An overrun stops nothing", the owner, 2026-11-20). A builder that is not
the lead never trips it: it stops its task with the question in its report, and you take it from
there.

## How it trips

1. **Commit what the task has**, in the worktree: a dropped task's worktree goes, and only its
   branch stays. The script refuses a worktree with an uncommitted change of a tracked file.
2. **`handoff.md`** in the task directory, whole: what is settled, what is open, the next step, and
   what was tried and failed, each with its file and line. A fresh agent goes on from it, maybe a
   week later, and knows nothing else of your context.
3. **`breaker.md`** in the task directory, in the form of `SKILL_DIR/templates/breaker.md`, which
   says each part. Read `SKILL_DIR/prompts/writing.md` first. It is the one thing of the build that
   reaches the owner, far from the moment he thought about the task, often on his phone: it brings
   the context back before it asks anything. Today and After as two runs of one input, the case
   that broke with its chart, the root cause, the options as this or that in a table with what each
   leads to, your recommendation, what each level of the ladder said, and the assumptions. A
   picture of `media/` when the case shows on a screen. The board draws it as a page; write it as
   one, never as a bare question with a paragraph. The record keeps it as `breaker-N.md`, N the
   breaker's number, so each breaker of the task keeps its own document.
4. **Record it**:

   ```bash
   lem decisions --repo WORKTREE breaker SLUG --cause irreversible|criteria [--irreversible data|system|person|money]
   ```

   It refuses a document without one of its parts, a missing `handoff.md` and a second breaker while
   one waits; it records the stop with its number N and writes the state `held` with the line
   `breaker N waits for the owner`, which is what the board and Lem read.
5. **Then**, as a lead: `report.md` with the breaker under "held", as `stages/build.md` ends, and
   wait in this session for the owner (`prompts/session.md`, "While the owner is needed"), with one
   line: the document's title, that he can talk it through here, and his two other answers, `/lem
   park SLUG` and `/lem drop SLUG`. As a defender: stop; the lead's wait for the talk ends on the
   state, and the lead takes the breaker up in its session.

## After it

The board puts the document first on the task, and its "Waits for you" and a push to his phone
tell him. He answers one of three ways: he helps, in a talk about the document in the task's
session; he parks the task (`/lem park SLUG`); or he drops it (`/lem drop SLUG`). `/lem resume
SLUG` goes back to the talk after either. While he is away, the breaker also reaches his inbox with
the same three answers, and help, park or drop may come from there as well (`inbox-reply`): the
first answer counts, and it is his as if typed here. The board's row has Help, Park and Drop with
a note, and his pick there is his typed word too (`prompts/session.md`, "His answer on the
board"): Help brings his note as his first part of the talk, Drop is `/lem drop SLUG`, and Park the
board runs itself.

- **The talk.** You stand in for the lead that tripped it, or you are that lead: answer from the
  document, `handoff.md` and the code. "What do the experts say?" is the document's line of the
  ladder; his "ask them again" is `load-skill` of `lem-ask-expert` with the question in words, and
  the dialectic and the panel are his to call the same way.
- **His decision** is one record: `lem decisions log SLUG --by owner --breaker N --what WHAT
  --chose "WHAT HE DECIDED" --why "HIS REASON, IN HIS WORDS"`, with `--words` for his own words
  when they are not the `--chose` text; after his Help on the board, `--why` also names its record:
  its key, `via` and `device`. When you cannot tell what he decided, ask him again. Then
  build what he decided, in this session, from `handoff.md`, the breaker's document (`breaker-N.md`)
  and that record. A
  criterion his decision changes gets its record, `lem decisions criterion ... --decision ID`, with
  his decision's number: the change is his, and the pull request is not held back for it.
- **He leaves the talk with no decision**: take nothing; the breaker waits, and the board's row
  brings him back to this session. When the talk began with his Help on the board, its record hides
  the row until the next state block: write the breaker's held block again, with your one line to
  his note, so that the row comes back under a new key, with Help, Park and Drop:

  ```bash
  lem project state SLUG held "breaker N waits for the owner" "YOUR ONE LINE TO HIS NOTE"
  ```
