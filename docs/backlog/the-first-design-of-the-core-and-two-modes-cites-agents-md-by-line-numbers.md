---
worth: later
where: docs/plans/2026-11-18-core-and-two-modes/first-design.md
added: 2026-11-21
---
# The first design of the core and two modes cites AGENTS.md by line numbers

`docs/plans/2026-11-18-core-and-two-modes/first-design.md` cites the owner's rulings as lines of
`AGENTS.md`: `AGENTS.md:244-254` for "at the start of every wait", `AGENTS.md:498-502`,
`AGENTS.md:618-621`, `AGENTS.md:507-509`, `AGENTS.md:495-497` (two times), `AGENTS.md:492-494` and
`AGENTS.md:39-50`. Since the rulings moved into `docs/rulings/`, `AGENTS.md` has 523 lines (`wc -l`):
lines 39 to 50 are rules of "Rules for a change here", 244 to 254 links of the rulings, 492 to 509
lines of "Layout", and 618 to 621 lie past its end. Some cites were off before the move too. A
reader who follows a cite lands on another text or on none. A fix names each ruling by its sentence, or by
its file in `docs/rulings/`, in place of the line numbers.
