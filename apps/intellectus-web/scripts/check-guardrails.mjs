import { readdir, readFile } from 'node:fs/promises'
import { extname, join, relative, resolve } from 'node:path'

const projectRoot = resolve(import.meta.dirname, '..')
const sourceRoot = join(projectRoot, 'src')
const runtimeExtensions = new Set(['.css', '.ts', '.tsx'])

const forbiddenPatterns = [
  { label: 'unfinished content marker', pattern: /Content migration pending/ },
  { label: 'simulated research claim', pattern: /Live research running/ },
  { label: 'legacy review label', pattern: /Ready for Human Review/ },
  { label: 'placeholder link', pattern: /href\s*=\s*["']#["']/ },
  { label: 'legacy brand name', pattern: /Intellectus AI/ },
  { label: 'promotional AI claim', pattern: /AI-powered/i },
  { label: 'direct service endpoint', pattern: /\/(?:api|webhooks?)\//i },
  { label: 'local persistence', pattern: /\b(?:localStorage|sessionStorage|indexedDB)\b/i },
  { label: 'TypeScript suppression', pattern: /@ts-ignore/ },
]

async function collectRuntimeFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const pathname = join(directory, entry.name)
    if (entry.isDirectory()) {
      files.push(...(await collectRuntimeFiles(pathname)))
    } else if (
      runtimeExtensions.has(extname(entry.name)) &&
      !entry.name.includes('.test.')
    ) {
      files.push(pathname)
    }
  }

  return files
}

const files = [...(await collectRuntimeFiles(sourceRoot)), join(projectRoot, 'index.html')]
const violations = []

const frozenStyleRequirements = [
  '--color-ink: #171c2d;',
  '--color-canvas: #fffaf7;',
  '--color-surface: #ffffff;',
  '--color-blush: #fbece9;',
  '--color-accent: #9f4f4a;',
  '--color-sage: #456653;',
  '--color-sage-soft: #e8f0ea;',
  '--color-border: #ded4cf;',
  '--color-muted: #5e5b63;',
  '--color-danger: #9b2f2f;',
  '--font-sans: "Inter Variable", Inter, ui-sans-serif, system-ui, sans-serif;',
  '--font-serif: "Newsreader Variable", Newsreader, Georgia, serif;',
  '--radius-control: 0.375rem;',
  '--radius-panel: 0.75rem;',
  '--container-content: 72rem;',
  '--container-reading: 48rem;',
  '--container-document: 58rem;',
]

const styleFile = join(sourceRoot, 'styles', 'index.css')
const styleContents = await readFile(styleFile, 'utf8')

for (const requirement of frozenStyleRequirements) {
  if (!styleContents.includes(requirement)) {
    violations.push(`src/styles/index.css: missing frozen style token (${requirement})`)
  }
}

if (/gradient\s*\(/i.test(styleContents)) {
  violations.push('src/styles/index.css: gradients are not allowed')
}

const approvedHexColors = new Set([
  '#171c2d', '#fffaf7', '#ffffff', '#fbece9', '#9f4f4a', '#456653',
  '#e8f0ea', '#ded4cf', '#5e5b63', '#9b2f2f', '#8b423f', '#8a5a24', '#7f3e3a',
])
for (const color of styleContents.match(/#[0-9a-f]{6}\b/gi) ?? []) {
  if (!approvedHexColors.has(color.toLowerCase())) {
    violations.push(`src/styles/index.css: unapproved palette color (${color})`)
  }
}

if (/min-w-\[(?!0)/.test(await readFile(join(sourceRoot, 'pages', 'ProductPages.tsx'), 'utf8'))) {
  violations.push('src/pages/ProductPages.tsx: fixed minimum width may cause horizontal scrolling')
}

for (const file of files) {
  const contents = await readFile(file, 'utf8')
  const projectPath = relative(projectRoot, file).replaceAll('\\', '/')
  if (/\bfetch\b/.test(contents) && projectPath !== 'src/repositories/n8nDiagnosticRepository.ts') {
    violations.push(`${projectPath}: network transport must remain inside the n8n infrastructure adapter`)
  }
  for (const { label, pattern } of forbiddenPatterns) {
    if (pattern.test(contents)) {
      violations.push(`${projectPath}: ${label}`)
    }
  }
  const externalUrls = contents.match(/https?:\/\/[^'"`\s]+/g) ?? []
  for (const url of externalUrls) {
    if (url !== 'https://calendar.google.com/calendar/render') {
      violations.push(`${projectPath}: unapproved direct HTTP(S) URL (${url})`)
    }
  }
}

const primaryCopyFiles = [
  join(sourceRoot, 'app', 'App.tsx'),
  join(sourceRoot, 'app', 'routeRegistry.ts'),
  join(sourceRoot, 'components', 'layout', 'AppShell.tsx'),
  join(sourceRoot, 'components', 'layout', 'Brand.tsx'),
  join(sourceRoot, 'pages', 'ProductPages.tsx'),
]

const prohibitedPrimaryCopy = [
  /Review this area/,
  /Provenance/,
  /Analytical item/,
  /Interface demonstration/,
  /Diagnostic Pack/,
  /Evidence gap/,
  /Client-use approval/,
  /\bUnknown\b/,
  /\bHypothesis\b/,
  /\bRecommendation\b/,
  /(?:UNK|HYP|REC|KPI)-\d+/,
  /Awaiting consultant decision/,
  /Exclude from review/,
  /Add as roadmap proposal/,
  /90-Day Roadmap/,
]

for (const file of primaryCopyFiles) {
  const contents = await readFile(file, 'utf8')
  for (const pattern of prohibitedPrimaryCopy) {
    if (pattern.test(contents)) {
      violations.push(`${relative(projectRoot, file)}: prohibited primary-interface copy (${pattern})`)
    }
  }
}

const routerFiles = [
  join(sourceRoot, 'app', 'App.tsx'),
  join(sourceRoot, 'app', 'routeRegistry.ts'),
]

const routeRegistryContents = await readFile(join(sourceRoot, 'app', 'routeRegistry.ts'), 'utf8')
const registeredStepCount = (routeRegistryContents.match(/\bstep:\s*[1-5],/g) ?? []).length
if (registeredStepCount !== 5) {
  violations.push(`src/app/routeRegistry.ts: expected 5 guided steps, found ${registeredStepCount}`)
}

const shellContents = await readFile(join(sourceRoot, 'components', 'layout', 'AppShell.tsx'), 'utf8')
if (/\b(?:Sidebar|Drawer|Breadcrumbs)\b/.test(shellContents)) {
  violations.push('src/components/layout/AppShell.tsx: legacy navigation shell detected')
}
const retiredPaths = [
  '/new-brief',
  '/intake',
  '/research-progress',
  '/diagnostic-overview',
  '/evidence/what-we-know',
  '/evidence/gaps',
  '/hypotheses',
  '/workshop-questions',
  '/recommended-actions',
  '/roadmap',
  '/diagnostic-pack',
]

for (const file of routerFiles) {
  const contents = await readFile(file, 'utf8')
  for (const pathname of retiredPaths) {
    if (contents.includes(pathname)) {
      violations.push(`${relative(projectRoot, file)}: retired route ${pathname}`)
    }
  }
}

if (violations.length > 0) {
  console.error('Guardrail violations found:')
  violations.forEach((violation) => console.error(`- ${violation}`))
  process.exitCode = 1
} else {
  console.log(`Guardrails passed across ${files.length} runtime files.`)
}
