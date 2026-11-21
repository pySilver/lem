// A markdown document, rendered in the browser by the kit's reader (entry.js: raw HTML as text, safe
// links only, pictures only from the task's media folder) from the text the server put escaped into the
// element's <template>, then enhanced: tables scroll sideways, pictures are figures, a before and an after
// sit side by side, and mermaid blocks are charts (charts.js). The element carries a key of its text:
// a refresh whose text did not change leaves the element as it is (data-keep in app.js), with its
// drawing, and a new key renders it again. A link to a heading of the document (#words) scrolls to it.
import {Controller} from '@hotwired/stimulus';
import {slugOf} from '../entry.js';

export default class extends Controller {
  static values = {key: String, media: String, dir: String};

  connect() {
    this.render();
    this.onClick = ev => this.anchor(ev);
    this.element.addEventListener('click', this.onClick);
  }

  disconnect() {
    this.element.removeEventListener('click', this.onClick);
  }

  keyValueChanged() {
    if (this.element.isConnected) this.render();
  }

  render() {
    const source = this.element.querySelector(':scope > template');
    if (!source || !window.LemKit) return;
    let out = this.element.querySelector(':scope > .md-out');
    if (!out) { out = document.createElement('div'); out.className = 'md-out'; this.element.append(out); }
    if (out.dataset.key === this.keyValue) return;
    out.innerHTML = window.LemKit.markdown(source.content.textContent, {media: this.mediaValue, dir: this.dirValue});
    out.dataset.key = this.keyValue;
    window.LemKit.enhance(out);
  }

  anchor(ev) {
    const link = ev.target instanceof Element ? ev.target.closest('a[href^="#"]') : null;
    if (!link) return;
    const want = slugOf(decodeURIComponent(link.getAttribute('href').slice(1)));
    const heading = [...this.element.querySelectorAll('[data-h]')].find(h => h.dataset.h === want) ?? this.element.querySelector(`[id="${CSS.escape(want)}"]`);
    if (!heading) return;
    ev.preventDefault();
    heading.scrollIntoView({behavior: 'smooth', block: 'start'});
  }
}
