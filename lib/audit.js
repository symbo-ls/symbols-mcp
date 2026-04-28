/**
 * @symbo.ls/mcp/lib/audit — backward-compat shim.
 *
 * The legacy regex-based implementation (~700 lines, 56 hand-written regex
 * rules across FORBIDDEN_SYNTAX / HARDCODED_VALUES / MODERN_STACK_BYPASS /
 * DOM_BANS / STRUCTURAL / ICON_BANS / POLYGLOT_HINTS) was retired in 3.14.0
 * in favor of `@symbo.ls/frank-audit` — the AST-based audit engine that ships
 * the canonical 59-rule registry, prescription generation, and verify-or-
 * rollback fixers. This file is a thin shim: every entry point now subprocesses
 * the `frank-audit` CLI (or hits its `/audit-content` HTTP endpoint when
 * `FRANK_AUDIT_URL` is set) and translates the new envelope back to the legacy
 * field shape so external consumers (bin/symbols-audit, the @symbo.ls/cli
 * audit runner, the MCP HTTP worker) keep working.
 *
 * Findings drift vs the old regex output is expected and correct — frank-audit
 * detects more issues with higher accuracy. Field names stay the same where
 * possible (file, line, rule, severity, category, snippet, suggested_fix).
 *
 * Don't add rules here. Add them to smbls/plugins/frank-audit/src/core/rules/.
 *
 * The Python MCP server has its own subprocess bridge in symbols_mcp/server.py
 * — this file does NOT touch that path.
 */

'use strict'

const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const crypto = require('node:crypto')
const { spawnSync } = require('node:child_process')

const FRANK_AUDIT_BIN = process.env.FRANK_AUDIT_BIN || 'frank-audit'
const FRANK_AUDIT_URL = process.env.FRANK_AUDIT_URL || null

// Severity ordering is preserved for backward compatibility with consumers
// that sort by it. frank-audit uses the same canonical severities.
const SEVERITY_ORDER = { critical: 0, structural: 1, systemic: 2, cosmetic: 3, info: 4 }

function shortHash (s) {
  return 'f_' + crypto.createHash('sha256').update(s).digest('hex').slice(0, 7)
}

function classifyOrigin (file) {
  if (!file) return 'project'
  const f = file.replace(/\\/g, '/')
  if (f.includes('/node_modules/') || f.startsWith('node_modules/')) return 'framework'
  if (f.includes('/.symbols_local/') || f.startsWith('.symbols_local/')) return 'shared'
  if (f.includes('/shared-libraries/') || f.includes('/sharedLibraries/')) return 'shared'
  return 'project'
}

function runFrankAudit (args) {
  const result = spawnSync(FRANK_AUDIT_BIN, [...args, '--json'], {
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024
  })
  if (result.error && result.error.code === 'ENOENT') {
    return { ok: false, error: { code: 'E_FRANK_AUDIT_NOT_FOUND', message: `frank-audit CLI not found (looked for: ${FRANK_AUDIT_BIN}). Install with: npm i -g @symbo.ls/frank-audit, or set FRANK_AUDIT_BIN to the executable path.` } }
  }
  if (result.status !== 0 && !result.stdout) {
    return { ok: false, error: { code: 'E_FRANK_AUDIT_FAILED', message: `frank-audit exited ${result.status}: ${(result.stderr || '').slice(0, 500)}` } }
  }
  try {
    return JSON.parse(result.stdout)
  } catch (e) {
    return { ok: false, error: { code: 'E_FRANK_AUDIT_BAD_OUTPUT', message: `frank-audit emitted invalid JSON: ${e.message}` } }
  }
}

// Translate one frank-audit/1.0 finding to the legacy shape.
function translateFinding (f) {
  const file = (f.file || '').replace(/\\/g, '/')
  const line = f.line || 0
  const rule = f.ruleId || f.rule || 'unknown'
  const snippet = (f.meta && f.meta.snippet) || f.snippet || (f.message || '').slice(0, 120)
  const suggested_fix = f.message || f.suggested_fix || ''
  return {
    id: shortHash(`${file}:${line}:${rule}:${snippet}`),
    file,
    line,
    rule,
    severity: f.severity || 'critical',
    category: f.category || 'general',
    origin: classifyOrigin(file),
    snippet,
    suggested_fix,
    status: 'open',
    discovered_at: new Date().toISOString(),
    resolved_at: null,
    attempts: 0,
    notes: []
  }
}

function envelopeToFindings (payload) {
  if (!payload || payload.ok === false) {
    const err = (payload && payload.error) || { code: 'E_UNKNOWN', message: 'frank-audit returned no payload' }
    return [{
      id: shortHash(`<frank-audit>:${err.code}`),
      file: '<frank-audit>',
      line: 0,
      rule: err.code,
      severity: 'critical',
      category: 'frank-audit',
      origin: 'framework',
      snippet: err.code,
      suggested_fix: `[frank-audit unavailable: ${err.code}] ${err.message || ''}`,
      status: 'open',
      discovered_at: new Date().toISOString(),
      resolved_at: null,
      attempts: 0,
      notes: []
    }]
  }
  return (payload.findings || []).map(translateFinding)
}

/**
 * Audit a single component's source code.
 * Writes the code to a synthetic components/Inline.js + state.js and runs
 * `frank-audit audit <tmp>`. (Or hits the HTTP /audit-content endpoint when
 * FRANK_AUDIT_URL is set — pure, no fs.)
 *
 * @returns {Array} legacy-shape findings
 */
function auditContent (code, opts = {}) {
  const file = opts.file || '<inline>'

  if (FRANK_AUDIT_URL) {
    try {
      // Synchronous HTTP via spawnSync(curl) keeps the legacy sync API.
      const res = spawnSync('curl', ['-fsS', '-X', 'POST', '-H', 'Content-Type: application/json', '--data-binary', '@-', `${FRANK_AUDIT_URL.replace(/\/$/, '')}/audit-content`], {
        input: JSON.stringify({ code, file }),
        encoding: 'utf-8',
        maxBuffer: 64 * 1024 * 1024
      })
      if (res.status === 0 && res.stdout) {
        return envelopeToFindings(JSON.parse(res.stdout))
      }
    } catch (_) { /* fall through to CLI */ }
  }

  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'symbols-mcp-audit-'))
  try {
    fs.mkdirSync(path.join(tmp, 'components'), { recursive: true })
    fs.writeFileSync(path.join(tmp, 'components', 'Inline.js'), code, 'utf-8')
    fs.writeFileSync(path.join(tmp, 'state.js'), 'export default {}\n', 'utf-8')
    const payload = runFrankAudit(['audit', tmp])
    return envelopeToFindings(payload).map(f => {
      // Re-display as <inline> — the tmp path is an internal detail.
      if (f.file && f.file.startsWith(tmp)) f.file = file
      return f
    })
  } finally {
    try { fs.rmSync(tmp, { recursive: true, force: true }) } catch (_) {}
  }
}

/**
 * Audit a list of in-memory files. Iterates and concatenates per-file results.
 * Cross-file rules (orphan detection, etc.) won't fire across the boundary —
 * for that, callers should use auditDirectory on a real fs path.
 */
function auditFiles (files, opts = {}) {
  const findings = []
  for (const { path: filePath, content } of files) {
    if (!content) continue
    findings.push(...auditContent(content, { ...opts, file: filePath }))
  }
  sortFindings(findings)
  return findings
}

/**
 * Walk a symbols/ directory via `frank-audit audit <dir> --json` and
 * return findings + scannedFiles in the legacy shape.
 */
function auditDirectory (symbolsDir, opts = {}) {
  const projectRoot = opts.projectRoot || path.dirname(symbolsDir)
  const payload = runFrankAudit(['audit', symbolsDir])
  const findings = envelopeToFindings(payload).map(f => {
    if (f.file && path.isAbsolute(f.file)) {
      f.file = path.relative(projectRoot, f.file).replace(/\\/g, '/')
    }
    return f
  })
  sortFindings(findings)
  return {
    findings,
    scannedFiles: payload.scannedFiles ?? findings.length
  }
}

// ─── Persistence helpers (preserved verbatim from the legacy module) ──────────

function sortFindings (items) {
  items.sort((a, b) =>
    ((SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9)) ||
    a.file.localeCompare(b.file) ||
    (a.line - b.line)
  )
}

function mergeFindings (oldItems, newItems) {
  const oldById = new Map((oldItems || []).map(it => [it.id, it]))
  const merged = []
  for (const f of newItems) {
    const prior = oldById.get(f.id)
    if (prior) {
      merged.push({ ...f, status: prior.status, resolved_at: prior.resolved_at, attempts: prior.attempts, notes: prior.notes })
      oldById.delete(f.id)
    } else {
      merged.push(f)
    }
  }
  for (const stale of oldById.values()) {
    if (stale.status !== 'resolved' && stale.status !== 'framework_bug') {
      stale.status = 'resolved'
      stale.resolved_at = stale.resolved_at || new Date().toISOString()
    }
    merged.push(stale)
  }
  return merged
}

function summarize (items) {
  const open = items.filter(f => f.status === 'open' || f.status === 'in_progress')
  const byCategory = open.reduce((acc, f) => { acc[f.category] = (acc[f.category] || 0) + 1; return acc }, {})
  const bySeverity = open.reduce((acc, f) => { acc[f.severity] = (acc[f.severity] || 0) + 1; return acc }, {})
  const byOrigin = open.reduce((acc, f) => { const o = f.origin || 'project'; acc[o] = (acc[o] || 0) + 1; return acc }, {})
  return {
    open: open.length,
    total: items.length,
    resolved: items.filter(f => f.status === 'resolved').length,
    frameworkBugs: items.filter(f => f.status === 'framework_bug').length,
    byCategory,
    bySeverity,
    byOrigin
  }
}

function ensureDir (d) { fs.mkdirSync(d, { recursive: true }) }

function readFindingsFile (auditDir) {
  const findingsPath = path.join(auditDir, 'findings.json')
  if (!fs.existsSync(findingsPath)) return { items: [] }
  try { return JSON.parse(fs.readFileSync(findingsPath, 'utf-8')) } catch { return { items: [] } }
}

function writeFindingsFile (auditDir, items) {
  ensureDir(auditDir)
  const findingsPath = path.join(auditDir, 'findings.json')
  fs.writeFileSync(findingsPath, JSON.stringify({ $schema: 'symbols-mcp findings v1 (frank-audit-backed)', items }, null, 2))
  return findingsPath
}

function snapshot (symbolsDir) {
  // Lightweight snapshot — counts only what frank-audit can already see.
  const files = []
  function walk (d) {
    if (!fs.existsSync(d)) return
    for (const name of fs.readdirSync(d)) {
      if (['node_modules', '.parcel-cache', '.cache', 'dist', 'audit', '.frank-audit'].includes(name)) continue
      const p = path.join(d, name)
      const st = fs.statSync(p)
      if (st.isDirectory()) walk(p)
      else if (name.endsWith('.js')) files.push(p)
    }
  }
  walk(symbolsDir)
  const components = files.filter(f => f.includes('/components/') && !f.endsWith('/index.js'))
  const pages = files.filter(f => f.includes('/pages/') && !f.endsWith('/index.js'))
  let lineCount = 0
  for (const f of files) { try { lineCount += fs.readFileSync(f, 'utf-8').split('\n').length } catch (_) {} }
  return {
    timestamp: new Date().toISOString(),
    fileCount: files.length,
    componentCount: components.length,
    pageCount: pages.length,
    lineCount
  }
}

function createReportTemplates (auditDir, { deepFrameworkAudit = true } = {}) {
  ensureDir(auditDir)
  const projPath = path.join(auditDir, 'symbols_audit_results.md')
  const fwPath = path.join(auditDir, 'framework_audit_results.md')
  const created = { proj: false, fw: false }
  if (!fs.existsSync(projPath)) {
    fs.writeFileSync(projPath, `---\nkind: project-audit-results\ncreated_at: ${new Date().toISOString()}\n---\n\n# Symbols project audit — findings & resolutions\n\nPopulated by the agent during Phase 2.\n`)
    created.proj = true
  }
  if (!fs.existsSync(fwPath)) {
    fs.writeFileSync(fwPath, `---\nkind: framework-audit-results\ncreated_at: ${new Date().toISOString()}\ndeep_framework_audit: ${deepFrameworkAudit}\n---\n\n# Symbols framework audit — bugs originating in smbls/, plugins, or shared libs\n\nPopulated by the agent during Phase 2 + Phase 4.\n`)
    created.fw = true
  }
  return { projPath, fwPath, created }
}

// ALL_RULES is no longer hand-maintained here — frank-audit owns the registry.
// Exported as an empty array for backward compatibility with consumers that
// just want to iterate (they should query frank-audit directly for the list).
const ALL_RULES = []

module.exports = {
  // Constants
  ALL_RULES,
  SEVERITY_ORDER,
  // Layer 1: pure
  auditContent,
  auditFiles,
  // Layer 2: filesystem
  auditDirectory,
  snapshot,
  // Layer 3: persistence
  mergeFindings,
  summarize,
  sortFindings,
  readFindingsFile,
  writeFindingsFile,
  createReportTemplates,
  // Helpers
  classifyOrigin,
  shortHash
}
