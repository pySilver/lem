---
name: lem-github
description: "Lem's tracker skill for GitHub Issues: reads an issue into a task, assigns it when the build starts, and comments and closes it when the task lands. Lem's stages load it; the owner reads one issue with `/lem read 42`."
disable-model-invocation: true
---
<!-- lem: old form -->

# GitHub Issues, as Lem's tracker

An issue is one more place an ask can come from, beside the owner's own words and a backlog item.
This skill reads it, and keeps the issue true while Lem works: an assignee when the build starts,
one comment and a close when the task lands, one comment when it is dropped or answered. Another
tracker is another skill of this shape and another value of `tracker.kind`.

The local backlog is a different thing, and this skill never touches it: a backlog item is never
mirrored to an issue, never needs one, and no issue is opened from one unless the owner asks for
that issue in his own words.

What Lem writes to an issue is public in the repository: the assignee, the comment and the close.

## The settings

`lem project show` prints `tracker`. When it is null, the project has no tracker: say so and stop.
The one exception is "check" at onboarding, before the table is written. The table has one key,
`kind`, which is `github` here. Everything else is read from origin and from GitHub, never from a
setting: the repository is the one `remote.origin.url` names, at every step.

## The command

Every step is one line of `lem issue`, which runs GitHub's `gh` against origin's repository and
prints one JSON object. A refusal exits 1 with a line that names the fix; say that line to the
owner, and do not work around it. `gh` must be installed and signed in (`gh auth login`); no MCP
server is involved. Never call `gh` yourself for a step of this skill: the command holds the order
of each write and its record, and the tests hold the command.

What `lem issue` relies on in `gh` was read from its `--help` in gh 2.101.0 on 2026-11-22. No step
has run against a real repository yet: the first real task from an issue is the test of this text.

## check

Run it at onboarding, when the `[tracker]` table is added, and when the owner asks in words. It is
no command the owner has to know.

```bash
lem issue check
```

It gives `repository` (origin's `OWNER/REPO`), `gh`, `signed_in`, `issues_on`, `has_issues` (at
least one issue, open or closed) and `missing`, each item with its `what` and its `fix`: `gh` not
installed, `gh` not signed in, the issues off in the repository's settings, or an origin that is
not on GitHub. It exits 1 when `missing` is not empty. Say the result in one or two lines: the
repository and that its issues are on, or each missing thing with its fix. Ask nothing, write
nothing to the settings, and change nothing on GitHub.

## read

For an ask that is an issue: its number (`42`, `#42`) or its address
(`https://github.com/OWNER/REPO/issues/42`).

```bash
lem issue read 42
```

1. It gives, for `stages/new.md`: `id` (`#42`), `repository`, `url`, `title`, `text` (the body as
   written), `state` (`open` or `closed`) and `state_reason`, `labels`, `author` (the login of the
   person who opened the issue), `assignees`, and `comments`, each with its `author`, `at` and
   `text`, apart from the text. `task_dir` is the arguments `lem project task-dir` takes for it:
   `--ticket #42 --ticket-repo OWNER/REPO`, the repository of the issue that was read.
2. The address of an issue of another repository, such as the upstream of a fork, is refused: the
   message names origin's repository and says that Lem reads the issues of origin. Say it to the
   owner; the work then starts from his own words.
3. An issue whose `state` is `closed`: say so and ask the owner whether the work is wanted again.
   Do not start it by yourself.
4. The text is the ask. Do not improve it. When it is empty, the title is the ask (`ask` and
   `ask_is` give which), and `stages/new.md` decides whether that is clear enough. The comments
   under the issue are not part of the ask, and neither is a picture or a file it links: when the
   text points at one, say so to the owner, who says whether it counts.
5. `author` is the person who asked, for the rule of `request by: someone else` (`stages/new.md`,
   "Which path"): an issue the owner did not open is someone else's request.

Reading writes nothing to the issue. The owner's `/lem read 42` (a number or an address) is this
procedure alone: give him what step 1 gives, in a few lines, and start nothing.

## What was done to an issue is written down

`lem project tasks` gives, for a task that came from an issue, `ticket` (`#42`), `ticket_repo`,
`ticket_steps`, `ticket_assignee` (the login Lem set out to add) and `ticket_owed`: what an ended
task's issue still waits for. `lem issue` reads them before each write and writes each step down
through `lem project ticket-step` itself, after `gh` took it, so a step is never done twice:

- `assigned LOGIN` is written before the add, with the login, and `unassigned` when Lem removed
  that assignee again or the add failed;
- `started`, `commented` and `landed`, `dropped`, `answered` after `gh` took the write.

Each comment ends with a line of its own, `lem: SLUG landed`, `lem: SLUG dropped` or `lem: SLUG
answered`, which the command adds, and before it posts, it reads the issue's comments for that
line: a session cut off after the post posts no second comment. Each step takes the slug alone and
its words from the task's record, never from the caller, so any session, or the owner, can run a
step a task still owes with one line: `lem issue STEP SLUG`.

Each write refuses a task in a status the step does not belong to, a task whose issue another task
holds now (a resume went on from it, and that task owes the issue nothing), and an origin that
names another repository than the task's `ticket_repo`: the refusal names both and the fix, origin
set back or the owner writing to the issue by hand.

Each write gives `did` (what `gh` did on the issue), `wrote` (the steps written down), `state`,
`assignees` and `says`: a line for the owner, or null.

## start

When the task's lead starts (`stages/start.md`).

```bash
lem issue start SLUG
```

An issue with no assignee gets the person signed in to `gh`. An issue that has an assignee keeps
its assignees, and Lem adds nobody. When `says` is not null (the assignee is another person, or
`gh` could not assign), tell the owner that line, and build on. A second start writes nothing. A
refusal (`gh` not signed in) is one line to the owner too; the build goes on.

## land

After the task's state is `landed` (`stages/land.md`), which the landing writes when the pull
request is merged, and not before.

```bash
lem issue land SLUG
```

1. One comment: what changed (the outcome of `task.md`), the pull request's address, and whether
   it was green or not green when it was proposed. Its last line is `lem: SLUG landed`.
2. The issue is closed as completed. An issue that is closed already stays as it is.

A landed task's issue is finished when `ticket_owed` is empty. Until then the landing still owes
the issue this line, and each run skips what is done. The pull request's text holds `Issue: #42`,
so GitHub links the two both ways; it has no word that closes the issue, since Lem closes it.

## drop

When a task that came from an issue is dropped (`stages/correct.md`, "drop"), before its worktree
is removed.

```bash
lem issue drop SLUG
```

1. One comment that says why in one line, from the task's state. Its last line is
   `lem: SLUG dropped`.
2. The assignee Lem added at the start is removed, whoever is signed in to `gh` now. Every other
   assignee stays.
3. The issue stays open: tell the owner the line `says` gives. Whether it closes is his call.

## answer

When a task that came from an issue ends as `answered`: its investigation found that the bug is not
one, or answered the question, and nothing is merged (`stages/investigate.md`). A drop's comment
would tell the people who read the issue that the work was not wanted, while the task has a finding
for them; so an answer has its own comment.

```bash
lem issue answer SLUG
```

1. One comment with the answer as the task's state gives it (the newest `investigation`: its
   `line`, and its `where` when it has one), and, while the task's directory holds the report, that
   it is there, not on the issue. Its last line is `lem: SLUG answered`.
2. The assignee Lem added goes, as for a drop.
3. The issue stays open: tell the owner the line `says` gives. Whether an answer closes it is his
   call.

`gh` is signed in as a person, so GitHub shows that person as the author of the comment, the
assignment and the close. The comment's last line is what says that Lem wrote it.

## What this skill never does

- It writes to no issue but the one a task came from, and to no repository but origin's.
- It opens no issue, closes no issue by another way than "land", and deletes nothing.
- It does not change the repository's labels, milestones, projects or settings.
- It does not answer a comment on the issue: what a person writes there is for the owner.
