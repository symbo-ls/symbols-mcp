'use strict'
// Structural checks for audit_component — the STRICT rules a regex cannot
// see because they are about the SHAPE of a component object:
//
//   Rule 19  one condition repeated across 3+ CSS props of one element
//            (each prop a `(el, s) => cond ? a : b` function) — use isX +
//            '.isX' / '!isX'
//   Rule 65  an interactive element (Link / Button family, `href`,
//            `onClick`, tag a / button) declares ':hover' but no ':active'
//   Rule 68  a call site (a nested element, not the exported definition)
//            of a built-in Button overrides its padding / height
//
// One implementation serves both servers: bin/symbols-mcp.cjs requires it,
// symbols_mcp/server.py runs it with `node structural.cjs` (code on stdin,
// JSON on stdout). Every finding is a warning.
//
// The source is never evaluated. A small tokenizer (strings, templates,
// comments and regex literals handled) feeds a parser that only understands
// object literals in expression position: `export const X = { … }`, and any
// `key: { … }` value inside one. Everything else is skipped as opaque tokens.

const BUTTON_CONTROLS = new Set(['Button', 'IconButton', 'SquareButton', 'CircleButton'])
const INTERACTIVE = new Set(['Link', ...BUTTON_CONTROLS])
const PADDING_HEIGHT = new Set([
  'padding', 'paddingInline', 'paddingBlock', 'paddingTop', 'paddingRight',
  'paddingBottom', 'paddingLeft', 'paddingInlineStart', 'paddingInlineEnd',
  'paddingBlockStart', 'paddingBlockEnd', 'height', 'minHeight'
])
// Keys that are not CSS props, for the Rule 19 count.
const NON_CSS = new Set([
  'text', 'html', 'if', 'show', 'hide', 'children', 'content', 'state', 'attr',
  'data', 'key', 'tag', 'extends', 'childExtends', 'childExtendsRecursive',
  'childProps', 'childrenAs', 'href', 'src', 'srcset', 'value', 'placeholder',
  'role', 'class', 'classlist', 'style', 'vars', 'fetch', 'routes', 'scope',
  'define', 'query', 'title', 'alt', 'name', 'type', 'disabled', 'checked',
  'selected', 'id', 'for', 'target', 'rel', 'aria', 'props', 'context',
  'stateDeps', 'subscribeTo', 'metadata', 'lang', 'dir', 'tabindex', 'tabIndex',
  'icon', 'src', 'label', 'level'
])

// ── tokenizer ────────────────────────────────────────────────────────────
const PUNCT3 = ['...', '===', '!==', '**=', '>>>', '<<=', '>>=', '??=', '||=', '&&=']
const PUNCT2 = ['=>', '==', '!=', '<=', '>=', '&&', '||', '??', '?.', '++', '--', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '**', '<<', '>>']
const REGEX_BEFORE = new Set(['(', ',', '=', ':', '[', '!', '&', '|', '?', '{', '}', ';', '&&', '||', '??', '=>', 'return', 'typeof', '+', '-', '*', '%', '<', '>', '==', '===', '!=', '!==', '<=', '>='])

function tokenize (src) {
  const toks = []
  let i = 0
  const n = src.length
  const push = (type, value, start) => toks.push({ type, value, start })
  while (i < n) {
    const c = src[i]
    if (c === ' ' || c === '\t' || c === '\n' || c === '\r') { i++; continue }
    if (c === '/' && src[i + 1] === '/') { while (i < n && src[i] !== '\n') i++; continue }
    if (c === '/' && src[i + 1] === '*') { const e = src.indexOf('*/', i + 2); i = e < 0 ? n : e + 2; continue }
    if (c === '"' || c === "'") {
      const start = i
      let v = ''
      i++
      while (i < n && src[i] !== c) {
        if (src[i] === '\\') { v += src[i + 1] || ''; i += 2; continue }
        if (src[i] === '\n') break
        v += src[i++]
      }
      i++
      push('string', v, start)
      continue
    }
    if (c === '`') {
      const start = i
      i++
      let depth = 0
      while (i < n) {
        if (src[i] === '\\') { i += 2; continue }
        if (depth === 0 && src[i] === '`') { i++; break }
        if (src[i] === '$' && src[i + 1] === '{') { depth++; i += 2; continue }
        if (depth > 0 && src[i] === '{') depth++
        else if (depth > 0 && src[i] === '}') depth--
        i++
      }
      push('template', src.slice(start, i), start)
      continue
    }
    if (c === '/') {
      const prev = toks[toks.length - 1]
      if (!prev || (prev.type === 'punct' && REGEX_BEFORE.has(prev.value)) || (prev.type === 'ident' && REGEX_BEFORE.has(prev.value))) {
        const start = i
        i++
        let inClass = false
        while (i < n && src[i] !== '\n') {
          if (src[i] === '\\') { i += 2; continue }
          if (src[i] === '[') inClass = true
          else if (src[i] === ']') inClass = false
          else if (src[i] === '/' && !inClass) { i++; break }
          i++
        }
        while (i < n && /[a-z]/i.test(src[i])) i++
        push('regex', src.slice(start, i), start)
        continue
      }
    }
    if (/[A-Za-z_$]/.test(c)) {
      const start = i
      while (i < n && /[\w$]/.test(src[i])) i++
      push('ident', src.slice(start, i), start)
      continue
    }
    if (/[0-9]/.test(c) || (c === '.' && /[0-9]/.test(src[i + 1] || ''))) {
      const start = i
      while (i < n && /[\w.]/.test(src[i])) i++
      push('number', src.slice(start, i), start)
      continue
    }
    const three = src.slice(i, i + 3)
    const two = src.slice(i, i + 2)
    if (PUNCT3.includes(three)) { push('punct', three, i); i += 3; continue }
    // `?.` followed by a digit is a ternary `? .5`
    if (PUNCT2.includes(two) && !(two === '?.' && /[0-9]/.test(src[i + 2] || ''))) { push('punct', two, i); i += 2; continue }
    push('punct', c, i)
    i++
  }
  return toks
}

// ── parser: object literals only ─────────────────────────────────────────
const OPEN = { '(': ')', '[': ']', '{': '}' }

// Index of the token that closes the bracket at `i`.
function matchClose (toks, i) {
  const open = toks[i].value
  const close = OPEN[open]
  let depth = 0
  for (let j = i; j < toks.length; j++) {
    const t = toks[j]
    if (t.type !== 'punct') continue
    if (t.value === open) depth++
    else if (t.value === close && --depth === 0) return j
  }
  return toks.length - 1
}

// Parse the object literal whose `{` is at `i`. Returns a node:
// { start, end, entries: [{ key, keyTok, from, to, child }] }
function parseObject (toks, i) {
  const end = matchClose(toks, i)
  const node = { start: i, end, entries: [] }
  let j = i + 1
  while (j < end) {
    const t = toks[j]
    if (t.type === 'punct' && t.value === ',') { j++; continue }
    if (t.type === 'punct' && t.value === '...') { j = skipValue(toks, j + 1, end); continue }
    let key = null
    const keyTok = t
    if (t.type === 'ident' || t.type === 'string' || t.type === 'number') key = t.value
    else if (t.type === 'punct' && t.value === '[') { j = matchClose(toks, j) + 1 } // computed key
    const next = toks[key !== null ? j + 1 : j]
    if (key !== null) j++
    if (next && next.type === 'punct' && next.value === ':') {
      const from = j + 1
      const to = skipValue(toks, from, end)
      const entry = { key, keyTok, from, to, child: null }
      const v = toks[from]
      if (v && v.type === 'punct' && v.value === '{' && matchClose(toks, from) === to - 1) {
        entry.child = parseObject(toks, from)
      }
      node.entries.push(entry)
      j = to
      continue
    }
    // shorthand `key,` / method `key () {}` / anything else: skip to the next comma
    j = skipValue(toks, j, end)
  }
  return node
}

// The index after the value that starts at `j` (the next depth-0 `,` or `end`).
function skipValue (toks, j, end) {
  while (j < end) {
    const t = toks[j]
    if (t.type === 'punct') {
      if (t.value === ',') return j
      if (OPEN[t.value]) { j = matchClose(toks, j) + 1; continue }
    }
    j++
  }
  return end
}

function roots (toks) {
  const out = []
  for (let i = 0; i < toks.length - 3; i++) {
    const t = toks[i]
    // export const Name = {      export default {
    if (t.type === 'ident' && t.value === 'export') {
      const a = toks[i + 1]
      if (a && a.value === 'default' && toks[i + 2] && toks[i + 2].value === '{') {
        out.push({ name: 'default', node: parseObject(toks, i + 2) })
      } else if (a && (a.value === 'const' || a.value === 'let' || a.value === 'var') &&
        toks[i + 2] && toks[i + 2].type === 'ident' && toks[i + 3] && toks[i + 3].value === '=' &&
        toks[i + 4] && toks[i + 4].value === '{') {
        out.push({ name: toks[i + 2].value, node: parseObject(toks, i + 4) })
      }
    }
  }
  return out
}

// ── helpers ──────────────────────────────────────────────────────────────
const lineOf = (src, offset) => src.slice(0, offset).split('\n').length
const baseName = (key) => String(key).split(/[_.]/)[0]
const isPascal = (key) => /^[A-Z]/.test(String(key))

function entryMap (node) {
  const m = new Map()
  for (const e of node.entries) if (!m.has(e.key)) m.set(e.key, e)
  return m
}

function stringsIn (toks, from, to) {
  const out = []
  for (let k = from; k < to; k++) if (toks[k].type === 'string') out.push(toks[k].value)
  return out
}

// Component names the element is built from: its `extends` strings, plus its
// own key when that key is PascalCase (a bare key auto-extends).
function builtFrom (toks, node, key) {
  const names = new Set()
  const m = entryMap(node)
  const ext = m.get('extends')
  if (ext) for (const s of stringsIn(toks, ext.from, ext.to)) names.add(baseName(s))
  if (key && isPascal(key)) names.add(baseName(key))
  return names
}

// `(el, s) => cond ? a : b`, `el => …`, `function (el, s) { return cond ? … }`
// → the condition, with the parameters renamed by position; else null.
function ternaryCondition (toks, from, to) {
  let j = from
  let params = []
  if (toks[j] && toks[j].value === 'async') j++
  if (toks[j] && toks[j].value === 'function') {
    j++
    if (toks[j] && toks[j].type === 'ident') j++
  }
  if (toks[j] && toks[j].value === '(') {
    const close = matchClose(toks, j)
    for (let k = j + 1; k < close; k++) if (toks[k].type === 'ident') params.push(toks[k].value)
    j = close + 1
  } else if (toks[j] && toks[j].type === 'ident' && toks[j + 1] && toks[j + 1].value === '=>') {
    params = [toks[j].value]
    j++
  } else return null
  if (toks[j] && toks[j].value === '=>') j++
  let bodyFrom = j
  let bodyTo = to
  if (toks[j] && toks[j].value === '{') {
    const close = matchClose(toks, j)
    if (!(toks[j + 1] && toks[j + 1].value === 'return')) return null
    bodyFrom = j + 2
    bodyTo = close
    // a single return statement only
    for (let k = bodyFrom, d = 0; k < bodyTo; k++) {
      const v = toks[k].value
      if (toks[k].type === 'punct' && OPEN[v]) { k = matchClose(toks, k); continue }
      if (v === ';' && d === 0 && k !== bodyTo - 1) return null
    }
  }
  // the depth-0 `?` of the body
  for (let k = bodyFrom; k < bodyTo; k++) {
    const t = toks[k]
    if (t.type === 'punct' && OPEN[t.value]) { k = matchClose(toks, k); continue }
    if (t.type === 'punct' && t.value === '?') {
      if (k === bodyFrom) return null
      const parts = []
      for (let q = bodyFrom; q < k; q++) {
        const p = toks[q]
        const idx = p.type === 'ident' ? params.indexOf(p.value) : -1
        // a parameter read as `.x` is a property name, not the parameter
        const isProp = q > bodyFrom && toks[q - 1].value === '.'
        parts.push(idx >= 0 && !isProp ? '$' + idx : (p.type === 'string' ? JSON.stringify(p.value) : p.value))
      }
      let cond = parts.join(' ').replace(/ ?(\?\.|\.) ?/g, '$1').replace(/\( /g, '(').replace(/ \)/g, ')').replace(/ ([(,])/g, '$1').replace(/^\((.*)\)$/, '$1')
      if (cond.startsWith('!')) cond = cond.replace(/^! /, '!')
      return cond
    }
    if (t.type === 'punct' && (t.value === ',' || t.value === ';')) return null
  }
  return null
}

const isCssKey = (key) => {
  const k = String(key)
  if (!/^[a-z]/.test(k)) return false // children, ':hover', '@media', '.isX', '--x', '&…'
  if (k.includes('-')) return false // attributes (aria-*, data-*)
  if (/^on[A-Z]/.test(k) || /^(is|has|use|aria)[A-Z]/.test(k)) return false
  return !NON_CSS.has(k)
}

// ── checks ───────────────────────────────────────────────────────────────
function checkNode (src, toks, node, ctx, out) {
  const m = entryMap(node)

  // Rule 19 — one condition across 3+ CSS props
  const groups = new Map()
  for (const e of node.entries) {
    if (!isCssKey(e.key)) continue
    const cond = ternaryCondition(toks, e.from, e.to)
    if (!cond) continue
    if (!groups.has(cond)) groups.set(cond, [])
    groups.get(cond).push(e)
  }
  for (const [cond, es] of groups) {
    if (es.length < 3) continue
    out.push({
      line: lineOf(src, es[0].keyTok.start),
      rule: 'Rule 19',
      message: `[Rule 19] ${ctx.label}: the condition \`${cond.replace(/\$(\d)/g, (_, d) => ['el', 's', 'ctx'][d] || 'arg' + d)}\` gates ${es.length} CSS props (${es.map((e) => e.key).join(', ')}) — declare it once as \`isX: (el, s) => …\` and move the values into a \`'.isX'\` / \`'!isX'\` block`
    })
  }

  const from = builtFrom(toks, node, ctx.key)
  const tagEntry = m.get('tag')
  const tag = tagEntry ? stringsIn(toks, tagEntry.from, tagEntry.to)[0] : null

  // Rule 65 — interactive element with ':hover' and no ':active'
  const keys = node.entries.map((e) => String(e.key))
  const hoverKey = node.entries.find((e) => /(^|[&\s,]):hover\b/.test(String(e.key)) && !String(e.key).startsWith('@'))
  const hasActive = keys.some((k) => /:active\b/.test(k))
  // An element that extends a PROJECT component inherits its states from
  // that primitive, which this one file cannot see: only a built-in base
  // (Link, the Button family) or no `extends` at all is judged here.
  const extNames = m.has('extends') ? stringsIn(toks, m.get('extends').from, m.get('extends').to).map(baseName) : []
  const projectBase = extNames.length > 0 && !extNames.some((n) => INTERACTIVE.has(n))
  // A nested PascalCase key with no `extends` may be an instance of a
  // project component (bare key → that component): judged only when the
  // key or its `extends` names a built-in, or it is an exported definition.
  const builtInBase = [...from].some((n) => INTERACTIVE.has(n)) || tag === 'a' || tag === 'button'
  const ownHandler = m.has('href') || m.has('onClick')
  const interactive = !projectBase && (builtInBase || (ownHandler && (ctx.isRoot || !isPascal(ctx.key))))
  if (hoverKey && !hasActive && interactive) {
    out.push({
      line: lineOf(src, hoverKey.keyTok.start),
      rule: 'Rule 65',
      message: `[Rule 65] ${ctx.label}: an interactive element declares ':hover' but no ':active' — declare ':active' (and ':focus-visible') on the same element`
    })
  }

  // Rule 68 — a call site overrides a built-in Button's padding / height
  if (!ctx.isRoot && [...from].some((n) => BUTTON_CONTROLS.has(n))) {
    const over = node.entries.filter((e) => PADDING_HEIGHT.has(String(e.key)))
    if (over.length) {
      const btn = [...from].find((n) => BUTTON_CONTROLS.has(n))
      out.push({
        line: lineOf(src, over[0].keyTok.start),
        rule: 'Rule 68',
        message: `[Rule 68] ${ctx.label}: this ${btn} call site overrides ${over.map((e) => e.key).join(', ')} — keep the control's scale; use a variant on the primitive (its own minHeight + padding) or a design-system token`
      })
    }
  }

  for (const e of node.entries) {
    if (!e.child) continue
    const k = String(e.key)
    // a CSS block (':hover', '@media', '.isX', '&…') belongs to its element
    const isBlock = /^[:@.!&$>~+*[]/.test(k)
    if (isBlock) continue
    checkNode(src, toks, e.child, { key: k, isRoot: false, label: `${ctx.label} › ${k}` }, out)
  }
}

function structuralChecks (src) {
  let toks
  try { toks = tokenize(String(src)) } catch (e) { return [] }
  const out = []
  for (const r of roots(toks)) {
    try {
      checkNode(src, toks, r.node, { key: r.name, isRoot: true, label: r.name }, out)
    } catch (e) { /* an unparsable shape yields no finding */ }
  }
  return out.sort((a, b) => a.line - b.line)
}

module.exports = { structuralChecks, tokenize }

if (require.main === module) {
  let input = ''
  process.stdin.setEncoding('utf8')
  process.stdin.on('data', (d) => { input += d })
  process.stdin.on('end', () => {
    process.stdout.write(JSON.stringify(structuralChecks(input)) + '\n')
  })
}
