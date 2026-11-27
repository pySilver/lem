// The first visible board takes the server's notice. Turbo keeps it in this page until the owner
// closes it or leaves the document. A notice the server could not read or keep shows the server's line.
import { Controller } from '@hotwired/stimulus'

const ADDRESS = '/api/server/update'
// The server's own failure (a record that does not read, a home folder it cannot write). The door's
// 502 while the server starts again is no answer: the page asks again at its next visit.
const FAILED = 500

export default class extends Controller {
  static targets = ['note', 'title', 'line']

  connect () { this.show() }

  async show () {
    if (this.reading || !this.noteTarget.hidden || document.visibilityState !== 'visible' ||
      document.documentElement.hasAttribute('data-turbo-preview')) return
    this.reading = true
    try {
      const available = await fetch(ADDRESS, { cache: 'no-store' })
      if (available.status === FAILED) {
        await this.failed(available)
        return
      }
      if (available.status !== 200 || document.visibilityState !== 'visible') return
      const reply = await fetch(ADDRESS, { method: 'POST', cache: 'no-store' })
      if (reply.status === FAILED) {
        await this.failed(reply)
        return
      }
      if (reply.status !== 200) return
      const { version, previous_version: previous } = await reply.json()
      this.say(`Lem was updated to ${version}`, `Replaces ${previous}.`)
    } catch {
      // A page that loses its connection can ask again at its next visit.
    } finally {
      this.reading = false
    }
  }

  async failed (reply) { this.say('Lem could not keep its update notice', await reply.text()) }

  say (title, line) {
    this.titleTarget.textContent = title
    this.lineTarget.textContent = line
    this.noteTarget.hidden = false
  }

  close () { this.noteTarget.hidden = true }
}
