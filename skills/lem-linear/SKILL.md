---
name: lem-linear
description: "Lem's tracker skill for Linear: read a ticket into a task, move it when its work starts and when it lands, and comment the landing, through Linear's MCP server and as the project's `[tracker]` settings say. Lem's stages load it, and its check of the connection runs at onboarding and with the first read of a ticket, never as a command of the owner's; an owner may type \"/lem linear MBZ-12\" to read one ticket. Use when a `/lem` ask is a Linear ticket (an id such as MBZ-12 or a linear.app URL), when a task that came from a ticket starts or lands, and when the user says \"read the ticket\" or asks in words whether Linear is connected."
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
The one exception is "check" at onboarding, before the table is written: it takes the values the
owner gave in the interview, and the table is written only after it passed.

| Key | Meaning |
| --- | --- |
| `kind` | `linear` |
| `server` | the name the Linear MCP server has in the agent (`docs/linear.md` of Lem's repository says how it is connected) |
| `workspace` | the workspace, as its address has it: `acme` for `linear.app/acme` |
| `team` | the key of the one team whose tickets this project takes, as in `MBZ-12` |
| `moves` | who moves a ticket's status: `lem`, or `tracker` when Linear's own automation does it (its pull-request integration moves a ticket when a pull request opens, is reviewed and merges) |
| `started`, `landed` | with `moves = "lem"`: the names of the two statuses a ticket gets, as that team spells them |

Two workspaces may each have a team with the same key and a ticket with the same id, and a
connection is signed in to one workspace. So every procedure below starts with the same test,
and it is not repeated in their steps:

> **The workspace test.** `whoami`. The workspace it returns has the address
> `linear.app/WORKSPACE`, with the settings' `workspace`. When it has another, stop: this
> connection belongs to another workspace, and nothing is read or written there. Say which
> workspace it is.

Status names are each team's own, and a status type does not name one status: one team had two
statuses of the type `started` (seen on 2026-11-14). So the settings carry the two names, and
this skill never picks a status by its type.

## The server's tools

The Linear server gives these tools, and your agent shows them under its own prefix for the
server (the harness file says which, and whether a tool loads on its first use): `whoami`,
`get_issue`, `get_team`, `list_issue_statuses`, `list_comments`, `save_issue`, `save_comment`. When your session
cannot call them, the server was added after the session started, or it is not signed in: say
that, name `docs/linear.md`, and stop. Never fall back to a guess of the ticket from its URL.

`whoami` takes an optional `source`: pass `lem-linear`, so the calls are known as Lem's.

What follows about each tool's answer was read from the real server on 2026-11-15, with one
ticket of one team. The four procedures from "check" to "land" ran on that ticket the same day,
in one task from its start to its landing; "drop" and "answer" have not run yet.

## check

Run it at onboarding, when the `[tracker]` settings change, and when the owner asks in words. It
is no command the owner has to know: the first read of a ticket makes the workspace test and the
team test below, and fails with the same words.

1. The workspace test. `whoami` returns the workspace with its address, the user (`name`) and a
   `connection` with its `access`.
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

1. The workspace test. Then the id's letters before the hyphen are the settings' `team`: check
   that before `get_issue`, which does not return the team's key. A ticket of another team is
   refused: this project does not take it. A URL of another workspace is refused the same way.
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

## What was done to a ticket is written down

`project.py tasks` gives, for a task that came from a ticket, `ticket` and `ticket_steps`: what
Lem did to that ticket so far. Before a write, look there: a step that is listed was done, and
it is never done again. After a write that the server took, write the step down at once:

```bash
python3 SKILL_DIR/scripts/project.py ticket-step SLUG started|commented|landed|dropped|answered
```

`SKILL_DIR` is the `lem` skill's directory. `ticket_owed` in the same output is what an ended
task's ticket still waits for: a later session sees there what a session before it did not
finish.

A session can also be cut off between the two: the server took a comment, and the step was not
written down yet. So each comment of Lem's ends with a line of its own, `lem: SLUG landed`,
`lem: SLUG dropped` or `lem: SLUG answered`, and before a comment is posted, `list_comments` on the ticket is read for
that line. When it is there, the comment was posted: write the step down and post nothing. A
status change needs no such line, because a ticket that already has the status is left as it
is.

## start

When the task's lead starts (`stages/new.md`, "Start a lead"), and only with `moves = "lem"`.

1. The workspace test, and the connection's `access` allows a write; a read-only connection
   stops here, and you say so.
2. `save_issue` on the ticket with the status the settings name as `started`. Nothing else: not
   the assignee, not the labels, not the description. A ticket that is already in that status
   is left as it is. Then write the step `started` down.

With `moves = "tracker"`, write nothing: Linear moves the ticket itself.

## land

After the task's state is `landed` (`stages/land.md`), which the landing writes when the pull
request is merged or the ready branch is on the base branch, and not before.

1. The workspace test, and the connection's `access` allows a write.
2. Unless `commented` is written down, or a comment on the ticket ends with `lem: SLUG landed`:
   `save_comment` on the ticket, in plain words: what the owner gets, the pull request's address or the landed range, the
   base branch, and the last line of each gate command. A decision Lem
   took alone is written as Lem's ("decided without the owner: ..."), never as his. Its last
   line is `lem: SLUG landed`. Then write the step `commented` down.
3. With `moves = "lem"`, unless `landed` is written down: `save_issue` with the status the
   settings name as `landed`. Then write the step `landed` down.
4. With `moves = "tracker"`: the comment only.

A landed task's ticket is finished when `ticket_owed` is empty. Until then the landing still
owes the ticket this procedure, and each step of it skips what is done.

## drop

When a task that came from a ticket is dropped (`stages/new.md`, "When a task is dropped").

1. The workspace test, and the connection's `access` allows a write.
2. Unless `dropped` is written down, or a comment on the ticket ends with `lem: SLUG dropped`:
   `save_comment` that says the task was dropped, and why in one line. Its last line is
   `lem: SLUG dropped`. Then write the step `dropped` down.
3. No status change. Tell the owner which status the ticket has now: where a ticket goes when
   its work is not done is his call, and he moves it.

## answer

When a task that came from a ticket ends as `answered`: its investigation found that the bug is
not one, or answered the question, and nothing is merged (`stages/new.md`, "A bug and a
question"). A drop's comment would tell the people who read the ticket that the work was
not wanted, while the task has a finding for them; so an answer has its own comment.

1. The workspace test, and the connection's `access` allows a write.
2. Unless `answered` is written down, or a comment on the ticket ends with `lem: SLUG answered`:
   `save_comment` with the answer as the task's state gives it in one line (the newest
   `investigation` in `project.py tasks`: its `line`, and its `where` when it has one), and that
   the report is in the task's directory, not on the ticket. Its last line is `lem: SLUG answered`.
   Then write the step `answered` down.
3. No status change, as for a drop. Tell the owner which status the ticket has now: whether an
   answer closes the ticket is his call, and he moves it.

The connection is a person's, so Linear shows that person as the author of the comment and of
the status changes. The comment's last line is what says that Lem wrote it; never leave it out.

## What this skill never does

- It writes to no ticket but the one a task came from.
- It creates no ticket, closes no ticket by another way than the settings' `landed` status, and
  deletes nothing.
- It does not change the team's statuses, labels or settings.
- It does not answer a comment on the ticket: what a person writes there is for the owner.
