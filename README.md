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

## Two real requests

### A small change

```text
/lem the README shows one example of a heading, 3-9 Mar 2026, below the first paragraph
```

Lem answers at once:

> docs, small: "the README shows one example of a heading, `3-9 Mar 2026`, below its first
> paragraph". The branch is `docs/readme-shows-a-heading-example`. One builder now makes the
> change. Then the checks run, one review reads it, and it goes to a pull request. Nothing waits
> for you. Say "full" if you want acceptance criteria for it.

[Pull request #5](https://github.com/pySilver/lem-scratch/pull/5) opened 3 minutes and 41 seconds
after the request. Its first line:

> **Green.** The checks passed with the bar where it was, the review left no must-fix, no
> criterion changed, and no decision was taken by timeout or by the experts.

### A full change

```text
/lem the shop can read a heading back into its two dates, for the import of old reports
```

> feat, full: "the shop can read a heading back into its two dates". The branch is
> `feat/heading-reads-back-into-dates`. First an interview, then acceptance criteria for your yes.
> After that, the task runs to the pull request without you.

Lem asked one question at a time, each with its guess. Then it wrote four acceptance criteria,
rules in plain words with real examples: "`3-9 Mar 2026` reads as 3 Mar 2026 to 9 Mar 2026". Two
personas, people that the change affects, read them before the owner said yes. Then agents built
and reviewed the change with no question.
[Pull request #6](https://github.com/pySilver/lem-scratch/pull/6) opened 26 minutes after the
request, green.

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
| "full" | a small change becomes a full change |
| "careful" | the task gets the full review and a merge by a person |
| "drop" | the task stops |
| "go alone", "go alone for all", "I am back" | one task, or every task, goes on without you until you come back |
| `/lem learn` | Lem puts your correction into the file that owns the step |

Type the words in quotes as plain text in Lem's session. If you accept them at setup, scheduled
jobs run `/lem retro` each morning and `/lem night` each night.

## What you can rely on

- Nothing merges before your tests pass and an agent that did not build the change reviews it.
- After an interview, nothing builds before your yes to the acceptance criteria, unless you say
  "go alone".
- A change that can affect what you said must never go wrong gets the full review and a merge
  by a person.
- A step that nobody can undo always waits for you.
- Lem never pushes over a commit that it did not push.

## Skills you can call

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
