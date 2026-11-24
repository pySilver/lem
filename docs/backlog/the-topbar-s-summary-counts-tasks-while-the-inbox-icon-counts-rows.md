---
worth: later
where: src/lem/board_pages.py:summary_of
added: 2026-11-22
---
# The topbar's summary counts tasks while the inbox icon counts rows

The topbar's summary (`summary_of`, `len(m.for_owner)`) and the kanban's column of the owner
(`m.lane["you"]`) count tasks, while the sidebar's "Waits for you", the inbox icon and the view's own
count count rows (`bm.waits_of`). One task whose merge review calls the owner is two rows, and a "no
session" row belongs to no task of `for_owner`. So with one such task the topbar says "1 waits for you"
and the inbox icon says 2 on the same page, for as long as that state lasts. The first investigation of
counters-in-sync read it in the code and did not run it. A fix picks one unit for every count of what
waits, or says in the summary which one it counts.
