// What only agterm does, on a page the server drew for this Mac (its body carries the address of the
// acts, data-agterm-url-value): go to a task's session. agterm gives a page served over http no bridge,
// so the page asks the server to select the session and the server answers with what it did
// or why not, and with a notice when it did only a part. A button takes no second click while its
// act runs, so a session of another Mac is never attached twice.
import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static values = { url: String }

  async post (session) {
    const reply = await fetch(`${this.urlValue}/${encodeURIComponent(session)}`, { method: 'POST', cache: 'no-store' })
    let answer = null
    try { answer = await reply.json() } catch { /* the server said no JSON */ }
    if (!reply.ok) throw new Error(answer?.error?.why ?? answer?.said ?? `the server answered ${reply.status}`)
    return answer
  }

  async jump (ev) {
    if (!this.urlValue || !ev.params.session) return
    ev.preventDefault()
    const at = ev.currentTarget
    if (at.hasAttribute('data-js-pending')) return
    at.setAttribute('data-js-pending', '')
    at.setAttribute('aria-disabled', 'true')
    if ('disabled' in at) at.disabled = true
    try {
      const answer = await this.post(ev.params.session)
      if (answer?.notice) this.note(at, answer.notice)
    } catch (err) {
      this.note(at, `It did not switch: ${err?.message ?? err}`, true)
    } finally {
      at.removeAttribute('data-js-pending')
      at.removeAttribute('aria-disabled')
      if ('disabled' in at) at.disabled = false
    }
  }

  // why the jump failed, in a note of its own after its button
  note (at, text, bad = false) {
    const place = at.nextElementSibling?.matches('[data-js-note]') ? at.nextElementSibling : document.createElement('span')
    place.setAttribute('data-js-note', '')
    place.className = 'bl-note'
    at.after(place)
    place.textContent = text
    place.classList.toggle('bad', bad)
  }
}
