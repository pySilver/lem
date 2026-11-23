# The interview and the acceptance criteria

The standard track with an interview, after "The request" wrote the task's brief and the state
`held` with `the interview waits for the owner` (`stages/new.md`), and criteria that wait for his
yes. It runs in the task's own session, with him, and ends with criteria he approved, which the
lead may not change without the record saying so, and with the hand-over to the build. While he
is away it goes on without him, as `stages/away.md` says. A session that ended before the end is
opened again on his word (the board's row, or `/lem status SLUG`), and the new one goes on from the
files these steps write as they go, so each step writes as it comes and never after the last
question. While it waits for him, keep the watch of his mark (`stages/away.md`, "The watch").

Criteria that wait for his yes with no interview (a lead's, of a complete request) start at step
6, from the lead's `report.md`, which holds them on top with the personas' read: write them into
`criteria.md` with no test lines, and put them to him.

1. **Start the scout and the interview at once.** A fix whose investigation found its cause has
   no scout: the investigation's report is its facts of the code, and wherever these steps name
   the scout's report, read that one. Nor has a task whose fast-track builder found a full change:
   that builder's `report.md` is the scout's. A `scout.md` already in the task directory is a scout
   that ran for a session before you, and none starts again. The scout is a fresh read-only agent that
   reads the code around the ask and returns facts, not a plan: `spawn-builder` with the brief

   ```
   Read `skills/lem/prompts/scout.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.
   request: TASK_DIRECTORY/ask.txt
   checkout: the main checkout's absolute path
   task directory: TASK_DIRECTORY
   ```

   The interview does not wait for it, so it costs him no wait: on 2026-11-16 a scout took 26.7 s
   in a tiny repository and 116.5 s in Lem's own, 12 files opened in each (one request each).
   Log the start of each, so that the board draws both: `lem project
   log SLUG scout.start` as the scout starts, and `lem project log SLUG interview.start` before
   the first question. The scout is your builder, so its reply comes to you, and it is its
   report: write it word for word into `scout.md` in the task directory, and log `lem project log
   SLUG scout`, its end. It is the one place where knowledge of the code comes up to you, and
   only as facts for the criteria: you still read no diff and write no code.
2. **The interview.** One question at a time, each with your own guess, so that he reacts and
   does not compose. A question he answers with a yes to your guess, or by typing a value (a
   name, a number, a word), is one line in the conversation: that is the owner's own exception
   to the page, "something fixed choice, trivial, without additional context". A question that
   sets two or more options side by side, each with what it changes for a person, goes on the
   question page (`ask-owner`), as his ruling says of every other question; put the options
   that are ready on one page, never one page per question. The questions come from the
   `lem-interview-me` method (`load-skill`); its restate and its explicit yes are the criteria
   and his yes to them (steps 4 to 7), so nothing is restated before the criteria and he says yes
   once. A fact of the scout's report may go into a later question ("the export already
   writes an empty cell for a missing value; keep that for the note?"). It may be technical: he
   is a developer. Each answer of his that sets the outcome goes into `interview-notes.md` in the
   task directory as it comes, one line each, the question in a few words and his answer as he
   gave it; a question that file or `directions.md` already answers is not asked again. Stop when
   you can write the outcome and each rule without a guess.
3. **The directions.** What he names in the interview, a technology, a library, an approach, an
   option he picked between two, is a direction, and so is one he named in the talk that led to
   the ask (`talk.md`). Write each into `directions.md` in the task directory as he names it, one
   line each, with his words. The lead's plan follows them; a plan that departs from one is a
   decision of the build (`stages/build.md`, "A choice in the build"). Then write `task.md` again
   with the outcome and the "done when" his answers gave, once the last question is answered. Read
   `SKILL_DIR/prompts/writing.md` first: the `## Outcome` is its story of what he will see, Today
   and After, with a chart when the change is a flow or a rule with branches. Once it is written,
   log the end of the questions, `lem project log SLUG interview.end`, also when they ended with
   your guesses while he is away: from then on the board says that you write the criteria, and no
   longer lists the task as his while the scout still reads and you write.
   A defect outside the request, that he names or that the scout's report shows, is no part of
   the task and is not lost: write it to `outside.md` in the task directory, one line each, with
   its place (`path` or `path:symbol`) and what is wrong. Do not ask him whether to file it, and
   do not put it into the criteria. The landing's polish pass takes each one by the bar of rule 6
   of the builder's standing rules, and the pull request lists what it fixed, what it filed and
   what it saw and did not file.
4. **The criteria**, when the scout's report is in and not before. Write them from his words, the
   directions, the project's profile and the report, in the form `lem criteria --help` shows: the
   `## Acceptance criteria` heading, the line `Size: full, because ...`, and numbered criteria, each
   a business rule in plain language with one concrete example, with real names and values, and
   a case or a chart where `prompts/writing.md`, "In the acceptance criteria", asks for one. No
   test lines: the lead adds those. Keep the file as `criteria.md` in the task directory (over the
   fast track's one criterion, when the task came from there; its approval keeps that text), and
   for each criterion the facts of the report that shaped it, for his page.
5. **Show them in the conversation, and start the personas' read in the same moment.** Write the
   criteria as plain text, each with the scout's facts that shaped it beside it, and the
   directions, and say that the personas read them now (a chart stays in the file and goes on the
   page of step 6). No page opens before the read is in.
   Log its start, `lem project log SLUG criteria.read.start by=lem`; the
   record below is its end. The read is the persona panel's
   "Reading acceptance criteria" mode (`load-skill`). It runs on one model family: a task's session
   has no paired agent of the other family, and the panel never puts a one-shot agent of that
   family in its place, so the record's `families` has one entry and the panel says that one family
   answered. A persona agent that does not answer leaves a partial
   read, which counts: the record says who did not answer and why. A read in which nobody
   answered is written down too, with `answered:=0`, `families:='[]'` and each source in
   `silent`, and started once more. After a second such read in a row the criteria go on
   unread: the owner's yes of step 6 still freezes them, and the pull request is not green, with
   "the criteria were not read" first. A partial read counts by his word of 2026-11-16 ("Thats
   fine - just log and proceed"); the second try is the amendment's design. The landing refuses a
   request whose newest read had no answer and was the first. When the answers are in, copy the
   panel's `criteria-read.md` into the task directory as `criteria-read.md`, with each answer below
   it, its persona and its family named, in its words: a session after you puts his page up from
   that file and asks for no second read. Then write the one event the landing reads:

   ```bash
   lem project log SLUG criteria.read by=lem asked:=N answered:=N families:='["FAMILY", ...]' silent:='[{"name": "PERSONA, FAMILY", "why": "WHAT STOPPED IT"}]' criteria:=N flagged:=N split:=true|false digest=DIGEST
   ```

   `asked` is the personas the panel asked and `answered` those of whom at least one family
   answered; `silent` names each source that gave no answer, `[]` when every one did. `flagged`
   counts the criteria an answer called unexpected, confusing or wrong; `split` says whether the
   two families answered a criterion differently, which counts as a doubt too. `DIGEST` is the
   `digest` field of what `lem criteria digest SLUG --file FILE` prints
   for the criteria file the personas read, so that the record knows when he changes them after
   the read.

   **The read is his to skip, never yours.** When a criterion names a person other than the
   developer (a customer, a clerk, a reader of a file), the read starts and you ask nothing. When
   every criterion names only the developer, ask one fixed question in the terminal before the
   read starts, a fixed choice with no context: "The acceptance criteria name only you. Skip the
   persona read? (y/n)". Log it as you ask it, `lem project log SLUG read.skip.asked`: the board
   lists the task as his again until he answers. Never skip the read by your own judgment: you wrote the criteria, and the author of a
   wrong reading sees it as clear (a Fable second opinion, 2026-11-16, which he agreed to). On his
   no, the read starts as above. On his yes, write his words at once, then take his approval of
   step 6 and freeze the criteria with step 7; a session after you reads that decision and asks
   neither again:

   ```bash
   lem decisions log SLUG --by owner --what "the personas' read of the criteria" --chose "no read: the criteria name only the developer" --why "HIS ANSWER, AS HE TYPED IT"
   ```

   His Yes or No on the board's row "Skip the persona read?" is the same y or n
   (`prompts/session.md`, "His answer on the board"): on his Yes the `--why` names its record, its
   key, `via` and `device`, and his note goes in `--words`.

   The landing knows his word by `--by owner` and those two texts, word for word, and takes it
   only with an approval of his after it and before any lead of the task started; the pull request
   then says "the criteria: not read by the personas, on the owner's word (DATE); the owner
   approved them", and stays green, since the decision was his. On the standard track from a complete
   request this question is never asked: there the read is the only approval (`stages/plan.md`,
   step 1), and the landing refuses a word to skip it that comes after the lead started.
6. **His yes.**
   - *He typed it in the conversation before the read was in*: take it, and wait for the read
     before you freeze anything. When the read is in and nobody is confused and the families
     agree, say so in one line, open no page, and freeze the criteria on that yes (step 7). When a
     criterion is flagged or the families split, open the page below for that: his answer there is
     his yes. An approval written before the read is in counts for nothing: the build starts
     only after the read's record (or his word to skip it), so that no lead starts before a doubt
     reaches him.
   - *Otherwise*, when the read is in, open one page through `ask-owner`:
     - the personas' result on top, for each persona and each model family, with a split
       between the families said first, in one line ("the Opus answers doubt criterion 1, the Sol
       answers do not");
     - each criterion, with the scout's facts that shaped it beside it, and its case and its chart
       as the file has them (a chart as the page's diagram block);
     - a criterion a persona flagged as you wrote it, with the answers that flagged it quoted beside
       it. Never reword it before he sees it: what changes it is his;
     - the directions.
   He approves, or changes a criterion, a direction or the set. Write each change in his words into
   the criteria file or `directions.md`. The personas do not read his own change again; the pull
   request then says that the criteria changed after the read.
7. **Freeze them**: `lem criteria approve SLUG --file FILE`, again after
   each change of his. The criteria are then kept word for word with a digest, and the plan's
   criteria have to be those, with only the test lines added: a criterion the build changes, adds or
   drops has its own record (`lem decisions criterion`), and the pull request is not green for it.
   Write no `lead:` line before it: the landing reads the first `lead:` line as the end of the
   interview. Then the start of the build, `stages/start.md`: it may queue the task, and otherwise
   it writes the lead's state and hands the task to a fresh lead. Criteria that a lead put to him
   (a complete request) start nothing here: after his yes that lead builds on, as `stages/plan.md`
   says. A stop between the approval and
   the hand-over loses nothing: the session opened after it reads the record. The landing refuses a task on the standard track
   whose criteria nobody read and whose read he did not skip (step 5), one whose read found a
   doubt with no yes of his after it, and one that had an interview and whose criteria carry no
   approval of his, nor one with `--alone` while he was away: a clear read is no yes.

When he says that he is away during the interview, it goes on without him as step 3 of
`stages/away.md` says: your guesses, logged, the read, each flagged criterion settled by the
ladder, and the criteria approved with `--alone`, then the end of step 7.
When he leaves with no such words, nothing is written: the question or the page waits in this
session, and the state stays `held` with `the interview waits for the owner`.
