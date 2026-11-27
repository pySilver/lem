// Run the site's transcript script on code blocks, and print each block's turns after it: the
// class, the speaker's word and the text of each turn, or null for a block it left alone.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { runInNewContext } from 'node:vm'

class Element {
  constructor (tagName) {
    this.tagName = tagName
    this.className = ''
    this.children = []
    this.text = ''
  }

  get textContent () {
    if (!this.children.length) return this.text
    return this.children.map(child => (typeof child === 'string' ? child : child.textContent)).join('')
  }

  set textContent (text) {
    this.children = []
    this.text = text
  }

  append (...children) { this.children.push(...children) }

  replaceChildren (...children) {
    this.text = ''
    this.children = children
  }
}

const [script] = process.argv.slice(2)
const codes = JSON.parse(readFileSync(0, 'utf8')).map(text => {
  const code = new Element('code')
  code.textContent = text
  return code
})
const document = {
  createElement: tagName => new Element(tagName),
  querySelectorAll (selector) {
    assert.equal(selector, '.language-text pre > code')
    return codes
  },
}
runInNewContext(readFileSync(script, 'utf8'), { document })
process.stdout.write(JSON.stringify(codes.map(code => code.children.length
  ? code.children.map(turn => ({ className: turn.className, speaker: turn.children[0].textContent, text: turn.textContent }))
  : null)))
