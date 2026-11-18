<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/lem-night.svg">
    <img src="assets/lem.svg" alt="Lem: a tall hooded figure holds one line, and four figures hang from it" width="720">
  </picture>
</p>

# Lem

Type a request in plain words, and get a pull request whose first line says green or not green.
Agents plan, build, test and review the change in your repository, and you merge a green one
without a read.

Lem is a Claude Code plugin for macOS, and it runs in the [agterm](https://agterm.com) terminal.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/screens/board-dark.png">
    <img src="assets/screens/board-light.png" alt="The board of all tasks, in lanes by who acts next" width="900">
  </picture>
</p>

*The board of all tasks. The picture shows demo data.*

## What it looks like

```mermaid
flowchart LR
  request[Your request] --> read{Lem reads it}
  read -->|small| builder[One builder]
  builder --> checks[Checks and one review]
  read -->|full| talk[Interview, criteria, your yes]
  talk --> build[Build and review]
  checks --> pr[Pull request: green or not green]
  build --> pr
```

Two examples of the form, not logs:

```text
you  /lem the footer says Terms, not Terms and condtions
lem  docs, small: "the footer says Terms". Branch docs/footer-says-terms. One builder,
     the checks, one read, then the pull request. Nothing waits for you.
     Wrong read? /lem full, /lem careful.
lem  The pull request is open. Green.
```

```text
you  /lem the export holds the gift note of an order
lem  feat, full: "an export holds the gift note". Branch feat/gift-note-in-export.
     An interview now, then acceptance criteria for your yes. Wrong read? /lem careful.
lem  An order with two notes: both in one cell, with a semicolon? My guess: yes.
you  yes
lem  The acceptance criteria, which two personas read:
     1. Order 1042 with the note "for Ania" has that text in its row.
     2. An order with no note has an empty cell.
you  yes
lem  The pull request is open. Green.
```

## Install

[Install](docs/install.md) lists the tools that Lem needs, and `/lem init` checks each one.

> [!TIP]
> Codex is optional and highly recommended: with it, a second model family reviews the larger
> changes and answers as an expert.

At the root of your repository:

```bash
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

Then start Claude Code in agterm there, and type `/lem init`. Answer three questions, read Lem's
page, and type "land" to accept the setup. Then type `/lem` and your first request.

## What you type

| You type | What happens |
| --- | --- |
| `/lem <request>` | Lem opens a task, and tells you its type and size |
| `/lem` | the list of what waits for you, and the board |
| `/lem status <task>` | the board of one task |
| `/lem plan <request>` | a full change that stops after its plan. `/lem build` builds it |
| `/lem land <task>`, or "land it" | Lem merges the pull request |
| `/lem careful`, `/lem full`, `/lem drop` | you change a task: careful until the merge, full until its pull request, or stopped |
| `/lem away`, `/lem active` | the tasks go on without you, or wait for you again |
| `/lem learn` | Lem puts your correction into the file that owns the step |

In Lem's session, plain words that say the same work too. If you accept them at setup, scheduled
jobs run `/lem retro` each morning and `/lem night` each night.

## What you can rely on

- Nothing merges before your tests pass and an agent that did not build the change reviews it.
- After an interview, nothing builds before your yes to the acceptance criteria, unless you are
  away.
- A change that can affect what you said must never go wrong gets the full review and a merge
  by a person.
- A step that nobody can undo always waits for you.
- Lem never pushes over a commit that it did not push.

## Skills you can call

In Lem's session, plain words start a skill too: "let's brainstorm this" starts `interview-me`.

| Example | Use it when |
| --- | --- |
| `/lem interview-me a faster export` | your request is not clear yet |
| `/lem dialectic this table stays below one million rows` | a plan rests on a claim that you doubt |
| `/lem root-cause the import stops at row 5000` | a defect comes back after two fixes |
| `/lem ask-expert` | you want two expert models to answer the open question, or your own |
| `/lem panel docs/backlog/export-drops-custom-columns.md` | you want the personas to read a text |
| `/lem linear ABC-12` | you want to read a Linear ticket |

## Guides

- [How a task goes](docs/flow.md)
- [When Lem needs you](docs/when-lem-needs-you.md)
- [The pull request](docs/pull-request.md)
- [Install, update, remove](docs/install.md)
- [Settings](docs/settings.md)
- [Connect Linear](docs/linear.md)
