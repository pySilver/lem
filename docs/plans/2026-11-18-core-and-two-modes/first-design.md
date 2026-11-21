# Design: the mode of a task (plan task 2) and the ladder of opinions (plan task 3)

Snapshot read: `/Users/Silver/Projects/GitHub/lem/.claude/worktrees/diet-run` at `cfc4831`. Every
line number below is in that snapshot. Words are `wc -w` at that commit; a number after the change
is labeled "estimate" until a builder measures it.

## For the owner

One question only. Everything else is decided below as the session's, open to him.

**A. Does a decision that the gate or the personas settled reach him as a card when the task runs
with him?**

1. You type `/lem add a gift note to the order export` and stay at the desk. The task runs with you.
2. In the build, the lead meets a choice: "Where does the note go in the row: the last column, or
   after the price?" The lead picks "the last column".
3. The gate finds no ruling on it. Three personas answer, and all three pick "the last column".

What should happen?

- **A1 (recommended): it is taken with no card.** You see it on the board and in `decisions.md`, and
  the pull request stays green. Reason: your rule of 2026-11-16, "if its clear choice - pick it, log
  the event so it will be presented at PR review time", and it is what Lem does today.
- **A2: a card opens for it.** "The last column" is marked as the pick. With no answer in 15 minutes
  it is taken, and the pull request is not green for it. This is the plan's sentence "With the owner,
  the result of the ladder is the card he sees", read word for word.
- **A3: a card opens for your information only.** With no answer in 15 minutes it is taken, and the
  pull request stays green.

Reply with A1, A2 or A3. The design below is built for A1. A2 or A3 is one constant
(`CARD_FROM` in `decisions.py`) and one sentence of `stages/ladder.md`.

Why this is asked and not decided: it sets how many cards he reads in the mode he chose in order to
see decisions ("Sometimes I would love to know the decisions taken before implementation"), and
only he knows what that sentence meant. With A1 he sees fewer cards than the plan's text promises.
With A2 he sees more cards than today.

## Where the plan's wording and the code disagree

1. **"alone" is a name in use.** `lem project alone` is the lock for commands that need the machine
   to themselves (`project.py:2250`, parser `2422`), with the setting `checks.alone`, the block
   `tests/lem-alone.sh`, and the pull request text "(alone, under the lock)" (`land.py:2245`,
   `2305`). Plan task 2 says "`lem project` writes it". Proposal: the command is `lem project mode`.
   The record keeps his word `alone` as the mode's value. Every text for a person says "without the
   owner", never "alone". Task 1b may want to rename the lock, but that is not decided here.
2. **The gate comes before the lead in the plan's list, but the gate reads the options.** The lead's
   judge prompt reads a question file with its options (`skills/lem-gate/references/judge.md`). So
   the lead writes the options and its pick first, and then the gate judges. Level 1 never settles
   a decision. A decision the lead may settle alone never enters the ladder: it is the lead's own,
   as today (`stages/build.md:102-103`).
3. **The dialectic has no countable result today.** `skills/lem-dialectic/SKILL.md:31-46` ends in a
   synthesis and a check that one model writes. The ladder needs a count, so the design gives the
   two agents a fixed answer form, and a script checks each cite.
4. **"A pull request of a task that ran alone is not green" (plan task 2).** The design derives "not
   green" from what was decided without him. A task that ran without him and in which nothing was
   decided without him is green, and one line says that it ran without him. A "not green" that names
   nothing would teach him to merge past "not green". This is a story that ends with nobody worse
   off: the same pull request as with him at the desk. So it is decided, not asked.
5. **Experts "at the start of every wait" (his pick of 2026-11-16, the ruling "Two experts answer a choice that waits for him", now under "Replaced, not in force" in "The build asks him nothing, and the ladder always decides" (`docs/rulings/rulings.md`)).** The plan
   moves the experts to level 4, before the card ("This replaces the card with the experts' advice
   at the start of the wait"). The second half of that ruling stays: a choice the experts decided
   without him is not green.
6. **The night.** `night: yes` makes `decisions.py ask` refuse (`decisions.py:484-496`), and the
   plan stops at the decision (`stages/plan.md:194-198`, `stages/night.md:29-39`). The design leaves
   both as they are. Task 5 replaces them with the mode (see "A night run").
7. **Not in any task of the plan:** his ruling "the plan talk ... may cancel further execution if
   there are signs that the design is wrong" ("The plan talk stays as one plan, one reviewer and a closed list, and it can stop a task", now in the bullet "The plan talk is a pair in a companion that closes after it, and it can stop a task" of `docs/rulings/rulings.md`). `stages/talk.md` has no such
   stop. The ladder does not cover it. This is a note for the orchestrator.
8. **Not in scope, seen on the way:** `skills/lem-gate/references/judge.md` says "no shopper, merchant
   or operator would notice it" and "a probe on the test stack". Those are one project's words in a
   shipped skill. Task T4 below changes them to "nobody of the project's cast", because the gate
   now decides.

## The mode of a task

### Where it lives, its values, who writes it, the event

- **The record is an event, `task.mode`**, in the event log that `project.py` keeps
  (`append_event`, `project.py:1670-1684`). Its fields: `mode` (`with-owner` or `alone`), `by`
  (`owner` or `lem`), `words` (his words, verbatim, or Lem's reason when `by` is `lem`), and `all`
  (true when one sentence of his set every open task). `lem project log SLUG task.mode` is refused,
  as `task.state` is (`project.py:1845-1846`): "task.mode is written by `lem project mode`".
- **`lem project tasks` gives `mode` and `mode_since`** for each task, from the newest `task.mode`
  of that task, read in the same pass that finds `plan.talk` and `investigation`
  (`newest_events`, `project.py:2073-2089`; `read_tasks`, `2107-2146`). A task with no `task.mode`
  event is `with-owner`, so every task that an older Lem opened reads as it did.
- **Why an event and not a line in `brief.md`:** the interview runs before the brief exists
  (`stages/new.md:137`, step 6), and he may say "go alone" during the interview. The board draws
  the event with no new command. The rejected alternative, a line in `brief.md` such as `night:
  yes`: it does not exist yet during the interview, and a lead that already runs does not read its
  brief again.
- **Who writes it:** whoever hears his words in his own session writes `--by owner`: Lem, or a lead
  or a defender whose session he types in (`prompts/lead.md` step 5 already tells a lead to write
  down his words). `--by lem` is for two cases only: the night run (task 5), and a task that Lem
  opens itself while every open task runs without him (the task for a red base,
  `stages/land.md:103`). No script can tell who typed, so the stage texts say this.

The commands (`project.py`):

```bash
lem project mode SLUG alone --by owner --words "go alone"
lem project mode --all alone --by owner --words "go alone for all"
lem project mode --all with-owner --by owner --words "I am back"
```

- `SLUG` and `--all` are one or the other. `--all` writes one event for each task that is not
  `landed`, `answered` or `dropped` (`ENDED`, `project.py:317`) and whose mode is not that mode
  already, and prints the slugs it wrote. A task with the same mode gets no event.
- Refusals, each with exit 1: a value that is not `with-owner` or `alone` (the message names both);
  `--words` missing or empty ("his words, as he typed them"); `--by` other than `owner` or `lem`;
  an ended task by its slug ("an ended task stays ended; new work is a new ask"), as
  `project.py:1720-1724` says for a state.
- Output: `{"tasks": [{"slug", "mode", "was"}], "since": TS}`.

"I am back" applies to every task that runs without him (`--all`): it is his word as a person. For
one task, his words name it ("I am back for gift-note"), and Lem writes that task only. The session's
decision; the rejected alternative, "I am back" for the one task of the conversation: he leaves the
house for every task, not for one.

"Go alone for all" covers the tasks that exist when he says it, and a task that Lem opens itself
while every open task runs without him. A task he asks for after it starts with him: he typed it,
so he is there. The session's decision; the rejected alternative, a switch for the whole session:
it is a second record to keep, and it needs a second "I am back".

When his words are not plain ("I have to go, carry on"), Lem asks one fixed question in the
terminal: "Run gift-note without you until you say 'I am back'? (y/n)". A fixed choice with no
context stays in the terminal by his own exception.

### What Lem does at the moment of the words (`stages/mode.md`, new, Lem's)

Lem reads this file only when he says one of the three sentences, so no other path pays for it.

**"go alone"**, for each task the words reach:

1. `lem project mode ...` as above.
2. Each choice of the task whose card waits and is not irreversible: `lem decisions timeout SLUG N`.
   This takes the ladder's pick at once (see "timeout" below). It replaces `settle --away`.
3. A task `held` with `the criteria wait for the owner`: `lem criteria approve SLUG --file FILE
   --alone`, then start its lead (`stages/start.md`).
4. A task whose interview runs: go on as `stages/interview.md` says for a task without him.
5. One line to him: which tasks run without him, that a step a later "no" cannot reverse still waits
   for him, and that the merge stays as `branch.land` says.

**"I am back"**:

1. `lem project mode --all with-owner ...`.
2. One line for each task that ran without him: how many choices were taken without him, whether
   Lem approved its criteria, and `/lem status SLUG` for the details. Nothing is undone. A choice
   taken while he was away stays taken. A different wish of his is a correction: for the lead while
   the task builds, and a new ask after that (`stages/choice.md`, step 3, today's rule).
3. A card that waits now (an irreversible step, or a ladder that ended since): show it now
   (`stages/choice.md`).

**A ladder that climbs at the moment of the words** reads the mode when it ends, not when it began.
If he said "go alone" while the personas answered, the end takes the result with no card. If he
said "I am back" while the experts answered, the end is a card with its wait (when the level makes
a card, see the ladder's end). The script reads the mode under the record's lock in the same write
as the end, so each choice has one outcome.

### What "alone" changes, step by step

| Step | With the owner (today) | Alone |
| --- | --- | --- |
| The interview (`stages/interview.md` step 2) | one question at a time, his answer | Lem takes its own guess for each question left, and logs it: `lem decisions log SLUG --by lem --interview --what "QUESTION" --chose "GUESS" --why "WHY"`. The type question (fix or feat, `stages/new.md:54-61`) is one of them. |
| The skip of the persona read (`interview.md` step 5) | his y/n when every criterion names only him | never asked: the read always runs |
| The persona read of the criteria | runs | runs, the same |
| His yes (`interview.md` steps 6 and 7) | his approval, `approve --file` | `lem criteria approve SLUG --file FILE --alone`, whatever the read found. A flagged criterion stays as written, and the read's answers go in the pull request. |
| A complete request, read flagged, or `request by: someone else` (`plan.md` step 1, `:73-86`) | `held`, the criteria wait for him | the lead approves with `lem criteria approve SLUG --file PLAN --alone` and builds |
| A plan that needs a plan talk | Lem opens the companion; the talk needs no owner | the same. Its open questions and design choices take the ladder. |
| A choice in the plan or the build | the ladder, then a card when it went past the personas (A1) | the ladder, and nothing waits |
| A step that a later "no" cannot reverse | waits for his word, with no end | the same; the question also goes to his away channel, as `ask-owner` says |
| `stop after the plan: yes` (`/lem plan`) | stops at the plan | stops at the plan: he asked to read it. Lem says so in its line. |
| `held` for one more fact (an investigation), or a step of his | waits | waits: these are no decisions with options |
| The landing | `propose`, then `branch.land` | the same. A task that is not green is never merged by an agent (`may_merge`, `land.py:2567-2569`). |

The session's decision on a flagged criterion: Lem keeps it as written. The rejected alternative, a
flagged criterion takes the ladder: the personas answered it already, so level 2 would repeat
itself, and the stages forbid an agent's rewrite of his contract before he reads it
(the session's decision "Where the stages keep what the amendment of 2026-11-16 says otherwise", whose parts are in `docs/rulings/history.md`).

What alone never changes: a step that a later "no" cannot reverse waits for him in both modes, and
`branch.land` decides who merges in both modes.

`criteria.py` (`cmd_approve`, `criteria.py:664-720`; `main`, `723-753`) gets `--alone`:

- It writes `by: "alone"` and logs `criteria.approved by=alone`.
- It is refused when the task's mode is `with-owner`: "gift-note runs with the owner: the owner's
  yes approves its criteria (`stages/interview.md`, step 7)".
- It is refused when an approval exists that is not Lem's small-change approval (`by: lem`): "approval
  N of SLUG is the owner's (or a read's): a criterion changes through its record". It is allowed
  after `by: lem`, since a small change that turned out to be a full change needs its full
  approval (`stages/new.md:225-230`).
- It is refused with `--small` or `--read` ("one of the three"), and for `Size: small`.
- An owner's approval after it is always allowed, as today. It takes over: the newest approval is
  then his.

`decisions.py log` gets `--interview`: allowed only with `--by lem`, and refused while the task's
mode is `with-owner` ("the owner answers the interview himself while the task runs with him"). It
adds `"interview": true` to the line.

### What the pull request says (`land.py`)

`land.py` derives every line from the records. No agent writes them. The rules:

- **Criteria.** The newest approval is `by: alone` → reason: `the owner did not approve the
  criteria: Lem approved them on DATE while the task ran without the owner`, plus `; the personas'
  read flagged criterion N` (or `the two families split`) when the newest read says so, and `; the
  request was written by someone else` when `someone_elses(task)` (`land.py:1120`). The two refusals
  of `propose` at `land.py:2423` (a flagged read with no approval of his) and `land.py:2432` (someone
  else's request) take an `alone` approval at or after the read as enough to go on, so that the
  request is proposed, not green.
- **Choices** (see the ladder, "What is not green").
- **The first line** names what he did not approve, and the span when the task ran without him:

```
**Not green.** It ran without the owner from 2026-11-18 14:02 UTC (the owner's words: "go alone"). The owner did not approve: the criteria, choice 3, choice 4.

- the owner did not approve the criteria: Lem approved them on 2026-11-18 while the task ran without the owner; the personas' read flagged criterion 2
- choice 3 was taken without the owner (Where the note goes in the row): "after the price", by the experts, both for it, while the task ran without the owner. Fable: ... Astra: ...
- choice 4 was taken without the owner (Which note wins): "the first", the lead's pick: no level of the ladder settled it
- ... every other reason, as today
```

With him at the desk and one card he did not answer:

```
**Not green.** The owner did not approve: choice 3.

- choice 3 was taken without the owner (Where the note goes in the row): "after the price", by the dialectic, 2 points for it and no break, after the owner's wait of 15 minutes ended with no answer
```

A task that ran without him, with nothing decided without him:

```
**Green.** The checks passed with the bar where it was, the review left no must-fix, no criterion changed, and nothing that was the owner's was decided without the owner.

It ran without the owner from 2026-11-18 14:02 UTC (the owner's words: "go alone"); nothing was decided without the owner.
```

The span is read from the task's `task.mode` events (`events_of`, `land.py:1596`): "from T" or "from
T to T2", one clause for each span, in UTC. `GREEN` (`land.py:442`) becomes the sentence above. The
seven things of `stages/land.md:185-189` change one item: "no choice was taken by timeout or by the
experts" becomes "no choice past the personas was taken without the owner, and Lem approved no
criteria while the task ran without him". `small_text` (`land.py:2222-2271`) does not change: a
small change has no decision and no full approval.

### With the owner: a card he does not answer

The card's wait (`flow.decision_wait`, 15 minutes unless the project says otherwise, `project.py:363`)
starts when the ladder ends with a card. When it ends with no answer, `timeout` takes the ladder's
pick, as if the task ran without him for that one decision, and the pull request is not green for it.

| Today | After |
| --- | --- |
| `wait` (`decisions.py:589-607`) | stays. It also returns when the task's mode becomes `alone` (`"ended": "the task runs without the owner now"`, `next`: `timeout`) and when he asked for all opinions (`"ended": "all opinions"`, `next`: the level that is due). |
| `timeout` (`650-664`) | stays. It takes the ladder's pick (the `ended` line's `chose`). It is refused while the ladder climbs and while the wait runs, except when the task's mode is `alone`. It is always refused for an irreversible step. A record of the form before the ladder takes, as today, the experts' shared pick or the recommended option (`ending`, `367-372`). |
| `advise` (`524-555`) | goes. `lem decisions experts` records level 4 before the card. On a choice of the form before the ladder that still waits, `experts` writes an `advised` line as `advise` did, so the experts that an older lead started still count. |
| `settle --away` (`667-694`) | goes. His "go alone" is the word that he is away (`lem project mode`), and `timeout` then takes the pick at once. The rule "away on two facts" (`harness/claude-code.md:107-110`, `stages/choice.md:56-65`) goes with it. |
| `advise` and `settle` as words | each stays one release as a stub that refuses and names the new form ("`settle` is gone: the owner's 'go alone' is `lem project mode SLUG alone`, and then `lem decisions timeout SLUG N` takes the ladder's pick at once"). A later change may drop the stubs. |

### A night run (task 5)

"Alone" covers the part of `night: yes` that is about decisions, and changes it as he asked: a night
no longer ends its draft on a decision, it takes it by the ladder, and the pull request is not green
for it ("Yes this is what I want", "The lessons, the retro and Jev stay; a night run ends as a pull request; naps are not shown", `docs/rulings/rulings.md`). The differences that stay task 5's:

1. What the night picks (no item in reach of a topic, no item another branch holds,
   `stages/night.md:11-24`) is not the mode's. A task by day may run alone and be careful.
2. `night: yes` also means `stop after the plan: yes` today (`night.md:25-28`). The mode stops
   nothing.
3. The brake counts drafts (`night.md:7-10`). Task 5 changes it to pull requests.
4. A night has no session in which he could say "I am back". The next morning's `/lem` is where he
   says it.

So tasks 2 and 3 leave the `night: yes` refusal in `decisions.py:484-496` and the exception in
`stages/plan.md:194-198` as they are. Task 5 opens each night task with `lem project mode SLUG alone
--by lem --words "the night run"` and removes both.

## The ladder of opinions

### Which decisions enter it

The rule of today stays (`stages/build.md:102-114`, `stages/plan.md:164-170`):

- **The lead's own**, with `lem decisions log SLUG --by lead --why ... --undo ...` and no ladder:
  the criteria and the directions stay true, and no option costs a person more than another. A
  ruling, a test or a probe that the lead reads itself is quoted in `--why`.
- **The ladder**: a criterion or a direction would change, or each option costs a person something
  and nothing the lead read answers it. Also, always, a question that the plan talk left open, and a
  design choice of the talk (`stages/talk.md:48-50`, `86-88`).
- **The ladder with `--intent`**: a question of what the owner meant, or of taste. No agent answers
  that for him (`skills/lem-panel/SKILL.md:22-24`). Levels 2 to 4 do not run unless he asks for all
  opinions. With him, it is a card after level 0. Without him, the lead's pick stands (level 5), not
  green.

The separate bullet "a claim that can be argued both ways → the dialectic first" (`plan.md:167-168`)
goes: the dialectic is level 3 of the ladder now.

A builder that is not the lead meets such a choice and asks nobody: it stops its task with the
question in its report (`build.md:164-166`, unchanged).

Today's personas step logs a clear answer with `log --by personas` (`build.md:109-112`). That step is
level 2 now, so `log --by personas` and `criterion --by personas` are refused, with the message
"a pick of the personas is level 2 of the ladder now: open the choice with `lem decisions ask`, and
name it with `criterion --choice N` (`stages/ladder.md`)". The lines that an older Lem wrote with `by:
personas` still read (`decided`, `land.py:2153`; `change_line`, `2094`).

### The levels, and the count that stops each

Each level's answer is a file in the fixed form below, which a script reads and counts. No model
judges a level's result. The "pick" is the lead's pick at level 1 (`recommended` in the record), and
"changed" always compares with it.

| Level | Who | Answers | Stops the ladder when (the count) | Agents it starts |
| --- | --- | --- | --- | --- |
| 0, the gate | the gate's judge (`lem-gate`), a fresh read-only agent | `decided` + the option a ruling gives, `checkable` + the check, `cheap`, or `held` | `decided`, `checkable` (with the option the check showed) or `cheap` (the lead's pick) | 1 |
| 1, the lead | the lead | the options, its pick, the facts | never: a decision the lead may settle alone does not enter | 0 |
| 2, the personas | the panel's persona agents (`lem-panel`, "In the ladder") | per persona and family: `pick` + `sure`, `none fits`, or `not affected` | votes from 2 personas or more, no `none fits`, and every vote for the lead's pick | 1 brief check + N personas (N = 2 to 3), + 1 practice scout when `facts.md` names a fact |
| 3, the dialectic | two read-only agents of the lead, for and against the option the personas voted for most | `hold` lines and `break` lines, each with a cite | at least 1 checked hold, and 0 checked breaks | 2 |
| 4, the experts | the two seats of `seats.experts` (`lem-ask-expert`) | each `pick`, `none fits`, or no answer | both pick the same option | 2 |
| 5 | nobody | none | always: the lead's pick stands, not green | 0 |

**Level 0.** A verdict of a judge that did not write the question, as the gate is today
(`skills/lem-gate/SKILL.md:38-58`). A ruling decides because it is his. A check decides because it
is a fact. "Cheap" decides because the gate's own rule says so, and he kept the gate as a part that
"may decide" ("The question gate stays, hidden, and may decide", `docs/rulings/rulings.md`).

**Level 2, a vote.** A vote is an answer whose last lines are `pick: OPTION` (word for word) and
`sure: sure` or `sure: leaning`. `sure: no preference` and `not affected` are no vote. `none fits` is a
vote against every option, so it blocks the stop. Each family's answer is one vote, so a persona of
two families gives two. "Votes from 2 personas or more" is the panel's own floor ("Two is the floor:
with one persona there is no second view", `lem-panel/SKILL.md:75-76`). The session's choices:

- "Leaning" counts as a vote: it names a side. The rejected alternative, only "sure" counts: with 2
  to 3 personas the level would almost never stop, and today's "nobody in doubt"
  (`build.md:109`) was never a count. This is a guess, not a measurement.
- Unanimity has to be for the lead's pick. Personas who all pick another option do not stop the
  ladder: the dialectic then tests their option. His words are "if no clear consensus reached", and
  the lead plus the personas is the consensus so far. The rejected alternative, unanimity for any
  option stops: a pick that the code-reading agent did not choose would then be taken on the votes
  of agents that read no code.
- "The option with the most votes" is the `lean`: on a tie, the lead's pick when it is among the
  tied, else the first tied option in the record's order; with no vote, the lead's pick.

In a lead there is no paired Codex, so one family answers (`stages/plan.md:63-64`). Where the runner
has a paired agent of the other family (Lem's session, a companion), both families answer, and the
count reads both.

**Level 3, the dialectic.** The "for" agent writes up to 5 holds, the "against" agent up to 5
breaks, in this form:

```
hold: ONE SENTENCE
cite: PATH:LINE "THE WORDS AT THAT LINE"
```

```
break: ONE SENTENCE
breaks: criterion N | direction N | ruling FILE | it cannot be built
cite: PATH:LINE "THE WORDS AT THAT LINE"
```

or `no hold`, `no break`. A break is only one of those four kinds. A cost or a risk is no break: the
personas weighed those. The script checks each cite: `PATH` inside the checkout, `LINE` in the file,
the quoted words (3 words or more) in lines `LINE-2` to `LINE+2`, compared with each run of spaces as
one. It also checks that `criterion N` names an approved criterion, that `direction N` is a line of
`directions.md`, and that `ruling FILE` is a file of `docs/rulings`. A point whose cite does not check
is dropped and named in the record. "Clear" is at least 1 checked hold and 0 checked breaks. The
reasons: one checked break means the option fails his contract, a direction, a ruling, or cannot be
built, and no lead should take that on its own; an option for which no agent can cite one line is
no clear result. The tolerance of 2 lines and the cap of 5 are guesses, not measurements.

The two agents are started with `fan-out`, read-only, on the model the harness file names (Opus at
high, his own example, in "In doubt, a decision climbs a ladder of opinions, and a count decides, not a model." (`docs/rulings/rulings.md`)). They run as subagents of the lead, as he left it for
now.

**Level 4.** Today's rule for the experts' agreement (`shared`, `decisions.py:358-364`): both
answered, and both picked one option. It may be another option than the lead's pick: then
`changed` is true. An expert that does not answer twice is recorded as silent, and the level does
not stop.

The experts' brief becomes neutral, as the panel's brief is (`lem-panel/SKILL.md:111-113`): no
recommended option and no answers of the levels before. Today it holds both
(`experts.py:239-241`). The reason: an agreement with what they read is no second opinion, and the
count of "changed the pick" is to measure each level on its own. The session's choice; the rejected
alternative, the brief shows the earlier levels: the experts would then confirm the personas, and
the log could not tell which of the two serves better, which he left open ("I'm not sure if
personas are better than two experts").

### "All opinions"

- **How he says it:** on the card, the option "All opinions: run the levels that did not run, and
  ask me again". Or in words in Lem's session, "all opinions for choice 3 of gift-note", or "all
  opinions" while one card waits. Lem writes `lem decisions all SLUG N --words "HIS WORDS"`.
- **What it changes:** the choice climbs again. Each level that did not run is due, in order (0, 2,
  3, 4). The levels that ran do not run again. The result is still the first level in order that
  settles, so "all opinions" adds information and never changes which rule decides. When the last
  level is in, the end is written again, and with him a new card shows every level with a new wait.
- It is for one decision. The rejected alternative, a mode for every decision of a task: up to 8
  agents on each decision, and he did not ask for it.

### The gate at level 0

- **What it reads:** the judge's own list (`judge.md`): the rulings folder `docs/rulings` (fixed by
  task 1b), the review profile's rejected findings, the backlog, the active plan, `AGENTS.md` and
  `.claude/rules`. The question is `choices/N.md` in the task directory, which `lem decisions ask`
  writes: the what, the case, the cause and the options, with no pick. The judge's reply is written
  word for word into `choices/N.gate.md`, and its first line is the verdict. `judge.md` adds one line
  to its form: for `decided`, `option: THE OPTION, WORD FOR WORD`.
- **How it is logged:** `lem decisions gate SLUG N` reads `choices/N.gate.md` and writes the level
  line, `by: gate` when it settles. For `checkable` the lead runs the check that the judge named, then
  gives `--chose OPTION --shown "WHAT THE CHECK SHOWED"`.
- **Shadow mode goes.** He ruled that the gate "should stay as hidden feature" and that its decisions
  land in `decisions.md` ("The question gate stays, hidden, and may decide", `docs/rulings/rulings.md`). A gate in shadow mode decides nothing, which is the
  opposite.
- **Its log goes.** `skills/lem-gate/scripts/gate-log.py` (164 lines), its row in `bin/lem:36`, and its
  part of `tests/test-gate-panel.sh` (lines 11-47) go. The verdict is a line of `decisions.jsonl`
  now, beside his answer when he answered, which is the comparison the log was for. `lem decisions
  levels` counts the verdicts. A `decide-gate.jsonl` left in `.lem/state/` is read by nobody and goes
  with the state folder.
- **The step "is this answer a durable ruling?" goes**, with `references/durable.md` (249 words). It
  uses Jev, and the plan gives Jev one place, the correction queue. In its place the card has one
  more control, "also a rule for later tasks", off by default. When he turns it on, `answer` writes
  `"rule": true`. The lead then writes `docs/rulings/SLUG-N.md` in the ruling format of
  `lem-gate/SKILL.md:88-93` and commits it on the task's branch with the work that builds the option.
  So it reaches the base branch through the review, and the pull request lists it. The session's
  choice; the rejected alternative, keep the Jev step: it is a model's judgment on his words, which
  he doubted, and a ruling is a product decision of his.
- The panel's question mode keeps its framing check with Jev for `/lem panel` by hand
  (`lem-panel/SKILL.md:196-202`). The ladder does not use it.

### The record (`decisions.jsonl`)

A record of the form before the ladder has no `ladder` key, and every command reads it as today.
The new form adds lines with new `kind` values. Each line is also the event `decision.KIND`, as today
(`decisions.py:318-319`).

```jsonc
// opens it: today's `asked` line, with `ladder`, `intent`, and no deadline yet
{"id": 3, "at": "...", "kind": "asked", "ladder": true, "what": "...", "case": "1. ...\n2. ...", "case_was": "derived",
 "cause": "...", "options": ["the last column", "after the price"], "recommended": "the last column", "why": "...",
 "intent": false, "irreversible": null, "wait_minutes": null, "deadline": null}
// one line for each level that ran
{"id": 3, "at": "...", "kind": "level", "level": 0, "name": "gate", "verdict": "held", "cite": "no ruling covers it",
 "answer": null, "settled": false, "changed": false}
{"id": 3, "at": "...", "kind": "level", "level": 2, "name": "personas", "dir": "PANEL_DIR",
 "votes": [{"persona": "merchant", "family": "opus", "pick": "after the price", "sure": "sure"}, ...],
 "for": 1, "against": 1, "no_vote": 0, "lean": "after the price", "answer": null, "settled": false, "changed": false}
{"id": 3, "at": "...", "kind": "level", "level": 3, "name": "dialectic", "option": "after the price",
 "holds": [{"text": "...", "cite": "export.py:41 \"...\"", "checked": true}],
 "breaks": [{"text": "...", "breaks": "criterion 2", "cite": "...", "checked": false, "why": "the words are not at line 88"}],
 "for": 1, "against": 0, "answer": "after the price", "settled": true, "changed": true}
// the experts: one line each, and the level line in the write of the second
{"id": 3, "at": "...", "kind": "expert", "expert": "fable", "pick": "after the price", "why": "..."}
{"id": 3, "at": "...", "kind": "expert", "expert": "astra", "silent": true, "why": "did not start twice"}
{"id": 3, "at": "...", "kind": "level", "level": 4, "name": "experts", "picks": {"fable": "after the price", "astra": null},
 "answer": null, "settled": false, "changed": false}
// the end, written by the script in the write of the level that settles, or of level 4
{"id": 3, "at": "...", "kind": "ended", "level": 3, "by": "dialectic", "chose": "after the price", "mode": "with-owner",
 "card": true, "wait_minutes": 15, "deadline": "..."}
// the owner asked for all opinions: it climbs again
{"id": 3, "at": "...", "kind": "all", "words": "all opinions"}
// as today, with `rule` when he turned it on, and the new `timeout`
{"id": 3, "at": "...", "kind": "answered", "chose": "the last column", "words": "...", "rule": true}
{"id": 3, "at": "...", "kind": "timeout", "chose": "after the price", "by": "dialectic", "level": 3, "early": true}
```

- **States** (`decisions()`, today `219-243`): `climbs` (opened, or after `all`), `waits` (ended with a
  card), `taken` (ended with no card), `answered`, `timeout`, and `late` as today. The old states
  `settled` and `timeout by experts` stay for old records.
- **The end** is written by the script, never by an agent: in the write of the level that settles,
  or in the write of level 4 when it does not (then `level: 5`, `by: lead`, `chose` = the lead's
  pick). For `--intent`, the write of level 0 ends at 5 when the gate does not settle.
- **A card or not** (`card`), by the mode read under the lock at the end:
  - irreversible: always a card with no deadline, in both modes;
  - with the owner: a card when the settling level is 3 or higher (`CARD_FROM = 3`, answer A1),
    with `deadline` = the end + `flow.decision_wait`;
  - alone: no card.
- **`changed`** is true when the level's answer is an option and not the lead's pick. `lean` keeps the
  side of a level that did not settle.
- **The level of a settled level** is never written twice: a second `personas` on the same choice is
  refused.

### What is not green

For a choice of the new form, a line of `not_green` (`land.py:2029-2075`) when the choice ended at
level 3, 4 or 5 and has no answer of his (state `taken` or `timeout`). The form is `choice N was
taken without the owner (WHAT): "CHOSE", BY-WHOM-AND-COUNT, WHEN`, where WHEN is "while the task ran
without the owner", "after the owner's wait of 15 minutes ended with no answer", or "when the owner
said 'go alone', before the wait ended" (`early`). A choice that ended at level 0 or 2 is no cause of
not green. Neither is one he answered.

Why level 3 too, when the plan names only level 5: today everything past the personas that he did
not answer is not green (timeout and experts, `land.py:2062-2074`). The dialectic is two subagents of
the lead, which is less independent than the two experts. A green result from the weaker look would
be odd. The session's choice.

`decided()` (`land.py:2128-2158`) gets one form per level, for example: `- Where the note goes in
the row: "the last column", by the personas: 3 of 3 votes, as the lead picked.` / `..., by the gate:
a ruling (docs/rulings/export-columns.md, "New columns go last").` / `..., the lead's pick: no level
settled it (the personas split 1 to 1, the dialectic found 1 break, the experts split).` `TAKEN_BY`
(`land.py:440`) gets `gate` and `dialectic`. The refusal of `propose` while a choice waits
(`land.py:2455-2466`) also covers a choice that climbs: "choice 3 of gift-note climbs the ladder:
level 3 is due (`stages/ladder.md`)".

### The `lem decisions` commands after the change

| Command | Arguments | Refuses (exit 1, key words of the message) |
| --- | --- | --- |
| `log` | `SLUG --what --chose --why --by lead\|owner\|lem [--said] [--undo] [--interview]` | `--by personas` ("level 2 of the ladder now"); `--interview` without `--by lem`, or while the mode is `with-owner` |
| `criterion` | as today, `(--choice ID \| --by lead)` | `--by personas` (as above); `--choice` whose state is not `answered`, `timeout`, `taken` or old `settled` |
| `changes` | `SLUG` | as today |
| `ask` | `SLUG --what --case --case-was reproduced\|derived --cause --option ... --recommended OPTION --why [--intent] [--irreversible data\|system\|person\|money] [--said]` | as today (`steps`, `--case-was`, two options, `--recommended` an option, the night line); `--said` is optional now: a lead of the stage text before it passes it, and it is kept for the card |
| `gate` | `SLUG N [--chose OPTION --shown TEXT]`; reads `choices/N.gate.md` | a choice of the form before ("of the form before the ladder"); not `climbs`; level 0 written already; the file is missing or its first line is no verdict; `decided` with no `option:` line or an option not word for word; `checkable` without `--chose` and `--shown`; `--chose` with another verdict |
| `personas` | `SLUG N --dir PANEL_DIR`; reads `PANEL_DIR/answers/PERSONA.FAMILY.md` | not `climbs`; level 0 missing; level 2 written; no answer file; an answer not in the form ("PATH: ask that persona once more with the same brief; when its second answer is refused too, move the file out of answers/ and say so"); a pick that is no option |
| `dialectic` | `SLUG N --brief` writes `choices/N.dialectic.md` with the option under test; `SLUG N` reads `choices/N.for.md` and `choices/N.against.md` | not `climbs`; level 2 missing; level 2 settled with no `all`; level 3 written; a file missing; a file not in the form (once more, as above); a cite path outside the checkout |
| `experts` | `SLUG N --expert fable\|astra (--pick OPTION \| --none \| --silent) --why TEXT` | new form: not `climbs`, or level 4 not due ("level K is due"); the expert answered already; a pick not an option. Form before: as `advise` did; `--silent` refused there ("with one advice the end of the wait takes the recommended option") |
| `all` | `SLUG N [--words TEXT]` | form before; state `answered`, `timeout` or `taken` ("it was taken: a change now is a correction"); every level ran ("the card shows each") |
| `pending` | `[SLUG]` | as today. `waiting` holds the cards (`waits`), each with its levels |
| `wait` | `SLUG N [--seconds N]` | as today; returns for `answered`, `taken`, `timeout`, the end of the wait, the mode `alone`, `all`, a task that ended |
| `answer` | `SLUG N (--chose OPTION \| --instead TEXT) [--words] [--why] [--rule]` | as today. Allowed while the choice climbs too: his word ends it, and a level after it is refused |
| `timeout` | `SLUG N` | while it climbs ("level K is due"); while the wait runs and the mode is `with-owner`; irreversible always |
| `levels` | none, read-only, every task | nothing. Prints per level: how often it ran, settled, and changed the pick, and how often its `lean` differed from the lead's pick |
| `list` | `SLUG` | as today |
| `advise`, `settle` | stubs | always, each with the command that replaces it |

`levels` exists because he left open whether the personas or the experts serve better, and the plan
says "after real decisions, the log shows which level never changes anything". Without it, an agent
counts by hand, and a number needs its source. It costs a small change nothing.

What replaces each caller of `advise` and `settle`:

- `experts.py:330-331` (`cmd_choice_record`) calls `decisions experts`.
- `stages/choice.md:56-65` (step 4, the owner is away) goes. One line names `stages/mode.md`.
- `stages/build.md:151-152` ("`wait` also returns when Lem settled ...") goes into `stages/ladder.md`
  as the `wait` returns above.
- `harness/claude-code.md:107-110` goes, except the sentence on his away channel.
- `lem-ask-expert/SKILL.md:87-99` (the wait, `settle`, "never green") becomes three lines: level 4,
  the count, not green without him.

### With the owner: the card (`stages/choice.md`, Lem's)

- **When:** the ladder ended with a card (level 3 or higher with A1, or an irreversible step). The lead,
  or the defender, sends `lem: SLUG choice N waits` through `tell-coordinator` after the end, not after
  the ask. Lem also finds it in `lem decisions pending` at each turn, as today. The part of the build
  that needs the choice waits; the rest goes on. So the card comes "before the build goes on" for
  that part.
- **Through:** `ask-owner`, as today. The question gate no longer sits at this card (its judge ran at
  level 0), the panel is not run again, and there is no Jev framing check.
- **What it shows, in this order:**
  1. the run: the case in its numbered steps, whether it was reproduced or derived, and its cause
     (today, `choice.md:20-21`);
  2. the ladder, one line for each level that ran: the gate's verdict and cite; the lead's pick and
     why; the personas' votes, one row per persona and family; the dialectic's checked holds and
     breaks, with each break's text; the experts' picks and reasons; then the result ("the dialectic
     took 'after the price'", or "no level settled it: the lead's pick stands");
  3. the options, with the ladder's pick marked as recommended and the settling level's reason;
  4. the time the wait ends, in his clock, and that after it the ladder's pick is taken and the pull
     request is not green for it; for an irreversible step, its kind and that only the part that needs
     it waits;
  5. the answers: each option; "All opinions" when a level did not run; his own words (`--instead`);
     and the control "also a rule for later tasks".

### Irreversible choices in both modes

The four kinds stay (`decisions.py:150-155`). The ladder climbs as for any choice, and its pick is the
card's recommendation only. The end is always a card with no deadline, in both modes. `timeout` and
the mode never take it. Only his `answer` ends it. Without him, the question also goes to his away
channel where his instructions name one (`ask-owner`). The part of the plan that needs the step
waits. When every task left needs it, the lead writes `held` with `choice N waits for the owner`
(`build.md:155-162`, unchanged). `propose` refuses while it waits (`land.py:2455-2466`, unchanged),
and task 4's red block names it.

## What it costs

Agents and words of Lem's session and of the lead. "Before" is `wc -w` at `cfc4831`. "After" is an
estimate until the builder of T5 measures it. N is the number of personas a panel brings: 2 to 3
(the floor of two, and "only the people the question affects", `lem-panel/SKILL.md:70-76`; an
estimate, not a measurement).

The lead today reads `prompts/lead.md` 799, `SKILL.md` 5,898, `harness/claude-code.md` 5,679,
`stages/plan.md` 3,004, `stages/build.md` 3,033 and its agent body `agents/lem-builder.md` 1,395, which
is 19,808 words. The panel's texts are `lem-panel/SKILL.md` 3,463 and `references/messages.md` 2,456,
5,919 together.

| Path | Agents before | Agents after | Lead reads before | Lead reads after (estimate) | Lem reads for it, before → after |
| --- | --- | --- | --- | --- | --- |
| Small change | 2 (builder, review agent) | 2 | builder: 2,221 (`small.md` 826 + `lem-builder.md` 1,395) | 2,221 | `SKILL.md` 5,898 → ~5,730 |
| Full change, no decision | unchanged | unchanged | 19,808 | ~18,260 | `SKILL.md` −~170 |
| One decision, settled at level 0 | today it goes to the panel: N + 1 moderator = 3 to 4 | 1 | +5,919 | +~2,330 (`ladder.md` ~1,300, `lem-gate` ~690, `judge.md` 337) | 0 → 0 |
| Settled at level 2 | 3 to 4 | 1 + 1 + N = 4 to 5 | +5,919 | +~8,430 | 0 → 0 |
| Settled at level 3 | today a card: 3 to 4 + 2 experts + 1 gate judge = 6 to 7, + 2 Jev calls | 6 to 7, no Jev call | +7,364 (+ `lem-ask-expert` 1,445) | +~9,090 (+ `lem-dialectic` ~660) | `choice.md` 987 + `lem-gate` 1,059 + `judge.md` 337 + `durable.md` 249 = 2,632 → `choice.md` ~880 |
| Level 4 or 5 | 6 to 7 | 8 to 9 | +7,364 | +~10,290 (+ `lem-ask-expert` ~1,195) | 2,632 → ~880 |

- A practice scout adds 1 agent at level 2 when `facts.md` names a fact, before and after.
- After the change, the lead of a full change with no decision reads about 1,550 fewer words
  (estimate), because the steps of a choice move to `stages/ladder.md`, which a lead reads only at its
  first decision.
- The small change reads no new text and starts no new agent. Lem's `SKILL.md` gets one row for the
  three sentences (~40 words, estimate), and its paragraph on decisions (`SKILL.md:140-156`, 306
  words) shrinks to about 100 (estimate). `stages/mode.md` is read only when he says the words.
- A decision at level 2 costs one agent more than today (the gate's judge). A decision that a ruling
  settles costs 1 agent where today it costs 3 to 4.

### What the design removes, counted

Script lines (`grep -c ''` at `cfc4831`):

- `skills/lem-gate/scripts/gate-log.py`: 164 lines.
- `decisions.py`: `cmd_settle` 28 (`667-694`), its parser 4 (`754-757`) and dispatch 7 (`788-794`),
  and the docstring of `advise`, `settle` and the wait at the start (`57-68`, `99-106`): 20. Total 59.
  `cmd_advise` (32) becomes `cmd_experts` with its old-form branch, so it saves about nothing.
- `bin/lem:36`: 1 row.
- Tests: `tests/test-gate-panel.sh:11-47` (37 lines, the gate log); `tests/test-ask-expert.sh:165-212`
  (48 lines, `settle --away`).

Words:

- `lem-gate/SKILL.md`: the shadow mode and steps 3 to 5, 493 of 1,059 words, give way to a short "In the
  ladder" section (~120, estimate). `references/durable.md`: 249.
- `stages/choice.md`: step 4, 156 words, and the gate and the experts' timing in step 1 (part of 309).
- `harness/claude-code.md:102-110`: 145 words, of which one sentence on the away channel stays.
- `lem-ask-expert/SKILL.md`, "A choice of a task": 550 words become about 300 (estimate).
- `stages/build.md`, steps 2 to 4 of "A choice in the build": 913 words, and `stages/plan.md` step 5:
  565 words, move into the new `stages/ladder.md` (~1,300, estimate), which only a lead at a decision
  reads.

Added (estimates): `decisions.py` about +220 lines, a new `skills/lem/scripts/ladder.py` of about 150
(the answer forms, the vote count and the cite check, pure functions), `project.py` about +50,
`criteria.py` +20, `land.py` +70, `experts.py` +10. So the scripts grow by about 300 lines net. The
plain fact: the ladder is new machinery. Each part names the act of Lem's that does harm without it:

- the count of the votes and of the cites: without it, "by the personas" or "by the dialectic" in a
  pull request is a lead's own say-so, and Lem owns the truth of its words;
- the mode: without it, every card he cannot see waits 15 minutes and then goes "not green" with no
  reason he gave, and a choice he wanted to see is taken while he is at the desk;
- `levels`: without it, the question he left open has no number with a source.

Each costs a small change nothing.

## The build

Tasks 2 and 3 of the plan are one chain of six builder tasks, one builder at a time in a file set.
Each builder runs only the blocks it names. Task 1a may change how a block is written (one Python
process for logic): the tests below are named by behavior, and each is a thing a developer would
notice.

**T1. The mode.** Files: `skills/lem/scripts/project.py` (`mode`, `task.mode` in `tasks`, the
refusal in `log`), `skills/lem/scripts/criteria.py` (`--alone`), `skills/lem/scripts/decisions.py`
(`log --interview` only, and `mode` read in `Task.read_status`). Tests:
- `mode SLUG alone`, then `tasks` gives `alone` with its time; `mode --all with-owner` takes it back;
  a task with no event is `with-owner`;
- `--all` writes for every task that did not end, and for none that ended; an ended task by its slug
  is refused;
- a wrong value, empty words or a wrong `--by` is refused, and `log SLUG task.mode` is refused;
- `approve --alone` is refused while the task runs with the owner, taken while it runs without him
  (`by: alone`), refused after the owner's approval, taken after a small change's approval, and
  refused with `--small` or `--read`;
- `log --interview` is refused with the owner, and with `--by lead`.
Blocks: `tests/lem-state.sh`, `tests/lem-settings.sh`, `tests/lem-decisions.sh`.

**T2. The ladder's record and commands.** Files: `decisions.py`, new `skills/lem/scripts/ladder.py`
(parsing, the vote count, the cite check), `choices/N.md` written by `ask`. Tests:
- `ask` opens a choice that climbs, with no deadline, and writes `choices/N.md` with no pick;
- the gate: a ruling ends it at level 0 with no card in both modes; `cheap` takes the lead's pick;
  `held` makes level 2 due; `checkable` needs `--chose` and `--shown`;
- the personas: 3 votes for the lead's pick end it at level 2 with no card; a split 2 to 1 makes level
  3 due on the option with 2 votes; 3 votes for another option do not end it; one persona's two
  family votes are not enough; an answer not in the form names its file; a pick that is no option
  is refused;
- the dialectic: a checked break keeps it climbing; a cite whose words are not at the line is dropped
  and named; one checked hold and no break ends it at level 3;
- the experts: one option from both ends it at level 4, also against the lead's pick (`changed`
  true); a split or a silent expert ends it at level 5 with the lead's pick;
- the end with the owner and level 3 or higher is a card with a deadline; alone it is taken; an
  irreversible step is a card with no deadline in both modes;
- `mode alone` while a card waits: `timeout` is taken before the deadline (`early`), and `wait` returns
  "the task runs without the owner now"; `mode with-owner` while it climbs: its end is a card;
- `all` after an end at level 2: levels 3 and 4 become due, the end after them still takes level 2's
  pick, and a new card holds every level; `all` is refused once every level ran, and after `taken`;
- an answer while it climbs ends it, and a level after the answer is refused;
- `timeout` while it climbs is refused, naming the level that is due;
- `levels` over two tasks counts ran, settled and changed for each level;
- `advise` and `settle` exit 1 and name what replaces them;
- `log --by personas` and `criterion --by personas` are refused, naming the ladder.
Blocks: `tests/lem-decisions.sh`, `tests/test-ask-expert.sh` (its part on the record), and an
in-process test of `ladder.py` where task 1a set that form.

**T3. The pull request's text.** Files: `skills/lem/scripts/land.py` (`not_green`, `decided`,
`TAKEN_BY`, `GREEN`, the first line, the refusals at `2423` and `2432` with an `alone` approval, the
refusal for a choice that climbs). Tests:
- criteria approved without him: proposed, not green, the first line names "the criteria";
- a flagged read with an approval without him: proposed, not green, with the flag; the same for a
  request someone else wrote;
- his approval after it makes that line go;
- a choice ended at level 4 while the task ran without him: a not-green line with both experts'
  reasons; at level 2: a decision line only, green;
- a card not answered in its wait: "after the owner's wait of 15 minutes"; one taken early by "go
  alone": "when the owner said 'go alone'";
- a task that ran without him with nothing decided without him: green, with the line that it ran
  without him;
- `land --by agent` refuses a not-green request of a task that ran without him;
- `propose` refuses while a choice climbs, naming the level.
Blocks: `tests/lem-land-local.sh`, `tests/lem-land-small.sh` (the small text does not change),
`tests/lem-old-tasks.sh`.

**T4. The skills of the ladder.** Files: `skills/lem-ask-expert/scripts/experts.py` (the neutral brief
for the new form, `record` through `decisions experts`, refused before level 4) and its `SKILL.md`;
`skills/lem-gate/SKILL.md` (shorter, "In the ladder"), `references/judge.md` (the `option:` line, no
project's words), `references/durable.md` and `scripts/gate-log.py` out, `bin/lem` without
`gate-log`; `skills/lem-panel/SKILL.md` ("In the ladder": steps 1 and 2 of a question only, then
`lem decisions personas`) and `references/messages.md` (the fixed last lines of each persona's
answer); `skills/lem-dialectic/SKILL.md` ("In the ladder": the two forms, no synthesis). Tests:
- the experts' brief of a new choice holds no recommended option and no earlier answer; that of a
  choice of the form before still holds them;
- `record` puts the advice into level 4; a brief before level 4 is refused, naming the level;
- `lem help` lists no `gate-log`, and `lem gate-log` says the name is unknown;
- the gate part of `tests/test-gate-panel.sh` goes, and the cast part stays green.
Blocks: `tests/test-ask-expert.sh`, `tests/test-gate-panel.sh`, `tests/lem-command.sh`.

**T5. The stage texts.** Files: new `skills/lem/stages/ladder.md` (a lead's and a defender's, read at the
first decision), new `skills/lem/stages/mode.md` (Lem's), `stages/build.md` ("A choice in the build"
keeps `log`, `criterion` and step 1, and names `ladder.md`), `stages/plan.md` (step 5 shrinks; step 1
gets `--alone` for a complete request), `stages/choice.md` (the card above; step 4 goes),
`stages/interview.md` (the paragraph for a task without him), `stages/stopped.md` (the talk's open
choices ran their ladder), `prompts/lead.md` (step 5: his words go to `lem project mode`; a decision
goes to the ladder), `prompts/defender.md` (step 6: the ladder before it stops; no `advised` line),
`SKILL.md` (one row for the three sentences; the decision paragraph shorter), `harness/README.md`
(the question gate's row: "decides a question at the first level of the ladder"),
`harness/claude-code.md` (the away rule goes; `fan-out` for the dialectic; `tell-coordinator` sends
`waits` at the end of the ladder and no `advised`). No unit test: the real runs are their proof. The
report gives the `wc -w` table of every file before and after, and a search of `skills/` for
`settle`, `advise`, `--by personas`, `shadow`, `gate-log`, `away on two facts` and `advised`, each with
what is left and why.

**T6. The board.** Files: `skills/lem/assets/board.html` (the events `decision.level`,
`decision.expert`, `decision.ended`, `decision.all` and `task.mode`; a choice that climbs shows its
level; a task without him shows since when). Tests in `tests/test-board.sh`: a choice that climbs, a
card that waits after the ladder, a task that runs without the owner, and the old decision events of
its fixture, drawn as before. T6 may run beside T5: no file is shared.

### The old forms that must still read

Each in `tests/lem-old-tasks.sh` or the block named, written by hand as the older script wrote it:

1. A choice with no `ladder` key that waits, with one expert's advice: `pending` lists it with its
   seconds; `experts` records the second advice as `advised`; `timeout` after its deadline takes the
   shared pick; `timeout` before it, with the mode `alone`, takes it too, which is what `settle` did
   (`tests/test-ask-expert.sh`).
2. A `settled` line of an older Lem: `list` shows it, and the pull request says "taken by the experts
   while the owner was away", not green (`tests/lem-land-local.sh`).
3. `taken` lines and criterion lines with `by: personas`: the pull request's decision and criterion
   lines read as today (`tests/lem-land-local.sh`).
4. The tasks of an older Lem in `tests/lem-old-tasks.sh` have no `task.mode`: they read
   `with-owner` and land as before.
5. Approvals `by: owner`, `read`, `lem` and the old `correction`: unchanged, and `alone` is new
   (`tests/lem-decisions.sh`, `tests/lem-land-local.sh`).
6. The board's fixture of old decision events draws as before (`tests/test-board.sh`).

A later change may drop the old forms and the two stubs once no task that wrote them is open. Each
place in the code says so in a comment, as the rule "A change to what an open task's record holds
keeps reading the form before it" of "Rules for a change here" asked; "Lem is not released, so a
change keeps no reading of the form before it" took its place on 2026-11-18.

### What only a real task with a model can show

1. Whether persona agents end their answers with the fixed `pick:` and `sure:` lines, and how often
   one needs a second ask.
2. Whether the dialectic's agents write cites that the check finds (`PATH:LINE` and the words), and
   how many points it drops. If many real breaks are dropped for a wrong line, the tolerance of 2
   lines is wrong.
3. Whether the gate's judge finds a ruling in `docs/rulings` that answers, and how often each verdict
   comes.
4. Whether a lead sends the right decisions to the ladder: too many costs agents, and too few hides
   decisions in `log --by lead`.
5. How long the ladder takes from `ask` to its end at each level. With him at the desk, his wait
   starts only after it.
6. Whether Lem hears "go alone" in the middle of an interview, logs each guess, and approves with
   `--alone`.
7. Whether a lead in its `wait` loop sees the mode change and runs `timeout`.
8. Whether the card with the ladder's lines reads at a glance, and whether "All opinions" and "also
   a rule for later tasks" are used.
9. Whether the two experts start from a lead (`harness/claude-code.md:356-357`: not run yet from a
   `lem-builder`), and whether the dialectic's two agents start by `fan-out` from a lead.
10. Whether the first line of a not-green pull request of a task that ran without him tells him at once
    what to read.
11. After real decisions, what `lem decisions levels` shows: which level settles, and which never
    changes the pick.
12. Whether a lead that read the stage text before the update meets a refusal it can follow (the
    `--by personas` refusal and the `lem experts brief` refusal before level 4).
