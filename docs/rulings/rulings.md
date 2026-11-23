# The owner's rulings

Each bullet below is a ruling of the owner in force. A ruling is reopened only by asking him.

A bullet is its rule in bold; where the rule alone could mislead, the words after it say how far it
reaches, and a quote is his words. A part marked "(the form is the session's)" is the maintaining
session's form of his ruling, open to him, and not his ruling. The parentheses at the end hold the
day he ruled it, or the days of the rulings a bullet joins. What a test or one place now holds is in
`docs/rulings/history.md`.

## What Lem is, and who it is for

- **Lem is for experienced developers, and every change is measured against that.** Its user is a
  senior developer with little attention to give, never a business reader: "Lem should not make
  simple things complicated". (2026-11-16)
- **What he names in the interview is a direction the plan follows**, a technology or options to
  review. (2026-11-16)
- **One Lem for one repository.** No ability across repositories, and no global Lem. (2026-11-14,
  2026-11-19)
- **Claude Code and agterm first, and Codex for reviews.** The reviewer may be Codex or a second
  Claude, and the harness file for Codex comes after Claude Code works. (2026-11-14, 2026-11-20)
- **Opinionated and small.** Out of scope: a peer-planning flow, a skill-activation hook,
  language-server plugins, output styles, a brainstorm skill, clipboard helpers, a writing-style
  skill. (2026-11-14)
- **The rules of an existing project stay where they are.** Lem reads `.claude/rules` and never
  moves or links a file of it; a move of the rules is a new decision of his ("For now").
  (2026-11-15)
- **Another program's settings stay where that program keeps them.** Lem never moves, links or
  reshapes `.revmux`; the learn stage may write a line there, and names what changed and why.
  (2026-11-14)
- **Three more commands are no commands of his, and two recipes of the agterm cookbook become
  required.** Lem calls `/lem ask` by itself; there is no `/lem annotate` and no `lem-backlog`
  skill: `/webrev` (the way to mark up a plan or a document) and `/backlog` are required recipes,
  none copied into Lem. (2026-11-15, 2026-11-18)
- **Lem is a plugin, and nothing else.** "It should be always installed as a CC/Codex plugin": no
  setup script and no link, and the correction hook comes with the plugin. (2026-11-17)
- **Lem is his one desk for work in a repository, and its core is the path from a request to a
  merged pull request.** A helper stays in the core when a step of the path uses it, and he can then
  call that step by hand. (2026-11-17 and 2026-11-18)
- **Release, last-tag and the review of another person's pull request leave the core.** They leave
  the repository, and `docs/backlog/add-ons-after-the-core.md` lists what may come back as an
  add-on. (2026-11-17 and 2026-11-18)
- **No word of a Lem before is kept; a release reads the records of the release just before it,
  and no older ones.** No older command word and no refusal of a settings key that went; a task
  begun two releases back stops, and its message names the way on. (2026-11-18, 2026-11-23)
- **The shipped skills are for the times he steps in.** (2026-11-16)

## What Lem needs on the machine

- **agterm, the mailbox chat and revmux stay required.** agterm is a hard dependency: Lem does not
  run outside it. agdoc and plannotator-tui are recommended, and Lem installs one only on a
  developer's yes. (2026-11-14, 2026-11-15, 2026-11-17 and 2026-11-18)
- **cronn is required, and Codex is highly recommended.** The machine check fails without cronn and
  `/lem init` stops for it; a scheduled job is still added only on his yes. (2026-11-18)
- **Lem assumes auto mode**, in Claude Code and in Codex. (2026-11-18)
- **Python 3.11 stays, in the modern form.** No script has `from __future__ import annotations`, and
  `lem_python.py` finds a newer Python for `bin/lem` and the hooks. (2026-11-20)

## A request: its type, its track and its commands

- **What must not go wrong is named by topic, and an agent says whether a task is careful.** `/lem
  init` proposes the topics from the code, he adds his own, and an agent judges each task against
  them. (2026-11-15, 2026-11-18)
- **Lem tells the type of a request, asks when it is unclear, and a bug is investigated first.** The
  type is a Conventional Commits type or `question`, from the ask's words alone (the form is the
  session's). (2026-11-16)
- **The first line is where he corrects Lem's read of a request.** A clear read asks nothing; a read
  Lem cannot settle (the size, the type, careful) asks one line in the terminal with its guess,
  before any agent starts, and while he is away Lem takes the safer read. (2026-11-18)
- **The two tracks are the fast track and the standard track.** A text for a person says "the fast
  track" and "the standard track"; "size" means files and changed lines only, and "full" means the
  review only. The records keep their words: `Size: small|full`, `--small`, `prompts/small.md`.
  (2026-11-18)
- **A helper starts from plain words.** "lets braindstorm" works as "interview-me" does, and a model
  unsure which skill fits asks in the terminal with a suggestion. (2026-11-18)
- **A task order in his words stays.** A task also waits when his words put it after another task,
  as after X or when X lands; a lead never removes that order, and says so in its report when it
  sees no need for it. (2026-11-21)

## The interview, the criteria and the personas

- **The personas' read of the acceptance criteria is his to skip, and only when every criterion
  names only the developer.** Lem then asks one fixed question; a criterion that names anyone else
  gets the read, and Lem never skips it on its own judgment. On his yes Lem logs his words, he
  approves the criteria, and the pull request stays green. (2026-11-16)
- **Every project of Lem has personas, and a panel asks the project's own.** `/lem init` ends with a
  cast of two or more people who would notice different things; without one the setup is not
  finished, and no generic cast stands in. (2026-11-15)
- **One approved line of a task is an acceptance criterion.** Every text a person reads, and the
  names of the script, the files and the events, say criterion and criteria; none says story.
  (2026-11-17)
- **A complete ticket that someone else wrote needs his yes to its criteria, and no interview.** His
  yes comes on one page after the personas' read, and Lem scans no ticket for an attack; a request
  he wrote himself runs with no touch. (2026-11-17)
- **Most requests have an interview and his check of the acceptance criteria, and the pull request
  says green or not green first.** (2026-11-16)
- **The personas read first, and their confusion may change the design.** (2026-11-16)
- **When the personas flag a criterion and give a rewrite that keeps its rule, the rewrite is
  taken.** (2026-11-22)

## The plan, the build and the tests

- **The first run is in a scratch repository**, then in a real project. (2026-11-14)
- **Each task of a plan gets a fresh builder.** No threshold decides it. (2026-11-14)
- **The plan talk is a pair in a companion that closes after it, and it can stop a task.** One plan,
  one reviewer and a closed list, "Not task by task", in a companion of the task's session; the
  ladder decides its choices, and it stops a task only by the circuit breaker. (2026-11-16,
  2026-11-17 and 2026-11-18)

## A decision without him: the ladder, the experts and the breaker

- **The owner learns at the end what was decided for him, each with a short why.** The report holds
  those lines itself. (2026-11-14)
- **In doubt, a decision climbs a ladder of opinions, and a count decides, not a model.** The lead,
  the personas, the dialectic, then the experts, and each level logs whether it changed the pick; a
  builder's question about the outcome goes to the personas, not to the reviewer. (2026-11-14,
  2026-11-17 and 2026-11-18)
- **The question gate stays, hidden, and may decide.** It has no command of his, and a decision it
  takes lands in `decisions.md` at the pull request. (2026-11-17 and 2026-11-18)
- **The build asks him nothing, and the ladder always decides.** A decision in the build goes to the
  personas first; a pick past the personas is logged with its story and makes the pull request not
  green, and his away status changes nothing in a build. (2026-11-16, 2026-11-20)
- **Only a circuit breaker stops a task, with a document.** Its two causes: a next step a later "no"
  cannot reverse, or no option that keeps the rule of an approved criterion; "An overrun stops
  nothing". A breaker writes `held`; a machine failure is `blocked` (`docs/rulings/history.md`).
  (2026-11-20)

## The review, the pull request and the merge

- **A review comes before the merge, and a task ends as a pull request.** No plan argued question by
  question, and no review of every task of a usual request. (2026-11-16)
- **Lem's agents file a defect outside the task as a `worth: later` item only when it happens today
  and is one of the "real issues that confuse my users, break contracts, damage data or cost
  money", or when he said it is worth an item, and one under that bar as a `worth: no` item.**
  Its reason line is optional. Cheap is only text that does not run and a check's finding its
  rerun shows fixed, which an agent at work on the branch fixes in a commit that names it; a
  refactor or a removal of unused code outside the task is an item. (2026-11-22, 2026-11-23)
- **The review is routed by an agent that knows what each profile is for.** It picks the profiles
  from the diff, "So documentation does not trigger security or architecture checks"; no code and no
  list of words routes, and `land.py` holds only the floor. (2026-11-16)
- **Landings run in parallel, and the machine's load decides when checks start.** The checks start
  only below `[load] start` of `machine.toml`, 40 when it has no number, and merges go one at a time
  (the form is the session's). (2026-11-20, 2026-11-22)
- **A fresh merge agent reads every proposed task, and merges it or calls him.** The fast track too;
  a pull request that is not green and a careful change call him. `seats.merger` comes from the
  repository, else from `~/.config/lem/settings.toml`, and `branch.land` stays the switch.
  (2026-11-20)
- **GitHub pull requests are the one way to land.** The button on GitHub and `/lem land` are the
  same merge, a task's branch is never merged by hand, and a merge asks no prompt. (2026-11-17,
  2026-11-18, 2026-11-20)

## A task's session, and whether he is there

- **A task runs with him or alone, and he can let go at any stage.** At the end he reads what was
  decided and why, and what was built and why. (2026-11-17 and 2026-11-18)
- **He says whether he is there, and Lem assumes nothing.** His being there is one status that only
  he sets, with `/lem im-away` and `/lem im-back`: no timeout, "no assumptions". (2026-11-18)
- **Each task lives in a session of its own, from its shape to its merge, and there is no Lem
  session.** `/lem` and an idea in any session, or "+" on the board, opens it; a fresh agent takes
  each phase from `handoff.md`, the first with the talk copied in by `lem session talk`.
  (2026-11-19, 2026-11-20)
- **A session that Lem opens never takes the focus, also when it asks him a question.** Only his
  own act selects a session (his pick in the picker, his click on the board, `lem board --follow`);
  one that waits for him shows it by its mark in the sidebar, "Waits for you" and his Inbox.
  (2026-11-23)

## The board and the pages for him

- **The monitor is required**: a board of all tasks, and the board of one task on request, "as
  beautiful as it is now or better". (2026-11-14)
- **Lem asks through its question page.** "every question goes via huddle, unless its something
  fixed choice, trivial, without additional context"; the page is `lem-ask`, and Lem calls it by
  itself. (2026-11-15)
- **A page for the owner has the board's look.** Every page links `skills/lem/assets/lem.css`, and a
  stage builds its page from a pattern beside it. (2026-11-14)
- **What reaches across tasks is the board server's.** It runs `lem land merged` and wakes a task's
  session; it never types into a session, selects one without his click, closes one or decides.
  (2026-11-21)
- **The board is a served app**, Hotwire, rendered on the server, with no database: "I agree that
  sqlite for now might be too much." (2026-11-20)
- **The board's icons are a subset of Font Awesome Pro, in the repository, under his license.**
  `board-icons.json` stays as `tools/board-kit` builds it from his Pro download, and no agent
  reopens this. (2026-11-21)
- **Tailscale is the way from his phone, and nothing supervises the server.** Only his tailscale
  login gets in, never through Funnel, and Tailscale is not required: "if one does not need it -
  then fine, DIY". The SessionStart hook and `lem board` start the server, no login item.
  (2026-11-20)
- **Stories, flowcharts and pictures, early.** Rich media and step-by-step stories in markdown,
  produced early, "for example after acceptance crierions are settled". (2026-11-20)
- **The board takes an answer with a note, never a conversation.** "A note with no option picked is
  refused on the board": the row stays in "Waits for you", and he asks in the session at the Mac.
  (2026-11-23)

## The settings, the seats and the tracker

- **Linear and GitHub Issues, and the local backlog stays local.** `[tracker] kind` is `linear`
  or `github`. A backlog item is never mirrored to a tracker, and Lem makes no ticket from one
  unless he asks. (2026-11-17)
- **No setting counts the tasks that run. A night works its items one after another.** No key limits
  the tasks that run, and nothing stops a start; a night takes four items at most, or the N of `/lem
  night N`. (2026-11-18)
- **The Done column shows the newest ended tasks, and one setting says how long an ended task's
  files stay.** "keep `last N` done items"; one machine may set its own number in its
  `.lem/settings.local.toml`, not in `machine.toml`. (2026-11-21)
- **`[tracker]` has one key**, `kind`: the team comes from the ticket's id, the agent reads the
  team's statuses by their type, and a connection that fails points to Linear's MCP help page.
  (2026-11-18, 2026-11-19)
- **A project's rulings are one list file, one bullet for each ruling under the heading of its
  group.** It holds for every project, as for Lem's own list: `paths.rulings` names the file, and
  no setting names a file for each ruling. (2026-11-22)

## The README, the guides and the logo

- **The logo is the owner's pick** ("The Line in the Field"), the animated scene with a signal from
  Lem's hands to its four agents' red eyes, a living sky in each theme, the same in the README and
  the page. Change it only on his word; the night palette of its dark-theme version is his pick too.
  (2026-11-14, 2026-11-21, 2026-11-23)
- **The README is in ASD-STE100 Simplified Technical English**, easy for a reader who is not a
  native speaker: one topic in a sentence, 20 words at most in an instruction and 25 in a
  description, the active voice, no word only Lem uses as a noun ("ask"). (2026-11-14, 2026-11-17)
- **A guide of `docs/` aims at under 800 words, or a bit more when needed.** The 800 is no hard
  rule: "We are not the army here". (2026-11-22)
- **The skill files keep their own voice.** (2026-11-14)
- **An example in the README that no run produced says that it is an illustration**, and a picture
  of demo data says so in its caption. (2026-11-14)
- **The README and the docs do not report what ran.** No "proven", no "not run yet", no date of a
  run in a text for a reader; the README shows the interaction in a short form or a small flowchart,
  and links to no run. (2026-11-17, 2026-11-18)
- **No history and no reasons in a text for a reader.** `README.md` and `docs/` say what is, never
  what was or why it changed. The rulings list and its history keep days and his words, for the
  agents that change Lem: that reading is the session's, and open to him. (2026-11-17)
- **Lem's docs do not speak for another tool.** Of `.revmux/` in the removal steps: "its not our
  tool". (2026-11-17)

## The lessons, the correction queue, the naps, the night and the free hour

- **The free hour searches and proposes, and makes no branch.** What it finds is a proposal in the
  night's file, and the scheduled retro takes no free hour: "Those proposals should go through
  reviewer Agent and eventually my “yes” first". (2026-11-23)
- **A project that uses Lem gets Lem's improvements only through the agreed paths.** A proposal of
  the night or the retro, the reviewer's read, a backlog item he starts as a task, and its pull
  request. (2026-11-23)
- **Lem naps, and the naps are Lem's look back over its own memory.** An optional part, after his
  own nap brief, and the retro reads its waking note. (2026-11-17, 2026-11-21)
- **The lessons, the retro and Jev stay; a night that builds a backlog item ends as a pull request;
  naps are not shown.** A night writes the criteria itself, builds, and opens a pull request that
  says "not green: you did not approve the criteria", which he approved: "Yes this is what I want".
  The night of Lem's own repository makes no branch and writes proposals. (2026-11-17, 2026-11-18
  and 2026-11-23)
- **The correction queue's switch is the machine's alone, `collect` under `[corrections]` of
  `~/.config/lem/machine.toml`, and the hook works only on its yes.** It holds in every repository
  on that machine, and a repository's file may not hold it: "Looks like this settings `corrections`
  belongs on a machine level only". (2026-11-23)

## Choices of the maintaining session

None of these is his ruling: each is a choice of the session that maintains Lem, and each is open to
him.

- **Lem is a companion, not a gate.** Lem owns its pushes, merges, rewrites and deletions, the truth
  of its words and the path to a pull request; any other failure gets one honest sentence at most,
  and a new mechanism names the act of Lem's that does harm without it. (decided 2026-11-17)
- **Whether a change is careful is inferred from what the owner said must not go wrong, never
  matched from a list of paths.** The ask, the plan and the review of the diff each judge a change
  against `flow.topics`, careful in doubt; the topics come from the main checkout, so a branch
  cannot lift them. (decided 2026-11-16)
- **No project's session edits Lem.** A lesson about a step of Lem is one line in the project's own
  lessons file that opens with the stage's name; in Lem's own repository a stage file is a project
  file, and its edit is a task. (decided 2026-11-17)
- **The mode and the ladder are built in the smaller of two designs.** The ladder is one stage text
  the lead applies; the script checks only two persona votes or more, all for the option taken,
  until a real run shows a lead that records a level wrongly. (decided 2026-11-18)
- **An ask waits for another task when it needs that task's result, not when it names the same
  code.** Two asks that only name the same file or function each start at once, each in a worktree
  of its own. It also waits when his words put it after another task ("A task order in his words
  stays"). (decided 2026-11-17)
- **A task that ended stays ended.** No state moves a task out of `landed`, `answered` or `dropped`,
  and new work on an ended task is a new ask. (decided 2026-11-17)
- **The copied talk stays in Lem's untracked state folder and never reaches git or a pull request.**
  (decided 2026-11-19)
- **Lem lands Lem by a rule, not by machinery.** No copy of the scripts runs a landing, and no step
  is added for it. (decided 2026-11-16)
- **Two reviews of the release, and what the session took.** Not taken: a second load number, a load
  gate for a builder's tests, a `dnd` command word, the parity tool, a guard on who wrote the merge
  verdict, and one on an agent's item that he starts on the board (his start is his word). (decided
  2026-11-21)
