// The harness's phone capture uses Chrome's DevTools pipe and a throwaway profile.
import { spawn } from 'node:child_process'
import { EventEmitter, once } from 'node:events'
import { writeFileSync } from 'node:fs'

const [, , chrome, profile, output] = process.argv
const browser = spawn(chrome, [
  '--headless=new', '--use-mock-keychain', `--user-data-dir=${profile}`,
  '--disable-background-networking', '--remote-debugging-pipe', 'about:blank',
], { stdio: ['ignore', 'ignore', 'inherit', 'pipe', 'pipe'] })
const closed = once(browser, 'close')
const [send, receive] = browser.stdio.slice(3)
const pending = new Map()
const events = new EventEmitter()
let number = 0
let buffer = ''

receive.setEncoding('utf8')
receive.on('data', chunk => {
  const messages = (buffer + chunk).split('\0')
  buffer = messages.pop()
  for (const raw of messages) {
    const reply = JSON.parse(raw)
    if (reply.method) events.emit(`${reply.sessionId}:${reply.method}`)
    const found = pending.get(reply.id)
    if (!found) continue
    pending.delete(reply.id)
    if (reply.error) found.reject(new Error(reply.error.message))
    else found.resolve(reply.result)
  }
})

function call (method, params = {}, sessionId) {
  const id = ++number
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject })
    send.write(JSON.stringify({ id, method, params, sessionId }) + '\0', error => {
      if (error) reject(error)
    })
  })
}

const alarm = AbortSignal.timeout(15000)
try {
  const capture = async () => {
    const { targetId } = await call('Target.createTarget', { url: 'about:blank' })
    const { sessionId } = await call('Target.attachToTarget', { targetId, flatten: true })
    await call('Emulation.setDeviceMetricsOverride', {
      width: 390, height: 844, deviceScaleFactor: 2, mobile: true,
    }, sessionId)
    await call('Emulation.setTouchEmulationEnabled', { enabled: true }, sessionId)
    await call('Emulation.setEmulatedMedia', {
      features: [{ name: 'prefers-color-scheme', value: 'dark' }],
    }, sessionId)
    await call('Page.enable', {}, sessionId)
    const loaded = once(events, `${sessionId}:Page.loadEventFired`)
    await call('Page.navigate', {
      url: "data:text/html,<meta name=viewport content='width=device-width'><h1>Gift note</h1>",
    }, sessionId)
    await loaded
    const { data } = await call('Page.captureScreenshot', { format: 'png' }, sessionId)
    writeFileSync(output, Buffer.from(data, 'base64'))
  }
  await Promise.race([
    capture(),
    once(alarm, 'abort').then(() => { throw new Error('Chrome did not answer the capture') }),
    closed.then(([code]) => { throw new Error(`Chrome exited during the capture (${code})`) }),
  ])
} finally {
  if (browser.exitCode === null && browser.signalCode === null) browser.kill('SIGTERM')
  await closed
}
