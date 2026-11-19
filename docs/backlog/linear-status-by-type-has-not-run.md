---
worth: yes
where: skills/lem-linear/SKILL.md
added: 2026-11-18
---
# The Linear status by its type has not run on a real ticket

The `[tracker]` table has one key, `kind = "linear"`. Lem takes the team from the ticket's id, the
server from the agent, and the two statuses from Linear itself: from `list_issue_statuses` for the
ticket's team, the status of the type `started` and the one of the type `completed`. A team with
two statuses of one type gets the one whose name says the step; when the names do not settle it,
Lem moves nothing and says so to the owner. One real team has that case: "In Progress" and "In
Review" are both of the type `started` (read from Linear on 2026-11-18).

Nothing of this ran with a model and a real ticket. The tests cover the settings; the procedures
are text in `skills/lem-linear/SKILL.md`. The owner, of that gap: "put into backlog".

What a first real task from a ticket must show:

- Lem reads the ticket with nothing in the settings but `kind`.
- With one status of each type, the ticket moves when the work starts and when it lands.
- With "In Progress" and "In Review", the ticket gets "In Progress" when the work starts.
- A ticket that an automation of Linear already moved is left as it is, and the step is written
  down.
- `/lem init` in a repository that shows Linear proposes `kind = "linear"` alone, and asks
  nothing about a status.
- With two Linear servers, one for each workspace, Lem uses the one whose teams hold the
  ticket's key.
- A ticket given by its address, from another workspace than the connection's, stops with a line
  that names both.
