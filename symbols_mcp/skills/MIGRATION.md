# Migration Rules: DOMQL v2 to v3 & Framework to Symbols

Apply these transformation rules when migrating code. Each rule is a BEFORE/AFTER pair.

---

## Part 1: DOMQL v2 to v3

### Rule Summary

| What changed            | v2 (REMOVE)                   | v3 (USE INSTEAD)              |
| ----------------------- | ----------------------------- | ----------------------------- |
| CSS props wrapper       | `props: { padding: 'A' }`    | `padding: 'A'` (at root)     |
| Events wrapper          | `on: { click: fn }`          | `onClick: fn` (at root)      |
| Inheritance             | `extend: 'Component'`        | `extends: 'Component'`       |
| Child extend            | `childExtend: 'Item'`        | `childExtends: 'Item'`       |
| Child element detection | any key including lowercase   | PascalCase keys ONLY          |
| Base components         | `extends: 'Text'` / `'Box'`  | Remove — implicit defaults    |

### Rule 1: Flatten `props` and `on`

Move all `props` entries to root. Remove `on` wrapper; prefix each event with `on` + CapitalizedEventName. Apply at root AND all nested elements.

BEFORE:
```js
{
  props: { position: 'absolute', gap: 'A' },
  on: {
    render: e => {},
    click: (e, t) => {},
    wheel: (e, t) => {},
  },
}
```

AFTER:
```js
{
  position: 'absolute',
  gap: 'A',
  onRender: e => {},
  onClick: (e, t) => {},
  onWheel: (e, t) => {},
}
```

### Rule 2: Rename `extend` to `extends`, `childExtend` to `childExtends`

BEFORE:
```js
{ extend: SomeComponent, childExtend: AnotherComponent }
```

AFTER:
```js
{ extends: SomeComponent, childExtends: AnotherComponent }
```

### Rule 3: Replace `$stateCollection` with `children` + `childrenAs: 'state'`

BEFORE:
```js
{
  childExtend: 'TeamItem',
  $stateCollection: (el, s) => s.data
}
```

AFTER (Option A -- explicit):
```js
{
  childExtends: 'TeamItem',
  childrenAs: 'state',
  children: (el, s) => s.data
}
```

AFTER (Option B -- preferred for nested state):
```js
{
  state: 'data',
  childExtends: 'TeamItem',
  children: ({ state }) => state
}
```

**`state: true` requirement for child components:** Components used with `childExtends` that read individual item state need `state: true` at their root so each child receives its own state from the parent's children array.

BEFORE (parent + child):
```js
// Parent container
export const TeamList = {
  state: 'members',
  childExtends: 'TeamItem',
  children: ({ state }) => state
}

// Child component -- state: true is REQUIRED
export const TeamItem = {
  state: true,
  Title: { text: ({ state }) => state.name },
  Role: { text: ({ state }) => state.role }
}
```

**CRITICAL PITFALL -- `children: ({ state }) => state.data`:**

WRONG -- children don't get individual state:
```js
{ children: ({ state }) => state.data, childExtends: 'Item' }
```

CORRECT -- `state: 'data'` narrows scope, children get individual items:
```js
{ state: 'data', children: ({ state }) => state, childExtends: 'Item' }
```

### Rule 4: Replace `$propsCollection` with `children`

`$propsCollection` is fully removed in v3. Replace 1:1 with `children`.

BEFORE:
```js
{
  childExtend: 'Paragraph',
  $propsCollection: ({ state }) => state.parse()
}
```

AFTER:
```js
{
  childExtends: 'Paragraph',
  children: ({ state }) => state.parse()
}
```

Also applies to array data:

BEFORE: `$propsCollection: ({ state }) => state`
AFTER: `children: ({ state }) => state`

### Rule 5: Replace `props: (fn)` function with individual prop functions

Dynamic props functions are REMOVED in v3. Split into per-property functions.

BEFORE:
```js
{
  props: ({ state }) => ({
    color: state.active ? 'red' : 'blue',
    opacity: state.loading ? 0.5 : 1
  })
}
```

AFTER:
```js
{
  color: ({ state }) => state.active ? 'red' : 'blue',
  opacity: ({ state }) => state.loading ? 0.5 : 1
}
```

### Rule 6: PascalCase-only child elements

In v3, only PascalCase keys create child elements. Lowercase keys are treated as CSS properties.

BEFORE (v2):
```js
{ div: {} }   // creates <div>
```

AFTER (v3):
```js
{ div: {} }   // treated as a plain prop, NOT rendered
{ Div: {} }   // creates a child element (equivalent to { extends: 'Div' })
```

### Rule 7: Replace array spread with `children` array

Array spread creates numeric keys (`0`, `1`, `2`...) which v3 treats as CSS properties. Always use `children` array.

BEFORE:
```js
{
  childExtend: 'NavLink',
  ...[{ text: 'About us' }, { text: 'Hiring' }]
}
```

AFTER:
```js
{
  childExtends: 'NavLink',
  children: [{ text: 'About us' }, { text: 'Hiring' }]
}
```

### Rule 8: Picture `src` must go on Img child

The HTML `<picture>` tag does NOT support `src` as an attribute. In v3, lowercase props move to `element.props`, so `element.parent.src` returns `undefined`.

WRONG:
```js
Picture: { src: '/files/photo.jpg', width: '100%' }
```

CORRECT:
```js
Picture: {
  Img: { src: '/files/photo.jpg' },
  width: '100%',
  aspectRatio: '16/9'
}
```

For theme-aware sources, use `@dark`/`@light` with `srcset` on Picture, but always put the default `src` on the Img child.

### Rule 9: `<map>` tag auto-detection

Component keys named `Map` auto-detect as the HTML `<map>` tag (for image maps), which defaults to `display: inline` and has height 0. If using `Map` as a component name for geographic maps or similar, add `tag: 'div'`:

```js
export const Map = {
  flow: 'y',
  tag: 'div',     // prevents <map> auto-detection
  // ...
}
```

### Rule 10: Non-existent base components

These v2 component names don't exist in v3 uikit:

| v2 (REMOVE)            | v3 (USE INSTEAD)                          |
| ---------------------- | ----------------------------------------- |
| `extends: 'Page'`     | `flow: 'column'`                           |
| `extends: 'Overflow'` | `flow: 'x'`                                |

### Rule 11: `state: true` vs `state: 'fieldName'` for children

| Context                            | Use              | Purpose                                                   |
| ---------------------------------- | ---------------- | --------------------------------------------------------- |
| `childExtends`-created children    | `state: true`    | Maps individual array items as each child's state          |
| Direct PascalCase children         | `state: 'field'` | Picks a specific field from parent state                   |

```js
// childExtends children -- use state: true on the child component
export const ListItem = {
  state: true,
  Title: { text: ({ state }) => state.name }
}

// Direct PascalCase child -- use state: 'fieldName'
Description: {
  state: 'description',
  childExtends: 'Paragraph',
  children: ({ state }) => state.parse()
}
```

### Rule 12: Remove `extends: 'Text'` and `extends: 'Box'`

`Text` and `Box` are built-in implicit defaults. Extending them causes unnecessary merge at runtime.

BEFORE:
```js
Tag: { extends: 'Text', text: 'NEW', padding: 'X A' }
Card: { extends: 'Box', padding: 'B', background: 'white' }
```

AFTER:
```js
Tag: { tag: 'span', text: 'NEW', padding: 'X A' }
Card: { tag: 'div', padding: 'B', background: 'white' }
```

Use semantic or functional components instead (`Flex`, `Link`, `Button`, `Header`, `Section`, etc.).

### Full v2 to v3 transformation example

BEFORE:
```js
{
  extend: 'Flex',
  childExtend: 'ListItem',
  props: { position: 'absolute' },
  attr: { 'gs-w': 1, 'gs-h': 1 },
  SectionTitle: { text: 'Notes' },
  Box: {
    props: {
      '--section-background': '#7a5e0e55',
      id: 'editorjs',
    },
    on: {
      frame: (e, t) => {},
      render: e => {},
      wheel: (e, t) => {},
      dblclick: (e, t) => { e.stopPropagation() },
    },
  },
}
```

AFTER:
```js
{
  flow: 'x',
  childExtends: 'ListItem',
  position: 'absolute',
  attr: { 'gs-w': 1, 'gs-h': 1 },
  SectionTitle: { text: 'Notes' },
  Box: {
    '--section-background': '#7a5e0e55',
    id: 'editorjs',
    onFrame: (e, t) => {},
    onRender: e => {},
    onWheel: (e, t) => {},
    onDblclick: (e, t) => { e.stopPropagation() },
  },
}
```

---

## Part 2: React / Angular / Vue to Symbols

### React to Symbols

| React Pattern                          | Symbols Equivalent                                                        |
| -------------------------------------- | ------------------------------------------------------------------------- |
| `function Component()` / `class`       | `export const Component = { flow: 'y', ... }`                            |
| `import Component from './Component'`  | Reference by key: `{ Component: {} }`                                     |
| `useState(val)`                        | `state: { key: val }` + `s.update({ key: newVal })`                       |
| `useEffect(() => {}, [])`              | `onRender: (el, s) => {}`                                                 |
| `useEffect(() => {}, [dep])`           | `onStateUpdate: (changes, el, s) => {}`                                   |
| `useContext`                           | `s.root` for global state                                                 |
| `useRef`                               | `el.node` for DOM access                                                  |
| `props.onClick`                        | `onClick: (e, el, s) => {}`                                               |
| `props.children`                       | PascalCase child keys or `children` array                                 |
| `{condition && <Component />}`         | `if: (el, s) => condition`                                                |
| `{items.map(i => <Item key={i.id}/>)}` | `children: (el, s) => s.items, childExtends: 'Item'`                      |
| `className="flex gap-4"`              | `flow: 'x', gap: 'A'` (design tokens)                                    |
| `style={{ padding: '16px' }}`         | `padding: 'A'`                                                            |
| `<Link to="/page">`                   | `Link: { href: '/page', text: '...' }`                                    |
| `useNavigate()` / `history.push`      | `el.call('router', '/path', el.getRoot())`                                |
| Redux / Zustand store                 | `state/` folder + `s.root` access                                         |
| `useMemo` / `useCallback`             | Dynamic prop function: `text: (el, s) => s.a + s.b`                      |
| CSS Modules / styled-components       | Flatten styles as props with design tokens                                |
| `<form onSubmit>`                     | `tag: 'form', onSubmit: (ev, el, s) => { ev.preventDefault(); ... }`      |
| `fetch()` in components               | `functions/fetch.js` + `el.call('fetch', method, path, data)`             |

### Angular to Symbols

| Angular Pattern                    | Symbols Equivalent                                                     |
| ---------------------------------- | ---------------------------------------------------------------------- |
| `@Component({ template, styles })` | Plain object with flattened props and child keys                       |
| `@Input() propName`                | `propName: value` at root                                              |
| `@Output() eventName`              | `onEventName: (e, el, s) => {}`                                        |
| `*ngIf="condition"`                | `if: (el, s) => condition`                                             |
| `*ngFor="let item of items"`       | `children: (el, s) => s.items, childExtends: 'X'`                     |
| `[ngClass]="{ active: isActive }"` | `.isActive: { background: 'primary' }`                                 |
| `(click)="handler()"`              | `onClick: (e, el, s) => {}`                                            |
| `{{ interpolation }}`              | `text: '{{ key }}'` or `text: (el, s) => s.key`                        |
| `ngOnInit()`                       | `onInit: (el, s) => {}`                                                |
| `ngAfterViewInit()`                | `onRender: (el, s) => {}`                                              |
| `ngOnDestroy()`                    | Return cleanup fn from `onRender`                                      |
| `ngOnChanges(changes)`             | `onStateUpdate: (changes, el, s) => {}`                                |
| Services / DI                      | `functions/` folder + `el.call('serviceFn', args)`                     |
| `RouterModule` routes              | `pages/index.js` route mapping                                         |
| `routerLink="/path"`               | `Link: { href: '/path' }`                                              |
| `Router.navigate(['/path'])`       | `el.call('router', '/path', el.getRoot())`                             |
| NgRx / BehaviorSubject store       | `state/` folder + `s.root` access                                      |
| SCSS / component styles            | Flatten to props with design tokens                                    |
| Reactive Forms                     | `tag: 'form'`, `Input` children with `name`, `onSubmit` handler        |

### Vue to Symbols

| Vue Pattern                       | Symbols Equivalent                                                                |
| --------------------------------- | --------------------------------------------------------------------------------- |
| `<template>` + `<script>` SFC     | Single object with child keys and flattened props                                 |
| `:propName="value"` (v-bind)      | `propName: value` or `propName: (el, s) => s.value`                               |
| `@click="handler"` (v-on)         | `onClick: (e, el, s) => {}`                                                       |
| `v-if="condition"`                | `if: (el, s) => condition`                                                        |
| `v-show="condition"`              | `hide: (el, s) => !condition`                                                     |
| `v-for="item in items"`           | `children: (el, s) => s.items, childExtends: 'X'`                                |
| `v-model="value"`                 | `value: '{{ key }}'` + `onInput: (e, el, s) => s.update({ key: e.target.value })` |
| `ref="myRef"`                     | `el.node` or `el.lookup('Key')`                                                   |
| `data()` / `ref()` / `reactive()` | `state: { key: value }`                                                           |
| `computed`                        | `text: (el, s) => s.first + ' ' + s.last`                                        |
| `watch`                           | `onStateUpdate: (changes, el, s) => {}`                                           |
| `mounted()`                       | `onRender: (el, s) => {}`                                                         |
| `created()` / `setup()`           | `onInit: (el, s) => {}`                                                           |
| Vuex / Pinia store                | `state/` folder + `s.root` access                                                 |
| `<router-link to="/path">`        | `Link: { href: '/path' }`                                                         |
| `$router.push('/path')`           | `el.call('router', '/path', el.getRoot())`                                        |
| `<slot>`                          | PascalCase child keys or `content` property                                       |
| `<slot name="header">`            | Named child key: `Header: {}`                                                     |
| Mixins / Composables              | `extends` for shared logic; `functions/` for shared utilities                     |
| `$emit('eventName', data)`        | `s.parent.update({ key: data })` or callback via state                            |

---

## Part 3: CSS to Design Tokens

| CSS                                                   | Symbols                                      |
| ----------------------------------------------------- | -------------------------------------------- |
| `padding: 16px`                                       | `padding: 'A'`                               |
| `padding: 16px 26px`                                  | `padding: 'A B'`                             |
| `margin: 0 auto`                                      | `margin: '- auto'`                           |
| `gap: 10px`                                           | `gap: 'Z'`                                   |
| `border-radius: 12px`                                 | `borderRadius: 'Z1'` or `round: 'Z1'`        |
| `width: 42px; height: 42px`                           | `boxSize: 'C'`                               |
| `display: flex; flex-direction: column`               | `flow: 'y'`                                  |
| `display: flex; flex-direction: row`                  | `flow: 'x'`                                  |
| `align-items: center; justify-content: center`        | `align: 'center center'`                     |
| `display: grid; grid-template-columns: repeat(3,1fr)` | `extends: 'Grid', columns: 'repeat(3, 1fr)'` |
| `font-size: 20px`                                     | `fontSize: 'A1'`                             |
| `font-weight: 500`                                    | `fontWeight: '500'`                          |
| `color: rgba(255,255,255,0.65)`                       | `color: 'white.65'`                          |
| `background: #000`                                    | `background: 'black'`                        |
| `background: rgba(0,0,0,0.5)`                         | `background: 'black.5'`                      |
| `cursor: pointer`                                     | `cursor: 'pointer'`                          |
| `overflow: hidden`                                    | `overflow: 'hidden'`                         |
| `position: absolute; inset: 0`                        | `position: 'absolute', inset: '0'`           |
| `z-index: 99`                                         | `zIndex: 99`                                 |
| `transition: all 0.3s ease`                           | `transition: 'A defaultBezier'`              |
| `:hover { background: #333 }`                         | `':hover': { background: 'gray3' }`          |
| `@media (max-width: 768px) { ... }`                   | `'@mobileL': { ... }`                        |

### Spacing token quick reference

| Token | ~px | Token | ~px | Token | ~px |
| ----- | --- | ----- | --- | ----- | --- |
| X     | 3   | A     | 16  | D     | 67  |
| Y     | 6   | A1    | 20  | E     | 109 |
| Z     | 10  | A2    | 22  | F     | 177 |
| Z1    | 12  | B     | 26  |       |     |
| Z2    | 14  | B1    | 32  |       |     |
|       |     | B2    | 36  |       |     |
|       |     | C     | 42  |       |     |
|       |     | C1    | 52  |       |     |
|       |     | C2    | 55  |       |     |

---

## Part 4: v3 Component Template

Use this as the base template for every new component:

```js
// components/ComponentName.js
export const ComponentName = {
  // Props flattened at root (design tokens)
  flow: 'y',
  padding: 'A B',
  background: 'surface',
  borderRadius: 'B',
  gap: 'Z',

  // Lifecycle events
  onRender: (el, s) => {},
  onInit: (el, s) => {},

  // DOM events
  onClick: (e, el, s) => {},

  // Conditional cases (v3 pattern)
  isActive: false,
  '.isActive': { background: 'primary', color: 'white' },

  // Responsive
  '@mobileL': { padding: 'A' },
  '@tabletS': { padding: 'B' },

  // Children -- PascalCase keys, no imports
  Header: {},
  Content: {
    Article: { text: 'Hello' },
  },
  Footer: {},
}
```

---

## Part 5: State Management Migration

| Framework pattern                       | Symbols equivalent                                                            |
| --------------------------------------- | ----------------------------------------------------------------------------- |
| Global store (Redux, Pinia, NgRx)       | `state/index.js` with initial flat state. Access via `s.root` in any component |
| Local component state                   | `state: { key: val }` on the component                                        |
| Derived/computed state                  | Dynamic prop function: `text: (el, s) => derived(s)`                          |
| Async data fetch                        | `onRender: async (el, s) => { ... s.update({data}) }`                         |
| State persistence                       | Functions that read/write to localStorage/cookie                              |

Async state pattern:

```js
export const DataView = {
  state: { data: null, loading: true, error: null },

  onRender: async (el, state) => {
    try {
      const data = await el.call('fetchData', el.props.id)
      state.update({ data, loading: false })
    } catch (e) {
      state.update({ error: e.message, loading: false })
    }
  }
}
```

---

## Part 6: Color/Border/Shadow Syntax Migration (v3.1)

### Color tokens: space-separated to dot-notation

| BEFORE            | AFTER            | Notes                         |
| ----------------- | ---------------- | ----------------------------- |
| `'white .1'`      | `'white.1'`      | Opacity 0.1                   |
| `'gray 0.85'`     | `'gray.85'`      | Opacity 0.85                  |
| `'gray .92 +8'`   | `'gray.92+8'`    | Opacity + relative tone       |
| `'gray 1 +16'`    | `'gray+16'`      | Alpha 1 = default, omit       |
| `'gray 1 -68'`    | `'gray-68'`      | Relative tone                 |
| `'gray 1 90'`     | `'gray=90'`      | Absolute lightness (=prefix)  |
| `'white 1 -78'`   | `'white-78'`     | Tone only                     |

### border: comma-separated to space-separated (CSS order)

| BEFORE                      | AFTER                   |
| --------------------------- | ----------------------- |
| `'solid, gray, 1px'`       | `'1px solid gray'`      |
| `'gray6 .1, solid, 1px'`   | `'1px solid gray6.1'`   |
| `'solid, mediumGrey'`      | `'solid mediumGrey'`    |
| `'1px, solid'`             | `'1px solid'`           |

### boxShadow: commas to spaces within shadow, pipe to comma between shadows

| BEFORE                              | AFTER                       |
| ----------------------------------- | --------------------------- |
| `'white .1, 0, A, C, C'`           | `'white.1 0 A C C'`        |
| `'black .10, 0px, 2px, 8px, 0px'`  | `'black.1 0px 2px 8px 0px'` |
| `'a, b \| c, d'`                   | `'a b, c d'`                |

### textStroke/textShadow: comma-separated to space-separated

| BEFORE                | AFTER              |
| --------------------- | ------------------ |
| `'1px, gray6'`       | `'1px gray6'`      |
| `'gray1, 6px, 6px'`  | `'gray1 6px 6px'`  |

### CSS fallback

Raw CSS values pass through unchanged:
```js
boxShadow: '0 2px 8px rgba(0,0,0,0.1)'  // passes through as-is
border: '1px solid #333'                  // passes through as-is
```
