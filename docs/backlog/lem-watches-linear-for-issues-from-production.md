---
worth: later
where: skills/lem-linear/SKILL.md
added: 2026-11-27
---
# Lem watches Linear for issues that production raised

The owner's direction of 2026-11-25: Sentry already posts errors from production to Linear, and Lem
"may watch Linear for issues of a given type" — "reading the source of issue, not directly
integrating". Today Lem reads a Linear ticket only when the owner names it (`/lem new ABC-12`); an issue
that Sentry opened waits until he sees it.

What a reader would get wrong: this is not a Sentry integration. Lem reads Linear, which it already
reads through Linear's MCP server, and Linear stays the one source.

Options:

- (a) The board's server reads the team's issues of a type the settings name (a label, such as
  `Sentry`) once an hour, and lists the new ones on the board as proposals, each with its source link;
  the owner starts a task from one with "Start a task", as from a backlog item. Cost: one read an hour,
  one setting, a new row type on the board.
- (b) The night reads them and writes each one as a proposal of the night's file, which the morning's
  reviewer reads with the others. Cost: no new board part; an issue waits until the next morning.
- (c) Nothing: the owner names a ticket when he wants it.

Recommendation: (b). The night already turns findings into proposals that a reviewer reads, and an error
from production that waits until morning is the usual pace of a backlog. Unknown that settles the
`later`: whether the first real tickets from Linear run as `docs/backlog/linear-status-by-type-has-not-run.md`
expects; build this after that item is closed.

Surfaced in the roadmap of the rebuild, "After the cutover" (the owner's answers, decision 20).
