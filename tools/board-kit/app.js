// The one script of the served board (lem serve): Turbo, which visits the board's pages and morphs
// a page into its new version when the server says the workspace changed, the board's Stimulus
// controllers, each with one job, the markdown reader of entry.js, and what refresh.js sets right in a
// page refresh. esbuild bundles it into one classic script, vendor/board-app.js.
import './entry.js'
import * as Turbo from '@hotwired/turbo'
import './refresh.js'
import { Application } from '@hotwired/stimulus'
import { CONTROLLERS } from './controllers/index.js'

// An attribute named data-js-* is the browser's own state (an open drawer, an item the filter hides,
// the backlog's cursor), which the server never renders: a morph keeps it. So does the `open` of a
// <details>, which the owner opened or closed.
document.addEventListener('turbo:before-morph-attribute', ev => {
  const { attributeName } = ev.detail
  if (attributeName.startsWith('data-js-') || (attributeName === 'open' && ev.target.localName === 'details') ||
    (ev.target.localName === 'turbo-frame' && FRAME_OWN.has(attributeName))) ev.preventDefault()
})
document.addEventListener('turbo:before-morph-element', ev => {
  // An element the browser drew from the server's text (a markdown artifact, data-keep: its file's
  // path, time and size) stays as it is while its key is the same: the server's version holds the text,
  // and the page's holds what it rendered. So does the step of a session's card (its page id), whose
  // frame holds the owner's choice and words while the card waits. A card that no longer waits comes
  // with no key, so on every board, the one that took the answer too, the frame gives way to the
  // server's line of what was taken.
  const next = ev.detail?.newElement
  // The writable box keeps the owner's words until the matching form leaves the page.
  if (ev.target.matches('input[type="text"][id], textarea[id]') && ev.target.id === next?.id &&
      ev.target.value !== ev.target.defaultValue) ev.preventDefault()
  const keep = ev.target.dataset?.keep
  const coming = next?.dataset?.keep
  if (keep && coming === keep) ev.preventDefault()
})
// The attributes Turbo puts on the task's frame after it navigated (src, complete, busy) are its own:
// the server renders the frame without them, and a morph that took them away would make it load again.
const FRAME_OWN = new Set(['src', 'complete', 'busy', 'aria-busy'])

// A menu of the page (a <details data-menu>, the switcher of the workspaces) closes at a click
// anywhere else, as a menu does; Escape closes it too (the hotkeys controller).
document.addEventListener('click', ev => {
  for (const menu of document.querySelectorAll('details[data-menu][open]')) if (!menu.contains(ev.target)) menu.open = false
})

window.Turbo = Turbo
const app = Application.start()
for (const [name, controller] of Object.entries(CONTROLLERS)) app.register(name, controller)
