# The harness contract

A stage of Lem says what to do. How an agent starts a builder, asks the owner or loads
another skill differs between Claude Code, Codex and the next agent the owner tries, and that
difference belongs to the agent, not to the stage. It is written once per agent in this folder,
in a file named after the agent. A stage names a capability from the table and never a tool, so a
new agent is one new file here and no edit to a stage.

| Capability | Meaning |
| --- | --- |
| `load-skill` | bring another skill's instructions into context once, and reuse them while they are there |
| `ask-owner` | put a short choice to the owner and wait for the answer. An interview's questions are no such choice: they are lines in the conversation (`stages/interview.md`) |
| `spawn-builder` | give one task to a fresh agent on the workhorse model, able to edit, run commands and commit in a directory it is given, and already holding the builder's standing rules (`agents/lem-builder.md` in this repository is their text); you are told when it ends, and its reply is one line. The agent's file says whether a builder can start builders of its own; where it cannot, the lead of any plan stops `blocked` and says so, since every task of a plan gets a builder of its own |
| `open-task-session` | start a fresh agent of your own kind in a session of its own, under yours or beside it where the agent's file says so, in a directory it is given, on the model and the effort the settings' `seats.planner` names when it names them, with a brief it reads from a file; the owner can read it and type there; later, send it a message, and close it. Lem opens one for a plan talk only, and closes it when the talk is done |
| `tell-coordinator` | from a plan talk's companion or from a builder that leads a task, send the coordinator one line that wakes it: the task and its new status, or a choice that waits for the owner |
| `second-opinion` | send a plan to talk through to the reviewer: a second agent in the other pane of the session that asks, the agent the settings' `seats.reviewer` names, with its model and its effort when the seat names them, read-only and started fresh for each talk |
| `fan-out` | run several fresh agents over independent inputs at once |
| `ask-experts` | start each expert of the list the experts' brief prints, which are the settings' `seats.experts`, of two model families, each with the agent, the model and the effort its entry names, at one moment, in the background and read-only, each on the same brief file; you are told when each ends, and each one's last message becomes its answer file word for word |
| `run-in-background` | run one command in the background and go on with other work; you are told when it ends, with its exit status and what it printed, and that end wakes you, also while you wait between two of the owner's messages. A stage that names such a command says when one at most may run |
| `show-page` | show the owner something to read (a report, a diff, a table) without asking a question |
| `start-nap` | start a nap (`stages/nap.md`): a fresh agent of your own kind, in the background and with no context of yours, in the state folder it is given, with `prompts/nap.md` as its brief and the nap's time beside it; it can read and write files in that folder and nowhere else, and run no command. You are told when it ends, and nothing of what it prints is for you |

And three roles a stage names instead of a skill id, because the id differs per agent:

| Role | What it is |
| --- | --- |
| the question gate | decides whether a question reaches the owner, from the rulings and from what a probe can answer |
| the persona panel | has the people a decision affects answer it, from the project's cast, before the owner sees it; no generic cast stands in for the project's own |
| the review tool | runs one review round over a range with the project's lenses and profile |
| the tracker | reads a ticket into a task, moves it when its work starts and lands where the project's settings say Lem does, and comments the landing |

A stage may name a skill this repository ships by its id, which is the same in every agent:
`lem-interview-me`, `lem-ask`, `lem-backlog`, `lem-dialectic`, `lem-root-cause`,
`lem-gate`, `lem-panel`, `lem-linear`, `lem-ask-expert`. Each id starts with
`lem-`, so it cannot collide with another skill in an agent that keeps all skills in one flat list.

Each agent's file answers every row, or says the capability is absent and what the stage does
then. A file exists only for an agent the contract was checked in.
