# status

A bare `/lem`, `/lem status` and `/lem status <task>`. First find out what merged and open the
board, as `SKILL.md` says under Status.

A task's own board also shows its criteria, as the top of its plan has them: each with the tests
that hold it and what the last check of those tests gave. `lem criteria
show SLUG` prints the same. The criteria are what the owner reads of a task; the rest of the plan
is the agents'. For a status of one task, say its criteria in his words before anything else.
Then, for a task on the standard track that was proposed, `show-page` the page of what was built and decided,
`page.html` in its task directory, as a companion beside the board (a second `/lem status SLUG` reloads it); when it has `built.md` and no page yet, make the page first,
as `stages/pages.md` says.

Every project of Lem has personas, and a project without them has an onboarding that is not
finished. The machine check (`lem doctor`), run in the repository, has
a `project personas` row that says how many the panel finds, from the checkout or the default
branch. Look at it with the status: with none, say so and name the step, `/lem init`, which
asks who a decision here affects and writes them without touching the settings that exist; with
one, say that a panel needs a second person who would notice other things. A `correction hook`
row is there only when a settings file also names the hook, beside the plugin: say each file and
the entry its `without_it` says to delete by hand, in one line, and ask nothing. Each message is
still judged once, so it waits for no answer.

Then say what waits for him, as one list in one order, the same at every bare `/lem`:

```bash
lem project waiting
```

While `owner` says that he is away, the list's first line says so and since when, in his clock:
"You are away since 14:05; the tasks go on without you until /lem im-back." Then it gives each
kind under its key, in this order, and you say them so, in plain names and never in
task codes, one line each, and leave out a kind that has none:

1. `choices`: each choice of a task that waits for him, as `lem decisions pending` gives it: the
   task and the choice;
2. `criteria`: each task whose acceptance criteria wait for his yes;
3. `held`: each task that waits for a step of his or one more fact, with that step;
4. `pull_requests`: each open pull request, its address (or that its branch is ready to land),
   and green or each reason it is not; a task with a `night` says "of the night";
5. `retros`: "the retro of DATE proposes N changes" for each file; a file with a `problem` is
   named with it.

When `count` is 0, say "nothing waits for you" in one line. Then, after the list, what builds and
what each other task waits on, what landed today, and what was answered today with its answer in
one line, from `lem project tasks`.

A retro's proposals are his to answer, and they wait until he says so: on his word ("open
them"), `ask-owner` with one page that holds each of them as a question of its own, each with
the three answers approve, reject and later. A proposal shows the move it would make, with the
file, the change and the case that asks for it, as the retro wrote it. For each answer: approve
makes the move as `stages/learn.md` says, reject records it as rejected there, later keeps it.
Rewrite the retro's file with the proposals answered later only, and remove it when none is left,
so that the list names what still waits.

A dropped, landed or answered task has no choice that waits. A task whose status is null has a
state nobody wrote through the script: say so. A task with a `ticket_owed` ended, and its ticket in
the tracker does not say so yet: say that too. When `night_report` is not null, say after the
list, from that file, which items became which pull request, which the night left out and why,
and which task it left held for him; the files hold no record of a status shown. The status
changes what already happened and nothing else: a merge on the forge is written down, with the
steps that follow a merge and the queue that it frees.
