// Run the board's stream controller through a visit with a permanent live indicator.
import { registerHooks } from 'node:module'
import { pathToFileURL } from 'node:url'

const [, , controller, slug, workspace, rendered] = process.argv
registerHooks({
  resolve (specifier, context, nextResolve) {
    if (specifier === '@hotwired/stimulus') {
      return { url: 'data:text/javascript,export class Controller {}', shortCircuit: true }
    }
    return nextResolve(specifier, context)
  }
})

let source
globalThis.EventSource = class {
  constructor (url) { source = new URL(url, 'http://127.0.0.1') }
  addEventListener () {}
  close () {}
}
globalThis.window = { Turbo: { connectStreamSource () {}, disconnectStreamSource () {} } }
globalThis.location = { pathname: '/studio/shop/' }
const markers = new Map([
  ['', { dataset: { streamRendered: workspace } }],
  [slug, { dataset: { streamRendered: rendered } }]
])
globalThis.document = {
  getElementById () { return null },
  querySelector (selector) {
    for (const [task, marker] of markers) {
      if (selector === `[data-stream-rendered][data-stream-task="${task}"]`) return marker
    }
    return null
  }
}

const { default: Stream } = await import(pathToFileURL(controller))
const live = new Stream()
live.urlValue = '/studio/shop/stream'
live.sinceValue = workspace
live.lastId = workspace
live.say = () => {}
live.open()
globalThis.location.pathname += `tasks/${slug}`
live.open()
console.log(source.search.slice(1))
