# The board

The board shows every task of a repository in one place, and it updates by itself. One server on
your computer draws it. agterm, a browser and your phone show the same board.

## Open it

- Type `/lem`. Lem opens the board in agterm, beside your sessions.
- Type `/lem status <task>` to open one task.
- In a browser on the same computer, open `http://127.0.0.1:4536/`.

The first page lists the repositories that use Lem, each with what waits for you.
Each repository and each task has an address, for example `/laptop/shop/tasks/gift-note`:
the computer, the repository, the task.

## The views

| View | Key | It answers |
| --- | --- | --- |
| **Tasks** | `T` | Who acts next? One column for each actor. |
| **Waits for you** | `W` | What must I do? One row for each breaker, approval, step of yours, stopped task, plan, merge review, merge and task with no session. |
| **Backlog** | `B` | What waits for later? The backlog, in groups by worth. |
| **Activity** | `A` | Where did the time go? A chart of each task, and every event. |

A task opens in a panel beside the view, or as a page of its own on a phone. Its five tabs have
the keys `1` to `5`, and `Escape` closes the panel:

1. **Overview**: what the task builds, the first line of the task until its next step, and green or not green with each reason.
2. **Criteria and decisions**: your criteria, and each decision with who took it.
3. **Checks and review**: each test command, and what each reviewer found.
4. **Timeline**: who held the work, and for how long.
5. **Artifacts**: the plan, the reports and the pictures of the task.

Each open board changes with the tasks, with no reload. In agterm, it also takes you to the
session of a task.

## Act from the board

Rows of "Waits for you" and task pages have buttons. Each does what Lem does on your words:

- **New task** (`+`, or the key `N`): type a request, and Lem opens the session of the new task.
  A backlog item has **Start a task**.
- **Approve the criteria**: your yes to the criteria that the board shows.
- **Merge**: a page shows green or not green, the pull request and the commit first. You cannot
  undo a merge.
- **Park it**: puts aside a task that a breaker stopped, with one line of why.
- **Open a session**: starts a new agent for a task that has no session.

The page then shows the result, or why Lem refused.

## The board on your phone

Your phone opens the board through [Tailscale](https://tailscale.com), a private network of your
own devices. Only your Tailscale login gets access.

1. Install Tailscale on the computer and on the phone.
2. Sign in to both with the same account.
3. In the Tailscale admin console, turn on MagicDNS and HTTPS.
4. Type `/lem serve tailscale` in Claude Code one time.
5. On the phone, open the `tailscale` address that Lem gives.
6. In the browser's share menu, select "Add to Home Screen".
7. Open Lem from the Home Screen, and open "Waits for you".
8. Tap "Turn on", and allow notifications.

The phone then gets a notification each time something starts to wait for you, also while you are
away. The computer must be awake: when it sleeps, the phone cannot open the board.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/phone-dark.png">
    <img src="../assets/screens/phone-light.png" alt="The board on a phone: the column Waits for you, with three tasks" width="300">
  </picture>
</p>

*The board on a phone. The picture shows demo data.*

## Two computers, one address

1. On each computer, type `/lem serve tailscale` one time.
2. On the computer whose address you open, type `/lem serve join HOST`. HOST is the name of the
   other computer in Tailscale.
3. Open the address of the first computer.

Its first page then lists the repositories of both computers, each under the name of its
computer. When the other computer does not answer, its repositories show "not reachable".

## The server

A new Claude Code session in a repository that uses Lem starts the server, and so does the first
`lem` command of any session. The first session after an update replaces it.

The server tells the session of a task about a merge or a conflict on GitHub. It also opens the
session of a task that waited for another task. When the merge agent gives the verdict merge, the
server merges the pull request. It never types into a session.

## Commands

Type these in Claude Code. Lem runs the `lem serve` command for each.

| You type | What it does |
| --- | --- |
| `/lem serve` | starts the server if necessary, and gives the address of the board |
| `/lem serve tailscale`, `/lem serve tailscale off` | lets your phone in, or closes the door |
| `/lem serve join HOST`, `/lem serve leave HOST` | adds or removes a second computer |
| `/lem serve stop` | stops the server |

The `lem` command is on the path of Claude Code only. After a remote login with no Claude Code,
use its full path:

```bash
~/.claude/plugins/marketplaces/lem/bin/lem serve --ensure
```

`lem doctor` gives this line for your computer.
