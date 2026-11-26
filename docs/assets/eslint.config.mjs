// The lint of the site's script: JavaScript Standard Style through neostandard, as the root's
// eslint.config.mjs holds Lem's other JavaScript. ESLint takes the nearest config file of each file,
// so this one holds docs/assets/, and zensical.toml leaves it off the site. lem-charts.js is a
// classic script for the browser; pele.js is a link to Pele's own bundle in
// skills/lem/assets/vendor/, which the root's config leaves out too.
import { defineConfig, globalIgnores } from 'eslint/config'
import { neostandard } from 'neostandard'

export default defineConfig([
  globalIgnores(['pele.js']),
  ...neostandard({ env: ['browser'] }),
  {
    files: ['lem-charts.js'],
    languageOptions: { sourceType: 'script' },
  },
])
