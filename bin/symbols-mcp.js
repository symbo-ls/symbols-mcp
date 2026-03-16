#!/usr/bin/env node
'use strict'
const fs = require('fs')
const path = require('path')
const readline = require('readline')
const https = require('https')
const http = require('http')

const SKILLS_DIR = path.join(__dirname, '..', 'symbols_mcp', 'skills')
const API_BASE = process.env.SYMBOLS_API_URL || 'https://api.symbols.app'

// ---------------------------------------------------------------------------
// Helpers — skills
// ---------------------------------------------------------------------------

function readSkill(filename) {
  const p = path.join(SKILLS_DIR, filename)
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : `Skill '${filename}' not found`
}

function loadAgentInstructions() {
  const ai = path.join(SKILLS_DIR, 'AGENT_INSTRUCTIONS.md')
  return fs.existsSync(ai) ? fs.readFileSync(ai, 'utf8') : readSkill('CLAUDE.md')
}

function searchDocs(query, maxResults = 3) {
  const keywords = query.toLowerCase().split(/\s+/).filter(w => w.length > 2)
  if (!keywords.length) keywords.push(query.toLowerCase())

  const results = []
  for (const fname of fs.readdirSync(SKILLS_DIR)) {
    if (!fname.endsWith('.md')) continue
    const content = fs.readFileSync(path.join(SKILLS_DIR, fname), 'utf8')
    if (!keywords.some(kw => content.toLowerCase().includes(kw))) continue
    const lines = content.split('\n')
    for (let i = 0; i < lines.length; i++) {
      if (keywords.some(kw => lines[i].toLowerCase().includes(kw))) {
        results.push({ file: fname, snippet: lines.slice(Math.max(0, i - 2), Math.min(lines.length, i + 20)).join('\n') })
        break
      }
    }
    if (results.length >= maxResults) break
  }
  return results.length ? JSON.stringify(results, null, 2) : `No results found for '${query}'`
}

// ---------------------------------------------------------------------------
// Helpers — API
// ---------------------------------------------------------------------------

const AUTH_HELP = `To authenticate, provide one of:
- **token**: JWT from \`smbls login\` (stored in ~/.smblsrc) or env var SYMBOLS_TOKEN
- **api_key**: API key (sk_live_...) from your project's integration settings

To get a token:
1. Run \`smbls login\` in your terminal, or
2. Use the \`login\` tool with your email and password`

function apiRequest(method, urlPath, { token, apiKey, body } = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(API_BASE + urlPath)
    const isHttps = url.protocol === 'https:'
    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method,
      headers: { 'Content-Type': 'application/json' }
    }
    if (apiKey) options.headers['Authorization'] = `ApiKey ${apiKey}`
    else if (token) options.headers['Authorization'] = `Bearer ${token}`

    const payload = body ? JSON.stringify(body) : null
    if (payload) options.headers['Content-Length'] = Buffer.byteLength(payload)

    const req = (isHttps ? https : http).request(options, res => {
      let data = ''
      res.on('data', chunk => { data += chunk })
      res.on('end', () => {
        try { resolve(JSON.parse(data)) }
        catch { resolve({ success: false, error: `HTTP ${res.statusCode}`, message: data }) }
      })
    })
    req.on('error', err => reject(err))
    req.setTimeout(30000, () => { req.destroy(); reject(new Error('Request timeout')) })
    if (payload) req.write(payload)
    req.end()
  })
}

function requireAuth(token, apiKey) {
  if (!token && !apiKey) return `Authentication required.\n\n${AUTH_HELP}`
  return null
}

async function resolveProjectId(project, token, apiKey) {
  if (!project) return { id: '', error: 'Project identifier is required.' }
  const isKey = project.startsWith('pr_') || !/^[0-9a-f]+$/.test(project)
  if (isKey) {
    const result = await apiRequest('GET', `/core/projects/key/${project}`, { token, apiKey })
    if (result.success) return { id: result.data?._id || '', error: null }
    return { id: '', error: `Project '${project}' not found: ${result.error || 'unknown error'}` }
  }
  return { id: project, error: null }
}

// ---------------------------------------------------------------------------
// Helpers — JS-to-JSON conversion (mirrors frank pipeline)
// ---------------------------------------------------------------------------

const DATA_KEYS = ['components', 'pages', 'snippets', 'functions', 'methods',
  'designSystem', 'state', 'dependencies', 'files', 'config']
const CODE_SECTIONS = new Set(['components', 'pages', 'functions', 'methods', 'snippets'])

function findObjectEnd(code, start) {
  if (start >= code.length) return -1
  let i = start
  while (i < code.length && ' \t\n\r'.includes(code[i])) i++
  if (i >= code.length || !'{['.includes(code[i])) return -1
  const opener = code[i]
  const closer = opener === '{' ? '}' : ']'
  let depth = 1
  i++
  let inString = null, inTemplate = false, escaped = false
  while (i < code.length && depth > 0) {
    const ch = code[i]
    if (escaped) { escaped = false; i++; continue }
    if (ch === '\\') { escaped = true; i++; continue }
    if (inString) { if (ch === inString) inString = null; i++; continue }
    if (inTemplate) { if (ch === '`') inTemplate = false; i++; continue }
    if (ch === "'" || ch === '"') inString = ch
    else if (ch === '`') inTemplate = true
    else if (ch === opener) depth++
    else if (ch === closer) depth--
    i++
  }
  return depth === 0 ? i : -1
}

function parseJsToJson(sourceCode) {
  const result = {}
  const code = sourceCode.replace(/^\s*import\s+.*$/gm, '')
  const stripped = code.trim()
  if (stripped.startsWith('{')) {
    try { return JSON.parse(stripped) } catch {}
  }
  const exportRe = /export\s+const\s+(\w+)\s*=\s*/g
  let m
  const matches = []
  while ((m = exportRe.exec(code)) !== null) matches.push(m)
  for (const match of matches) {
    const name = match[1]
    const start = match.index + match[0].length
    const end = findObjectEnd(code, start)
    if (end === -1) continue
    result[name] = code.slice(start, end).trim()
  }
  if (!matches.length) {
    const defMatch = /export\s+default\s+/.exec(code)
    if (defMatch) {
      const start = defMatch.index + defMatch[0].length
      const end = findObjectEnd(code, start)
      if (end !== -1) result['__default__'] = code.slice(start, end).trim()
    }
  }
  return result
}

function jsObjToJson(rawJs) {
  let s = rawJs.trim()
  // Stringify function values
  s = stringifyFunctionsInJs(s)
  // Normalize quotes
  s = normalizeQuotes(s)
  // Quote unquoted keys
  s = s.replace(/(?<=[\{,\n])\s*([a-zA-Z_$][\w$]*)\s*:/g, ' "$1":')
  s = s.replace(/(?<=[\{,\n])\s*(@[\w$]+)\s*:/g, ' "$1":')
  // Remove trailing commas
  s = s.replace(/,\s*([}\]])/g, '$1')
  try { return JSON.parse(s) } catch { return s }
}

function stringifyFunctionsInJs(code) {
  const result = []
  let i = 0
  while (i < code.length) {
    const rest = code.slice(i)
    const arrowMatch = rest.match(/^(\([^)]*\)\s*=>|\w+\s*=>)\s*/)
    const funcMatch = rest.match(/^function\s*\w*\s*\(/)
    if (arrowMatch && isValuePosition(code, i)) {
      const fnEnd = findFunctionEnd(code, i, true)
      if (fnEnd > i) {
        result.push(JSON.stringify(code.slice(i, fnEnd).trim()))
        i = fnEnd; continue
      }
    }
    if (funcMatch && isValuePosition(code, i)) {
      const fnEnd = findFunctionEnd(code, i, false)
      if (fnEnd > i) {
        result.push(JSON.stringify(code.slice(i, fnEnd).trim()))
        i = fnEnd; continue
      }
    }
    result.push(code[i]); i++
  }
  return result.join('')
}

function isValuePosition(code, pos) {
  let j = pos - 1
  while (j >= 0 && ' \t\n\r'.includes(code[j])) j--
  return j >= 0 && ':=,['.includes(code[j])
}

function findFunctionEnd(code, start, isArrow) {
  let i = start
  if (isArrow) {
    const arrowPos = code.indexOf('=>', i)
    if (arrowPos === -1) return -1
    i = arrowPos + 2
    while (i < code.length && ' \t\n\r'.includes(code[i])) i++
    if (i < code.length && code[i] === '{') return findObjectEnd(code, i)
    let depth = 0
    while (i < code.length) {
      const ch = code[i]
      if ('({['.includes(ch)) depth++
      else if (')}]'.includes(ch)) { if (depth === 0) return i; depth-- }
      else if (ch === ',' && depth === 0) return i
      i++
    }
    return i
  } else {
    const brace = code.indexOf('{', i)
    if (brace === -1) return -1
    return findObjectEnd(code, brace)
  }
}

function normalizeQuotes(s) {
  const result = []
  let i = 0
  while (i < s.length) {
    if (s[i] === "'") {
      let j = i + 1
      while (j < s.length) {
        if (s[j] === '\\' && j + 1 < s.length) { j += 2; continue }
        if (s[j] === "'") break
        j++
      }
      const inner = s.slice(i + 1, j).replace(/"/g, '\\"')
      result.push(`"${inner}"`); i = j + 1
    } else if (s[i] === '"') {
      let j = i + 1
      while (j < s.length) {
        if (s[j] === '\\' && j + 1 < s.length) { j += 2; continue }
        if (s[j] === '"') break
        j++
      }
      result.push(s.slice(i, j + 1)); i = j + 1
    } else {
      result.push(s[i]); i++
    }
  }
  return result.join('')
}

function encodeSchemaCode(codeStr) {
  return codeStr.replace(/\n/g, '/////n').replace(/`/g, '/////tilde')
}

function buildSchemaItem(section, key, value) {
  const codeStr = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  const item = {
    title: key, key, type: section,
    code: encodeSchemaCode(`export default ${codeStr}`)
  }
  if (section === 'components' || section === 'pages') {
    Object.assign(item, { settings: { gridOptions: {} }, props: {}, interactivity: [], dataTypes: [], error: null })
  }
  return item
}

function buildChangesAndSchema(data) {
  const changes = [], granular = [], orders = []
  for (const [sectionKey, sectionData] of Object.entries(data)) {
    if (!DATA_KEYS.includes(sectionKey)) continue
    if (typeof sectionData !== 'object' || sectionData === null || Array.isArray(sectionData)) {
      changes.push(['update', [sectionKey], sectionData])
      granular.push(['update', [sectionKey], sectionData])
      continue
    }
    const sectionItemKeys = []
    for (const [itemKey, itemValue] of Object.entries(sectionData)) {
      const itemPath = [sectionKey, itemKey]
      changes.push(['update', itemPath, itemValue])
      sectionItemKeys.push(itemKey)
      if (typeof itemValue === 'object' && itemValue !== null && !Array.isArray(itemValue)) {
        const itemKeys = []
        for (const [propKey, propValue] of Object.entries(itemValue)) {
          granular.push(['update', [...itemPath, propKey], propValue])
          itemKeys.push(propKey)
        }
        if (itemKeys.length) orders.push({ path: itemPath, keys: itemKeys })
      } else {
        granular.push(['update', itemPath, itemValue])
      }
      if (CODE_SECTIONS.has(sectionKey)) {
        const schemaItem = buildSchemaItem(sectionKey, itemKey, itemValue)
        const schemaPath = ['schema', sectionKey, itemKey]
        changes.push(['update', schemaPath, schemaItem])
        granular.push(['delete', [...schemaPath, 'code']])
        for (const [sk, sv] of Object.entries(schemaItem)) {
          granular.push(['update', [...schemaPath, sk], sv])
        }
      }
    }
    if (sectionItemKeys.length) orders.push({ path: [sectionKey], keys: sectionItemKeys })
  }
  return { changes, granular, orders }
}

// ---------------------------------------------------------------------------
// Audit helpers (deterministic rule checking — mirrors server.py)
// ---------------------------------------------------------------------------

const V2_PATTERNS = [
  [/\bextend\s*:/g, "v2 syntax: use 'extends' (plural) instead of 'extend'"],
  [/\bchildExtend\s*:/g, "v2 syntax: use 'childExtends' (plural) instead of 'childExtend'"],
  [/\bon\s*:\s*\{/g, "v2 syntax: flatten event handlers with onX prefix (e.g. onClick) instead of on: {} wrapper"],
  [/\bprops\s*:\s*\{(?!\s*\})/g, "v2 syntax: flatten props directly on the component instead of props: {} wrapper"],
]

const RULE_CHECKS = [
  [/\bimport\s+.*\bfrom\s+['"]\.\//, "FORBIDDEN: No imports between project files — reference components by PascalCase key name"],
  [/\bexport\s+default\s+\{/, "Components should use named exports (export const Name = {}), not default exports"],
  [/\bfunction\s+\w+\s*\(.*\)\s*\{[\s\S]*?return\s*\{/, "Components must be plain objects, not functions that return objects"],
  [/\bextends\s*:\s*(?!['"])\w+/, "FORBIDDEN: extends must be a quoted string name (extends: 'Name'), not a variable reference — register in components/ and use string lookup (Rule 10)"],
  [/extends\s*:\s*['"]Flex['"]/, "Replace extends: 'Flex' with flow: 'x' or flow: 'y' — do NOT just remove it, the element needs flow to stay flex (Rule 26)"],
  [/extends\s*:\s*['"]Box['"]/, "Remove extends: 'Box' — every element is already a Box (Rule 26)"],
  [/extends\s*:\s*['"]Text['"]/, "Remove extends: 'Text' — any element with text: is already Text (Rule 26)"],
  [/\bchildExtends\s*:\s*\{/, "FORBIDDEN: childExtends must be a quoted string name, not an inline object — register as a named component (Rule 10)"],
  [/(?:padding|margin|gap|width|height|fontSize|borderRadius|minWidth|maxWidth|minHeight|maxHeight|top|left|right|bottom|letterSpacing|lineHeight|borderWidth|outlineWidth)\s*:\s*['"]?\d+(?:\.\d+)?px/, "FORBIDDEN: No raw px values — use design system tokens (A, B, C, etc.) instead of hardcoded pixels (Rule 28)"],
  [/(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['"]#[0-9a-fA-F]/, "Use design system color tokens (primary, secondary, white, gray.5) instead of hardcoded hex colors (Rule 27)"],
  [/(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['"]rgb/, "Use design system color tokens instead of hardcoded rgb/rgba values (Rule 27)"],
  [/(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['"]hsl/, "Use design system color tokens instead of hardcoded hsl/hsla values (Rule 27)"],
  [/<svg[\s>]/, "FORBIDDEN: Use the Icon component for SVG icons — store SVGs in designSystem/icons, never inline (Rule 29)"],
  [/tag\s*:\s*['"]svg['"]/, "FORBIDDEN: Never use tag: 'svg' — store SVGs in designSystem/icons and use Icon component (Rule 29)"],
  [/tag\s*:\s*['"]path['"]/, "FORBIDDEN: Never use tag: 'path' — store SVG paths in designSystem/icons and use Icon component (Rule 29)"],
  [/extends\s*:\s*['"]Svg['"]/, "Use Icon component for icons, not Svg — Svg is only for decorative/structural SVGs (Rule 29)"],
  [/\biconName\s*:/, "FORBIDDEN: Use icon: not iconName: — the prop is icon: 'name' matching a key in designSystem/icons (Rule 29)"],
  [/document\.createElement\b/, "FORBIDDEN: No direct DOM manipulation — use DOMQL declarative object syntax instead (Rule 30)"],
  [/\.querySelector\b/, "FORBIDDEN: No DOM queries — reference elements by key name in the DOMQL object tree (Rule 30)"],
  [/\.appendChild\b/, "FORBIDDEN: No direct DOM manipulation — nest children as object keys or use children array (Rule 30)"],
  [/\.removeChild\b/, "FORBIDDEN: No direct DOM manipulation — use if: (el, s) => condition to show/hide (Rule 30)"],
  [/\.insertBefore\b/, "FORBIDDEN: No direct DOM manipulation — use children array ordering (Rule 30)"],
  [/\.innerHTML\s*=/, "FORBIDDEN: No direct DOM manipulation — use text: or html: prop (Rule 30)"],
  [/\.classList\./, "FORBIDDEN: No direct class manipulation — use isX + '.isX' pattern (Rule 19/30)"],
  [/\.setAttribute\b/, "FORBIDDEN: No direct DOM manipulation — set attributes at root level in DOMQL (Rule 30)"],
  [/\.addEventListener\b/, "FORBIDDEN: No direct event binding — use onX props: onClick, onInput, etc. (Rule 30)"],
  [/\.style\.\w+\s*=/, "FORBIDDEN: No direct style manipulation — use DOMQL CSS-in-props (Rule 30)"],
  [/html\s*:\s*\(?.*\)?\s*=>\s*/, "FORBIDDEN: Never use html: as a function returning markup — use DOMQL children, nesting, text:, and if: instead (Rule 31)"],
  [/return\s*`<\w+/, "FORBIDDEN: Never return HTML template literals — use DOMQL declarative children and nesting (Rule 31)"],
  [/style\s*=\s*['"`]/, "FORBIDDEN: No inline style= strings in html — use DOMQL CSS-in-props (Rule 31)"],
  [/window\.innerWidth/, "FORBIDDEN: No window.innerWidth checks — use @mobileL, @tabletS responsive breakpoints (Rule 31)"],
  [/\.parentNode\b/, "FORBIDDEN: No DOM traversal — use state and reactive props instead of walking the DOM tree (Rule 32)"],
  [/\.childNodes\b/, "FORBIDDEN: No DOM traversal — use state-driven children with if: props (Rule 32)"],
  [/\.textContent\b/, "FORBIDDEN: No DOM property access — use state and text: prop (Rule 32)"],
  [/Array\.from\(\w+\.children\)/, "FORBIDDEN: No DOM child iteration — use state arrays with children/childExtends and if: filtering (Rule 32)"],
  [/\.style\.display\s*=/, "FORBIDDEN: No style.display toggling — use show:/hide: to toggle visibility or if: to remove from DOM (Rule 32)"],
  [/\.style\.cssText\s*=/, "FORBIDDEN: No direct cssText — use DOMQL CSS-in-props (Rule 32)"],
  [/\.dataset\./, "FORBIDDEN: No dataset manipulation — use state and attr: for data-* attributes (Rule 32)"],
  [/\.remove\(\)/, "FORBIDDEN: No DOM node removal — use if: (el, s) => condition to conditionally render (Rule 32)"],
  [/el\.node\.\w+\s*=/, "FORBIDDEN: No direct el.node property assignment — use DOMQL props (placeholder:, value:, text:, etc.). Reading el.node is fine (Rule 39), writing is not (Rule 32)"],
  [/document\.getElementById\b/, "FORBIDDEN: No document.getElementById — use el.lookdown('key') to find DOMQL elements (Rule 40)"],
  [/document\.querySelectorAll\b/, "FORBIDDEN: No document.querySelectorAll — use el.lookdownAll('key') to find DOMQL elements (Rule 40)"],
  [/el\.parent\.state\b/, "FORBIDDEN: Never use el.parent.state — with childrenAs: 'state', use s.field directly (Rule 36)"],
  [/el\.context\.designSystem\b/, "FORBIDDEN: Never read designSystem from el.context in props — use token strings directly (Rule 38)"],
  [/^const\s+\w+\s*=\s*(?:\(|function)/m, "FORBIDDEN: No module-level helper functions — move to functions/ and call via el.call('fnName') (Rule 33)"],
  [/^let\s+\w+\s*=/m, "FORBIDDEN: No module-level variables — use el.scope for local state, functions/ for helpers (Rule 33)"],
  [/^var\s+\w+\s*=/m, "FORBIDDEN: No module-level variables — use el.scope for local state, functions/ for helpers (Rule 33)"],
]

function auditCode(code) {
  const violations = []
  const warnings = []

  for (const [pattern, message] of V2_PATTERNS) {
    const re = new RegExp(pattern.source, pattern.flags)
    let m
    while ((m = re.exec(code)) !== null) {
      const line = code.slice(0, m.index).split('\n').length
      violations.push({ line, severity: 'error', message })
    }
  }

  for (const [pattern, message] of RULE_CHECKS) {
    const re = new RegExp(pattern.source, pattern.flags || 'g')
    let m
    while ((m = re.exec(code)) !== null) {
      const line = code.slice(0, m.index).split('\n').length
      const level = message.includes('FORBIDDEN') ? 'error' : 'warning'
      const target = level === 'error' ? violations : warnings
      target.push({ line, severity: level, message })
    }
  }

  const totalIssues = violations.length + warnings.length
  const score = Math.max(1, 10 - totalIssues)

  return {
    passed: violations.length === 0,
    score,
    violations,
    warnings,
    summary: `${violations.length} errors, ${warnings.length} warnings — compliance score: ${score}/10`
  }
}

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------

const TOOLS = [
  {
    name: 'get_project_rules',
    description: 'ALWAYS call this first before any generate_* tool. Returns the mandatory Symbols.app rules that MUST be followed. Violations cause silent failures — black page, nothing renders.',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'search_symbols_docs',
    description: 'Search the Symbols documentation knowledge base for relevant information including CLI commands, SDK services, syntax, components, and more.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Natural language search query about Symbols/DOMQL/CLI/SDK' },
        max_results: { type: 'number', description: 'Maximum number of results (1-5)', default: 3 }
      },
      required: ['query']
    }
  },
  {
    name: 'get_cli_reference',
    description: 'Returns the complete Symbols CLI (@symbo.ls/cli) command reference — all smbls commands, options, and workflows.',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'get_sdk_reference',
    description: 'Returns the complete Symbols SDK (@symbo.ls/sdk) API reference — all services, methods, and usage examples.',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'generate_component',
    description: 'Generate a Symbols.app DOMQL v3 component from a description with full context (rules, syntax, cookbook, default library).',
    inputSchema: {
      type: 'object',
      properties: {
        description: { type: 'string', description: 'What the component should do and look like' },
        component_name: { type: 'string', description: 'PascalCase name for the component', default: 'MyComponent' }
      },
      required: ['description']
    }
  },
  {
    name: 'generate_page',
    description: 'Generate a Symbols.app page with routing integration and full context.',
    inputSchema: {
      type: 'object',
      properties: {
        description: { type: 'string', description: 'What the page should contain and do' },
        page_name: { type: 'string', description: 'camelCase name for the page', default: 'home' }
      },
      required: ['description']
    }
  },
  {
    name: 'convert_react',
    description: 'Convert React/JSX code to Symbols.app DOMQL v3 with migration context.',
    inputSchema: {
      type: 'object',
      properties: {
        source_code: { type: 'string', description: 'The React/JSX source code to convert' }
      },
      required: ['source_code']
    }
  },
  {
    name: 'convert_html',
    description: 'Convert raw HTML/CSS to Symbols.app DOMQL v3 components with full context.',
    inputSchema: {
      type: 'object',
      properties: {
        source_code: { type: 'string', description: 'The HTML/CSS source code to convert' }
      },
      required: ['source_code']
    }
  },
  {
    name: 'detect_environment',
    description: 'Detect project type (local, CDN, JSON runtime, or remote server) based on project indicators.',
    inputSchema: {
      type: 'object',
      properties: {
        has_symbols_json: { type: 'boolean', default: false },
        has_symbols_dir: { type: 'boolean', default: false },
        has_package_json: { type: 'boolean', default: false },
        has_cdn_import: { type: 'boolean', default: false },
        has_iife_script: { type: 'boolean', default: false },
        has_json_data: { type: 'boolean', default: false },
        has_mermaid_config: { type: 'boolean', default: false },
        file_list: { type: 'string', description: 'Comma-separated list of key files', default: '' }
      }
    }
  },
  {
    name: 'audit_component',
    description: 'Audit a Symbols/DOMQL component for v3 compliance — checks for v2 syntax, raw px values, hardcoded colors, direct DOM manipulation, and more. Returns violations, warnings, and a score.',
    inputSchema: {
      type: 'object',
      properties: {
        component_code: { type: 'string', description: 'The JavaScript component code to audit' }
      },
      required: ['component_code']
    }
  },
  {
    name: 'convert_to_json',
    description: 'Convert DOMQL v3 JavaScript source code to platform JSON format. Parses export statements, stringifies functions, outputs JSON ready for save_to_project.',
    inputSchema: {
      type: 'object',
      properties: {
        source_code: { type: 'string', description: 'JavaScript source code with export const/default statements' },
        section: { type: 'string', description: 'Target section: components, pages, functions, snippets, designSystem, state', default: 'components' }
      },
      required: ['source_code']
    }
  },
  {
    name: 'login',
    description: 'Log in to the Symbols platform and get an access token for project operations.',
    inputSchema: {
      type: 'object',
      properties: {
        email: { type: 'string', description: 'Symbols account email address' },
        password: { type: 'string', description: 'Symbols account password' }
      },
      required: ['email', 'password']
    }
  },
  {
    name: 'list_projects',
    description: 'List the user\'s Symbols projects (names, keys, IDs) to choose from.',
    inputSchema: {
      type: 'object',
      properties: {
        token: { type: 'string', description: 'JWT access token from login' },
        api_key: { type: 'string', description: 'API key (sk_live_...)' }
      }
    }
  },
  {
    name: 'create_project',
    description: 'Create a new Symbols project on the platform.',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Project display name' },
        key: { type: 'string', description: 'Project key (pr_xxxx format). Auto-generated if empty' },
        token: { type: 'string', description: 'JWT access token from login' },
        api_key: { type: 'string', description: 'API key (sk_live_...)' },
        visibility: { type: 'string', description: 'private, public, or password-protected', default: 'private' }
      },
      required: ['name']
    }
  },
  {
    name: 'get_project',
    description: 'Get a project\'s current data (components, pages, design system, state).',
    inputSchema: {
      type: 'object',
      properties: {
        project: { type: 'string', description: 'Project key (pr_xxxx) or project ID' },
        token: { type: 'string', description: 'JWT access token from login' },
        api_key: { type: 'string', description: 'API key (sk_live_...)' },
        branch: { type: 'string', description: 'Branch to read from', default: 'main' }
      },
      required: ['project']
    }
  },
  {
    name: 'save_to_project',
    description: 'Save components/pages/data to a Symbols project. Creates a new version with change tuples, granular changes, orders, and auto-generated schema entries (mirrors CLI push pipeline).',
    inputSchema: {
      type: 'object',
      properties: {
        project: { type: 'string', description: 'Project key (pr_xxxx) or project ID' },
        changes: { type: 'string', description: 'JSON string with project data: { components: {...}, pages: {...}, designSystem: {...}, state: {...}, functions: {...} }' },
        token: { type: 'string', description: 'JWT access token from login' },
        api_key: { type: 'string', description: 'API key (sk_live_...)' },
        message: { type: 'string', description: 'Version commit message' },
        branch: { type: 'string', description: 'Branch to save to', default: 'main' }
      },
      required: ['project', 'changes']
    }
  },
  {
    name: 'publish',
    description: 'Publish a version of a Symbols project. Makes the specified version (or latest) the published/live version.',
    inputSchema: {
      type: 'object',
      properties: {
        project: { type: 'string', description: 'Project key (pr_xxxx) or project ID' },
        token: { type: 'string', description: 'JWT access token from login' },
        api_key: { type: 'string', description: 'API key (sk_live_...)' },
        version: { type: 'string', description: 'Version string or ID. Empty for latest' },
        branch: { type: 'string', description: 'Branch to publish from', default: 'main' }
      },
      required: ['project']
    }
  },
  {
    name: 'push',
    description: 'Deploy a Symbols project to an environment (production, staging, dev).',
    inputSchema: {
      type: 'object',
      properties: {
        project: { type: 'string', description: 'Project key (pr_xxxx) or project ID' },
        token: { type: 'string', description: 'JWT access token from login' },
        api_key: { type: 'string', description: 'API key (sk_live_...)' },
        environment: { type: 'string', description: 'Target environment key', default: 'production' },
        mode: { type: 'string', description: 'Deploy mode: latest, published, version, or branch', default: 'published' },
        version: { type: 'string', description: 'Version string when mode is "version"' },
        branch: { type: 'string', description: 'Branch when mode is "latest" or "branch"', default: 'main' }
      },
      required: ['project']
    }
  }
]

// ---------------------------------------------------------------------------
// Tool handlers
// ---------------------------------------------------------------------------

async function handleTool(name, args) {
  // Documentation tools (sync)
  if (name === 'get_project_rules') return loadAgentInstructions()
  if (name === 'search_symbols_docs') return searchDocs(args.query, args.max_results || 3)
  if (name === 'get_cli_reference') return readSkill('CLI.md')
  if (name === 'get_sdk_reference') return readSkill('SDK.md')

  // Helper to read and concatenate multiple skill files
  function readSkills(...filenames) {
    return filenames.map(f => readSkill(f)).filter(c => !c.startsWith('Skill ')).join('\n\n---\n\n')
  }

  // generate_component
  if (name === 'generate_component') {
    const componentName = args.component_name || 'MyComponent'
    const context = readSkills('RULES.md', 'COMMON_MISTAKES.md', 'COMPONENTS.md', 'SYNTAX.md', 'COOKBOOK.md', 'DEFAULT_LIBRARY.md')
    return `# Generate Component: ${componentName}\n\n## Description\n${args.description}\n\n## Requirements\n- Named export: \`export const ${componentName} = { ... }\`\n- DOMQL v3 syntax only (extends, childExtends, flattened props, onX events)\n- **MANDATORY: ALL values MUST use design system tokens** — spacing (A, B, C, D), colors (primary, surface, white, gray.5), typography (fontSize: 'B'). ZERO px values, ZERO hex colors, ZERO rgb/hsl.\n- NO imports between files — PascalCase keys auto-extend registered components\n- Include responsive breakpoints where appropriate (@tabletS, @mobileL)\n- Use the default library components (Button, Avatar, Icon, Field, etc.) via extends\n- Use Icon component for SVGs — store icons in designSystem/icons\n- NO direct DOM manipulation — all structure via DOMQL declarative syntax\n- Follow modern UI/UX: visual hierarchy, confident typography, minimal cognitive load\n\n## Context — Rules, Syntax & Examples\n\n${context}`
  }

  // generate_page
  if (name === 'generate_page') {
    const pageName = args.page_name || 'home'
    const context = readSkills('RULES.md', 'COMMON_MISTAKES.md', 'PROJECT_STRUCTURE.md', 'PATTERNS.md', 'SNIPPETS.md', 'DEFAULT_LIBRARY.md', 'COMPONENTS.md')
    return `# Generate Page: ${pageName}\n\n## Description\n${args.description}\n\n## Requirements\n- Export as: \`export const ${pageName} = { ... }\`\n- Page is a plain object composing components\n- Add to pages/index.js route map: \`'/${pageName}': ${pageName}\`\n- Use components by PascalCase key (Header, Footer, Hero, etc.)\n- **MANDATORY: ALL values MUST use design system tokens** — spacing (A, B, C, D), colors (primary, surface, white, gray.5), typography (fontSize: 'B'). ZERO px values, ZERO hex colors, ZERO rgb/hsl.\n- Use Icon component for SVGs — store icons in designSystem/icons\n- NO direct DOM manipulation — all structure via DOMQL declarative syntax\n- Include responsive layout adjustments\n\n## Context — Rules, Structure, Patterns & Snippets\n\n${context}`
  }

  // convert_react
  if (name === 'convert_react') {
    const context = readSkills('RULES.md', 'MIGRATION.md', 'SYNTAX.md', 'COMPONENTS.md', 'LEARNINGS.md')
    return `# Convert React → Symbols DOMQL v3\n\n## Source Code to Convert\n\`\`\`jsx\n${args.source_code}\n\`\`\`\n\n## Conversion Rules\n- Function/class components → plain object exports\n- JSX → nested object children (PascalCase keys auto-extend)\n- import/export between files → REMOVE (reference by key name)\n- useState → state: { key: val } + s.update({ key: newVal })\n- useEffect → onRender (mount), onStateUpdate (deps)\n- props → flattened directly on component (no props wrapper)\n- onClick={handler} → onClick: (event, el, state) => {}\n- className → use design tokens and theme directly\n- map() → children: (el, s) => s.items, childExtends, childProps\n- conditional rendering → if: (el, s) => boolean\n- CSS modules/styled → CSS-in-props with design tokens\n- React.Fragment → not needed, just nest children\n\n## Context — Migration Guide, Syntax & Rules\n\n${context}`
  }

  // convert_html
  if (name === 'convert_html') {
    const context = readSkills('RULES.md', 'SYNTAX.md', 'COMPONENTS.md', 'DESIGN_SYSTEM.md', 'SNIPPETS.md', 'LEARNINGS.md')
    return `# Convert HTML → Symbols DOMQL v3\n\n## Source Code to Convert\n\`\`\`html\n${args.source_code}\n\`\`\`\n\n## Conversion Rules\n- <div> → Box, Flex, or Grid (based on layout purpose)\n- <span>, <p>, <h1>-<h6> → Text, P, H with tag property\n- <a> → Link (has built-in SPA router)\n- <button> → Button (has icon/text support)\n- <input> → Input, Radio, Checkbox (based on type)\n- <img> → Img\n- <form> → Form (extends Box with tag: 'form')\n- <ul>/<ol> + <li> → children array with childExtends\n- CSS classes → flatten as CSS-in-props on the component\n- CSS px values → design tokens (16px → 'A', 26px → 'B', 42px → 'C')\n- CSS colors → theme color tokens\n- media queries → @tabletS, @mobileL, @screenS breakpoints\n- id/class attributes → not needed (use key names and themes)\n- inline styles → flatten as component properties\n- <style> blocks → distribute to component-level properties\n\n## Context — Syntax, Components & Design System\n\n${context}`
  }

  // detect_environment
  if (name === 'detect_environment') {
    let envType = 'unknown', confidence = 'low'
    if (args.has_mermaid_config) { envType = 'remote_server'; confidence = 'high' }
    else if (args.has_json_data) { envType = 'json_runtime'; confidence = 'high' }
    else if (args.has_symbols_json && args.has_symbols_dir) { envType = 'local_project'; confidence = 'high' }
    else if (args.has_symbols_dir || (args.has_package_json && args.has_symbols_json)) { envType = 'local_project'; confidence = 'medium' }
    else if (args.has_cdn_import || args.has_iife_script) { envType = 'cdn'; confidence = 'high' }
    else if (args.has_package_json) { envType = 'local_project'; confidence = 'low' }
    else if (args.file_list) {
      const files = args.file_list.toLowerCase()
      if (files.includes('index.html') && !files.includes('package.json') && !files.includes('symbols.json')) { envType = 'cdn'; confidence = 'medium' }
    }
    const guide = readSkill('RUNNING_APPS.md')
    return `# Environment Detection\n\n**Detected: ${envType}** (confidence: ${confidence})\n\n${guide}`
  }

  // audit_component (sync)
  if (name === 'audit_component') {
    const result = auditCode(args.component_code)
    const rulesContext = readSkill('AUDIT.md')
    let output = `# Audit Report\n\n## Summary\n${result.summary}\nPassed: ${result.passed ? 'Yes' : 'No'}\n\n## Violations (Errors)\n`
    if (result.violations.length) {
      for (const v of result.violations) output += `- **Line ${v.line}**: ${v.message}\n`
    } else {
      output += 'No violations found.\n'
    }
    output += '\n## Warnings\n'
    if (result.warnings.length) {
      for (const w of result.warnings) output += `- **Line ${w.line}**: ${w.message}\n`
    } else {
      output += 'No warnings.\n'
    }
    if (result.violations.length) {
      output += '\n## MANDATORY ACTION\n\n**Every violation above MUST be fixed. There is NO concept of "known debt", "accepted violations", or "95% fixed" in Symbols. ALL violations must reach 100% resolution. Do NOT label any violation as "known debt" or defer it. Rewrite the code using proper DOMQL syntax.**\n\n'
    }
    output += `\n## Detailed Rules Reference\n\n${rulesContext}`
    return output
  }

  // convert_to_json (sync)
  if (name === 'convert_to_json') {
    const section = args.section || 'components'
    const parsed = parseJsToJson(args.source_code)
    if (!Object.keys(parsed).length) {
      return 'Could not parse any exports from the source code. Make sure it contains `export const Name = { ... }` or `export default { ... }`.'
    }
    const result = {}
    for (const [exportName, rawValue] of Object.entries(parsed)) {
      const converted = typeof rawValue === 'string' ? jsObjToJson(rawValue) : rawValue
      if (exportName === '__default__') {
        if (['designSystem', 'state', 'dependencies', 'config'].includes(section)) {
          result[section] = converted
        } else {
          if (!result[section]) result[section] = {}
          result[section]['default'] = converted
        }
      } else {
        if (!result[section]) result[section] = {}
        result[section][exportName] = converted
      }
    }
    const output = JSON.stringify(result, null, 2)
    const sections = Object.keys(result)
    const items = []
    for (const sec of sections) {
      if (typeof result[sec] === 'object' && result[sec]) items.push(...Object.keys(result[sec]))
    }
    return `# Converted to Platform JSON\n\n**Section:** ${sections.join(', ')}\n**Items:** ${items.join(', ') || 'default export'}\n\n\`\`\`json\n${output}\n\`\`\`\n\nThis JSON is ready to use with \`save_to_project\`. Pass the JSON object above as the \`changes\` parameter.\n\n**Full flow:**\n1. \`convert_to_json\` (done) → structured JSON\n2. \`save_to_project\` → push to platform (creates new version)\n3. \`publish\` → make version live\n4. \`push\` → deploy to environment (production/staging/dev)`
  }

  // login
  if (name === 'login') {
    const result = await apiRequest('POST', '/core/auth/login', {
      body: { email: args.email, password: args.password }
    })
    if (result.success) {
      const { tokens = {}, user = {} } = result.data || {}
      const token = tokens.accessToken || ''
      return `Logged in as ${user.name || user.email || 'unknown'}.\nToken: ${token}\nExpires: ${tokens.accessTokenExp?.expiresAt || 'unknown'}\n\nUse this token with project, save, publish and push tools.`
    }
    return `Login failed: ${result.error || result.message || 'Unknown error'}`
  }

  // list_projects
  if (name === 'list_projects') {
    const authErr = requireAuth(args.token, args.api_key)
    if (authErr) return authErr
    const result = await apiRequest('GET', '/core/projects', { token: args.token, apiKey: args.api_key })
    if (result.success) {
      const projects = result.data || []
      if (!projects.length) return 'No projects found. Use `create_project` to create one.'
      const lines = ['# Your Projects\n']
      for (const p of projects) {
        lines.push(`- **${p.name || 'Untitled'}** — key: \`${p.key || '—'}\`, id: \`${p._id || ''}\`, visibility: ${p.visibility || 'private'}`)
      }
      return lines.join('\n')
    }
    return `Failed to list projects: ${result.error || 'Unknown error'}`
  }

  // create_project
  if (name === 'create_project') {
    const authErr = requireAuth(args.token, args.api_key)
    if (authErr) return authErr
    const body = { name: args.name, visibility: args.visibility || 'private', language: 'javascript' }
    if (args.key) body.key = args.key
    const result = await apiRequest('POST', '/core/projects', { token: args.token, apiKey: args.api_key, body })
    if (result.success) {
      const d = result.data || {}
      return `Project created successfully.\nName: ${d.name || args.name}\nKey: \`${d.key || 'unknown'}\`\nID: \`${d._id || 'unknown'}\`\n\nUse this project key/ID with \`save_to_project\` to push your components.`
    }
    return `Create failed: ${result.error || 'Unknown error'}\n${result.message || ''}`
  }

  // get_project
  if (name === 'get_project') {
    const authErr = requireAuth(args.token, args.api_key)
    if (authErr) return authErr
    const branch = args.branch || 'main'
    const project = args.project
    const isKey = project.startsWith('pr_') || !/^[0-9a-f]+$/.test(project)
    const urlPath = isKey
      ? `/core/projects/key/${project}/data?branch=${branch}&version=latest`
      : `/core/projects/${project}/data?branch=${branch}&version=latest`
    const result = await apiRequest('GET', urlPath, { token: args.token, apiKey: args.api_key })
    if (result.success) {
      const data = result.data || {}
      const components = data.components || {}
      const pages = data.pages || {}
      const ds = data.designSystem || {}
      const state = data.state || {}
      const functions = data.functions || {}
      const lines = [`# Project Data (branch: ${branch})\n`]
      lines.push(`**Components (${Object.keys(components).length}):** ${Object.keys(components).slice(0, 20).join(', ') || 'none'}`)
      lines.push(`**Pages (${Object.keys(pages).length}):** ${Object.keys(pages).slice(0, 20).join(', ') || 'none'}`)
      lines.push(`**Design System keys:** ${Object.keys(ds).slice(0, 15).join(', ') || 'none'}`)
      lines.push(`**State keys:** ${Object.keys(state).slice(0, 15).join(', ') || 'none'}`)
      lines.push(`**Functions (${Object.keys(functions).length}):** ${Object.keys(functions).slice(0, 15).join(', ') || 'none'}`)
      lines.push(`\n---\n\nFull data:\n\`\`\`json\n${JSON.stringify(data, null, 2).slice(0, 8000)}\n\`\`\``)
      return lines.join('\n')
    }
    return `Failed to get project data: ${result.error || 'Unknown error'}`
  }

  // save_to_project
  if (name === 'save_to_project') {
    const authErr = requireAuth(args.token, args.api_key)
    if (authErr) return authErr
    let changesData
    try { changesData = JSON.parse(args.changes) }
    catch (e) { return `Invalid JSON in changes: ${e.message}` }
    if (typeof changesData !== 'object' || changesData === null) {
      return 'Changes must be a JSON object with keys like components, pages, designSystem, state, functions.'
    }
    const { id: projectId, error: resolveErr } = await resolveProjectId(args.project, args.token, args.api_key)
    if (resolveErr) return resolveErr
    const { changes, granular: granularChanges, orders } = buildChangesAndSchema(changesData)
    if (!changes.length) return 'No valid changes found. Include at least one data section.'
    const branch = args.branch || 'main'
    const body = {
      changes, granularChanges, orders,
      message: args.message || 'Updated via Symbols MCP',
      branch, type: 'patch'
    }
    const result = await apiRequest('POST', `/core/projects/${projectId}/changes`, { token: args.token, apiKey: args.api_key, body })
    if (result.success) {
      const d = result.data || {}
      const version = d.value || d.version || d.id || 'unknown'
      const savedSections = Object.keys(changesData)
      return `Saved to project \`${args.project}\` successfully.\nVersion: ${version}\nBranch: ${branch}\nSections updated: ${savedSections.join(', ')}\n\nUse \`publish\` to make this version live, or \`push\` to deploy to an environment.`
    }
    return `Save failed: ${result.error || 'Unknown error'}\n${result.message || ''}`
  }

  // publish
  if (name === 'publish') {
    const authErr = requireAuth(args.token, args.api_key)
    if (authErr) return authErr
    const { id: projectId, error: resolveErr } = await resolveProjectId(args.project, args.token, args.api_key)
    if (resolveErr) return resolveErr
    const body = { branch: args.branch || 'main' }
    if (args.version) body.version = args.version
    const result = await apiRequest('POST', `/core/projects/${projectId}/publish`, { token: args.token, apiKey: args.api_key, body })
    if (result.success) {
      const d = result.data || {}
      return `Published successfully.\nVersion: ${d.value || d.id || 'unknown'}`
    }
    return `Publish failed: ${result.error || 'Unknown error'}\n${result.message || ''}`
  }

  // push
  if (name === 'push') {
    const authErr = requireAuth(args.token, args.api_key)
    if (authErr) return authErr
    const { id: projectId, error: resolveErr } = await resolveProjectId(args.project, args.token, args.api_key)
    if (resolveErr) return resolveErr
    const environment = args.environment || 'production'
    const mode = args.mode || 'published'
    const branch = args.branch || 'main'
    const body = { mode, branch }
    if (args.version) body.version = args.version
    const result = await apiRequest('POST', `/core/projects/${projectId}/environments/${environment}/publish`, { token: args.token, apiKey: args.api_key, body })
    if (result.success) {
      const d = result.data || {}
      const config = d.config || {}
      return `Pushed to ${d.key || environment} successfully.\nMode: ${config.mode || mode}\nVersion: ${config.version || 'latest'}\nBranch: ${config.branch || branch}`
    }
    return `Push failed: ${result.error || 'Unknown error'}\n${result.message || ''}`
  }

  throw new Error(`Unknown tool: ${name}`)
}

// ---------------------------------------------------------------------------
// JSON-RPC server
// ---------------------------------------------------------------------------

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n')
}

async function handle(req) {
  if (!req.method) return
  if (req.method === 'initialize') {
    return send({
      jsonrpc: '2.0', id: req.id,
      result: {
        protocolVersion: req.params?.protocolVersion ?? '2025-03-26',
        capabilities: { tools: {} },
        serverInfo: { name: 'Symbols MCP', version: '1.0.15' }
      }
    })
  }
  if (req.method === 'notifications/initialized') return
  if (req.method === 'ping') return send({ jsonrpc: '2.0', id: req.id, result: {} })
  if (req.method === 'tools/list') return send({ jsonrpc: '2.0', id: req.id, result: { tools: TOOLS } })
  if (req.method === 'tools/call') {
    const { name, arguments: args = {} } = req.params
    try {
      const text = await handleTool(name, args)
      return send({ jsonrpc: '2.0', id: req.id, result: { content: [{ type: 'text', text }] } })
    } catch (e) {
      return send({ jsonrpc: '2.0', id: req.id, result: { content: [{ type: 'text', text: e.message }], isError: true } })
    }
  }
  if (req.id !== undefined) {
    send({ jsonrpc: '2.0', id: req.id, error: { code: -32601, message: 'Method not found' } })
  }
}

const rl = readline.createInterface({ input: process.stdin, terminal: false })
rl.on('line', line => {
  if (!line.trim()) return
  try { handle(JSON.parse(line)).catch(e => process.stderr.write(`Handler error: ${e.message}\n`)) }
  catch (e) { process.stderr.write(`Parse error: ${e.message}\n`) }
})
rl.on('close', () => process.exit(0))
