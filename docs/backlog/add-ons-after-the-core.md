---
worth: yes
where: skills/
added: 2026-11-18
---
# Add-ons after the core

The core of Lem is the path from a request to a merged pull request, and a helper stays in it
only when a step of that path uses it. The owner, on the skills that no step uses (`/lem release`,
`/lem last-tag`, `/lem pr-review`): "yeah, those looks like lem addons more than core
functionality", and "Release functionality may go as an addon later. What else beside `release`
we can create later? Not necessarily out of what we have already." Of the list below: "Worth
adding to backlog now" (2026-11-18).

Open before the first one is built: the form of an add-on (a second plugin in the same
marketplace, or a folder a project switches on), and how an add-on names the step of the path it
hangs on. Nothing of this is decided.

The candidates, none of them started:

- **Release.** Version, tag, notes and a changelog after merges. The skills `lem-release` and
  `lem-last-tag` with their scripts were in the core until they left it; `git log -- skills/lem-release`
  finds them.
- **Review.** A review of another person's pull request from its URL: no search of the forge,
  starts where the owner stopped, the project's lenses, a pending review that he submits. The
  owner called the shape sane (2026-11-17). `lem-pr-review` was the copied skill; same way to find it.
- **Digest.** One page a week: what Lem built and why, made from the tasks' merge reviews
  (`merge-review.md`). It
  answers his "when there are lots of tasks and plans, its easy to loose track on what we build".
  The maintaining session would build this one first.
- **Triage.** Reads new tickets and proposes which are ready to become a request. Not in the
  core by his word: "it would be a wrong tool to make a prefilter of the incoming tickets".
- **CI repair.** A red check on the base branch becomes a bug request with its log.
- **Night jobs.** Test gaps, docs that differ from the code, dependency updates, each ending as
  a pull request like any night run.
- **Adapters.** Jira, and GitLab as a forge. His ruling of 2026-11-20 makes GitHub pull requests
  the one way to land ("we can assume that we fully use Github"), so a forge adapter needs his word
  first. Codex in each role left this list with his ruling "Claude Code and agterm first, and Codex
  for reviews" (2026-11-20).
- **Pictures.** For a change of a page, the pull request shows the page before and after.
