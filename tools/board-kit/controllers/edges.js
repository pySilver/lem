// A list that scrolls inside itself fades at each edge where it cuts a row: the start once it is
// scrolled, the end while more is below. The classes are data-js-* attributes, which a morph keeps.
import {Controller} from '@hotwired/stimulus';

export default class extends Controller {
  connect() {
    this.update = () => this.edges();
    this.element.addEventListener('scroll', this.update, {passive: true});
    document.addEventListener('turbo:morph', this.update);
    window.addEventListener('resize', this.update);
    this.edges();
  }

  disconnect() {
    this.element.removeEventListener('scroll', this.update);
    document.removeEventListener('turbo:morph', this.update);
    window.removeEventListener('resize', this.update);
  }

  edges() {
    const list = this.element;
    list.toggleAttribute('data-js-cut-start', list.scrollTop > 1);
    list.toggleAttribute('data-js-cut-end', list.scrollTop + list.clientHeight < list.scrollHeight - 1);
  }
}
