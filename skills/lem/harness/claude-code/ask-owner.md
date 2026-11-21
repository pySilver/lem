# Claude Code: ask-owner

A part of `../claude-code.md`, read at the first question a session puts to the owner.

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

When the owner is away (he left before he answered, or a question starts at a time he said he is
not there), Lem has no channel of its own. Where his own instructions name one, such as an inbox
he reads away from the Mac, the question goes there, with the same case and options; otherwise
it waits for him, and the task's state says what waits. Not checked in a run.

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
