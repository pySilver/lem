# Claude Code: ask-owner

A part of `../claude-code.md`, read at the first question a session puts to the owner, and at the
first wake or reply that comes from his inbox (`inbox-reply`).

## ask-owner

`lem-ask`, Lem's own page, for every question that asks the owner to choose or to approve: each
option with what the owner would see and what it costs. Lem opens the page each time it asks; the
owner types nothing for it. It is a part of Lem, not a tool of the machine: the machine check has
no row for it, and no page for the owner lists it as one. Its command is `lem ask`,
a name of Lem's command `lem`. If `result.outcome` is `no-agterm`, ask in the conversation as a numbered list with the
recommended option first.

The question itself has one form whatever shows it: one concrete case, the options with what the
owner would see for each, the recommended one with its reason, and the shortest way to answer.
Three kinds of question stay in the terminal under every value: a value the owner types (a name,
a path, a number), a bare go-ahead on a step just described, and a fixed, trivial choice that
needs no context. The owner's global instructions say how a question is told; they outrank this
file.

When the owner is away, what waits for him reaches his inbox through the board's server, which is
its one sender (`inbox-reply`, below). A session sends no question there itself: one that is not a
thing of "Waits for you" (`lem waiting --task SLUG`) waits for him in the session.

**A card in a task's session** waits for his answer with no time limit, and the session still
takes a wake-up meanwhile: run `lem ask ask SPEC --timeout 86400` with the Bash tool's
`run_in_background`, and without `--follow`, so that the card takes no focus. The session's turn
then ends while the card is up, so a wake-up reaches it (the mailbox hook hands mail over between
two turns, "A wake-up" in `task-session.md`), and the end of the command wakes it with the answer. For `result.outcome: "pending"`, run `lem ask wait PAGEID` the same way.
The outcome `dismissed` means the owner closed the card. If the outcome is `chat`, or the
answer has `text` and no selection on a choice question, answer the owner in the session's
conversation and put up the same spec again. Each session can show one card. The outcome
`busy` names the page when that session already shows one of its question pages.

The card is on the board too: its row in "Waits for you" opens the same page, on the Mac or the
phone, and his pick there ends the card's own command as a pick on the card does ("A card of a
task's session" in lem-ask's `SKILL.md`); the command closes its own page first. The result's
`from` says where the answer came from, `session` or `board`; a board answer also carries `via`
(`local` or `door`), `device` (`phone` or `computer`) and a `said` line, and so does every answer
when two came before the command read either. Say the `said` line in the session as it is, one
line: which answer was taken and from where. Then act on his pick as on his typed word, log his
decision `--by owner` with the note (the answer's `text`) as `--words`, and the card's `pageID`,
`from`, `via` and `device` in `--why` ("his pick on the board, card PAGEID, via door, from the
phone"), and go on. A note with no option and `chat`, above, stay as they are for a pick in the
session: the board refuses both. The outcomes `closed` and `dismissed` end the card.

## inbox-reply

The owner's inbox is the Plannotator Inbox. While his mark says away, the board's server sends each
thing of "Waits for you" there once, in the thread named by the task's slug, as the task's newest
Claude Code session (`plannotator inbox call --session claude-code:ID`, `inbox.py`), and
withdraws its question as the same session when the thing leaves the list. Plannotator brings his
reply back into the session the message went as ("Where replies go" in `plannotator inbox --help`,
read 2026-11-22). With no Inbox on the machine, or one with no tailnet address, nothing goes there,
and what waits stays in the session and on the board. To write in a thread, use Plannotator's
`plannotator_inbox` tool, `send_message` with `reply_to` his reply's id and `project_path` the main
checkout (`main checkout:` of `session.md`), as the server sends.

**The server is the one sender.** Send nothing to the Inbox for a thing that waits for him: no
question, no copy and no note, before the server's first look as after it. This holds also when a
personal rule of the owner's or a hook asks a session to use the Inbox while he is away: his own
rule names the Inbox for that case, and Plannotator's prompt hook asks every session to send a
decision there. In a task's session Lem's rule holds over such a rule, as "Only the skills a stage
names" in `SKILL.md` holds over one, so that each thing reaches the Inbox once. A session writes in
a thread only to answer a reply of his, as below.

**The wake.** The server wakes the session with `lem: SLUG inbox` after it sent a question of the
task, and after his reply came in a thread whose session no longer runs the task. Read `owner` of
`lem waiting --task SLUG`:

- **He is away**, and this session waits for him on the task's row there: for a blocked task or
  an order of his that names no task, put up a card with a text answer, as "A card in a task's
  session" says, in the background and without `--follow`, so that it takes no focus; the board
  shows it as a card row with its text field. A breaker, a plan, a merge and the yes/no rows
  ("Skip the persona read?", "Approve this criterion?", "Approve the criteria?") get no card: the board answers each with
  its own buttons (a merge with Merge; its "Not now" is no act), and a card would be a second row
  for one thing. Put up no second card for a thing whose card is up. His answer on the card is his
  typed word, and it is the first answer: the server then withdraws the Inbox question.
- **He is back**: put up no card; a breaker stays one line and the waiting mark. Read the task's
  thread yourself: `read_thread` with `asked_by: "anyone"` and `project_path` the main checkout
  lists the threads, the one whose `thread_name` is the slug is the task's, and `read_thread` with
  its `thread_id` reads it. A reply of his after its newest question is his answer, taken as below.

**His reply** arrives as a new message that starts `Plannotator Inbox:`, with his words and
"Answers to your questions". It is his answer, as if he typed it in the session, to the one thing its
message named (breaker N, the merge of the commit TIP, the plan, the blocked task, his order), and
only while that thing still waits:

1. Read `lem task show SLUG` before you act. When the task left that wait (his park on the board or
   his word at the Mac came first, the task is `parked`, a newer state block, another proposal than
   TIP), act on nothing. Answer in the thread, as yourself, that the question no longer applies and
   what took effect. Read the task's `task.json` in the directory from `lem task dir SLUG`. If the matching
   question there holds his answer from the board, the
   board's answer came first and counts: take it as `prompts/session.md`, "A wake-up", says, and
   say in one line in the session and in one line in the thread which answer was taken, from where,
   and that his reply came after it.
2. Act as on his typed word, by the stage that waits for it, and log his decision with his words,
   `--by owner`: a breaker as "After it" in `stages/breaker.md` says, Help with the words of his note
   as his part of the talk. His "Merge" is `lem land merge SLUG --by owner --tip TIP`, TIP the commit
   the question named. The command refuses a merge of any other proposal
   and nothing is merged that he did not read; his "Not now" leaves the pull request open. An answer
   that asks something back or thinks aloud is no pick: say in the thread what you read, and wait
   for his yes there or at the Mac.
3. Close the card when one is up (`lem ask close`: the card's own command then returns the
   outcome `closed`, which needs no act), clear the waiting mark (its reverse in
   `../claude-code.md`), and say in one line in the session and in one line in the thread that his
   answer came from the Inbox and what it did. Do this before the stage's own last act (the close
   of a parked or dropped task's session).

A message from the Inbox that answers no such question (a tag, a reaction, a new thread of his, a
reply with no answer picked) is his words in the session's conversation, never an answer to a thing
that waits: answer it in its thread. When the thing of a card leaves its wait another way (his park
on the board, a newer state block), close the card the same way.
