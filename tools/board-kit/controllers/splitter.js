// The grip at the panel's left edge: a drag gives the panel the owner's width, which the cookie keeps
// for every page of the device; a double click gives the panel its usual width back (two columns of
// the kanban, board.css). The stylesheet keeps any width inside what the stage holds.
import {Controller} from '@hotwired/stimulus';
import {write} from './prefs.js';

export default class extends Controller {
  start(ev) {
    if (ev.button !== 0) return;
    ev.preventDefault();
    const grip = this.element;
    const stage = document.getElementById('stage');
    const panel = grip.closest('.panel');
    if (!stage || !panel) return;
    try { grip.setPointerCapture(ev.pointerId); } catch { /* the moves still reach the grip under the pointer */ }
    grip.classList.add('drag');
    const right = stage.getBoundingClientRect().right;
    const move = e => stage.style.setProperty('--pw', `${Math.round(right - e.clientX)}px`);
    const up = () => {
      grip.classList.remove('drag');
      for (const [name, fn] of [['pointermove', move], ['pointerup', up], ['pointercancel', up]]) grip.removeEventListener(name, fn);
      // the width the stylesheet let it have, so that the cookie holds what shows
      const width = Math.round(panel.getBoundingClientRect().width);
      stage.style.setProperty('--pw', `${width}px`);
      write({pw: width});
    };
    for (const [name, fn] of [['pointermove', move], ['pointerup', up], ['pointercancel', up]]) grip.addEventListener(name, fn);
  }

  reset(ev) {
    ev.preventDefault();
    document.getElementById('stage')?.style.removeProperty('--pw');
    write({pw: null});
  }
}
