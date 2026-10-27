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
//   Rule 66  a nested element with a sibling, gated by an `if:` that reads
//            state, and not out of the flow (its own position absolute /
//            fixed, or an out-of-flow built-in) — `if:` adds and removes the
//            node, so its siblings move. Two in-place swaps are skipped: a
//            run of 2–6 adjacent gated siblings of which exactly one shows
//            in every case (P), and an empty note beside the list it stands
//            for (E) — see "Rule 66 swaps" below.
//
// Allow comments, as frank-audit reads them: `// frank-allow FA810` …
// `FA813` above a line (or after code on it) allows that rule there;
// `// frank-allow-block FA813: <why>` above an element (or its `export`)
// allows FA813 on its direct children. An FA813 allow that covers no
// finding is reported (`kind`: unused-allow / invalid-allow).
//
// One implementation serves both servers: bin/symbols-mcp.cjs requires it,
// symbols_mcp/server.py runs it with `node structural.cjs` (code on stdin,
// JSON on stdout). Every finding is a warning. frank-audit (FA810–FA813)
// makes the same decisions; its agreement tests (FA810-FA812-structural,
// FA813-mcp-agreement) compare the two readers case by case.
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
// Built-ins whose own root is `position: 'fixed'` or `'absolute'` — out of
// the flow, so an `if:` on one moves nothing (Rule 66). default-config:
// Dropdown, TooltipHidden, TooltipLayer; @symbo.ls/windows: ModalLayer,
// ModalRoot; @symbo.ls/dropdown: DropdownRoot; @symbo.ls/tooltip: TooltipRoot.
const OUT_OF_FLOW = new Set([
  'Dropdown', 'TooltipHidden', 'TooltipLayer', 'ModalLayer', 'ModalRoot', 'DropdownRoot', 'TooltipRoot'
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

// Tokens are { type, value, start, end } (offsets into src); the comments
// are kept on `toks.comments` as { start, end, text, prev } — `prev` is the
// index of the token before the comment (-1 at the start).
function tokenize (src) {
  const toks = []
  const comments = []
  let i = 0
  const n = src.length
  const push = (type, value, start, end) => toks.push({ type, value, start, end: end === undefined ? i : end })
  while (i < n) {
    const c = src[i]
    if (c === ' ' || c === '\t' || c === '\n' || c === '\r') { i++; continue }
    if (c === '/' && src[i + 1] === '/') {
      const start = i
      while (i < n && src[i] !== '\n') i++
      comments.push({ start, end: i, text: src.slice(start + 2, i), prev: toks.length - 1 })
      continue
    }
    if (c === '/' && src[i + 1] === '*') {
      const start = i
      const e = src.indexOf('*/', i + 2)
      i = e < 0 ? n : e + 2
      comments.push({ start, end: i, text: src.slice(start + 2, e < 0 ? n : e), prev: toks.length - 1 })
      continue
    }
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
    if (PUNCT3.includes(three)) { push('punct', three, i, i + 3); i += 3; continue }
    // `?.` followed by a digit is a ternary `? .5`
    if (PUNCT2.includes(two) && !(two === '?.' && /[0-9]/.test(src[i + 2] || ''))) { push('punct', two, i, i + 2); i += 2; continue }
    push('punct', c, i, i + 1)
    i++
  }
  toks.comments = comments
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

// Every export: `export default { … }` and `export const Name = …` — `node`
// is the object literal (null for any other value), `at` the `export` token.
function roots (toks) {
  const out = []
  for (let i = 0; i < toks.length - 3; i++) {
    const t = toks[i]
    // export const Name = {      export default {
    if (t.type === 'ident' && t.value === 'export') {
      const a = toks[i + 1]
      if (a && a.value === 'default' && toks[i + 2] && toks[i + 2].value === '{') {
        out.push({ name: 'default', node: parseObject(toks, i + 2), at: i })
      } else if (a && (a.value === 'const' || a.value === 'let' || a.value === 'var') &&
        toks[i + 2] && toks[i + 2].type === 'ident' && toks[i + 3] && toks[i + 3].value === '=') {
        const isObject = toks[i + 4] && toks[i + 4].value === '{'
        out.push({ name: toks[i + 2].value, node: isObject ? parseObject(toks, i + 4) : null, at: i })
      }
    }
  }
  return out
}

// ── helpers ──────────────────────────────────────────────────────────────
// The 1-based line of an offset (the line starts of the last source, cached).
let lineSrc = null
let lineStarts = null
const lineOf = (src, offset) => {
  if (src !== lineSrc) {
    lineSrc = src
    lineStarts = [0]
    for (let i = 0; i < src.length; i++) if (src[i] === '\n') lineStarts.push(i + 1)
  }
  let lo = 0
  let hi = lineStarts.length - 1
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1
    if (lineStarts[mid] <= offset) lo = mid
    else hi = mid - 1
  }
  return lo + 1
}
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

// Does an `if:` value read STATE — so it can change after the first render?
// `(el, s) => …s…` (the second parameter used, or destructured), `({ state })
// => …`, or any `….state` read. A gate on props or the element alone
// (`(el) => !!el.icon`) is decided when the element is created: no shift.
function readsState (toks, from, to) {
  let j = from
  if (toks[j] && toks[j].value === 'async') j++
  if (toks[j] && toks[j].value === 'function') {
    j++
    if (toks[j] && toks[j].type === 'ident') j++
  }
  const params = []
  if (toks[j] && toks[j].value === '(') {
    const close = matchClose(toks, j)
    let cur = []
    for (let k = j + 1; k < close; k++) {
      const tk = toks[k]
      if (tk.type === 'punct' && OPEN[tk.value]) {
        const c = matchClose(toks, k)
        for (let q = k; q <= c; q++) cur.push(toks[q])
        k = c
        continue
      }
      if (tk.type === 'punct' && tk.value === ',') { params.push(cur); cur = []; continue }
      cur.push(tk)
    }
    if (cur.length) params.push(cur)
    j = close + 1
  } else if (toks[j] && toks[j].type === 'ident' && toks[j + 1] && toks[j + 1].value === '=>') {
    params.push([toks[j]])
    j++
  } else return false
  if (toks[j] && toks[j].value === '=>') j++
  const [first, second] = params
  // ({ state }) => …
  if (first && first[0] && first[0].value === '{') {
    for (let k = 1; k < first.length; k++) {
      if (first[k].type === 'ident' && first[k].value === 'state' && (first[k - 1].value === '{' || first[k - 1].value === ',')) return true
    }
  }
  // (el, { query }) => …: the state, destructured
  if (second && second[0] && (second[0].value === '{' || second[0].value === '[')) return true
  const name = second && second[0] && second[0].type === 'ident' ? second[0].value : null
  for (let k = j; k < to; k++) {
    const tk = toks[k]
    if (tk.type !== 'ident') continue
    const member = toks[k - 1] && (toks[k - 1].value === '.' || toks[k - 1].value === '?.')
    if (member) {
      if (tk.value === 'state') return true
    } else if (name && tk.value === name) return true
  }
  return false
}

// Is this element out of the flow? Its own `position` is 'absolute' / 'fixed'
// — or not a plain string, which one file cannot judge — or it is built from
// an out-of-flow built-in.
function outOfFlow (toks, m, from) {
  if ([...from].some((n) => OUT_OF_FLOW.has(n))) return true
  const position = m.get('position')
  if (!position) return false
  if (position.to - position.from !== 1 || toks[position.from].type !== 'string') return true
  return /^(absolute|fixed)$/.test(toks[position.from].value.trim().toLowerCase())
}

const isCssKey = (key) => {
  const k = String(key)
  if (!/^[a-z]/.test(k)) return false // children, ':hover', '@media', '.isX', '--x', '&…'
  if (k.includes('-')) return false // attributes (aria-*, data-*)
  if (/^on[A-Z]/.test(k) || /^(is|has|use|aria)[A-Z]/.test(k)) return false
  return !NON_CSS.has(k)
}

// ── Rule 66 swaps (frank-audit swaps.js, read from tokens) ──────────────
// An `if:` that swaps one thing for another IN PLACE moves nothing that
// stays on screen:
//
//   P  the gated element sits in a run of 2–6 adjacent in-flow PascalCase
//      siblings, each gated by a one-expression `if:`, and in every case
//      exactly one of the run shows (a loading view and its content);
//   E  its gate says "array X is empty" (`!X.length`, `X.length === 0`,
//      `!(X || []).length`) and the adjacent in-flow sibling — or a
//      descendant of it, up to four levels down — renders its `children`
//      from that same X (an empty note beside its list).
//
// "At most one of the two shows" is NOT skipped: a status line that goes
// blank is Rule 66's own case. A gate is an AND of atoms on SUBJECTS — an
// expression's text with the parameters renamed by position ($el, $s,
// $ctx; a destructured `{ state }` is $s, `{ parent }` $el.parent, any
// other destructured name the element's own $el.<name>), `?.` read as `.`.
// A subject that reads the element itself ($el, except $el.parent…) differs
// between siblings: the run is refused. So is a member whose base sets a
// `state:` of its own (then its `s` is another state): the bases come from
// the components this file exports and the framework's (the lists below).

const MAX_CASES = 50000
const OTHER_TRUTHY = { other: true }
const OTHER_FALSY = { other: false }

// The framework tier of frank-audit's component registry: default-config's
// built-ins and the windows / dropdown / tooltip plugin components; and the
// ones whose definition, or a base, sets `state:`. frank-audit's FA813 test
// pins both lists to its runtime tables.
const FRAMEWORK_COMPONENTS = new Set([
  'A', 'AlertTemplate', 'AssetPicture', 'Audio', 'Avatar', 'B', 'Block', 'Box', 'Br', 'Bridge',
  'Button', 'ButtonSet', 'CancelButton', 'Caption', 'Checkbox', 'CheckboxHgroup', 'Circle',
  'CircleButton', 'Clickable', 'ConfirmTemplate', 'CustomTemplate', 'Data', 'Dialog',
  'DialogFooter', 'DialogHeader', 'Dropdown', 'DropdownDisclosure', 'DropdownList',
  'DropdownParent', 'DropdownParentFocus', 'DropdownRoot', 'DropdownSiblingFocus',
  'DropdownTrigger', 'FileIcon', 'Flex', 'Focusable', 'FocusableComponent', 'Footnote', 'Form',
  'Grid', 'Gutter', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'Headline', 'Hgroup', 'HgroupButton',
  'HgroupRows', 'Hoverable', 'Hr', 'I', 'Icon', 'IconButton', 'IconText', 'Iframe', 'Img',
  'Inline', 'InlineFlex', 'InlineGrid', 'Input', 'Italic', 'KangorooButton', 'Li', 'Link',
  'ModalHeader', 'ModalLayer', 'ModalPhoneSheet', 'ModalRoot', 'ModalWindow', 'Notification',
  'NumberInput', 'Ol', 'P', 'Picture',
  'PromptTemplate', 'Radio', 'RadioHgroup', 'Range', 'RouteLink', 'RouterLink', 'Select',
  'Shape', 'Span', 'SquareButton', 'Strong', 'Subhead', 'Svg', 'Text', 'Textarea',
  'TextareaWithButton', 'Theme', 'Title', 'Toggle', 'ToggleHgroup', 'Tooltip', 'TooltipHidden',
  'TooltipLayer', 'TooltipParent', 'TooltipRoot', 'TooltipTrigger', 'U', 'Ul', 'Underline', 'Video'
])
const FRAMEWORK_STATEFUL = new Set(['DropdownRoot', 'ModalRoot', 'TooltipLayer', 'TooltipRoot'])

const CLOSE = new Set([')', ']', '}'])
const isOpen = (tk) => !!tk && tk.type === 'punct' && !!OPEN[tk.value]
const isPunct = (tk, v) => !!tk && tk.type === 'punct' && tk.value === v
const isWord = (tk, v) => !!tk && tk.type === 'ident' && tk.value === v

// [from, to) ranges between the depth-0 commas of toks[from, to); a final
// empty range (a trailing comma) is dropped.
function splitDepth0 (toks, from, to) {
  const out = []
  let at = from
  for (let k = from; k < to; k++) {
    if (isOpen(toks[k])) { k = matchClose(toks, k); continue }
    if (isPunct(toks[k], ',')) { out.push([at, k]); at = k + 1 }
  }
  if (at < to) out.push([at, to])
  return out
}

// ── a small expression parser: nodes { t, from, to } over token ranges ──
// t: id | lit | arr | mem | call | un | bin | log | cond | other. `from` /
// `to` are the node's own tokens (the parentheses around it excluded);
// `ofrom` / `oto` include them, as an enclosing node's range does.
const BINARY = {
  '??': 3, '||': 3, '&&': 4, '|': 5, '^': 6, '&': 7,
  '==': 8, '!=': 8, '===': 8, '!==': 8, '<': 9, '>': 9, '<=': 9, '>=': 9,
  '<<': 10, '>>': 10, '>>>': 10, '+': 11, '-': 11, '*': 12, '/': 12, '%': 12, '**': 13
}
const PREFIX_PUNCT = new Set(['!', '-', '+', '~'])
const PREFIX_WORD = new Set(['typeof', 'void', 'await', 'delete'])

const mk = (node, from, to) => Object.assign(node, { from, to, ofrom: from, oto: to })

function parseRange (toks, from, to) {
  if (from >= to) return null
  const st = { toks, p: from, end: to }
  let node = null
  try { node = parseExpr(st, 0) } catch (e) { return null }
  return node && st.p === to ? node : null
}

function parseExpr (st, minBp) {
  let left = parseUnary(st)
  if (!left) return null
  while (st.p < st.end) {
    const tk = st.toks[st.p]
    if (isPunct(tk, '?')) {
      if (minBp >= 2) break
      st.p++
      const yes = parseExpr(st, 0)
      if (!yes || !isPunct(st.toks[st.p], ':') || st.p >= st.end) return null
      st.p++
      const no = parseExpr(st, 1)
      if (!no) return null
      left = mk({ t: 'cond' }, left.ofrom, no.oto)
      continue
    }
    const bp = tk.type === 'punct' ? BINARY[tk.value] : (isWord(tk, 'in') || isWord(tk, 'instanceof') ? 9 : undefined)
    if (!bp || bp <= minBp) break
    st.p++
    const right = parseExpr(st, tk.value === '**' ? bp - 1 : bp)
    if (!right) return null
    const op = tk.value
    left = mk({ t: op === '&&' || op === '||' || op === '??' ? 'log' : 'bin', op, l: left, r: right }, left.ofrom, right.oto)
  }
  return left
}

function parseUnary (st) {
  const tk = st.toks[st.p]
  if (!tk || st.p >= st.end) return null
  if ((tk.type === 'punct' && PREFIX_PUNCT.has(tk.value)) || (tk.type === 'ident' && PREFIX_WORD.has(tk.value))) {
    const at = st.p++
    const arg = parseUnary(st)
    return arg ? mk({ t: 'un', op: tk.value, arg }, at, arg.oto) : null
  }
  if (isWord(tk, 'new')) {
    const at = st.p++
    const target = parsePostfix(st)
    return target ? mk({ t: 'other' }, at, target.oto) : null
  }
  return parsePostfix(st)
}

// The index of the bracket that closes the one at `i`, inside the range.
function closeIn (st, i) {
  const j = matchClose(st.toks, i)
  return j < st.end && isPunct(st.toks[j], OPEN[st.toks[i].value]) ? j : -1
}

function parseList (toks, from, to) {
  const out = []
  for (const [a, b] of splitDepth0(toks, from, to)) {
    if (a === b) { out.push(null); continue }
    if (isPunct(toks[a], '...')) { out.push(mk({ t: 'other' }, a, b)); continue }
    const n = parseRange(toks, a, b)
    if (!n) return null
    out.push(n)
  }
  return out
}

function parsePostfix (st) {
  let node = parsePrimary(st)
  if (!node) return null
  const from = node.ofrom
  while (st.p < st.end) {
    const tk = st.toks[st.p]
    const nx = st.toks[st.p + 1]
    if (isPunct(tk, '.') || isPunct(tk, '?.')) {
      if (st.p + 1 >= st.end || !nx) return null
      if (nx.type === 'ident') {
        node = mk({ t: 'mem', obj: node, prop: nx.value, computed: false }, from, st.p + 2)
        st.p += 2
        continue
      }
      if (tk.value === '?.' && (isPunct(nx, '(') || isPunct(nx, '['))) { st.p++; continue }
      return null
    }
    if (isPunct(tk, '[')) {
      const close = closeIn(st, st.p)
      const inner = close < 0 ? null : parseRange(st.toks, st.p + 1, close)
      if (!inner) return null
      node = mk({ t: 'mem', obj: node, prop: inner, computed: true }, from, close + 1)
      st.p = close + 1
      continue
    }
    if (isPunct(tk, '(')) {
      const close = closeIn(st, st.p)
      const args = close < 0 ? null : parseList(st.toks, st.p + 1, close)
      if (!args || args.includes(null)) return null
      node = mk({ t: 'call', callee: node, args }, from, close + 1)
      st.p = close + 1
      continue
    }
    if (tk.type === 'template') {
      node = mk({ t: 'other' }, from, st.p + 1)
      st.p++
      continue
    }
    break
  }
  return node
}

// `(…) =>`, `x =>`, `async (…) =>`, `async x =>` at `at`
function arrowAt (st, at) {
  const { toks } = st
  let j = at
  if (isWord(toks[j], 'async') && toks[j + 1] && (toks[j + 1].type === 'ident' || isPunct(toks[j + 1], '('))) j++
  if (toks[j] && toks[j].type === 'ident') return isPunct(toks[j + 1], '=>')
  if (isPunct(toks[j], '(')) {
    const close = matchClose(toks, j)
    return close < st.end && isPunct(toks[close + 1], '=>')
  }
  return false
}

function parsePrimary (st) {
  const { toks } = st
  const at = st.p
  const tk = toks[at]
  if (!tk || at >= st.end) return null
  // an arrow function reaches the end of its slot (an argument, an element)
  if (arrowAt(st, at)) { st.p = st.end; return mk({ t: 'other' }, at, st.end) }
  if (isPunct(tk, '(')) {
    const close = closeIn(st, at)
    const inner = close < 0 ? null : parseRange(toks, at + 1, close)
    if (!inner) return null
    st.p = close + 1
    inner.ofrom = at
    inner.oto = close + 1
    return inner
  }
  if (isPunct(tk, '[')) {
    const close = closeIn(st, at)
    const elements = close < 0 ? null : parseList(toks, at + 1, close)
    if (!elements) return null
    st.p = close + 1
    return mk({ t: 'arr', elements }, at, close + 1)
  }
  if (isPunct(tk, '{')) {
    const close = closeIn(st, at)
    if (close < 0) return null
    st.p = close + 1
    return mk({ t: 'other' }, at, close + 1)
  }
  if (tk.type === 'string') { st.p++; return mk({ t: 'lit', kind: 'string', value: tk.value }, at, at + 1) }
  if (tk.type === 'number') {
    st.p++
    const raw = tk.value.replace(/_/g, '')
    if (/n$/.test(raw)) return mk({ t: 'other' }, at, at + 1) // a BigInt is not a number literal
    return mk({ t: 'lit', kind: 'number', value: Number(raw) }, at, at + 1)
  }
  if (tk.type === 'template' || tk.type === 'regex') { st.p++; return mk({ t: 'other' }, at, at + 1) }
  if (tk.type === 'ident') {
    if (tk.value === 'true' || tk.value === 'false') { st.p++; return mk({ t: 'lit', kind: 'boolean', value: tk.value === 'true' }, at, at + 1) }
    if (tk.value === 'null') { st.p++; return mk({ t: 'lit', kind: 'null', value: null }, at, at + 1) }
    if (tk.value === 'function' || (tk.value === 'async' && isWord(toks[at + 1], 'function'))) {
      let j = tk.value === 'async' ? at + 2 : at + 1
      if (toks[j] && toks[j].type === 'ident') j++
      if (!isPunct(toks[j], '(')) return null
      j = matchClose(toks, j) + 1
      if (!isPunct(toks[j], '{')) return null
      const close = closeIn(st, j)
      if (close < 0) return null
      st.p = close + 1
      return mk({ t: 'other' }, at, close + 1)
    }
    if (tk.value === 'class') return null
    st.p++
    return mk({ t: 'id', name: tk.value }, at, at + 1)
  }
  return null
}

// ── a function value: its parameters and body ──────────────────────────
// `(…) => body`, `x => body`, `async …`, `function [name] (…) { … }`, the
// whole of toks[from, to). → { params: [token ranges], bodyFrom, bodyTo,
// block } or null.
function fnOf (toks, from, to) {
  let j = from
  if (isWord(toks[j], 'async')) j++
  if (isWord(toks[j], 'function')) {
    j++
    if (toks[j] && toks[j].type === 'ident') j++
    if (!isPunct(toks[j], '(')) return null
    const close = matchClose(toks, j)
    const params = splitDepth0(toks, j + 1, close)
    j = close + 1
    if (!isPunct(toks[j], '{') || matchClose(toks, j) !== to - 1) return null
    return { params, bodyFrom: j, bodyTo: to, block: true }
  }
  let params
  if (isPunct(toks[j], '(')) {
    const close = matchClose(toks, j)
    if (close >= to) return null
    params = splitDepth0(toks, j + 1, close)
    j = close + 1
  } else if (toks[j] && toks[j].type === 'ident' && isPunct(toks[j + 1], '=>')) {
    params = [[j, j + 1]]
    j++
  } else return null
  if (!isPunct(toks[j], '=>')) return null
  j++
  if (j >= to) return null
  if (isPunct(toks[j], '{')) return matchClose(toks, j) === to - 1 ? { params, bodyFrom: j, bodyTo: to, block: true } : null
  return { params, bodyFrom: j, bodyTo: to, block: false }
}

// The one expression a function returns, as a node, or null.
function returnedNode (toks, fn) {
  if (!fn.block) return parseRange(toks, fn.bodyFrom, fn.bodyTo)
  const close = fn.bodyTo - 1
  let j = fn.bodyFrom + 1
  if (!isWord(toks[j], 'return')) return null
  j++
  let e = j
  while (e < close) {
    if (isOpen(toks[e])) { e = matchClose(toks, e) + 1; continue }
    if (isPunct(toks[e], ';')) break
    e++
  }
  if (e === j) return null
  if (e < close && !(isPunct(toks[e], ';') && e + 1 === close)) return null
  return parseRange(toks, j, e)
}

const POSITION = ['$el', '$s', '$ctx']
const FIRST_PARAM_NAMES = { state: '$s', parent: '$el.parent', context: '$ctx' }

// name → canonical text, for every parameter a canonical text renames.
function paramNames (toks, fn) {
  const names = new Map()
  fn.params.forEach(([a, b], i) => {
    if (a >= b) return
    const first = toks[a]
    if (first.type === 'ident' && (b - a === 1 || isPunct(toks[a + 1], '='))) {
      names.set(first.value, POSITION[i] || '$' + i)
      return
    }
    if (i > 1 || !isPunct(first, '{')) return
    const close = matchClose(toks, a)
    for (const [p, q] of splitDepth0(toks, a + 1, close)) {
      const key = toks[p]
      if (p >= q || !(key.type === 'ident' || key.type === 'string' || key.type === 'number')) continue
      let local = null
      if (q - p === 1 || isPunct(toks[p + 1], '=')) local = key.type === 'ident' ? key.value : null
      else if (isPunct(toks[p + 1], ':') && toks[p + 2] && toks[p + 2].type === 'ident' && (q - p === 3 || isPunct(toks[p + 3], '='))) local = toks[p + 2].value
      if (!local) continue
      names.set(local, i === 1 ? '$s.' + key.value : (FIRST_PARAM_NAMES[key.value] || '$el.' + key.value))
    }
  })
  return names
}

// Whitespace removed, except one space between two word characters (the
// space a minifier keeps: `return $s.rows`).
function squeeze (text) {
  return text.replace(/\s+/g, (gap, at, all) => (/[\w$]/.test(all[at - 1] || '') && /[\w$]/.test(all[at + gap.length] || '') ? ' ' : ''))
}

// The canonical text of toks[from, to): the source with the parameters
// renamed (not a member property, not an object key), `?.` read as `.`.
function canonRange (src, toks, from, to, names) {
  if (from >= to) return ''
  let out = ''
  let at = toks[from].start
  const stack = []
  for (let k = from; k < to; k++) {
    const tk = toks[k]
    if (tk.type === 'punct') {
      if (OPEN[tk.value]) stack.push(tk.value)
      else if (CLOSE.has(tk.value)) stack.pop()
      continue
    }
    if (tk.type !== 'ident') continue
    const text = names.get(tk.value)
    if (!text) continue
    const prev = toks[k - 1]
    if (isPunct(prev, '.') || isPunct(prev, '?.')) continue
    if (stack[stack.length - 1] === '{' && (isPunct(prev, '{') || isPunct(prev, ',')) && isPunct(toks[k + 1], ':')) continue
    out += src.slice(at, tk.start) + text
    at = tk.end
  }
  out += src.slice(at, toks[to - 1].end)
  return squeeze(out).replace(/\?\./g, '.')
}

const readsOwnElement = (text) => /\$el(?!\.parent\b)/.test(text)
const isLit = (n) => !!n && n.t === 'lit'
const countSubject = (text) => /\.(length|size)$/.test(text)
const EQUALITY = new Set(['===', '==', '!==', '!='])

// A gate's body as an AND of atoms (frank-audit atomsOf).
function atomsOf (n, g, neg = false) {
  const canon = (node) => canonRange(g.src, g.toks, node.from, node.to, g.names)
  if (n.t === 'log' && n.op === '&&' && !neg) return [...atomsOf(n.l, g), ...atomsOf(n.r, g)]
  if (n.t === 'un' && n.op === '!') {
    const inner = n.arg
    if (inner.t === 'un' && inner.op === '!') return atomsOf(inner.arg, g, neg)
    return atomsOf(inner, g, !neg)
  }
  if (n.t === 'call' && n.callee.t === 'id' && n.callee.name === 'Boolean' && n.args.length === 1) return atomsOf(n.args[0], g, neg)
  if (n.t === 'bin' && EQUALITY.has(n.op)) {
    const positive = n.op === '===' || n.op === '=='
    const loose = n.op.length === 2
    // [lits].indexOf(x) !== -1 / === -1
    const idx = (side, other) => side.t === 'call' && side.callee.t === 'mem' && !side.callee.computed &&
      side.callee.prop === 'indexOf' && side.callee.obj.t === 'arr' && side.callee.obj.elements.every(isLit) &&
      side.args.length === 1 && other.t === 'un' && other.op === '-' && other.arg.t === 'lit' && other.arg.kind === 'number' && other.arg.value === 1
    if (idx(n.l, n.r) || idx(n.r, n.l)) {
      const call = idx(n.l, n.r) ? n.l : n.r
      const isIn = !positive
      return [{ k: (isIn !== neg) ? 'in' : 'nin', x: canon(call.args[0]), set: call.callee.obj.elements.map((e) => e.value) }]
    }
    const litSide = isLit(n.r) ? n.r : isLit(n.l) ? n.l : null
    const other = litSide === n.r ? n.l : n.r
    if (litSide) {
      const x = canon(other)
      if (loose && litSide.kind === 'null') return [{ k: (positive !== neg) ? 'in' : 'nin', x, set: [null, undefined] }]
      // a count is a number: a loose comparison with a number is a strict one
      if (!loose || (countSubject(x) && litSide.kind === 'number')) return [{ k: (positive !== neg) ? 'eq' : 'neq', x, v: litSide.value }]
    }
  }
  if (n.t === 'bin' && (n.op === '>' || n.op === '>=') && n.r.t === 'lit' && n.r.kind === 'number') {
    const x = canon(n.l)
    const positiveCount = (n.op === '>' && n.r.value === 0) || (n.op === '>=' && n.r.value === 1)
    if (positiveCount && countSubject(x)) return [{ k: neg ? 'falsy' : 'truthy', x }]
  }
  if (n.t === 'call' && n.callee.t === 'mem' && !n.callee.computed && n.callee.prop === 'includes' &&
      n.callee.obj.t === 'arr' && n.callee.obj.elements.every(isLit) && n.args.length === 1) {
    return [{ k: neg ? 'nin' : 'in', x: canon(n.args[0]), set: n.callee.obj.elements.map((e) => e.value) }]
  }
  if (n.t === 'log' && n.op === '||' && !neg) {
    // x === a || x === b → in(x, { a, b })
    const parts = []
    const flat = (p) => { if (p.t === 'log' && p.op === '||') { flat(p.l); flat(p.r) } else parts.push(p) }
    flat(n)
    const as = parts.map((p) => atomsOf(p, g))
    if (as.every((a) => a.length === 1 && a[0].k === 'eq') && new Set(as.map((a) => a[0].x)).size === 1) {
      return [{ k: 'in', x: as[0][0].x, set: as.map((a) => a[0].v) }]
    }
  }
  if (n.t === 'mem' || n.t === 'id' || n.t === 'call' || n.t === 'log') return [{ k: neg ? 'falsy' : 'truthy', x: canon(n) }]
  return [{ k: neg ? 'nop' : 'op', x: canon(n) }]
}

const truth = (val) => (val === OTHER_TRUTHY ? true : val === OTHER_FALSY ? false : !!val)
const isStandIn = (val) => val === OTHER_TRUTHY || val === OTHER_FALSY

function holds (a, val) {
  switch (a.k) {
    case 'eq': return !isStandIn(val) && val === a.v
    case 'neq': return !(!isStandIn(val) && val === a.v)
    case 'in': return !isStandIn(val) && a.set.includes(val)
    case 'nin': return !(!isStandIn(val) && a.set.includes(val))
    case 'truthy': case 'op': return truth(val)
    case 'falsy': case 'nop': return !truth(val)
  }
  return false
}

// The gate of an `if:` entry: its body's atoms, or null (not a function
// with one returned expression).
function gateOf (src, toks, entry) {
  if (entry.gate !== undefined) return entry.gate
  entry.gate = null
  const fn = fnOf(toks, entry.from, entry.to)
  const body = fn && returnedNode(toks, fn)
  if (body) entry.gate = { atoms: atomsOf(body, { src, toks, names: paramNames(toks, fn) }) }
  return entry.gate
}

// Exactly one of the run's gates is true in every case.
function exactlyOne (src, toks, gateEntries) {
  const conj = []
  for (const e of gateEntries) {
    const g = gateOf(src, toks, e)
    if (!g || g.atoms.some((a) => readsOwnElement(a.x))) return false
    conj.push(g.atoms)
  }
  const vars = new Map()
  for (const as of conj) {
    for (const a of as) {
      const v = vars.get(a.x) || { lits: new Set(), valued: false }
      if (a.k === 'eq' || a.k === 'neq') { v.valued = true; v.lits.add(a.v) }
      if (a.k === 'in' || a.k === 'nin') { v.valued = true; for (const x of a.set) v.lits.add(x) }
      vars.set(a.x, v)
    }
  }
  const names = [...vars.keys()]
  const domains = names.map((nm) => {
    const v = vars.get(nm)
    return v.valued ? [...new Set([...v.lits, OTHER_TRUTHY, undefined, OTHER_FALSY])] : [true, false]
  })
  let total = 1
  for (const d of domains) {
    total *= d.length
    if (total > MAX_CASES) return false
  }
  const env = new Map()
  for (let c = 0; c < total; c++) {
    let rest = c
    for (let k = 0; k < names.length; k++) {
      const d = domains[k]
      env.set(names[k], d[rest % d.length])
      rest = Math.floor(rest / d.length)
    }
    let on = 0
    for (const as of conj) if (as.every((a) => holds(a, env.get(a.x)))) on++
    if (on !== 1) return false
  }
  return true
}

// The arrays a gate says are empty.
function emptyRefs (src, toks, entry) {
  const g = gateOf(src, toks, entry)
  if (!g) return []
  const refs = []
  for (const a of g.atoms) {
    const isEmpty = (a.k === 'falsy' && /\.length$/.test(a.x)) || (a.k === 'eq' && a.v === 0 && /\.length$/.test(a.x))
    if (!isEmpty) continue
    let x = a.x.replace(/\.length$/, '')
    const m = x.match(/^\((.*)(\|\||\?\?)\[\]\)$/)
    if (m) x = m[1]
    // the element's own props differ between the two (`el.call` reads the
    // same function with the same arguments: accepted)
    if (/\$el(?!\.parent\b|\.call\()/.test(x)) continue
    refs.push(x)
  }
  return refs
}

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const readsPath = (text, ref) => new RegExp('(^|[^\\w$.])' + escapeRe(ref) + '(?![\\w$])').test(text)

// A value that is one string, or an array of strings: those; else null.
function stringList (toks, from, to) {
  if (to - from === 1 && toks[from].type === 'string') return [toks[from].value]
  if (isPunct(toks[from], '[') && matchClose(toks, from) === to - 1) {
    const out = []
    for (const [a, b] of splitDepth0(toks, from + 1, to - 1)) {
      if (b - a !== 1 || toks[a].type !== 'string') return null
      out.push(toks[a].value)
    }
    return out
  }
  return null
}

// What a member's base check needs: its key and the names its `extends` /
// `extend` give (null when one is not a string; [] when it has none).
function describe (toks, key, node) {
  const m = node ? entryMap(node) : new Map()
  let names = []
  for (const k of ['extends', 'extend']) {
    const v = m.get(k)
    if (!v) continue
    const list = stringList(toks, v.from, v.to)
    if (list === null) { names = null; break }
    names.push(...list)
  }
  return { key: String(key), base: baseName(key), extends: names }
}

// The sibling (or a descendant, up to four levels; one with its own state
// is not entered) renders `children` from `ref` → the element path, or null.
function rendersList (src, toks, entry, ref) {
  const parentRef = /^\$el\.parent\b/.test(ref)
  const visit = (key, node, depth, path) => {
    if (depth > 4) return null
    const m = entryMap(node)
    if (depth > 0 && m.has('state')) return null
    const here = [...path, describe(toks, key, node)]
    const ch = m.get('children')
    if (ch && (!parentRef || depth === 0)) {
      const fn = fnOf(toks, ch.from, ch.to)
      if (fn && readsPath(canonRange(src, toks, fn.bodyFrom, fn.bodyTo, paramNames(toks, fn)), ref)) return here
    }
    for (const e of node.entries) {
      if (!e.child || !isPascal(e.key)) continue
      const found = visit(String(e.key), e.child, depth + 1, here)
      if (found) return found
    }
    return null
  }
  return visit(String(entry.key), entry.child, 0, [])
}

const isFalsyLiteral = (toks, e) => e.to - e.from === 1 && (isWord(toks[e.from], 'null') || isWord(toks[e.from], 'false'))

// The in-place swaps a flagged child could take (frank-audit swapCandidates).
function swapCandidates (src, toks, entries, child, gate) {
  if (entryMap(child.child).has('state')) return []
  const kids = entries.filter((e) => isPascal(e.key) && !isFalsyLiteral(toks, e))
  const flow = kids.filter((e) => e === child || !(e.child && outOfFlow(toks, entryMap(e.child), builtFrom(toks, e.child, String(e.key)))))
  const i = flow.indexOf(child)
  if (i < 0) return []
  const out = []
  const gateEntry = (e) => {
    if (e === child) return gate
    if (!e.child) return null
    const m = entryMap(e.child)
    if (m.has('state')) return null
    return m.get('if') || null
  }
  // P — windows of 2..6 adjacent gated in-flow siblings that hold the child
  for (let len = 2; len <= 6; len++) {
    for (let l = Math.max(0, i - len + 1); l <= i; l++) {
      const win = flow.slice(l, l + len)
      if (win.length !== len) continue
      const gates = win.map(gateEntry)
      if (gates.some((g) => !g)) continue
      if (exactlyOne(src, toks, gates)) out.push({ kind: 'P', members: win.map((e) => describe(toks, e.key, e.child)) })
    }
  }
  // E — the emptied list beside it
  const refs = emptyRefs(src, toks, gate)
  if (refs.length) {
    for (const j of [i - 1, i + 1]) {
      const sib = flow[j]
      if (!sib || !sib.child || entryMap(sib.child).has('state')) continue
      for (const ref of refs) {
        const path = rendersList(src, toks, sib, ref)
        if (path) {
          out.push({ kind: 'E', members: [describe(toks, child.key, child.child), ...path] })
          break
        }
      }
    }
  }
  return out
}

// What the parent hands every child: `childExtends` / `childExtendsRecursive`
// names (null when one is not a string) and whether a `childProps` (or an
// inline childExtends) object sets `state:`.
function childBase (toks, node) {
  const m = entryMap(node)
  let names = []
  let ownState = false
  for (const k of ['childExtends', 'childExtendsRecursive', 'childProps']) {
    const v = m.get(k)
    if (!v) continue
    const parts = isPunct(toks[v.from], '[') && matchClose(toks, v.from) === v.to - 1
      ? splitDepth0(toks, v.from + 1, v.to - 1)
      : [[v.from, v.to]]
    for (const [a, b] of parts) {
      if (b - a === 1 && toks[a].type === 'string' && k !== 'childProps') {
        if (names) names.push(toks[a].value)
      } else if (isPunct(toks[a], '{') && matchClose(toks, a) === b - 1) {
        const obj = parseObject(toks, a)
        if (entryMap(obj).has('state')) ownState = true
        const inner = describe(toks, '', obj).extends
        if (inner === null) names = null
        else if (names) names.push(...inner)
      } else {
        names = null
      }
    }
  }
  return { extends: names, ownState }
}

// The components one file can see (frank-audit componentRegistry, one file):
// what it exports, then the framework's. A key that names neither is a
// plain element.
const AMBIGUOUS = Symbol('ambiguous')
function fileRegistry (toks, exported) {
  const project = new Map()
  for (const x of exported) {
    if (x.name === 'default') continue
    project.set(x.name, project.has(x.name) ? AMBIGUOUS : x.node)
  }
  const tierOf = (name) => (project.has(name) ? 'project' : FRAMEWORK_COMPONENTS.has(name) ? 'framework' : null)
  const anyBase = (names, seen) => {
    if (names === null) return null
    let unknown = false
    for (const name of names) {
      const r = setsState(name, seen)
      if (r === true) return true
      if (r === null) unknown = true
    }
    return unknown ? null : false
  }
  function setsState (name, seen = new Set()) {
    if (seen.has(name)) return false
    seen = new Set(seen).add(name)
    if (project.has(name)) {
      const def = project.get(name)
      if (!def || def === AMBIGUOUS) return null
      if (entryMap(def).has('state')) return true
      return anyBase(describe(toks, name, def).extends, seen)
    }
    if (FRAMEWORK_COMPONENTS.has(name)) return FRAMEWORK_STATEFUL.has(name)
    return null
  }
  function elementSetsState (d) {
    if (!d || d.extends === null) return null
    if (d.extends.length) return anyBase(d.extends, new Set())
    if (!d.base || !/^[A-Z]/.test(d.base)) return false
    if (tierOf(d.base)) return setsState(d.base)
    return false
  }
  // One of the child's swaps holds: no member's base sets a state of its
  // own, and the parent hands its children none.
  function swapped (swaps, handed) {
    if (handed && (handed.ownState || elementSetsState({ key: '', base: '', extends: handed.extends }) !== false)) return false
    return swaps.some((s) => s.members.every((m) => elementSetsState(m) === false))
  }
  return { swapped }
}

// ── allow comments ───────────────────────────────────────────────────────
const PRAGMA_RE = /\bfrank-(?:allow|disable|ignore)\b\s*:?\s*([A-Z]+\d+(?:\s*[,\s]\s*[A-Z]+\d+)*)/i
const BLOCK_RE = /\bfrank-(?:allow|disable|ignore)-block\b\s*:?\s*([A-Z]+\d+(?:\s*[,\s]\s*[A-Z]+\d+)*)(.*)$/is
const RULE_ID = { 'Rule 19': 'FA810', 'Rule 65': 'FA811', 'Rule 68': 'FA812', 'Rule 66': 'FA813' }
const idsOf = (text) => text.split(/[\s,]+/).map((x) => x.trim().toUpperCase()).filter(Boolean)

// Every allow comment: line ones with the line they cover (frank-audit's
// reading of where the parser attaches a comment: after code on its line →
// that line; above a node → the next line; at the end of an empty
// container → none), block ones with the element line they cover.
function allowsOf (src, toks, lineOf) {
  const out = { line: [], block: [] }
  for (const c of toks.comments || []) {
    const start = lineOf(c.start)
    const end = lineOf(Math.max(c.start, c.end - 1))
    const block = c.text.match(BLOCK_RE)
    if (block) {
      const before = src.slice(src.lastIndexOf('\n', c.start - 1) + 1, c.start)
      const reason = block[2].replace(/^\s*[:—–-]?\s*/, '').trim()
      out.block.push({ line: start, covers: before.trim() === '' ? end + 1 : start, ids: idsOf(block[1]), valid: /[\p{L}\p{N}]/u.test(reason) })
      continue
    }
    const m = c.text.match(PRAGMA_RE)
    if (!m) continue
    const prev = toks[c.prev]
    const next = toks[c.prev + 1]
    let covers
    if (prev && lineOf(prev.end - 1) === start && !isOpen(prev)) covers = start
    else if (!next) covers = prev ? start : 0
    else if (next.type === 'punct' && CLOSE.has(next.value)) covers = prev && !isOpen(prev) ? start : 0
    else covers = end + 1
    out.line.push({ line: start, covers, ids: idsOf(m[1]) })
  }
  return out
}

function applyAllows (src, toks, lineOf, found) {
  const { line, block } = allowsOf(src, toks, lineOf)
  const used = new Set()
  const kept = []
  for (const f of found) {
    const id = RULE_ID[f.rule]
    let allowed = false
    for (const a of line) {
      if (a.covers && a.covers === f.line && a.ids.includes(id)) { used.add(a); allowed = true }
    }
    if (id === 'FA813' && f.parentLine) {
      for (const a of block) {
        if (a.valid && a.covers === f.parentLine && a.ids.includes(id)) { used.add(a); allowed = true }
      }
    }
    if (!allowed) kept.push(f)
  }
  // an FA813 allow that covers no finding (frank-audit reports it too)
  for (const a of line) {
    if (used.has(a) || !a.ids.includes('FA813')) continue
    kept.push({
      line: a.line,
      rule: 'Rule 66',
      kind: 'unused-allow',
      message: `[Rule 66] \`frank-allow FA813\` covers no FA813 finding${a.covers ? ` (line ${a.covers} has none)` : ''} — remove it, or FA813 from it`
    })
  }
  for (const a of block) {
    if (used.has(a) || !a.ids.includes('FA813')) continue
    kept.push(a.valid
      ? { line: a.line, rule: 'Rule 66', kind: 'unused-allow', message: `[Rule 66] \`frank-allow-block FA813\` covers no FA813 finding: no direct child of the element on line ${a.covers} is reported — remove it` }
      : { line: a.line, rule: 'Rule 66', kind: 'invalid-allow', message: '[Rule 66] `frank-allow-block FA813` needs a reason after the rule id (`// frank-allow-block FA813: <why>`) — it allows nothing until it has one' })
  }
  return kept
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
      message: `[Rule 19] ${ctx.label}: the condition \`${cond.replace(/\$(\d)/g, (_, d) => ['el', 's', 'ctx'][d] || 'arg' + d)}\` gates ${es.length} CSS props (${es.map((e) => e.key).join(', ')}) — declare it once as \`isX: (el, s) => …\` and move the values into a \`'.isX'\` / \`'!isX'\` block (frank-audit FA810, opt-in)`
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
      message: `[Rule 65] ${ctx.label}: an interactive element declares ':hover' but no ':active' — declare ':active' (and ':focus-visible') on the same element (frank-audit FA811, opt-in)`
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
        message: `[Rule 68] ${ctx.label}: this ${btn} call site overrides ${over.map((e) => e.key).join(', ')} — keep the control's scale; use a variant on the primitive (its own minHeight + padding) or a design-system token (frank-audit FA812, opt-in)`
      })
    }
  }

  // Rule 66 — a child gated by a state-driven `if:`, in flow beside other
  // children: `if:` adds and removes the node, so its siblings move. An
  // in-place swap (P, E) moves nothing and is skipped; `parentLine` (this
  // element's key or `export` line) is what a block allow above it covers.
  const children = node.entries.filter((e) => e.child && isPascal(e.key))
  if (children.length > 1) {
    let handed = null
    for (const e of children) {
      const cm = entryMap(e.child)
      const gate = cm.get('if')
      if (!gate || !readsState(toks, gate.from, gate.to)) continue
      if (outOfFlow(toks, cm, builtFrom(toks, e.child, String(e.key)))) continue
      if (!handed) handed = childBase(toks, node)
      let swaps = []
      try { swaps = swapCandidates(src, toks, node.entries, e, gate) } catch (err) { swaps = [] }
      if (ctx.registry && ctx.registry.swapped(swaps, handed)) continue
      out.push({
        line: lineOf(src, gate.keyTok.start),
        rule: 'Rule 66',
        parentLine: ctx.line || 0,
        message: `[Rule 66] ${ctx.label} › ${e.key}: \`if:\` adds and removes this element, so the elements beside it move when it toggles — if it is chrome (a button, a count, a status line), keep it mounted and toggle \`visibility\`, \`pointerEvents\`, \`tabindex\` and \`aria.hidden\` instead (frank-audit FA813, opt-in)`
      })
    }
  }

  for (const e of node.entries) {
    if (!e.child) continue
    const k = String(e.key)
    // a CSS block (':hover', '@media', '.isX', '&…') belongs to its element
    const isBlock = /^[:@.!&$>~+*[]/.test(k)
    if (isBlock) continue
    checkNode(src, toks, e.child, { key: k, isRoot: false, label: `${ctx.label} › ${k}`, line: lineOf(src, e.keyTok.start), registry: ctx.registry }, out)
  }
}

function structuralChecks (input) {
  const src = String(input)
  let toks
  try { toks = tokenize(src) } catch (e) { return [] }
  const out = []
  const exported = roots(toks)
  let registry = null
  try { registry = fileRegistry(toks, exported) } catch (e) { registry = null }
  for (const r of exported) {
    if (!r.node) continue
    try {
      checkNode(src, toks, r.node, { key: r.name, isRoot: true, label: r.name, line: lineOf(src, toks[r.at].start), registry }, out)
    } catch (e) { /* an unparsable shape yields no finding */ }
  }
  let kept = out
  try { kept = applyAllows(src, toks, (offset) => lineOf(src, offset), out) } catch (e) { kept = out }
  return kept.map(({ parentLine, ...f }) => f).sort((a, b) => a.line - b.line)
}

module.exports = { structuralChecks, tokenize, FRAMEWORK_COMPONENTS, FRAMEWORK_STATEFUL }

if (require.main === module) {
  let input = ''
  process.stdin.setEncoding('utf8')
  process.stdin.on('data', (d) => { input += d })
  process.stdin.on('end', () => {
    process.stdout.write(JSON.stringify(structuralChecks(input)) + '\n')
  })
}
