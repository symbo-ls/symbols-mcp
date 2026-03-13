# Symbols Cookbook — Interactive DOMQL v3 Recipes

Practical recipes showing state, events, rendering, data fetching, and more.
Every example is a complete, runnable DOMQL v3 component.

---

## State Toggle

Switch a boolean and update UI.

```js
export const StateToggle = {
  flexFlow: 'y',
  gap: 'A',
  state: {
    isOn: false,
  },
  Button: {
    tag: 'button',
    text: (element, state) => state.isOn ? 'Turn Off' : 'Turn On',
    onClick: (event, element, state) => state.toggle('isOn'),
  },
  LabelTag: {
    flexAlign: 'center',
    gap: 'X2',
    Circle: {
      boxSize: 'X2',
      isActive: (element, state) => state.isOn,
      round: 'C1',
      '.isActive': {
        background: 'green',
      },
      '!isActive': {
        background: 'gray',
      },
    },
    P: {
      text: (element, state) => state.isOn ? 'ON' : 'OFF',
    },
  },
}
```

---

## Counter

Increment and decrement a number.

```js
export const Counter = {
  state: {
    count: 0,
  },
  Flex: {
    flexAlign: 'center',
    gap: 'A',
    Button: {
      text: '+',
      onClick: (event, element, state) => state.update({
        count: state.count + 1
      }),
    },
    P: {
      text: (element, state) => 'Count: ' + state.count,
    },
  },
}
```

---

## Conditional Rendering

Show or hide content based on state.

```js
export const ConditionalRender = {
  state: {
    show: false,
  },
  Button: {
    tag: 'button',
    text: 'Toggle Secret',
    onClick: (event, element, state) => state.update({
      show: !state.show
    }),
  },
  Secret: {
    if: (element, state) => state.show,
    P: {
      text: 'The secret content is now visible!',
    },
  },
}
```

---

## Async Data Fetch

Fetch data from an API and update state.

```js
export const AsyncFetch = {
  state: {
    buttonText: 'Load Data',
  },
  P: {
    width: 'G',
    text: '{{ setup }}',
  },
  P_2: {
    fontWeight: 'bold',
    width: 'G',
    margin: '0 0 C',
    text: '{{ punchline }}',
  },
  Button: {
    text: '{{ buttonText }}',
    onClick: async (event, element, state) => {
      state.update({ buttonText: 'loading...' })
      const res = await fetch('https://official-joke-api.appspot.com/jokes/programming/random')
      const data = await res.json()
      state.update({
        ...data[0],
        buttonText: 'Load Data'
      })
    },
  },
}
```

---

## Form Input

Capture input and reflect in UI.

```js
export const FormInput = {
  state: {
    name: '',
  },
  Input: {
    placeholder: 'Enter your name',
    onInput: (event, element, state) => state.update({
      name: element.node.value
    }),
  },
  P: {
    text: (element, state) => state.name ?
      'Hello, ' + state.name + '!' : 'Waiting for input...',
  },
}
```

---

## Form Validation

Simple validation with visual feedback.

```js
export const FormValidation = {
  state: {
    email: '',
    isValid: true,
  },
  Input: {
    type: 'email',
    placeholder: 'Enter email',
    onInput: (e, el, s) => {
      const val = el.node.value
      const isValid = /^[^@]+@[^@]+\.[^@]+$/.test(val)
      s.update({ email: val, isValid })
    },
  },
  P: {
    text: (el, s) => s.isValid ? 'Valid email' : 'Invalid email',
    '.isValid': { color: 'green' },
    '!isValid': { color: 'red' },
  },
}
```

---

## Two-Way Binding

Sync multiple inputs with shared state.

```js
export const TwoWayBinding = {
  state: {
    text: '',
  },
  Flex: {
    gap: 'A',
    Input_1: {
      placeholder: 'Type here...',
      value: '{{ text }}',
      onInput: (e, el, s) => s.update({ text: el.node.value }),
    },
    Input_2: {
      placeholder: 'Mirrors input 1',
      value: '{{ text }}',
      onInput: (e, el, s) => s.update({ text: el.node.value }),
    },
  },
  P: {
    text: (el, s) => 'Shared: ' + s.text,
  },
}
```

---

## Clock (Auto-update)

Auto-update every second using setInterval.

```js
export const Clock = {
  state: {
    time: '',
  },
  onRender: (el, s) => {
    const int = setInterval(() => {
      s.update({ time: new Date().toLocaleTimeString() })
    }, 1000)
    return () => clearInterval(int)
  },
  P: {
    text: (el, s) => 'Time: ' + s.time,
  },
}
```

---

## Tabs

Switch content via active state using children array.

```js
export const Tabs = {
  state: {
    active: 'Home',
  },
  Flex: {
    gap: 'A2',
    children: ['Home', 'Profile', 'Settings'],
    childrenAs: 'state',
    childExtends: 'Button',
    childProps: {
      text: '{{ value }}',
      onClick: (event, element, state) => state.parent.update({
        active: state.value
      }),
    },
  },
  P: {
    text: 'Tab: {{ active }}',
  },
}
```

---

## Accordion

Expand and collapse sections.

```js
export const Accordion = {
  state: {
    open: null,
  },
  Ul: {
    children: [
      { title: 'Intro', text: 'Welcome!' },
      { title: 'Details', text: 'Here is more.' },
      { title: 'Summary', text: 'Done reading.' },
    ],
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: {
      H6: {
        text: '{{ title }}',
        margin: '0',
        onClick: (event, element, state) => state.parent.update({
          open: state.parent.open === state.title ? null : state.title
        }),
      },
      P: {
        if: (element, state) => state.parent.open === state.title,
        margin: 'X 0 C1',
        text: '{{ text }}',
      },
    },
  },
}
```

---

## Todo App

Add and toggle tasks with keyboard input.

```js
export const TodoApp = {
  state: {
    tasks: [],
  },
  Input: {
    placeholder: 'New task...',
    onKeydown: (e, el, s) => {
      if (e.key === 'Enter') {
        const value = el.node.value.trim()
        if (value) {
          s.update({
            tasks: [...s.tasks, { text: value, isDone: false }]
          })
          el.node.value = ''
        }
      }
    },
  },
  Ul: {
    children: (el, s) => s.tasks,
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: {
      text: '{{ text }}',
      onClick: (e, el, s) =>
        s.parent.update({
          tasks: s.parent.tasks.map(t =>
            t.text === s.text ? { ...t, isDone: !t.isDone } : t
          ),
        }),
      '.isDone': { textDecoration: 'line-through' },
      '!isDone': { textDecoration: 'none' },
    },
  },
}
```

---

## Dynamic List

Add and remove list items dynamically.

```js
export const DynamicList = {
  state: {
    items: ['Apples', 'Oranges'],
  },
  Flex: {
    gap: 'A',
    Button_Add: {
      text: 'Add Item',
      onClick: (e, el, s) => s.replace({
        items: [...s.items, 'Item ' + (s.items.length + 1)]
      }),
    },
    Button_Remove: {
      text: 'Remove Last',
      onClick: (e, el, s) => s.replace({
        items: s.items.slice(0, -1)
      }),
    },
  },
  Ul: {
    children: (el, s) => s.items,
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: { text: '{{ value }}' },
  },
}
```

---

## API Pagination

Fetch paginated data with prev/next buttons.

```js
export const ApiPagination = {
  state: {
    page: 1,
    data: [],
  },
  scope: {
    load: async (el, s) => {
      const res = await fetch('https://jsonplaceholder.typicode.com/posts?_limit=3&_page=' + s.page)
      const json = await res.json()
      s.replace({ data: json })
    },
  },
  onRender: (el, s) => {
    el.scope.load(el, s)
  },
  Flex: {
    gap: 'A',
    Button_Prev: {
      text: 'Prev',
      onClick: (e, el, s) => {
        if (s.page > 1) {
          s.update({ page: s.page - 1, data: [{ title: 'loading' }] })
          el.scope.load(el, s)
        }
      },
    },
    Button_Next: {
      text: 'Next',
      onClick: (e, el, s) => {
        s.update({ page: s.page + 1, data: [{ title: 'loading' }] })
        el.scope.load(el, s)
      },
    },
  },
  Ul: {
    children: (el, s) => s.data,
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: { text: '{{ title }}' },
  },
}
```

---

## Modal Window

Open and close a modal overlay.

```js
export const ModalExample = {
  state: {
    open: false,
  },
  Button: {
    text: 'Open Modal',
    onClick: (e, el, s) => s.update({ open: true }),
  },
  Modal: {
    if: (el, s) => s.open,
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    theme: 'dialog',
    padding: 'C2',
    P: { text: 'This is a modal window.' },
    Button: {
      text: 'Close',
      onClick: (e, el, s) => s.update({ open: false }),
    },
  },
}
```

---

## WebSocket

Receive live stream messages via WebSocket.

```js
export const WebSocketDemo = {
  state: {
    msgs: [],
  },
  scope: {},
  onRender: (el, s) => {
    const ws = new WebSocket('wss://ws.postman-echo.com/raw')
    el.scope.ws = ws
    ws.onopen = () => ws.send('Hello WebSocket!')
    ws.onmessage = (e) => {
      s.update({ msgs: [...s.msgs, e.data] })
    }
  },
  Ul: {
    children: (el, s) => s.msgs,
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: { text: '{{ value }}' },
  },
  Button: {
    text: 'Send new message',
    onClick: (event, element, state) => {
      element.scope.ws.send('Message at ' + new Date().toLocaleTimeString())
    },
  },
}
```

---

## Theme Switcher

Toggle light/dark theme dynamically.

```js
export const ThemeSwitcher = {
  state: {
    theme: 'light',
  },
  Button: {
    text: (element, state) => state.theme === 'light' ? 'Go Dark' : 'Go Light',
    onClick: (event, element, state) => state.update({
      theme: state.theme === 'light' ? 'dark' : 'light'
    }),
  },
  Box: {
    theme: (el, s) => 'document @' + s.theme,
    P: {
      text: (el, s) => 'Theme: ' + s.theme,
    },
  },
}
```

---

## Fade Animation

Animate opacity on toggle with CSS transitions.

```js
export const FadeAnimation = {
  state: {
    isVisible: true,
  },
  IconButton: {
    margin: '- B2 C1',
    icon: (el, s) => s.isVisible ? 'eye' : 'eyeOff',
    onClick: (e, el, s) => s.toggle('isVisible'),
  },
  Flex: {
    '.isVisible': { opacity: '1' },
    '!isVisible': { opacity: '0' },
    transition: 'opacity 0.5s',
    theme: 'dialog',
    boxSize: 'E',
    marginTop: 'A',
    Box: { margin: 'auto', text: 'Content' },
  },
}
```

---

## Stopwatch

Start, stop, and reset timer.

```js
export const Stopwatch = {
  state: {
    running: false,
    time: 0,
  },
  onRender: (el, s) => {
    setInterval(() => {
      if (s.running) s.update({ time: s.time + 1 })
    }, 1000)
  },
  Flex: {
    gap: 'A',
    Button_Start: {
      text: (el, s) => s.running ? 'Pause' : 'Start',
      onClick: (e, el, s) => s.update({ running: !s.running }),
    },
    Button_Reset: {
      text: 'Reset',
      onClick: (e, el, s) => s.update({ time: 0 }),
    },
  },
  P: {
    text: (el, s) => 'Elapsed: ' + s.time + 's',
  },
}
```

---

## Progress Bar

Fill dynamically with state.

```js
export const ProgressBar = {
  state: {
    progress: 0,
  },
  Button: {
    text: 'Increase',
    onClick: (event, element, state) =>
      state.update({ progress: Math.min(state.progress + 10, 100) }),
  },
  Bar: {
    width: (el, s) => s.progress + '%',
    height: '20px',
    background: 'green',
  },
  P: {
    text: (element, state) => 'Progress: ' + state.progress + '%',
  },
}
```

---

## Draggable Box

Drag an element using mouse events.

```js
export const DragBox = {
  state: {
    dragging: false,
  },
  Box: {
    boxSize: '90px',
    background: 'blue',
    position: 'absolute',
    onMousedown: (e, el, s) => (s.dragging = true),
    onMouseup: (e, el, s) => (s.dragging = false),
    onMousemove: (e, el, s) => {
      if (s.dragging) el.setProps({
        left: (e.clientX - 45) + 'px',
        top: (e.clientY - 45) + 'px'
      })
    },
  },
}
```

---

## Lazy Image

Load image on intersection using IntersectionObserver.

```js
export const LazyImage = {
  state: {
    loaded: false,
  },
  onRender: (el, s) => {
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) s.update({ loaded: true })
    })
    observer.observe(el.Img.node)
  },
  Img: {
    src: (el, s) => s.loaded ? 'https://picsum.photos/300/200' : '',
    alt: 'Lazy loaded image',
  },
}
```

---

## Text Typer

Animate text one character at a time.

```js
export const TextTyper = {
  state: {
    text: '',
    full: 'Welcome to Symbols!',
  },
  scope: {
    type: (el, s) => {
      let i = 0
      const int = setInterval(() => {
        if (i < s.full.length) {
          s.update({ text: s.text + s.full[i++] })
        } else clearInterval(int)
      }, 75)
    },
  },
  onRender: (el, s) => el.scope.type(el, s),
  P: {
    text: '{{ text }}',
    onClick: (ev, el, s) => {
      s.text = ''
      el.scope.type(el, s)
    },
  },
}
```

---

## Temperature Converter

Convert Celsius to Fahrenheit in real time.

```js
export const TempConverter = {
  state: { c: 0, f: 32 },
  Input_C: {
    type: 'number',
    value: '{{ c }}',
    onInput: (e, el, s) => {
      const c = parseFloat(el.node.value)
      s.update({ c, f: (c * 9 / 5) + 32 })
    },
  },
  Input_F: {
    type: 'number',
    value: '{{ f }}',
    onInput: (e, el, s) => {
      const f = parseFloat(el.node.value)
      s.update({ f, c: (f - 32) * 5 / 9 })
    },
  },
  P: {
    text: (el, s) => s.c + '°C = ' + s.f.toFixed(1) + '°F',
  },
}
```

---

## Image Gallery

Cycle through images with state.

```js
export const ImageGallery = {
  state: {
    index: 0,
    images: [
      'https://picsum.photos/200/200',
      'https://picsum.photos/201/200',
      'https://picsum.photos/202/200',
    ],
  },
  Img: {
    src: (el, s) => s.images[s.index],
    alt: 'Gallery image',
  },
  Hr: {},
  Button_Next: {
    text: 'Next',
    onClick: (e, el, s) =>
      s.update({ index: (s.index + 1) % s.images.length }),
  },
}
```

---

## Local Storage

Persist state between page reloads.

```js
export const LocalStorage = {
  state: { note: '' },
  onInit: (el, s) => {
    s.note = localStorage.getItem('note') || ''
  },
  Textarea: {
    placeholder: 'Write something...',
    value: '{{ note }}',
    onInput: (event, element, state) => {
      const value = element.node.value
      state.update({ note: value })
      localStorage.setItem('note', value)
    },
  },
  P: {
    text: (element, state) => 'Saved: ' + state.note,
  },
}
```

---

## Slider Control

Adjust a range and reflect in state.

```js
export const SliderControl = {
  state: { volume: 50 },
  Input: {
    type: 'range',
    min: 0,
    max: 100,
    value: '{{ volume }}',
    onInput: (e, el, s) => s.update({
      volume: parseInt(el.node.value)
    }),
  },
  P: {
    text: (el, s) => 'Volume: ' + s.volume,
  },
}
```

---

## Keyboard Shortcut

Listen for keypress and update state.

```js
export const KeyboardShortcut = {
  state: { key: 'None' },
  onRender: (el, s) => {
    window.addEventListener('keydown', e =>
      s.update({ key: e.key })
    )
  },
  P: {
    text: (el, s) => 'Last key pressed: ' + s.key,
  },
}
```

---

## Mouse Tracker

Track cursor position in real-time.

```js
export const MouseTracker = {
  state: { x: 0, y: 0 },
  onRender: (el, s) => {
    window.addEventListener('mousemove', e =>
      s.update({ x: e.clientX, y: e.clientY })
    )
  },
  P: {
    text: (el, s) => 'X: ' + s.x + ', Y: ' + s.y,
  },
}
```
