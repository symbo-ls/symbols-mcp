#!/usr/bin/env node
const { spawn } = require('child_process')
const { execSync } = require('child_process')

let cmd, args

try {
  execSync('uvx --version', { stdio: 'ignore' })
  cmd = 'uvx'
  args = ['symbols-mcp']
} catch {
  cmd = 'python3'
  args = ['-m', 'symbols_mcp.server']
}

const child = spawn(cmd, args, { stdio: 'inherit' })
child.on('exit', code => process.exit(code ?? 0))
