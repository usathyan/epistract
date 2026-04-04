/**
 * Render Mermaid diagrams to professional SVGs using beautiful-mermaid.
 * Usage: node scripts/render-diagrams.mjs
 */
import { renderMermaidSVG, THEMES } from 'beautiful-mermaid'
import { readFileSync, writeFileSync, readdirSync } from 'fs'
import { join, basename } from 'path'

const DIAGRAMS_DIR = 'docs/diagrams'
const THEME = THEMES['github-light']

const mmdFiles = readdirSync(DIAGRAMS_DIR)
  .filter(f => f.endsWith('.mmd'))

for (const file of mmdFiles) {
  const mmdPath = join(DIAGRAMS_DIR, file)
  const svgPath = mmdPath.replace('.mmd', '.svg')
  const source = readFileSync(mmdPath, 'utf-8')

  try {
    const svg = renderMermaidSVG(source, {
      ...THEME,
      font: 'Inter, system-ui, -apple-system, sans-serif',
      padding: 48,
      nodeSpacing: 32,
      layerSpacing: 48,
      thoroughness: 5,
    })
    writeFileSync(svgPath, svg)
    console.log(`✓ ${file} → ${basename(svgPath)}`)
  } catch (err) {
    console.error(`✗ ${file}: ${err.message}`)
  }
}

console.log(`\nRendered ${mmdFiles.length} diagrams with ${Object.keys(THEME).length > 2 ? 'enriched' : 'mono'} theme`)
