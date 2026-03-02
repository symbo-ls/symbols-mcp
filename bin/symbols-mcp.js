#!/usr/bin/env node
'use strict'
const fs = require('fs')
const path = require('path')
const readline = require('readline')

const SKILLS_DIR = path.join(__dirname, '..', 'symbols_mcp', 'skills')

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

const TOOLS = [
  {
    name: 'get_project_rules',
    description: 'ALWAYS call this first before any generate_* tool. Returns the mandatory Symbols.app rules that MUST be followed. Violations cause silent failures — black page, nothing renders.',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'search_symbols_docs',
    description: 'Search the Symbols documentation knowledge base for relevant information.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Natural language search query about Symbols/DOMQL' },
        max_results: { type: 'number', description: 'Maximum number of results (1-5)', default: 3 }
      },
      required: ['query']
    }
  }
]

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n')
}

function handle(req) {
  if (!req.method) return
  if (req.method === 'initialize') {
    return send({
      jsonrpc: '2.0', id: req.id,
      result: {
        protocolVersion: req.params?.protocolVersion ?? '2025-03-26',
        capabilities: { tools: {} },
        serverInfo: { name: 'Symbols MCP', version: '1.0.6' }
      }
    })
  }
  if (req.method === 'notifications/initialized') return
  if (req.method === 'ping') return send({ jsonrpc: '2.0', id: req.id, result: {} })
  if (req.method === 'tools/list') return send({ jsonrpc: '2.0', id: req.id, result: { tools: TOOLS } })
  if (req.method === 'tools/call') {
    const { name, arguments: args = {} } = req.params
    try {
      let text
      if (name === 'get_project_rules') text = loadAgentInstructions()
      else if (name === 'search_symbols_docs') text = searchDocs(args.query, args.max_results || 3)
      else throw new Error(`Unknown tool: ${name}`)
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
  try { handle(JSON.parse(line)) } catch (e) { process.stderr.write(`Parse error: ${e.message}\n`) }
})
rl.on('close', () => process.exit(0))
