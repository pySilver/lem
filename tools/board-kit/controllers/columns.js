// The kanban on a phone shows one column at a time: a strip of tabs names them, a tab scrolls the
// kanban to its column, and a swipe marks the tab of the column in view.
import {Controller} from '@hotwired/stimulus';

export default class extends Controller {
  static targets = ['board', 'tab'];

  connect() {
    this.mark = () => this.marked();
    this.boardTarget.addEventListener('scroll', this.mark, {passive: true});
    document.addEventListener('turbo:morph', this.mark);
    this.marked();
  }

  disconnect() {
    this.boardTarget.removeEventListener('scroll', this.mark);
    document.removeEventListener('turbo:morph', this.mark);
  }

  show(ev) {
    ev.preventDefault();
    const board = this.boardTarget;
    board.scrollTo({left: Number(ev.params.index) * board.clientWidth, behavior: 'smooth'});
  }

  marked() {
    const board = this.boardTarget;
    const at = board.clientWidth ? Math.round(board.scrollLeft / board.clientWidth) : 0;
    this.tabTargets.forEach((tab, i) => {
      tab.setAttribute('data-js-on', String(i === at));
      if (i === at && board.clientWidth) {
        const strip = tab.parentElement;
        if (tab.offsetLeft < strip.scrollLeft || tab.offsetLeft + tab.offsetWidth > strip.scrollLeft + strip.clientWidth) strip.scrollTo({left: tab.offsetLeft - 10, behavior: 'smooth'});
      }
    });
  }
}
