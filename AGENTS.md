# Lem

Lem is the `lem` skill and the skills it ships: one flow for a unit of work in any repository, with each project's settings kept
in that project's repository. `README.md` says what it does; this file says how to change it.

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
- **Documentation describes the current state.** No changelog paragraphs, no "previously".
- **A session with nobody at the terminal reads `docs/free-hour.md` first.** A setup links Lem
  from this clone's main checkout, so an edit there is live at once in every repository that
  uses Lem. Such a session works in a worktree, on a branch, and never pushes.

## The owner's rulings

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

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
- **What must not go wrong is named by topic as well as by path, and the agent says whether a
  task is careful**: "we analyze the project, then we suggest what are the dangerous zones or
  topics and let user provide more ... Later at a plan time we can understand if it touches
  anything whats dangerous and needs to be taken carefully. Works better than just code path",
  and "it would be nice to get a suggestion from Agent whether its should be safe run or not,
  human can overlook real danger" (2026-11-15). The form is a design from those words:
  `flow.topics` beside `flow.careful`, proposed at onboarding; the lead's call with one sentence
  of why in the plan, the state and the report; a path match that no judgment overturns; the
  owner's "this one is careful" at any time before the landing. No code matches a topic.
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
  question. `plan.md` step 4 holds the rules, and `project.py`'s `plan.talk` the counts, with
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
  and the machine check know two names. Not in it, and his to rule: the plugin as the one
  documented way to install, which waits for one real task in that form.
- **One person can say no to the correction queue, and nobody is switched on by a file git does
  not show**: `[corrections] collect = false` in `.lem/project.local.toml`, and never `true`
  there. A design of the session that carries his words, for the half of him that leaned to
  each person's own yes.

- **The reviewer's seat is a table**, after "should we or can we specify model and effort level
  of the reviewer?": `[seats.reviewer]` with `agent`, `model`, `effort`, `plan_effort`.
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

## Checks

```bash
bash tests/test-lem.sh        # Lem's scripts, in throwaway repositories; loads the board in headless Chrome when one is installed
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
- `skills/lem/stages/`: one file per subcommand.
- `skills/lem/harness/`: the capability contract and one file per agent.
- `skills/lem/scripts/`: `project.py` (a repository's settings, task state and the event log),
  `doctor.py` (the machine),
  `board.py` (opens the board), `land.py` (the landing, one refusable step at a time: the
  machine checks, the review's floor and its record, the pull request, the merge),
  `corrections.py` (the optional queue of the owner's corrections: its hook, and what a retro
  reads), `jev.py` (the client of the Jev decision model, which the hook runs by its path and
  the setup links as the `jev` command), `stories.py` (a task's stories, read from the top of
  its plan, and the check that each one's tests pass on the branch and fail on the base commit),
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
  builders of a landing, of the agent that routes and runs a review before a change is proposed,
  and of the reviewer in the other pane.
- `docs/`: `free-hour.md` (how an unattended session may change Lem), `linear.md` (how a
  project connects Linear), and `backlog/`, Lem's own deferred work.
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
- `assets/screens/`: the README's pictures of the board, for a light and a dark theme, at two
  device pixels for each pixel. `board-*` and `task-*` are renders of
  `skills/lem/assets/board.html` over demo data, and so is `backlog-*`; `real-task-*` is the board of the first task
  that ran through Lem, over its real event log.
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
