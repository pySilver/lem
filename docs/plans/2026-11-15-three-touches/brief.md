# Three ways for coding agents to take a request to a merged change

A tool coordinates AI coding agents in one git repository for a professional developer (the
"owner"). The owner types a request in plain words. One coordinating agent gives the work to
builder agents, each in its own branch and worktree. A second agent of another model family is
available as a reader. A multi-agent review tool is available too: one "round" of it starts
several reviewing agents over a diff, each with its own lens, and takes several minutes.

The repository has a test command that the tool runs as a machine check. It may or may not have a
remote on GitHub or GitLab, CI, branch protection and other developers.

The question is which of the three flows below should be the tool's default. Each is described as
what happens to one request. The numbers come from the tool's own records of two projects; nobody
measured them a second time.

## Flow A: pair everything

1. Two agents argue the plan until they agree. A review round then reads the whole plan.
2. For each task of the plan: the two agents may discuss the approach first; a builder writes the
   code; the second agent reads the diff before the commit.
3. When all tasks are done: a review round over the whole branch, a polish pass, the whole test
   suite.
4. The owner merges.

Known: in one project the read in step 2 found something it called a must-fix on 184 of 414
tasks. It is not known how many of those were defects a user would have met and how many were
about style or structure. The owner's words on speed: "every, even trivial plan takes ages to
implement". No time was measured.

## Flow B: land, then review

1. A builder writes a short plan and the code. The machine check runs.
2. The change goes to the base branch: by the agent, or by the owner's own merge when the project
   says so.
3. A review round reads the change later, from a queue. A confirmed defect becomes a new request.
4. A request that touches a path the project listed as risky gets flow A's steps 1 and 2 instead.

Known: in one project this landed 67 branches in about 28 hours with one coordinator and about
five builders, on an integration branch that is not the main branch. After those 28 hours 43 of
48 queued reviews were still open.

## Flow C: one read before the merge, depth by risk

1. The coordinator restates the request in a few lines with its "done when" checks. It asks the
   owner only when the request is unclear.
2. A builder writes a short plan and the code in small commits, with tests. A plan of several
   tasks is a stack: the next task starts on top of the one before and does not wait for its read.
3. Machine checks: the project's test command; a check that the change did not lower the bar (a
   new lint suppression, a skipped or deleted test, a removed assertion); a size check that asks
   for a split above a few hundred changed lines.
4. One independent read before anything is merged: a fresh agent of the other model family gets
   the request, the "done when" lines, the diff and the project rules that cover the changed
   files, and not the builder's reasoning. It is asked to find what is wrong. It labels each
   finding must-fix, should or nit; only a must-fix sends the change back. After two rounds
   without a clean read, the change goes to the owner as it is, with the open findings.
5. The change ends as a pull request when the repository has a GitHub or GitLab remote, and as a
   branch marked "ready" when it has none. Its description holds the request, what changed, the
   check results, the read's verdict, every decision the agents took with a one-line reason, and
   up to three places where a human eye is worth the time.
6. A request is "risky" when the agent judges that it touches a topic the project named (money,
   data that cannot be rebuilt, private data, sign-in, the checks themselves), a path the project
   listed, or a design choice that other code will copy. The agent writes its call and one
   sentence of why, and the owner can overrule it. A risky request adds: a second opinion on the
   plan before the build, with a panel of simulated users when the choice costs a person
   something; a read after each task; and one full review round over the branch before the pull
   request.

Nothing was measured for flow C. It costs at least one more agent run per request than flow B.

## Open questions

Q1. In flow C, who merges a request that is not risky and whose read is clean: always a person,
    or the agent when the project allows it?
Q2. Should some class of change skip the read in step 4, for example a change that touches only
    documentation files? Who or what decides that a change is in the class?
Q3. Should the owner see the plan before the build of a request that is not risky, or only in
    the pull request?
Q4. Is anything missing from, or too much in, what a risky request adds?
