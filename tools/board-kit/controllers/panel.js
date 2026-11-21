// The panel of a task: it marks the task's card and its rows of "Waits for you" while it is open, so
// that the view says which task the panel shows also after the panel changed in its frame (the server
// renders the same marks at each refresh); it brings the tab shown into view where the tabs scroll
// sideways (a phone); it opens the row a link named (data-row, a decision a reason of not green names)
// and brings it into view; and it expands to the stage's whole width or docks at the right, which the
// cookie keeps for the next page. It takes the focus when a link outside it opened it (to its title),
// keeps it on the tabs when a tab changed it, and gives it back to the task's card when it closes.
import {Controller} from '@hotwired/stimulus';
import {write} from './prefs.js';

function select(slug) {
  for (const node of document.querySelectorAll('.tc[data-task], .wi[data-task]')) {
    const on = node.dataset.task === slug;
    node.classList.toggle('sel', on);
    const link = node.matches('.tc') ? node.querySelector('.tc-link') : node;
    if (on) link?.setAttribute('aria-current', 'page'); else link?.removeAttribute('aria-current');
  }
}

let wanted = null;
// the link or the button that changed the panel last: where the focus goes when the new panel comes
let trigger = null;
document.addEventListener('click', ev => {
  const link = ev.target instanceof Element ? ev.target.closest('a[data-row]') : null;
  if (link) wanted = link.dataset.row;
  trigger = ev.target instanceof Element ? ev.target.closest('a, button') : null;
}, true);

export default class extends Controller {
  connect() {
    select(this.element.dataset.task);
    this.focus();
    const tab = this.element.querySelector('.ptab[aria-current]');
    const strip = tab?.parentElement;
    if (tab && strip && (tab.offsetLeft < strip.scrollLeft || tab.offsetLeft + tab.offsetWidth > strip.scrollLeft + strip.clientWidth)) strip.scrollLeft = tab.offsetLeft - 12;
    // the row a link named before the panel came (a frame's visit keeps no #anchor), opened and in view
    const named = wanted ? this.element.querySelector(`[id="${CSS.escape(wanted)}"]`) : null;
    wanted = null;
    if (named) {
      if (named instanceof HTMLDetailsElement) named.open = true;
      requestAnimationFrame(() => named.scrollIntoView({block: 'start', behavior: 'smooth'}));
    }
  }

  disconnect() {
    // a panel that gave way to another task's is followed by its connect; one that closed leaves none
    const slug = this.element.dataset.task;
    const closed = trigger?.matches('.p-close, .p-back');
    queueMicrotask(() => {
      if (document.querySelector('#task > .panel')) return;
      select(null);
      // closed by its control or by Escape: the focus goes back to the task's card, or its row of what waits
      if (closed) {
        trigger = null;
        (document.querySelector(`#card-${CSS.escape(slug)} .tc-link`) ?? document.querySelector(`.wi[data-task="${CSS.escape(slug)}"]`))?.focus({preventScroll: true});
      }
    });
  }

  focus() {
    const from = trigger;
    trigger = null;
    if (!from || from.isConnected && this.element.contains(from)) return;
    // a tab of the old panel: the same tab of the new one; any other way in: the panel's title
    const target = from.matches('.ptab') ? this.element.querySelector('.ptab[aria-current]') : from.closest('#task') ? null : this.element.querySelector('.p-title');
    target?.focus({preventScroll: true});
  }

  expand(ev) {
    ev.preventDefault();
    const stage = document.getElementById('stage');
    const full = !stage.classList.contains('full');
    stage.classList.toggle('full', full);
    write({full});
  }
}
