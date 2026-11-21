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
  names that file in one line: a task on the fast track reads nothing that only the standard track needs.
- **A task's phases stay apart.** `plan` and `build` are the lead's, in the build phase. A step
  that reads a task's code or its diff goes to the lead, a builder or a fresh agent (the
  investigator, the review, the merge agent), never into the shape (`new`, `interview`) or the
  landing (`land`).
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init` with no base it can tell asks for `--base`).
- **A change is measured by what it costs a developer on a small task** (the touches it asks of
  him, the waits, the agents it starts) as well as by what it guards.
- **Documentation describes the current state.** No changelog paragraphs, no "previously".
- **A maintainer's session with nobody at the terminal reads `docs/free-hour.md` first.** It works in a
  worktree of this clone, on a branch, and never pushes: `main` of this repository is what every
  project's next update of the plugin installs.
- **Lem is not released, so a change keeps no reading of the form before it.** A change to the
  settings, a record, an event, a state or a command reads and writes the new form only, and the
  maintaining session corrects the repositories that use Lem by hand. When Lem has users, this
  rule changes.

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
- **Opinionated and small.** His first form let a developer use their own tool for a role
  (`tools.annotate`); he let that go with the `[tools]` table on 2026-11-18 (his interview, below).
  Out of scope: a peer-planning flow, a skill-activation hook, language-server plugins, output styles,
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
  answer in `--why`; `land.py` (`READ_SKIP`) takes a full change with no `criteria.read` only when an
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
  approves. Since his rulings of 2026-11-19 (below) the page opens in a need's companion under
  Lem's session, never over Lem's own: his page for the criteria in the companion of the interview
  or of the criteria, and the card of a choice in the companion of that choice.
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
  `init --existing link` was how an adopted project named its folders until 2026-11-18, when
  every place became fixed (his interview, below): a project moves its personas and its profile
  into `.lem/`, and `.claude/rules` is the one place Lem reads the rules for the code. "For now"
  is his: a move of the rules is a new decision of his, and nothing here prepares one. The form built from it
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
  for huddle, then name and the way out". The key was `tools.ask`, beside `tools.annotate`. He
  let both go on 2026-11-18 ("[tools] - goes away?", his interview, below): Lem asks with its own
  page, which needs agterm, and agterm is required.
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
  keep that way for now".
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
  `lem-backlog` was a shipped skill until 2026-11-18, when he took the agterm cookbook's backlog
  recipe in its place (his interview, below). The item format and the tab stay: the board's
  second tab shows the items by their `worth`, with one action that gives an item to Lem as a
  request. The content follows a page of his own; no code of it is used.
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
  Since 2026-11-19 (below) the card of a talk's choice opens in no plan talk's companion: the
  defender tells Lem `lem: SLUG choice N waits`, Lem opens that choice's own companion
  (`SLUG · choice N`), and gives the defender his answer as one message. The talk stays a
  companion of Lem's session with the reviewer in its split pane, as before.
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
  `question` for a task that commits nothing. The track is the fast track or the standard track
  (`small` and `full` in the records), and careful is a mark on top. Lem's first line says both
  ("fix: ... Fast track: ..."). The kind `correction` is gone: the fast track is a track, never a
  type.
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
- **Codex in each role is wanted** (replaced on 2026-11-20, below).

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

His interview of 2026-11-17 and 2026-11-18 on what stays in Lem; a quote is his words. He asked
for it ("Lets have quick interview what should stay and what should leave the Lem plugin") after
he measured Lem against three sentences of his: "Good tools don't demand extra attention", "One
thing. Done well - Not an everything Companion. A useful tool that fits into an ordinary developer
day", "Best practices without confusion". `docs/plans/2026-11-18-core-and-two-modes.md` is the
build that follows.

- **Lem is his one desk for work in a repository, and its core is the path from a request to a
  merged pull request.** "my workflow is agterm + few cookbooks + skills that I write somewhere, I
  want to have a clean desk again", and "we aim to build end-to-end opinionated workflow for a
  developer". A helper stays in the core when a step of the path uses it, and he can then call
  that step by hand; to that rule, the maintaining session's wording, he marked "Looks good" on
  the list it gives. He uses by hand: "interview-me when I start the plan / task", "dialectic,
  ask-expert, panel of personas: those skills help me take a decision during planning", the
  acceptance criteria, the backlog, and "RCA when I investigate some weird issue".
- **Release, last-tag and the review of another person's pull request leave the core**: "yeah,
  those looks like lem addons more than core functionality", and "Release functionality may go as
  an addon later". What leaves goes out of the repository (his pick on the page: "They leave the
  repository"); `docs/backlog/add-ons-after-the-core.md` lists what may come back as an add-on
  ("Worth adding to backlog now").
- **agterm, the mailbox chat and revmux stay required** ("as today"), **and agdoc is required
  too**: of the page at the end of a task, "done by agdoc (hard requirement of the Lem)".
- **cronn is required, and Codex is highly recommended** (his notes on the README and on the
  install page, 2026-11-18): of the cronn row, "make it required, `/retro` add a lot of value of
  the time", and of "Codex is optional", "while godex is optional - its highly recommended". So
  the machine check fails without cronn and `/lem init` stops for it; a scheduled job is still
  added only on his yes.
- **Three more commands are no commands of his, and two recipes of the agterm cookbook become
  required** (his note on the plan, 2026-11-18): "`/lem ask` is suppossed to be called
  automatically, just like `huddle` today. `/webrev` becomes a required reciepie. (no need for
  `/lem annotate`) `/backlog` becomes a required reciepie. from
  https://github.com/umputun/agterm/tree/master/cookbook/backlog-picker (I don't recall why I
  wanted my own)". Why he had wanted his own, from his ruling of 2026-11-15 above: three stages
  live on the backlog (the night picks from it, a landing files into it, a request starts from
  it). Those stages need the item format, which is the recipe's own (`docs/backlog/<slug>.md`
  with `worth`, `where`, `added`; read in its README on 2026-11-18), not the skill. So the
  `lem-backlog` skill leaves, the stage texts say the format, and the board's Backlog tab stays
  (his "Backlog tab - I like this idea"). The recipe's skill tells an agent never to commit an
  item on its own; Lem's builders load no such skill and file on the task's branch, as he ruled.
- **A task runs with him or alone, and he can let go at any stage.** "Sometimes I would love to
  know the decisions taken before implementation, and sometimes I want autonomous exection with 2
  artifacts at the end: what decision were taken and why (a beautiful, easy to read HTML file) and
  what we actually have been building here and why we want it (when there are lots of tasks and
  plans, its easy to loose track on what we build)". And: "I also want to let go sometimes,
  telling the lem to go fully autonomous at any stage. Lets say we discussed a bit of the issue
  and I suddenly need to leave the house - I should be able to say that all upcoming task work
  goes autonomous (probably it should make a switch in task file, some flag) so all upcoming
  decisions will be taken automatically and when in doubt Lead will use: the panel, ask-expert,
  dialectic; all by himself". The form is the session's, each part marked "Looks good" by him: his
  words "go alone" and "go alone for all", a flag in the task's record, and "I am back", which
  takes it off for the steps that remain. A step that a later "no" cannot reverse and the merge
  wait for him in either mode, and of those: "It can be described as big red flag in artifact
  files so I will not overlook it".
- **The two artifacts are files of the task, not of the repository.** Asked whether
  `decisions.md` is committed on the branch: "idk, if task folder isn't committed than no. its
  just a file that will load a context to my brain when I will have a time too look at the PR, to
  decide whether I like it or not and second artifact file should tell what and why build here".
  Of a sample of the page (agdoc's "classic" design, a red block first on the screen for what
  waits for him; `docs/plans/2026-11-18-core-and-two-modes/pages/`): "sample page is fine".
- **Not every section of the settings stays** (his note on the plan, 2026-11-18): "I also have
  doubts all sections of the settings should stay ... paths.styleguide - is it really part of the
  Lem or harness setup itself? paths.lessons vs paths.rules (wft? which is what? why?)
  paths.backlog - coookbook covers this. [checks] - thats git hook job. [tools] - goes away?".
  The answer is the session's, task 1b of the plan, which he passed with no note: the settings go
  from 40 keys to 25; Lem's own files and the folders of other tools have one place each and no
  key; the rules for the code are the harness's folder, and Lem only names the matching files to
  the agents that load nothing by themselves; `[tools]` goes; and `[checks]` stays with
  `commands`, `setup` and `alone`, because a test suite is no git hook's job and "green" must be
  what a script saw. His two rulings that this reopens, on his own question: "A developer may ask
  with a tool of their own" (`tools.ask`, `tools.annotate`) and the linked folders of an adopted
  project (`init --existing link`).
- **The tests are to be useful and fast**: "Please make all kind test actually useful and not
  painfully slow. I can't wait to use Lem!" (the same page). Task 1a of the plan.
- **He says whether he is there, and Lem assumes nothing** (his notes on the README, 2026-11-18,
  after the words "go alone" were built): "also a bit confusing. In a typical flow I may want to
  mark myself as `dnd` or `online` (or some better keyword). When I'm `dnd` - everything goes
  without my attention. I don't want any assumptions whether I'm dnd or not. Lets remove this
  15min automatic timeout - to have more explicit: Owner either tells dnd or not, no assumptions.
  In the future there might be some external connectors that would tell that owner is dnd, but
  thats a backlog item story. Command suggestion: with `/lem dnd`, `/lem online` (suggest better
  keyword, something chat app related?)". So his being there is one status of the machine (his
  interview of 2026-11-19, below), not a switch of each task, and it replaces "go alone", "go alone for all" and "I am back"; while he
  is there, a choice of his waits for his answer with no time limit, and `flow.decision_wait`
  goes. This replaces his ruling of 2026-11-16 that a choice "waits for him 15 minutes at most".
  The keywords are his: to the session's `/lem away` and `/lem back` he wrote "Lets follow Slack:
  `/away` and `/active`", so they are `/lem away` and `/lem active`.
- **The first line is where he corrects Lem's read of a request** (the same notes): of the row
  `"full", "careful" or "drop"`, "I see why want it, but I cant imagine this being clear to
  developer. Maybe it should be a quiz with assumption at the beginning. During the execution, we
  cannot switch from short path to full, it's too late. But we can drop the plan. I'm not sure we
  can swith to careful execution, probably not?". The session answered that the first
  line is that quiz with its assumption taken, and that it adds no question; he wrote back: "I
  think confirmation step (when confused) should be add. When its clear - we go without it. I
  understand that it breaks contract, but isn't it a right thing?" So a clear read asks nothing,
  and a read that Lem cannot settle (the size, the type, careful) asks one line in the terminal
  with its guess, before any agent starts; while he is away Lem asks nothing and takes the safer
  read. Of "careful until the merge": "Still, weird interface. Maybe it should be something like
  a command that would affect the plan, and even when plan is already completed it will do the
  right thing, for example it will run the proper review", and of "drop": "but still - Lem
  should understand what plan is affected the current one or something else". So the three are
  commands that take a task, `/lem careful`, `/lem standard`, `/lem drop` (`stages/correct.md`): a
  task with an open pull request that is called careful goes through the full review again;
  `standard` holds until a task on the fast track is proposed; and Lem asks which task when more than one
  could be meant.
- **The README shows the interaction, and links to no run** (the same day): "Having examples of
  execution in Readme in a form of links to some repo is plain stupid. I would rather show
  interaction in some short form, or steps in form of small flowchart."
- **The two tracks are the fast track and the standard track** (the same day). Of the words
  before: "The only weird thing for me is naming "small, full". Its not wrong, just naming weird
  for me", and "Ask Fable, maybe my confusion comes from wrong design". Fable's answer: a problem
  of names, not of design; Lem called the path a "size", and a reader takes a size as a measure
  of the change, while one line in the code of a charge takes the long path and a rename across
  300 lines the short one. He then chose the words: "Maybe we should call it `quick path/flow`
  and `standard path/flow` ?", and of the caution that "quick" promises no time, "analogy to fast
  track would be perfect, maybe we should even name this mode that way". So a text for a person
  says "the fast track" and "the standard track", the name stands at the steps in Lem's first
  line, "size" means files and changed lines only, "full" means the review only, and the command
  is `/lem standard`. The records keep their words (`Size: small|full`, `--small`,
  `call=small|full`, `prompts/small.md`), so that a task that is open reads as before; the
  session's decisions above keep the words of their day.
- **A helper starts from plain words** (the same notes): "will it work if a bit different
  wording will be used like "lets braindstorm" instead of literal "interview-me". It would be
  nice to have more natural way of speaking. When model is unsure which skill should be used - it
  will ask directly with suggestion (plain terminal ask)."
- **In doubt, a decision climbs a ladder of opinions, and a count decides, not a model.** His
  order: "Lead -> Personas -> Experts -> Dialectic (or Dialectic before Experts as its cheaper...)",
  and "Next level follows if no clear consensus reached or owner wants to check all possible
  opinions". Of a model as the judge: "I'm a bit in doubt what Jev can decide here without whole
  context of the use case, specicially Jev cannot read the code". To the session's order, lead,
  personas, the dialectic on the option with the most votes, then the experts, he wrote "you are
  right". Whether personas or the experts serve better he left open ("I'm not sure if personas
  are better than two experts"), so each level logs whether it changed the pick. The dialectic's
  two agents are subagents of the lead for now: the session's answer to his "for now that would be
  a typical subagent, like opus 5.5:high? or do we want to run them in separate agterm companion
  session", open to him.
- **The question gate stays, hidden, and may decide**: "Sounds useful and it should stay as
  hidden feature. Decisions taken that way lands in `decisions.md` artifact at PR time." He had
  forgotten what it was ("sing that I forgot says a lot"), so it has no command of his.
- **The plan talk stays as one plan, one reviewer and a closed list, and it can stop a task**: "one
  model prepares the plan and then have limited discussion with the reviewer. Not task by task.
  And this discussion has closed list of issues and may cancel futher execution if there are signs
  that the design is wrong and fixing it brings even more problems on a plate or requires dirty
  hacks."
- **The lessons, the retro and Jev stay; a night run ends as a pull request; naps are not
  shown**: "lessons stops agent repeating same errors, retro and Jev proved thier efficiency,
  night execution is just a fun thing to build something while nobody's looking and its actually
  got to be a PR to merge, not a plan. Naps and dreams are worthy but does not need to be exposed
  at all. Its just affects "retro"". Of a night run that writes the criteria itself, builds, and
  opens a pull request that says "not green: you did not approve the criteria": "Yes this is what
  I want".

His review of the README and of each guide on 2026-11-18, after that build; a quote is his words.
Where a note replaces an earlier ruling, this is the ruling now.

- **The commands of his status and of a task are `/lem im-away`, `/lem im-back`, `/lem be-careful
  [task]`, `/lem standard-track [task]` and `/lem drop [task]`.** He asked: "Whats your opinion on
  renaming: `/lem careful, /lem standard, /lem away, /lem active` to: `/lem careful-track, /lem
  standard-track, /lem im-away, /lem im-active`?" Careful is a mark and no track, so the session
  proposed other words. Of `im-away`: "use it"; of `im-back`: "I like that one"; of
  `standard-track`: "use it"; of `be-careful`: "I'm not totally sold, but this one sounds best
  now. As far as I understand it's the command we need to run occasionally, when we change our
  mind about task severity". These replace `/lem away`, `/lem active`, `/lem careful` and `/lem
  standard` in the rulings above.
- **No word and no form of a Lem before is kept.** The session had left the older command words
  as accepted "when you type them by habit"; he wrote: "what habits? its unreleased code!!". Asked
  whether the refusal of a settings key that went and the reading of an open task's older records
  should go too, with the two repositories that use Lem corrected by hand: "yes, remove". The
  rule is in "Rules for a change here".
- **The README says a plugin that works closely with agterm, and names no operating system**:
  "Should be rephrased as there is an agterm fork that runs on linux (and probably windows),
  potentially it is compatible. So in fact its a plugin tightly integrated with agterm. Is it
  Claude Code exclusive? Now yes, but it will work with Codex as 1st class citizen very soon."
- **A chord opens a list of the tasks**: "Add a shortcut functionality for agterm that behave
  like currently installed backlog picker, so its trivial to navigate between task". The form is
  the session's: `picker.py` (`lem picker`), and a row of the machine check that gives the line
  for agterm's keymap, which is the owner's file and which Lem never edits.
- **The Linear table is short**: "Do we really need all these settings for Linear integration?",
  and "Linear - yes, shorter, everything can be infered from Ticket ID". `[tracker]` needs only
  `kind`. The team comes from the ticket's id, and the two statuses from Linear by their type
  (the next day he took the last other keys out too, below). This replaces
  "Status names are carried by name in the settings". Of a connection that fails: "I think we
  should simply point to Linear MCP help page. We don't know exact problems and reasons here."
  No real ticket has run through it; of that gap, "put into backlog"
  (`docs/backlog/linear-status-by-type-has-not-run.md`).
- **`branch.history` is `"squash"` by default**: "my opionated default is "squash"".
- **Each of the three seats is written whole**: "I think it should be explicitly
  `agent/model:effort` in all 3; not simply "claude" or "codex"", and of the models, "Use latest
  `codex/gpt-6.2-sol:high` and `codex/gpt-6.2-astra:high` (released yesterday)". A guide names
  the experts without a version: "its better to call these models as latest Anthropic Fable and
  OpenAI Astra to avoid version drift".
- **Without Codex one expert answers alone.** Of a second Claude model as the second expert:
  "Sound pointless and should be degraded to a single expert then. Once we have 1st class support
  for Codex this can be reverse situation (only Astra works, alone)". `lem project init --codex
  no` writes the seats for such a machine.
- **No setting counts the tasks that run**: of `flow.max_tasks`, "will it be default for
  developer or a project? Feels like it depends on developer machine capacity. But then maybe we
  shouldn't even have such option and let Developer decide whether to run a session or not. Why
  block him?" The key is gone and nothing stops a start. **A night works its items one after
  another**, four at most, or the N of `/lem night N`: "I think night run works linearly ... one
  task at a time per project is fine default for night runs."
- **`[checks]` keeps three keys, and `alone` is `serial`.** "I'm a bit confused with this
  section. Yes its Lead who usually run tests, and e2e local tests are usually needs to run in
  queue. Then maybe we need to name `alone` differently? Should Lem support something like merge
  train or test train? Ask Fable for opinion for that section". Fable's answer, which the session
  took: no train; `checks.serial` names the tests that two tasks cannot run at the same time, and
  they run one at a time for all tasks. `checks.setup` runs once in each new worktree.
- **The topics are proposed at the setup**: "It should predict during initialization what are
  the dangerous zones for that project". `/lem init` proposes them from the code, and the guide
  says so.
- **Four places are settings**: "all 3 should be configurable: rulings location, plans location,
  plan file names format, rulings file names format; For the team it stays consistent in the
  project, but there might be different defaults for different teams that adopts or evaluates
  Lem." `[paths]` holds `plans`, `plan_file`, `rulings` and `ruling_file`; the lessons keep their
  one place, `.lem/lessons.md`.
- **Every way to merge stays, and there is no train.** He drew three cases (GitHub with pull
  requests, GitHub with a direct merge, another host) and asked: "Ask Fable - maybe we should not
  support some of those modes for simplicity as an opionated tool?", and "What is the recommended
  flow for Github based projects: triggering "merge" in Github or via Lem?" Fable's answer, which
  the session took: drop none; with pull requests the button on GitHub and `/lem land` are the
  same merge, and a task's branch is never merged by hand.
- **A choice that matters is logged, also when nobody was asked**: of the pull request's lines
  for what was decided without him, "this is different case than "Agent took a decision durign
  implementation without asking". The latter happens all the time. Some important choices needs
  to be logged into our artifact log." The lead logs such a choice with `--by lead`
  (`stages/ladder.md`), and `decisions.md` shows it.
- **The investigation of a bug keeps its method**: "If we aim to support the bug investigation,
  then we need to revert removal of the RCA skill. It may be hidden and called by the model
  during investigation". `lem-root-cause` was never removed: the investigator loads it, and it
  has no command of his.
- **The Jev model comes through any provider**: "since its using jev lib and jev lib only care
  about API url and API token - we can use any provider, not the openrouter. Ask user to provide
  the token in settings or in environment key and the api url". The form is the session's:
  `JEV_API_KEY` and `JEV_API_URL` in the environment, OpenRouter's address by default, and no key
  in a file. This replaces "OpenRouter is the one way to the Jev model for now".
- **Lem assumes auto mode**: "I would rather state that we assume that automode is used in codex
  and claude code."
- **A page to read opens as a companion**: "Command like this and possibly others that opens
  html overlay should be opened in companion `/lem status working-days-of-a-range`; isn't it?"
  `lem board --page FILE` opens it. A question page and a mark-up stay overlays, since each waits
  for his answer: that part is the session's.
- **The board as a tabbed interface is a backlog item**: "redesign board to a tabbed interface,
  consider using the WebAwesome (we have a professional license)" (built on 2026-11-20, below).

His notes of 2026-11-19, in the session, on the Linear page and in the interview on his away
status; a quote is his words.

- **The tests are chosen by what can fail, and a task is quick.** Of three builders that took 49,
  99 and 115 minutes the day before: "Why the hell it takes so long!?", "thats still enormous
  amount of time for the skill repository! what those tests doing so long?", and "I demand quick
  tasks run". He had an Opus subagent and Codex Astra asked two times what the tests of such a
  repository should look like. Their answers agree, and the session took them: a rule that takes
  facts and returns a result is a unit case, a call of its function (`tests/unit/`); a fact only
  git can show is a check in a real repository; a journey is run once, not once for each input.
  The loop of "Checks" is the other half: half of a builder's time had been test runs that the
  session's own briefs asked for. A cache of git's answers inside one process (`perf/ask-once`)
  was built that night and not taken: a Fable second opinion, Opus and Astra all said that a stale
  answer in the code that merges costs more than the 0.1 s it gives a developer.
- **`[tracker]` has one key**: of the keys that were left, "why the heck we need any other
  settings for linear?". The form is the session's: which status a ticket gets is the agent's read
  of the team's statuses by their type, and by their names where a type has two; in doubt it moves
  nothing and says so in one line; a ticket already at the target is not moved, so no key says who
  moves; and the server is the one the agent has, with no key that names it.
- **`/lem read KEY` shows a ticket**: "`/lem linear ABC-12` looks odd, specifically when only
  tracker is allowed. Maybe `/leam read ABC-12`?" The word names no tracker, so a second tracker
  needs no new command.
- **A persona's file names its models**: "`[seats]` in settings. We should also add settings for
  models for personas (or its frontmatter settings per persona file? probably better idea)". So
  `seats:` in a persona file's frontmatter, in the form of the settings' seats, and no key in the
  settings; a file without it answers as the panel answers by itself.
- **The experts know the personas**: "experts should have a context of personas I think, so they
  can also reason about what kind of users builded code are expected". Their brief holds the
  profile and each persona as context; an expert still answers as an engineer.
- **Each label of a chart is quoted.** "all flowcharts needs to be checked, some are broken", and
  after every label got quotes, "flowcharts now works, weird". The three charts drew without an
  error in two versions of Mermaid on the session's machine before the change, so GitHub's own
  version reads an unquoted label in another way (a label that starts with `/` is the likely one;
  not proved). A chart in `README.md` or `docs/` writes each node's and each edge's text in double
  quotes, and is drawn once before it is committed.
- **His away status is one mark of the machine, and a night task always runs without him** (his
  interview of 2026-11-19, `docs/plans/2026-11-19-away-for-the-whole-machine.md`). To "Is the
  machine's mark the only mark?" he answered "y". Of the night: "Night run is an exceptional
  unattented type of run and should not be affected by the state of my availability. It should
  always run unattended. Even when I'm up at night and doing something in other sessions." Of the
  place: "I belive something should live in `~/.config/lem` to support that". So `/lem im-away` and
  `/lem im-back`, typed in any repository, hold in every repository on the machine, no repository
  has a status of its own, and his `back` never ends a night task's time without him. The form is
  the session's: `owner.jsonl` in `$XDG_CONFIG_HOME/lem`, or in `~/.config/lem` when the variable
  is unset (a relative value is refused), one line appended for each away and each back and none
  removed, so that another repository still reads the span of a task that ran without him; Lem's
  session in each repository keeps one watch of it (`lem project owner watch`) and acts on its end
  as on his word there, and the session of a night keeps none; the board reads `owner.js`, a copy
  in the state folder; and every test suite sets `XDG_CONFIG_HOME` under its own folder. Each
  repository's Lem still runs only its own tasks and reads one more fact, the mark: that is how
  the change keeps "One Lem for one repository".

His rulings of 2026-11-19 on where he answers Lem; a quote is his words. He had held two
interviews at once that morning, in two sessions he opened by hand, and asked whether one Lem
across all his repositories would serve better. The experts' answers are in
`.lem/state/experts/2026-11-19-142351-how-many-lem-sessions-should-the/`, and
`docs/plans/2026-11-19-interview-in-a-companion.md` is the build that follows.

- **One Lem session for each repository, and no global Lem.** Both experts (Fable and Astra) and
  the session found no place for a Lem across repositories: each repository loads its own
  permission rules, hooks and `.claude/rules`, and its state, board and landing lock belong to its
  checkout. To setup B, one Lem session that holds the board, the asks, the status and the landing
  and never waits for him in the foreground, he answered "Ok (B)". So "One Lem for one repository" (2026-11-14) stands, as
  one session.
- **A companion opens only when something waits for him, and closes when he answered.** His ask:
  "Each interview runs in a companion session forked from Lem's conversation, and closes after my
  yes to the criteria; Lem only takes asks, starts leads, lands and reports", with the reason:
  "Naturally I don't want to sit and wait for personas reivews or anything when there is a work to
  discuss, unrelated to what we are discussing in first session most of the time. Its pure waste
  of time if we wait. This is why I manually opened a second session." On a page he picked "After
  your yes to the criteria" for its close, on Fable's recommendation, and setup B, his "Ok (B)",
  gives a companion to each thing that waits for his words: an interview, criteria that wait only
  for his yes, and the card of one choice of a lead. B replaced a card that waited in the
  background over Lem's session, since a second card in one session fails (`lem-ask` exit 5,
  `busy`). The form is the session's design: `lem companion open` names each in the sidebar
  (`SLUG · interview`, `SLUG · criteria`, `SLUG · choice N`) and takes no focus, the board's
  "Waits for you" opens the one that waits, nothing opens while he is away, and at `/lem im-back`
  one opens for each step that a later "no" cannot reverse.
- **A companion is a fresh agent, with the talk copied in.** His ask said "forked from Lem's
  conversation"; on the page he then picked "A fresh agent, with the talk copied in" over a fork of
  Lem's conversation, which would have carried every other task and Lem's duties at each
  turn. The form is the session's design: `lem companion talk` copies the turns of Lem's session
  that led to the ask, word for word, from Claude Code's transcript into the task's `talk.md`, and
  the companion (`prompts/companion.md`) reads that and the task's files, knows no other task, and
  takes no ask, starts no lead and lands nothing.
- **A companion tells Lem with an agterm pane message.** His first word was "if group messaging
  isn't there yet - use default claude code communication bus. It will block making Codex 1st
  class citizen, but its fine for now. We will find a workaround for Codex later then."; on the
  page he then picked "agterm pane message", which woke an idle Lem before (agterm 0.41.1) and
  reaches a Codex pane too. The option he picked keeps the task's files as the truth: the message
  only wakes Lem, which reads the files at each turn and starts the lead of an approved task that
  has no lead. The form is the session's design: `lem companion due` at each of Lem's turns.

The session's design, after these: a companion runs only on the owner's machine and asks nothing
of a teammate, and the copied talk stays in Lem's untracked state folder and never reaches git or
a pull request.

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

His rulings of 2026-11-20 and 2026-11-21, while his interview redesigned how a task runs and the
board became a served app; a quote is his words. His answers Q7 to Q11 and notes P1 to P9 are in
`.lem/state/tasks/one-lem-parallel-landings/`, which git ignores. Where a note replaces an earlier
ruling, this is the ruling now.

The first three tasks of the redesign, in the order he agreed to (Q9, "Yes I agree"):

- **Landings run in parallel, and the machine's load decides when checks start**: "tests should run
  in parallel", under Umputun's load-average rule, and "on macbook I want to be able to use laptop
  comfortable, on my powerful mac mini: I can hummer it" (P7). This replaces his "yes" of 2026-11-19
  to one landing at a time (criterion 6 of `landing-in-the-background`), and his count of check runs
  of the same morning. The form is the session's: `lem land start` takes any number of tasks; the
  checks start only below `[load] start` of `machine.toml` (`lem project load --start N`), two runs
  start at least 60 s apart (a guess), and with no number there is no gate; merges go one at a time
  under `merge.lock`. At a start of 1 in his first trial: "We stuck, I think LA will never get that
  low."
- **The build asks him nothing, and the ladder always decides**: his "yes" to Q7, and "I'd rather
  review the PR and request a fix then find a work blocked on some question that automated anwers
  could answer right." A pick past the personas is logged with its story and makes the pull request
  not green; `lem decisions` asks nothing, and his away status changes nothing in a build. This
  replaces "Two experts answer a choice that waits for him" (2026-11-16) and, for a choice of the
  build, "He says whether he is there" (2026-11-18), "Lem asks through its question page"
  (2026-11-15), "A companion opens only when something waits for him" (2026-11-19) and "The plan
  talk is a pair in a companion" (2026-11-16); of the session's decisions, "Every decision that is
  the owner's takes one path" and the card in "The mode and the ladder are built in the smaller of
  two designs".
- **Only a circuit breaker stops a task, with a document**: "Hard circut breaker should stop
  execution and I will either rule to abandon / return the task and keep the context or help right
  away" (P3), with "a landing page that I can read easily, with diagrams, flowcharts, user stories,
  choices, recommendations and assumptions" (P2). Its two causes: a next step that a later "no"
  cannot reverse, which replaces that step's wait in "A task runs with him or alone" (2026-11-18),
  or no option that keeps the rule of an approved criterion ("agree"). "An overrun stops nothing".
  The form is the session's: `lem decisions breaker` with `breaker.md`, the state `parked`, and `lem
  project resume`.
- **A fresh merge agent reads every proposed task, and merges it or calls him**: an "additional
  Agent with fresh context" with a "settings configurable model" (P6). On a question page he picked,
  against both recommendations, "The merge agent reads each task, the fast track too" and "Each
  not-green pull request calls you"; a careful change always calls him ("It calls you"). Its seat:
  "this should be set on most generic level, not in code (`~/.config/lem` ?)", so `seats.merger`
  comes from the repository, else from `machine.toml`. `branch.land` stays the switch: "developer
  can configure `lem` the say he always needs to review before merge. Merge review still applies."
  The form is the session's: `prompts/merge.md`, the default `"agent"`, and `merge-review.md` in
  place of the owner's page of a task.
- **GitHub pull requests are the one way to land**: "we can assume that we fully use Github: PR,
  reviews etc to avoid support for multiple ways of doing same thing". `branch.propose` goes, and
  his merge and the agent's are one step, `lem land merge SLUG --by owner|merger`: the session's
  form. With the merge agent it replaces "A project may land with no pull request" (2026-11-16), the
  `branch.propose` part of "One way to merge in each project" (2026-11-17), the first half of "Every
  way to merge stays" (2026-11-18), the merge in "Most requests have an interview" (2026-11-16) and
  in "A task runs with him or alone" (2026-11-18), "agdoc is required too" (2026-11-18) for the page
  at the end of a task, "The two artifacts are files of the task" (2026-11-18), and the session's
  sentences on `branch.propose` and on `lem land land --by agent`.

Task 4, a session for each task: `shape-task-4.md` is its shape, and section 7 of `plan-task-4.md`
holds the coordinating session's decisions of 2026-11-21.

- **Each task lives in a session of its own, from its shape to its merge, and there is no Lem
  session.** To Q11's guess (no Lem session; `/lem` and an idea in any session, or "+" on the
  board, opens the task's own session) he wrote "I like that. Yes to all points in that guess.",
  and to Q10's (a fresh agent at each change of phase, from the leaving agent's `handoff.md`)
  "yes". The form is the session's: `lem session` and its events `session.open|close|wake`;
  `prompts/session.md`, which reads the state before `handoff.md` (a Fable second opinion he asked
  for); and the fast track as one session, since a fresh one starts at about 84,000 tokens (that
  opinion's median of 10 sessions).
- **Inside a phase a session compacts itself at his number, for all his repositories.** Of the
  number: "Globally configurable value please"; of the scouts' proposal, Claude Code's own
  compaction inside a phase with the handoff's form: "I agree with proposal, but lets keep the
  limit at 600K for now (default settings)" (2026-11-21). The form is the session's: `[handoff]
  tokens` in `machine.toml`, 600,000 when absent, 0 for no number of Lem's, under 100,000 refused;
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in each launch line; the `PreCompact` and `SessionStart` hooks
  of `session_hook.py`; and "hand off" in his words starts a fresh session in any phase.
- **What reaches across tasks is the board server's**: the session's proposal in the shape he
  reviewed, in place of Q11's watch in each session. The server runs `lem land merged`, wakes or
  opens the task's session for its cleanup, a conflict or a queued task's turn, and shows "no
  session", and since 2026-11-21 it runs the merge agent's merge too (the maintaining session's
  decision of that day, below); it never types into a session, selects one without his click,
  closes one or decides.
  Its wake-up is an agterm pane message, and the session acts on the files, never on the line.
  Section 7: "no session" is a row only when something is stuck, and every task with no live
  session has "Open a session"; `bin/lem` starts the server after a cheap look; a task's session
  sits on `seats.session` when one is set.

With Q11 as the new fact, this replaces "One Lem session for each repository, and no global Lem"
(2026-11-19) and the coordinating Lem of "One Lem for one repository" (2026-11-14); "A companion
opens only when something waits for him" and "A companion tells Lem with an agterm pane message"
(2026-11-19); Lem's watch in "His away status is one mark of the machine" (2026-11-19), now the
shape's session's; and the companions of "The plan talk is a pair in a companion that closes after
it" (2026-11-16) and of "Lem asks through its question page" (2026-11-15), now the task's session.
"A companion is a fresh agent, with the talk copied in" (2026-11-19) stays as `lem session talk`.
The server takes over the session's decision "The status knows what merged" (2026-11-17), and types
no line as "The board is served, and the server draws it" (2026-11-20) has it; in "A task that ended
stays ended" (2026-11-17), `prompts/session.md` takes the place of `stages/stopped.md`.

The board, whose form is the session's decision "The board is served, and the server draws it":

- **Claude Code and agterm first, and Codex for reviews**: "my opionated choice is to have Lem a
  Claude Code and agterm first class citizen. ... I mostly use CC and Codex for reviews." This
  replaces "Codex in each role is wanted" (2026-11-17) and the Codex builder that "Claude Code
  first" (2026-11-14) promises.
- **The board is a served app**: "Lack of being able to oversee the process away from laptop its my
  biggest pain". Hotwire, rendered on the server; "I agree that sqlite for now might be too much."
  This replaces "The board as a tabbed interface is a backlog item" (2026-11-18).
- **The board's icons are a subset of Font Awesome Pro, in the repository, under his license**: "Dont
  bother with license - my license allows the usage" (2026-11-20). On 2026-11-21 the session found
  that the repository is public, told him that Font Awesome's pages keep Pro files out of a public
  repository, and began to move the repository to the Free icons. He ruled: "Yes I can use Font
  Awesome fo my sites! This is allowed by the license. I cannot build similar products to
  FontAwesome or WebAwesome", and "I am 100% sure I am allowed this. The reason is: we use a subset
  of icons not a whole set." So `board-icons.json` stays as `tools/board-kit` builds it from his Pro
  download, only the icons `icons.mjs` lists, and no agent reopens this.
- **Tailscale is the way from his phone, and nothing supervises the server**: "Server: I want
  tailscale usage be the first class citizen. Thats my opionated choice. Obviosly if one does not
  need it - then fine, DIY". The door lets in only his tailscale login, never through Funnel. "I'd
  rather keep the Plannotator approach and avoid polluting launchd. I can always remote login to the
  machine and start the server manually." So the plugin's SessionStart hook and `lem board` start
  it, and no login item does.
- **An address for each workspace and task, two machines under one, and pushes**: his ask, not kept
  in his words. `/HOST/WORKSPACE/tasks/SLUG`, `lem serve --join HOST`, and a push when "Waits for
  you" gains a row; with Apple's topic `lemwaits`, "push notification worked".
- **He acts from the board**: of actions from the phone, "worth doing", and with no look of his at
  their design, "I allow you to use headless chrome for that, I think it will work?". Approve the
  criteria, merge after a confirm step, park: each the command a session runs, the session's form.
- **No stale pull request, and a folded header on a phone**: "gihub issue with stale elements should
  not happen again", so the server runs `lem land merged` for a pull request merged or closed on
  GitHub; of a task's header, "I believe it should be collapsed by default and unfold when
  requrested". His other notes are in `board-plan.md` of that folder.
- **A release is a change of the plugin's `version`** ("The latter will be a bit easier to manage"),
  which replaces "no version" in the design "Lem is a Claude Code plugin" (2026-11-15). Of this
  work: "I trust you here, go merge and push whenever you need to. ... I will wait for release.",
  and "we can afford breaking things (old Lem)".

What agents write, and the Python Lem needs:

- **Stories, flowcharts and pictures, early**: "rich media in markdown files - lem should know it's
  worth being used when tasks are planned and executed under lem; as well as step by step stories",
  and "those flowcharts and stories are worth to be produced early - for example after acceptance
  crierions are settled". The form is the session's: `prompts/writing.md`, read from the interview
  to the merge agent, with `--case` and `--chart` on an important decision. To his "Should we add
  anything about screenshots?" it added "A screenshot" and the capability `take-screenshot`.
- **A task's artifacts have one map**: "core sections and components should be standard for every
  project, so task artifacts map is predictable", and "I agree to limited number of artifacts - good
  choice": seven sections in one order, the records folded, as an Opus opinion proposed.
- **Python 3.11 stays, in the modern form.** Of a floor of 3.9: "Test it but if it will fail hard,
  we will use modern version. Its opionated software", and "`from __future__ import annotations`
  this considered harmful in python." So no script has that import; `lem_python.py` finds a newer
  Python for `bin/lem` and the hooks. Of the finder: "also `uv` can be tried". The form is the
  session's: `uv` is asked last, only for a Python it has, and the fix names `uv python install`
  beside `brew install python`.

## Decisions the maintaining session took

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

- **Every decision that is the owner's takes one path**, at plan time as in the build: the
  persona panel (`lem-panel`, the lead's step), then `decisions.py ask` with one concrete run
  (`--case`, `--case-was`, `--cause`, which the card shows above it), the wait for his answer
  while the rest goes on, with no time limit since 2026-11-18, and, when he says he is away, the
  experts' shared pick or the recommended option, not green. The question gate (`lem-gate`) sits at Lem's card. A decision
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
  too, so the landing, the lead, `decisions.py` (audit findings S1 and W2) and the review read
  the main checkout's table, and `land.py` reads every setting from it
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
  plan file that says `Size: small`, and a night that meets an item that is one plain change drafts no plan and
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
- **The mode and the ladder are built in the smaller of two designs** (2026-11-18). A first
  design of the plan's tasks 2 and 3 added six `lem decisions` commands, forms for what agents
  answer, a script that checked the lines a dialectic agent cites, and about 300 script lines
  (its own estimate). A Fable second opinion, asked before any builder started: "The ladder half
  is a state machine with parsers that no act of Lem's needs, and three of its rules fail toward
  settled", for one a persona's objection that the script could not parse was dropped and the
  rest then settled the decision green. So the rules of the ladder are one stage text that the
  lead applies, since the lead reads the code, and the script checks one thing only: two persona
  votes or more, all for the option taken. A count moves into a script when a real run shows a
  lead that records a level wrongly, and only that count.
  `docs/plans/2026-11-18-core-and-two-modes/mode-and-ladder.md` is the design. It corrects two
  sentences of the plan the owner passed, both told to him: a task that ran without him is not
  green only when something of his was decided without him, and an agent never merges while a
  task runs alone; and with him a decision that the gate or the personas settled gets no card,
  while Lem says each decision once in the conversation, for his "Sometimes I would love to know
  the decisions taken before implementation".
- **Two things a real run showed on 2026-11-18** (pySilver/lem-scratch#5 and #6, with the stage
  texts split by path). Lem tried `lem land land --by agent` after a proposal where
  `branch.land` is `owner`, because `stages/land.md` told it to try and let the script refuse;
  Claude Code's classifier blocked the call and showed the owner "2 actions blocked". The text
  now has Lem run it only where the settings say `agent`. And Lem did not know that the watch
  covers a pull request opened after it started; `SKILL.md` says so now. The same session
  refused a merge on the owner's words as relayed by its operator, as the text asks: nobody
  else's word is his.
- **A night ends as pull requests, and a task without the owner covers what a night was**
  (2026-11-18), on his "its actually got to be a PR to merge, not a plan". A night takes backlog
  items, the smallest first, four at most and one after another, marks each as the night's with `task-dir
  --night DATE`, which runs it without the owner, and from there every path is the one a day has. So the night's own path is
  gone: `night: yes` in a brief, the refusal of `lem decisions ask` for it, the draft that ended on
  a decision, the three tries. The sentences above that describe them ("A night plan asks no such
  decision", "a night that meets an item that is one plain change drafts no plan", "a report of
  that night ... that names a draft still `drafted`") and `settle --away` in his ruling on the
  experts tell the form before, and the state `drafted` is gone with it. The brake counts a night's pull requests that nobody merged or
  closed: with two or more, the night opens nothing.
- **The board is served, and the server draws it** (2026-11-20). The owner: "Lack of being able to
  oversee the process away from laptop its my biggest pain". The board was one file:// page that agterm
  opened, with 2,980 lines of its own JavaScript (the one script of `board.html` at 1971c8e)
  that read the state folder through copies of the log and of each task's files as scripts. Now
  `lem serve`, one standard-library server for the machine, draws every page from the state folder
  (`lem_board_model`, `lem_board_pages`, `lem_board_task`), and Turbo and a few Stimulus controllers
  are all the browser runs: a stream of server-sent events tells an open page each change, which it
  morphs in, so a phone, a laptop and agterm show the same board, and no file of the page is written
  at an event. Tailscale is the first-class way in from another device, behind `tailscale serve`, with
  the owner's own login as the check, Funnel refused, and the Mac itself served on 127.0.0.1 with no
  check. The server starts on demand (`--ensure` from the SessionStart hook and from `lem board`)
  and replaces itself after an update, with no launchd agent to install or to outlive the plugin. It
  shows a list of workspaces for the machine (`workspaces.json`), and the machine's name is in each
  address, so that a second machine's workspaces can join under their own. agterm gives an http page
  no bridge, so the board's two acts of agterm go through the server, on this Mac only. The board
  notices a merge on the forge itself: a thread of `lem serve` asks GitHub a few minutes apart about
  the open pull requests nobody watches, and for one merged or closed there runs `lem land merged`,
  the bookkeeping a status runs and no other step. Its notifications are web pushes with no payload,
  signed with a key kept in Lem's home folder, and `/usr/bin/openssl` signs them, the one program
  outside the standard library (`lem_push.py`). Two machines show under one address with `lem serve
  --join HOST`, which lists the other's workspaces as `HOST/WORKSPACE` and passes its pages and its
  stream through over the tailnet (`lem_peers.py`). A chart is drawn by a vendored mermaid, the file
  `lem-ask` pins, which only a document with a chart names and a page loads at its first chart.
- **The board's server runs the merge agent's merge, and the agent only writes its review**
  (2026-11-21). The first real task (pySilver/lem-scratch#12) showed it: the merge agent's review
  said `Verdict: merge.`, the task's session ran `lem land merge SLUG --by merger`, Claude Code's
  auto mode blocked that one Bash call ("1 action blocked by auto mode"), and the pull request
  stayed open until the owner opened a second session from his phone, which ran the same command
  unblocked. A block that holds in one session and not in the next is no step to rest the flow on.
  So the session writes the review down (`lem land merge-review SLUG --file ANSWER`), says one line
  and waits, and the server's duty runs `lem land merge SLUG --by merger --via server` in a thread,
  as it runs the owner's merge from the board; land.py's rules stay the gate, `merge.start` and
  `merged_by` say who merged and who ran the call, and a refusal of that merge, GitHub's or Lem's
  own (the base moved, the tip changed), is kept for its tip, so that the server tries the tip once
  and wakes the session with `lem: SLUG refused`. The script still takes `--by merger` from an
  agent; no text tells one to run it. The same task showed a live session called dead: agterm's
  tree gives a task's session as the login shell with the agent inside its `-c` string, and
  `agent_runs` read only the first two words, so the board said "No session runs this task" and
  the owner opened a second session beside the live one; it now reads the `-c` string as a shell
  would.

## Checks

```bash
bash tests/all.sh              # every suite below at the same time, one log each, a line of ok, FAIL and SKIP per suite
python3 tests/pick.py --base main  # the suites to run for what the branch changed (or name the files); all.sh still runs before main moves
python3 -B -m unittest discover -s tests/unit  # the unit level: one file for each script, its rules called in one process; all.sh runs it as the suite unit
```

The loop: the unit level after each edit; while a task is in work, only the one block that holds
the journey it changes; the blocks that `tests/pick.py` names once for a task, at its end;
`tests/all.sh` once before `main` moves. A block is never run before a change to count it: the
counts of the last full run are the before. A rule that takes facts and returns a result is a
unit case, a call of its function; a fact only git can show is a check in a block, in a throwaway
repository.

Each suite says how many checks it holds (`collected N`, `tests/checks.sh`), and a check that
cannot run here prints a `SKIP` line of its own. A suite whose `ok` and `SKIP` lines do not add up
to that count fails, and so does one that runs over its time limit (`LEM_TEST_LIMIT`, 30 minutes).
With `LEM_TEST_TIMES=FILE` each check of a block appends its seconds to FILE, so one run shows
which checks hold the time.

One suite alone, in the order of `tests/all.sh`:

```bash
bash tests/lem-settings.sh     # the settings and the places of what Lem reads, a task's state and the event log, the rule picker, the criteria and their check on the base (each lem-* block sources tests/lib.sh)
bash tests/lem-machine.sh      # the machine check, the correction queue and its hook, the plugin's files
bash tests/lem-state.sh        # the state folder git never sees, and the owner's status
bash tests/lem-decisions.sh    # a task's decisions, each taken by a level of the ladder, and the circuit breaker from its trip to his help, park, drop and resume
bash tests/lem-land-shop.sh    # the landing from `ready` through the checks and one read to a pull request, the merge agent's read and the merge, on the stand-in for gh
bash tests/lem-land-local.sh   # the landing in two halves of about equal time: decisions, criteria and the personas' read in the pull request's text here,
bash tests/lem-land-review.sh  # and the polish pass, the review, the bar, what makes a request careful and who merges it here
bash tests/lem-land-backlog.sh # what a review saw outside the change, filed as backlog items
bash tests/lem-land-github.sh  # the forge's own cases, and a remote that is not GitHub, which lands nothing
bash tests/lem-land-guards.sh  # the landing's guards and refusals, each next step run as the refusal names it
bash tests/lem-land-small.sh   # the fast track's landing, and what keeps it safe
bash tests/lem-serial.sh       # checks.serial under the repository's one lock, and checks.setup in a new worktree
bash tests/lem-naps.sh         # the [naps] settings and lem project may-nap
bash tests/lem-command.sh      # the command lem: each name, its arguments, stdin and exit status, help, and that no text names a script by its path
bash tests/lem-picker.sh       # the task picker, with a stand-in for agtermctl
bash tests/lem-session.sh      # a task's own session (lem session) with a stand-in for agtermctl, and the copy of the talk
bash tests/lem-serve.sh        # the board server and lem board over HTTP, on the afternoon of tests/board-showcase.py: the routes, each page's words, the stream, the jump to a session, the start on demand
bash tests/lem-board-act.sh    # the owner's acts from the board, and the server's duties across tasks, with a stand-in for lem session
bash tests/lem-peers.sh        # two machines under one address: two board servers on this Mac, a join, the loop guard, a machine that does not answer
bash tests/test-gate-panel.sh  # the panel's cast, in its one place
bash tests/test-ask.sh         # lem-ask's spec checks and every template; loads pages in headless Chrome when one is installed
bash tests/test-ask-expert.sh  # the experts' brief of a question in words, its folder and the record of each answer, one expert alone; no expert runs
bash tests/test-site.sh        # the page on GitHub Pages, from pages.yml's own copy step; its drawn page in headless Chrome when one is installed
bash tests/shellcheck.sh       # ShellCheck over tests/*.sh, one check for each file, or over the files named
python3 tests/pick.py --check  # the map of tests/pick.py: every file read by a suite, every suite in all.sh
bash tests/test-lem.sh         # every lem-* block at the same time, with its output in order; all.sh runs each as a suite of its own
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

To run a clone of Lem in one session, without the plugin's install, load its folder as the plugin
(Claude Code 2.1.325, 2026-11-17: the session listed every `lem:` skill and `lem:lem-builder`):

```bash
claude --plugin-dir /path/to/lem   # the plugin from this folder, for this session only, with its skills, agent, commands and hooks
```

A task's session that `lem session open` starts gets no `--plugin-dir` (`launch_line` in
`session.py`): its `lem` commands are the installed plugin's, not the clone's (read in the code,
not tried).

## Layout

Each script's module docstring says what it does and why; this list says where each thing is.

- `skills/lem/SKILL.md`: the entry point, what holds in every stage, and "One session for each
  task".
- `skills/lem/stages/`: one file for each subcommand, read only when it runs. `new.md` opens a task
  in its own session, and its "The request" and "The fast track" are that session's first steps;
  `interview.md` (the interview and the criteria) and `investigate.md` (a bug, a question) are the
  rest of the shape. `start.md` starts the build, `plan.md` and `build.md` are the lead's, `talk.md`
  is the plan talk, which only its defender reads, `ladder.md` a decision in doubt and `breaker.md`
  the circuit breaker. `land.md` is the land phase, and `polish.md` its step 3, on the standard
  track only. `status.md`, `away.md`, `correct.md`, `park.md`, `night.md`, `init.md`, `learn.md`
  and `nap.md` are the owner's other commands and the scheduled ones.
- `skills/lem/prompts/`: the standing briefs: `session.md` (a task's session: what it reads, a
  change of phase, a wake-up, what it never does), `lead.md`, `defender.md` and `reviewer.md` (the
  plan talk's pair), `scout.md`, `investigator.md`, `small.md` (the fast track's one builder),
  `landing.md` (a builder of a landing), `review.md` (the review before a pull request), `merge.md`
  (the merge agent), `writing.md` (how a document for the owner is written, from the interview to
  the merge agent) and `nap.md`.
- `skills/lem/templates/`: `profile.md` and `persona.md`, which onboarding fills; `handoff.md`, the
  hand-over between two agents of a task; `breaker.md`, the breaker's document.
- `skills/lem/harness/`: the capability contract, `README.md`, and one file for each agent.
- `skills/lem/scripts/`, each a command of `lem` or a module the commands share:
  - `project.py` (`lem project`): a repository's settings and the one place of each file Lem reads
    beside them (`PLACES`), a task's state and directory, the event log, the owner's status and its
    watch, `waiting` (the one list of what waits for the owner), and the machine's `load` and
    `handoff` numbers.
  - `session.py` (`lem session`): a task's own session in agterm, its change of phase, its wake-up,
    the handoff's check and the copy of the talk; `session_hook.py`: the plugin's `PreCompact` and
    `SessionStart` (`compact`) hooks of a task's session.
  - `land.py` (`lem land`): the landing, one refusable step at a time, from `ready` through the
    checks and the review to a pull request on GitHub, the merge agent's read, the merge and the
    cleanup.
  - `criteria.py` (`lem criteria`): a task's acceptance criteria, and the check that each one's
    tests pass on the branch and fail on the base. `decisions.py` (`lem decisions`): a task's
    decisions, each taken without the owner, and its breakers.
  - `serve.py` (`lem serve`): the machine's one board server, with the owner's acts, the jump to a
    session, the tailnet door and the duties across tasks; `serve_hook.py`: the SessionStart hook
    that starts it. Its parts: `lem_board_model.py` (the model, pure functions over the files),
    `lem_board_pages.py` (the pages of a workspace), `lem_board_task.py` (the board of one task),
    `lem_artifacts.py` (a task's files on one map), `lem_html.py` (`h()`, which escapes every text),
    `lem_push.py` (the notifications) and `lem_peers.py` (another machine joined with `--join`).
  - `board.py` (`lem board`): makes sure the server runs and opens a board, or with `--page FILE`
    any page of Lem, as a companion. `picker.py` (`lem picker`): agterm's picker over the tasks.
  - `doctor.py` (`lem doctor`): the machine check. `corrections.py` (`lem corrections`): the
    optional queue of the owner's corrections and its hook. `jev.py` (`lem-jev`): the client of the
    Jev model.
  - `lem_state.py` (the state folder and Lem's home folder), `lem_plans.py` (a plan's and a ruling's
    file name), `lem_sibling.py` (a sibling's command in the same process) and `lem_python.py` (a
    Python of 3.11 or newer for `bin/lem` and the hooks).
- `skills/lem/assets/`: what `lem serve` sends under `/assets/`. `board.css` is the board's look,
  the phone's too; `lem.css` and `lem.js` are the look and the palette every page of Lem shares, and
  a new page for the owner links both and brings no style of its own. `push.css` and `sw.js` are the
  notifications', `icons/` the board's icons, and `handover.html` the pattern of the onboarding's
  page. `vendor/` holds what `tools/board-kit` builds: `board-app.js`, the board's one script,
  `board-icons.json` and `mermaid.min.js`.
- `tools/board-kit/`: the maintainer's build of `vendor/`, which nobody who installs the plugin
  runs: the built files are committed. Its `README.md` says how to build and how to add a Stimulus
  controller to `controllers/`.
- Lem's home folder, `$XDG_CONFIG_HOME/lem` or `~/.config/lem` (`lem_state.config()`):
  `owner.jsonl`, the owner's away and back; `machine.toml`, this machine's settings, `[load]`,
  `[serve]`, `[peers]`, `[seats]` (`merger` and `session`, for a repository whose settings name
  none) and `[handoff]`; `workspaces.json`, the repositories the server shows; and what the server
  and the checks keep there: `serve.lock`, `serve.log`, `load.lock`, the push key `push-key.pem` and
  the devices `push.json`.
- `.lem/`: Lem's own settings, profile, cast and lessons, in the places every repository has them.
  Its `state/`, which git ignores, is the state of a repository's Lem: the tasks, the event log,
  the night reports, the naps, the experts' folders and a panel's copies. `.lem/worktrees/` holds
  the tasks' worktrees. `.revmux/` is the review tool's configuration for this repository.
- The naps, an optional part: `prompts/nap.md` is written after the owner's own nap routine and
  keeps its voice (a change is tried with one real nap, and its dream is read: a brief that makes a
  report of it is wrong); `stages/nap.md` starts one and `lem project may-nap` says whether one
  may. No page shows them; the retro reads their waking notes.
- `docs/`: the guides the README links, each in STE like the README, each with one job and under
  800 words: `flow.md` (how a task goes, with the one diagram), `when-lem-needs-you.md`,
  `pull-request.md` (what green means, the merge review, the merge, a conflict), `board.md` (the
  board, the phone, two machines under one address, the server), `install.md` and `linear.md`; and
  `settings.md`, the reference, one table for each table of the settings, one to one with
  `project.py` (`tests/lem-settings.sh` checks it). How Lem works inside is in this file and the
  skill. Beside them: `free-hour.md` (how an unattended maintainer's session may change Lem),
  `backlog/`, Lem's own deferred work, and `plans/`, the plans that built Lem, each finished one
  with a status line that names its commits and where later decisions changed it.
- `tests/`: the suites of "Checks". `unit/` is the unit level, a `test_*.py` for each script;
  `lib.sh` is what each `lem-*.sh` block sources, `checks.sh` how every suite counts its checks,
  `suites.sh` and `limit.py` what `all.sh` and `test-lem.sh` share, and `pick.py` the map of which
  suite reads which file. `board-showcase.py` writes the demo afternoon that `lem-serve.sh` serves,
  and makes the board's pictures through headless Chrome (`board-cdp.mjs`, which needs Node).
  `.github/workflows/ci.yml` runs `all.sh` when someone starts it by hand.
- `.claude-plugin/`, `bin/` and `hooks/`: what Claude Code reads to load this repository as the
  plugin `lem`, the one way Lem installs. `bin/lem` is Lem's one command: `lem NAME` runs the script
  NAME stands for, and `lem help` lists them; `lem-ask` and `lem-jev` are links to it.
  `hooks/hooks.json` starts, each through `lem_python.py`, the correction hook, the SessionStart
  hook of the board server and the two hooks of a task's session. Every text and every message of a
  script says `lem NAME`, so one permission rule, `Bash(lem *)`, covers them on every machine and
  after every update.
- `agents/lem-builder.md`: the builder, as a Claude Code agent definition; its body is the builder's
  standing rules, and `harness/claude-code.md` says how it is used and overridden.
- `assets/`: the logo (`lem.svg`), the figure alone (`lem-mark.svg`), and both in the night palette
  (`*-night.svg`, written by `night.py`). `assets/screens/` holds the board's pictures, light and
  dark, made by `tests/board-showcase.py`: `board-*` (the kanban), `task-*` (a task on "Overview"),
  `backlog-*` and `phone-*`. The README shows `board-*` and `phone-*`, `docs/board.md` `phone-*`,
  `docs/when-lem-needs-you.md` `task-*`, the site all three, and no page `backlog-*`.
- `site/`: Lem's page on GitHub Pages, `index.html` and `style.css`, written from the README and the
  guides in their STE, in the board's look (the six hues of `lem.css` at the same values), light or
  dark by the visitor's theme, with the copy buttons as its one script and nothing from another
  host. `.github/workflows/pages.yml`, started by hand only, copies it with the logo and the six
  pictures into `_site/` at their repository paths and publishes that; `tests/test-site.sh` runs that
  copy step as written.
- `skills/lem-ask/`, `skills/lem-interview-me/`, `skills/lem-dialectic/`, `skills/lem-root-cause/`,
  `skills/lem-gate/`, `skills/lem-panel/`, `skills/lem-linear/`, `skills/lem-ask-expert/`: the
  skills Lem names and ships. `lem-ask-expert` is Lem's own, with `scripts/experts.py` (`lem
  experts`: the brief of a question in words and the record of the experts' answers, in a folder of
  `.lem/state/experts/`). `lem-panel`'s `scripts/cast.py` (`lem cast`) finds the cast, copies it
  into a project, and keeps the copies a panel read in Lem's state folder. `NOTICE` says where each
  came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools,
and lem-ask's Stop hook (`skills/lem-ask/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, the mailbox chat, webrev,
agdoc, the backlog recipe, cronn, plannotator-tui, Codex) is checked for by `doctor.py` and never
copied in. The backlog's item format is the recipe's, and Lem's builders read it in rule 6 of
`agents/lem-builder.md`; no builder loads the recipe's skill, which is the owner's own tool.
