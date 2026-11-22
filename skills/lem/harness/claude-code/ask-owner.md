# Claude Code: ask-owner

A part of `../claude-code.md`, read at the first question a session puts to the owner, and at the
first wake or reply that comes from his inbox (`inbox-reply`).

## ask-owner

`lem-ask`, Lem's own page, for every question that asks the owner to choose or to approve: each
option with what the owner would see and what it costs. Lem opens the page each time it asks; the
owner types nothing for it. It is a part of Lem, not a tool of the machine: the machine check has
no row for it, and no page for the owner lists it as one. The plugin puts its `lem-ask` command on
the Bash tool's `PATH`. Outside agterm it exits 3 and opens nothing; then ask in the conversation,
as a numbered list with the recommended option first.

The question itself has one form whatever shows it: one concrete case, the options with what the
owner would see for each, the recommended one with its reason, and the shortest way to answer.
Three kinds of question stay in the terminal under every value: a value the owner types (a name,
a path, a number), a bare go-ahead on a step just described, and a fixed, trivial choice that
needs no context. The owner's global instructions say how a question is told; they outrank this
file.

When the owner is away, what waits for him reaches his inbox through the board's server, which is
its one sender (`inbox-reply`, below). A session sends no question there itself: one that is not a
thing of "Waits for you" (`lem project waiting`) waits for him in the session.

**A card in a task's session** waits for his answer with no time limit, and the session still
takes a wake-up meanwhile: run `lem-ask ask SPEC --timeout 86400` with the Bash tool's
`run_in_background`, and without `--follow`, so that the card takes no focus. The session's turn
then ends while the card is up, so a wake-up reaches it (the mailbox hook hands mail over between
two turns, "A wake-up" in `task-session.md`), and the end of the command wakes it with the answer. Exit 4 after that wait is `lem-ask wait PAGEID` the same way, again.
Exit 2 (`dismissed`) is a card he closed with no answer. Exit 0 with `status: "chat"`, or a `text`
with no option selected, is a question of his or a wish to talk: answer it in the session's
conversation, and put the card up again with the same spec. The overlay covers that session only,
so two tasks' sessions can show two cards at once, where one session shows one at a time (exit 5,
`busy`). Not run yet: a card in a task's session.

## inbox-reply

The owner's inbox is the Plannotator Inbox. While his mark says away, the board's server sends each
thing of "Waits for you" there once, in the thread named by the task's slug, as the task's newest
Claude Code session (`plannotator inbox call --session claude-code:ID`, `lem_inbox.py`), and
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
`lem project waiting`:

- **He is away**, and this session waits for him on the task's row there: put up a card with the
  same answers as the Inbox message, as "A card in a task's session" says, in the background and
  without `--follow`, so that it takes no focus. A breaker gets Help, Park and Drop; a merge, Merge
  and Not now, with the pull request and the commit its review read; a plan, Build and Drop; a
  blocked task or an order of his that names no task, a text answer. Put up no second card for a
  thing whose card is up. His answer on the card is his typed word, and it is the first answer:
  the server then withdraws the Inbox question.
- **He is back**: put up no card; a breaker stays one line and the waiting mark. Read the task's
  thread yourself: `read_thread` with `asked_by: "anyone"` and `project_path` the main checkout
  lists the threads, the one whose `thread_name` is the slug is the task's, and `read_thread` with
  its `thread_id` reads it. A reply of his after its newest question is his answer, taken as below.

**His reply** arrives as a new message that starts `Plannotator Inbox:`, with his words and
"Answers to your questions". It is his answer, as if he typed it in the session, to the one thing its
message named (breaker N, the merge of the commit TIP, the plan, the blocked task, his order), and
only while that thing still waits:

1. Read `lem project tasks` before you act. When the task left that wait (his park on the board or
   his word at the Mac came first, the task is `parked`, a newer state block, another proposal than
   TIP), act on nothing. Answer in the thread, as yourself, that the question no longer applies and
   what took effect, as the board refuses a park whose breaker no longer waits (`act_park` in
   `serve.py`).
2. Act as on his typed word, by the stage that waits for it, and log his decision with his words,
   `--by owner`: a breaker as "After it" in `stages/breaker.md` says, Help with the words of his note
   as his part of the talk. His "Merge" is `lem land merge SLUG --by owner --tip TIP`, TIP the commit
   the question named, so that `land.py` refuses a merge of any other proposal (`expected_refusal`)
   and nothing is merged that he did not read; his "Not now" leaves the pull request open. An answer
   that asks something back or thinks aloud is no pick: say in the thread what you read, and wait
   for his yes there or at the Mac.
3. Close the card when one is up (`lem-ask close`: the card's own command then ends as `dismissed`,
   which here is your close and needs no act), clear the waiting mark (its reverse in
   `../claude-code.md`), and say in one line in the session and in one line in the thread that his
   answer came from the Inbox and what it did. Do this before the stage's own last act (the close
   of a parked or dropped task's session).

A message from the Inbox that answers no such question (a tag, a reaction, a new thread of his, a
reply with no answer picked) is his words in the session's conversation, never an answer to a thing
that waits: answer it in its thread. When the thing of a card leaves its wait another way (his park
on the board, a newer state block), close the card the same way. Not run yet: a reply of his from
the Inbox in a task's session, and `lem-ask close` on a real card.
