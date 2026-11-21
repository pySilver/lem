// The artifacts of a task: the groups of its files the owner folded or unfolded, and how far he scrolled
// the list, kept for the task while the page lives. Picking a file brings the panel anew in its frame,
// and the list then opens as he left it; a refresh of the page keeps both by itself (a morph keeps the
// node, and the `open` of each group).
import {Controller} from '@hotwired/stimulus';

const folds = new Map();
const scrolls = new Map();

export default class extends Controller {
  static targets = ['side'];
  static values = {task: String};

  connect() {
    const mine = folds.get(this.taskValue);
    if (mine) for (const [id, open] of mine) { const group = document.getElementById(id); if (group && group.open !== open) group.open = open; }
    if (this.hasSideTarget && scrolls.has(this.taskValue)) this.sideTarget.scrollTop = scrolls.get(this.taskValue);
    this.onToggle = ev => {
      if (!(ev.target instanceof HTMLDetailsElement) || !ev.target.id) return;
      if (!folds.has(this.taskValue)) folds.set(this.taskValue, new Map());
      folds.get(this.taskValue).set(ev.target.id, ev.target.open);
    };
    this.element.addEventListener('toggle', this.onToggle, true);
  }

  disconnect() {
    this.element.removeEventListener('toggle', this.onToggle, true);
    if (this.hasSideTarget) scrolls.set(this.taskValue, this.sideTarget.scrollTop);
  }
}
