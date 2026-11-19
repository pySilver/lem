---
worth: later
where: site/index.html
added: 2026-11-19
---
# The landing page shows the board before its new look

The owner asked for this item when the status boards got their new look: "Once we fix that - we
will have a followup task to update screenshorts at our landing page (you can file a backlog item
for that now)".

Section "03 · The board" of `site/index.html` shows `assets/screens/board-light.png` and
`board-dark.png`. `.github/workflows/pages.yml` copies those two files into the published folder,
and it runs only when someone starts it by hand. So the branch `feat/status-boards-steady-look`
makes the pictures again under the same names, and once it is on `main` the files are new, but
the published page keeps the old board until the workflow runs again.

What to do after that branch lands:

- `site/index.html` gives the picture `width="1440" height="1625"`, the size of the old board.
  `python3 -B tests/board-showcase.py DIR` printed `board-light.png (1440 x 2159)` for the new one
  (2026-11-19, at the commit that made the pictures). Write the new height, or the browser keeps
  the old shape's room until the picture loads.
- `.frame` in `site/style.css` shows at most 600 px of the picture. At the new board's 16 px type
  the same 600 px hold less: look at what the frame shows in light and in dark, and choose whether
  it still shows the lanes.
- The caption says "The picture shows demo data"; the README and the guides now say "The picture
  shows example tasks". Use one of the two.
- Run `tests/test-site.sh`, then start the Pages workflow by hand and look at the published page.
