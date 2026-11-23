---
worth: later
where: skills/lem/scripts/land.py:cmd_base
added: 2026-11-23
---
# One rebase of base carries the review over a change from which git left a commit out

A task's branch holds two commits on base `B0`: `feature`, which changes `feature.txt` from `old` to `new`, and `label`, which changes `label.txt` from `old` to `new`. A review answers on that change. The base then cherry-picks `feature` and reverts it in the next commit, so `feature.txt` on the base is `old` again. `lem land base SLUG` rebases the branch onto that base with no conflict: git skips `feature`, since a commit of the base carries the same patch, and the tip has one commit, which changes `label.txt` alone; `feature.txt` stays `old`. `cmd_base` decides whether the review carries before the rebase, from the change as it was, so the review carries, and the owner's standing merge or the merge agent's then merges a change that lacks the feature the review read. A probe ran it in a throwaway repository with git 2.55.0 on 2026-11-23: `commits_after_one_rebase` 1, `files_after_one_rebase` `["label.txt"]`, `feature_on_tip` `old`.

The fix that decision 6 of task owner-merge-survives-a-red-base weighed, a check of the change after the rebase, ends the merge whenever the base changed any line of a file of the change, so it is no cheap fix. The case is on the base commit too; that task's plan names it under "Seen outside the change".
