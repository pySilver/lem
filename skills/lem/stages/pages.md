# The owner's page of a task on the standard track

Step 6 of `stages/land.md`, after `propose`, on the standard track.

`propose` wrote two files into the task directory, which `pages` in its output names: `built.md`,
what the owner asked, what was built and why, and what was not built; and `decisions.md`, each
decision with who took it, what it chose over what, and why. Both open with a red block when
something of the owner's was decided without him, one item for each reason the request is not
green, and have none otherwise. A part that no record holds is left out. They are no commit's: the
owner asked for them as "a file that will load a context to my brain when I will have a time too
look at the PR" (2026-11-18), and the pull request's text is the form for a teammate.

Make one page of the two: `make-page`, with the brief `SKILL_DIR/templates/page-brief.md` and each
`{{...}}` in it filled from the table under it. The page is `page.html` in the task directory. Do
not wait for it: the landing goes on. When it is made, tell the owner in one line where it is, and
that `/lem status SLUG` opens it. Do not open it yourself. A task that runs without the owner gets
its page all the same, and the page waits for his `/lem status SLUG`.

Each later `propose` of the task writes the two files again, so the page is made again after it.
