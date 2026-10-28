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
  const body = hits[0]
    .replace(/^export const (\w+) = /gm, '__d.push(["$1"]); __d[__d.length - 1][1] = ')
    .replace(/^export default /gm, '__d.push(["default"]); __d[__d.length - 1][1] = ')
    // A block that shows two files (`// lang.js` … `// context.js`
    // `import lang from './lang.js'`): the import binds the export above it.
    .replace(/^import (\w+) from '\.\/[^']+'\s*$/gm, 'const $1 = __d[__d.length - 1][1]')
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

  // SYNTAX lifecycle list + "State hooks".
  async lifecycleSignatures () {
    const seen = []
    const app = await mount({
      state: { x: 1 },
      Probe: {
        state: { y: 1 },
        onStateInit: (el, data, ctx) => { seen.push('stateInit'); data.seeded = true; eq(typeof data.update, 'undefined', 'onStateInit gets plain data') },
        onStateCreated: (el, s, ctx) => { seen.push('stateCreated'); eq(typeof s.update, 'function', 'onStateCreated gets the store') },
        onInit: () => seen.push('init'),
        onBeforeUpdate: (el, s, ctx) => { seen.push(['beforeUpdate', el.key, typeof s.update, !!ctx].join()) },
        onBeforeStateUpdate: (el, s, ctx, { changes }) => {
          seen.push('beforeStateUpdate:' + JSON.stringify(changes))
          if (changes.y === 99) return false
          if (changes.y === 5) changes.y = 6
        },
        onUpdate: () => seen.push('update'),
        Shared: { onStateInit: () => seen.push('sharedInit'), onStateCreated: () => seen.push('sharedCreated') }
      }
    })
    const p = app.Probe
    eq(seen.slice(0, 3).join(), 'stateInit,stateCreated,init', 'state hooks run before onInit')
    expect(!seen.includes('sharedInit') && !seen.includes('sharedCreated'), 'an element sharing its parent state runs neither')
    eq(p.state.seeded, true, 'onStateInit writes land in the state')
    seen.length = 0
    p.update({})
    await flush()
    expect(seen.includes('beforeUpdate,Probe,function,true'), 'onBeforeUpdate(el, s, ctx)')
    seen.length = 0
    const ret = p.state.update({ y: 99 })
    await flush()
    expect(ret === p.state, 'a cancelled update still returns the state')
    eq(p.state.y, 1, 'false cancels the write')
    expect(!seen.includes('update'), 'cancelled: no onUpdate')
    p.state.update({ y: 5 })
    await flush()
    eq(p.state.y, 6, 'the handler may adjust changes')
    seen.length = 0
    p.state.update({ y: 7 }, { preventBeforeStateUpdateListener: true })
    p.state.y = 8
    p.state.toggle('seeded')
    await flush()
    expect(!seen.some((x) => String(x).startsWith('beforeStateUpdate')), 'skip option, direct write, toggle run no onBeforeStateUpdate: ' + seen)
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

// SYNTAX "Reactive CSS Props Write Inline": a block that sets the same
// property as a reactive (inline) prop is emitted with !important, so the
// block still wins while it applies.
Object.assign(cases, {
  async reactiveBaseBlocksWin () {
    const app = await mount({
      state: { on: false },
      Swatch: {
        background: (el, s) => s.on ? 'blue' : 'red',
        ':hover': { background: 'green' },
        ':active': { background: 'green' },
        '@dark': { background: 'green' }
      }
    })
    const node = app.Swatch.node
    expect(/background/.test(node.style.cssText), 'reactive background is inline')
    const own = ownRules(node)
    for (const sel of [':hover', ':active', '[data-theme="dark"]']) {
      const rule = own.split('\n').find((t) => t.includes(sel) && /background/.test(t))
      expect(rule && /!important/.test(rule), `${sel} block carries !important: ${rule}`)
    }
  }
})

// COMPONENTS "TooltipLayer": data attributes from `data: {}`, a role=tooltip
// node, aria-describedby while it shows, Escape hides it.
Object.assign(cases, {
  async tooltipLayer () {
    const app = await mount({
      Toolbar: {
        Close: { extends: 'SquareButton', icon: 'x', aria: { label: 'Close' }, data: { tooltip: 'Close panel', tooltipDescription: 'Esc also closes' } },
        TooltipLayer: { tooltipDelay: 0 }
      }
    })
    const btn = app.Toolbar.Close.node
    eq(btn.getAttribute('data-tooltip'), 'Close panel', 'data: { tooltip } → data-tooltip')
    eq(btn.getAttribute('data-tooltip-description'), 'Esc also closes', 'data: { tooltipDescription } → data-tooltip-description')
    btn.focus()
    btn.dispatchEvent(new window.FocusEvent('focusin', { bubbles: true }))
    await flush()
    await new Promise((r) => setTimeout(r, 30))
    const tip = document.querySelector('[role="tooltip"]')
    expect(tip, 'a role=tooltip node exists')
    const shown = (btn.getAttribute('aria-describedby') || '').split(/\s+/).includes(tip.id)
    expect(shown && /Close panel/.test(tip.textContent), 'focus shows it: aria-describedby + text (' + btn.getAttribute('aria-describedby') + ')')
    document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await flush()
    await new Promise((r) => setTimeout(r, 150))
    expect(!(btn.getAttribute('aria-describedby') || '').split(/\s+/).includes(tip.id), 'Escape hides it')
  }
})

// SYNTAX "Shorthand vs longhand — which one wins". The cascade is read from
// the element's own rules + inline style, in emission order: a later
// declaration of the same property wins unless an earlier one is !important.
const effective = (node, prop) => {
  let val = null
  let imp = false
  const take = (text) => {
    const re = new RegExp('(?:^|[;{\\s])' + prop + ':\\s*([^;}]+)', 'g')
    let m
    while ((m = re.exec(text))) {
      const v = m[1].trim()
      const isImp = /!important/.test(v)
      if (imp && !isImp) continue
      val = v.replace(/\s*!important/, ''); imp = isImp
    }
  }
  for (const t of ownRules(node).split('\n')) if (!/:hover|:focus|:active|@media|data-theme/.test(t)) take(t)
  take(node.style.cssText)
  return val
}
Object.assign(cases, {
  async shorthandLonghand () {
    const app = await mount({
      Same: { paddingTop: 'B', padding: 'A' },
      Base: { extends: 'Flex', paddingTop: 'C', backgroundColor: 'primary', borderStyle: 'dashed', borderWidth: '2px' },
      Over: { extends: 'Base', padding: 'A' },
      Pos: { extends: 'Base', background: 'none' },
      Line: { extends: 'Base', border: 'none' }
    }, { components: { Base: { paddingTop: 'C', backgroundColor: 'primary', borderStyle: 'dashed', borderWidth: '2px' } } })
    // paddingTop is emitted as its logical longhand, padding-block-start
    const top = (n) => effective(n, 'padding-block-start') || effective(n, 'padding-top')
    const rules = ownRules(app.Same.node).split('\n')
    const iLong = rules.findIndex((t) => /padding-block-start|padding-top/.test(t))
    const iShort = rules.findIndex((t) => /\{padding:/.test(t))
    expect(/spacing-B/.test(top(app.Same.node) || '') && iLong > iShort, 'same component: the longhand comes after the shorthand and wins')
    expect(!top(app.Over.node), "a later layer's padding replaces the base paddingTop: " + top(app.Over.node))
    expect(/dashed/.test(effective(app.Pos.node, 'border-style') || ''), 'base borderStyle kept where no border shorthand')
    expect(!effective(app.Line.node, 'border-style'), "border: 'none' resets the base borderStyle")
    expect(/primary/.test(effective(app.Pos.node, 'background-color') || ''), 'background (positional) keeps the base backgroundColor: ' + effective(app.Pos.node, 'background-color'))
    expect(/2px/.test(effective(app.Line.node, 'border-width') || ''), "border: 'none' keeps the base borderWidth: " + effective(app.Line.node, 'border-width'))
  },

  async focusVisibleRecolorsRing () {
    const app = await mount({ Ring: { extends: 'Link', href: '/x', text: 'x', ':focus-visible': { outlineColor: 'primary' } } })
    const rule = ownRules(app.Ring.node).split('\n').find((t) => /:focus-visible/.test(t) && /outline-color/.test(t))
    expect(rule && /outline-color:[^;}]*!important/.test(rule), ':focus-visible outlineColor carries !important: ' + rule)
  }
})

// SYNTAX: "A base that owns a lifecycle step" and "View events".
Object.assign(cases, {
  // The base's `always` onRender runs although Card declares its own.
  async alwaysLifecycle () {
    const [[, Tracked], [, Card]] = docExports('SYNTAX.md', 'never instead of it')
    const seen = []
    await mount({ Item: { extends: 'Card' } }, {
      components: { Tracked, Card },
      functions: { trackImpression (key) { seen.push(key) } }
    })
    eq(JSON.stringify(seen), '["Item"]', "Tracked's onRender ran beside Card's own")
  },

  // Rise rises once at its threshold; onLeaveView runs on the way out.
  async viewEvents () {
    const [[, Rise]] = docExports('SYNTAX.md', 'every component that extends Rise keeps this step')
    const observers = []
    class FakeIO {
      constructor (cb, options) { this.cb = cb; this.options = options || {}; this.targets = new Set(); observers.push(this) }
      observe (node) { this.targets.add(node) }
      unobserve (node) { this.targets.delete(node) }
      disconnect () { this.targets.clear() }
    }
    const had = dom.window.IntersectionObserver
    dom.window.IntersectionObserver = FakeIO
    try {
      const paused = []
      const app = await mount({ Card: { extends: 'Rise' } }, {
        components: { Rise },
        functions: { pausePreview (el) { paused.push(el.key) } }
      })
      const node = app.Card.node
      const deliver = (ratio) => {
        for (const io of observers) {
          if (io.targets.has(node)) io.cb([{ target: node, isIntersecting: ratio > 0, intersectionRatio: ratio, time: 1 }], io)
        }
      }
      eq(node.getAttribute('data-rise'), 'wait', 'waits before it is seen')
      deliver(0.05)
      eq(node.getAttribute('data-rise'), 'wait', 'below threshold 0.1: still waiting')
      deliver(0.5)
      eq(node.getAttribute('data-rise'), 'in', 'rose at its threshold')
      deliver(0)
      eq(JSON.stringify(paused), '["Card"]', 'onLeaveView ran on the way out')
      expect(observers.filter((io) => io.options.threshold === 0.1).every((io) => !io.targets.size), '`once` let the element go')
    } finally {
      if (had) dom.window.IntersectionObserver = had
      else delete dom.window.IntersectionObserver
    }
  }
})

// SYNTAX "Element Methods": el.whenConnected runs once the node is in the
// document. onRender runs on a detached node (the first render builds the
// root outside the document), so the documented focus lands only through it.
Object.assign(cases, {
  async whenConnectedFocus () {
    const [[, SearchField]] = docExports('SYNTAX.md', 'el.whenConnected(() => el.node.focus())')
    const app = await mount({ Field: { extends: 'SearchField' } }, { components: { SearchField } })
    const node = app.Field.node
    eq(node.tagName, 'INPUT', 'SearchField extends Input')
    expect(document.activeElement === node, 'the field is focused once it is in the document')
  }
})

// Round 3 (smbls 3.14.840): the start language, DropdownDisclosure, Dialog
// locked, and the stale-seed refresh of a pre-built page.
Object.assign(cases, {
  // SYNTAX "The start language": /en/about starts in English over a stored
  // 'ka'; 'fallback' lets the stored choice win; the address is never stored.
  async polyglotStartLang () {
    const [[, polyglot]] = docExports('SYNTAX.md', "addressLang: true,")
    eq(polyglot.addressLang, true, 'the documented default')
    const tree = { Hello: { text: '{{ hello | polyglot }}' } }
    window.history.replaceState(null, '', '/en/about')
    localStorage.setItem('smbls_lang', 'ka')
    try {
      const fresh = () => JSON.parse(JSON.stringify(polyglot))
      const app = await mount(tree, { polyglot: fresh() })
      eq(app.state.lang, 'en', 'the address wins over the stored choice')
      eq(app.Hello.node.textContent, 'Hello', 'the first render shows the address language')
      eq(localStorage.getItem('smbls_lang'), 'ka', 'the address language is not stored')
      const fallback = await mount(tree, { polyglot: { ...fresh(), addressLang: 'fallback' } })
      eq(fallback.state.lang, 'ka', "'fallback': the stored choice wins")
      localStorage.removeItem('smbls_lang')
      window.history.replaceState(null, '', '/')
      const home = await mount(tree, { polyglot: fresh() })
      eq(home.state.lang === 'ka' || home.state.lang === undefined, true, '/ with nothing stored: the default (got ' + home.state.lang + ')')
      eq(home.Hello.node.textContent, polyglot.translations.ka.hello, '/ renders the default language')
    } finally {
      localStorage.removeItem('smbls_lang')
      window.history.replaceState(null, '', '/')
    }
  },

  // PATTERNS "Polyglot": the one declaration, `polyglot: { defaultLang,
  // languages, translations: lang }` in context.js, translates; a bare `lang`
  // key in the context starts no polyglot, so the pipe renders empty.
  async polyglotOneForm () {
    const [[, lang], [, context]] = docExports('PATTERNS.md', 'translations: lang')
    eq(context.polyglot.translations, lang, 'context.js passes lang.js as polyglot.translations')
    const tree = { Title: { text: '{{ welcome | polyglot }}' } }
    const app = await mount(tree, { polyglot: context.polyglot })
    eq(app.Title.node.textContent, lang.en.welcome, 'the documented form translates')
    const bare = await mount(tree, { lang })
    eq(bare.Title.node.textContent, '', 'a bare lang key: no polyglot, the pipe renders empty')
  },

  // COMPONENTS "DropdownDisclosure": aria-expanded + aria-controls, no
  // aria-haspopup, no menu role; click opens, Escape closes back to the trigger.
  async dropdownDisclosure () {
    const [[, AccountMenu]] = docExports('COMPONENTS.md', "extends: 'DropdownDisclosure'")
    const app = await mount({ Menu: { extends: 'AccountMenu' } }, { components: { AccountMenu }, functions: { signOut () {} } })
    const menu = app.Menu
    const button = menu.Button.node
    const panel = menu.Dropdown.node
    eq(button.getAttribute('aria-expanded'), 'false', 'closed: aria-expanded="false"')
    eq(button.getAttribute('aria-controls'), panel.id, 'aria-controls names the panel')
    eq(button.getAttribute('aria-haspopup'), null, 'no aria-haspopup')
    expect(!document.querySelector('[role="menu"], [role="menuitem"]'), 'no menu roles')
    button.focus()
    button.dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true }))
    await flush()
    eq(button.getAttribute('aria-expanded'), 'true', 'click opens')
    eq(menu.node.getAttribute('data-dropdown-open'), 'true', 'data-dropdown-open="true"')
    const link = menu.Dropdown.Profile.node
    eq(link.getAttribute('tabindex'), null, 'links keep the normal tab order')
    link.focus()
    link.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }))
    await flush()
    eq(button.getAttribute('aria-expanded'), 'false', 'Escape in the panel closes')
    expect(document.activeElement === button, 'focus returns to the trigger')
  },

  // COMPONENTS "Dialog — locked": no built-in cancel controls, closedby="none",
  // the cancel event prevented; OK still renders.
  async dialogLocked () {
    const [[, ForcedPasswordChange]] = docExports('COMPONENTS.md', 'export const ForcedPasswordChange')
    const app = await mount({ state: { mustChangePassword: true }, Change: { extends: 'ForcedPasswordChange' } }, {
      components: { ForcedPasswordChange }, functions: { savePassword () {} }
    })
    const node = app.Change.node
    eq(node.tagName, 'DIALOG', 'a <dialog>')
    eq(node.getAttribute('closedby'), 'none', 'closedby="none"')
    const buttons = [...node.querySelectorAll('button')]
    const labels = buttons.map((b) => (b.getAttribute('aria-label') || b.textContent || '').trim().toLowerCase())
    expect(!labels.some((l) => /close|cancel/.test(l)), 'no close button, no Cancel: ' + JSON.stringify(labels))
    expect(labels.some((l) => /ok/.test(l)), 'OK still renders: ' + JSON.stringify(labels))
    const cancel = new window.Event('cancel', { cancelable: true })
    node.dispatchEvent(cancel)
    expect(cancel.defaultPrevented, 'the cancel event is prevented')
  },

  // SYNTAX "A pre-built page's data — fetch.seed": a pre-built page whose
  // build stamp the project's isStale rejects adopts the build's answers,
  // then after its first view asks again — the declarative query refetches,
  // and a changed imperative read reaches onRefresh(changes, root). A replaced
  // page (`hydrate: false`): the server markup goes, the seed stays. Runs
  // SYNTAX: "Breakpoints that follow a container" — a descendant's width
  // breakpoint compiles to @container, print stays @media, the declaring
  // element is the size container.
  async breakpointsFromContainer () {
    const [[, Canvas]] = docExports('SYNTAX.md', "breakpointsFrom: 'container',")
    const app = await mount({ state: { previewWidth: '390px' }, Canvas })
    const canvas = app.Canvas
    const own = ownRules(canvas.node)
    expect(/container-type:\s*inline-size/.test(own), 'Canvas is an inline-size container: ' + own)
    expect(/container-name:\s*breakpoints/.test(own), 'Canvas container-name breakpoints: ' + own)
    const page = ownRules(canvas.Page.node)
    expect(/@container breakpoints \(max-width: 768px\)/.test(page), '@mobileL → @container: ' + page)
    expect(/@media print/.test(page), '@print stays @media: ' + page)
    expect(!/@media[^{]*max-width: 768px/.test(page), 'no window max-width query left: ' + page)
  },

  // SYNTAX: "CSS system colours and forced-colours blocks" — a system colour
  // in a forced-colours block is emitted as written, in the shorthand too.
  async forcedColorsSystemColor () {
    const [[, FilterChip]] = docExports('SYNTAX.md', "'@media (forced-colors: active)': {")
    const app = await mount({ FilterChip: { ...FilterChip, extends: undefined } })
    const css = ownRules(app.FilterChip.node)
    expect(/forced-colors: active/.test(css), 'forced-colors block emitted: ' + css)
    expect(/color:\s*ButtonText/i.test(css), 'color ButtonText kept: ' + css)
    expect(/1px solid ButtonText/i.test(css), 'border shorthand keeps ButtonText: ' + css)
    expect(!/BUTTONTEXT/.test(css), 'no spacing var for the system colour: ' + css)
  },

  // SYNTAX: "The ROOT state follows the same rule" — root keys named like an
  // element method (log) and a store method (keys) are data; $update is the method.
  async rootStateMethodNamedKeys () {
    const [[, state], [, Summary]] = docExports('SYNTAX.md', 'export default { log: [], keys:')
    const app = await mount({ state: JSON.parse(JSON.stringify(state)), Summary })
    eq(Array.isArray(app.state.log), true, 'root log is data')
    eq(Array.isArray(app.state.keys), true, 'root keys is data')
    eq(app.Summary.Count.node.textContent, '0 events, 2 keys', 'Count text')
    app.Summary.Button.node.dispatchEvent(new window.Event('click', { bubbles: true }))
    await flush()
    eq(app.state.count, 1, 's.root.$update wrote count')
  },

  // SYNTAX: "Choosing a route from data" — the guard shows /:page for an
  // address /:lang matched; the address stays; a per-call { route } chooses too.
  async routeChoiceGuard () {
    const [[, config]] = docExports('SYNTAX.md', 'const languageOrPage')
    const wait = () => new Promise((r) => setTimeout(r, 60))
    const holder = document.createElement('div')
    document.body.appendChild(holder)
    history.pushState(null, '', '/volunteer')
    try {
      const pages = {
        '/': { text: 'root' },
        '/:lang': { H: { text: 'home' } },
        '/:page': { H: { text: (el, s) => 'page ' + s.root.route } }
      }
      const app = await create({}, {
        key: 'example' + (++n), parent: holder, sync: false, globalTheme: 'auto', designSystem: DS, pages,
        polyglot: { defaultLang: 'en', languages: ['en', 'ka'], translations: { en: {}, ka: {} } },
        router: config.router
      })
      await wait()
      eq(location.pathname, '/volunteer', 'the address stays')
      eq(holder.textContent, 'page /:page', 'the guard chose /:page (state.route is the chosen key)')
      app.router('/en', app)
      await wait()
      eq(holder.textContent, 'home', '/en is a language home')
      app.router('/volunteer', app, {}, { route: '/:page' })
      await wait()
      eq(holder.textContent, 'page /:page', 'a per-call { route } chooses')
    } finally {
      history.replaceState(null, '', '/')
    }
  },

  // last: it boots over a pre-rendered page.
  async staleSeedRefresh () {
    const [[, config]] = docExports('SYNTAX.md', 'seed: {')
    const early = await import(pathToFileURL(join(tree, 'plugins', 'fetch', 'early.js')).href)
    const { brenderStampMeta } = await import(pathToFileURL(join(tree, 'packages', 'utils', 'index.js')).href)
    const fetchConfig = { ...config.fetch, auth: false }
    const url = (from) => fetchConfig.url + '/' + from
    const BUILD = { posts: [{ title: 'Alpha' }], settings: { v: 1 } }
    const FRESH = { posts: [{ title: 'Alpha' }, { title: 'Beta' }], settings: { v: 2 } }
    const TIME = Date.now()
    const head = document.createElement('div')
    head.innerHTML = '<meta name="brender" content="replace">' + brenderStampMeta({ stamp: 'catalog-v1', time: TIME })
    const metas = [...head.children]
    metas.forEach((m) => document.head.appendChild(m))
    const holder = document.createElement('div')
    holder.innerHTML = '<main>SERVER</main>'
    document.body.appendChild(holder)
    const seed = document.createElement('div')
    seed.innerHTML = early.createEarlySeedBlock(['posts', 'settings'].map((from) => ({ url: url(from), body: JSON.stringify(BUILD[from]) })))
    const block = seed.firstElementChild
    document.body.appendChild(block)
    const realFetch = globalThis.fetch
    const calls = []
    globalThis.fetch = async (req) => {
      const at = String(req)
      calls.push(at)
      const from = Object.keys(FRESH).find((k) => at.startsWith(url(k)))
      return new Response(JSON.stringify(FRESH[from]), { status: 200, headers: { 'content-type': 'application/json' } })
    }
    const quiet = { retry: false, refetchOnWindowFocus: false, refetchOnReconnect: false }
    try {
      const app = await create({
        state: { settings: null },
        Posts: {
          tag: 'ul',
          state: { items: [] },
          fetch: { from: 'posts', as: 'items', ...quiet },
          children: (el, s) => s.items,
          childrenAs: 'state',
          childProps: { tag: 'li', text: (el, s) => s.title }
        },
        Settings: {
          text: (el, s) => (s.root.settings ? 'v' + s.root.settings.v : ''),
          onRender: async (el) => {
            const db = await el.getDB()
            const { data } = await db.select({ from: 'settings' })
            el.state.root.update({ settings: data })
          }
        }
      }, { key: 'example' + (++n), parent: holder, router: false, sync: false, globalTheme: 'auto', designSystem: DS, fetch: fetchConfig })
      eq(JSON.stringify(app.context.prerender), JSON.stringify({ stamp: 'catalog-v1', time: TIME }), 'el.context.prerender')
      const rows = () => [...app.Posts.node.querySelectorAll('li')].map((li) => li.textContent).join()
      await Promise.resolve()
      const first = rows()
      for (let i = 0; i < 150 && !(rows() === 'Alpha,Beta' && app.state.settings && app.state.settings.v === 2); i++) {
        await new Promise((r) => setTimeout(r, 20))
      }
      eq(rows(), 'Alpha,Beta', 'the declarative query refetched after the first view (first: ' + first + ')')
      eq(app.state.settings && app.state.settings.v, 2, 'onRefresh wrote the changed read into root state')
      eq(calls.length, 2, 'one request each, both from the refresh: ' + JSON.stringify(calls))
      await flush()
      eq(app.Settings.node.textContent, 'v2', 'the page shows the fresh value')
    } finally {
      globalThis.fetch = realFetch
      metas.forEach((m) => m.remove())
      block.remove()
    }
  }
})

// The fetch trigger list, the afterFirstView create option and polyglot's
// prefetch (smbls after 3.14.857 / fetch after 3.14.671 / polyglot after
// 3.14.611): the documented blocks, on a mock adapter, no network.
Object.assign(cases, {
  // FRAMEWORK §5 "A list of triggers": one config loads on create and runs
  // again when the state its params read changes — not for its own rows.
  async fetchTriggerList () {
    const [[, ArticleList]] = docExports('FRAMEWORK.md', "on: ['create', 'stateChange']")
    const asked = []
    const select = async ({ params }) => { asked.push(params.kind); return { data: [{ title: params.kind + '-1' }] } }
    const app = await mount({ ArticleList }, { fetch: { name: 'mock', auth: false, select } })
    for (let i = 0; i < 50 && app.ArticleList.node.textContent !== 'texts-1'; i++) await flush()
    eq(app.ArticleList.node.textContent, 'texts-1', 'loaded on create')
    eq(asked.join(), 'texts', 'one request on create')
    app.ArticleList.state.update({ kind: 'vlog' })
    for (let i = 0; i < 50 && app.ArticleList.node.textContent !== 'vlog-1'; i++) await flush()
    eq(app.ArticleList.node.textContent, 'vlog-1', 'ran again when s.kind changed')
    await flush()
    eq(asked.join(), 'texts,vlog', 'no request for its own rows')
  },

  // SYNTAX "When the app's first view is in — afterFirstView": runs once, a
  // task after the first view, with (app, state, context).
  async afterFirstViewOption () {
    const [[, config]] = docExports('SYNTAX.md', 'afterFirstView: (app, state, context) =>')
    const views = []
    let seen = null
    const app = await mount({ Hello: { text: 'hi' } }, {
      afterFirstView: (a, s, ctx) => { seen = [a, s, ctx]; return config.afterFirstView(a, s, ctx) },
      functions: { pageView () { views.push(this.Hello && this.Hello.node.textContent) } }
    })
    for (let i = 0; i < 20 && !views.length; i++) await flush()
    eq(views.length, 1, 'ran once')
    eq(views[0], 'hi', 'after the first view is in')
    expect(seen[0] === app && seen[1] === app.state && seen[2] === app.context, '(app, state, context)')
    await flush()
    eq(views.length, 1, 'never again')
  },

  // SYNTAX "Warming the other languages — prefetch": at idle the other
  // language's labels load and are stored; the active language stays.
  async polyglotPrefetch () {
    const [[, polyglot]] = docExports('SYNTAX.md', 'prefetch: true')
    const LABELS = { ka: { hello: 'გამარჯობა' }, en: { hello: 'Hello' } }
    const asked = []
    const rpc = async ({ from, params }) => {
      asked.push(from + ':' + params.p_lang)
      return { data: { changed: true, version: 1, translations: LABELS[params.p_lang] } }
    }
    const stored = (lang) => localStorage.getItem((polyglot.storagePrefix || 'smbls_t_') + lang)
    localStorage.removeItem('smbls_lang')
    try {
      const app = await mount({ Hello: { text: '{{ hello | polyglot }}' } }, {
        polyglot: JSON.parse(JSON.stringify(polyglot)),
        fetch: { name: 'mock', auth: false, rpc, select: async () => ({ data: [] }) }
      })
      for (let i = 0; i < 100 && !stored('en'); i++) await new Promise((r) => setTimeout(r, 10))
      expect(stored('en'), 'the other language is stored after idle: ' + JSON.stringify(asked))
      eq(asked[0], 'get_translations_if_changed:ka', 'the active language first')
      expect(asked.includes('get_translations_if_changed:en'), 'then the other one')
      eq(app.Hello.node.textContent, 'გამარჯობა', 'the screen stays in the active language')
    } finally {
      for (const lang of ['ka', 'en']) {
        localStorage.removeItem('smbls_t_' + lang)
        localStorage.removeItem('smbls_tv_' + lang)
      }
    }
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
