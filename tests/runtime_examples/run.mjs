// Runs key documented examples from the skill docs against a BUILT smbls.
//
//   node tests/runtime_examples/run.mjs <smbls-tree>
//
// <smbls-tree> is a checkout of the smbls monorepo with
// packages/smbls/dist/smbls.esm.js built and jsdom installed. Each case pulls
// its code block out of a skill doc by an anchor string (so the test runs the
// text agents read, not a copy), mounts it with smbls create() under jsdom,
// drives state and checks what a browser would apply. Prints one JSON line:
//   { ok, smbls: { version, commit }, cases: [{ name, ok, error? }] }
// and exits 1 when any case fails.

import { readFileSync, existsSync } from 'node:fs'
import { createRequire } from 'node:module'
import { execFileSync } from 'node:child_process'
import { join, resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const SKILLS = process.env.SYMBOLS_MCP_SKILLS_DIR || resolve(HERE, '..', '..', 'symbols_mcp', 'skills')
const tree = resolve(process.argv[2] || '')
const DIST = join(tree, 'packages', 'smbls', 'dist', 'smbls.esm.js')
if (!process.argv[2] || !existsSync(DIST)) {
  console.error(`usage: run.mjs <smbls-tree> (needs ${DIST})`)
  process.exit(2)
}

const version = JSON.parse(readFileSync(join(tree, 'packages', 'smbls', 'package.json'), 'utf8')).version
let commit = null
try { commit = execFileSync('git', ['-C', tree, 'rev-parse', '--short=9', 'HEAD'], { encoding: 'utf8' }).trim() } catch {}

// ── DOM ───────────────────────────────────────────────────────────────────
const { JSDOM } = createRequire(join(tree, 'package.json'))('jsdom')
const dom = new JSDOM('<!doctype html><html><head></head><body></body></html>', {
  url: 'http://localhost/', pretendToBeVisual: true
})
for (const k of ['window', 'document', 'navigator', 'location', 'history', 'HTMLElement',
  'Node', 'Element', 'SVGElement', 'getComputedStyle', 'requestAnimationFrame',
  'cancelAnimationFrame', 'MutationObserver', 'Event', 'CustomEvent',
  'localStorage', 'sessionStorage']) {
  Object.defineProperty(globalThis, k, { value: dom.window[k], configurable: true, writable: true })
}
const { create } = await import(pathToFileURL(DIST).href)

// ── helpers ───────────────────────────────────────────────────────────────
const flush = async () => {
  for (let i = 0; i < 6; i++) await Promise.resolve()
  await new Promise((r) => setTimeout(r, 5))
}

// The ```js block of <file> that contains <anchor>, evaluated: every
// `export const X = …` lands in the returned list as [name, value].
function docExports (file, anchor) {
  const text = readFileSync(join(SKILLS, file), 'utf8')
  const blocks = [...text.matchAll(/```js\n([\s\S]*?)```/g)].map((m) => m[1])
  const hits = blocks.filter((b) => b.includes(anchor))
  if (hits.length !== 1) throw new Error(`${file}: ${hits.length} js blocks contain ${JSON.stringify(anchor)}`)
  const body = hits[0].replace(/^export const (\w+) = /gm, '__d.push(["$1"]); __d[__d.length - 1][1] = ')
  const __d = []
  // eslint-disable-next-line no-new-func
  new Function('__d', body)(__d)
  if (!__d.length) throw new Error(`${file}: block for ${JSON.stringify(anchor)} has no export`)
  return __d
}

const rulesText = () => [...document.head.querySelectorAll('style')]
  .flatMap((s) => [...(s.sheet ? s.sheet.cssRules : [])]).map((r) => r.cssText)
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const ownRules = (node) => {
  const classes = [...node.classList]
  return rulesText().filter((t) => classes.some((c) => new RegExp('\\.' + escapeRe(c) + '(?![\\w-])').test(t))).join('\n')
}

function expect (cond, msg) { if (!cond) throw new Error(msg) }
function eq (actual, expected, what) {
  if (actual !== expected) throw new Error(`${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
}

let n = 0
// The docs' tokens (`primary`, `hairline2`) come from a project design system.
// One document holds every app here and its :root variables come from the
// first app's config, so every app gets the same design system.
const DS = { color: { primary: '#336699' }, sizes: { hairline2: '2px' } }

async function mount (tree, extra = {}) {
  const holder = document.createElement('div')
  document.body.appendChild(holder)
  const app = await create(tree, {
    key: 'example' + (++n), parent: holder, router: false, sync: false, globalTheme: 'auto', designSystem: DS, ...extra
  })
  await flush()
  return app
}

// ── cases ─────────────────────────────────────────────────────────────────
const cases = {
  // SYNTAX: "Reactive grouped CSS via .isX" — the block follows root state,
  // both ways, and its `aria` lands as an attribute.
  async isxRootState () {
    const [[, Item]] = docExports('SYNTAX.md', 'Reactive grouped CSS via .isX')
    const app = await mount({ state: { active: 'Item' }, Item })
    const node = app.Item.node
    eq(node.getAttribute('aria-selected'), 'true', 'active: aria-selected')
    eq(node.style.opacity, '1', 'active: opacity')
    app.state.update({ active: 'Other' })
    await flush()
    eq(node.getAttribute('aria-selected'), null, 'inactive: aria-selected removed')
    expect(node.style.opacity !== '1', `inactive: opacity reverts (got ${node.style.opacity})`)
    app.state.update({ active: 'Item' })
    await flush()
    eq(node.getAttribute('aria-selected'), 'true', 'active again: aria-selected')
  },

  // SYNTAX: "'!isX' for the inverse branch" — exactly one branch applies.
  async isxInverse () {
    const [, [, Item]] = docExports('SYNTAX.md', "'!isX' for the inverse branch")
    const app = await mount({ Item: { ...Item, state: { selectedId: null } } })
    const el = app.Item
    eq(el.node.style.opacity, '0.6', 'not selected: !isSelected opacity')
    el.state.update({ selectedId: 'Item' })
    await flush()
    expect(el.node.style.opacity !== '0.6', `selected: !isSelected reverts (got ${el.node.style.opacity})`)
    expect(/background/.test(ownRules(el.node) + el.node.style.cssText), 'selected: .isSelected background applies')
  },

  // SYNTAX: "CSS Custom Properties — vars and '--x'" (the Gauge example).
  async vars () {
    const [[, Gauge]] = docExports('SYNTAX.md', 'export const Gauge')
    const app = await mount({ state: { done: 1, total: 4, flipped: false }, Gauge })
    const el = app.Gauge
    eq(el.node.tagName, 'DIV', 'example keys are not HTML tag names')
    const st = el.node.style
    eq(st.getPropertyValue('--fill'), '25%', 'factory vars entry inline')
    eq(st.getPropertyValue('--tilt'), '', 'top-level factory returning null sets nothing')
    expect(/--trackOpacity:\s*0\.4/.test(ownRules(el.node)), 'static vars entry compiles into the class')
    app.state.update({ done: 4, flipped: true })
    await flush()
    eq(st.getPropertyValue('--fill'), '100%', 'factory follows state')
    eq(st.getPropertyValue('--tilt'), '180deg', 'top-level factory follows state')
    const track = st.getPropertyValue('--trackOpacity') ||
      ((ownRules(el.node).match(/--trackOpacity:\s*([^;}]+)/g) || []).pop() || '').split(':').pop().trim()
    eq(track, '1', '.isDone block overrides --trackOpacity')
    app.state.update({ flipped: false })
    await flush()
    eq(st.getPropertyValue('--tilt'), '', 'null removes the property')
  },

  // SYNTAX: "onStateUpdate + stateDeps" — fires on a root-state change to the
  // selected key only, never on first render, with { prev, next }.
  async stateDeps () {
    const [[, MessageList]] = docExports('SYNTAX.md', 'export const MessageList')
    const read = []
    const app = await mount(
      { state: { activeChannelId: 'general', unrelated: 0 }, MessageList },
      { functions: { markRead (id) { read.push(id) } } }
    )
    eq(read.length, 0, 'no call on first render')
    app.state.update({ unrelated: 1 })
    await flush()
    eq(read.length, 0, 'no call when another key changes')
    app.state.update({ activeChannelId: 'random' })
    await flush()
    eq(JSON.stringify(read), '["general"]', 'prev[0] passed on change')
    app.state.update({ activeChannelId: 'random' })
    await flush()
    eq(read.length, 1, 'no call when the value is the same')
    expect(!app.MessageList.node.children.length, 'stateDeps renders no child element')
  },

  // SYNTAX lifecycle list: onBeforeUpdate is element-first, and the three
  // reserved names the runtime does not call stay uncalled (when one starts
  // to run, the docs must say so).
  async lifecycleSignatures () {
    const seen = {}
    const app = await mount({
      state: { x: 1 },
      Probe: {
        state: { y: 1 },
        onStateCreated: (el, s, ctx) => { seen.stateCreated = [el.key, typeof s.update, !!ctx] },
        onBeforeUpdate: (el, s, ctx) => { seen.beforeUpdate = [el.key, typeof s.update, !!ctx] },
        onStateInit: () => { seen.stateInit = true },
        onBeforeStateUpdate: () => { seen.beforeStateUpdate = true }
      }
    })
    app.Probe.update({})
    app.Probe.state.update({ y: 2 })
    await flush()
    eq(JSON.stringify(seen.beforeUpdate), '["Probe","function",true]', 'onBeforeUpdate(el, s, ctx)')
    eq(seen.stateInit, undefined, 'onStateInit is not called')
    eq(seen.stateCreated, undefined, 'onStateCreated is not called')
    eq(seen.beforeStateUpdate, undefined, 'onBeforeStateUpdate is not called')
  }
}

// SYNTAX "Which hook runs on which state change", "$settled()", onWindowLoad.
Object.assign(cases, {
  async onUpdateContract () {
    const calls = []
    const log = (name) => (el, s, ctx, opts) => calls.push([name, el.key, opts === undefined ? 'no-opts' : 'opts'])
    const app = await mount({
      state: { tab: 1 },
      Owner: {
        state: { n: 0, flag: false },
        onUpdate: log('owner'),
        Child: { text: (el, s) => String(s.n), onUpdate: log('child') }
      },
      Watcher: {
        subscribeTo: ['tab'],
        onBeforeUpdate: (el, s, ctx, opts) => calls.push(['watcherBefore', el.key, opts && opts.updateBySubscription]),
        onUpdate: log('watcher')
      }
    })
    const owner = app.Owner
    owner.state.update({ n: 1 })
    await flush()
    eq(JSON.stringify(calls), '[["owner","Owner","no-opts"]]', 'store update(): owner onUpdate (el, s, ctx), no child onUpdate')
    calls.length = 0
    owner.state.toggle('flag')
    owner.state.n = 2
    owner.state.replace({ n: 3, flag: true })
    await flush()
    eq(calls.length, 0, 'direct write / toggle / replace run no onUpdate')
    owner.update({})
    await flush()
    eq(JSON.stringify(calls), '[["owner","Owner","opts"]]', 'el.update(): (el, s, ctx, opts)')
    calls.length = 0
    app.state.update({ tab: 2 })
    await flush()
    const names = calls.map((c) => c[0])
    expect(!names.includes('child') && !names.includes('owner'), 'root change runs no descendant onUpdate: ' + JSON.stringify(calls))
    eq(JSON.stringify(calls.filter((c) => c[1] === 'Watcher')), '[["watcherBefore","Watcher",true],["watcher","Watcher","no-opts"]]', 'subscribeTo: onBeforeUpdate(updateBySubscription) then onUpdate(el, s, ctx)')
  },

  async ariaFromState () {
    const app = await mount({ Field: { tag: 'input', state: { error: null }, 'aria-invalid': (el, s) => Boolean(s.error) || null } })
    const node = app.Field.node
    eq(node.getAttribute('aria-invalid'), null, 'no error: no aria-invalid')
    app.Field.state.update({ error: 'Required' })
    await flush()
    eq(node.getAttribute('aria-invalid'), 'true', 'error: aria-invalid="true"')
    app.Field.state.update({ error: null })
    await flush()
    eq(node.getAttribute('aria-invalid'), null, 'cleared: aria-invalid removed')
  },

  async settled () {
    const app = await mount({ state: { label: 'a' }, Label: { text: (el, s) => s.label } })
    const back = await app.state.update({ label: 'b' }).$settled()
    expect(back === app.state, '$settled() resolves with the state')
    eq(app.Label.node.textContent, 'b', 'DOM applied when $settled() resolves')
    app.state.label = 'c'
    await app.state.$settled()
    eq(app.Label.node.textContent, 'c', 'after a direct write')
    const { settled } = await import(pathToFileURL(DIST).href)
    app.state.update({ label: 'd' })
    await settled()
    eq(app.Label.node.textContent, 'd', 'settled() from smbls')
  },

  async onWindowLoadAfterLoad () {
    if (document.readyState !== 'complete') {
      await new Promise((r) => window.addEventListener('load', r, { once: true }))
    }
    let runs = 0
    await mount({ Late: { onWindowLoad: (e, el) => { runs++; eq(el.key, 'Late', 'second argument is the element') } } })
    await flush()
    eq(runs, 1, 'onWindowLoad runs once for an element created after load')
  }
})

// SYNTAX "Raw Style Object" tokens; DESIGN_SYSTEM sizes negation + variables.
Object.assign(cases, {
  async styleBlockTokens () {
    const app = await mount({ Box: { style: { padding: 'A', gridArea: 'A', '& > span': { marginLeft: '-Z' } }, Span: { tag: 'span' } } })
    const st = app.Box.node.style
    expect(/var\(--[\w-]*spacing-A\)/.test(st.getPropertyValue('padding')), 'style padding: A → spacing var (got ' + st.getPropertyValue('padding') + ')')
    eq(st.getPropertyValue('grid-area'), 'A', 'gridArea: A stays A')
    const rules = rulesText().join('\n')
    expect(/> span[^{]*\{[^}]*margin-(left|inline-start):[^;}]*spacing-Z/.test(rules), '& block marginLeft: -Z resolves')
  },

  async sizesNegationAndVars () {
    const app = await mount({ Ring: { outlineOffset: '-hairline2', width: 'hairline2' } })
    const own = ownRules(app.Ring.node) + app.Ring.node.style.cssText
    expect(/outline-offset:\s*calc\(2px \* -1\)/.test(own), 'negated size: ' + own)
    expect(/width:\s*2px/.test(own), 'positive size stays literal')
    expect(/--size-hairline2:\s*2px/.test(rulesText().join('\n')), '--size-hairline2 published')
  }
})

const results = []
for (const [name, fn] of Object.entries(cases)) {
  try {
    await fn()
    results.push({ name, ok: true })
  } catch (e) {
    results.push({ name, ok: false, error: String(e && e.message || e) })
  }
}
const ok = results.every((r) => r.ok)
process.stdout.write(JSON.stringify({ ok, smbls: { version, commit }, cases: results }) + '\n')
process.exit(ok ? 0 : 1)
