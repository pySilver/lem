# How one task goes

This page gives each step of a task, from your request to the merge. The words of a day are in
the [README](../README.md#the-words-you-meet), and the parts inside Lem are in
[inside.md](inside.md).

```mermaid
flowchart TD
    req([You type /lem and a request]) --> look{Lem names the type and the size,<br/>and reads the request against each topic}
    look -- a bug or a question --> inv[A builder investigates it first]
    look -- small change --> small[One builder makes the change.<br/>No lead, no plan, no wait for you]
    look -- full change --> ctx{Is the whole context written,<br/>for example in a complete ticket?}
    ctx -- no --> interview[The interview, one question at a time.<br/>A scout reads the code at the same time]
    interview --> crit[Lem writes the acceptance criteria.<br/>The personas read them]
    crit --> approve[You approve the criteria]
    ctx -- yes --> leadcrit[The lead writes the criteria.<br/>The personas read them.<br/>A doubt stops the task for you]
    approve --> plan[The lead commits a short plan]
    leadcrit --> plan
    plan --> big{Is the plan careful or large?}
    big -- no --> build[One new builder for each task of the plan]
    big -- yes --> talk[The plan talk in a companion session]
    talk --> build
    build --> polish[The polish pass]
    small --> checks
    polish --> checks{The checks}
    checks -- red --> repair[A builder repairs it] --> checks
    checks -- green --> review{A review, as large as the change needs}
    review -- a must-fix finding --> fix[A builder fixes it] --> checks
    review -- no must-fix, or two rounds done --> pr[A pull request:<br/>green or not green in its first line]
    pr --> merge[You merge it. Lem merges a green one that is not careful,<br/>if the settings permit it]
    merge --> after[Lem brings each other open task onto the new base]
```

## The first look

Lem reads the words of your request before an agent reads the code. It names the type, the size
and the topics in reach, in one line, before an agent starts. Nothing repeats that line.

**The type** is a Conventional Commits type, and it gives the branch its name, `<type>/<slug>`.
The words in the table are hints for the judgment of Lem. No code compares your words with them.

| Type | Use it when | Words that often show it |
| --- | --- | --- |
| `fix` | something is wrong today | "broken", "shows 0", "since yesterday" |
| `feat` | something is not there | "add", "allow", "let me" |
| `refactor` | the code changes, and the behavior does not | "rename", "move", "split" |
| `perf` | the same result, faster or with less | "slow", "faster" |
| `test` | only tests change | "cover", "a test for" |
| `docs` | only a document changes | "document", a typo in the README |
| `chore` | work that no user of the product sees | "upgrade", "bump", "the CI" |
| `question` | you want an answer, not a change | "why", "find out", "check if" |

When your words do not show a fix or a feat, the first question of the interview asks it. Lem
gives its guess with the question. Only you change the type of a task.

**The size** selects the path. A small change is one plain change: one acceptance criterion in
your own sentence, no topic in reach, and no open question. A typo, a rename, a version bump and
a fix of one rule are examples. Each other request is a full change. If Lem cannot tell, it takes
the small change, and the builder checks the size again. `/lem plan` always makes a full change.

**The topics** are the sentences of what must never go wrong in your project. A topic in reach
comes first in the line, for example "Careful: this changes how a customer is charged. feat, full:
...". A request in reach of a topic is never a small change.

## A small change

1. Lem writes the one criterion into `criteria.md` in the task directory, and approves it in your
   name. The personas do not read it, and the pull request says so.
2. One new builder makes the change. There is no lead and no plan file.
3. A change of behavior gets a test that fails on the base branch. A change that keeps behavior
   gets the line `no test: the change keeps behavior; the suite holds it`.
4. The builder runs the tests of the files that it changed. It also runs the formatter, the linter
   and the type checker that the `AGENTS.md` of the project names.
5. Before it commits, the builder reads its change against each topic. It stops if the change
   could reach a topic, needs a second rule or a decision, lowers the bar, or grew. Then Lem tells you in one line that the request is a full change, and why, and
   the interview starts. The commits stay on the branch.
6. A defect that the builder saw outside the change becomes one backlog item, in a commit of its
   own. Nobody asks you about it.
7. The landing has five steps: `start`, `base`, the checks, one read by the review agent, and
   `propose`. There is no polish pass.

- Say "full" at any time, and the task becomes a full change.
- A small change that is careful after all is not green, and a person merges it. The review can
  call it careful, and an edit of `.lem/project.toml` makes it careful.
- A small change that lowers the bar is refused at the checks, and it becomes a full change.
- A small change starts two agents: the builder and the review agent.

## A full change

### The interview and the acceptance criteria

You are there for this part. It ends with criteria that you approved.

- **The task shows at once**, with the state "the interview waits for the owner".
- **A scout reads the code during the interview.** It changes nothing. It gives facts: what is
  there, what the code does today, and what limits your request.
- **Lem asks one question at a time**, with its guess. A yes or a typed value is one line in the
  conversation. A question with two or more options goes on the question page.
- **You can be technical.** A technology, a library or an approach that you name is a direction,
  and the plan obeys it.
- **A defect outside your request is not lost.** The polish pass repairs a small one, and it files
  each other one in the backlog.
- **Lem writes the criteria after the scout reports.** It shows them in the conversation, each
  with the facts that it comes from. At the same time, the personas read them with two model
  families. A split between the families counts as a doubt.
- **A partial read counts.** The pull request says who did not answer. If nobody answers, the read
  starts again. If nobody answers two times, the work continues, and the pull request is not
  green, with "the criteria were not read" first.
- **You can skip the read when the criteria name only you.** Lem then asks: "The acceptance
  criteria name only you. Skip the persona read? (y/n)". Lem never skips it by its own decision.
- **You approve the criteria once.** If you say yes before the read ends and nobody is confused,
  Lem tells you so in one line. Otherwise one page shows the result of the personas, then each
  criterion. A criterion that a persona flagged stays as Lem wrote it, with the answers next to
  it.
- **The build starts only after your yes.** If you go away first, the task waits with the line
  "the criteria wait for the owner".
- **Approved criteria do not change silently.** A change of a criterion gets a record with the
  text before and after, and the pull request is not green until you approve the change.

### A complete request

These requests have all of their context, and they get no interview:

- a ticket that says what you want, and how to see that it is done;
- a backlog item with settled options;
- a night plan that you start;
- an investigation report that settles what you want.

Lem tells you so in one line, and you can say "interview me". The lead writes the
criteria from the code, and the personas read them. If nobody is confused, the build starts
without a wait. If a persona has a doubt, or a rule needs a guess, the task waits for you.

### The plan and the build

- **A builder leads the task.** Its first commit is a short plan in
  `docs/plans/YYYY-MM-DD-<slug>.md`. The setting `paths.plan_file` changes the form of the name.
- **The plan starts with the acceptance criteria**, word for word. The lead adds only the test
  lines.
- **A plan has one to seven tasks.** A plan with more than three tasks is large. A plan can end
  with a task that corrects the documents that the change made false.
- **A plan can name a lowered bar**, with a reason for each file under `## The bar`. The pull
  request is then not green.
- **The lead decides if the plan is careful**, and writes the reason under the title of the plan.
  A careful or large plan stops for the plan talk.
- **One new builder makes each task of the plan.** The lead writes no code. No review comes after
  each task: the review before the pull request reads the whole change.
- **A builder obeys the `AGENTS.md` of the project.** A worktree is a plain git worktree, with no
  `.env` file and no test database. If your tasks need them, name a worktree script there.
- **A task can need the result of another task.** If the lead finds this at its plan, and the
  other task is not landed, its task waits in the queue after the other task.
- **An approach that failed two times gets a new approach**, not a third patch.
- **The lead writes a report**, and the state becomes `ready`.

## Careful

Your project names what must never go wrong as topics in `flow.topics`, for example "a customer is
charged the wrong amount". No list of paths decides it. Three agents read a change against the
topics, and in doubt each one says careful:

1. Lem reads your request and the facts of the scout.
2. The lead reads its plan. A plan is also careful when it starts product code that other code
   will copy.
3. A new agent that did not build the change reads the diff before the pull request.

Your word, the line `careful: yes` of the plan, the newest review, and a diff that changes
`.lem/project.toml` each make a task careful. A careful task gets:

- a plan talk before the code, if the plan was careful;
- the full review set of the project;
- a person's merge, whatever `branch.land` says;
- a line after green or not green that says careful, with each reason;
- a note that says if the change holds a migration, and how to revert it.

Lem reads `flow.topics` from the main checkout, so a branch cannot change the topics that guard
it. Only your yes adds a topic.

## The plan talk

The builder that wrote the plan stops. Lem opens a companion session. Its agent, the defender,
argues the plan with the reviewer in the other pane, through the mailbox. You can read both panes.

- **The reviewer gives all of its questions in its first turn**, the most expensive first.
- **Each question gets one repair**, or a refutation with a cite. The reviewer answers each
  question by its number: `closed` or `holds`.
- **A question that holds two times becomes a design choice**, and Lem asks it.
- **A repair that adds a mechanism**, for example a guard, a cache, a flag or a retry, names the
  decision under it. The reviewer says "at the cause" or "layer over" that decision. A layer over a
  decision with no source is no repair.
- **An addition names four things, or the other side refuses it**: the failure that it prevents,
  the input that causes it, if that input is realistic, and what breaks without it.
- **A late question is not argued.** The plan records it as "raised, not argued", and the review
  before the pull request examines it.
- **The talk has a limit** of four turns for each question, plus two. A talk over the limit is
  recorded as it occurred, and the pull request shows it.
- **A settled position is a claim**, not a fact, for the review before the pull request.
- **The companion closes after the talk.** Then a new builder leads the build.

`[seats]` names the reviewer and the defender ([settings.md](settings.md#seats)).

## Which tests run when

- **A builder runs the tests of the files that it changed**, and of their direct callers. No
  builder runs the whole suite.
- **The checks run the whole suite one time**, before the pull request: each command of
  `checks.commands`.
- **A command under `checks.alone` needs the computer to itself**, for example an end-to-end suite
  with fixed ports, one database or a browser. Lem runs these commands under one lock for the
  repository, after `checks.commands` pass. A builder that needs one such test for its criterion
  runs it through the same lock.
- **The test of each criterion runs on the branch and on the base commit**, one time, in the
  checks.
- **With git hooks, the checks hold only tests.** At `/lem init`, Lem looks for pre-commit, husky
  or lefthook. With hooks, it proposes only test commands, because the hooks run the linter and
  the type checker at each commit. With no hooks, it also proposes the linter and the type checker
  that it finds.

## The landing

One task is in the landing at a time. A landing that stopped continues from where it stopped.

1. **`start`.** A project with no command in `checks.commands` gets no pull request. The one
   exception is the task that adds the checks, and its pull request is not green.
2. **`base`.** Lem rebases the branch on the base branch. A builder resolves a conflict.
3. **`polish`.** For a full change, a new builder makes the polish pass.
4. **The checks**, with no model in them.
5. **The review.** An agent that did not build the change reads the diff.
6. **`propose`.** Lem pushes the branch and opens the pull request, or marks the branch as ready.
7. **The merge.** You merge, or Lem merges if the settings permit it.
8. **`clean`.** Lem removes the worktree and the branch of the task.

**The polish pass** looks for a short, fixed list, and nothing else:

- a comment or a document that the change made false;
- a leftover, for example debug output or dead code;
- code that works and is difficult to read;
- the defects outside the task: it repairs a small one, and files each other one.

The pass changes no behavior, no test of a criterion and no plan.

**The checks** run each command of `checks.commands` at the root of the worktree, then each
command of `checks.alone` under the lock. Lem removes the untracked files that a command leaves,
and names them. The test of each criterion must pass on the branch and fail on the base commit.
The bar must not go down, unless the plan gives a reason for that file. A red check goes to a
builder. If the base branch already fails the same command, Lem opens a task for that command, and
this task waits for it.

**The review** is as large as the change needs. An agent reads the diff and what each profile of
the review tool is for. A small and simple change gets one read. Each other change gets a round
with the profiles that fit, so a change of documents gets no security check. A careful task gets
the full set. A must-fix finding goes to a builder, and the fix gets the checks and a second
round. After two rounds, Lem proposes the change as it is. If one source does not answer, the
review counts, and the pull request says who answered.

## The pull request

The first line says green or not green. Each reason for "not green" is one line, before all other
text. Then come your words, the acceptance criteria with their tests, each check, each decision
with who took it and why, and the notes of Lem.

A pull request is green when all of these are true:

- the checks passed, and the bar did not go down;
- a review read the change as it is now, was as large as the floor, and found no must-fix;
- no acceptance criterion changed during the build, or you approved each change;
- no choice was taken by the timeout or by the experts;
- the checks were the checks of the main checkout;
- the read of the criteria did not stay unanswered two times;
- it is not a small change that is careful.

With a remote on GitHub, Lem pushes the branch and opens the pull request without a question:
`branch.propose = "pull-request"` is your approval, and you gave it at onboarding. With `merge`,
with another remote or with no remote, Lem marks the branch as ready. Other steps that leave the
computer wait for your word.

**The merge.** A person merges by default (`branch.land = "owner"`). With `branch.land = "agent"`,
Lem merges a pull request only if it is green and its newest review said not careful. Type
`/lem land <task>`, or say "land it", to merge an open pull request or a ready branch. If the base
branch moved after the checks, the checks run again first.

## After a merge

- **Lem watches its open pull requests.** One watch runs in the background while a task is open.
  It asks the forge every `flow.watch_seconds` seconds, with one call for all the pull requests.
  A session of Lem that starts also asks the forge first.
- **A merged pull request ends its task.** Lem marks the task `landed`, removes its worktree and
  branch, and moves its ticket. A task that waited for it can start.
- **A pull request closed with no merge drops its task.** The branch keeps its commits, and Lem
  tells you how to delete it.
- **Each other open task comes onto the new base**, the ones with a conflict first. Lem rebases the
  branch, and a builder resolves a conflict. The checks run again. After a conflict, one read
  checks the resolution. Then Lem updates the pull request, and it tells you in one line: "rebased
  on main after #3 merged; one conflict in shop/dates.py, resolved by a builder; the checks passed
  again".
- **The board shows when Lem last checked the pull requests.** When no watch runs, it says
  "nobody watches". Type `/lem` to look again.

## The queue

- **The limit is `flow.max_tasks`** tasks that build or land at one time. A task over the limit
  waits, and it starts when a place is free.
- **A task waits for another task only when it needs its result.** Its state is `queued`, with the
  line `after:` and the name of that task.
- **Two requests that only name the same file each start at once.** The landing settles an
  overlap.

## A bug and a question

```mermaid
flowchart TD
    bug([A bug: something is wrong today]) --> inv[A new builder, the investigator, examines it.<br/>For a bug: a test that fails, and the cause<br/>as a file and a symbol. It changes no behavior]
    question([A question]) --> inv
    inv --> report[Its report: reproduced or not,<br/>the cause or the answer,<br/>and what comes next]
    report -- one rule removes the cause --> smallfix[A small change.<br/>The test of the investigator is its test]
    report -- a larger change --> interview[The interview starts from the cause]
    report -- the code does what it should --> nb[Lem tells you what the code does and why.<br/>The task is answered]
    report -- not reproduced --> fact[Lem tells you each try<br/>and asks you for one more fact]
    report -- the answer to a question --> ans[Lem shows you the answer.<br/>The task is answered]
    fact --> inv
```

- **A bug whose cause your words do not show gets an investigation first.** The cause decides the
  change, so Lem writes no criterion before the cause is known.
- **The report replaces the scout.** A cause near a topic is never a small change.
- **An answered task has nothing to merge.** Its worktree goes. A branch with the test of the bug
  stays, and Lem tells you how to delete it.
- **You can start a task from a report**: type `/lem new` and the path of the report.

## Decisions

- **You are necessary at three points**: your yes to the criteria, a decision whose options each
  cost a person something, and the pull request. A small change needs only the pull request.
- **Lem takes the small decisions.** It logs each one with its reason, and the pull request lists
  them for you to overturn.
- **The personas answer a decision of yours first.** A clear answer of theirs is taken and logged.
- **An unclear answer comes to you as a card** that starts with one example that ends badly.
  Two experts of two model families answer the same choice, and their answers are on the card.
- **The choice waits `flow.decision_wait` minutes**, 15 by default, while the other work
  continues. Then the lead takes the shared option of the experts, or the recommended option. The
  pull request is not green for it. When you said that you are away, Lem takes the shared option
  at once.
- **A step that nobody can undo waits for your word**: a step that destroys data, writes to an
  outside system, sends something to a person, or spends money.
- **A night plan asks you nothing.** A plan that meets a decision of yours stops, and the night
  report gives you the question.

## What you can say at any time

- "full": a small change becomes a full change.
- "careful": the task gets the careful flow.
- "interview me": a complete request gets the interview.
- "drop": the task stops. A branch with commits stays.
- "land it": your word to merge a pull request that is open.

A task that ended (landed, answered or dropped) does not start again. New work on it is a new
request.

## What Lem and the jobs start

The README gives the commands that you type. These commands start without you:

- **`/lem land`**: Lem starts it when a task is ready.
- **A nap**: Lem starts one in the background when naps are on. `/lem nap` starts one by hand.
- **`/lem retro`**: a scheduled job, each morning. It reads the landed tasks, the correction queue
  and the notes of the naps, and proposes where a repeated correction goes. With nobody there, it
  records its proposals, and `/lem` lists them for you.
- **`/lem night`**: a scheduled job, each night. It writes a plan for one backlog item that needs
  no decision. An item that is one plain change gets no plan: the night report names it as ready
  to start as a small change.

The scheduled jobs are jobs in cronn. `/lem init` offers them, and adds a job only after your yes.
