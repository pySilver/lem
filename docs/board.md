# The board

The board shows your tasks in agterm, a browser and [your phone](phone.md), and updates by itself.

## Open it

- Type `/lem`. Lem opens the board in agterm, beside your sessions.
- Type `/lem status <task>` to open one task.
- In a browser on the same computer, open `http://127.0.0.1:4536/`.

The first page lists the repositories that use Lem, each with what waits for you. The address
`/laptop/shop/tasks/gift-note` names the computer, the repository and the task.

## The server

A new Claude Code session in a repository that uses Lem starts the board server, and so does the
first `lem` command of any session. The server shows the board, merges each
[safe change](merge.md#the-merge-review), and wakes a task whose pull request conflicts. It never
types into a session. `/lem serve stop` stops it.

## The views

| View | Key | It answers |
| --- | --- | --- |
| **Tasks** | `T` | Who acts next? One column for each actor. |
| **Waits for you** | `W` | What must I do? [What waits for you](when-lem-needs-you.md#what-waits-for-you), one row for each task. |
| **Backlog** | `B` | What waits for later? The [reviewer's items](#the-reviewers-items), then the backlog in groups by worth, each item with who added it and when. |
| **Activity** | `A` | Where did the time go? A chart of each task, and every event. |

`Cmd-K` (`Ctrl-K` off a Mac), or the **Search** button, finds any task or backlog item by its
title.

`J`, `K`, `↑` and `↓` move a mark in a column, and on **Tasks** `H`, `L`, `←` and `→` move it to
the next column. `Enter` opens the marked task, the session where you answer its row, or a stack.

A task opens in a panel, or as a page on a phone. The keys `1` to `5` open its tabs:
**Overview**, **Criteria and decisions**, **Checks and review**, **Timeline** and **Artifacts**.
The **Overview** gives the next step, and green or not green with each reason. `Escape` closes
the panel.

## Act from the board

Buttons on "Waits for you" and the task pages do what Lem does on your words:

- **New task** (`+`, or the key `N`): type a request, and Lem opens the session of the new task.
  **Start a task** on a backlog item does the same for the item.
- **Merge…**: a page shows green or not green, the pull request and the commit first.
  **Approve** authorizes Lem to merge the commit you see. The approval can carry to a new commit
  after a rebase under [the merge rules](merge.md#merge-it). You cannot undo a merge.
  On a phone, read to the end of the page to enable **Approve**.
- **Open a session**: starts a new agent for a task that has no session, or whose session stopped.

You also answer the questions of a task on the board. Each question has one field for a note:

- **A card**, the question page that a task's session shows in agterm: **Answer the card** opens
  it, with the same options. Your answer closes it there and on each board.
- **A plan** that waits for you to read it: **Build** or **Drop**.
- **A breaker**: **Help**, **Park** or **Drop**. Help sends your note to the agent of the task, so
  Help needs a note.
- **Skip the persona read?** of an interview: **Yes** or **No**.
- **Approve this criterion?** of a small change that another person asked for, and **Approve the
  criteria?** of the standard track: **Yes** or **No**. No needs a note: what to change. On
  **Waits for you**, the row has **Read and approve…**, which opens the card.

**Park** and **Drop** ask you to confirm first. The board takes an answer with a note, never a
conversation. Only the first answer counts.

## The reviewer's items

After each retro, a reviewer agent reads the new
[proposals of the night and the retro](away.md#the-night-and-the-retro). It writes one backlog
item for each area of the proposals that pass, and records each refuted proposal as `worth: no`
with its reason. Git holds `docs/backlog/`, and ignores `.lem/state/backlog/`, the folder of these
items. **Backlog** shows the items that passed first, and the refuted items under "Decided
against".

- The **Backlog** key and the totals of each folder leave out the items with `worth: no`. The
  **Decided against** chip counts them.
- While a task builds an item, the item shows the name of the task. The item leaves the backlog
  when the task merges. When you drop the task, the item is "undecided" again.
- **Drop** removes an item of the reviewer at once, and no later reviewer passes that proposal
  again. While a task builds the item, Lem refuses the drop and gives the name of the task.
