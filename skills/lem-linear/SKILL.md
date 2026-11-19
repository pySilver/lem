---
name: lem-linear
description: "Lem's tracker skill for Linear: reads a ticket into a task, moves it and comments the landing. Lem's stages load it; the owner reads one ticket with `/lem read KEY`."
disable-model-invocation: true
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

`lem project show` prints `tracker`. When it is null, the project has no tracker: say so and stop.
The one exception is "check" at onboarding, before the table is written. The table has one key,
`kind`, which is `linear` here. Everything else is read from the ticket and from Linear, never
from a setting: the team, the server and the status.

The team of a ticket is the letters of its id before the hyphen (`MBZ` in `MBZ-12`).

> **The status.** `list_issue_statuses` with the ticket's team, and the status whose type is
> `started` when the work starts, or `completed` when it lands. A team can have two or more of a
> type (a real team had "In Progress" and "In Review", both `started`, read on 2026-11-18). Then
> take the one whose name says that the work began, never one that names a later step (a review,
> a test, a release); for `completed`, the one that says done, never one that says cancelled or
> duplicate (Linear gives those types of their own). When the names do not settle it, move
> nothing, and tell the owner in one line, with the names. The step stays not written down.
>
> **A ticket that is already there.** A ticket whose status is already of the type it would get,
> or of a later one (`completed` is later than `started`; `canceled` and `duplicate` are later
> than both), is not moved, and the step is written down as done. So Lem and an automation of
> Linear that moves a ticket by its pull request never work against each other, and nothing in
> the settings says who moves.

## The server's tools

The Linear server gives these tools, and your agent shows them under its own prefix for the
server (the harness file says which, and whether a tool loads on its first use): `get_issue`,
`get_team`, `list_issue_statuses`, `list_comments`, `save_issue`, `save_comment`. The server is
the Linear MCP server connected in your agent, whatever its name. With more than one (one for each
workspace), use the one whose teams hold the ticket's team key: `get_team` with the key on each,
and the one that answers. When your session cannot call them, the server was added after the
session started, or it is not signed in: say that, name `docs/linear.md`, and stop. Never fall
back to a guess of the ticket from its URL.

What follows about each tool's answer was read from the real server on 2026-11-15, with one
ticket of one team. The four procedures from "check" to "land" ran on that ticket the same day,
with the two status names in the settings of that day and a test of the workspace and the team
that is gone now; the status by its type, "drop" and "answer" have not run yet.

## check

Run it at onboarding, when the `[tracker]` table is added, and when the owner asks in words. It
is no command the owner has to know. It takes a team key: the one the repository shows, or the
letters of a ticket id the owner gives.

1. `get_team` with the key, on the server as above. An answer means that this connection sees the
   team; it returns the team's `id`, `key` and `name`. No answer from any server means that the
   connection is signed in to another workspace, or that the key is wrong: say so and stop.
2. `list_issue_statuses` with the team's `id`, and the status for `started` and for `completed`
   as above.
3. Say the result in two lines: the team by its key and name, with the server that sees it when
   there are two; the two statuses, each as found, absent, or not settled by the names (with the
   names). Ask nothing, write nothing to the settings, and change nothing in Linear.

## read

For an ask that is a ticket: an id (`MBZ-12`) or a `linear.app` URL, where the id is the part
after `/issue/`.

1. `get_issue` with the id. Give back, for `stages/new.md`: the `id` (`MBZ-12`, never the
   `uuid`), the URL, the title, the description as written, the status (`status` is its name,
   `statusType` its type), the labels, and `gitBranchName` when the ticket gives one.
   The parent is not in the default answer. When the ask needs its context, call `get_issue`
   again with `parentId` among its `fields`, and once more for the parent's title. For an ask that
   was a URL, the URL in the answer has the same workspace (`linear.app/WORKSPACE/`); when it has
   another, the connection is signed in to another workspace: say so and stop.
2. A ticket whose `statusType` is `completed`, `canceled` or `duplicate`: say so and ask the
   owner whether the work is wanted again. Do not start it by yourself.
3. The description is the ask. Do not improve it. When it is empty, the title is the ask, and
   `stages/new.md` decides whether that is clear enough. The discussion under the ticket is not
   part of the ask, and neither is an attachment or a picture: when the description points at
   one, say so to the owner, who says whether it counts.

Reading writes nothing to Linear. The owner's `/lem read KEY` (an id or a URL) is this procedure
alone: give him what step 1 gives, in a few lines, and start nothing.

## What was done to a ticket is written down

`lem project tasks` gives, for a task that came from a ticket, `ticket` and `ticket_steps`: what
Lem did to that ticket so far. Before a write, look there: a step that is listed was done, and
it is never done again. After a write that the server took, write the step down at once:

```bash
lem project ticket-step SLUG started|commented|landed|dropped|answered
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

When the task's lead starts (`stages/start.md`).

1. The status of the type `started`, as above. A ticket already there or later is left as it
   is: write the step `started` down and stop.
2. `save_issue` on the ticket with that status. Nothing else: not the assignee, not the labels,
   not the description. Then write the step `started` down.

## land

After the task's state is `landed` (`stages/land.md`), which the landing writes when the pull
request is merged or the ready branch is on the base branch, and not before.

1. Unless `commented` is written down, or a comment on the ticket ends with `lem: SLUG landed`:
   `save_comment` on the ticket, in plain words: what the owner gets, the pull request's address or the landed range, the
   base branch, and the last line of each gate command. A decision Lem
   took alone is written as Lem's ("decided without the owner: ..."), never as his. Its last
   line is `lem: SLUG landed`. Then write the step `commented` down.
2. Unless `landed` is written down: the status of the type `completed`, as above. A ticket
   already there (an automation of Linear moves it when its pull request merges) is left as it
   is; otherwise `save_issue` with that status. Then write the step `landed` down.

A landed task's ticket is finished when `ticket_owed` is empty. Until then the landing still
owes the ticket this procedure, and each step of it skips what is done.

## drop

When a task that came from a ticket is dropped (`stages/correct.md`, "drop").

1. Unless `dropped` is written down, or a comment on the ticket ends with `lem: SLUG dropped`:
   `save_comment` that says the task was dropped, and why in one line. Its last line is
   `lem: SLUG dropped`. Then write the step `dropped` down.
2. No status change. Tell the owner which status the ticket has now: where a ticket goes when
   its work is not done is his call, and he moves it.

## answer

When a task that came from a ticket ends as `answered`: its investigation found that the bug is
not one, or answered the question, and nothing is merged (`stages/investigate.md`). A drop's comment would tell the people who read the ticket that the work was
not wanted, while the task has a finding for them; so an answer has its own comment.

1. Unless `answered` is written down, or a comment on the ticket ends with `lem: SLUG answered`:
   `save_comment` with the answer as the task's state gives it in one line (the newest
   `investigation` in `lem project tasks`: its `line`, and its `where` when it has one), and that
   the report is in the task's directory, not on the ticket. Its last line is `lem: SLUG answered`.
   Then write the step `answered` down.
2. No status change, as for a drop. Tell the owner which status the ticket has now: whether an
   answer closes the ticket is his call, and he moves it.

The connection is a person's, so Linear shows that person as the author of the comment and of
the status changes. The comment's last line is what says that Lem wrote it; never leave it out.

## What this skill never does

- It writes to no ticket but the one a task came from.
- It creates no ticket, closes no ticket by another way than "land", and deletes nothing.
- It does not change the team's statuses, labels or settings.
- It does not answer a comment on the ticket: what a person writes there is for the owner.
