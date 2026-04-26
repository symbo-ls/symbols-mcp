#!/usr/bin/env node
// Lightweight review server for symbols-mcp md files.
// Serves the files at GET /api/files/:name, lists at /api/files,
// accepts comments at POST /api/comments, lists at /api/comments.
// Comments persist to ./comments.json so Claude can read + reply.

import { createServer } from 'node:http'
import { readFile, writeFile, readdir, stat } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { join, dirname, extname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SKILLS_DIR = join(__dirname, '..', 'symbols_mcp', 'skills')
const PUBLIC_DIR = join(__dirname, 'public')
const COMMENTS_FILE = join(__dirname, 'comments.json')
const PORT = process.env.PORT ? Number(process.env.PORT) : 4747

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon'
}

async function readComments() {
  if (!existsSync(COMMENTS_FILE)) return []
  try {
    const raw = await readFile(COMMENTS_FILE, 'utf-8')
    return JSON.parse(raw)
  } catch {
    return []
  }
}

async function writeComments(list) {
  await writeFile(COMMENTS_FILE, JSON.stringify(list, null, 2), 'utf-8')
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'access-control-allow-headers': 'content-type',
    ...headers
  })
  res.end(body)
}

function sendJSON(res, status, obj) {
  send(res, status, JSON.stringify(obj, null, 2), { 'content-type': 'application/json; charset=utf-8' })
}

async function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = []
    req.on('data', (c) => chunks.push(c))
    req.on('end', () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf-8') || '{}')) }
      catch (e) { reject(e) }
    })
    req.on('error', reject)
  })
}

async function listFiles() {
  const entries = await readdir(SKILLS_DIR)
  const out = []
  for (const name of entries) {
    if (!name.endsWith('.md')) continue
    const full = join(SKILLS_DIR, name)
    const st = await stat(full)
    out.push({
      name,
      bytes: st.size,
      lines: (await readFile(full, 'utf-8')).split('\n').length,
      mtime: st.mtimeMs
    })
  }
  return out.sort((a, b) => a.name.localeCompare(b.name))
}

async function serveStatic(res, urlPath) {
  let path = urlPath === '/' ? '/index.html' : urlPath
  if (path.includes('..')) return send(res, 400, 'bad path')
  const full = join(PUBLIC_DIR, path)
  if (!existsSync(full)) return send(res, 404, 'not found')
  const buf = await readFile(full)
  send(res, 200, buf, { 'content-type': MIME[extname(full)] || 'application/octet-stream' })
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`)
  const path = url.pathname

  if (req.method === 'OPTIONS') return send(res, 204, '')

  try {
    if (path === '/api/files') {
      return sendJSON(res, 200, await listFiles())
    }
    if (path.startsWith('/api/files/')) {
      const name = path.slice('/api/files/'.length)
      if (!/^[A-Za-z0-9_.-]+\.md$/.test(name)) return sendJSON(res, 400, { error: 'bad name' })
      const full = join(SKILLS_DIR, name)
      if (!existsSync(full)) return sendJSON(res, 404, { error: 'not found' })
      if (req.method === 'GET') {
        const content = await readFile(full, 'utf-8')
        return sendJSON(res, 200, { name, content })
      }
      return sendJSON(res, 405, { error: 'method not allowed' })
    }
    if (path === '/api/comments') {
      if (req.method === 'GET') {
        return sendJSON(res, 200, await readComments())
      }
      if (req.method === 'POST') {
        const body = await readBody(req)
        const list = await readComments()
        const item = {
          id: `c_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
          file: String(body.file || ''),
          quote: String(body.quote || ''),
          line: Number(body.line || 0),
          comment: String(body.comment || ''),
          status: 'open',
          createdAt: new Date().toISOString(),
          author: 'nika'
        }
        if (!item.file || !item.comment) return sendJSON(res, 400, { error: 'file + comment required' })
        list.push(item)
        await writeComments(list)
        return sendJSON(res, 201, item)
      }
      return sendJSON(res, 405, { error: 'method not allowed' })
    }
    if (path.startsWith('/api/comments/')) {
      const id = path.slice('/api/comments/'.length)
      const list = await readComments()
      const idx = list.findIndex((c) => c.id === id)
      if (idx === -1) return sendJSON(res, 404, { error: 'not found' })
      if (req.method === 'PUT') {
        const body = await readBody(req)
        list[idx] = { ...list[idx], ...body, id, updatedAt: new Date().toISOString() }
        await writeComments(list)
        return sendJSON(res, 200, list[idx])
      }
      if (req.method === 'DELETE') {
        list.splice(idx, 1)
        await writeComments(list)
        return sendJSON(res, 204, '')
      }
      return sendJSON(res, 405, { error: 'method not allowed' })
    }

    return serveStatic(res, path)
  } catch (e) {
    console.error('server error:', e)
    return sendJSON(res, 500, { error: e.message })
  }
})

server.listen(PORT, () => {
  console.log(`\n  📚 symbols-mcp review server`)
  console.log(`     http://localhost:${PORT}\n`)
  console.log(`     skills dir : ${SKILLS_DIR}`)
  console.log(`     comments   : ${COMMENTS_FILE}\n`)
})
