# Symbols Cookbook — DOMQL Recipes

28 complete, runnable DOMQL component recipes covering state, events, rendering, data fetching, and more.

---

## 1. State Toggle

Toggle a boolean and update UI.

```js
export const StateToggle = {
  flow: 'y',
  gap: 'A',
  state: {
    isOn: false
  },
  Button: {
    tag: 'button',
    text: (el, s) => (s.isOn ? 'Turn Off' : 'Turn On'),
    onClick: (e, el, s) => s.toggle('isOn')
  },
  LabelTag: {
    flow: 'x',
    align: 'center',
    gap: 'X2',
    Circle: {
      boxSize: 'X2',
      round: 'C1',
      background: (el, s) => (s.isOn ? 'green' : 'gray')
    },
    P: {
      text: (el, s) => (s.isOn ? 'ON' : 'OFF')
    }
  }
}
```

---

## 2. Counter

Increment and decrement a number.

```js
export const Counter = {
  state: {
    count: 0
  },
  Row: {
    flow: 'x',
    align: 'center',
    gap: 'A',
    Button: {
      text: '+',
      onClick: (e, el, s) =>
        s.update({
          count: s.count + 1
        })
    },
    P: {
      text: (el, s) => 'Count: ' + s.count
    }
  }
}
```

---

## 3. Conditional Rendering

Show or hide content based on state.

```js
export const ConditionalRender = {
  state: {
    show: false
  },
  Button: {
    tag: 'button',
    text: 'Toggle Secret',
    onClick: (e, el, s) =>
      s.update({
        show: !s.show
      })
  },
  Secret: {
    if: (el, s) => s.show,
    P: {
      text: 'The secret content is now visible!'
    }
  }
}
```

---

## 4. Async Data Fetch

Fetch data from an API and update state.

```js
export const AsyncFetch = {
  state: {
    buttonText: 'Load Data'
  },
  fetch: {
    url: 'https://official-joke-api.appspot.com/jokes/programming/random',
    auto: false,
    onSuccess: (data, el, s) => {
      const joke = Array.isArray(data) ? data[0] : data
      s.update({ ...joke, buttonText: 'Load Data' })
    }
  },
  P: {
    width: 'G',
    text: '{{ setup }}'
  },
  P_2: {
    fontWeight: 'bold',
    width: 'G',
    margin: '0 0 C',
    text: '{{ punchline }}'
  },
  Button: {
    text: '{{ buttonText }}',
    onClick: (e, el, s) => {
      s.update({ buttonText: 'loading...' })
      el.refetch()
    }
  }
}
```

---

## 5. Form Input

Capture input and reflect in UI.

```js
export const FormInput = {
  state: {
    name: ''
  },
  Input: {
    placeholder: '{{ enterYourName | polyglot }}',
    onInput: (e, el, s) =>
      s.update({
        name: el.node.value
      })
  },
  P: {
    text: (el, s) =>
      s.name ? 'Hello, ' + s.name + '!' : 'Waiting for input...'
  }
}
```

---

## 6. Form Validation

Validation with visual feedback.

```js
export const FormValidation = {
  state: {
    email: '',
    isValid: true
  },
  Input: {
    type: 'email',
    placeholder: '{{ enterEmail | polyglot }}',
    onInput: (e, el, s) => {
      const val = el.node.value
      const isValid = /^[^@]+@[^@]+\.[^@]+$/.test(val)
      s.update({ email: val, isValid })
    }
  },
  P: {
    text: (el, s) => (s.isValid ? 'Valid email' : 'Invalid email'),
    color: (el, s) => (s.isValid ? 'green' : 'red')
  }
}
```

---

## 7. Two-Way Binding

Sync multiple inputs with shared state.

```js
export const TwoWayBinding = {
  state: {
    text: ''
  },
  Row: {
    flow: 'x',
    gap: 'A',
    Input_1: {
      placeholder: '{{ typeHere | polyglot }}',
      value: '{{ text }}',
      onInput: (e, el, s) => s.update({ text: el.node.value })
    },
    Input_2: {
      placeholder: '{{ mirrorsInput1 | polyglot }}',
      value: '{{ text }}',
      onInput: (e, el, s) => s.update({ text: el.node.value })
    }
  },
  P: {
    text: (el, s) => 'Shared: ' + s.text
  }
}
```

---

## 8. Clock (Auto-update)

Auto-update every second using setInterval.

```js
export const Clock = {
  state: {
    time: ''
  },
  onRender: (el, s) => {
    const int = setInterval(() => {
      s.update({ time: new Date().toLocaleTimeString() })
    }, 1000)
    return () => clearInterval(int)
  },
  P: {
    text: (el, s) => 'Time: ' + s.time
  }
}
```

---

## 9. Tabs

Switch content via active state using children array.

```js
export const Tabs = {
  state: {
    active: 'Home'
  },
  Row: {
    flow: 'x',
    gap: 'A2',
    children: ['Home', 'Profile', 'Settings'],
    childrenAs: 'state',
    childExtends: 'Button',
    childProps: {
      text: '{{ value }}',
      onClick: (e, el, s) =>
        s.parent.update({
          active: s.value
        })
    }
  },
  P: {
    text: 'Tab: {{ active }}'
  }
}
```

---

## 10. Accordion

Expand and collapse sections.

```js
export const Accordion = {
  state: {
    open: null
  },
  Ul: {
    children: [
      { title: 'Intro', text: 'Welcome!' },
      { title: 'Details', text: 'Here is more.' },
      { title: 'Summary', text: 'Done reading.' }
    ],
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: {
      H6: {
        text: '{{ title }}',
        margin: '0',
        onClick: (e, el, s) =>
          s.parent.update({
            open: s.parent.open === s.title ? null : s.title
          })
      },
      P: {
        if: (el, s) => s.parent.open === s.title,
        margin: 'X 0 C1',
        text: '{{ text }}'
      }
    }
  }
}
```

---

## 11. Todo App

Add and toggle tasks with keyboard input.

```js
export const TodoApp = {
  state: {
    tasks: []
  },
  Input: {
    placeholder: '{{ newTask | polyglot }}',
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
    }
  },
  Ul: {
    children: (el, s) => s.tasks,
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: {
      text: '{{ text }}',
      onClick: (e, el, s) =>
        s.parent.update({
          tasks: s.parent.tasks.map((t) =>
            t.text === s.text ? { ...t, isDone: !t.isDone } : t
          )
        }),
      textDecoration: (el, s) => (s.isDone ? 'line-through' : 'none')
    }
  }
}
```

---

## 12. Dynamic List

Add and remove list items dynamically.

```js
export const DynamicList = {
  state: {
    items: ['Apples', 'Oranges']
  },
  Row: {
    flow: 'x',
    gap: 'A',
    Button_Add: {
      text: 'Add Item',
      onClick: (e, el, s) =>
        s.replace({
          items: [...s.items, 'Item ' + (s.items.length + 1)]
        })
    },
    Button_Remove: {
      text: 'Remove Last',
      onClick: (e, el, s) =>
        s.replace({
          items: s.items.slice(0, -1)
        })
    }
  },
  Ul: {
    children: (el, s) => s.items,
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: { text: '{{ value }}' }
  }
}
```

---

## 13. API Pagination

Fetch paginated data with prev/next buttons.

```js
export const ApiPagination = {
  state: {
    page: 1,
    data: []
  },
  fetch: {
    url: (el, s) =>
      'https://jsonplaceholder.typicode.com/posts?_limit=3&_page=' + s.page,
    deps: (el, s) => [s.page],
    onSuccess: (data, el, s) => s.replace({ data })
  },
  Row: {
    flow: 'x',
    gap: 'A',
    Button_Prev: {
      text: 'Prev',
      onClick: (e, el, s) => {
        if (s.page > 1) {
          s.update({ page: s.page - 1, data: [{ title: 'loading' }] })
        }
      }
    },
    Button_Next: {
      text: 'Next',
      onClick: (e, el, s) =>
        s.update({ page: s.page + 1, data: [{ title: 'loading' }] })
    }
  },
  Ul: {
    children: (el, s) => s.data,
    childrenAs: 'state',
    childExtends: 'Li',
    childProps: { text: '{{ title }}' }
  }
}
```

---

## 14. Modal Window

Open and close a modal overlay.

```js
export const ModalExample = {
  state: {
    open: false
  },
  Button: {
    text: 'Open Modal',
    onClick: (e, el, s) => s.update({ open: true })
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
      onClick: (e, el, s) => s.update({ open: false })
    }
  }
}
```

---

## 15. WebSocket

Receive live messages via WebSocket.

```js
export const WebSocketDemo = {
  state: {
    msgs: []
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
    childProps: { text: '{{ value }}' }
  },
  Button: {
    text: 'Send new message',
    onClick: (e, el, s) => {
      el.scope.ws.send('Message at ' + new Date().toLocaleTimeString())
    }
  }
}
```

---

## 16. Theme Switcher

Toggle light/dark theme dynamically.

```js
export const ThemeSwitcher = {
  state: {
    theme: 'light'
  },
  Button: {
    text: (el, s) => (s.theme === 'light' ? 'Go Dark' : 'Go Light'),
    onClick: (e, el, s) => {
      const next = s.theme === 'light' ? 'dark' : 'light'
      s.update({ theme: next })
      el.call('changeGlobalTheme', next)
    }
  },
  Status: {
    P: {
      text: (el, s) => 'Theme: ' + s.theme
    }
  }
}
```

---

## 17. Fade Animation

Animate opacity on toggle with CSS transitions.

```js
export const FadeAnimation = {
  state: {
    isVisible: true
  },
  IconButton: {
    margin: '- B2 C1',
    icon: (el, s) => (s.isVisible ? 'eye' : 'eyeOff'),
    onClick: (e, el, s) => s.toggle('isVisible')
  },
  Stage: {
    flow: 'x',
    opacity: (el, s) => (s.isVisible ? '1' : '0'),
    transition: 'opacity 0.5s',
    theme: 'dialog',
    boxSize: 'E',
    marginTop: 'A',
    Body: { margin: 'auto', text: 'Content' }
  }
}
```

---

## 18. Stopwatch

Start, stop, and reset timer.

```js
export const Stopwatch = {
  state: {
    running: false,
    time: 0
  },
  onRender: (el, s) => {
    setInterval(() => {
      if (s.running) s.update({ time: s.time + 1 })
    }, 1000)
  },
  Controls: {
    flow: 'x',
    gap: 'A',
    Button_Start: {
      text: (el, s) => (s.running ? 'Pause' : 'Start'),
      onClick: (e, el, s) => s.update({ running: !s.running })
    },
    Button_Reset: {
      text: 'Reset',
      onClick: (e, el, s) => s.update({ time: 0 })
    }
  },
  P: {
    text: (el, s) => 'Elapsed: ' + s.time + 's'
  }
}
```

---

## 19. Progress Bar

Fill dynamically with state.

```js
export const ProgressBar = {
  state: {
    progress: 0
  },
  Button: {
    text: 'Increase',
    onClick: (e, el, s) =>
      s.update({ progress: Math.min(s.progress + 10, 100) })
  },
  Bar: {
    width: (el, s) => s.progress + '%',
    height: 'A',
    background: 'green'
  },
  P: {
    text: (el, s) => 'Progress: ' + s.progress + '%'
  }
}
```

---

## 20. Draggable Box

Drag an element using mouse events.

```js
export const DragBox = {
  state: {
    dragging: false
  },
  Handle: {
    boxSize: 'D',
    background: 'blue',
    position: 'absolute',
    onMousedown: (e, el, s) => (s.dragging = true),
    onMouseup: (e, el, s) => (s.dragging = false),
    onMousemove: (e, el, s) => {
      if (s.dragging)
        el.update({
          left: e.clientX - 45 + 'px',
          top: e.clientY - 45 + 'px'
        })
    }
  }
}
```

---

## 21. Lazy Image

Load image on intersection using IntersectionObserver.

```js
export const LazyImage = {
  state: {
    loaded: false
  },
  onRender: (el, s) => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) s.update({ loaded: true })
    })
    observer.observe(el.Img.node)
  },
  Img: {
    src: (el, s) => (s.loaded ? 'https://picsum.photos/300/200' : ''),
    alt: 'Lazy loaded image'
  }
}
```

---

## 22. Text Typer

Animate text one character at a time.

```js
export const TextTyper = {
  state: {
    text: '',
    full: 'Welcome to Symbols!'
  },
  scope: {
    type: (el, s) => {
      let i = 0
      const int = setInterval(() => {
        if (i < s.full.length) {
          s.update({ text: s.text + s.full[i++] })
        } else clearInterval(int)
      }, 75)
    }
  },
  onRender: (el, s) => el.scope.type(el, s),
  P: {
    text: '{{ text }}',
    onClick: (ev, el, s) => {
      s.text = ''
      el.scope.type(el, s)
    }
  }
}
```

---

## 23. Temperature Converter

Convert Celsius to Fahrenheit in real time.

```js
export const TempConverter = {
  state: { c: 0, f: 32 },
  Input_C: {
    type: 'number',
    value: '{{ c }}',
    onInput: (e, el, s) => {
      const c = parseFloat(el.node.value)
      s.update({ c, f: (c * 9) / 5 + 32 })
    }
  },
  Input_F: {
    type: 'number',
    value: '{{ f }}',
    onInput: (e, el, s) => {
      const f = parseFloat(el.node.value)
      s.update({ f, c: ((f - 32) * 5) / 9 })
    }
  },
  P: {
    text: (el, s) => s.c + '°C = ' + s.f.toFixed(1) + '°F'
  }
}
```

---

## 24. Image Gallery

Cycle through images with state.

```js
export const ImageGallery = {
  state: {
    index: 0,
    images: [
      'https://picsum.photos/200/200',
      'https://picsum.photos/201/200',
      'https://picsum.photos/202/200'
    ]
  },
  Img: {
    src: (el, s) => s.images[s.index],
    alt: 'Gallery image'
  },
  Hr: {},
  Button_Next: {
    text: 'Next',
    onClick: (e, el, s) => s.update({ index: (s.index + 1) % s.images.length })
  }
}
```

---

## 25. Local Storage

Persist state between page reloads.

```js
export const LocalStorage = {
  state: { note: '' },
  onInit: (el, s) => {
    s.note = localStorage.getItem('note') || ''
  },
  Textarea: {
    placeholder: '{{ writeSomething | polyglot }}',
    value: '{{ note }}',
    onInput: (e, el, s) => {
      const value = el.node.value
      s.update({ note: value })
      localStorage.setItem('note', value)
    }
  },
  P: {
    text: (el, s) => 'Saved: ' + s.note
  }
}
```

---

## 26. Slider Control

Adjust a range and reflect in state.

```js
export const SliderControl = {
  state: { volume: 50 },
  Input: {
    type: 'range',
    min: 0,
    max: 100,
    value: '{{ volume }}',
    onInput: (e, el, s) =>
      s.update({
        volume: parseInt(el.node.value)
      })
  },
  P: {
    text: (el, s) => 'Volume: ' + s.volume
  }
}
```

---

## 27. Keyboard Shortcut

Listen for keypress and update state.

```js
export const KeyboardShortcut = {
  state: { key: 'None' },
  tabindex: '0',
  onKeydown: (e, el, s) => s.update({ key: e.key }),
  onRender: (el, s) => el.node.focus(),
  P: {
    text: (el, s) => 'Last key pressed: ' + s.key
  }
}
```

---

## 28. Mouse Tracker

Track cursor position in real-time.

```js
export const MouseTracker = {
  state: { x: 0, y: 0 },
  width: '100%',
  height: '100vh',
  onMousemove: (e, el, s) => s.update({ x: e.clientX, y: e.clientY }),
  P: {
    text: (el, s) => 'X: ' + s.x + ', Y: ' + s.y
  }
}
```
