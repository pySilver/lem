// The board's keys, by the physical key (KeyboardEvent.code), so they work in every keyboard layout:
// an element with data-hotkey="KeyT" is clicked on T (an input is focused instead), and Escape closes
// an open menu of the page first. No key acts while the focus is in a field or with a modifier.
import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  key (ev) {
    if (ev.metaKey || ev.ctrlKey || ev.altKey || ev.defaultPrevented) return
    if (ev.key === 'Escape') {
      const menu = document.querySelector('details[data-menu][open]')
      if (menu) { ev.preventDefault(); menu.open = false; return }
    }
    if (ev.target instanceof Element && ev.target.closest('input, textarea, select, [contenteditable]')) return
    const code = ev.key === 'Escape' ? 'Escape' : ev.code
    const target = [...document.querySelectorAll(`[data-hotkey~="${code}"]`)].find(n => n.getClientRects().length)
    if (!target) return
    ev.preventDefault()
    if (target.matches('input, textarea')) { target.focus(); target.select?.() } else target.click()
  }
}
