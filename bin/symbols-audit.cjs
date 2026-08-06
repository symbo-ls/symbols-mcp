#!/usr/bin/env node
/**
 * symbols-audit — thin wrapper around `@symbo.ls/frank-audit`.
 *
 * The legacy regex-based audit was retired in 3.14.0; this binary now
 * delegates to the frank-audit CLI which owns the canonical 59-rule
 * registry and the AST-based detection. The user-facing flag surface
 * is preserved for compatibility with existing scripts and CI:
 *
 *   symbols-audit [path]                     # path defaults to ./symbols (STRICT BY DEFAULT)
 *   symbols-audit --json                     # machine output (frank-audit/1.0 envelope)
 *   symbols-audit --allow-findings           # opt out of strict mode (exit 0 even with findings)
 *   symbols-audit --no-deep-fix              # legacy flag — passed to agents reading the log only
 *   symbols-audit --no-deep-framework-audit  # legacy flag — passed to agents reading the log only
 *
 * Exit codes:
 *   0 — clean (no critical/high findings) OR --allow-findings was passed
 *   1 — findings present in strict mode, or frank-audit failed
 *   2 — invalid args / project path not found
 *
 * Override the binary location via FRANK_AUDIT_BIN if `frank-audit` isn't
 * on PATH (e.g. in monorepo dev: FRANK_AUDIT_BIN=/path/to/frank-audit.js).
 */

'use strict'

const fs = require('node:fs')
const path = require('node:path')
const { spawnSync } = require('node:child_process')

const FRANK_AUDIT_BIN = process.env.FRANK_AUDIT_BIN || 'frank-audit'

const args = process.argv.slice(2)
const flagJson = args.includes('--json')
const flagAllowFindings = args.includes('--allow-findings') || args.includes('--no-strict') || args.includes('--soft')
const flagStrict = !flagAllowFindings
const targetArg = args.find(a => !a.startsWith('--')) || './symbols'
const PROJECT_ROOT = path.resolve(targetArg)

if (!fs.existsSync(PROJECT_ROOT)) {
  console.error(`✗ Project path does not exist: ${PROJECT_ROOT}`)
  process.exit(2)
}

const frankArgs = ['audit', PROJECT_ROOT]
if (flagStrict) frankArgs.push('--strict')
if (flagJson) frankArgs.push('--json')

// Pass through any unrecognized --flag args (e.g. --rule, --no-color, --verbose)
const KNOWN = new Set(['--json', '--allow-findings', '--no-strict', '--soft', '--no-deep-fix', '--no-deep-framework-audit'])
for (const a of args) {
  if (a === targetArg) continue
  if (a.startsWith('--') && !KNOWN.has(a) && !a.startsWith('--no-deep-')) {
    frankArgs.push(a)
  }
}

const result = spawnSync(FRANK_AUDIT_BIN, frankArgs, {
  stdio: 'inherit',
  encoding: 'utf-8'
})

if (result.error && result.error.code === 'ENOENT') {
  console.error(`✗ frank-audit CLI not found (looked for: ${FRANK_AUDIT_BIN})`)
  console.error('  Install: npm i -g @symbo.ls/frank-audit')
  console.error('  Or set FRANK_AUDIT_BIN to the executable path.')
  process.exit(1)
}

process.exit(result.status ?? 1)
