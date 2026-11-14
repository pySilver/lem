# The harness contract

A stage of the task skill says what to do. How an agent starts a builder, asks the owner or loads
another skill differs between Claude Code, Codex and the next agent the owner tries, and that
difference belongs to the agent, not to the stage. It is written once per agent in this folder,
in a file named after the agent. A stage names a capability from the table and never a tool, so a
new agent is one new file here and no edit to a stage.

| Capability | Meaning |
| --- | --- |
| `load-skill` | bring another skill's instructions into context once, and reuse them while they are there |
| `ask-owner` | put a short choice to the owner and wait for the answer; one question at a time in an interview |
| `spawn-builder` | give one task to a fresh agent on the workhorse model, able to edit, run commands and commit in a directory it is given |
| `second-opinion` | give a plan or a diff to a fresh, read-only agent on the strongest model, of another model family when one is paired |
| `fan-out` | run several fresh agents over independent inputs at once |
| `show-page` | show the owner something to read (a report, a diff, a table) without asking a question |

And three roles a stage names instead of a skill id, because the id differs per agent:

| Role | What it is |
| --- | --- |
| the question gate | decides whether a question reaches the owner, from the rulings and from what a probe can answer |
| the persona panel | has the people a decision affects answer it, from the project's cast, before the owner sees it |
| the review tool | runs one review round over a range with the project's lenses and profile |

A stage may name a skill this repository ships (`interview-me`, `huddle`, `webrev`, `backlog`,
`dialectic`, `root-cause-investigator`) by its name: the name is the same in every agent.

Each agent's file answers every row, or says the capability is absent and what the stage does
then. A file exists only for an agent the contract was checked in.
