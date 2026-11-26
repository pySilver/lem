# Real trials

Run these checks with the approved release, the owner's private `pySilver/lem-scratch`, and the
homes from [the run order](run.md). Keep every branch you send to GitHub under `trial-*`. Keep
only the PRs and evidence from this run. The owner gives access to the scratch repository and
its trial credentials before the run. A box marked **Runs alone** needs no decision during it.

## Scratch checkout

Choose a fresh lowercase `RUN` identifier. In each folder choose a `CASE` from the check. Set
`BASE=trial-$RUN-$CASE-base`. Before any push, confirm the destination under `origin` is the
private scratch repository and that the remote branch does not yet exist. Use HTTPS with the
scratch `gh` credential helper. Use the trial identity for the two local Git settings. Run:

```sh
mkdir "$T/repo" "$T/git-hooks"
"$T/step" --cwd repo setup-git -- git init -b "$BASE"
"$T/step" --cwd repo setup-origin -- git remote add origin https://github.com/pySilver/lem-scratch.git
"$T/step" --cwd repo setup-who -- git config user.name 'Lem Trial'
"$T/step" --cwd repo setup-mail -- git config user.email "$TRIAL_EMAIL"
"$T/step" --cwd repo setup-helper -- gh auth setup-git --hostname github.com
"$T/step" --cwd repo setup-visibility -- gh repo view pySilver/lem-scratch --json nameWithOwner,visibility
"$T/step" --cwd repo setup-remote -- git ls-remote --heads origin "refs/heads/$BASE"
"$T/step" --cwd repo setup-lem -- lem init --base "$BASE"
```

Install the following `T/git-hooks/pre-push` and set its mode to `700`. Run
`git -C "$T/repo" config core.hooksPath "$T/git-hooks"` through `T/step`. Install the same hook
in any teammate clone. This check covers pushes from the checkout and its task worktrees.

```sh
#!/bin/sh
set -eu
[ "$2" = https://github.com/pySilver/lem-scratch.git ] || exit 1
while read -r local_ref local_oid foreign_ref foreign_oid; do
    case "$foreign_ref" in
        refs/heads/trial-*) ;;
        *) printf 'Outside the trial refs: %s\n' "$foreign_ref" >&2; exit 1 ;;
    esac
done
```

Set `[branch]` in `.lem/settings.toml` to `base = "$BASE"` with the value expanded,
`land = "agent"`, `history = "squash"`. Set `[checks] commands = ["sh tests/words.sh"]`.
Keep the other keys from `lem init`. Set the scratch project's branch naming rule in `AGENTS.md`.
It must tell Lem to use `trial-$RUN-$CASE-SLUG` with the identifiers expanded and the task slug
in place of `SLUG`. For an agent session, name the branch in the ask or item too. Inspect its task
record and branch before it proposes. Keep `.lem/state/` and `.lem/worktrees/` ignored. Seed:

```sh
mkdir -p "$T/repo/docs" "$T/repo/tests"
printf 'recieve\n' > "$T/repo/docs/word-list.txt"
printf 'recieve\n' > "$T/repo/docs/other-list.txt"
printf '%s\n' '#!/bin/sh' 'set -eu' 'test -s docs/word-list.txt' 'test -s docs/other-list.txt' > "$T/repo/tests/words.sh"
"$T/step" --cwd repo setup-add -- git add --all
"$T/step" --cwd repo setup-commit -- git commit -m 'chore(trial): seed the scratch checkout'
"$T/step" --cwd repo setup-push -- git push --set-upstream origin "HEAD:refs/heads/$BASE"
```

Add each box's changes to this seed before its base push. Make one base per named subcase when it
needs an independent landing. A local-only box can stop after its seed commit if it uses no
worktree. For the checks that need a worktree, let `origin` have the scratch base.

For a local board, set `PORT` to a free port other than 4536 and 4537. Use `lem settings set
serve.port PORT --machine` in the trial checkout. Start the child in the background with
`"$T/step" --cwd repo board-run -- lem serve run --port "$PORT" &`. Keep the process ID from
`board-run.pid`. Poll `/api/server` at `http://127.0.0.1:$PORT` with `curl` until it answers or
record a timeout. Verify that `home`, `port` and `pid` identify this trial. Use that address and
its actual host and workspace names to open the pages. To stop, record `lem serve stop` from
that checkout and wait for the child. If `serve stop` cannot reach the verified listener, end
only the PID of the trial child with TERM and wait for it. Check that its ports are closed.

Run Chrome only with `--headless --use-mock-keychain --user-data-dir="$T/chrome"`. Use a fresh
profile for each server folder. Add those flags to the `CHROME` binary whenever a box uses it.
For example, `"$T/step" r-board-dom -- "$CHROME" --headless --use-mock-keychain
--user-data-dir="$T/chrome" --dump-dom "$URL"` records the rendered page of a scratch URL.
Use the phone's browser for the owner actions in R6. For P3 or A1, use the actual scratch agterm
GUI. Pass that scratch pane's inherited `AGTERM_*` variables explicitly through `/usr/bin/env`
after `T/enter`, in particular `AGTERM_SESSION_ID`, and the socket or CLI settings of that pane.
Check the same home, config and connection in the lead, builder and companion panes.

## Common landing commands

R3, R4, R5 and R6 use a fast-track fixture to reach the row they test. Set `SLUG` and `BRANCH`
for the case, then record these commands from `T/repo`. Here and in each box, use `T/step --cwd
repo NAME -- COMMAND …`, or use `--cwd "$WT"` where the worktree is named. `WT` is `result.worktree`
from the worktree command. `D` is `T/repo/.lem/state/tasks/$SLUG`.

```sh
lem task open "$SLUG" --ask 'Correct the word in the list as specified for the trial.' --branch "$BRANCH"
lem task read "$SLUG" --type docs --why 'One word of a list.' --track small --then fast
lem task worktree "$SLUG" --branch "$BRANCH"
lem task move "$SLUG" building --line 'Build the word-list fixture.'
```

In `D/criteria.md`, write `## Acceptance criteria`, a blank line, `Size: small, because the task
changes one line.`, a blank line, and `1. The word list says receive.`. Use each box's word for its
criterion. Run `lem criteria approve "$SLUG" --small` before the edit. In `WT`, edit the named
list, commit with `git commit --all -m 'docs(trial): correct the list'`, and append
`   - no test: the word changes no program behavior` to the criterion in `D/criteria.md`. In
`WT`, run `lem criteria record "$SLUG"` and `lem task move "$SLUG" ready --line 'The list is ready.'`.

From `T/repo`, record `lem land next "$SLUG"` before each step. Take `lem land start "$SLUG"`,
`lem land base "$SLUG"`, and `lem land checks "$SLUG"` when due. For the controlled read, run
`lem land read "$SLUG"`, then copy its `attempt` and `tip` into the following trial record.
Set `kind` to `round` if the command asks for a round. Save it at `D/trial-read.json` and run
`lem land read "$SLUG" --record "$D/trial-read.json"`. Use a fresh evidence copy for each read.

```json
{
  "kind": "read", "attempt": 1, "tip": "TIP",
  "ran": [{"name": "claude", "why": "Read the fixture diff."}],
  "left_out": [], "answered": ["claude"], "silent": [], "must_fix": 0, "should": 0,
  "nit": 0, "outside": [], "careful": false, "careful_why": "Only the scratch list changes."
}
```

Keep the diff with the record. These are fixture reads. R1, R8 and R9 use actual agent reads.
Use a notes file with `## Decisions`, `## Left open`, `## Worth a look`, `## Filed in the backlog`
and `## Not done`, each with `None.` as its text. At `propose` run `lem land propose "$SLUG"
--title 'docs(trial): correct the list' --notes "$D/trial-notes.md"`. Set `PR` to the number in its
result. Inspect `gh pr view "$PR" --repo pySilver/lem-scratch --json
number,state,headRefName,headRefOid,baseRefName,mergeable,mergeCommit,autoMergeRequest`.
Require the exact scratch base and head you assigned. For a fixture verdict, run `lem land
merge-review "$SLUG"` and record what it shows as `TIP` and `BASED`. Make `D/trial-verdict.md`
with `Verdict: merge`, a blank line, and `The fixture has the specified word and passing checks.`.
File it with `lem land merge-review "$SLUG" --file "$D/trial-verdict.md" --tip "$TIP" --base "$BASED"`.
Where a box says to finish by CLI, stop the trial board server first as in Scratch checkout.
Keep automatic serve off because the board server can merge the PR while it runs. Run
`lem land merge "$SLUG" --by merger --message 'docs(trial): correct the list'`,
`lem land merged "$SLUG"`, and `lem land clean "$SLUG"` when due. Keep `land next` and task
snapshots to show which process took each step.

## Checks

- [ ] R1 The standard track in a real session. **Owner at the Mac.**

  On the scratch base, seed a project cast with an export operator and a support reader. Use
  the project's `/lem init` cast stage if this fixture has none. Set `flow.topics` to
  `["A change to the exported text format must preserve the exact format for support."]`. In the scratch GUI pane, start the installed
  Claude Code plugin with `"$T/enter" "$CLAUDE"`. Submit `/lem Add a one-line glossary export
  and its smoke check for a support reader. Use the trial branch named in AGENTS.md.`
  During the interview, give the example input `recieve` and require output `receive` followed
  by one newline. Approve the criteria after the export operator and support reader give their
  reads. Approve the plan or give its build word when the session asks. Let the careful plan
  take a real plan talk in a companion before the build. Keep its complete closed-list exchange.
  Let the real lead and builders prepare the PR. Let the real review and merge agent read it.
  If the merge review calls the owner, give the merge approval on that PR.

  Pass when the transcript shows the distinct interview, persona reads, owner approval and plan
  talk. The task record must cite the approval, committed plan, talk and checks. The GitHub PR
  must name the planned scratch branches and the final base must contain the checked export.
  Keep the original ask, criteria before and after the persona read, plan, talk, task record,
  review, PR body and GitHub merge result. Read status with `lem task show "$SLUG"` and
  `lem criteria show "$SLUG"`. Use the slug the session returned.

- [x] R2 A breaker waits for help, park and drop. **Owner at the Mac.**

  Passed on 2026-11-26 (round 3) on the installed tag `v0.99.0`, `RUN=s26`, with two findings;
  the trial operator answered as the owner in the scratch repository (decision 27,
  `r2-owner-words.md`). Its board ran on port 65361 with a Lem home of its own
  (`T/r2/config/lem`); every task session ran through the trial's agterm stand-in. The board's
  Help with `Keep the source rows as a separate list.` reached the session word for word (decision
  2's `words`), but the session took the note as his decision and cleared the hold; on his word it
  logged decision 3 and held the task again under breaker 4 with the same document. `/lem park`
  left the wait list empty (hold `parked`), `/lem resume` brought back breaker 4 in the same
  worktree at tip `54c5957` with `handoff.md`, and `/lem drop` ended it `dropped` with no wait
  row. Findings: a session opened on the fixture before the breaker took it as a fast task and
  moved it to the interview (the sheet should trip the breaker before `lem session open`); the
  live wake did not reach the session, since the trial home had no mailbox waiter hook then.
  Evidence in `/private/tmp/lem-trial-r1/evidence/`: `r2-*`, `r2-transcripts/`,
  `r2-task-folder-final/`.

  Open a scratch task with `lem task open breaker-sample --ask 'Keep every original row after
  replacement.' --branch "$BRANCH"`. Use a `trial-*` branch and make its worktree with
  `lem task worktree breaker-sample --branch "$BRANCH"`. Set `SLUG=breaker-sample` and use
  the common fixture's task read and small approval commands. For approval set criterion 1
  to `Keep both original rows after replacement.`. Move the task to `building` with
  `lem task move breaker-sample building --line 'Start the breaker fixture.'` and write the handoff. Use `skills/lem/templates/breaker.md` from `APP` for the
  document. Use this case in all parts of the document. The input file has two rows with key
  `red`. The only available fixture reader keeps one row per key. Neither choice keeps both rows
  under the approved rule. Keep all worktree changes in a commit and put `handoff.md` and
  `breaker.md` in the task folder. Start the board and open the task session using
  `lem session open breaker-sample --why owner` from the scratch pane.

  1. Run `lem decisions breaker breaker-sample --cause criteria` in the lead's checkout.
  2. Read the board's breaker document. Choose **Help** with `Keep the source rows as a separate list.`
  3. Check the task session receives that exact note. Leave the choice open so the hold remains.
  4. In Claude Code enter `/lem park breaker-sample`. Confirm the wait leaves the board.
  5. Enter `/lem resume breaker-sample`. Confirm it returns to its prior hold and worktree.
  6. Enter `/lem drop breaker-sample`. Confirm it ends and leaves the wait list.

  Capture the breaker, the help receipt, the branch tip and `lem task show breaker-sample` and
  `lem waiting --task breaker-sample` after each action. Pass when the record preserves the
  handoff and prior hold through park/resume and the original task ends `dropped`.

- [x] R3 Two tasks conflict after one lands. **Runs alone.**

  Passed on 2026-11-26 (round 2) against `pySilver/lem-scratch`, `RUN=n26`, with `lem` from the
  `rb/trial-run` worktree's editable install at `1b570abd`, not a keg. PRs 21 and 22. The board
  (port 65331) recorded `CONFLICTING` in `forge.json` and tried `lem session wake conflict-second
  --why conflict`, which failed as meant without agterm (`r3-board-run.err`). The base step's
  refusal `conflict` left the tip at `7093da8e` and the worktree clean; PR 22 kept its number
  and took `ce9b9db3`; the board's server merged it (`via: server`). Merge commits `8c04ebde`
  and `8a1d0758`; the final base says `received`. Evidence in `/private/tmp/lem-trial-r1/evidence/`:
  `r3-*`. The trial notes said `None` with no period: the trial build read `None.` as a finding
  (`r3-first-land-11-propose`, refusal `no-bar-call`).

  Use the common fixture twice from the same base. `conflict-first` changes `recieve` to
  `receive`. `conflict-second` changes the same line to `received`. Its criterion must name
  `received`. Both tasks must be open with different `trial-*` heads before `conflict-first`
  merges. Keep the trial board stopped and finish the first task by CLI. Leave the agterm tool
  out of this folder's PATH so its wake cannot start a second landing. Start the scratch board.
  Poll for the second GitHub PR to report `CONFLICTING`. Record
  `lem waiting --task conflict-second` after the board tries to wake the task. Keep the
  board's conflict and wake evidence. Stop the trial board server and wait for it to exit. Run
  `lem land start conflict-second --conflicting` and `lem land base conflict-second`. Keep the
  conflict refusal and the clean status of the restored worktree. In its worktree, run
  `git fetch origin "$BASE"`, `git rebase "origin/$BASE"`, set `docs/word-list.txt` to `received`,
  stage that file with `git add docs/word-list.txt` and run `git -c core.editor=true rebase --continue`.
  Continue the `land next` steps. Use a fresh read of the resolution and repropose on the same PR.
  Finish the second task by CLI when its checks and review allow it.

  Pass when the board recognizes the conflict, the base step preserves the original tip on its
  refusal, and the repaired PR keeps its number and takes the new head. Confirm the two GitHub
  merges have different merge commits and the final base has `received`. Keep both PRs, the wait
  row, resolution diff, round records and merge SHAs.

- [x] R4 The merge review and approval carry across a moved base. **Owner for the approval.**

  Passed on 2026-11-26 (round 2), PRs 23 and 24; the trial operator gave the owner's word in the
  scratch repository only (decision 27, `r4-owner-word-note.txt`). Both words were refused
  `base`. Safe path: start said "the approval stands", base `carried: true`, checks on the new
  base `01fef8b1`, no new read, PR 23 took `87456f31` with `owner_merge: stands`, and the board's
  server merged it `by: owner, via: server`. Review path: the base step refused `conflict`, the
  rebase was resolved to `receive`, `land next` asked one read of the resolution after the
  checks, and no merge was due before it was proposed. Lem then carried both the merge review
  ("carries after the read of the resolution") and the owner's merge (`stands`) onto `b5017fe0`,
  as `landing.md` D says; no new merge review or approval was asked. Evidence:
  `r4safe-*`, `r4review-*`.

  On independent `r4-safe` and `r4-review` bases, take one fixture task to an open PR and file
  its merge verdict. Record its checked tree, tip, base, read count and PR number. In a teammate
  clone under `T`, check out that base. For `r4-safe`, commit `NOTES.md` with `A teammate note.`.
  For `r4-review`, replace `recieve` in `docs/word-list.txt` with `recieves` and commit it.
  In each teammate clone run `git push origin "HEAD:refs/heads/$BASE"` after confirming the
  recorded origin and hook. The owner gives the word from the old PR tip with
  `lem land merge "$SLUG" --by owner --tip "$TIP"` before any new check. Record its result.

  1. For `r4-safe`, keep the board stopped while you take `land next` through start, base, checks
     and propose. Require the checks on the new base. Verify that the prior review carries
     and the owner's approval stands. Verify the existing PR carries its new tip. Start the
     trial board and verify that the server finishes with the standing approval. Stop the
     trial board server before you start the conflict path.
  2. For `r4-review`, take the same steps through the conflict refusal. Resolve the rebase as
     in R3, this time to `receive`. Require `land next` to ask for one read of the resolution
     after the checks. Record an answered read with no findings or careful call. Repropose
     on the same PR without a later commit. Verify that the prior merge review and the owner's
     approval carry to the new tip, as specified by the "Merge read carry, conflict" and
     "Standing merge" rows in [the landing annex, part D](../landing.md).
     An unshown rebase is one Git cannot prove kept the change. Verify that merge review is
     not due. Keep the trial board server stopped and finish by CLI.

  Pass when both paths carry the merge review and approval after checks on the new base.
  The conflict path must also show the one read of the resolution. Keep both task records,
  the checks and read artifacts, GitHub tips and bases, and the approval states. Compare the
  evidence for the old and new tips.

- [x] R5 The merge and the checks recover after a stop. **Owner for the fresh retry in R5a.**

  Passed on 2026-11-26 (round 2), PRs 25, 26 and 27; the trial operator gave R5a's fresh word as
  the owner in the scratch repository (`r5a/owner-word-note.txt`). Calls forwarded to the real
  `gh`: R5a 0 before, at and after the cut, 0 after the reconcile (refusal `intent`), 1 after the
  owner's checked word, 1 after a repeat; R5b 1 at the barrier, 1 after the reconcile, 1 after
  `merged`; R5c 1 after the lost reply (exit 3, both loss markers, intent kept), 1 after the
  reconcile and `merged`. In R5b and R5c the reconcile refused `not-due` and named
  `lem land merged`, which recorded GitHub's own merge commit (`32010c1a`, `a1eadc14`). R5d: TERM
  at the barrier ended the dummy child, the log holds the barrier line, the record says
  `stopped`, `land next` said `checks`, the new run passed, nothing was pushed. Evidence:
  `r5a/` to `r5d/` and `r5*-*`.

  Prepare the common fixture on three separate scratch bases. Set `GH` to the absolute real `gh`
  and install `"$T/merge_calls" install "$GH"` in each trial folder before its GitHub steps.
  Use `gh` through the wrapper for Lem. Use the real `"$GH"` for the independent forge reads.
  Prepare each task through a pinned merge verdict. Use a separate case directory `C` under
  `T/evidence`, such as `T/evidence/r5a`. Put the PR number from the fixture's propose result in
  `C/pr`. Stop the trial board server before R5 and keep automatic serve off. Check that GitHub
  shows an open, mergeable PR with the exact `trial-*` branches, proposed head and no queued merge.

  For the first two subcases use the following background command. Set `MODE` to `before` for
  R5a or `after` for R5b. Record the first count with `"$T/merge_calls" count "$C"`.

  ```sh
  "$T/step" --cwd repo r5-cut -- /usr/bin/env TRIAL_MERGE_CASE="$C" TRIAL_MERGE_MODE="$MODE" lem land merge "$SLUG" --by merger --message 'docs(trial): correct the list' &
  recorder=$!
  ```

  Wait for `before-send` or `after-reply` in `C/calls.jsonl`, whichever the mode names. These
  barriers are after Lem wrote its intent. The latter barrier also follows a successful real
  `gh` exit. Use the barrier before its 110 second deadline, which the wrapper sets below the
  forge adapter's 120 second child timeout. Read and keep a copy of `D/task.json` at the barrier.
  Before sending TERM, check the PID in `r5-cut.pid` is the still-running trial step leader.
  Stop its group and wait for the recorder:

  ```sh
  "$PY" -I -B -c 'import os, signal, sys; os.killpg(int(sys.argv[1]), signal.SIGTERM)' "$(cat "$T/evidence/r5-cut.pid")"
  wait "$recorder"
  ```

  Keep the recorder's signal status. In each subcase record the count after the cut, after
  reconciliation and after any new call. Take both `gh pr view` and `task.json` before and
  after reconciliation. For the reconciliation itself use:

  ```sh
  "$T/step" --cwd repo r5-reconcile -- /usr/bin/env TRIAL_MERGE_CASE="$C" lem land merge "$SLUG" --by merger --message 'docs(trial): correct the list'
  ```

  1. **R5a, before the call.** The counts are 0 before and after the cut and 0 after reconcile.
     The PR stays open and reconcile refuses `intent`. Have the owner check the actual GitHub
     PR, confirm its tip and that it has no merge or queue, and give the fresh word. Copy the
     moment from the refusal into `MOMENT`. Run the command below. Require one call after the
     owner's word and one GitHub merge into the recorded base. A repeat of the original reconcile
     must add zero calls.

     ```sh
     "$T/step" --cwd repo r5-checked -- /usr/bin/env TRIAL_MERGE_CASE="$C" lem land merge "$SLUG" --by owner --tip "$TIP" --checked "$MOMENT" --message 'docs(trial): correct the list'
     ```

  2. **R5b, after the call.** The count is 1 at the barrier and remains 1 after reconcile.
     Observe GitHub's merge before reconcile. Require the refusal `not-due` to name
     `lem land merged`. Run `lem land merged "$SLUG"` and compare the recorded merge commit
     with GitHub's merge commit. The count must stay at 1.
  3. **R5c, lost reply.** Run `r5-cut` in the foreground with `TRIAL_MERGE_MODE=lost` and no
     signal. The wrapper sends the real command, then drops its successful reply and the adapter's
     immediate GraphQL read. Expect exit 3, the intent still on record and the two loss markers.
     Save the fault and the scratch `lem.log`. Observe GitHub's merge through `"$GH"`. Run the
     reconcile without the mode variable as above. Require the refusal `not-due` to name
     `lem land merged`. Run `lem land merged "$SLUG"` and compare the recorded merge commit
     with GitHub's merge commit. The count must stay at 1.

  Run `lem land merged "$SLUG"` and `lem land clean "$SLUG"` when due. If reconciliation finds
  an accepted queue instead of a merge, keep that evidence and repeat the case on a base where
  GitHub merges directly. The counts refer to invocations forwarded to real `gh`. The GitHub
  receipts establish the remote outcomes.

  **R5d, stop during the checks.** Use a fourth base. Add `sh tests/cut-check.sh` as its first
  check. In that script use the following. Its readiness and descendant PID come from the check
  itself. A successful retry leaves the `pause` file absent.

  ```sh
  #!/bin/sh
  set -eu
  if [ -f "$TMPDIR/pause" ]; then
      sleep 300 &
      child=$!
      printf '%s\n' "$child" > "$TMPDIR/check-child"
      printf '%s\n' 'trial check reached the barrier'
      wait "$child"
  fi
  ```

  Take the fixture through `land base`. Create `T/tmp/pause`. Start `"$T/step" --cwd repo
  r5-check-cut -- lem land checks "$SLUG"` in the background. Wait for `T/tmp/check-child`.
  Send TERM to the verified Lem process from `r5-check-cut.pid` with `kill -TERM "$PID"`.
  Wait for the recorder. Verify the descendant PID no longer runs, the check output contains
  the barrier line, and the record says `stopped`. `land next` must still say `checks`. Remove
  `T/tmp/pause` and run a new recorded `lem land checks "$SLUG"`. Require a passed check for the
  current tree and no push or merge from the interrupted run. Keep both runs and the process
  evidence. The 300 seconds bound the dummy child only. Use the readiness file for the stop.

- [x] R6 A phone passes through the door, answers a card and approves a merge. **Owner and phone.**

  Passed on 2026-11-26 (round 3) on the tag `v0.99.0`, `RUN=r3net`, PR 28, door
  `https://macbook-pro-slvr.tail6cced0.ts.net:65462/` (ports 65461 and 65462, home `T/r6/config/lem`).
  Direct request 403, no Funnel. The task's session ran through the agtermctl stand-in in the trial
  home. On the phone, in Safari's desktop mode (the record says device `computer`, User-Agent of a
  Mac), the owner answered card `4173D006`: `Write a dash`, note `For the export`, from `board`, via
  `door`; the waiting row closed. He approved the merge on the phone: GitHub `MERGED`, commit
  `426cee77`, merged head `6b56723d` = the approved tip; `landed` on the board and in
  `lem task show`. An earlier card he answered in the Mac overlay (from `session`) is kept for the
  overlay path. Two defects he saw: the card re-rendered while he typed, and after the merge the
  page went white and reloaded to `?note=`. Door off, server stopped, Tailscale back to the owner's
  entries. Evidence: `T/evidence/r6-*`.

  On the dedicated tailnet Mac select a free `PORT` and `DOOR` outside 4536 and 4537. Check
  `tailscale serve status --json` before the run. Reject a port with an existing target.
  Take an R6 fixture task to an open PR. Use `Verdict: call` with the reason `The owner tests
  approval on the phone.` in its pinned merge-review file. Keep `TIP`, `PR` and the checked base.
  Run the commands below from the scratch checkout:

  ```sh
  lem settings set serve.port "$PORT" --machine
  lem settings set serve.tailscale_port "$DOOR" --machine
  /usr/bin/env -u LEM_SERVE lem serve door on
  tailscale serve status --json
  ```

  Read the local `/api/server`. Compare its `home`, main port and door URL with the command.
  Open the door URL from the owner's phone over the tailnet. Use `DOOR_NAME` for the URL host.
  Record `curl -sS -D - -H "Host: $DOOR_NAME:$DOOR" "http://127.0.0.1:$DOOR/"` at the test Mac.
  This direct request has no Tailscale login. Expect 403. Confirm the status
  shows no Funnel entry for the door. Open a separate scratch agterm pane for this task with
  `lem session open "$SLUG" --why owner`. In that pane run:

  ```sh
  lem ask q 'What goes in the empty cell?' 'Keep it empty' 'Write a dash' --no-wait
  lem ask wait "$PAGEID"
  ```

  Set `PAGEID` to the open command's page id. In the phone's board, select `Write a dash` and
  add the note `For the export`. Require the answer to name the board listener and device and
  close the waiting row. On the reviewed PR's card, open the merge page and tap **Approve**.
  Wait for GitHub to report `MERGED`, then for the board and `lem task show "$SLUG"` to show
  `landed`. The merged head must be the head on the approved page. Keep the before and after
  door state, phone captures, card receipt, approval, task record and GitHub merge result.
  Unsubscribe the trial board on the phone if you subscribed. Take the door down with
  `/usr/bin/env -u LEM_SERVE lem serve door off` and stop the scratch server. Check Tailscale's
  status again and verify only the trial entry left.

- [x] R7 Two servers join. **Owner for the two tailnet hosts.**

  Passed on 2026-11-26 (round 3) on the tag `v0.99.0`: Alpha `macbook-pro-slvr` (the keg, home
  `T/r7/config/lem`, ports 65371 and door 65372, `alpha-repo` on `pySilver/lem-scratch` base
  `trial-r3net-r7-base`) and Beta `silvers-mac-mini` (Lem from the tag's archive in a venv of
  `/private/tmp/lem-trial-r7`, ports 65373 and door 65374, `beta-repo` with a local bare origin in
  that folder, since the mini has no scratch credential; `lem init` ran before the origin was added).
  Both joins reachable; each workspace list names both hosts; each relayed page shows the peer's
  `peer-card`; POST 405, `Lem-Hop` 404; with Beta stopped Alpha's peer page gives 502, its list keeps
  Beta's row `reachable: false`, its own page 200. Both doors off, both servers stopped, Tailscale
  back to the owner's entries on both hosts, the mini's folder removed. Both hosts ran Tailscale's
  CLI through `LEM_TAILSCALE=/usr/local/bin/tailscale`. Evidence: `T/evidence/r7-*`.

  On the two disposable hosts make separate trial folders. For R7 only, substitute `alpha-repo`
  and `beta-repo` for `repo` in the scratch setup. Run `lem task open peer-card --ask 'Show this
  card from the other board.'` in each checkout. Register each with `lem serve add DIRECTORY`. Use distinct main and door ports from R6 and from each other. Use the R6 commands
  to open each host's private tailnet door. Keep both local `/api/server` results. Define `ALPHA`
  and `BETA` as the tailnet host labels reported by the servers, `APORT` and `BPORT` as the
  local main ports, and `ADOOR` and `BDOOR` as the HTTPS door ports. At Alpha run
  `lem serve join "$BETA:$BDOOR"`. At Beta run `lem serve join "$ALPHA:$ADOOR"`.
  Record `lem serve peers` on both hosts, plus the following reads at Alpha:

  ```sh
  curl -fsS "http://127.0.0.1:$APORT/api/workspaces"
  curl -fsS "http://127.0.0.1:$APORT/$BETA/$BETA_WORKSPACE/"
  curl -sS -D - -o /dev/null -X POST "http://127.0.0.1:$APORT/$BETA/$BETA_WORKSPACE/"
  curl -sS -D - -o /dev/null -H 'Lem-Hop: 1' "http://127.0.0.1:$APORT/$BETA/$BETA_WORKSPACE/"
  ```

  Repeat the workspace list and peer page at Beta with Alpha's names. Pass when the workspace
  list shows both distinct hosts, each relayed page shows the peer's actual card, the write
  gets 405 and an extra hop gets 404. At Beta stop the trial server. At Alpha read the peer page
  again. Require the unreachable state without loss of Alpha's page. Keep both peer lists,
  response headers, both pages, the unreachable row, port evidence and any trial process logs.
  Run `lem serve leave "$BETA"` at Alpha and `lem serve leave "$ALPHA"` at Beta. Close both doors
  and stop both servers as in R6. If `door off` restarts Beta for cleanup, stop that child too.

- [x] R8 A night takes an item to its PR. **Runs alone after scratch setup.**

  Passed on 2026-11-26 (round 3) on the installed tag `v0.99.0`, `RUN=s26`, base
  `trial-s26-r8-base`. The operator typed only `/lem night 1` and answered nothing. The night
  opened task `word-list` in its own session (through the trial's agterm stand-in, HOME in the
  trial home) on `trial-s26-r8-word-list`; PR 30 is open and not merged: criteria approved `alone`,
  not green for that reason alone, `docs/backlog/word-list.md` removed in the PR, merge review
  `call`, `land next` says the owner merges. The night's own close was refused as the owner's
  session, as the stage says. Evidence in `/private/tmp/lem-trial-r1/evidence/`: `r8-*`,
  `r8-pr-view.out`, `r8-night-report.md`, `r8-transcripts/`, `r8-task-folder/`.

  Seed one tracked `docs/backlog/word-list.md` in the scratch base. Use this item and substitute
  the current date and the exact scratch head branch:

  ```markdown
  ---
  worth: yes
  where: docs/word-list.txt
  added: YYYY-MM-DD
  ---
  # Correct the word list

  Change `recieve` to `receive` in the word list. Use the branch `trial-RUN-r8-word-list`.
  ```

  In the scratch agterm pane at `T/repo` start the P1 Claude Code plugin. Enter `/lem night 1`.
  Use the night stage through the creation of a real task session, build, checks, review and
  proposal. A manual start of this stage creates no scheduled job. Keep the session transcript.
  Let the stage close its own session if it is a job. Close the scratch pane yourself if it is the
  orchestrator's pane. Do not answer on behalf of the owner or approve a merge. Record
  `lem path backlog`, `lem waiting`, `lem task show "$SLUG"`, and the opened GitHub PR and body.
  Keep the dated night report in `.lem/state/night/`. Pass when the one item results in one open
  PR. Require the `alone` approval, not-green reason for the criteria, the item removed in the PR,
  a merge review that calls the owner, and no PR merge. Capture the open result before cleanup.

- [x] R9 A task on a scratch copy of a real project. **Owner for the snapshot and criteria.**

  Passed on 2026-11-26 (round 3), `RUN=j26`, with the keg 0.99.0. The 34 owner-approved paths
  of mybaze `0455840a` came by `git archive`, each with the archive's hash and the commit's blob
  (`r9-export-compare.json`); the check of the commands is `r9-commands-check.txt`. The session
  took the fast track; Lem approved its one criterion alone, so no owner step was asked. PR 29
  (`trial-j26-r9-one-size-labels-match-nfc` into `trial-j26-r9-base`) was green after one read,
  and the merge agent said merge. The trial board (port 65491) merged it `via: server`, merge
  commit `eed7f01e`. A fresh clone of the merged base gave 191 passed with the agreed pytest line
  (`r9-final-test`), and the owner's task held apart from the session's tests
  (`r9-final-owner-criteria-2`). The board's `merged` wake waited unheard, because the trial home
  has no `mailbox-chat.py claude-hook`; the operator typed the line, and the session cleaned and
  closed (`r9-wake-unheard.txt`, `r9-wake-typed.txt`). Evidence in
  `/private/tmp/lem-trial-r1/evidence/`: `r9-*`.

  Ask the owner for a project commit, a reviewed export safe to put in the private scratch
  repository, and one task with a real local check. The project is the source for the task and
  snapshot. Use no checkout metadata, credentials, private local data, production environment,
  existing Lem state, or remote hooks from it. From the approved export, copy only the approved
  files into `T/repo` before its first commit. Record the approved file list, source commit and
  comparison in the trial evidence. Keep only the scratch origin. Use the project's current
  criteria, commands and cast as applicable, with explicit scratch settings and a reproducible
  local test. Check that the project commands point only to scratch resources before the run.

  In a fresh scratch agterm pane run `"$T/enter" "$CLAUDE"`, then enter `/lem` and the approved
  request with the trial branch. Let its session select a track. Complete the owner steps that
  it asks for. Record `lem task show "$SLUG"`, `lem criteria show "$SLUG"` and `lem land next
  "$SLUG"` at the handoffs. Let the approved change reach its checks, review and GitHub merge.
  Check the final base with `git log -1 "origin/$BASE"` and the agreed test in the scratch clone.
  Keep the transcript, plan if there is one, test output, reviewed diff, PR and merge commit.
  Pass when the approved criteria and project test hold in the merged scratch base and all
  forge writes point to the approved `trial-*` refs. Keep the source project's state intact.

## Cleanup

Keep a list of bases, heads, PR numbers, servers and session IDs from this trial. After the final
snapshots, close only open trial PRs from that list with `gh pr close "$PR" --repo
pySilver/lem-scratch`. Do not delete them with the close command. Keep their pre-close evidence.
Stop each board and close its scratch panes. Delete each listed trial ref that still exists with
`git push origin --delete "$REF"`. Confirm its absence with `git ls-remote --heads origin
"refs/heads/$REF"`. Do not delete branches from another run. Revoke or remove access from the
scratch login and retain the private evidence, without credentials, as required for the run.
