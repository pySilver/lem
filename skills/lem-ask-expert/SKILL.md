---
name: lem-ask-expert
description: "Lem's experts: two models of two families, or one without Codex, answer one question, read-only, at the same time. The owner calls it as `/lem ask-expert` with a question in words, or alone for the open question; a lead calls it at the last level of the ladder of a decision in doubt."
disable-model-invocation: true
argument-hint: '[question in words]'
---

# Ask the experts

Two experts of two model families answer one question from one brief, each on its own, at the
same moment, so that their agreement is worth more than two agents of one family would give. They
read; they change nothing. The owner asked for them as the way out when nobody is there to answer
a choice ("a skill "ask expert" which calls Fable subagent and GPT-6 Astra experts in background",
2026-11-16), and as an opinion he can call in the middle of a discussion or an interview ("I may
then provide context directly in command `/lem ask-expert what would be the best solution for this
kind of problem` or just type the `/lem ask-expert` and assume the skill knows what to ask from the
context", 2026-11-17).

Who they are is the settings' `seats.experts`, one or two seats `agent/model:effort`, which `lem
project show` prints with Lem's default where the project and this machine name none, each `here`
when its agent is on this machine. Only those answer: without Codex, one expert answers alone. An
expert's name is the last word of its model. The script prints each one with its name, its seat, its agent, its model and
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
   agent asked the owner or he raised and nobody settled. In a task's session that a breaker holds,
   it is the breaker's question, with its options from its document (`breaker-N.md`). When nothing is open, or more than one
   could be meant, ask the owner in one line which one, naming each, and start nothing. Never guess: the owner said "if question is
   unsure it gets back to user".
3. **A decision in doubt of a task**: a lead's level 4 of the ladder (`stages/ladder.md` in the
   `lem` skill), the last one. It is a question in words, below, with the decision's options word
   for word and the facts the levels before found in `--context`; both picking one option settles
   it, and the lead logs the pick (`--by experts`). Step 4 is then the lead's log, never a page:
   nothing of a build waits for the owner.

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
