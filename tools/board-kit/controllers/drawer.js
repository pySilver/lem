// The sidebar as a drawer on a phone: open and close it, close it on Escape and when a visit starts.
// Its state is the attribute data-js-drawer on the shell, which a morph keeps.
import {Controller} from '@hotwired/stimulus';

export default class extends Controller {
  connect() {
    this.onVisit = () => this.close();
    document.addEventListener('turbo:visit', this.onVisit);
  }

  disconnect() {
    document.removeEventListener('turbo:visit', this.onVisit);
  }

  open(ev) {
    ev?.preventDefault();
    this.element.setAttribute('data-js-drawer', '');
  }

  close(ev) {
    ev?.preventDefault();
    this.element.removeAttribute('data-js-drawer');
  }

  escape(ev) {
    if (ev.key === 'Escape' && this.element.hasAttribute('data-js-drawer')) {
      ev.preventDefault();
      ev.stopImmediatePropagation();
      this.close();
    }
  }
}
