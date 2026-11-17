# Lem

Lem is the `lem` skill and the skills it ships: one flow for a unit of work in any repository, with each project's settings kept
in that project's repository. `README.md` says what it does, the pages in `docs/` say how it
works, and this file says how to change it.

## Rules for a change here

- **The skill knows no project.** No repository, product, path or person of a real project appears
  in `skills/lem/SKILL.md`, the stage files, the harness files or the templates, except as the
  dated source of a measurement ("convertiser-server, 2026-11-14"). What a project needs to say,
  it says in its own `.lem/` folder or its own `AGENTS.md`.
- **A stage names a capability or a role, never a tool.** `spawn-builder`, `second-opinion`,
  `ask-owner`, `fan-out`, `show-page`, `load-skill`; the question gate, the persona panel, the
  review tool. `skills/lem/harness/README.md` is the contract. A tool's name belongs in the one
  harness file of its agent. A skill this repository ships is named by its name, which is the
  same in every agent.
- **A harness file exists only for an agent the contract was checked in.** Do not write one from
  another project's notes about an agent.
- **A number in a skill file carries its source and date.** A rule that rests on a measurement
  says so; a rule that rests on a guess says that instead (`READ_AT` in `land.py`).
- **One stage file per subcommand, read only when it runs, and a part that only one path reads
  is a file of its own.** `SKILL.md` holds what is true in every stage. A rule that one stage
  needs goes in that stage. A part of a stage that only one of its paths needs (the interview,
  an investigation, the polish pass) is a file beside it, and the step that chooses the path
  names that file in one line: a small change reads nothing that only a full change needs.
- **Lem's stages and a lead's stages stay apart.** `plan` and `build` are a lead's; the others
  are Lem's. A step that reads a task's code or its diff goes to a lead or to a fresh agent,
  never into `new`, `land` or `review`.
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init --existing`).
- **A change is measured by what it costs a developer on a small task** (the touches it asks of
  him, the waits, the agents it starts) as well as by what it guards.
- **Documentation describes the current state.** No changelog paragraphs, no "previously".
- **A session with nobody at the terminal reads `docs/free-hour.md` first.** It works in a
  worktree of this clone, on a branch, and never pushes: `main` of this repository is what every
  project's next update of the plugin installs.
- **A change to what an open task's record holds keeps reading the form before it.** A
  repository updates the plugin while its tasks are open, so the new scripts meet records the
  scripts before them wrote: a task that is `open` with its pull request, one whose landing was
  cut off, one that waits in the queue. `land.py merged`, `land` and `clean`, `project.py tasks`
  and `may-start`, the board, and the stage text Lem reads again each read what the code before
  the change wrote. So a change to the keys of `landing.json`, to the state names, to the form of
  a state block, an event or an approval, to a file's name in a task directory, or to the
  arguments of `project.py state`, `tasks` and `may-land`, reads the old form too, with a comment
  at the place that says so and a test that takes a task of the older scripts to its end
  (`tests/lem-old-tasks.sh`, `tests/lem-state.sh`). A settings key that changes is refused with
  the line to write in its place, never read silently. A later change may drop an old form, once
  no task that wrote it is open.

## The owner's rulings

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

- **Lem is for experienced developers, and every change is measured against that** (2026-11-16):
  "it is crucial not to forget that this tool is for experienced developers, so it has to be: 1.
  Polished experience 2. Actually helpful, not confusing 3. Opionated but extemely smart and
  pleasant to use 4. Lem would be positioned as an every day Developer's companion 5. Lem should
  not make simple things complicated, otherwise developers will get frustrated so often they will
  stop using Lem", and after it: "Think of Lem as a commercial product (even if its not), not
  half-done half-broken open source project. It has to be easy to adopt, easy to use, easy to
  understand, easy to predict while being complex inside. And boy, it has to be beautiful and
  clear."
- **agterm is a hard dependency**, and so is the mailbox chat from its cookbook. Lem does not run
  outside agterm.
- **One Lem for one repository.** It coordinates many tasks there. No ability across repositories.
- **A review comes before the merge, and a task ends as a pull request.** He chose "build
  first, review after" on 2026-11-14 and reopened it the next day, of commits that reach the
  base branch before a review: "I think its very dangerous in most cases". The flow that
  replaces it is `docs/plans/2026-11-15-three-touches.md` with its amendment, whose intent he
  confirmed with "yes, thats correct" and whose amended page he answered with "all good. lets
  wait for a build." (2026-11-16, as the design session carried it). What stays from the first
  ruling: the persona panel and the review tool with the project's own lenses; no plan argued
  question by question, and no review of every task of a usual request.
- **A project may land with no pull request**, for a developer who works alone and does not want
  their burden: "Yep, fix that. ... When remote GitHub exists, but developer does not want to use
  PR-s it is still valuable to merge with remote main dir, so parallel tasks will not be confused
  (worktrees will all merge with remote main, but without PR). When there is no remote git, then
  OK, merge with local main branch" (2026-11-16). The review still comes first, and who merges
  is still `branch.land`. The form is the session's design: `branch.propose = "merge"` beside the
  default `"pull-request"`, a GitHub remote then landed like any other remote, and onboarding
  asks it with who lands.
- **Claude Code first.** The harness file for Codex comes after that works. The reviewer may be
  Codex or a second Claude; Codex as the builder is wanted later.
- **Opinionated and small.** A developer may use their own tool for a role (`tools.annotate`). Out
  of scope: a peer-planning flow, a skill-activation hook, language-server plugins, output styles,
  a brainstorm skill, clipboard helpers, a writing-style skill.
- **A project can close branches** (`branch.protected`): a rewrite that lands on a branch of its
  own never lands on the release branches.
- **The monitor is required**, "as beautiful as it is now or better" than peer-planning's: a board
  of all tasks, and the board of one task on request.
- **The free hour may edit Lem's skills on a branch of the clone.** It never pushes; the owner or
  a session merges.
- **The first run is in a scratch repository**, then in a real project.
- **The correction hook is an optional part.** Lem recommends the correction queue and uses it
  only when the owner agrees. The hook and the client of its model are Lem's code, with no path
  into another tool's folder, and the owner registers the hook with Lem's setup: "I guess this
  should not be a cc-tools behaviour but Lem code instead … and it should be possible to setup
  during installation of the skill if needed or any time later" (2026-11-15). The form built from
  it is the session's design: `skills/lem/scripts/jev.py`, on the `PATH` as the `lem-jev`
  command, and the hook that the plugin brings, which the tracked `corrections.collect` turns on.
- **As a plugin, the correction hook comes with the install, and the repository says yes for
  all**: he picked "With the plugin; the repository says yes for all" and wrote "I'm divided
  between (1) and (2); I believe Lem will not be a personal preference but rather a way to work
  with specific project. Just like revmux" (2026-11-15; (1) was each person's own yes in the
  untracked file). So `hooks/hooks.json` is a part of the plugin, and the tracked
  `corrections.collect = true` is the consent of everybody who works in the repository.
- **The logo is the owner's pick** ("The Line in the Field"). Change it only on his word. The
  night palette of its dark-theme version is his pick too.
- **Each task of a plan gets a fresh builder** ("I usually start fresh executor for every task..
  since forever"). No threshold decides it.
- **A small defect outside the task is fixed at the end**, in the landing's polish pass, and a
  larger one becomes a backlog item ("Polishing step fixes it in place, right away if thats
  cheap small fixes and offer a backlog filing otherwise"; and on 2026-11-16: "During interview
  and execution there will be some defects that are out-of-scope. This is where backlog
  helps."). The item is filed without a question to him, on the task's branch, and the pull
  request lists it: that form is the design session's, on the page he answered with "all good".
- **A builder's question about the outcome goes to the personas**, not to the reviewer.
- **The personas' read of the acceptance criteria is his to skip, and only when every criterion
  names only the developer**: he asked whether the read should be optional ("In some cases the owner has all the
  knowledge that is needed for task, so personas read would be a pure waste of time and money"),
  and answered "I agree" (2026-11-16) to the proposal a Fable second opinion shaped. A criterion that
  names a person other than the developer gets the read, and Lem asks nothing. When every
  criterion names only the developer, Lem asks one fixed question in the terminal, "The acceptance
  criteria name only you. Skip the persona read? (y/n)". Lem never skips the read by its own
  judgment: it wrote the criteria, and the author of a wrong reading sees it as clear. On his yes
  Lem logs his words and he approves the criteria, and the pull request stays green, because the decision was his. A full
  change with an interview only: for a full change from a complete request the read is the only
  approval and always runs. The form is
  the session's design: his word is the decision `decisions.py log SLUG --by owner --what "the
  personas' read of the criteria" --chose "no read: the criteria name only the developer"`, with his
  answer in `--why` (the texts an older Lem wrote with "stories" still count for a task it took that
  far); `land.py` (`READ_SKIP`) takes a full change with no `criteria.read` only when an
  approval of his follows that decision and both come before the first state that names a lead
  (`lead: builder` or `lead: session`), which is how the script tells an interview from a
  complete request, and its checks then say "the criteria: not read by the personas, on his word (DATE); he
  approved them".
- **Every project of Lem has personas, and a panel asks the project's own**: "every project has
  personas, I don't see why we can have none when Lem is installed for a project" (2026-11-15).
  So `/lem init` always ends with a cast, of two people or more who would notice different
  things, and a project with none has a setup that is not finished: the machine check and the
  status say so, and `cast.py` refuses with the step that writes them. No generic cast stands
  in: the user's and the built-in cast are only what `cast.py init` copies a first cast from,
  and a technical question in a project whose cast has no engineer gets one as a paragraph in
  the panel's brief. For some hours of that day the skill files read his pick "The panel runs
  where the project has personas" as personas being optional; that reading was the session's
  that carries his words, and it is withdrawn.
- **Lem asks through its question page**, and he does not have to type it: "every question goes
  via huddle, unless its something fixed choice, trivial, without additional context". The page
  was named huddle then; it is `lem-ask` now, his call `/lem ask` and the command `lem-ask` ("I
  like your solution for huddle, then name and the way out. `/lem ask` is awesome", 2026-11-15).
  A project's settings may name another way to ask (`tools.ask`), which the same sentence of his
  approves.
- **A shipped skill's name follows `/lem`** ("/lem interview-me sounds perfect like a callout
  command"). The form that was built from it, the id `lem-<name>` and the dispatcher in
  `SKILL.md`, is the starting session's design and open to him.
- **The README is in ASD-STE100 Simplified Technical English**: "We need to use ASD-STE100
  Simplified Technical English (STE) style to describe what we offer here". One topic in each
  sentence, 20 words at most in an instruction and 25 in a description, the active voice, no
  "-ing" verb form except in a technical name, a vertical list for steps. Technical names stay
  exact. This file and the skill files keep their own voice. The README also has diagrams,
  examples and pictures of the board; an example that no run produced says that it is an
  illustration, and a picture of demo data says so in its caption.
- **The rules of an existing project stay where they are**: "ok rules stays for now"
  (2026-11-15). An adopted project's style guide is the folder its agent loads by itself
  (`.claude/rules`); Lem reads it and never moves or links a file of it, because "being able to
  share project rules between Codex and Claude Code is a huge benefit, especially for review
  rounds". Lem has no command that moves linked settings: `/lem migrate` "becomes pointless as
  personas is used in one or two of our projects so we can move those ad-hoc there", and
  `init --existing link` is how an adopted project names its folders. "For now" is his: a move
  of the rules is a new decision of his, and nothing here prepares one. The form built from it
  is the session's design: `project.py rules`, the one match of a change against the files'
  `paths:` scopes, whose answer goes to a builder's brief, the reviewer's message and a review
  round; one format, Claude Code's, until a project needs another.
- **Linear and GitHub Issues, and the local backlog stays local**: he first ruled Linear only,
  "built so that another can be added", and on 2026-11-17 picked "GitHub Issues as a second
  tracker" on a page: "Thats a real gap. Github is most used by typical developers. We cannot
  expect adoption without GitHub support". So `[tracker] kind` is `linear` or `github`, and a
  GitHub issue is read, marked as started and commented on the landing as a Linear ticket is.
  A backlog item is never mirrored to a tracker, never
  needs a ticket, and Lem creates no ticket from one unless he asks. Status names are carried by
  name in the settings ("Linear allows me to configure that", about the branch name: Lem takes
  what the tracker gives and assumes no shape).
- **Another program's settings stay where that program keeps them**: "I think we should not
  touch other apps settings. `.personas` are different, as its our invention". The review tool's
  folder is `.revmux` in every project, new or adopted; Lem never moves, links or reshapes it.
  A lesson may still change a file in it: "I believe learn stage should be able to modify
  profiles, lenses etc and be honest with Human what changes and why". So the learn stage writes
  a lens line, a profile line or a rejected finding there, and names each changed file, what
  changed and why. The cast and the profile are Lem's and move to `.lem`.
- **A developer may ask with a tool of their own**: "We also need a way out, to let dev avoid
  huddle if they prefer their own asker UI?", and of the key built from it, "I like your solution
  for huddle, then name and the way out". `tools.ask`, beside `tools.annotate` and allowed in the
  machine's own file: Lem's page (the default), `terminal`, or the name of a skill or a command.
  `TOOLS` in `project.py` is the one place that names Lem's own tool for each role.
- **The question page is a part of Lem, not a tool the machine has or lacks**: "it does not need
  to mention that 'huddle' dependency is satisfied as it's an internal lem feature" (the page's
  name at that time). The machine
  check has no row for it and no page for the owner lists it; the setup reports its link.
- **webrev is the recommended way to mark up a plan or a document**, before plannotator
  ("`/webrev` is awesome and needs to be recommended to use over plannotator"), and it is not a
  part of Lem. On "a dependency with an offered installation, and no copy in Lem": "yep, just
  like other things that we want to recommend to a developer that makes life easier: agdoc,
  webrev, plannotator-tui, mailbox, revmux" (2026-11-15). So none of the five is copied into
  Lem. webrev, agdoc and plannotator-tui are recommended tools: the machine check has a row and
  a guide for each, `tools.annotate` defaults to `webrev`, and Lem installs one only on a
  developer's yes. The mailbox and revmux stay required, as he ruled before; that reading of
  his sentence is the session's, not his words.
- **OpenRouter is the one way to the Jev model for now**: on a direct API beside it, "Ok. Lets
  keep that way for now" (`docs/backlog/no-direct-jev-api.md`).
- **What must not go wrong is named by topic, and an agent says whether a task is careful**: "we
  analyze the project, then we suggest what are the dangerous zones or topics and let user
  provide more ... Later at a plan time we can understand if it touches anything whats dangerous
  and needs to be taken carefully. Works better than just code path", and "it would be nice to
  get a suggestion from Agent whether its should be safe run or not, human can overlook real
  danger" (2026-11-15). On 2026-11-16, after an audit showed a branch that set `careful = []` in
  its own `.lem/project.toml`, a landing that read the branch's settings and an agent that merged
  it, he asked: "`careful = []` should we have this kind of thing in evolving app? why don't we
  infere whether changes are dangerous from context of the task/plan?" The form is the
  maintaining session's decision, below ("Whether a change is careful is inferred"), not his.
- **The owner learns at the end what was decided for him, each with a short why**: "human needs
  to know about such events in the end and what choices were taken with short 'why'". The
  report holds those lines itself.
- **The README tells a command he types from one a job or Lem runs**: "commands like this should
  be mentioned that it's not supposed to be run by human, but cron or agent?". Each shipped skill
  has a "use it when" and an example there: "how I am supposed to understand which skill does
  what and when I should use it?". It does not name `.personas` ("nobody uses `.personas` but
  me").
- **A check of the tracker is no command of the owner's**: "looks a bit pointless to have a
  command for that. mcp is either working or not". The onboarding and the first read of a ticket
  make the check.
- **A page for the owner has the board's look**: of the first onboarding's page, "a bit old
  school ... just a bit nicer fonts, colors, paddings, round boxes etc.". Every page links
  `skills/lem/assets/lem.css`, and a stage builds its page from a pattern beside it.
- **The backlog is a part of Lem, and its view is a tab of the board**: "Backlog tab - I like
  this idea" (2026-11-15), on the answer that three stages already live on the backlog (the
  night plan picks from it, the closing pass files into it, an ask starts from it). So
  `lem-backlog` stays a shipped skill, not a recommended outside tool, and the board's second
  tab shows the items by who can act, with one action that gives an item to Lem as an ask. The
  content follows a page of his own; no code of it is used.
- **A board of example tasks says so on the page**, and a line that waits for him says where he
  answers. He took a fixture's line for a real one on 2026-11-14.
- **Two experts answer a choice that waits for him**: "also at Lem we will need a skill "ask
  expert" which calls Fable subagent and GPT-6 Astra experts in background. This is good
  solution / way out in a situation where human isn't here to answer the question and we need to
  take a decision" (2026-11-16). On a page the same day he picked "At the start of every wait"
  for when they come in: their two answers are on his card while he decides, their shared pick
  is taken at the end of the wait (the recommended option when they split), and at once when he
  is away. And he picked "Not green" for a choice they decided: one line of the pull request
  names their pick and their reasons, and he reads it before he merges. A step that a later "no"
  cannot reverse is never decided by the experts and waits for him; that one was kept without a
  question and told to him on the page. The form is the session's design: the `lem-ask-expert`
  skill, `decisions.py advise` and `settle --away`, and the harness's `ask-experts`.
- **The plan talk is predictably short, over a closed list**: he asked "What makes it
  predictably short? I don't want them to argue till the end of days. What happens if its a
  design issue that causes endless corrections?", and on a Fable second opinion that proposed a
  closed list and one repair per position, "Fable idea is good. Actually we should borrow the
  idea from revmux which uses the closed list (revmux is weak for plans as I recall)"
  (2026-11-16). The form is Fable's proposal, which he approved, with revmux's rule that a
  finding which comes back stops the loop: the reviewer's first turn is the whole list; each
  question gets one repair; a question that holds a second time is a design choice, asked and
  never settled by an edit; a question after the first turn is "raised, not argued", and the
  review before the pull request checks it; a scope the plan puts out of the change is no
  question. `stages/talk.md` holds the rules, and `project.py`'s `plan.talk` the counts, with
  the bound of 4 × questions + 2 turns, which is derived and not measured.
- **The plan talk is a pair in a companion that closes after it**: "for such review we need a
  pair setup, so Lem (or Lead?) should open a companion where two agents of specific models and
  efforts have a chat about the plan under some rules that disallow endless discussion. This is
  the oppsite than calling fresh context all the time + gives a visibility if Owner want to have
  a look. Companion is closed once discussion is done" (2026-11-16). The form is the session's
  design, which he answered with "Good design!": Lem opens the companion when a builder stops at
  a careful or large plan, and closes it when the task's event log holds the talk's
  `plan.talk`; its left agent is the plan's defender (`prompts/defender.md`), on the seat
  `[seats.planner]` (only `claude`, with a model and an effort), and builds nothing; the build
  goes to a builder lead, one fresh builder per task; and a Fable second opinion's check for a
  layer of patches, which he asked for in "Sometimes the fix in the plan, even during discussion
  is just another layer of patching. It stays ugly but in a different way. And due to cap and
  rules it goes that way. So we need a critical look whether fix is good or just another layer":
  a repair that adds a mechanism names the decision it sits on, the reviewer says `at the cause`
  or `layer over D`, a layer over a decision with no cite closes as a design choice, and
  `plan.talk` counts `root`, `layer` and `shared`. He agreed with the check and asked: "One
  question - whether it will catch an issue where fix should be applied at root level (whatever
  it calls) and that change would trigger number of other issues (sign that such change is
  probably not the best solution)" (2026-11-16). What answers it is the session's design: each
  issue the reviewer finds in a changed decision is a hold of the same question, so such a
  question closes as a design choice, and the card compares the kept decision and its mechanisms
  with the reversed one, its tasks, its acceptance criteria and each issue raised against it.
- **Lem tells the type of a request, asks when it is unclear, and a bug is investigated
  first**: of a small fix taken as a correction with no scout, "Well typically the
  root-cause-investigation is needed to unerstand what triggers the bug that we aim to correct,
  isn't it?"; of the ask "invoices show 0 after a refund", "From such input its kinda hard to
  deduct if we want to investigate the bug or its a feature request. Confusion."; and "Lem should
  try to understand from the requestwhat kind of request it is and ask for clarification when
  confused? We may want to list few keywords for different types of work" (2026-11-16). The form
  is the session's design, to which he wrote "I have no objections for other stuff (work kind,
  merge strategies)": since his note of 2026-11-17 (below) the type is a Conventional Commits type
  or `question`, taken from the ask's words alone, with example words in `stages/new.md` as hints
  and no code that matches them; the first question of the interview when the words do not settle
  it; the type in `task.md` and in a state line `type: TYPE, because WHY`, and the branch's type
  from it; a bug whose cause the ask does not show investigated before any acceptance criterion by a fresh
  builder (`prompts/investigator.md`) that commits a failing test and finds the cause with the
  `lem-root-cause` method, whose report makes it a small fix, a full fix, or ends the task; a
  question that ends with its answer; and the state `answered`, a task that ended with a report
  and nothing to merge.
- **The time card gets exact start times**: asked in his Inbox on 2026-11-17 whether the board's
  time card should get exact start times now, he picked "Build it now: each stage logs its start,
  and the card becomes exact". The form is the maintaining session's: one `NAME.start` event for
  each stage that logged only its end, with a fixed form that `project.py log` checks (`STARTS`),
  and the event that already ended the stage stays its end. `land.py` logs the starts of the
  polish pass, the checks and a review that is due; the stage texts give the line for the
  interview, the scout (with `scout`, its end, which had no event), the personas' read, an
  investigation and each builder's job. `SKILL.md` lists them with their ends.
His review of the README and the docs on 2026-11-17, 27 notes; a quote is his words. Where a note
replaces an earlier ruling, this is the ruling now.

- **Lem is a plugin, and nothing else**: "I see no value in offering Lem as clone ... It should be
  always installed as a CC/Codex plugin. If one needs to customize - they can always clone the
  repo and make their own Lem. I don't want to support both ways here." So there is no setup
  script, no link and no `--corrections`; the correction hook comes with the plugin, and the
  repository's tracked `corrections.collect = true` turns the queue on. This replaces "the
  plugin first; the clone for people who change Lem" (his Inbox answer of the same day).
- **The texts assume a public repository**: "lets assume it's public. I mean its private now,
  because we didn't polish it enough to my standards." The README says nothing about access.
  When the repository becomes public is his.
- **The README and the docs do not report what ran**: "I'm not sure we should keep informing
  audience what we run / what we did not run yet. Our goal is to ship working tool, not a
  promise half-ready tool. So it's our job to run it in real projects, like mybaze and prove it
  works", and of a "What is proven" list: such logs "are confusing for readers". No "proven",
  no "not run yet", no date of a run in a text for a reader. Lem runs in mybaze after this pass,
  with a task he picks (his answer on a page the same day).
- **No history and no reasons in a text for a reader**: "no need to list historical changes and
  reasoning (in any md file) - nobody cares". `README.md` and `docs/` say what is, and never what
  was or why it changed. This file keeps the rulings with their dates and words, because the
  agents that change Lem read them: that reading is the session's, and open to him.
- **The README is easy for a reader who is not a native speaker**: "is has to be easy to read,
  especiall for non-native English speakers ... this first sentence sounds weird `Lem gives your
  ask to the agents that write code in one repository.` ... Employ some subagent specialized in
  American English so it will be easy to understand for everyone, especially technical
  non-english speakers." The STE rules stay; a word that only Lem uses as a noun ("ask") goes.
- **A task has a type and a size, and they are two words**: he found that a bug that "continues
  as a feature" reads wrong ("`feature` path sounds wrong for bug fix"), named Conventional
  Commits ("I am a big fan of Semantic Commits ... maybe our path should be somehow related to
  that schema"), and picked "Type and size apart: small or full" on a page. The type is a
  Conventional Commits type, `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`, and
  `question` for a task that commits nothing. The size is a small change or a full change, and
  careful is a mark on top. Lem's first line says both ("fix, small"). The kind `correction` is
  gone: small is a size, never a type.
- **One approved line of a task is an acceptance criterion**: "should we use `User Story` or
  `Usecase` to avoid confusions? Stories are sometimes taken as "epic task"", and on the page he
  picked "Acceptance criterion". Every text a person reads, and the names of the script, the
  files and the events, say criterion and criteria; none says story.
- **A seat is written `agent/model:effort`**: "People typically use `provider/model:effort` or
  `provider/model@effort` ... I personally prefer `codex/gpt-6.1-sol:high`". The settings, `/lem
  reviewer` and the experts use that one form.
- **`/lem ask-expert` takes a question in words, or none**: "during discussion or interview I
  would like to get an expert opinion, I may then provide context directly in command `/lem
  ask-expert what would be the best solution for this kind of problem` or just type the `/lem
  ask-expert` and assume the skill knows what to ask from the context"; `/lem ask-expert
  gift-note 3` "looks totally weird". Who the experts are and at what effort is in the settings.
- **`/lem ask` with no question takes the agent's last question**: "Can we use `/lem ask
  <question>` whithout question in a situations when Agent gave us a question in terminal and
  our intent is to have a rich contextual question instead?"
- **A plan's file is `YYYY-MM-DD-<slug>.md`**, and the settings can change the form: "I'd rather
  use `docs/plans/YYYY-MM-DD-<slug>.md` (let the user configure in settings)".
- **The state of Lem is not in the git directory**: "Is that a best practice to keep things in
  `.git/lem/`? It smells to me. Maybe it's better to keep those in untracked `.lem/something`
  dir?" The session checked one more reason: Codex's sandbox keeps `.git` read-only
  (`codex-rs/protocol/src/permissions.rs`, read 2026-11-17).
- **What waits for the owner is one list, with a decision for each item**: "maybe we need some
  morning digest command for that? Something that will allow human easily review the proposals
  ... and take a decision: approve, reject, postpone (keep undecided)". The session's form: the
  bare `/lem` is that list, and no new command. The free hour is the maintainer's and is no page
  of the user docs.
- **Lem naps**: "Should we introduce short nap times for Lem? It's extremelly fun to see Agent's
  dreams and things that bothers Lem can be used in `retro` from the latest naps", with his own
  nap brief as the model, and "Its not worthy to keep more than a week or a month (?) naps
  history. Idk - I cant prove its valuable at all but its cool and may improve Lem." An optional
  part.
- **No CI on a push for now**: "No need to run CI for now at Github. We can limit runs to local
  suits for now." The workflow starts by hand.
- **Lem's docs do not speak for another tool**: of `.revmux/` in the removal steps, "its not our
  tool".
- **Codex in each role is wanted**, as `docs/backlog/codex-in-each-role.md`.

- **A complete ticket that someone else wrote needs his yes to its criteria, and no interview**:
  an audit found that nobody at the terminal reads such a ticket before Lem builds it. On a page
  of 2026-11-17 he picked "Your yes to the criteria, no interview", and wrote: "I believe
  `security` profile of the revmux run will catch it. On the other hand Lem does not expect
  hackers being inside the team. it would be a wrong tool to make a prefilter of the incoming
  tickets." So the lead of such a request stops after the personas' read for his yes on one
  page, and Lem scans no ticket for an attack. A request he wrote himself runs with no touch, as
  he confirmed on 2026-11-16.

- **After a merge, Lem repairs only a pull request with a conflict**: the session had built a
  rebase and a new check of every open pull request after each merge. Asked for options on a
  page (2026-11-17), he asked "What is the typical strategry for teams that work via GitHub?";
  the answer was that most teams update a branch only on a conflict, and that a pull request bot
  does the same by default (Renovate's `rebaseWhen: auto`), and to "Lem repairs only a pull
  request with a conflict" he wrote "Great!". Every other open pull request waits for `/lem
  land` or for his click on the forge.
- **One way to merge in each project, and no prompt**: of a prompt at each merge by his word he
  wrote "private, solo dev projects - thats unwanted friction. Maybe it has to be a rule? If one
  files a PR to Github, then the only way to merge would be via api call to gh? If one does not
  use github PRs, the merge directly?", and to the answer that `branch.propose` decides exactly
  that he wrote "Great!". With `"pull-request"` every merge goes through the forge, whose own
  rules guard it; with `"merge"` Lem lands directly. The permissions that onboarding proposes
  hold no `ask` rule.

The session's answers to his notes that asked a question, each open to him: `[gate]` is renamed
`[checks]` ("I dont understand this section in settings at all"); a lead that finds at its plan
that its task needs the result of another open task queues it behind that task ("Will Lem put
new plan on queue instead of running it?"); a shipped skill starts only by its `/lem` name and
from Lem's stages, and the plugin's commands carry Lem's name, so that they do not meet a
developer's own skills and commands ("What are the critical points in Lem that may conflict with
existing Claude Code setup of the Developer?").

Designs taken on 2026-11-14 and 2026-11-15 after a question of the owner's. They are open to
him, and they are not his rulings until he says so:

- **`/lem annotate FILE` is the owner's verb for marking up**, after "then shouldn't it be
  `/lem annotate`?": it runs what `tools.annotate` names, as `/lem ask` is his verb for a
  question.
- **`/lem build` takes a plan file too, and lists the waiting plans when it gets no name**,
  after "why not `/lem build <path to plan>` instead?".
- **Lem is a Claude Code plugin**, after "can we make it more self contained? lem is aimed to be
  per-project companion" and his "I agree" to a test first. The test ran on 2026-11-15; on
  2026-11-17 he ruled that the plugin is the only form (above). The plugin's files are
  `.claude-plugin/plugin.json` with no version (so each commit is an update),
  `.claude-plugin/marketplace.json`, `bin/` with `lem`, `lem-ask` and `lem-jev`, and
  `hooks/hooks.json`. The builder is `lem:lem-builder`.
- **One person can say no to the correction queue, and nobody is switched on by a file git does
  not show**: `[corrections] collect = false` in `.lem/project.local.toml`, and never `true`
  there. A design of the session that carries his words, for the half of him that leaned to
  each person's own yes.

- **The reviewer's seat is a table**, after "should we or can we specify model and effort level
  of the reviewer?": `[seats.reviewer]` with `agent`, `model`, `plan_effort`. Its `effort` for
  the review of a diff went on 2026-11-17 (the maintaining session's, from audit W7): the pane
  opens for the plan talk only, and no step used it. A file that still has the key is read and
  the key is not used.
- **Lem brings its own builder agent**, after "it feels like we need to bring our own lem-worker
  agent which product may override? ... someone elses setup may have none": `agents/lem-builder.md`
  (his `lem-worker`; named for the role every Lem text uses), on Opus at high effort, overridden
  by a project's own file of the same name.
- **One machine may name its own reviewer for a while**, after "I may want to have a session
  based reviewer ... Codex is down or I run out of tokens there": `.lem/project.local.toml`,
  untracked, read from the main checkout, limited to `[seats]`, `[tools]` and the few keys one
  machine may set for itself (`LOCAL_TABLES` in `project.py`), its seat written by `/lem reviewer`.
  Lem never changes the seat by itself.

His notes of 2026-11-16 on the page of the new flow, as the design session carried them to the
session that builds. `docs/plans/2026-11-15-three-touches/amendment-2026-11-16.md` has each in
full, with what was designed from it.

- **The user of Lem is a senior developer with little attention to give**: "Assume that persone
  that works with Lem will be a skillful developer with many years of experience. Not a business
  person. Its just a developer that does a lot of things in many projects, so his attention is
  limited. But he may tell to use this and that technology or reivew options during interview."
  No text of Lem writes for a business reader. What he names in the interview is a direction
  the plan follows.
- **Most requests have an interview and his check of the acceptance criteria; a green pull request he merges
  without a read**: "most of the time there will be interview and there will be user stories to
  check by Lem user. PR review - not necessarily, I think most of the time if everything is
  green he will be merging it blindly." So the pull request says green or not green first.
- **The personas read first, and their confusion may change the design**: "any confusion raised
  by persnas check will drag attention and may turn into design change."
- **A polish pass is a step of the flow**: "Polishing step, sadly is unavoidable (most likely)
  ... this step is looking for very specific things, ulike other steps and review profiles".
  Where it runs (after the last task, before the checks and the review) is the design session's.
- **A decision in the build goes to the personas first, and waits for him 15 minutes at most**:
  "Tech lead should first gather personas opionions and if its clear choice - pick it, log the
  even so it will be presented at PR review time. If choice is unclear - one can try to reach a
  Human and if there is decision taken in 15 min, then Tech Lead picks a recommended action and
  logs the event". The design session reads the last part as "if no decision comes"; a step
  that a later "no" cannot reverse is never taken by timeout, which is its design.
- **A partial review is a review**: "Revmux can have degraded run, as well as personas check.
  Thats fine - just log and proceed. Its still a review and read, it's just not perfect." A
  review that nobody answered counts as none: the design session's.
- **The review is routed by an agent that knows what each profile is for**: "'One read' at the
  end is really useful only for small simple changes ... Serious changes usually require revmux
  run", and "It will be useful if routing Agent will decide what revmux profiles are worthy to
  be run in this particular plan judging by the diff and knowing what profiles do what. So
  documentation does not trigger security or architecture checks." No code and no list of words
  routes; `land.py` holds only the floor.
- **A plan may end with a documentation task**: "There is a documentation update step. It
  belongs to a plan".
- **The shipped skills are for the times he steps in**: "all those cool skills of Lem are useful
  in interactive mode when human actually does review things (at any point) and they are
  actually here to help him work with context".

A lowered bar (a new suppression, a skipped or deleted test, fewer assertions) makes a pull
request not green also when the plan gives its reason: the design session's decision of
2026-11-16, told to him as its own, and open to him.

## Decisions the maintaining session took

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

- **Every decision that is the owner's takes one path**, at plan time as in the build: the
  persona panel (`lem-panel`, the lead's step), then `decisions.py ask` with one concrete run
  (`--case`, `--case-was`, `--cause`, which the card shows above it), the wait of
  `flow.decision_wait` while the rest goes on, and then the experts' shared pick or the
  recommended option, not green. The question gate (`lem-gate`) sits at Lem's card. A decision
  of the plan no longer holds the task: it was the one place where his wait had no end. `held`
  keeps what has no options: the criteria that wait for his yes (a type only he may change among
  them), one more fact for an investigation, a step that is his to do, and an irreversible
  choice that every task left needs. A night plan asks no such decision, since nobody is there
  and every wait would end without him: its brief says `night: yes`, `decisions.py ask` refuses
  it, and the draft ends on the decision as before.
- **A plan talk's record is taken as it ran.** The bound of 4 × questions + 2 turns stays the
  rule of `stages/talk.md`, which the defender keeps. The script no longer refuses a
  record over it, nor one in which a second question on a decision did not close as a design
  choice: such a record is a fact, and its refusal left the companion open and the request
  unproposed for ever. `project.py log` adds the bound to the event as `bound`, and the pull
  request's line of the talk and the board say "N turns, over the bound of M for its Q
  questions". The checks that only a miscount breaks stay, and so does the floor of two turns.
- **Lem lands Lem by a rule, not by machinery**: the rule on what a landing reads after its
  merge, in "Rules for a change here". No copy of the scripts runs a landing, and no step is
  added for it. The backlog item that asked for one of the two is closed by the rule.
- **Where the stages keep what the amendment of 2026-11-16 says otherwise.** Its note 3 has the
  lead change a criterion a persona doubted before the owner sees it; the stages keep the criterion as
  written, with what the lead would change beside it as a proposal, because no agent rewrites
  his contract before he reads it. "Not green" stays for every choice the experts or the timeout
  took, where the amendment names only the timeout. The polish pass never runs for a small
  change: the weight of a step follows the size of the change.
- **Whether a change is careful is inferred from what the owner said must not go wrong, never
  matched from a list of paths**, after his question of 2026-11-16 in "What must not go wrong is
  named by topic". A list of paths goes stale as the code moves, misses new code, is a second
  thing to keep, and can be edited by the branch it guards. So `flow.careful` and `project.py
  careful` are gone, and `project.py` refuses a settings file that still has the list, with the
  sentence to write in its place. `flow.topics` is the one setting: sentences in the owner's
  words, proposed at onboarding by one question, "what must never go wrong here?". Three agents
  judge a change against them, and in doubt they say careful: Lem at the ask, from its words and
  the scout's facts, in the first line it says to the developer, and an ask in reach of a topic
  is never a small change; the lead at the plan, by a topic or a pattern other code will copy; and
  the fresh agent that reviews the diff before the pull request, whose record holds `careful`
  and `careful_why` and which runs the full set when it calls careful what the plan did not. The
  last is the look that takes the place of the path list's floor: its judge did not build the
  change. `land.py` enforces what the records say: a review record with no call is refused, a
  request is careful when the plan (its `careful: yes` under its title, in any commit of the
  branch), the owner's word in the brief or the newest answered review says so, and an agent
  merges only a green request whose newest review said not careful. `careful.missed` is the
  event for a careful call of the review that the plan did not make. The topics cannot be lifted
  by the branch they guard: `project.py` reads the main checkout's settings (its working tree
  while it is on the base branch, the base branch's commit while another branch is checked out
  there, `committed_settings`), and in a task's worktree it takes `[flow]` and `[naps]` from there
  too, so the landing, the lead, `decisions.py` with `flow.decision_wait` (audit findings S1 and
  W2) and the review read the main checkout's table, and `land.py` reads every setting from it
  wherever it runs. A change whose diff edits
  `.lem/project.toml`, in any table, is careful by the script: the one rule that is a match and
  not a judgment, because the file is Lem's own. The same holds for a diff that puts the
  machine's own `.lem/project.local.toml` into git (the second audit, N5). And a task in
  `landing` or `open` takes no state of a lead (`queued`, `building`, `planned`, `ready`,
  `drafted`): a lead that woke late wrote `ready` over an open task and its landing ran again
  (N1). `ready --start-over` is the one way back, and only `land.py`'s messages name it.
- **The size of a change decides its path** (2026-11-17), under his "Lem should not make simple
  things complicated, otherwise developers will get frustrated so often they will stop using
  Lem" and, of a polish agent with nothing to do on a typo, "That is exactly one of the cases
  that may frustrate the Developer" (2026-11-16). An audit that day walked ten everyday asks
  through the stage files: a typo started 6 to 11 agents and took 15 to 32 minutes to its pull
  request, a one-rule correction 6 agents and 15 to 25 minutes, against about 4 minutes measured
  for a correction in the first flow, and a lead read about 18,500 words before it acted (the
  times are unmeasured estimates built on the skill files' measurements; the words are `wc -w`
  of the files a lead reads). So a small change, one plain change with one acceptance criterion in his own
  sentence, no topic in reach and no question open, whatever its type, has one builder and no
  lead: `prompts/small.md`, a brief complete in itself, and the builder's standing rules. It
  commits no plan; its criterion is `criteria.md` in the task directory, approved in his name, with
  its test line, and `criteria.py` and `land.py` read it there when the branch has no plan file,
  for a small change only. A change that keeps behavior has `no test`; its builder runs the tests of the files it
  changed and of their direct callers, and the checks run the whole suite one time. Before it commits, the builder reads its change against the topics and stops
  with `the criteria wait for the owner: the small change is a full change` when it reaches one, needs
  a second rule or a decision, lowers the bar or grew. Its landing is `start`, `base`, `checks`
  (with `criteria.py red` once), one read by the review agent itself, and `propose` with a short
  text; no polish pass at all, and its builder files what it sees outside the change. A small
  change that is
  careful after all (by the review's call or its edit of the settings) is not green and a person
  merges it, since it skipped the interview, the read and the plan; one that lowers the bar is
  refused by the checks. Lem says the type and the size, the branch, the criterion, what happens and what he must do
  in one line before anything runs, and nothing repeats it. Counted from the text after the
  change, a typo, a rename and a one-rule fix each start two agents (the builder and the review
  agent), and the builder reads `prompts/small.md` and `agents/lem-builder.md`, 1,954 words
  (`wc -w`: 775 and 1,179, at 15d5697, 2026-11-17).
- **A full change has one approval and no ceremony that nobody asked for** (2026-11-17), from the same
  audit's findings: the interview's restate and explicit yes were a second approval of what the
  criteria say (F3), so the interview's questions come from the `lem-interview-me` method and its
  restate and yes are the criteria and his yes to them; each question is one line in the
  conversation with Lem's guess, and no page opens for it. A criterion whose change keeps behavior (a
  rename, a bump, a refactor) is held by the suite, `- no test: the change keeps behavior; the
  suite holds it`, and the checks run that suite one time, where a contrived failing test was
  asked before (F4). "A new kind of test" no longer makes a plan careful: a pattern is product code
  that other code will copy (F5), since a one-line fix could become a plan talk and the full
  review by it. A task has a state block from the moment it opens, `held` with `the interview
  waits for the owner` and the type line, so the status and the board show it during the
  interview (W6). The plan talk is `stages/talk.md`, which only the defender reads: it was half of
  `plan.md`, and every lead read it (F11; a lead read about 18,500 words before it acted, `wc -w`,
  2026-11-16).
- **The status knows what merged** (2026-11-17). The audit found that only a landing ran `land.py
  merged`, so a pull request he merged on the forge showed as open in the morning and a task
  queued `after:` it waited with nobody to act (F2, W3). So before a status, and at each turn of
  Lem's where it reads `decisions.py pending`, Lem runs `land.py merged` for each `open` task with
  a pull request, takes the steps after a merge, and looks at the queue. The status changes what
  already happened and nothing else. The night report rule read "newer than the last status
  shown", which no file records; it is now a report of that night or the one before that names a
  draft still `drafted`, which a fresh session can read from the files.
- **Onboarding asks three questions** (2026-11-17). The audit counted about ten questions and
  several offers before the first task, each a page, and 20 to 40 minutes to it (F10, an
  unmeasured estimate). `/lem init` asks only what only the developer knows: what the product is
  and who it is for, the people a change affects (two or more, his ruling), and what must never
  go wrong, each with Lem's proposal from the code. Every other setting is read from the
  repository or defaulted and shown on the hand-over page as an assumption he corrects with
  "change ...": who lands (`owner`), a pull request where the remote is GitHub, what lands, the
  closed branches, the tracker (none, or Linear when the repository shows it, after the
  tracker's check), the reviewer and the defender with their models, and the folders already
  there, linked: shown on the page with the word that changes it, so the choice is the owner's and
  no default is silent. The offers (the correction queue, with what he agrees to, the
  recommended tools, cronn and the scheduled jobs) are one short list at the end of the page,
  never a question each. The reviewer seat's `effort` for a diff and the diff half of
  `prompts/reviewer.md` are gone (W7).

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

- **Every edit of the settings file is careful** (A1). The script guarded only `[flow]` and
  `[gate]`, so a branch that changed `branch.land` from "owner" to "agent" in its own
  `.lem/project.toml` got one read, no careful call and a green pull request, and the same held
  for `[branch]`, `[corrections]`, `[seats]` and `[paths]`. A list of the tables that matter is a
  second thing to keep and misses the next one. So `land.py` calls careful any diff that touches
  the file, with that reason: the file is Lem's own and rarely edited, so the cost is a person's
  merge of a rare change.
- **A task that ended stays ended** (A2). A stale wake-up wrote `building` over a landed task, and
  in the audit's probe `landing.json` lost `merged`, `pr` and `gated`. So `project.py state`
  refuses a move out of `landed`, `answered` or `dropped`, `may-start` refuses a task that is
  `landing`, `open` or ended, and `stages/stopped.md` starts a lead only for a task that is `building`
  or has no new state block. New work on an ended task is a new ask.
- **A plan never makes a change small** (A3). A lead could write a small change's size line in a
  plan, for a full change from a complete request or at night, and then no approval, no read of
  the criteria and no polish pass was asked: the probe's plan went through the gate, the read and
  `propose` green, and `land --by agent` landed it. A one-rule ask is a small change, with its
  criterion in the task directory, approved by Lem with `--small`. `criteria.py` and `land.py` refuse a
  plan file that says `Size: small` (or `Kind: correction`, the line of an older Lem), and a night that meets an item that is one plain change drafts no plan and
  names it in the night report as ready to start as a small change.
- **The checks remove what their own commands leave** (R3, the first run). `python3 -m unittest`
  left two `__pycache__` folders in a repository with no `.gitignore`, the gate refused the tree,
  and the first small change ended in a second task for the ignore rule. The guard serves
  "nothing lands that the checks did not pass on", which is about the committed tree. So the
  checks note the untracked files before they run, remove the ones their commands created, name
  them, and refuse only a changed tracked file; onboarding proposes the ignore lines for what
  the commands leave, in its own commit. In the second run the same gate passed.
- **A small change never gets a polish pass** (R1, the first run). Its builder reported one
  defect outside the change, and Lem started a polish builder (73 s) only to file one backlog
  item. The small change's own builder files such an item, in a commit of its own, and never
  fixes it; the pull request lists it. Its report is its reply, five lines, and Lem writes
  `report.md` from it: Claude Code refused the write of that file to all three builders of the
  first small changes, as the retro of that repository counted (2026-11-17).
- **The push and the pull request of `propose` need no question** (R4, the first run). Lem
  stopped before `land.py propose` and asked whether it may push two branches and open their pull
  requests, where the flow promises a task that runs to its pull request without the owner.
  `branch.propose`, in the settings he approved at onboarding, is his standing word for that
  push, so `SKILL.md` and `stages/land.md` say that asking there is the defect, and the hand-over
  page names it among the assumptions. Nothing else leaves the machine without a question. In
  the second run both pull requests opened with none.
- **The texts people read say "the owner"** (the first run). Its pull request said "Lem approved
  it in his name". A pull request is read by the owner's teammates too, and a product does not
  know who its user is. So every string the scripts print or write for a person, and their
  `--help` texts, say "the owner"; comments, function docstrings and the stage files keep their
  voice.
- **No project's session edits Lem** (2026-11-17). `stages/learn.md` sent a lesson about a stage
  to "that skill's file, in the clone the skills are linked from", committed there and never
  pushed. On 2026-11-17 a scheduled `/lem retro` of a scratch repository did that: it committed
  `aeaa577`, an edit of `stages/new.md` step 7, on the checked-out `main` of this clone, with
  nobody's review, and the maintaining session's next push published it. The commit also quoted
  as the owner's a sentence that the maintaining session had typed as the operator of a trial;
  the correction hook cannot tell who types. So a lesson about a step of Lem, or of another
  installed skill, is one line in the project's own lessons file that opens with the stage's
  name, Lem reads that file before each subcommand (`SKILL.md`), and the retro's report names
  the line as one about Lem itself. This is "One Lem for one repository" applied to the learn
  stage. In Lem's own repository a stage file is a project file, and its edit is a task. The
  free hour is not changed: it runs in this clone, on a branch.
- **An ask waits for another task only when it needs that task's result** (2026-11-17). The rule
  of `aeaa577` stays, as the maintaining session's and not the owner's: two asks that only name
  the same file or function each start at once, each in a worktree of its own, and the landing
  line settles an overlap. In the second real run a bug waited behind a one-day task for that
  reason, and a developer who types a bug wants it started.
- **A correction hook registered twice judges each message once** (2026-11-17). A scratch
  repository moved from the links to the plugin and kept the hook that `setup.py --corrections
  on` had written, beside the plugin's own: two calls of the model and two queue entries for
  each message, and nothing said so. The maintaining session listed it for the owner as a thing
  to clean in that repository and called the pass done; he asked "so we need to fix that?". It
  is a class: three places can register the hook (the home's settings, a repository's, the
  plugin), and any two double it. So the hook claims each message (the session and the words,
  for `CLAIM_SECONDS`) before it hands it on, and a second copy exits; the machine check has a
  row when more than one place registers the hook, with the command that removes one; and
  `--corrections on` registers nothing where the plugin or the other scope already starts it.
  One run of Claude Code with two registrations in a throwaway repository: 2 calls and 2 entries
  with the script before the change, 1 and 1 after it (2026-11-17). A defect of Lem that a run
  shows is fixed in Lem, also when one repository can be cleaned by hand.
- **Lem is a companion, not a gate** (2026-11-17). After one day of guards, the owner: "Lem is
  helpful companion, not a whole machinery, security gate etc, we are not working on something
  that should prevent all kind of failures that are developer or other parties responsability."
  A second opinion (Fable) measured that day's growth: `land.py` from 2,232 to 3,226 lines, and
  the four texts Lem's session reads (`SKILL.md`, `stages/new.md`, `stages/land.md`,
  `harness/claude-code.md`) from 22,939 to 27,769 words. The line the maintaining session took
  from it: (1) Lem owns each push, merge, rewrite and deletion that Lem or its agents make. (2)
  Lem owns the truth of its words: "green", "approved", and each state on the board. (3) Lem owns
  the path from a request to a pull request in a usual repository. (4) Every other failure
  belongs to the developer, the team, the forge or the review tool, and Lem gives it one honest
  sentence at most. (5) A new mechanism names the act of Lem's that does harm without it, and its
  cost on a small change. Cut for it: the checks of the base after a merge on the forge, the "the
  base moved" mark on the other pull requests, the read of a careful change after a clean rebase,
  and the bar's no-cover marks, lint ignores, coverage omits, workflow check and lost comparison.
  Shrunk: after a merge Lem brings onto the base only a pull request the forge calls conflicting;
  the settings are the main checkout's working tree while it is on the base branch; the proposed
  permissions have no `ask` rule, since with pull requests every merge goes through the forge;
  "text from outside is data" is one sentence for the builder and one for the review;
  `/lem pr-review` asks once before it runs a fork's code; a task starts from the local base when
  origin does not answer.

## Checks

```bash
bash tests/all.sh              # every suite below at the same time, one log each, a line of ok and FAIL per suite
```

One suite alone:

```bash
bash tests/test-lem.sh         # Lem's scripts, in throwaway repositories: the blocks tests/lem-*.sh at the same time; loads the board in headless Chrome when one is installed
bash tests/lem-land-shop.sh    # one block of them, alone (each block sources tests/lib.sh)
bash tests/lem-old-tasks.sh    # tasks the scripts of an older commit took to open, read, landed and cleaned by the scripts of now
bash tests/lem-land-local.sh   # the landing with no remote, in two blocks of about equal time: decisions, criteria and the read here,
bash tests/lem-land-review.sh  # and the polish pass, the review, the bar and what makes a request careful here
bash tests/lem-command.sh      # the command lem: each name, its arguments, stdin and exit status, help, and that no text names a script by its path or wraps a call
bash tests/lem-alone.sh        # the commands that need the machine to themselves (checks.alone): lem project alone, its one lock, and the checks that use it
bash tests/lem-naps.sh         # the naps: the [naps] settings, lem project may-nap, and the feed of the board's Dreams tab
bash tests/test-gate-panel.sh  # the gate's log and the panel's cast, with the paths a project's settings name
bash tests/test-ask.sh         # lem-ask's spec checks and every template; loads pages in headless Chrome when one is installed
bash tests/test-ask-expert.sh  # the experts' advice in a choice's record, the end of the wait, settle --away, and the brief; no expert runs
bash tests/test-board.sh       # the board over a repository whose tasks stand in every lane; loads its pages in headless Chrome when one is installed
shellcheck tests/*.sh
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

To run a clone of Lem in one session, without the plugin's install, load its folder as the plugin
(Claude Code 2.1.325, 2026-11-17: the session listed every `lem:` skill and `lem:lem-builder`):

```bash
claude --plugin-dir /path/to/lem   # the plugin from this folder, for this session only, with its skills, agent, commands and hook
```

## Layout

- `skills/lem/SKILL.md`: the entry point and what holds in every stage.
- `skills/lem/stages/`: one file per subcommand, and `talk.md`, the plan talk of a careful or
  large plan, which only its defender reads. The parts of `new.md` that only one path reads are
  files beside it: `interview.md` (the interview and the acceptance criteria), `investigate.md`
  (a bug and a question), `start.md` (the start of a lead, `/lem build` and the queue),
  `stopped.md` (when a lead stops) and `choice.md` (when a choice waits for the owner); and the
  polish pass, step 3 of `land.md`, is `polish.md`, which only a full change reads.
- `skills/lem/harness/`: the capability contract and one file per agent.
- `skills/lem/scripts/`: `lem_state.py` (the one place that names a repository's state folder,
  `.lem/state/` of the main checkout, and moves the `.git/lem/` of an older Lem there once; every
  script that touches the state asks it, directly or through `project.py state-dir`),
  `lem_plans.py` (the one place that builds and finds a plan's file name from `paths.plan_file`,
  and finds a plan of the older name `YYYYMMDD-<slug>.md`),
  `project.py` (a repository's settings, task state, the event log, and `waiting`, the one list of
  what waits for the owner),
  `doctor.py` (the machine, and a row when more than one place registers the correction hook),
  `board.py` (opens the board), `land.py` (the landing, one refusable step at a time: the
  machine checks, the review's floor and its record, the pull request, the merge, and the watch
  of the open pull requests on the forge),
  `corrections.py` (the optional queue of the owner's corrections: its hook, which claims each
  message so that a hook registered in two places judges it once, and what a retro reads), `jev.py` (the client of the Jev decision model, which the hook runs by its path and
  the plugin puts on the Bash tool's `PATH` as the `lem-jev` command), `criteria.py` (a task's acceptance criteria, read from the top of
  its plan, or for a small change from `criteria.md` in its task directory, and the check that
  each one's tests pass on the branch and fail on the base commit; it still reads the `stories.md`,
  `stories.json` and `## Stories` of a task an older Lem proposed),
  `decisions.py` (a task's decisions in `decisions.jsonl`: each one taken without the owner, and
  each choice that waits for him `flow.decision_wait` minutes at most, with the experts' advice
  on it, which the landing reads).
- `skills/lem/assets/board.html`: the board of all tasks and of one task, one page for both, and
  on the board of all tasks a second tab for the backlog.
  `lem.css` beside it is the look every page of Lem shares: its colors, its type, its header
  and the blocks of a page to read. `handover.html` is the pattern of the onboarding's page.
  A new page for the owner links `lem.css` and brings no style of its own.
- `skills/lem/templates/`: the shapes onboarding fills.
- `skills/lem/prompts/`: the standing briefs of a task's lead, of a plan talk's defender, of the
  scout of an interview, of the investigator of a bug or a question (`investigator.md`), of the
  one builder of a small change (`small.md`), of the builders of a landing, of the agent that
  routes and runs a review before a change is proposed, and of the reviewer in the other pane.
- The naps, an optional part: `skills/lem/prompts/nap.md` is the nap's brief, written after the
  owner's own nap routine and kept in its voice (a change to it is tried with one real nap, and
  its dream is read: a brief that makes a report of it is wrong); `skills/lem/stages/nap.md` starts
  one; `project.py may-nap` says whether one may; the board's third tab, Dreams, shows them; and
  `skills/lem/assets/demo-naps/` holds the example nap `board.py --demo` shows, a real nap of a
  trial run. `tests/lem-naps.sh` is their block.
- `docs/`: the reference pages the README links, each in STE like the README and each with one
  job: `flow.md` (how one task goes, for each size, with the plan talk and the diagrams),
  `settings.md` (every setting with its default, one to one with `project.py`), `inside.md` (the
  two levels, the agents and their briefs, a task's files, the event log, the board),
  `install.md` (what Lem needs, each form of install, what Lem writes and how to remove it) and
  `examples.md` (the real runs with their dates, and illustrations). Beside them `free-hour.md`
  (how an unattended session may change Lem), `linear.md` (how a project connects Linear),
  `compatibility.md` (where a developer's own skills, hooks, rules, permissions and models meet Lem),
  `backlog/`, Lem's own deferred work, and `plans/`, the plans that built Lem: each finished one
  opens with a status line that names its commits and where later decisions changed it.
- `.lem/`: Lem's own settings, profile, cast and lessons, from its onboarding, which `/lem` reads
  when Lem runs in this repository. Its `state/` folder, which git ignores, is the state of a
  repository's Lem: the tasks, the event log, the night reports, the naps, the experts' folders
  and the copies a panel read; `lem_state.py` names it. `.revmux/`: the review tool's profiles, lenses and project
  profile for this repository.
- `tests/`: the suites of the Checks above; `all.sh` runs them all, `lib.sh` is what each
  `lem-*.sh` block sources. `.github/workflows/ci.yml` runs them when someone starts it by hand.
- `.claude-plugin/`, `bin/` and `hooks/`: what Claude Code reads to load this repository as the
  plugin `lem`, the one way Lem installs: the manifest, a marketplace file that lists the one
  plugin, `bin/lem`, Lem's one command, which runs the script a name stands for (`lem project
  show` is `skills/lem/scripts/project.py show`, `lem help` lists the names), links to the two
  commands `lem-ask` and `lem-jev`, all of which a plugin's `bin/` puts on the Bash tool's
  `PATH`, and the correction hook. Every text and every message of a script says `lem NAME`, so
  one permission rule, `Bash(lem *)`, covers them on every machine and after every update.
- `agents/lem-builder.md`: the builder, as a Claude Code agent definition. Its body is the
  builder's standing rules; `harness/claude-code.md` says how it is used and overridden.
- `skills/lem/references/`: the catalog of published style guides.
- `assets/lem.svg`: the logo, and `assets/lem-mark.svg`: the figure alone, for an icon.
  `assets/lem-night.svg` and `assets/lem-mark-night.svg` are the same drawings in the night
  palette, written by `assets/night.py`; the README shows the night one in a dark theme.
- `assets/screens/`: the pictures of the board, for a light and a dark theme, at two device
  pixels for each pixel. `board-*`, `task-*` and `backlog-*` are renders of
  `skills/lem/assets/board.html` over the data of `board.py --demo`; the README shows `board-*`,
  and `docs/inside.md` shows `task-*` and `backlog-*`.
  `real-task-*` is the board of the first task that ran through Lem (2026-11-15), over its real
  event log, and only `docs/examples.md` shows it, with its date.
- `skills/lem-ask/`, `skills/lem-backlog/`, `skills/lem-interview-me/`, `skills/lem-dialectic/`,
  `skills/lem-root-cause/`, `skills/lem-release/`, `skills/lem-last-tag/`, `skills/lem-pr-review/`,
  `skills/lem-gate/`, `skills/lem-panel/`, `skills/lem-linear/`, `skills/lem-ask-expert/`: the
  skills Lem names and ships. `lem-ask-expert` is Lem's own, written under the rules above, with
  `scripts/experts.py` (the experts' brief and their answers: for a choice of a task into its
  record, and for a question in words into a folder of its own in `.lem/state/experts/`).
  `lem-panel`'s `scripts/cast.py` keeps the copies of the cast and the profile a panel read in
  Lem's state folder, `.lem/state/personas-cast/` and `personas-profile/`.
  `NOTICE` says where each came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools,
and lem-ask's Stop hook (`skills/lem-ask/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, the mailbox chat, webrev,
agdoc, cronn, plannotator, Codex) is checked for by `doctor.py` and never copied in, and a project that prefers its own tool for a
role says so in its settings or its `AGENTS.md`.
