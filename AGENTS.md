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
- **One stage file per subcommand, read only when it runs.** `SKILL.md` holds what is true in
  every stage. A rule that one stage needs goes in that stage.
- **Lem's stages and a lead's stages stay apart.** `plan` and `build` are a lead's; the others
  are Lem's. A step that reads a task's code or its diff goes to a lead or to a fresh agent,
  never into `new`, `land` or `review`.
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init --existing`).
- **A change is measured by what it costs a developer on a small task** (the touches it asks of
  him, the waits, the agents it starts) as well as by what it guards.
- **Documentation describes the current state.** No changelog paragraphs, no "previously".
- **A session with nobody at the terminal reads `docs/free-hour.md` first.** A setup links Lem
  from this clone's main checkout, so an edit there is live at once in every repository that
  uses Lem. Such a session works in a worktree, on a branch, and never pushes.
- **A change to what a landing reads after its merge keeps reading the form before it, for one
  landing.** A setup links Lem from this clone's main checkout, so a landing of a change to Lem
  changes the files of the landing that runs. `land.py land` and `merged` put the change on the
  base branch and fast-forward the checkout that holds it (`follow`, or the merge itself where
  there is no remote), and from that moment every step runs the new files: the same run writes
  the state `landed` through the new `project.py state`; then `land.py clean`, a second run of a
  cut-off `land` or `merged`, the tracker's "land", `project.py tasks` and `may-start` for the
  queue, and the stage text Lem reads again (`stages/land.md` step 8, the end of
  `stages/new.md`). Each of them reads what the code before the change wrote. So a change to the
  keys of `landing.json` that those steps read (`branch`, `merged`, `merged_head` for `clean`;
  `intent`, `pr`, `proposed`, `gated`, `base`, `tree` and `landed_before` for a second run of
  `land`), to the state names, to the form of a state block that `project.py tasks` reads, or to
  the arguments of `project.py state`, `tasks` and `may-land`, reads the old form too. A later
  change may drop it, once no landing that wrote the old form is open. Nothing runs a landing
  from a copy of the scripts, and no step is added for it.

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
  it is the session's design: `skills/lem/scripts/jev.py`, linked as the `jev` command, and
  `setup.py --corrections on|off`, which the owner runs and no agent does.
- **As a plugin, the correction hook comes with the install, and the repository says yes for
  all**: he picked "With the plugin; the repository says yes for all" and wrote "I'm divided
  between (1) and (2); I believe Lem will not be a personal preference but rather a way to work
  with specific project. Just like revmux" (2026-11-15; (1) was each person's own yes in the
  untracked file). So `hooks/hooks.json` is a part of the plugin, and the tracked
  `corrections.collect = true` is the consent of everybody who works in the repository.
  `setup.py --corrections` stays for the link form while that form exists.
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
- **The personas' read of the stories is his to skip, and only when every story names only the
  developer**: he asked whether the read should be optional ("In some cases the owner has all the
  knowledge that is needed for task, so personas read would be a pure waste of time and money"),
  and answered "I agree" (2026-11-16) to the proposal a Fable second opinion shaped. A story that
  names a person other than the developer gets the read, and Lem asks nothing. When every story
  names only the developer, Lem asks one fixed question in the terminal, "The stories name only
  you. Skip the persona read? (y/n)". Lem never skips the read by its own judgment: it wrote the
  stories, and the author of a wrong reading sees it as clear. On his yes Lem logs his words and
  he approves the stories, and the pull request stays green, because the decision was his. The
  usual path only: the rare path's read is the only approval there and always runs. The form is
  the session's design: his word is the decision `decisions.py log SLUG --by owner --what "the
  personas' read of the stories" --chose "no read: the stories name only the developer"`, with his
  answer in `--why`; `land.py` (`READ_SKIP`) takes a feature with no `stories.read` only when an
  approval of his follows that decision and both come before the first state that names a lead
  (`lead: builder` or `lead: session`), which is how the script tells the usual path from the
  rare one, and its checks then say "the stories: not read by the personas, on his word (DATE); he
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
- **Linear only, and the local backlog stays local**: Lem supports Linear and no other tracker
  now, built so that another can be added. A backlog item is never mirrored to Linear, never
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
  with the reversed one, its tasks, its stories and each issue raised against it.
- **Lem tells the kind of a request, asks when it is unclear, and a bug is investigated
  first**: of a small fix taken as a correction with no scout, "Well typically the
  root-cause-investigation is needed to unerstand what triggers the bug that we aim to correct,
  isn't it?"; of the ask "invoices show 0 after a refund", "From such input its kinda hard to
  deduct if we want to investigate the bug or its a feature request. Confusion."; and "Lem should
  try to understand from the requestwhat kind of request it is and ask for clarification when
  confused? We may want to list few keywords for different types of work" (2026-11-16). The form
  is the session's design, to which he wrote "I have no objections for other stuff (work kind,
  merge strategies)": six kinds (bug, feature, correction, investigation, chore, docs) taken from
  the ask's words alone, with example words in `stages/new.md` as hints and no code that matches
  them; the first question of the interview when the words do not settle it; the kind in
  `task.md` and in a state line `kind: KIND, because WHY`, and the branch's type from it; a bug
  investigated before any story by a fresh builder (`prompts/investigator.md`) that commits a
  failing test and finds the cause with the `lem-root-cause` method, whose report takes the
  correction path, the usual path, or ends the task; an investigation that ends with its answer;
  and the state `answered`, a task that ended with a report and nothing to merge.
- **The time card gets exact start times**: asked in his Inbox on 2026-11-17 whether the board's
  time card should get exact start times now, he picked "Build it now: each stage logs its start,
  and the card becomes exact". The form is the maintaining session's: one `NAME.start` event for
  each stage that logged only its end, with a fixed form that `project.py log` checks (`STARTS`),
  and the event that already ended the stage stays its end. `land.py` logs the starts of the
  polish pass, the checks and a review that is due; the stage texts give the line for the
  interview, the scout (with `scout`, its end, which had no event), the personas' read, an
  investigation and each builder's job. `SKILL.md` lists them with their ends.
- **The README shows the plugin first, and the clone is for people who change Lem**: asked in his
  Inbox on 2026-11-17 (thread "Lem production pass") which install the README shows first, he
  picked "The plugin first; the clone for people who change Lem". So the README's install is the
  two `claude plugin` commands with `--scope project` and then `/lem init`, and the clone with
  `setup.py --project DIR` and the home links follow in a few lines with a link to
  `docs/install.md`. One repository still uses one way, the plugin or the links.
- **The repository is private now, and public later**: asked in the same thread whether the
  repository stays private, he picked "Private now, public later". So the README says that an
  install of the plugin needs read access to `pySilver/lem`; that line goes when he makes it
  public.

Designs taken on 2026-11-14 and 2026-11-15 after a question of the owner's. They are open to
him, and they are not his rulings until he says so:

- **`/lem annotate FILE` is the owner's verb for marking up**, after "then shouldn't it be
  `/lem annotate`?": it runs what `tools.annotate` names, as `/lem ask` is his verb for a
  question.
- **`/lem build` takes a plan file too, and lists the waiting plans when it gets no name**,
  after "why not `/lem build <path to plan>` instead?".
- **The correction hook is registered for one repository first**, after "should we place a hook
  per project or globally?": the yes is one project's, and a hook in the home settings starts on
  every message in every repository. The session that carried his notes decided it and told
  him; the home form stays for an owner with many repositories that use Lem.

- **Lem can load as a Claude Code plugin, beside the links**, after "can we make it more self
  contained? lem is aimed to be per-project companion" and his "I agree" to a test first. The
  test ran on 2026-11-15, and the session that carries his words decided the first step, which
  only adds files: `.claude-plugin/plugin.json` with no version (so each commit is an update),
  `.claude-plugin/marketplace.json`, `bin/` with links to `lem-ask` and `jev`, and
  `hooks/hooks.json` after his ruling on the hook. The links of the setup work as before, and
  removing the four undoes it. As a plugin the builder is `lem:lem-builder`, so the harness file
  and the machine check know two names. Which form the README shows first he ruled on
  2026-11-17 (above: the plugin first). No task has run in the plugin form yet; the README and
  `docs/install.md` each say so in one line, which the first such task replaces with its result.
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
  untracked, read from the main checkout, limited to `[seats]` and `[tools]`, written by
  `/lem reviewer`. Lem never changes the seat by itself.

His notes of 2026-11-16 on the page of the new flow, as the design session carried them to the
session that builds. `docs/plans/2026-11-15-three-touches/amendment-2026-11-16.md` has each in
full, with what was designed from it.

- **The user of Lem is a senior developer with little attention to give**: "Assume that persone
  that works with Lem will be a skillful developer with many years of experience. Not a business
  person. Its just a developer that does a lot of things in many projects, so his attention is
  limited. But he may tell to use this and that technology or reivew options during interview."
  No text of Lem writes for a business reader. What he names in the interview is a direction
  the plan follows.
- **Most requests have an interview and his check of the stories; a green pull request he merges
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
  keeps what has no options: the stories that wait for his yes (a kind only he may change among
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
  lead change a story a persona doubted before the owner sees it; the stages keep the story as
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
  is never a correction; the lead at the plan, by a topic or a pattern other code will copy; and
  the fresh agent that reviews the diff before the pull request, whose record holds `careful`
  and `careful_why` and which runs the full set when it calls careful what the plan did not. The
  last is the look that takes the place of the path list's floor: its judge did not build the
  change. `land.py` enforces what the records say: a review record with no call is refused, a
  request is careful when the plan (its `careful: yes` under its title, in any commit of the
  branch), the owner's word in the brief or the newest answered review says so, and an agent
  merges only a green request whose newest review said not careful. `careful.missed` is the
  event for a careful call of the review that the plan did not make. The topics cannot be lifted
  by the branch they guard: `project.py` reads `[flow]` from the main checkout's settings, also
  in a task's worktree, so the landing, the lead, `decisions.py` with `flow.decision_wait`
  (audit findings S1 and W2) and the review read the main checkout's table, and `land.py` reads
  every setting from the main checkout wherever it runs. A change whose diff edits
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
  of the files a lead reads). So a small change, one plain change with one story in his own
  sentence, no topic in reach and no question open, whatever its kind, has one builder and no
  lead: `prompts/small.md`, a brief complete in itself, and the builder's standing rules. It
  commits no plan; its story is `stories.md` in the task directory, approved in his name, with
  its test line, and `stories.py` and `land.py` read it there when the branch has no plan file,
  for a correction only. A change that keeps behavior has `no test` and its builder runs the
  whole gate suite. Before it commits, the builder reads its change against the topics and stops
  with `the stories wait for the owner: the small change is a feature` when it reaches one, needs
  a second rule or a decision, lowers the bar or grew. Its landing is `start`, `base`, `gate`
  (with `stories.py red` once), one read by the review agent itself, and `propose` with a short
  text; no polish pass at all, and its builder files what it sees outside the change. A small
  change that is
  careful after all (by the review's call or its edit of the settings) is not green and a person
  merges it, since it skipped the interview, the read and the plan; one that lowers the bar is
  refused at the gate. Lem says the size, the branch, the story, what happens and what he must do
  in one line before anything runs, and nothing repeats it. Counted from the text after the
  change, a typo, a rename and a one-rule fix each start two agents (the builder and the review
  agent), and the builder reads `prompts/small.md` and `agents/lem-builder.md`, 1,954 words
  (`wc -w`: 775 and 1,179, at 15d5697, 2026-11-17).
- **A feature has one approval and no ceremony that nobody asked for** (2026-11-17), from the same
  audit's findings: the interview's restate and explicit yes were a second approval of what the
  stories say (F3), so the interview's questions come from the `lem-interview-me` method and its
  restate and yes are the stories and his yes to them; each question is one line in the
  conversation with Lem's guess, and no page opens for it. A story whose change keeps behavior (a
  rename, a bump, a refactor) is held by the suite, `- no test: the change keeps behavior; the
  suite holds it`, and its builder runs the whole suite, where a contrived failing test was asked
  before (F4). "A new kind of test" no longer makes a plan careful: a pattern is product code
  that other code will copy (F5), since a one-line fix could become a plan talk and the full
  review by it. A task has a state block from the moment it opens, `held` with `the interview
  waits for the owner` and the kind line, so the status and the board show it during the
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
  `landing`, `open` or ended, and `stages/new.md` starts a lead only for a task that is `building`
  or has no new state block. New work on an ended task is a new ask.
- **No plan has the kind correction** (A3). A lead could write `Kind: correction` in a plan, on
  the rare path or at night, and then no approval, no read of the stories and no polish pass was
  asked: the probe's plan went through the gate, the read and `propose` green, and `land --by
  agent` landed it. A one-rule ask is a small change, with its story in the task directory,
  approved by Lem with `--correction`. `stories.py` and `land.py` refuse a plan file that says
  `Kind: correction`, and a night that meets an item that is one plain change drafts no plan and
  names it in the night report as ready to start as a small change.
- **The gate removes what its own commands leave** (R3, the first run). `python3 -m unittest`
  left two `__pycache__` folders in a repository with no `.gitignore`, the gate refused the tree,
  and the first small change ended in a second task for the ignore rule. The guard serves
  "nothing lands that the checks did not pass on", which is about the committed tree. So the
  gate notes the untracked files before it runs, removes the ones its commands created, names
  them, and refuses only a changed tracked file; onboarding proposes the ignore lines for what
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

## Checks

```bash
bash tests/all.sh              # every suite below at the same time, one log each, a line of ok and FAIL per suite
```

One suite alone:

```bash
bash tests/test-lem.sh         # Lem's scripts, in throwaway repositories: the blocks tests/lem-*.sh at the same time; loads the board in headless Chrome when one is installed
bash tests/lem-land-shop.sh    # one block of them, alone (each block sources tests/lib.sh)
bash tests/test-gate-panel.sh  # the gate's log and the panel's cast, with the paths a project's settings name
bash tests/test-ask.sh         # lem-ask's spec checks and every template; loads pages in headless Chrome when one is installed
bash tests/test-ask-expert.sh  # the experts' advice in a choice's record, the end of the wait, settle --away, and the brief; no expert runs
bash tests/test-board.sh       # the board over a repository whose tasks stand in every lane; loads its pages in headless Chrome when one is installed
shellcheck tests/*.sh
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

## Layout

- `skills/lem/SKILL.md`: the entry point and what holds in every stage.
- `skills/lem/stages/`: one file per subcommand, and `talk.md`, the plan talk of a careful or
  large plan, which only its defender reads.
- `skills/lem/harness/`: the capability contract and one file per agent.
- `skills/lem/scripts/`: `project.py` (a repository's settings, task state and the event log),
  `doctor.py` (the machine),
  `board.py` (opens the board), `land.py` (the landing, one refusable step at a time: the
  machine checks, the review's floor and its record, the pull request, the merge),
  `corrections.py` (the optional queue of the owner's corrections: its hook, and what a retro
  reads), `jev.py` (the client of the Jev decision model, which the hook runs by its path and
  the setup links as the `jev` command), `stories.py` (a task's stories, read from the top of
  its plan, or for a small change from `stories.md` in its task directory, and the check that
  each one's tests pass on the branch and fail on the base commit),
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
- `docs/`: the reference pages the README links, each in STE like the README and each with one
  job: `flow.md` (how one task goes, for each size, with the plan talk and the diagrams),
  `settings.md` (every setting with its default, one to one with `project.py`), `inside.md` (the
  two levels, the agents and their briefs, a task's files, the event log, the board),
  `install.md` (what Lem needs, each form of install, what Lem writes and how to remove it) and
  `examples.md` (the real runs with their dates, and illustrations). Beside them `free-hour.md`
  (how an unattended session may change Lem), `linear.md` (how a project connects Linear),
  `backlog/`, Lem's own deferred work, and `plans/`, the plans that built Lem: each finished one
  opens with a status line that names its commits and where later decisions changed it.
- `.lem/`: Lem's own settings, profile, cast and lessons, from its onboarding, which `/lem` reads
  when Lem runs in this repository. `.revmux/`: the review tool's profiles, lenses and project
  profile for this repository.
- `tests/`: the suites of the Checks above; `all.sh` runs them all, `lib.sh` is what each
  `lem-*.sh` block sources. `.github/workflows/ci.yml` runs them on a push.
- `scripts/setup.py`: the setup script. It links the skills, the builder agent and the `lem-ask`
  and `jev` commands from this clone into a home directory, never over something else, and runs
  the machine check. `--corrections on|off` registers the hook of the correction queue in the
  agent's settings or takes it out, and is the owner's to run. With `--project DIR` it links into one repository only. Use that for a trial: links in
  the home directory show Lem to every repository on the machine, also to one where an older
  flow still runs.
- `.claude-plugin/`, `bin/` and `hooks/`: what Claude Code reads to load this repository as the
  plugin `lem`: the manifest, a marketplace file that lists the one plugin, links to the two
  commands, which a plugin's `bin/` puts on the Bash tool's `PATH`, and the correction hook.
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
  `scripts/experts.py` (the experts' brief, and their answers into the record).
  `NOTICE` says where each came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools, `skills/lem-backlog` uses `${CLAUDE_SKILL_DIR}`,
and lem-ask's Stop hook (`skills/lem-ask/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, the mailbox chat, webrev,
agdoc, cronn, plannotator, Codex) is checked for by `doctor.py` and never copied in, and a project that prefers its own tool for a
role says so in its settings or its `AGENTS.md`.
