---
worth: later
where: tools/board-kit/controllers/stream.js:onVisit
added: 2026-11-22
---
# A back gesture between two addresses of one task shows the snapshot's old counts

A restore from Turbo's snapshot cache (the back gesture, `history.back()`) renders the page as it was
when the owner left it, with the counts of that time. The stream controller opens its stream again only
when the task in the address changes (`onVisit`: `this.task() !== this.watching`), and only a reopen gets
a refresh at once. The second investigation of counters-in-sync saw a restore show the old 4 on the demo
board, which the next refresh corrected in 0.2 s because the task in the address changed. Between two
tabs of the same task (`/tasks/SLUG` and `/tasks/SLUG/criteria`) nothing opens the stream again, so
the snapshot's old counts stay until the next change the stream tells; that case was not tried. A fix
opens the stream again, or renders a refresh, on every `turbo:load` that restored a snapshot.
