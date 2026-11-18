---
worth: yes
where: skills/lem-linear/SKILL.md
added: 2026-11-18
---
# The Linear status by its type has not run on a real ticket

The `[tracker]` table needs only `kind = "linear"` since 2026-11-18. Lem then takes the team from
the ticket's id and the two statuses from Linear itself: the one status of the type `started` and
the one of the type `completed`, from `list_issue_statuses` for the ticket's team. A team with two
statuses of one type needs the name in the settings (`started`, `landed`); Lem writes nothing to
the ticket there and gives the owner the line to write. One real team has that case: "In Progress"
and "In Review" are both of the type `started` (read from Linear on 2026-11-18).

Nothing of this ran with a model and a real ticket. The tests cover the settings; the procedures
are text in `skills/lem-linear/SKILL.md`. The owner, of that gap: "put into backlog".

What a first real task from a ticket must show:

- Lem reads the ticket with no `workspace` and no `team` in the settings.
- With one status of each type, the ticket moves when the work starts and when it lands.
- With two statuses of a type and no name in the settings, Lem moves nothing, and says the line
  to write.
- `/lem init` in a repository that shows Linear proposes `kind = "linear"` alone, and asks once
  for the status name when the team has two of a type.
- A ticket given by its address, from another workspace than the connection's, stops with a line
  that names both.
