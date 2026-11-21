---
worth: later
where: site/index.html
added: 2026-11-19
---
# The landing page shows the board before its new look

The owner asked for this item when the status boards got their new look: "Once we fix that - we
will have a followup task to update screenshorts at our landing page (you can file a backlog item
for that now)".

`site/index.html` shows `assets/screens/board-light.png` and `board-dark.png`, with the phone's and
the task's pictures. `.github/workflows/pages.yml` copies the six files into the published folder,
and it runs only when someone starts it by hand. 65df09a made the pictures again under the same
names and gave the page their size (`width="1440" height="900"`, for pictures of 2880 x 1800), and
`.frame` in `site/style.css` no longer cuts a picture at 600 px. The workflow last ran on
2026-11-19 at 12:19Z (`gh run list --workflow Pages`, read 2026-11-21), so the published page keeps
the old board until it runs again.

What is left:

- The captions differ: `site/index.html` (both), `README.md` (the phone) and `docs/board.md` say
  "The picture shows demo data"; `README.md` (the board) and `docs/when-lem-needs-you.md` say "The
  picture shows example tasks". Use one of the two.
- Run `tests/test-site.sh`, then start the Pages workflow by hand and look at the published page.
