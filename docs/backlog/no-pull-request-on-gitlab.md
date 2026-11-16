---
worth: yes
where: skills/lem/scripts/land.py
added: 2026-11-16
---
# no pull request on GitLab

`land.py propose` opens a pull request through the `gh` command when the remote `origin` is on
`github.com`. For every other remote it marks the branch ready, and `land.py land` then puts it
on the base branch as a fast-forward. The plan of the flow names GitLab beside GitHub
(`docs/plans/2026-11-15-three-touches.md`, step 9); it is not built, because the session that
built the step had no GitLab project to run the command against.

What it needs: the `glab` command's calls for the five things `gh` does here (list the open
request of a branch, create, edit, view its state and head, merge at one commit), each checked
in a run; a way to know the forge of a self-hosted remote, since the host name does not say it
(GitHub Enterprise has the same gap); and a row of the machine check for the command.
