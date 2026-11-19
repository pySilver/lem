---
name: lem-ask-expert
description: "Lem's experts: two models of two families, or one without Codex, answer one question, read-only, at the same time. The owner calls it as `/lem ask-expert` with a question in words, or alone for the open question; Lem's stages call it at a decision in doubt and for a choice that waits."
disable-model-invocation: true
argument-hint: '[question in words]'
---

# Ask the experts

Two experts of two model families answer one question from one brief, each on its own, at the
same moment, so that their agreement is worth more than two agents of one family would give. They
read; they change nothing. The owner asked for them as the way out when he is not there to answer
a choice ("a skill "ask expert" which calls Fable subagent and GPT-6 Astra experts in background",
2026-11-16), and as an opinion he can call in the middle of a discussion or an interview ("I may
then provide context directly in command `/lem ask-expert what would be the best solution for this
kind of problem` or just type the `/lem ask-expert` and assume the skill knows what to ask from the
context", 2026-11-17).

Who they are is the settings' `seats.experts`, one or two seats `agent/model:effort`, which `lem
project show` prints with Lem's default where the project and this machine name none, each `here`
when its agent is on this machine. Only those answer: without Codex, one expert answers alone. For a question in
words an expert's name is the last word of its model; for a choice of a task it is its place in
the record, below. The script prints each one with its name, its seat, its agent, its model and
its effort.

Every brief also says who the code is for: the project's profile by its path, and each persona by
its file, its first heading and its "Who they are", short enough to read in a minute (the owner:
"experts should have a context of personas I think, so they can also reason about what kind of
users builded code are expected", 2026-11-19). An expert weighs an option by what it does to these
people and still decides as an engineer; no expert answers as a persona. The script takes them from
`lem cast`, so a project with no personas, whose setup is not finished, gets no brief, and the
refusal says what `lem cast` said.

`SKILL_DIR` is this skill's directory. `CHECKOUT` is the checkout the question is about: the
task's worktree when it belongs to a task, else the one this session works in.

## Which question

1. **`/lem ask-expert` and a question in words**: the experts get that question. Give them the
   context this session has, since they see nothing else: what is being decided and why it came up,
   the options word for word when there are any, and the files that matter, by path.
2. **`/lem ask-expert` alone**: the question that is open in this conversation, the last one an
   agent asked the owner or he raised and nobody settled. Run `lem decisions
   --repo CHECKOUT pending` too: when no question is open here and exactly one choice of a task
   waits for the owner, that choice is the question, and it goes by "A choice of a task" below.
   When nothing is open and nothing waits, or more than one could be meant, ask the owner in one
   line which one, naming each, and start nothing. Never guess: the owner said "if question is
   unsure it gets back to user".
3. **A decision in doubt of a task**: a lead's level 4 of the ladder (`stages/ladder.md` in the
   `lem` skill). It is a question in words, below, with the decision's options word for word and
   the facts the levels before found in `--context`; both picking one option settles it.
4. **A choice of a task that waits, by its slug and number**: when the owner asks for all
   opinions on its card, and for a choice a lead of the text before asked. The advice goes into
   the choice's record, where `decisions.py` reads it.

## A question in words

1. **The brief.**

   ```bash
   lem experts --repo CHECKOUT brief --question "TEXT" [--context "TEXT"] [--option "TEXT" ...] [--file PATH ...]
   ```

   `--context` is what is being decided and why it came up, in a few sentences; `--option` names an
   option word for word, once for each, two or more, or none for an open question; `--file` names a
   file that matters, relative to the checkout. The script makes a folder for the question in Lem's
   state folder, `experts/DATE-TIME-WORDS/`, and writes `brief.md` there. It prints the folder's
   name (`folder`), the brief's path, each expert with its seat and its answer file, and the
   checkout the experts read. It removes the folders whose last write is older than 30 days first.

2. **Start every expert in `experts` at once, in the background**, through `ask-experts` in the
   harness file of your agent (`harness/` in the `lem` skill's directory), each on its seat. Each
   gets the brief's path and nothing else, works in the checkout read-only, and its last message is
   its answer. Go on with the conversation while they work; you are told when each ends, so never
   poll.

3. **As each one ends**, its answer file holds its last message word for word (the harness file
   says who writes it), and:

   ```bash
   lem experts --repo CHECKOUT record --folder FOLDER --expert NAME
   ```

   It writes the answer into the folder's `record.json` and prints the record: each answer, the
   pick all of them share (`agree`, for a question with options) and who is still to answer
   (`waiting`). It refuses an answer that is not in the brief's form, and a pick that is no option.
   Then ask that expert once more with the same brief. When the second answer is refused too, or
   the expert did not start, record nothing for it and say so in one line.

4. **Show the owner** the answers side by side, when `waiting` is empty: each expert's answer and
   its reasons, where they agree and where they split, and one line of what you would do with them.
   When the question has options to compare, that is a page (`ask-owner`): one option each, with
   which expert picked it and why, and your line as the recommendation. His answer there is his
   decision on the question. When the answers are short and have no options, they are a few lines
   in the conversation. Then go on with what the question interrupted.

## A choice of a task

Their advice goes on the owner's card, and decides nothing by itself; the record does that, by
the rules of `decisions.py`:

- when he says that he is away (`lem project owner away`), the choice is taken with the option
  both picked (or the one expert's, where one answers alone), and the recommended option when they
  split, when one found none fits, or when one did not answer;
- a choice the experts decided is never green: the pull request has a line with their pick and
  both reasons, and he reads it before he merges;
- a step that a later "no" cannot reverse (`--irreversible`) takes advice for his card, and is
  never decided by the experts: it waits for his word.

`WORKTREE` is the task's worktree, or any directory of the checkout. A task's record keeps the
advice in two places, `fable` and `astra`, the names `lem decisions` knows: the first seat of
`seats.experts` answers as `fable` and the second as `astra`, whatever model sits there.

1. **The brief.** Start it before anything else: the owner may answer, or say that he is away,
   while the experts read.

   ```bash
   lem experts --repo WORKTREE brief SLUG N [--file PATH ...]
   ```

   `--file` names a file the choice is about, relative to the worktree, once for each. The script
   writes `experts/choice-N.brief.md` in the task's directory: the choice, its options word for
   word, the recommended one and why, what the personas said, the task's acceptance criteria and
   its plan, the files, who the code is for, and the form of an answer. It prints the brief's path, each expert with its
   seat and its answer file, and the experts still to ask (`ask`). It refuses a choice that does not
   wait, and one that every expert advised already.

2. **Start the experts named in `ask` at once, in the background**, as step 2 above, in the
   task's worktree. Do not wait for them: go on with the work that does not depend on the choice.

3. **As each one ends**:

   ```bash
   lem experts --repo WORKTREE record SLUG N --expert NAME
   ```

   It writes the advice into the choice's record with `lem decisions advise`, under the task's
   lock, with the same refusals and the same one more ask as step 3 above. With one expert's
   advice his "away" takes the recommended option. Advice on a choice that no longer waits is
   refused too, and changes nothing.

4. **Tell who reads it.** Lem finds the advice in `lem decisions pending` and shows both answers
   to the owner on the choice's own options, as step 4 above.

`lem decisions list SLUG` and `lem decisions pending SLUG` show the advice under each choice
(`advice`), and `experts_pick` is the option every expert picked, or null.
