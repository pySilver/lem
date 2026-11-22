// The live page: one EventSource on the workspace's stream, whose messages are Turbo stream actions
// (`refresh`: Turbo fetches the page again and morphs it in). The element is permanent, so it lives
// across the visits of one workspace and its words in the status bar are its own.
//
// iOS drops an EventSource in the background, or keeps a dead one that still says it is open: a page
// that comes back into view, or out of the back-forward cache, opens a new one, which the server
// answers with a refresh when the log changed meanwhile (`?since=` the last id seen). An id is the log's
// version, its inode and its count of lines in one text ("8812-140"), kept whole: a log that
// `lem project prune` replaced has another inode, so the page is told also when the count is the
// same. With a task open (its address), the stream watches that task's files too (`&task=`). While the stream
// is down the page refreshes itself every POLL_MS, and only after the server answered a light
// request: a refresh that finds no server would make Turbo reload the page into the browser's error.
import {Controller} from '@hotwired/stimulus';
import {ago} from './time.js';

const POLL_MS = 10000;
const REFRESH = '<turbo-stream action="refresh"></turbo-stream>';

export default class extends Controller {
  static values = {url: String, since: String};

  connect() {
    this.lastId = this.sinceValue;
    this.lastMessage = 0;
    this.down = 0;
    this.onShow = () => { if (document.visibilityState === 'visible') this.open(); };
    this.onPageShow = ev => { if (ev.persisted) this.open(); };
    // a visit to another task opens the stream again for that task's files
    this.onVisit = () => { if (this.task() !== this.watching) this.open(); };
    document.addEventListener('visibilitychange', this.onShow);
    window.addEventListener('pageshow', this.onPageShow);
    document.addEventListener('turbo:load', this.onVisit);
    document.addEventListener('turbo:frame-load', this.onVisit);
    window.addEventListener('popstate', this.onVisit);
    this.timer = setInterval(() => this.tick(), 1000);
    this.open();
  }

  disconnect() {
    document.removeEventListener('visibilitychange', this.onShow);
    window.removeEventListener('pageshow', this.onPageShow);
    document.removeEventListener('turbo:load', this.onVisit);
    document.removeEventListener('turbo:frame-load', this.onVisit);
    window.removeEventListener('popstate', this.onVisit);
    clearInterval(this.timer);
    this.close();
  }

  // the task open in the page's address, whose files the stream watches too (an artifact written with no event)
  task() {
    return /\/tasks\/([a-z0-9-]+)/.exec(location.pathname)?.[1] ?? '';
  }

  open() {
    this.close();
    this.watching = this.task();
    const source = new EventSource(`${this.urlValue}?since=${encodeURIComponent(this.lastId)}${this.watching ? `&task=${this.watching}` : ''}`);
    source.addEventListener('open', () => { if (this.source === source) { this.down = 0; this.say(); } });
    source.addEventListener('message', ev => {
      if (this.source !== source) return;
      if (ev.lastEventId) this.lastId = ev.lastEventId;
      this.lastMessage = Date.now();
      this.down = 0;
      this.say();
    });
    source.addEventListener('error', () => {
      if (this.source !== source) return;
      if (!this.down) this.down = Date.now();
      this.say();
    });
    window.Turbo.connectStreamSource(source);
    this.source = source;
    this.say();
  }

  close() {
    if (!this.source) return;
    window.Turbo.disconnectStreamSource(this.source);
    this.source.close();
    this.source = null;
  }

  async tick() {
    this.say();
    if (!this.down || Date.now() - (this.polled ?? 0) < POLL_MS) return;
    this.polled = Date.now();
    // a stream the server refused stays closed: open it again, and read the page while it is down
    if (this.source?.readyState === EventSource.CLOSED) this.open();
    try {
      const reply = await fetch('/api/server', {cache: 'no-store'});
      if (reply.ok) { window.Turbo.renderStreamMessage(REFRESH); this.answered = Date.now(); }
    } catch {
      // the server does not answer: the page stays as it is, and says so
    }
    this.say();
  }

  say() {
    const now = Date.now();
    let text, title;
    if (!this.down && this.source?.readyState === EventSource.OPEN) {
      text = this.lastMessage ? `live · last change ${ago(now - this.lastMessage)}` : 'live';
      title = 'lem serve tells this page each change of the workspace, and the page changes with it';
    } else if (!this.down) {
      text = 'connecting…';
      title = 'The page opens its stream to lem serve';
    } else {
      text = this.answered && this.answered > this.down ? `the stream is down: the page reads again every ${POLL_MS / 1000}s` : 'lem serve does not answer';
      title = `Since ${new Date(this.down).toLocaleTimeString()}; the page tries again every ${POLL_MS / 1000}s`;
    }
    this.element.classList.toggle('down', Boolean(this.down));
    if (this.element.textContent !== text) this.element.textContent = text;
    this.element.title = title;
  }
}
