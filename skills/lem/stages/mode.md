# "go alone", "go alone for all", "I am back"

Read when the owner says one of them, and at no other time. A task runs with him unless his
words say otherwise ("I should be able to say that all upcoming task work goes autonomous",
2026-11-18). His words go into the record as he typed them; no script can tell who typed, so
write `--by owner` only for words he typed in this session. A text for him says "without you",
never "alone": `lem project alone` is the lock of the machine.

**"go alone"** reaches the task he names, or the one this conversation is about; **"go alone for
all"** every task that did not end. When his words are not that plain ("I have to go, carry
on"), ask once in the terminal: "Run SLUG without you until you say 'I am back'? (y/n)".

1. `lem project mode SLUG alone --by owner --words "HIS WORDS"`, or `--all` in the place of SLUG.
2. Each choice of those tasks that waits for him and is no irreversible step (`lem decisions
   pending`): `lem decisions timeout SLUG N`, which takes it now. A lead in its `wait` sees the
   mode by itself and does the same.
3. A task `held` with `the criteria wait for the owner`: `lem criteria approve SLUG --file FILE
   --alone`, with the criteria as they stand and a flagged one as written, then start its lead
   (`stages/start.md`).
4. An interview that runs goes on without him: take your guess for each question left and log
   each, `lem decisions log SLUG --by lem --what "THE QUESTION" --chose "YOUR GUESS" --why WHY`.
   The personas' read runs, since nobody can skip it now, and `--alone` approves the criteria
   whatever it found: the read's answers go into the pull request.
5. Tell him in one line which tasks run without him, and that a step a later "no" cannot reverse
   and the merge still wait for him.

A task you open yourself while every task runs without him (the task for a red base of
`stages/land.md`) runs without him too: `lem project mode SLUG alone --by lem --words "WHY"`.

**"I am back"** reaches every task that runs without him, or the one he names:
`lem project mode --all with-owner --by owner --words "HIS WORDS"`. Then one line for each such
task: how many decisions were taken without him, whether its criteria were approved without
him, and `/lem status SLUG` for the rest. Nothing is undone: a choice taken while he was away
stands, and a wish of his that differs is a correction (`stages/choice.md`, step 3). An
irreversible step that waits goes to him now, as `stages/choice.md` says.
