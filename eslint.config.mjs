// The maintainer's lint of Lem's JavaScript: JavaScript Standard Style through neostandard, whole,
// with no option of ours that changes a style rule. Nobody who installs the plugin runs it.
//
//     npm ci                       eslint and neostandard, at the versions of package-lock.json
//     npx eslint .                 the lint, silent when every file follows the style
//     npx eslint . --fix           what the style can fix by itself
//
// neostandard's base gives every file Node's globals and window, document and navigator. Each group
// below adds the globals of where its files run.
import { defineConfig, globalIgnores } from 'eslint/config'
import { neostandard } from 'neostandard'

// The files a browser runs as they are, as classic scripts: the palette every page of Lem loads, the
// question page's runtime, which lem-ask inlines into the page, and the board's service worker.
const PALETTE = 'skills/lem/assets/lem.js'
const ASK = 'skills/lem-ask/runtime/ask.js'
const WORKER = 'skills/lem/assets/sw.js'

export default defineConfig([
  globalIgnores([
    // The board's built files and Pele's own, which tools/board-kit writes (its README).
    'skills/lem/assets/vendor/',
    '**/node_modules/',
    '.venv/',
    '.claude/',
    '.lem/',
  ]),
  // Every JavaScript file, those of no group below too: tools/board-kit/*.mjs, the board's build,
  // and tests/board-cdp.mjs, the driver of headless Chrome, are Node's.
  ...neostandard(),
  // The board's sources: ES modules for the browser, which esbuild bundles into one classic script.
  {
    files: ['tools/board-kit/**/*.js', 'tests/unit/board/pages/browser.js'],
    extends: [neostandard({ env: ['browser'] })],
  },
  {
    files: [PALETTE, ASK],
    extends: [neostandard({ env: ['browser'] })],
    languageOptions: { sourceType: 'script' },
  },
  {
    files: [WORKER],
    extends: [neostandard({ env: ['serviceworker'] })],
    languageOptions: { sourceType: 'script' },
  },
])
