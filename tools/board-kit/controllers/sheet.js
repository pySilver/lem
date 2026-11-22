// The step of an act that has its button (a merge's confirm step): on a phone's screen the owner reads its
// text to the end before the button comes on. The controller marks the card (data-js-sheet), and board.css
// then makes it an overlay over the panel with the body as the one part that scrolls; the controller
// gates the button only while the body scrolls by itself, which it reads from the body's style, so the
// breakpoint has one place, board.css. While text is below the body's end the button has aria-disabled,
// says "Read to the end ↓" and its form's submit is cancelled; it never writes `disabled`, which stays
// Turbo's while a request runs. The read belongs to the text it read: the key is the digest of the body
// as the server rendered it (data-sheet-key-value), and the card keeps the key it showed last and the read
// in data-js-* attributes, which a morph keeps. A morph to another key scrolls the body to its top and
// turns the button off; a body whose content grows past what was in view turns it off again.
import {Controller} from '@hotwired/stimulus';

const GATE = 'Read to the end ↓';
// pixels of the body's end that count as read: a scroll that stops a hair short of it is at the end
const SLACK = 4;

export default class extends Controller {
  static targets = ['head', 'body'];
  static values = {key: String};

  connect() {
    this.element.setAttribute('data-js-sheet', '');
    this.check = () => this.read();
    this.morphed = () => { this.renew(); this.watch(); this.read(); };
    this.guard = ev => { if (ev.target instanceof HTMLFormElement && this.gated()) ev.preventDefault(); };
    this.observer = new ResizeObserver(this.check);
    this.bodyTarget.addEventListener('scroll', this.check, {passive: true});
    // before Turbo's listeners, on the frame and on the document, which leave a cancelled submit alone
    this.element.addEventListener('submit', this.guard);
    document.addEventListener('turbo:morph', this.morphed);
    // Turbo puts the button's content back when a request ends with no new page, then says so here
    document.addEventListener('turbo:submit-end', this.check);
    this.renew();
    this.watch();
    this.read();
    // after the panel gave the focus to the task's title, which the overlay covers
    requestAnimationFrame(() => { if (this.scrolls()) this.headTarget.focus({preventScroll: true}); });
  }

  disconnect() {
    this.observer.disconnect();
    this.bodyTarget.removeEventListener('scroll', this.check);
    this.element.removeEventListener('submit', this.guard);
    document.removeEventListener('turbo:morph', this.morphed);
    document.removeEventListener('turbo:submit-end', this.check);
  }

  // a key other than the one the body showed last: a text the owner has not read, from its top
  renew() {
    const shown = this.element.getAttribute('data-js-sheet-key');
    if (shown === this.keyValue) return;
    if (shown !== null) this.bodyTarget.scrollTop = 0;
    this.element.removeAttribute('data-js-sheet-read');
    this.element.setAttribute('data-js-sheet-key', this.keyValue);
    this.height = undefined;
  }

  // the body and each part of it, which a morph may have replaced: a part that grows grows the body's content
  watch() {
    this.observer.disconnect();
    this.observer.observe(this.bodyTarget);
    for (const part of this.bodyTarget.children) this.observer.observe(part);
  }

  scrolls() {
    return /^(auto|scroll)$/.test(getComputedStyle(this.bodyTarget).overflowY);
  }

  read() {
    if (this.scrolls()) {
      const body = this.bodyTarget;
      const height = body.scrollHeight;
      if (body.scrollTop + body.clientHeight >= height - SLACK) this.element.setAttribute('data-js-sheet-read', '');
      else if (this.height !== undefined && height > this.height) this.element.removeAttribute('data-js-sheet-read');
      this.height = height;
    } else {
      this.height = undefined;
    }
    this.paint();
  }

  gated() {
    return this.scrolls() && !this.element.hasAttribute('data-js-sheet-read');
  }

  button() {
    return this.element.querySelector('.cf-foot form button[type="submit"]');
  }

  paint() {
    const button = this.button();
    if (!button) return;
    const gated = this.gated();
    if (gated) button.setAttribute('aria-disabled', 'true');
    else button.removeAttribute('aria-disabled');
    // while Turbo's request runs the button says what runs, and its label is Turbo's to put back
    const label = button.querySelector(':scope > span');
    if (!label || button.disabled) return;
    if (label.textContent !== GATE) button.setAttribute('data-js-sheet-label', label.textContent);
    if (gated) label.textContent = GATE;
    else if (label.textContent === GATE) label.textContent = button.getAttribute('data-js-sheet-label') ?? label.textContent;
  }
}
