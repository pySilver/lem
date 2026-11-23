// A control that copies a text (a branch's name, an artifact's path) and shows a check for a moment.
import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static values = { text: String }

  async copy (ev) {
    ev.preventDefault()
    try {
      await navigator.clipboard.writeText(this.textValue)
    } catch {
      // a page without the clipboard's permission copies through a selection
      const area = Object.assign(document.createElement('textarea'), { value: this.textValue })
      document.body.append(area)
      area.select()
      document.execCommand('copy')
      area.remove()
    }
    this.element.setAttribute('data-js-done', '')
    clearTimeout(this.timer)
    this.timer = setTimeout(() => this.element.removeAttribute('data-js-done'), 1500)
  }
}
