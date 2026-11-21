# Claude Code: the onboarding

A part of `../claude-code.md`, read by `/lem init`.

## A session's name

`agtermctl session rename "Lem init · REPO" --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`
names this session, and `agtermctl session context 'TEXT' --target ...` puts one line about the
work into the title bar. A stage that runs for a repository the session did not start in (the
onboarding) does both, with the repository's name in each.

## The onboarding's pull request

On the owner's "land" (`stages/init.md`, step 6). `ROOT` is the repository's root, `BASE` the
settings' base branch, and `OWNER/NAME` the repository on GitHub, from origin's URL; `gh` takes it
with `-R`, since the session may stand in another folder. Run each line alone:

1. `git -C ROOT ls-remote --exit-code --heads origin BASE`. Exit 2 is an origin with no such branch
   (a new repository): `git -C ROOT push origin BASE`, once, and the answer says so.
2. `git -C ROOT fetch origin BASE`; when origin's base moved since the branch was made, `git -C
   ROOT rebase origin/BASE chore/lem-onboarding`.
3. `git -C ROOT push -u origin chore/lem-onboarding`.
4. `gh pr create -R OWNER/NAME --base BASE --head chore/lem-onboarding --title "chore: set up Lem"
   --body-file FILE`, with FILE a short body in the onboarding's directory: the root, what was
   generated, the assumptions. It prints the pull request's URL.
5. `gh pr merge URL -R OWNER/NAME --squash --subject "chore: set up Lem" --delete-branch`, with
   `--rebase` in the place of `--squash --subject ...` where `branch.history` is `"keep"`. A merge
   GitHub refuses (a review its rules require, a check that runs there) is no step to go around:
   tell the owner in one line, with GitHub's message, that the pull request waits for his merge
   there.
6. `git -C ROOT switch BASE` and `git -C ROOT pull --ff-only origin BASE`: the local base is then
   origin's, which a task's worktree starts from.

From a session that started in another folder, auto mode may refuse the push as one to another
repository than the session's own ("Auto mode" in the core): give him that line, as it says.

Not run yet: these steps.
