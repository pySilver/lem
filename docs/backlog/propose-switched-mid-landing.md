---
worth: yes
where: skills/lem/scripts/land.py
added: 2026-11-16
---
# a pull request that stays after branch.propose becomes merge

A task on a GitHub remote is proposed as a pull request, and `landing.json` keeps its `pr`. Then
the project sets `branch.propose = "merge"`. Nothing drops the `pr`: `start` keeps it when a
`ready` task takes the landing line again, and `propose` with no forge only adds `proposed`,
`title` and `not_green` beside it. Its output still names the old pull request, while the state
says that the branch is ready to land.

`land.py land` keys on `kept.get("pr")` and not on the setting. It views the pull request with
`gh`, and when the head there is the proposed tip it merges it with `gh pr merge`: the project
that wants no pull requests lands this one through the forge. When the branch has a new tip, the
step refuses with "the pull request's head is not the tip that was proposed" and names `propose`
again, which under `merge` never pushes the branch, so the refusal comes back on every run.
`land.py merged` refuses every task while `merge` is set, also this one, and names `land`; when
the owner merged the pull request on the forge, `land` then finishes the task as a forge merge,
the path the refusal said does not exist.

What it needs: a choice of what happens to the open pull request when the setting changes under
it, close it and land the branch on the remote's base branch, or land it as the pull request it
is. That choice is the owner's. Then the one place that decides it, read by `propose`, `land` and
`merged` alike, and a test that switches the setting between a proposal and the landing.
