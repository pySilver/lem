// node tests/board-cdp.mjs SPEC.json: drive headless Chrome over the DevTools protocol, for the board's
// pictures (tests/board-showcase.py), tests/lem-serve.sh's typing into a page, the keys of tests/lem-board-keys.sh and a builder's look at a page. SPEC has a viewport (`width`,
// `height`, `scale`, `mobile` for a phone's emulation), `dark` for the color scheme, `ua` for another
// user agent, and `steps`: {goto, wait}, {wait}, {eval}, {print}, {click} (with `tap`, a finger's touch, as a
// phone gets it), {sh} (a command, its output printed), {key} (with `code`, `vk`, `text`, `modifiers`), {shot}. Chrome runs
// with a throwaway profile and the mock keychain, and the profile goes at the end. CHROME names the
// browser; by default Google Chrome's place on macOS, else the first of google-chrome and chromium.
import {spawn, execSync} from 'node:child_process';
import {mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const spec = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const MAC = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const which = name => { try { return execSync(`command -v ${name}`, {encoding: 'utf8'}).trim(); } catch { return ''; } };
const CHROME = process.env.CHROME || (existsSync(MAC) ? MAC : which('google-chrome') || which('chromium'));
if (!CHROME) throw new Error('no Chrome: set CHROME to the browser to drive');
const profile = mkdtempSync(join(tmpdir(), 'lem-cdp-'));
const chrome = spawn(CHROME, ['--headless=new', '--use-mock-keychain', `--user-data-dir=${profile}`, '--remote-debugging-port=0', '--no-first-run',
  '--hide-scrollbars', '--disable-gpu', 'about:blank'], {stdio: 'ignore', env: {...process.env, TZ: process.env.TZ ?? 'UTC'}});
const sleep = ms => new Promise(r => setTimeout(r, ms));
try {
  let port = null;
  for (let i = 0; i < 100 && !port; i++) {
    await sleep(100);
    const file = join(profile, 'DevToolsActivePort');
    if (existsSync(file)) port = readFileSync(file, 'utf8').split('\n')[0];
  }
  const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = targets.find(t => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r));
  let id = 0;
  const waiting = new Map();
  ws.addEventListener('message', ev => { const m = JSON.parse(ev.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); } });
  const send = (method, params = {}) => new Promise(r => { const n = ++id; waiting.set(n, r); ws.send(JSON.stringify({id: n, method, params})); });
  const w = spec.width ?? 1440, h = spec.height ?? 900;
  await send('Emulation.setDeviceMetricsOverride', {width: w, height: h, deviceScaleFactor: spec.scale ?? 1, mobile: Boolean(spec.mobile)});
  if (spec.mobile) await send('Emulation.setTouchEmulationEnabled', {enabled: true, maxTouchPoints: 5});
  await send('Emulation.setEmulatedMedia', {features: [{name: 'prefers-color-scheme', value: spec.dark ? 'dark' : 'light'}]});
  if (spec.ua) await send('Emulation.setUserAgentOverride', {userAgent: spec.ua});
  await send('Page.enable');
  await send('Runtime.enable');
  for (const step of spec.steps) {
    if (step.goto) { await send('Page.navigate', {url: step.goto}); await sleep(step.wait ?? 1500); }
    else if (step.sh) { console.log(execSync(step.sh, {encoding: 'utf8'}).trim().slice(0, 300)); await sleep(step.after ?? 0); }
    else if (step.wait) await sleep(step.wait);
    else if (step.eval) { const r = await send('Runtime.evaluate', {expression: step.eval, awaitPromise: true}); if (r.result?.exceptionDetails) console.log('eval error', JSON.stringify(r.result.exceptionDetails).slice(0, 400)); await sleep(step.after ?? 300); }
    else if (step.print) { const r = await send('Runtime.evaluate', {expression: step.print, awaitPromise: true, returnByValue: true}); console.log(JSON.stringify(r.result?.result?.value ?? r.result)); }
    else if (step.click) {
      const r = await send('Runtime.evaluate', {expression: `(() => { const n = document.querySelector(${JSON.stringify(step.click)}); if (!n) return null; n.scrollIntoView({block: 'center'}); const b = n.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; })()`, returnByValue: true});
      const at = r.result?.result?.value;
      if (!at) { console.log('no element', step.click); continue; }
      if (step.tap) for (const type of ['touchStart', 'touchEnd']) await send('Input.dispatchTouchEvent', {type, touchPoints: type === 'touchStart' ? [{x: at[0], y: at[1]}] : []});
      else for (const type of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', {type, x: at[0], y: at[1], button: 'left', clickCount: 1});
      await sleep(step.after ?? 800);
    }
    else if (step.key) {
      // `text` types the character as a key of a keyboard does; `modifiers` holds them down (Alt 1, Ctrl 2, Meta/Cmd 4, Shift 8)
      for (const type of ['keyDown', 'keyUp']) {
        await send('Input.dispatchKeyEvent', {type, key: step.key, code: step.code ?? step.key, windowsVirtualKeyCode: step.vk ?? 0, modifiers: step.modifiers ?? 0,
          ...(type === 'keyDown' && step.text ? {text: step.text} : {})});
      }
      await sleep(step.after ?? 600);
    }
    else if (step.shot) {
      const r = await send('Page.captureScreenshot', {format: 'png'});
      writeFileSync(step.shot, Buffer.from(r.result.data, 'base64'));
      console.log(step.shot);
    }
  }
  ws.close();
} finally {
  chrome.kill('SIGTERM');
  await sleep(300);
  rmSync(profile, {recursive: true, force: true});
}
