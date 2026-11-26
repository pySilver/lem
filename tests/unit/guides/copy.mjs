// Run the built theme on one code block. The stand-in for the clipboard records the selection.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { runInNewContext } from 'node:vm'

const bundle = readFileSync(process.argv[2], 'utf8')
const { config, block, highlightClass, preAttributes } = JSON.parse(readFileSync(0, 'utf8'))

class Element extends EventTarget {
  attributes = new Map()
  children = []
  classList = { add () {}, remove () {}, contains: () => false }
  clientWidth = 100
  innerText = ''
  nodeType = 1
  style = {}

  constructor (tagName) {
    super()
    this.tagName = tagName.toUpperCase()
    this.nodeName = this.tagName
  }

  setAttribute (name, value) { this.attributes.set(name, value) }
  getAttribute (name) { return this.attributes.get(name) ?? null }
  hasAttribute (name) { return this.attributes.has(name) }
  removeAttribute (name) { this.attributes.delete(name) }
  getBoundingClientRect () { return { width: 100, height: 20 } }
  focus () {}
  select () { selected = this.value }
  setSelectionRange () {}

  append (...children) {
    this.children.push(...children)
    for (const child of children) child.parentElement = this
  }

  appendChild (child) { this.append(child) }

  insertBefore (child, next) {
    this.children.splice(this.children.indexOf(next), 0, child)
    child.parentElement = this
  }

  removeChild (child) { this.children.splice(this.children.indexOf(child), 1) }
  remove () { this.parentElement.removeChild(this) }

  matches (selectors) {
    return selectors.split(', ').some(selector => {
      if (selector.startsWith('[')) return this.hasAttribute(selector.slice(1, -1))
      if (selector.startsWith('.')) return this.getAttribute('class')?.split(' ').includes(selector.slice(1))
      return selector === this.tagName.toLowerCase()
    })
  }

  closest (selector) { return this.matches(selector) ? this : this.parentElement?.closest(selector) ?? null }

  querySelectorAll () { return [] }
  querySelector () { return null }
}

let selected
let clipboard
const content = new Element('article')
const highlight = new Element('div')
highlight.setAttribute('class', highlightClass)
const pre = new Element('pre')
for (const [name, value] of Object.entries(preAttributes)) pre.setAttribute(name, value)
pre.id = pre.getAttribute('id')
const code = new Element('code')
code.innerText = block
content.append(highlight)
highlight.append(pre)
pre.append(code)
content.querySelectorAll = selector => selector === 'pre:not(.mermaid) > code' ? [code] : []

const document = Object.assign(new EventTarget(), {
  documentElement: new Element('html'),
  body: new Element('body'),
  createElement: name => new Element(name),
  queryCommandSupported: command => ['copy', 'cut'].includes(command),
  execCommand (command) {
    assert.equal(command, 'copy')
    clipboard = selected
    return true
  },
  querySelector (selector) {
    if (selector === '#__config') return { textContent: config }
    if (selector === '[data-md-component=header]') return header
    if (toggles.has(selector)) return toggles.get(selector)
    if (selector === `#${pre.id} > code`) return code
    return null
  },
  querySelectorAll: selector => selector === '[data-md-component=content]' ? [content] : [],
})
const header = new Element('header')
const toggles = new Map(['drawer', 'search'].map(name => [`[data-md-toggle=${name}]`, new Element('input')]))
const location = new URL('https://pysilver.github.io/lem/')
const window = Object.assign(new EventTarget(), {
  location,
  pageYOffset: 0,
  pageXOffset: 0,
  getSelection: () => ({ removeAllRanges () {} }),
})
runInNewContext(bundle, {
  window,
  document,
  location,
  URL,
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
  navigator: { userAgent: '' },
  matchMedia: () => ({ matches: false, addListener () {} }),
  Element,
  HTMLElement: Element,
  Node: Element,
  CustomEvent: Event,
  DOMParser: class {},
  innerWidth: 1000,
  innerHeight: 800,
  scrollX: 0,
  scrollY: 0,
  ResizeObserver: class {
    observe () {}
    unobserve () {}
  },
})

document.dispatchEvent(new Event('DOMContentLoaded'))
await new Promise(resolve => setTimeout(resolve, 0))
const [nav] = pre.children
assert.equal(nav.tagName, 'NAV')
const [button] = nav.children
assert.equal(button.tagName, 'BUTTON')
assert.equal(button.getAttribute('data-md-type'), 'copy')
assert.equal(button.getAttribute('data-clipboard-target'), `#${pre.id} > code`)
const click = new Event('click')
Object.defineProperty(click, 'target', { value: button })
document.body.dispatchEvent(click)
assert.equal(clipboard, block.trimEnd())
