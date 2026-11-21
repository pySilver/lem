# Claude Code: show-page and the board

A part of `../claude-code.md`, read when a session shows the owner a page or opens the board.

## The board

`lem board` opens the board as a page companion of this session's group: agterm shows the board
server's address (`agtermctl session overlay open --url URL --persistent --js --companion`), with
its cookies kept, so that a folded column outlives a relaunch of agterm. agterm gives such a page no
bridge (an `--url` page has none: measured in agterm 0.41.1 on 2026-11-20), so what only agterm does, the jump to a session and
the open of a task's session (`lem session open`), the board asks of the server, which runs them
on this Mac.

## show-page

An HTML file opened as a page companion of this session's group, as the board opens, never
as an overlay that covers the session: `lem board --page FILE --name NAME`, with the file's
absolute path and a short name for the sidebar (the task's slug and what the page is, as
`gift-note page`). It opens the page with read access to the folder that holds it, so the page
reads the `lem.css` and `lem.js` beside it, and a second call with the same file reloads its companion. It
prints the companion's id, which `agtermctl session close --target ID` closes when the page is
done with. Outside agterm it refuses: give the owner the file's path to read. A question that
waits for an answer (`ask-owner`, the `lem-ask` page) and a text to mark up still open over the
session, since the session waits for their result.
A document the owner should mark up (a plan, a draft profile) opens with the `webrev` skill,
given the file's path: a recipe of the agterm cookbook that Lem needs and does not bring (the
machine check's `webrev skill` row is required and has its guide). When the session has no such
skill, say so once, with the guide to install it by; then give the owner the file's path to read
as it is, and take the notes in the conversation. Do not install it unasked.
