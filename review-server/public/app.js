// Symbols MCP review dashboard — frontend logic.
const API = ''
const els = {
  filelist: document.getElementById('filelist'),
  content: document.getElementById('content'),
  filetitle: document.getElementById('filetitle'),
  filemeta: document.getElementById('filemeta'),
  counts: document.getElementById('counts'),
  filter: document.getElementById('filter'),
  prevBtn: document.getElementById('prevBtn'),
  nextBtn: document.getElementById('nextBtn'),
  markedBtn: document.getElementById('markedBtn'),
  exportBtn: document.getElementById('exportBtn'),
  popover: document.getElementById('popover'),
  popQuote: document.getElementById('popQuote'),
  popText: document.getElementById('popText'),
  popCancel: document.getElementById('popCancel'),
  popSave: document.getElementById('popSave'),
  commentlist: document.getElementById('commentlist')
}

const state = {
  files: [],
  current: null,
  rawContent: '',
  comments: [],
  showSource: false,
  filterStatus: 'all'
}

// hljs registration
if (window.hljs) {
  hljs.registerLanguage('javascript', hljs.javascriptlanguage || hljsLangAlias('javascript'))
}
function hljsLangAlias(lang) { return null }

marked.setOptions({
  gfm: true, breaks: false,
  highlight: (code, lang) => {
    try {
      if (window.hljs && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value
      if (window.hljs) return hljs.highlightAuto(code).value
    } catch {}
    return code
  }
})

// ─── API ────────────────────────────────────────────────
async function fetchFiles() {
  const r = await fetch(`${API}/api/files`)
  state.files = await r.json()
}
async function fetchFile(name) {
  const r = await fetch(`${API}/api/files/${encodeURIComponent(name)}`)
  return r.json()
}
async function fetchComments() {
  const r = await fetch(`${API}/api/comments`)
  state.comments = await r.json()
}
async function postComment(payload) {
  const r = await fetch(`${API}/api/comments`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return r.json()
}
async function updateComment(id, patch) {
  const r = await fetch(`${API}/api/comments/${id}`, {
    method: 'PUT', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(patch)
  })
  return r.json()
}
async function deleteComment(id) {
  await fetch(`${API}/api/comments/${id}`, { method: 'DELETE' })
}

// ─── Sidebar / filelist ─────────────────────────────────
function renderFilelist() {
  const q = (els.filter.value || '').toLowerCase().trim()
  const counts = countsByFile()
  els.filelist.innerHTML = ''
  let shown = 0
  for (const f of state.files) {
    if (q && !f.name.toLowerCase().includes(q)) continue
    const div = document.createElement('div')
    div.className = 'item' + (state.current === f.name ? ' active' : '')
    const c = counts[f.name] || 0
    div.innerHTML = `
      <span class="ccount${c ? ' show' : ''}">${c}</span>
      <span class="name">${f.name.replace('.md', '')}</span>
      <span class="sub">${f.lines} lines · ${(f.bytes / 1024).toFixed(1)} KB</span>
    `
    div.onclick = () => loadFile(f.name)
    els.filelist.appendChild(div)
    shown++
  }
  els.counts.textContent = `${shown}/${state.files.length} files · ${state.comments.filter(c => c.status === 'open').length} open comments`
}

function countsByFile() {
  const out = {}
  for (const c of state.comments) {
    if (c.status !== 'open') continue
    out[c.file] = (out[c.file] || 0) + 1
  }
  return out
}

// ─── Content rendering ──────────────────────────────────
async function loadFile(name) {
  state.current = name
  const data = await fetchFile(name)
  state.rawContent = data.content
  renderFilelist()
  els.filetitle.textContent = name
  const fmeta = state.files.find(f => f.name === name)
  els.filemeta.textContent = fmeta ? `${fmeta.lines} lines · ${(fmeta.bytes / 1024).toFixed(1)} KB` : ''
  renderContent()
  history.replaceState(null, '', `#${encodeURIComponent(name)}`)
}

function renderContent() {
  if (!state.rawContent) { els.content.innerHTML = '<p style="color:var(--fg-mute)">Select a file to view.</p>'; return }
  if (state.showSource) {
    els.content.classList.add('source')
    const escaped = escapeHtml(state.rawContent)
    els.content.innerHTML = `<pre class="source-block">${escaped}</pre>`
  } else {
    els.content.classList.remove('source')
    const html = DOMPurify.sanitize(marked.parse(state.rawContent))
    els.content.innerHTML = html
    if (window.hljs) els.content.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b))
  }
  applyHighlights()
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

// Insert comment highlight markers by walking text nodes & matching quote substrings.
function applyHighlights() {
  const fileComments = state.comments.filter(c => c.file === state.current && c.quote)
  if (!fileComments.length) return
  // Walk text nodes
  const walker = document.createTreeWalker(els.content, NodeFilter.SHOW_TEXT, null)
  const nodes = []
  while (walker.nextNode()) nodes.push(walker.currentNode)
  for (const c of fileComments) {
    for (const node of nodes) {
      const text = node.nodeValue
      const idx = text.indexOf(c.quote)
      if (idx === -1) continue
      const before = text.slice(0, idx)
      const match = text.slice(idx, idx + c.quote.length)
      const after = text.slice(idx + c.quote.length)
      const span = document.createElement('span')
      span.className = 'has-comment' + (c.status === 'resolved' ? ' resolved' : '')
      span.dataset.cid = c.id
      span.title = c.comment
      span.textContent = match
      span.onclick = (e) => {
        e.stopPropagation()
        scrollToComment(c.id)
      }
      const parent = node.parentNode
      const frag = document.createDocumentFragment()
      if (before) frag.appendChild(document.createTextNode(before))
      frag.appendChild(span)
      if (after) frag.appendChild(document.createTextNode(after))
      parent.replaceChild(frag, node)
      break
    }
  }
}

// ─── Selection → popover ────────────────────────────────
let popoverPosition = { x: 0, y: 0 }

function onMouseUp() {
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) { hidePopover(); return }
  const range = sel.getRangeAt(0)
  if (!els.content.contains(range.commonAncestorContainer)) { hidePopover(); return }
  const text = sel.toString().trim()
  if (text.length < 3) return
  const rect = range.getBoundingClientRect()
  showPopover(text, rect)
}

function showPopover(quote, rect) {
  els.popover.classList.remove('hidden')
  els.popQuote.textContent = quote.length > 240 ? quote.slice(0, 240) + '…' : quote
  els.popText.value = ''
  // Position
  const x = Math.min(window.innerWidth - 380, rect.left)
  let y = rect.bottom + 8
  if (y + 200 > window.innerHeight) y = rect.top - 220
  els.popover.style.left = x + 'px'
  els.popover.style.top = y + 'px'
  popoverPosition = { quote, fileWhenOpened: state.current }
  setTimeout(() => els.popText.focus(), 50)
}

function hidePopover() {
  els.popover.classList.add('hidden')
  els.popText.value = ''
}

async function savePopover() {
  const quote = popoverPosition.quote
  const file = popoverPosition.fileWhenOpened
  const comment = els.popText.value.trim()
  if (!comment) return
  await postComment({ file, quote, comment })
  hidePopover()
  await fetchComments()
  renderComments()
  renderContent()
  renderFilelist()
}

// ─── Comments panel ────────────────────────────────────
function renderComments() {
  let list = state.comments.slice().reverse()
  if (state.filterStatus !== 'all') list = list.filter(c => c.status === state.filterStatus)
  els.commentlist.innerHTML = ''
  if (!list.length) {
    els.commentlist.innerHTML = '<p style="color:var(--fg-mute);font-size:12px;text-align:center;padding:20px">No comments yet. Select text in any file to add one.</p>'
    return
  }
  for (const c of list) {
    const div = document.createElement('div')
    div.className = 'cm' + (c.status === 'resolved' ? ' resolved' : '')
    div.id = `cm-${c.id}`
    div.innerHTML = `
      <div class="cm-meta">
        <span class="cm-file" data-file="${c.file}">${c.file}</span>
        <span>${new Date(c.createdAt).toLocaleString()}</span>
      </div>
      ${c.quote ? `<div class="cm-quote">${escapeHtml(c.quote)}</div>` : ''}
      <div class="cm-text">${escapeHtml(c.comment)}</div>
      <div class="cm-actions">
        <button class="resolve-btn" data-id="${c.id}">Resolve</button>
        <button class="reopen-btn" data-id="${c.id}">Reopen</button>
        <button class="delete-btn" data-id="${c.id}">Delete</button>
      </div>
    `
    div.querySelector('.cm-file').onclick = () => loadFile(c.file)
    div.querySelector('.resolve-btn').onclick = async () => {
      await updateComment(c.id, { status: 'resolved' })
      await fetchComments(); renderComments(); renderContent(); renderFilelist()
    }
    div.querySelector('.reopen-btn').onclick = async () => {
      await updateComment(c.id, { status: 'open' })
      await fetchComments(); renderComments(); renderContent(); renderFilelist()
    }
    div.querySelector('.delete-btn').onclick = async () => {
      if (!confirm('Delete this comment?')) return
      await deleteComment(c.id)
      await fetchComments(); renderComments(); renderContent(); renderFilelist()
    }
    els.commentlist.appendChild(div)
  }
}

function scrollToComment(id) {
  const el = document.getElementById(`cm-${id}`)
  if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.style.outline = '2px solid var(--accent)'; setTimeout(() => el.style.outline = '', 1200) }
}

// ─── Toolbar / filter chips ─────────────────────────────
document.querySelectorAll('.chip').forEach(chip => {
  chip.onclick = () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'))
    chip.classList.add('active')
    state.filterStatus = chip.dataset.status
    renderComments()
  }
})

els.markedBtn.onclick = () => {
  state.showSource = !state.showSource
  els.markedBtn.textContent = state.showSource ? 'Toggle rendered' : 'Toggle source'
  renderContent()
}

els.exportBtn.onclick = () => {
  const blob = new Blob([JSON.stringify(state.comments, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `symbols-mcp-comments-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

els.filter.oninput = renderFilelist

els.prevBtn.onclick = () => moveFile(-1)
els.nextBtn.onclick = () => moveFile(1)
function moveFile(dir) {
  const idx = state.files.findIndex(f => f.name === state.current)
  const next = state.files[(idx + dir + state.files.length) % state.files.length]
  if (next) loadFile(next.name)
}

document.addEventListener('keydown', (e) => {
  if (els.popover.contains(document.activeElement)) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); savePopover() }
    if (e.key === 'Escape') { e.preventDefault(); hidePopover() }
    return
  }
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  if (e.key === 'j') moveFile(1)
  if (e.key === 'k') moveFile(-1)
  if (e.key === '/') { e.preventDefault(); els.filter.focus() }
  if (e.key === 's') els.markedBtn.click()
})

els.popCancel.onclick = hidePopover
els.popSave.onclick = savePopover
document.addEventListener('mouseup', onMouseUp)
document.addEventListener('mousedown', (e) => {
  if (els.popover.contains(e.target)) return
  // Hide popover only if clicking outside it
  if (!els.popover.classList.contains('hidden')) hidePopover()
})

// ─── Init ──────────────────────────────────────────────
async function init() {
  await fetchFiles()
  await fetchComments()
  const initial = decodeURIComponent((location.hash || '').slice(1)) || (state.files[0]?.name)
  if (initial) await loadFile(initial)
  renderComments()
  renderFilelist()
  // Poll every 5s for fresh comments (so Claude's edits show up)
  setInterval(async () => {
    await fetchComments()
    renderComments()
    renderFilelist()
    // Also refresh content if Claude updated it
    if (state.current) {
      const data = await fetchFile(state.current)
      if (data.content !== state.rawContent) { state.rawContent = data.content; renderContent() }
    }
  }, 5000)
}
init()
