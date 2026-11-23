# The harness contract

A stage of Lem says what to do. How an agent starts a builder, asks the owner or loads
another skill differs between Claude Code, Codex and the next agent the owner tries, and that
difference belongs to the agent, not to the stage. It is written once per agent in this folder,
in a file named after the agent. A stage names a capability from the table and never a tool, so a
new agent is one new file here and no edit to a stage.

| Capability | Meaning |
| --- | --- |
| `load-skill` | bring another skill's instructions into context once, and reuse them while they are there |
| `ask-owner` | put a short choice to the owner and wait for the answer. An interview's questions are no such choice: they are lines in the conversation (`stages/interview.md`). In a task's session the card waits for his answer with no time limit, and the session still takes a wake-up while it waits |
| `inbox-reply` | an answer of the owner's that reaches a task's session from his inbox. While he is away, the board's server sends what waits for him there as the task's session, once, and withdraws it when it no longer waits; his reply comes back into that session, which takes it as his answer to that one thing while it still waits. The session itself never sends a thing that waits to his inbox. Where the agent has no such inbox, nothing goes there, and what waits stays in the session and on the board |
| `spawn-builder` | give one task to a fresh agent on the workhorse model, able to edit, run commands and commit in a directory it is given, and already holding the builder's standing rules (`agents/lem-builder.md` in this repository is their text); you are told when it ends, and its reply is one line. The agent's file says whether a builder can start builders of its own; where it cannot, the lead of any plan stops `blocked` and says so, since every task of a plan gets a builder of its own |
| `open-task-session` | start a fresh agent of your own kind in a session of its own, in a directory it is given, with a brief it reads from a file; the owner can read it and type there; later, close it. Two kinds: a task's own session, which `lem session open` starts for the task, at the end of the workspace and with no focus, and which is woken by a line that is not the owner's input; and the plan talk's pair, which a lead opens under its own session on the model and the effort of the seat `lem project seat SLUG planner` prints (a stand-in while one holds, else the settings' `seats.planner`), and closes when the talk is done |
| `mark-waiting` | show in the sidebar that a session waits for the owner, until he visits it |
| `second-opinion` | send a plan to talk through to the reviewer: a second agent in the other pane of the session that asks, on the seat `lem project seat SLUG reviewer` prints (a stand-in while one holds, else the settings' `seats.reviewer`), with the model and the effort the seat names, read-only and started fresh for each talk; an agent that gives an error goes to `lem project seat-failed`, which names the seat that stands in or blocks the task |
| `fan-out` | run several fresh agents over independent inputs at once |
| `ask-experts` | start each expert of the list the experts' brief prints, which are the settings' `seats.experts` whose agent this machine has (two of two model families, or one alone), each with the agent, the model and the effort its entry names, at one moment, in the background and read-only, each on the same brief file; you are told when each ends, and each one's last message becomes its answer file word for word |
| `run-in-background` | run one command in the background and go on with other work; you are told when it ends, with its exit status and what it printed, and that end wakes you, also while you wait between two of the owner's messages. A stage that names such a command says when one at most may run |
| `show-page` | show the owner something to read (a report, a diff, a table) without asking a question, beside his session and not over it |
| `ask-merger` | start the merge agent of one proposed task: one fresh agent on the seat `lem land merge-review` prints (a stand-in while one holds, else the settings' `seats.merger`, on `claude` or `codex`, with its model and its effort when the seat names them; an agent that gives an error goes to `lem project seat-failed`), read-only, in the background, on the brief file the step wrote; you are told when it ends, and its last message, word for word, becomes the answer file the step named |
| `take-screenshot` | take a picture of a page or a screen as the product runs, in the state the work needs, at a size named in CSS pixels (a desktop window, a phone) with two device pixels for each where the agent can, in the light or the dark scheme asked for, and with none of the agent's own windows, its terminal or another program in it; it is saved as a PNG at the path given, and a view it cannot reach is said so, never drawn |
| `start-nap` | start a nap (`stages/nap.md`): a fresh agent of your own kind, in the background and with no context of yours, in the state folder it is given, with `prompts/nap.md` as its brief and the nap's time beside it; it can read and write files in that folder and nowhere else, and run no command. You are told when it ends, and nothing of what it prints is for you |

And three roles a stage names instead of a skill id, because the id differs per agent:

| Role | What it is |
| --- | --- |
| the question gate | the first level of the ladder: settles a decision a ruling of the owner's, a test or a rule answers, or whose wrong pick is cheap to reverse |
| the persona panel | has the people a decision affects answer it, from the project's cast, before the owner sees it; no generic cast stands in for the project's own |
| the review tool | runs one review round over a range with the project's lenses and profile |
| the tracker | the skill `tracker.kind` names (`lem-linear`, `lem-github`): reads a ticket into a task, marks it when its work starts, and comments and finishes it when the task ends |

A stage may name a skill this repository ships by its id, which is the same in every agent:
`lem-interview-me`, `lem-ask`, `lem-dialectic`, `lem-root-cause`,
`lem-gate`, `lem-panel`, `lem-linear`, `lem-github`, `lem-ask-expert`. Each id starts with
`lem-`, so it cannot collide with another skill in an agent that keeps all skills in one flat list.

Each agent's file answers every row, or says the capability is absent and what the stage does
then. A file exists only for an agent the contract was checked in.

An agent's file is a core, read once per session, with what every phase needs. A capability or a
role that only some steps use may have a part of its own, in a folder named after the agent beside
the core (`claude-code/ask-experts.md`). The core names each part and what it answers, and a session
reads a part at the first use of what it answers, once.
