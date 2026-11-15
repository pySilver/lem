---
name: lem-linear
description: "Lem's tracker skill for Linear: read a ticket into a task, move it when its work starts and when it lands, and comment the landing, through Linear's MCP server and as the project's `[tracker]` settings say. Lem's stages load it; an owner may also type \"/lem linear check\" to test the connection, or \"/lem linear MBZ-12\" to read one ticket. Use when a `/lem` ask is a Linear ticket (an id such as MBZ-12 or a linear.app URL), when a task that came from a ticket starts or lands, and when the user says \"linear check\", \"read the ticket\" or \"is Linear connected\"."
---

# Linear, as Lem's tracker

A ticket is one more place an ask can come from, beside the owner's own words and a backlog
item. This skill reads it, and keeps the ticket true while Lem works: started when the work
starts, done and commented when it lands. It is the only tracker Lem has. Another one would be
another skill of this shape and another value of `tracker.kind`.

The local backlog is a different thing, and this skill never touches it: a backlog item is never
mirrored to Linear, never needs a ticket, and no ticket is created from one unless the owner
asks for that ticket in his own words.

## The settings

`project.py show` prints `tracker`. When it is null, the project has no tracker: say so and stop.

| Key | Meaning |
| --- | --- |
| `kind` | `linear` |
| `server` | the name the Linear MCP server has in the agent (`docs/linear.md` of Lem's repository says how it is connected) |
| `team` | the key of the one team whose tickets this project takes, as in `MBZ-12` |
| `moves` | who moves a ticket's status: `lem`, or `tracker` when Linear's own automation does it (its pull-request integration moves a ticket when a pull request opens, is reviewed and merges) |
| `started`, `landed` | with `moves = "lem"`: the names of the two statuses a ticket gets, as that team spells them |

Status names are each team's own, and a status type does not name one status: one team had two
statuses of the type `started` (seen on 2026-11-14). So the settings carry the two names, and
this skill never picks a status by its type.

## The server's tools

The Linear server gives these tools, and your agent shows them under its own prefix for the
server (the harness file says which, and whether a tool loads on its first use): `whoami`,
`get_issue`, `get_team`, `list_issue_statuses`, `save_issue`, `save_comment`. When your session
cannot call them, the server was added after the session started, or it is not signed in: say
that, name `docs/linear.md`, and stop. Never fall back to a guess of the ticket from its URL.

`whoami` takes an optional `source`: pass `lem-linear`, so the calls are known as Lem's.

What follows about each tool's answer was read from the real server on 2026-11-15, with one
ticket of one team.

## check

Run it at onboarding, when the settings change, and when the owner asks.

1. `whoami`. It returns the workspace, the user (`name`) and a `connection` with its `access`.
   One connection is one workspace.
2. `get_team` with the settings' `team`: it takes a key. An answer means that this connection
   sees the team; it returns the team's `id`, `key` and `name`. No answer means that the
   connection is signed in to another workspace than the project's, or that the key is wrong:
   say so and stop.
3. With `moves = "lem"`: `list_issue_statuses` with the team's `id` from step 2 (the tool is
   documented for a team's name or id). The answer has to hold the settings' `started` and
   `landed`, spelled the same. Name each one that is absent, with the names the team has.
4. Say the result in three lines: the workspace and the user with the connection's access; the
   team by its key and name; the two statuses, each as found or absent. Change nothing in Linear.

## read

For an ask that is a ticket: an id (`MBZ-12`) or a `linear.app` URL, where the id is the part
after `/issue/`.

1. The id's letters before the hyphen are the settings' `team`. Check that before any call:
   `get_issue` does not return the team's key. A ticket of another team is refused: this project
   does not take it.
2. `get_issue` with the id. Give back, for `stages/new.md`: the `id` (`MBZ-12`, never the
   `uuid`), the URL, the title, the description as written, the status (`status` is its name,
   `statusType` its type), the labels, and `gitBranchName` when the ticket gives one.
   The parent is not in the default answer. When the ask needs its context, call `get_issue`
   again with `parentId` among its `fields`, and once more for the parent's title.
3. A ticket whose status is already the settings' `landed`, or whose `statusType` is
   `completed`, `canceled` or `duplicate`: say so and ask the owner whether the work is wanted
   again. Do not start it by yourself.
4. The description is the ask. Do not improve it. When it is empty, the title is the ask, and
   `stages/new.md` decides whether that is clear enough. The discussion under the ticket is not
   part of the ask, and neither is an attachment or a picture: when the description points at
   one, say so to the owner, who says whether it counts.

Reading writes nothing to Linear.

## start

When the task's lead starts (`stages/new.md`, "Start a lead"), and only with `moves = "lem"`.

1. Before the first write of a session: `whoami`. The workspace is the one `check` found, and
   the connection's `access` allows a write; a read-only connection stops here, and you say so.
2. `save_issue` on the ticket with the status the settings name as `started`. Nothing else: not
   the assignee, not the labels, not the description.
3. A ticket that is already in that status is left as it is.

With `moves = "tracker"`, write nothing: Linear moves the ticket itself.

## land

After the task's state is `landed` (`stages/land.md`). With `branch.land = "owner"`, after the
owner says that it landed, and not before.

1. `save_comment` on the ticket, in plain words: what the owner gets, the landed range and the
   base branch, the last line of each gate command, and the review item's risk. A decision Lem
   took alone is written as Lem's ("decided without the owner: ..."), never as his.
2. With `moves = "lem"`: `save_issue` with the status the settings name as `landed`.
3. With `moves = "tracker"`: the comment only.

A task that is dropped gets one comment that says so, and no status change: where a ticket goes
when its work is not done is the owner's call.

## What this skill never does

- It writes to no ticket but the one a task came from.
- It creates no ticket, closes no ticket by another way than the settings' `landed` status, and
  deletes nothing.
- It does not change the team's statuses, labels or settings.
- It does not answer a comment on the ticket: what a person writes there is for the owner.
