# `im-away`, `im-back`

Read when the owner says that he is away or back again, and at no other time. He says whether
he is there, and Lem assumes nothing: "Owner either tells dnd or not, no assumptions" (2026-11-18).
`/lem im-away` and `/lem im-back` are his words, and so is a plain sentence that plainly says the
same ("I'm away", "I'm back", "I'm here again").
When his words are not that plain ("I have to go, carry on"), ask once in the terminal: "Mark you
away until you say /lem im-back? (y/n)".
His words go into the record as he typed them; no script can tell who typed, so write them only
for words he typed in this session. The same words typed in a need's companion are recorded
there, and reach you as the line `lem: the owner is away` (or `back`): a wake-up, whose fact is
his status in `lem companion due`'s `owner`. Take the steps below for it, all but the record.
A text for him says "without you", never "alone".

## Away

1. `lem project owner away --words "HIS WORDS"`. It marks the repository: every task that did not
   end runs without him from now, and so does each task opened while he is away. It takes at once
   each choice that waits for him and is no irreversible step, with the ladder's pick
   (`lem decisions away`), and the pull request is not green for each. A lead in its `wait` sees
   it by itself. From now no companion opens: `lem companion open` refuses while he is away.
2. A task `held` with `the criteria wait for the owner`: settle each flagged criterion as below,
   then `lem criteria approve SLUG --file FILE --alone` with the criteria as the ladder left
   them, and start its lead (`stages/start.md`). When their companion runs, it takes this step up
   to the approval, once step 4 told it, and the lead's start after it is yours (`stages/start.md`,
   "The queue").
3. An interview goes on without him: in its companion when one runs, once step 4 told it, and
   otherwise in this session, also for a request he types while he is away that takes an
   interview, with the steps of `stages/interview.md` and you as their actor. Take your guess for
   each question left and log each, `lem decisions log SLUG --by lem --what "THE QUESTION" --chose
   "YOUR GUESS" --why WHY`. The personas' read runs, since nobody can skip it now. Each criterion
   it flagged is settled as below, and then `--alone` approves the criteria. The read's answers go
   into the pull request.
4. **Each companion that runs**: `lem companion due` gives it. One whose choice step 1 took is
   under `close`: close it with the entry's `why`. Each other one is under `away`: send it one
   message that he is away (`open-task-session`), and record it, so that it is told once: `lem
   companion told-away SLUG --need NEED` (with `--choice N`). The companion of an irreversible
   choice stays open, since that choice still waits for him.
5. A request he types while he is away runs without a question to him: where a stage would ask
   him, take the safer read (the standard track, and careful in doubt) and log it.
6. Tell him in one line that the tasks go on without him, and that a step a later "no" cannot
   reverse and the merge still wait for him.

**At each of your turns while he is away** the files are the fact, also when the line from a
companion was lost: while `lem companion due`'s `owner` says away, steps 2 to 4 take what they did
not reach yet: each companion under `away`, and each `held` task whose wait has no approval after
it and no companion that runs.

**A flagged criterion without him** (one a persona called unexpected, confusing or wrong, or one
on which the two families split) is a decision in doubt whose personas answered and split. It
goes on from the dialectic of `stages/ladder.md`, level 3, and to the experts, level 4, when the
dialectic finds a break. Write the criterion into FILE as the level that settled it picked, and
log it with that level: `lem decisions log SLUG --what "criterion N" --option "AS YOU WROTE IT"
--option "AS THE PERSONA EXPECTED IT" --chose OPTION --by dialectic|experts --level
"personas=WHAT THEY SAID" --why WHY`. When no level settles it, it stays as you wrote it, with
`--by lead --unsettled`. Nothing waits for him: the pull request is not green in any case, since
he did not approve the criteria.

## Back

`lem project owner back --words "HIS WORDS"`: every task that ran without him comes back to him,
a night's too. Then one line for each such task: how many decisions were taken without him,
whether its criteria were approved without him, and `/lem status SLUG` for the rest. Nothing is
undone: a choice taken while he was away stands, and a wish of his that differs is a correction
(`stages/choice.md`, step 3). From now on a choice waits for his answer with no time limit.

Then `lem companion due`: its `open` gives one companion for each step a later "no" cannot
reverse that waited while he was away, also one whose card he closed before, and for each other
need that waits for him and whose companion he did not close. Open each, `lem companion open SLUG --need NEED` (with `--choice N`),
and say each `say` line.
