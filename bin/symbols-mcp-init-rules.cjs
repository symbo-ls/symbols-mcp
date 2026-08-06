#!/usr/bin/env node
/**
 * symbols-mcp-init-rules — drop editor-specific agent-rule files into a Symbols project.
 *
 * Usage:
 *   symbols-mcp-init-rules [project-root]        # defaults to cwd
 *   symbols-mcp-init-rules --force               # overwrite existing files
 *   symbols-mcp-init-rules --only=cursor,claude  # restrict to specific editors
 *   symbols-mcp-init-rules --detect              # restrict to AI agents detected on this machine
 *   symbols-mcp-init-rules --no-hooks            # skip Claude Code hooks install
 *   symbols-mcp-init-rules --no-skills           # skip the Claude Code `symbols` skill install
 *   symbols-mcp-init-rules --global              # install hooks + skill to ~/.claude/ (user-global)
 *                                                # — only meaningful with the claude editor;
 *                                                # other editors are skipped in --global mode
 *   symbols-mcp-init-rules --list                # show what would be written, don't write
 *   symbols-mcp-init-rules --help                # show usage
 *
 * Files written (by editor):
 *   CLAUDE.md                       — Claude Code, Anthropic-flavored agents
 *   .cursor/rules/symbols.md        — Cursor (auto-applies on every chat)
 *   .windsurfrules                  — Windsurf (Codeium)
 *   .clinerules                     — Cline (VS Code)
 *   AGENTS.md                       — Codex / Copilot / Gemini CLI / Aider / Cody / Goose / Warp / Antigravity / fallback
 *   .claude/skills/symbols/SKILL.md — Claude Code agent skill (auto-loads on Symbols work)
 *
 * Claude Code hooks (installed alongside CLAUDE.md unless --no-hooks):
 *   .claude/settings.json                     — wires the three hooks below
 *   .claude/hooks/symbols-mcp-require.sh      — PreToolUse Edit|Write — blocks JS edits
 *                                                in Symbols projects until
 *                                                mcp__symbols-mcp__get_project_rules
 *                                                (or get_project_context) was called
 *   .claude/hooks/symbols-mcp-reminder.sh     — UserPromptSubmit — injects MUST-DO sequence
 *                                                + frankability FA-rule cheatsheet per turn
 *   .claude/hooks/symbols-mcp-audit.sh        — PostToolUse Edit|Write — runs frank-audit +
 *                                                inline FA-rule pattern check on touched .js
 *
 * All files reference the symbols-mcp tools (`mcp__symbols-mcp__*`) and the strict
 * ruleset. Idempotent: skips files that already exist (use --force to overwrite).
 *
 * Goal: every Symbols project auto-bootstraps any agent that reads project-level
 * rules — no need to remind Claude/Cursor/Windsurf to "use symbols-mcp" each time.
 * For Claude Code specifically, the hooks layer makes rule-loading non-bypassable.
 */

'use strict'

const fs = require('node:fs')
const path = require('node:path')

const args = process.argv.slice(2)
if (args.includes('--help') || args.includes('-h')) {
  console.log(fs.readFileSync(__filename, 'utf-8').split('\n').slice(1, 23).join('\n').replace(/^ \*/gm, '').trim())
  process.exit(0)
}

const flagForce = args.includes('--force')
const flagList = args.includes('--list') || args.includes('--dry-run')
const flagNoHooks = args.includes('--no-hooks')
const flagNoSkills = args.includes('--no-skills')
const flagDetect = args.includes('--detect')
const flagGlobal = args.includes('--global')
const onlyArg = args.find(a => a.startsWith('--only='))
let onlyEditors = onlyArg ? onlyArg.slice('--only='.length).split(',').map(s => s.trim().toLowerCase()) : null
const projectArg = args.find(a => !a.startsWith('-')) || '.'
const PROJECT = path.resolve(projectArg)
const HOME = process.env.HOME || require('os').homedir()

// ── Agent detection (wrangler-style) ──────────────────────────────────────
// Probe well-known config dirs / binaries for AI coding agents present on
// this machine. Each detected agent maps to the editor target that carries
// its rules: claude/cursor/windsurf/cline have dedicated files; everything
// else (Codex, Copilot, Gemini CLI, Goose, Warp, Antigravity, Zed, Aider,
// Cody) auto-loads the vendor-neutral AGENTS.md.
const hasBin = (name) => {
  try {
    const { execSync } = require('node:child_process')
    execSync(process.platform === 'win32' ? `where ${name}` : `command -v ${name}`, { stdio: 'ignore', shell: true })
    return true
  } catch (_) { return false }
}
const dirExists = (...segs) => { try { return fs.existsSync(path.join(...segs)) } catch (_) { return false } }

const AGENT_PROBES = [
  ['Claude Code',   'claude',   () => dirExists(HOME, '.claude') || hasBin('claude')],
  ['Cursor',        'cursor',   () => dirExists(HOME, '.cursor')],
  ['Windsurf',      'windsurf', () => dirExists(HOME, '.codeium', 'windsurf')],
  ['Cline',         'cline',    () => dirExists(HOME, 'Library', 'Application Support', 'Code', 'User', 'globalStorage', 'saoudrizwan.claude-dev')],
  ['Codex',         'agents',   () => dirExists(HOME, '.codex') || hasBin('codex')],
  ['GitHub Copilot','agents',   () => dirExists(HOME, '.copilot') || hasBin('copilot')],
  ['Gemini CLI',    'agents',   () => dirExists(HOME, '.gemini') || hasBin('gemini')],
  ['Goose',         'agents',   () => dirExists(HOME, '.config', 'goose')],
  ['Warp',          'agents',   () => dirExists(HOME, '.warp') || dirExists(HOME, 'Library', 'Application Support', 'dev.warp.Warp-Stable')],
  ['Antigravity',   'agents',   () => dirExists(HOME, '.antigravity')],
  ['Zed',           'agents',   () => dirExists(HOME, '.config', 'zed')],
  ['Aider',         'agents',   () => dirExists(HOME, '.aider') || hasBin('aider')],
]

const detectAgents = () => AGENT_PROBES.filter(([, , probe]) => probe()).map(([label, target]) => ({ label, target }))

if (flagDetect) {
  const detected = detectAgents()
  if (detected.length) {
    console.log(`Detected AI coding agents on this machine: ${detected.map(d => d.label).join(', ')}.`)
    console.log(`Installing Symbols rules + skills for them.`)
    console.log()
    const targets = [...new Set(detected.map(d => d.target))]
    // Intersect with an explicit --only when both are given.
    onlyEditors = onlyEditors ? onlyEditors.filter(e => targets.includes(e)) : targets
  } else {
    console.log(`No AI coding agents detected — writing the full rule set anyway.`)
    console.log()
  }
}

if (!fs.existsSync(PROJECT)) {
  console.error(`✗ project root does not exist: ${PROJECT}`)
  process.exit(2)
}

const TEMPLATES_DIR = path.join(__dirname, '..', 'templates', 'agent-rules')

// (editor key, template relative path, destination relative path in project)
const TARGETS = [
  ['claude',   'CLAUDE.md',                    'CLAUDE.md'],
  ['cursor',   '.cursor/rules/symbols.md',     '.cursor/rules/symbols.md'],
  ['windsurf', '.windsurfrules',               '.windsurfrules'],
  ['cline',    '.clinerules',                  '.clinerules'],
  ['agents',   'AGENTS.md',                    'AGENTS.md'],
]

const filtered = onlyEditors
  ? TARGETS.filter(([key]) => onlyEditors.includes(key))
  : TARGETS

if (!filtered.length) {
  console.error(`✗ no editors matched --only=${onlyEditors.join(',')}`)
  console.error(`  available: ${TARGETS.map(([k]) => k).join(', ')}`)
  process.exit(2)
}

console.log(`symbols-mcp init-rules`)
console.log(`Project: ${PROJECT}`)
console.log(`Mode:    ${flagList ? 'list (no writes)' : (flagForce ? 'force overwrite' : 'idempotent (skip existing)')}`)
console.log()

let wrote = 0
let skipped = 0
let listed = 0

for (const [editor, src, dst] of filtered) {
  const srcPath = path.join(TEMPLATES_DIR, src)
  const dstPath = path.join(PROJECT, dst)

  if (!fs.existsSync(srcPath)) {
    console.error(`  ✗ template missing: ${src} (this is a packaging bug)`)
    continue
  }

  if (flagList) {
    const exists = fs.existsSync(dstPath)
    console.log(`  [${editor.padEnd(8)}] ${dst} ${exists ? '(EXISTS — would skip)' : '(would write)'}`)
    listed++
    continue
  }

  if (fs.existsSync(dstPath) && !flagForce) {
    console.log(`  [${editor.padEnd(8)}] ${dst}  SKIP (exists; use --force to overwrite)`)
    skipped++
    continue
  }

  fs.mkdirSync(path.dirname(dstPath), { recursive: true })
  fs.copyFileSync(srcPath, dstPath)
  console.log(`  [${editor.padEnd(8)}] ${dst}  ✓ written`)
  wrote++
}

// Install Claude Code hooks (project-level by default; user-global with --global)
const installHooks = !flagNoHooks && (!onlyEditors || onlyEditors.includes('claude'))
const HOOK_DEST_ROOT = flagGlobal ? path.join(HOME, '.claude') : path.join(PROJECT, '.claude')

if (installHooks) {
  console.log()
  console.log(`Claude Code hooks (${flagGlobal ? 'user-global at ~/.claude/' : 'project-level at .claude/'}):`)
  const HOOK_FILES = [
    'settings.json',
    'README.md',
    'hooks/README.md',
    'hooks/symbols-mcp-require.sh',
    'hooks/symbols-mcp-reminder.sh',
    'hooks/symbols-mcp-audit.sh',
  ]
  // Build the hooks block we'd inject (used for global merge AND project-level write)
  const HOOKS_BLOCK = {
    PreToolUse: [{
      matcher: 'Edit|Write|MultiEdit',
      hooks: [{ type: 'command', command: 'bash $CLAUDE_PROJECT_DIR/.claude/hooks/symbols-mcp-require.sh' }]
    }],
    UserPromptSubmit: [{
      hooks: [{ type: 'command', command: 'bash $CLAUDE_PROJECT_DIR/.claude/hooks/symbols-mcp-reminder.sh' }]
    }],
    PostToolUse: [{
      matcher: 'Edit|Write|MultiEdit',
      hooks: [{ type: 'command', command: 'bash $CLAUDE_PROJECT_DIR/.claude/hooks/symbols-mcp-audit.sh' }]
    }]
  }
  // For --global mode, swap $CLAUDE_PROJECT_DIR for absolute ~/.claude path so hooks
  // resolve regardless of cwd (Claude Code only sets $CLAUDE_PROJECT_DIR for project hooks).
  const swapForGlobal = (cmd) => cmd.replace('$CLAUDE_PROJECT_DIR/.claude/', `${path.join(HOME, '.claude')}/`)
  if (flagGlobal) {
    for (const ev of Object.keys(HOOKS_BLOCK)) {
      for (const e of HOOKS_BLOCK[ev]) for (const h of e.hooks) h.command = swapForGlobal(h.command)
    }
  }

  for (const rel of HOOK_FILES) {
    const srcPath = path.join(TEMPLATES_DIR, '.claude', rel)
    const dstPath = path.join(HOOK_DEST_ROOT, rel)
    if (!fs.existsSync(srcPath)) {
      console.error(`  ✗ template missing: .claude/${rel} (this is a packaging bug)`)
      continue
    }
    const dstRel = flagGlobal ? path.relative(HOME, dstPath) : path.relative(PROJECT, dstPath)
    const dstLabel = (flagGlobal ? '~/' : '') + dstRel

    // Special-case settings.json under --global: MERGE the hooks block into existing file
    // so we don't clobber MCP server config, plugins, env, etc.
    if (flagGlobal && rel === 'settings.json' && fs.existsSync(dstPath)) {
      if (flagList) {
        console.log(`  [hook    ] ${dstLabel} (EXISTS — would MERGE hooks block)`)
        continue
      }
      try {
        const existing = JSON.parse(fs.readFileSync(dstPath, 'utf8'))
        existing.hooks = existing.hooks || {}
        // Idempotent: replace the symbols-mcp-* triplet but preserve any other hooks
        const isOurHook = (h) => (h.hooks || []).some(x => /symbols-mcp-(require|reminder|audit)\.sh/.test(x.command || ''))
        for (const ev of Object.keys(HOOKS_BLOCK)) {
          existing.hooks[ev] = (existing.hooks[ev] || []).filter(e => !isOurHook(e))
          existing.hooks[ev].push(...HOOKS_BLOCK[ev])
        }
        // Backup before writing
        const backupPath = dstPath + '.backup-' + Date.now()
        fs.copyFileSync(dstPath, backupPath)
        fs.writeFileSync(dstPath, JSON.stringify(existing, null, 2) + '\n')
        console.log(`  [hook    ] ${dstLabel}  ✓ MERGED (backup: ${path.relative(HOME, backupPath)})`)
        wrote++
        continue
      } catch (e) {
        console.error(`  [hook    ] ${dstLabel}  ✗ merge failed: ${e.message}`)
        console.error(`     manual fix: copy hooks block from ${srcPath}`)
        continue
      }
    }

    if (flagList) {
      const exists = fs.existsSync(dstPath)
      console.log(`  [hook    ] ${dstLabel} ${exists ? '(EXISTS — would skip)' : '(would write)'}`)
      continue
    }
    if (fs.existsSync(dstPath) && !flagForce) {
      console.log(`  [hook    ] ${dstLabel}  SKIP (exists; use --force to overwrite)`)
      skipped++
      continue
    }
    fs.mkdirSync(path.dirname(dstPath), { recursive: true })
    fs.copyFileSync(srcPath, dstPath)
    if (rel.endsWith('.sh')) fs.chmodSync(dstPath, 0o755)
    console.log(`  [hook    ] ${dstLabel}  ✓ written`)
    wrote++
  }

  if (flagGlobal && !flagList) {
    console.log()
    console.log(`Note: user-global hooks at ~/.claude/ apply to ALL Claude Code projects.`)
    console.log(`The hooks self-detect a Symbols project (walk up for symbols.json) and`)
    console.log(`no-op everywhere else, so this is safe even on non-Symbols repos.`)
    console.log(`Existing ~/.claude/settings.json was MERGED, not overwritten — your other`)
    console.log(`config (MCP servers, plugins, env vars) is preserved. A timestamped backup`)
    console.log(`was saved alongside.`)
  }
}

// Install the Claude Code `symbols` agent skill (project-level by default;
// user-global with --global). Skills auto-load when the agent decides the
// task matches the skill's description — the Symbols skill triggers on any
// work inside a symbols.json project, so the rules surface without prompts.
const installSkills = !flagNoSkills && (!onlyEditors || onlyEditors.includes('claude'))

if (installSkills) {
  console.log()
  console.log(`Claude Code skill (${flagGlobal ? 'user-global at ~/.claude/skills/' : 'project-level at .claude/skills/'}):`)
  const SKILLS_SRC_DIR = path.join(__dirname, '..', 'templates', 'skills')
  const SKILL_DEST_ROOT = flagGlobal ? path.join(HOME, '.claude', 'skills') : path.join(PROJECT, '.claude', 'skills')
  const skillDirs = fs.existsSync(SKILLS_SRC_DIR)
    ? fs.readdirSync(SKILLS_SRC_DIR).filter(d => fs.existsSync(path.join(SKILLS_SRC_DIR, d, 'SKILL.md')))
    : []
  if (!skillDirs.length) {
    console.error(`  ✗ no skill templates found under templates/skills/ (this is a packaging bug)`)
  }
  for (const skill of skillDirs) {
    const srcPath = path.join(SKILLS_SRC_DIR, skill, 'SKILL.md')
    const dstPath = path.join(SKILL_DEST_ROOT, skill, 'SKILL.md')
    const dstLabel = (flagGlobal ? '~/' + path.relative(HOME, dstPath) : path.relative(PROJECT, dstPath))
    if (flagList) {
      const exists = fs.existsSync(dstPath)
      console.log(`  [skill   ] ${dstLabel} ${exists ? '(EXISTS — would skip)' : '(would write)'}`)
      listed++
      continue
    }
    if (fs.existsSync(dstPath) && !flagForce) {
      console.log(`  [skill   ] ${dstLabel}  SKIP (exists; use --force to overwrite)`)
      skipped++
      continue
    }
    fs.mkdirSync(path.dirname(dstPath), { recursive: true })
    fs.copyFileSync(srcPath, dstPath)
    console.log(`  [skill   ] ${dstLabel}  ✓ written`)
    wrote++
  }
}

console.log()
if (flagList) {
  console.log(`Listed ${listed} target(s). Run without --list to write.`)
} else {
  console.log(`Wrote ${wrote}, skipped ${skipped}.`)
  if (skipped > 0) console.log(`Pass --force to overwrite skipped files.`)
}

console.log()
console.log(`Next: open this project in your editor — it will auto-load the rules.`)
if (installSkills && !flagList) {
  console.log(`Claude Code skill installed: the \`symbols\` skill auto-loads on Symbols/DOMQL work.`)
}
if (installHooks && !flagList) {
  console.log(`Claude Code hooks installed (${flagGlobal ? 'user-global' : 'project-level'}):`)
  console.log(`  • PreToolUse  blocks Edit/Write on *.js until get_project_rules is called`)
  console.log(`  • UserPromptSubmit  injects the symbols-mcp MUST-DO sequence per turn`)
  console.log(`  • PostToolUse  runs frank-audit + FA-rule check after every JS edit`)
  console.log(`  Disable individually: SYMBOLS_MCP_REQUIRE_RULES=0 / SYMBOLS_MCP_REMINDER=0 / SYMBOLS_MCP_POST_AUDIT=0`)
  if (!flagGlobal) console.log(`  Or run with --global to install once for ALL Symbols projects.`)
}
console.log(`No more 'use symbols-mcp' reminders.`)
