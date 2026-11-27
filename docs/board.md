# The board

The board updates by itself. One server shows your tasks in agterm, a browser and
[your phone](phone.md).

## Open it

- Type `/lem`. Lem opens the board in agterm, beside your sessions.
- Type `/lem status <task>` to open one task.
- In a browser on the same computer, open `http://127.0.0.1:4536/`.

The first page lists the repositories that use Lem, each with what waits for you. The address
`/laptop/shop/tasks/gift-note` names the computer, the repository and the task.

## The views

| View | Key | It answers |
| --- | --- | --- |
| **Tasks** | `T` | Who acts next? One column for each actor. |
| **Waits for you** | `W` | What must I do? [What waits for you](when-lem-needs-you.md#what-waits-for-you): one row for each task, and one stack for a task with two or more things. |
| **Backlog** | `B` | What waits for later? The [reviewer's items](#the-reviewers-items), then the backlog in groups by worth, each item with who added it and when. |
| **Activity** | `A` | Where did the time go? A chart of each task, and every event. |

Press each key alone, with no Shift. `Cmd-K` (`Ctrl-K` off a Mac), or the **Search** button, finds
any task or backlog item by its title.

`J`, `K`, `↑` and `↓` move a mark in a column, and on **Tasks** `H`, `L`, `←` and `→` move it to
the next column. `Enter` opens the marked task, the session where you answer its row, or a stack.

A task opens in a panel, or as a page on a phone. The keys `1` to `5` open its tabs, and `Escape`
closes the panel:

1. **Overview**: what the task builds, its next step, and green or not green with each reason.
2. **Criteria and decisions**: your criteria, and who took each decision.
3. **Checks and review**: each test command, and what each reviewer found.
4. **Timeline**: who held the work, and for how long.
5. **Artifacts**: the plan, the reports and the pictures.

## Act from the board

Buttons on "Waits for you" and the task pages do what Lem does on your words:

- **New task** (`+`, or the key `N`): type a request, and Lem opens the session of the new task.
  A backlog item has **Start a task**. While the task runs, the item shows the name of the task,
  and the item leaves the backlog when that task merges.
- **Merge…**: a page shows green or not green, the pull request and the commit first.
  **Approve** authorizes Lem to merge the commit you see. The approval can carry to a new commit
  after a rebase under [the merge rules](merge.md#merge-it). You cannot undo a merge.
  On a phone, read to the end of the page to enable **Approve**.
- **Open a session**: starts a new agent for a task that has no session, or whose session stopped.

You also answer the questions of a task on the board. Each question has one field for a note:

- **A card**: the question page that the session of a task shows in agterm. **Answer the card**
  opens the same page, with the same options, pictures and note field.
- **A plan** that waits for you to read it: **Build** or **Drop**.
- **A breaker**: **Help**, **Park** or **Drop**. Help sends your note to the lead, so Help needs a
  note.
- **Skip the persona read?** of an interview: **Yes** or **No**.
- **Approve this criterion?** of a small change that another person asked for: **Yes** or **No**.
  No needs a note: what the criterion must say.
- **Approve the criteria?** of the standard track: **Yes** or **No**. No needs a note: what the
  criteria must say. On **Waits for you**, the row has **Read and approve…**, which opens the card.

**Park** and **Drop** ask you to confirm first. Park, and Yes to criteria, take effect at once. The
session of the task takes each other answer as your typed word.

The board takes an answer with a note, never a conversation: a note with no option records
nothing. Only the first answer counts.

## The reviewer's items

Each morning, a reviewer reads proposals from the night and the retro.
The reviewer writes one backlog item per area for proposals that pass.
It records each refuted proposal as `worth: no` with its reason.
Git ignores `.lem/state/backlog/`, which holds these items.
**Backlog** shows the items that passed first. It shows refuted items under "Decided against".

- The **Backlog** key and the page totals by folder exclude items with `worth: no`.
  The **Decided against** chip counts these items.
- An item that passed and that no task builds is "undecided".
- **Start a task** opens a task for the item. The item leaves the backlog when the task merges, and
  it is undecided again when you drop the task.
- **Drop** removes the item at once, and no later reviewer passes that proposal again. While a task
  builds the item, Lem refuses the drop and gives the name of the task.
