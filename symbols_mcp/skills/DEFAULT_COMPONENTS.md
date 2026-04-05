# Default Project Template — Complete Component Reference

All components from the default Symbols project template (default.symbo.ls).
Available in every project that includes the default library.
Reference by PascalCase key name — no imports needed.

For project configuration, see PROJECT_STRUCTURE.md. For design system values, see DEFAULT_STYLES.md.

---

## Components

### Accordion

```js
export const Accordion = {
  state: {
    activeAccordion: false
  },
  ButtonParagraph: {
    cursor: 'pointer',
    gap: 'D1',
    onClick: (event, element, state) => {
      state.update({
        activeAccordion: !state.activeAccordion
      })
    },
    P: {
      text: 'Question text one here'
    },
    Button: {
      text: '',
      Icon: {
        name: 'chevronDown',
        '.activeAccordion': {
          transform: 'rotate(-180deg)'
        },
        transition: 'transform .3s ease'
      }
    }
  },
  P: {
    text: 'Use a checkbox when users can select one option, multiple options, or no option from a list of a possible options',
    margin: '0',
    maxWidth: 'H',
    minWidth: 'H',
    position: 'absolute',
    left: '0',
    top: '2em',
    transition: 'min-height .3s ease, max-height .3s ease, opacity .3s ease',
    overflow: 'hidden',
    '.activeAccordion': {
      minHeight: '4em',
      maxHeight: '10em',
      opacity: '1'
    },
    '!activeAccordion': {
      minHeight: '0',
      maxHeight: '0',
      opacity: '0'
    }
  },
  flow: 'y',

  gap: 'Y2',

  position: 'relative'
}
```

### Avatar

```js
export const Avatar = {
  extends: 'smbls.Avatar',
  boxSize: 'C2'
}
```

### AvatarBadgeHgroup

```js
export const AvatarBadgeHgroup = {
  Avatar: {},
  Hgroup: {
    gap: 'V2',
    H: {
      display: 'flex',
      alignItems: 'center',
      gap: 'Y',
      Badge: {}
    },
    P: {}
  },
  extends: 'AvatarHgroup'
}
```

### AvatarChatPreview

```js
export const AvatarChatPreview = {
  Avatar: {},
  Flex: {
    flow: 'y',
    flex: '1',
    '> *': {
      minWidth: '100%'
    },
    ValueHeading: {
      H: {},
      UnitValue: {
        flow: 'row-reverse',
        Unit: {
          text: 'am'
        },
        Value: {
          text: '2:20'
        }
      }
    },
    NotCounterParagraph: {
      P: {
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        maxWidth: 'F2'
      },
      NotificationCounter: {}
    }
  },
  gap: 'Z1',

  minWidth: 'G3',

  align: 'center flex-start'
}
```

### AvatarHeading

```js
export const AvatarHeading = {
  Avatar: {},
  H: {
    tag: 'h6',
    lineHeight: '1em',
    text: 'Heading'
  },
  gap: 'X2',

  align: 'center flex-start'
}
```

### AvatarHgroup

```js
export const AvatarHgroup = {
  Avatar: {
    margin: '-X - - -'
  },
  Hgroup: {
    gap: 'X2',
    H: {
      tag: 'h6'
    },
    P: {}
  },
  gap: 'Z',

  align: 'center flex-start'
}
```

### AvatarHgroupIconButton

```js
export const AvatarHgroupIconButton = {
  Avatar: {},
  Hgroup: {
    H: {
      tag: 'h6'
    },
    P: {}
  },
  IconButton: {
    margin: '- - - auto',
    Icon: {
      name: 'copy'
    }
  },
  extends: 'AvatarHgroup',
  minWidth: 'G+Z2'
}
```

### AvatarHgroupSelect

```js
export const AvatarHgroupSelect = {
  Avatar: {},
  Hgroup: {
    H: {},
    P: {}
  },
  SelectPicker: {
    margin: '- - - auto',
    Select: {
      0: {
        value: 'Goat'
      },
      1: {
        value: 'Icon'
      }
    }
  },
  extends: 'AvatarHgroup',
  minWidth: 'G1'
}
```

### AvatarParagraph

```js
export const AvatarParagraph = {
  Avatar: {
    boxSize: 'B1'
  },
  P: {
    text: 'Can you join us today?',
    margin: '0'
  },
  align: 'center flex-start',

  gap: 'Y1'
}
```

### AvatarSelectPicker

```js
export const AvatarSelectPicker = {
  tag: 'label',
  Avatar: {},
  Select: {
    fontSize: 'A',
    boxSize: '100%',
    padding: '- B+V2 - Z',
    cursor: 'pointer',
    outline: 'none',
    appearance: 'none',
    flex: '1',
    zIndex: '2',
    lineHeight: 1,
    border: 'none',
    background: 'none',
    pointerEvents: 'All',
    color: 'title',
    ':focus-visible': {
      outline: 'none'
    },
    children: [
      {
        text: 'Nikoloza',
        value: 'Nikoloza'
      },
      {
        text: 'Svinchy',
        value: 'Svinchy'
      }
    ],
    childProps: {
      tag: 'option'
    }
  },
  Icon: {
    name: 'chevronDown',
    position: 'absolute',
    right: '0',
    margin: 'V - - -',
    fontSize: 'B'
  },
  round: '0',

  align: 'center flex-start',

  position: 'relative'
}
```

### AvatarSet

```js
export const AvatarSet = {
  display: 'flex',
  childExtends: 'Avatar',
  childProps: {
    border: 'solid codGray',
    borderWidth: 'X+W',
    ':first-child': {
      margin: '0 -Z1 0 0'
    },
    ':nth-child(2)': {
      margin: '0 -Z1 0 0'
    }
  },
  children: [{}, {}, {}]
}
```

### AvatarSetChatPreview

```js
export const AvatarSetChatPreview = {
  AvatarSet: {
    position: 'relative',
    boxSize: 'fit-content C2',
    border: '1px solid red',
    margin: '-Y2 - - -',
    childProps: {
      boxSize: 'C C',
      borderWidth: 'W',
      display: 'block',
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      ':first-child': {
        margin: 'Z2 0 0 0'
      },
      ':nth-child(2)': {
        margin: '0 0 0 Z1'
      },
      ':nth-child(3)': {
        margin: '-W 0 0 -Z1'
      }
    }
  },
  Flex: {
    flow: 'y',
    flex: '1',
    gap: 'W2',
    '> *': {
      minWidth: '100%'
    },
    ValueHeading: {
      minWidth: '0',
      maxWidth: '100%',
      H: {
        text: 'Design'
      },
      UnitValue: {
        flow: 'row-reverse',
        Unit: {
          text: 'am'
        },
        Value: {
          text: '2:20'
        }
      }
    },
    Flex: {
      gap: 'X2',
      Caption: {
        text: 'nick:',
        color: 'paragraph'
      },
      NotCounterParagraph: {
        flex: '1',
        justifyContent: 'space-between',
        P: {
          maxWidth: 'F2',
          whiteSpace: 'nowrap',
          overflow: 'hidden'
        },
        NotificationCounter: {}
      }
    }
  },
  gap: 'Z1',

  minWidth: 'G3',

  align: 'center flex-start'
}
```

### AvatarStatus

```js
export const AvatarStatus = {
  display: 'flex',
  Avatar: {},
  StatusDot: {
    position: 'absolute',
    bottom: 'W2',
    right: '0'
  },
  position: 'relative'
}
```

### AvatarStatusChatPreview

```js
export const AvatarStatusChatPreview = {
  AvatarStatus: {
    Avatar: {},
    StatusDot: {}
  },
  Flex: {
    flow: 'y',
    flex: '1',
    gap: 'W2',
    '> *': {
      minWidth: '100%'
    },
    ValueHeading: {
      H: {},
      UnitValue: {
        flow: 'row-reverse',
        Unit: {
          text: 'am'
        },
        Value: {
          text: '2:20'
        }
      }
    },
    NotCounterParagraph: {
      P: {},
      NotificationCounter: {}
    }
  },
  gap: 'Z1',

  minWidth: 'G3',

  align: 'center flex-start'
}
```

### Badge

```js
export const Badge = {
  tag: 'label',
  text: '-2.902',
  align: 'center center',

  theme: 'warning',

  round: 'C',

  lineHeight: '1em',

  boxSizing: 'content-box',

  padding: 'X1 Z1',

  backgroundColor: '',

  borderRadius: ''
}
```

### BadgeCaption

```js
export const BadgeCaption = {
  Caption: {
    text: 'CAPTION'
  },
  Badge: {},
  align: 'center flex-start',

  gap: 'Y'
}
```

### BadgeParagraph

```js
export const BadgeParagraph = {
  P: {
    margin: '0',
    text: `Hey team, I've finished the re...`,
    color: 'paragraph'
  },
  Badge: {},
  align: 'center space-between',

  gap: 'A'
}
```

### Breadcrumb

```js
export const Breadcrumb = {
  tag: 'nav',
  childExtends: 'Link',
  display: 'flex',
  align: 'center',
  childProps: {
    fontWeight: '400',
    textDecoration: 'none',
    scrollToTop: false,
    color: 'white 0.35',
    '&[href]': {
      color: 'title',
      '&:hover': {
        textDecoration: 'underline'
      }
    },
    '&:not([href])': {
      cursor: 'default'
    },
    '&:not(:first-child):before': {
      content: '""',
      display: 'inline-block',
      width: '2px',
      height: '2px',
      borderRadius: '100%',
      background: 'white',
      verticalAlign: '0.2em',
      marginInline: '.65em',
      opacity: '.5'
    }
  },
  children: (el, s, ctx) => {
    const routeArr = (s.root.route || window.top.location.pathname)
      .split('/')
      .slice(1)
    return routeArr
      .map((text, i) =>
        text === 'page'
          ? {
              href: '/pages',
              text: 'Page'
            }
          : el.getData('pages')['/' + text]
            ? {
                href: '/' + routeArr.slice(0, i + 1).join('/'),
                text: '/' + text
              }
            : {
                href: '/' + routeArr.slice(0, i + 1).join('/'),
                text: i === 0 ? ctx.utils.toTitleCase(text) : text
              }
      )
      .filter((_, k) => {
        const v = routeArr[k]
        return (
          !v.includes('-') && !v.includes('editor') && !v.includes('preview')
        )
      })
  }
}
```

### BulletCaption

```js
export const BulletCaption = {
  tag: 'caption',
  text: 'Orders history',
  align: 'center flex-start',
  gap: 'Y1',
  ':before': {
    content: '""',
    boxSize: 'Z1',
    background: 'blue',
    round: 'A2'
  }
}
```

### Button

```js
export const Button = {
  extends: 'smbls.Button'
}
```

### ButtonHeading

```js
export const ButtonHeading = {
  H: {
    tag: 'h6',
    text: 'Heading'
  },
  Button: {
    text: 'Button',
    theme: 'dialog'
  },
  align: 'center flex-start',

  gap: 'Z'
}
```

### ButtonHgroup

```js
export const ButtonHgroup = {
  Hgroup: {
    gap: 'X2',
    H: {
      tag: 'h6',
      text: 'Heading'
    },
    P: {}
  },
  Button: {
    text: 'Button',
    theme: 'dialog'
  },
  align: 'flex-start flex-start',

  gap: 'Z'
}
```

### ButtonParagraph

```js
export const ButtonParagraph = {
  display: 'flex',
  P: {
    text: `Didn't get the code?`,
    color: 'caption',
    margin: '0'
  },
  Button: {
    padding: '0',
    theme: 'transparent',
    text: 'Click to Resend'
  },
  alignItems: 'center',

  gap: 'X2'
}
```

### ButtonSet

```js
export const ButtonSet = {
  childExtends: 'Button',
  gap: 'Z',
  align: 'center flex-start',
  childProps: {
    theme: 'dialog',
    padding: 'A1 B2'
  },
  children: [
    {
      text: 'BUTTON 1'
    },
    {
      text: 'BUTTEN 2'
    }
  ]
}
```

### Caption

```js
export const Caption = {
  extends: 'smbls.Caption',
  text: 'It was the last day for our tribe, the year ends'
}
```

### CardNumberField

```js
export const CardNumberField = {
  display: 'flex',
  state: {
    value: 'XXXXXXXXXXXXXXXX'
  },
  childExtends: 'FixedNumberField',
  gap: '0',
  childProps: {
    Input: {
      textAlign: 'center',
      padding: 'X2 X',
      round: '0',
      outline: 'none',
      value: (el, s) => {
        const index = parseInt(el.parent.key)
        const valueArray = s.value
        const inputValue = el.node.value.split('')
        for (let i = 0; i < 4; i++) {
          const charIndex = index * 4 + i
          const numericPattern = /^\d$/
          const char = valueArray[charIndex]
          const isNumeric = numericPattern.test(char)
          if (isNumeric) inputValue[i] = char
        }
        return inputValue.join('')
      },
      ':focus-visible': {
        outline: 'none'
      },
      onUpdate: (el, s) => {
        el.node.value = el.props.value(el, s)
      },
      onInput: (ev, el, s, ctx) => {
        const index = parseInt(el.parent.key)
        const valueArray = s.value.split('')
        const inputValue = el.node.value
        for (let i = 0; i < 4; i++) {
          const charIndex = index * 4 + i
          valueArray[charIndex] = inputValue[i] || 'X'
        }
        s.update({
          value: valueArray.join('')
        })
        ctx.components.FixedNumberField.Input.onInput(ev, el, s, ctx)
      },
      onPaste: (ev, el, s) => {
        console.log(ev)
        const handlePastedInput = (event, validationFn) => {
          event.preventDefault()
          const pastedText = event.clipboardData.getData('text/plain')
          const value = validationFn ? validationFn(pastedText) : pastedText
          s.update({
            value
          })
        }
        const numericOnlyPaste = (input) => {
          return input.replace(/[^\d]/g, '')
        }
        const maxLengthPaste = (input, maxLength = 12) => {
          return input.slice(0, maxLength)
        }
        return handlePastedInput(ev, (text) => {
          return maxLengthPaste(numericOnlyPaste(text))
        })
      }
    },
    ':first-child input': {
      padding: 'X2 X X2 A1',
      round: 'A 0 0 A'
    },
    ':last-child input': {
      padding: 'X2 A1 X2 X',
      round: '0 A A 0'
    }
  },
  children: [{}, {}, {}, {}]
}
```

### CheckCaption

```js
export const CheckCaption = {
  Caption: {
    text: 'Caption'
  },
  Checkbox: {
    Input: {},
    Flex: {
      Icon: {
        name: 'check'
      }
    }
  },
  align: 'center flex-start',

  gap: 'Z'
}
```

### CheckCaptionList

```js
export const CheckCaptionList = {
  childExtends: 'CheckCaption',
  flow: 'y',
  gap: 'B',
  childProps: {
    Caption: {},
    Checkbox: {
      Input: {},
      Flex: {
        Icon: {
          name: 'check'
        }
      }
    }
  },
  children: [{}, {}]
}
```

### CheckHgroup

```js
export const CheckHgroup = {
  display: 'flex',
  Hgroup: {
    gap: 'W2',
    H: {
      tag: 'h6'
    },
    P: {}
  },
  Checkbox: {
    Input: {},
    Flex: {
      Icon: {
        name: 'check'
      }
    }
  },
  gap: 'Z'
}
```

### CheckHgroupList

```js
export const CheckHgroupList = {
  childExtends: 'CheckHgroup',
  flow: 'y',
  gap: 'B',
  childProps: {
    Hgroup: {
      gap: 'W2',
      H: {
        tag: 'h6'
      },
      P: {}
    },
    Checkbox: {
      Input: {},
      Flex: {
        Icon: {
          name: 'check'
        }
      }
    }
  },
  children: [{}, {}]
}
```

### CheckStep

```js
export const CheckStep = {
  Icon: {
    name: 'check',
    theme: 'dialog',
    display: 'block',
    boxSizing: 'content-box',
    padding: 'Y2',
    round: '100%'
  },
  H6: {
    text: 'Step'
  },
  Progress: {
    minWidth: 'E',
    maxWidth: 'E',
    value: 0,
    height: 'V',
    '.isActive': {
      value: 1
    }
  },
  align: 'center flex-start',

  gap: 'Z'
}
```

### CheckStepSet

```js
export const CheckStepSet = {
  display: 'flex',
  childExtends: 'CheckStep',
  gap: 'Z1',
  childProps: {
    Icon: {
      '.isActive': {
        theme: 'primary'
      }
    },
    Progress: {},
    ':last-child > progress': {
      hide: true
    }
  },
  children: [
    {
      Icon: {
        isActive: true
      }
    },
    {}
  ]
}
```

### CircleButton

```js
export const CircleButton = {
  extends: 'SquareButton',
  round: 'C'
}
```

### CircleProgress

```js
export const CircleProgress = {
  tag: 'progress',
  max: ({ props }) => props.max,
  progress: ({ props }) => props.progress,
  value: ({ props }) => props.value,
  boxSize: 'D D',
  value: 0.73,
  round: '100%',
  overflow: 'hidden',
  position: 'relative',
  '&::-webkit-progress-bar': {
    background: 'gray'
  },
  '&::-webkit-progress-value': {
    theme: 'primary'
  },
  ':after': {
    content: '""',
    position: 'absolute',
    width: 'B+B2',
    height: 'B+B2',
    round: '100%',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    background: 'codGray'
  }
}
```

### ConfirmationButtons

```js
export const ConfirmationButtons = {
  display: 'flex',
  childExtends: 'Button',
  gap: 'Y1',
  childProps: {
    theme: 'dialog',
    padding: 'Z1 B1'
  },
  children: [
    {
      text: 'No'
    },
    {
      text: 'YES'
    }
  ]
}
```

### CounterButton

```js
export const CounterButton = {
  extends: 'Button',
  position: 'relative',
  align: 'center space-between',
  padding: 'Z Z Z A1',
  minWidth: 'F',
  theme: 'field',
  Span: {
    text: 'Button'
  },
  NotificationCounter: {
    text: '7'
  }
}
```

### CounterIconButton

```js
export const CounterIconButton = {
  Icon: {
    name: 'smile'
  },
  NotificationCounter: {
    position: 'absolute',
    right: '-Y',
    top: '-W2'
  },
  extends: 'IconButton',
  position: 'relative'
}
```

### CounterParagraph

```js
export const CounterParagraph = {
  P: {
    margin: '0',
    text: `Hey team, I've finished the re...`,
    color: 'paragraph',
    maxWidth: 'E3+D1',
    overflow: 'hidden'
  },
  NotificationCounter: {},
  align: 'center space-between',
  gap: 'B'
}
```

### Field

```js
export const Field = {
  tag: 'label',
  Input: {
    round: 'C',
    padding: 'Z2 C Z2 A2',
    placeholder: 'Placeholder',
    minWidth: '100%'
  },
  Icon: {
    icon: 'info',
    fontSize: 'A2',
    lineHeight: '1em',
    position: 'absolute',
    right: 'Z2',
    opacity: '.45'
  },
  theme: 'field',

  align: 'center flex-start',

  round: 'D',

  position: 'relative'
}
```

### FieldCaption

```js
export const FieldCaption = {
  Caption: {
    tag: 'caption',
    text: 'Caption',
    lineHeight: '1em',
    fontSize: 'A',
    fontWeight: '400',
    padding: '- Y2 Z X',
    alignSelf: 'flex-start',
    whiteSpace: 'nowrap',
    textAlign: 'left'
  },
  Field: {
    width: '100%',
    Input: {},
    Icon: {}
  },
  flow: 'column',

  boxSize: 'fit-content fit-content'
}
```

### FixedNumberField

```js
export const FixedNumberField = {
  Input: {
    boxSize: 'B D',
    padding: 'X2 Z X2 A2',
    boxSizing: 'content-box',
    placeholder: '0000',
    letterSpacing: '.35em',
    maxlength: '4',
    textTransform: 'uppercase',
    style: {
      fontFamily: 'Courier, monospace'
    },
    onKeydown: (event, element, state) => {
      const numericPattern = /^\d$/
      const navigationKeys = [
        'Backspace',
        'ArrowLeft',
        'ArrowRight',
        'Tab',
        'Delete',
        'Home',
        'End',
        'Enter',
        'Escape'
      ]
      const ctrlShortcuts = ['a', 'c', 'v', 'x']

      const isNumeric = numericPattern.test(event.key)
      const isNavigationKey = navigationKeys.includes(event.key)
      const isCtrlShortcut =
        (event.metaKey || event.ctrlKey) && ctrlShortcuts.includes(event.key)

      // Allow only numeric input, navigation keys, and Ctrl shortcuts
      if (!isNumeric && !isNavigationKey && !isCtrlShortcut) {
        event.preventDefault()
      }
    },
    onInput: (event, element, state) => {
      if (element.node.value.length === 0) {
        element.parent.previousElement()?.Input?.node.focus()
      }
      if (element.node.value.length > 3) {
        element.parent.nextElement()?.Input?.node.focus()
      }
    }
  },
  extends: 'InputField'
}
```

### Flex

```js
export const Flex = {
  extends: 'smbls.Flex',
  flow: 'x'
}
```

### Footnote

```js
export const Footnote = {
  text: 'Footnote',
  extends: 'smbls.Footnote'
}
```

### Gif

```js
export const Gif = {
  extends: 'smbls.Img',
  src: 'https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExeWpmZDl5OXVzZGNjeHpuenRhZmNidHYzdzJiMXlkMmc3ODZwaHo1NiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/PkL0rQzXvMICwoKZGK/giphy.gif'
}
```

### Grid

```js
export const Grid = {
  extends: 'smbls.Flex'
}
```

### Group

```js
export const Group = {
  Title: {
    text: 'Field Title',
    color: 'caption',
    userSelect: 'none',
    whiteSpace: 'nowrap'
  },
  flow: 'y',
  align: 'flex-start',
  gap: 'Y1',
  minWidth: 'F',
  childProps: {
    width: '100%'
  }
}
```

### GroupField

```js
export const GroupField = {
  tag: 'label',
  extends: 'Group'
}
```

### H1

```js
export const H1 = {
  extends: 'smbls.H1',
  text: 'It was the last day for our tribe, the year ends'
}
```

### H2

```js
export const H2 = {
  extends: 'smbls.H2',
  text: 'It was the last day for our tribe, the year ends'
}
```

### H3

```js
export const H3 = {
  extends: 'smbls.H3',
  text: 'It was the last day for our tribe, the year ends'
}
```

### H4

```js
export const H4 = {
  extends: 'smbls.H4',
  text: 'It was the last day for our tribe, the year ends'
}
```

### H5

```js
export const H5 = {
  extends: 'smbls.H5',
  text: 'It was the last day for our tribe, the year ends'
}
```

### H6

```js
export const H6 = {
  extends: 'smbls.H6',
  text: 'It was the last day for our tribe, the year ends'
}
```

### Headline

```js
export const Headline = {
  text: 'Headline',
  extends: 'smbls.Headline'
}
```

### Hgroup

```js
export const Hgroup = {
  extends: 'smbls.Hgroup'
}
```

### HgroupSteps

```js
export const HgroupSteps = {
  Hgroup: {
    gap: 'Y1',
    H: {
      tag: 'h4',
      text: 'Symbols'
    },
    P: {
      text: 'The easiest way to build your own website'
    }
  },
  ProgressStepSet: {
    childProps: {
      flex: '1'
    }
  },
  flow: 'column',

  gap: 'A1',

  minWidth: 'G1',

  maxWidth: 'H'
}
```

### Hr

```js
export const Hr = {
  extends: 'smbls.Hr',
  minWidth: 'F'
}
```

### HrLegend

```js
export const HrLegend = {
  display: 'flex',
  text: 'Or',
  minWidth: 'G',
  fontWeight: '500',
  alignItems: 'center',
  gap: 'A',
  ':before': {
    content: '""',
    height: 'V',
    theme: 'dialog',
    round: 'C',
    flex: '1'
  },
  ':after': {
    content: '""',
    height: 'V',
    theme: 'dialog',
    round: 'C',
    flex: '1'
  }
}
```

### Icon

```js
export const Icon = {
  extends: 'smbls.Icon'
}
```

### IconButton

```js
export const IconButton = {
  Icon: {
    name: 'smile',
    fontSize: 'A2'
  },
  extends: 'Button',
  padding: 'A',

  aspectRatio: '1 / 1',

  boxSize: 'fit-content fit-content',

  round: '100%',

  boxSizing: 'content-box',

  align: 'center center',

  theme: 'dialog'
}
```

### IconButtonHeading

```js
export const IconButtonHeading = {
  H: {
    tag: 'h5',
    text: 'Heading'
  },
  IconButton: {},
  align: 'center flex-start',

  gap: 'Z'
}
```

### IconButtonHgroup

```js
export const IconButtonHgroup = {
  Hgroup: {
    gap: 'X2',
    H: {
      tag: 'h6',
      text: 'Heading'
    },
    P: {}
  },
  IconButton: {
    theme: 'dialog'
  },
  align: 'flex-start flex-start',

  gap: 'Z'
}
```

### IconButtonSet

```js
export const IconButtonSet = {
  display: 'flex',
  childExtends: 'IconButton',
  gap: 'Z',
  childProps: {
    Icon: {}
  },
  children: [
    {
      Icon: {
        name: 'sun'
      }
    },
    {
      Icon: {
        name: 'moon'
      }
    }
  ]
}
```

### IconCounterButton

```js
export const IconCounterButton = {
  extends: 'Button',
  position: 'relative',
  align: 'center flex-start',
  padding: 'Z Z Z Z1',
  minWidth: 'F',
  theme: 'field',
  gap: 'Z',
  Icon: {
    display: 'block',
    name: 'info'
  },
  Span: {
    text: 'Button'
  },
  NotificationCounter: {
    text: '7',
    margin: '- - - auto'
  }
}
```

### IconHeading

```js
export const IconHeading = {
  Icon: {
    name: 'logo',
    fontSize: 'C'
  },
  H: {
    tag: 'h5',
    text: 'Heading',
    lineHeight: '1em',
    fontWeight: '700'
  },
  gap: 'Z',

  align: 'center flex-start'
}
```

### IconHgroup

```js
export const IconHgroup = {
  Icon: {
    name: 'logo',
    display: 'block',
    color: 'blue',
    margin: '- X - -',
    fontSize: 'E'
  },
  Hgroup: {
    gap: 'Y',
    H: {
      tag: 'h2'
    },
    P: {}
  },
  gap: 'X',

  align: 'flex-start'
}
```

### IconInput

```js
export const IconInput = {
  tag: 'label',
  Input: {
    flex: '1',
    round: 'C',
    placeholder: 'Placeholder',
    padding: 'Z2 C Z2 A2',
    maxHeight: '100%'
  },
  Icon: {
    name: 'info',
    position: 'absolute',
    zIndex: '2',
    right: 'Z2'
  },
  minWidth: 'G',

  align: 'center flex-start',

  round: 'D',

  position: 'relative'
}
```

### IconText

```js
export const IconText = {
  extends: 'smbls.IconText'
}
```

### IcontextLink

```js
export const IcontextLink = {
  text: 'Follow Symbols',
  Icon: {
    fontSize: 'B',
    name: 'logo'
  },
  extends: ['Link', 'IconText'],
  gap: 'Y',

  maxHeight: '3em',

  cursor: 'pointer',

  round: 'D',

  fontWeight: '500'
}
```

### IconTextSet

```js
export const IconTextSet = {
  childExtends: ['IconText', 'Flex'],
  flow: 'y',
  gap: 'A',
  childProps: {
    align: 'center flex-start',
    gap: 'Y1',
    Icon: {}
  },
  children: [
    {
      Icon: {
        name: 'smile'
      },
      text: '+1 (555) 123-4567'
    },
    {
      Icon: {
        name: 'logo'
      },
      text: 'example@mail.com'
    }
  ]
}
```

### Img

```js
export const Img = {
  extends: 'smbls.Img',
  src: 'https://placehold.co/200'
}
```

### ImgButton

```js
export const ImgButton = {
  Img: {
    src: 'https://api.symbols.app/core/files/public/69325cf7ebee5529e0391f0b/download',
    boxSize: 'C1 D2'
  },
  extends: 'Button',
  theme: 'transparent',

  padding: '0',

  round: 'Z2',

  overflow: 'hidden'
}
```

### ImgHeading

```js
export const ImgHeading = {
  Img: {
    src: 'https://files-production-symbols-platform-development-en-d5-u3-p7x0.based.dev/fibd6dc13e/64be440c-ae12-4942-8da7-d772e06cb76c-b3013bf0-701c-4aff-b439-55d412265b2a-25215bc5-652d-40a7-8c99-af865865b74e.jpeg',
    widthL: 'auto',
    maxWidth: 'C',
    maxHeight: 'C',
    round: 'Z2'
  },
  H: {
    tag: 'h4',
    text: 'Heading'
  },
  align: 'center flex-start',

  gap: 'Y1'
}
```

### ImgHeadingButton

```js
export const ImgHeadingButton = {
  Img: {
    src: 'https://api.symbols.app/core/files/public/69325cf7ebee5529e0391f0b/download',
    boxSize: 'C1 D2',
    round: 'Z2'
  },
  H: {
    tag: 'h6',
    text: 'Heading'
  },
  extends: 'Button',
  theme: 'transparent',

  flow: 'y',

  gap: 'Z',

  padding: '0',

  round: '0'
}
```

### ImgHgroup

```js
export const ImgHgroup = {
  Img: {
    src: 'https://api.symbols.app/core/files/public/69325cf7ebee5529e0391f0b/download',
    boxSize: 'C+Y1 C2',
    round: 'Z2',
    margin: '-Y - - -'
  },
  Hgroup: {
    gap: 'W2',
    H: {
      tag: 'h5'
    },
    P: {}
  },
  align: 'center flex-start',

  gap: 'Y1'
}
```

### InputButton

```js
export const InputButton = {
  Input: {
    placeholder: 'Enter your email',
    minWidth: 'G+B1'
  },
  Button: {
    text: 'Sign up',
    theme: 'primary'
  },
  gap: 'Y2',
  align: 'center flex-start',
  height: 'C+X',
  '> *': {
    height: '100%',
    minHeight: '100%',
    maxHeight: '100%'
  }
}
```

### Italic

```js
export const Italic = {
  text: 'Italic text',
  extends: 'smbls.Italic'
}
```

### KangorooButton

```js
export const KangorooButton = {
  extends: 'Button',
  childExtends: 'IconText',
  padding: 'X',
  gap: 'A'
}
```

### LayerSimple

```js
export const LayerSimple = {
  Title: {
    text: 'Checklist'
  },
  Flex: {
    flow: 'column',
    gap: 'A',
    childProps: {
      gap: 'X',
      align: 'center'
    },
    childExtends: {
      Icon: {
        color: 'inactive',
        gap: 'Y1'
      },
      Span: {
        color: 'white',
        padding: '- - - X2'
      }
    },
    children: () => [
      {
        Icon: {
          icon: 'check'
        },
        Span: {
          text: 'Sun'
        }
      },
      {
        Icon: {
          icon: 'check'
        },
        Span: {
          text: 'Moon'
        }
      }
    ]
  },
  extends: 'Group',
  padding: 'Z A A A',

  margin: 'C -',

  round: 'Z2',

  gap: 'A',

  width: 'F1',

  background: 'gray'
}
```

### Link

```js
export const Link = {
  text: 'Link',
  extends: 'smbls.Link'
}
```

### LinkHgroup

```js
export const LinkHgroup = {
  Hgroup: {
    gap: 'X2',
    H: {
      tag: 'h2',
      text: 'Tbilisi'
    },
    P: {
      text: '35 Vazha-pshavela avenue.'
    }
  },
  Link: {
    text: 'Get direction'
  },
  flow: 'y',

  gap: 'Z'
}
```

### LinkParagraph

```js
export const LinkParagraph = {
  display: 'flex',
  P: {
    text: 'You are agree',
    color: 'caption',
    margin: '0'
  },
  Link: {
    padding: '0',
    theme: 'transparent',
    text: 'Privacy policy',
    textDecoration: 'underline',
    fontWeight: '400'
  },
  alignItems: 'center',

  gap: 'X2'
}
```

### LinkSet

```js
export const LinkSet = {
  tag: 'nav',
  childExtends: 'Link',
  align: 'center flex-start',
  gap: 'A',
  childProps: {
    cursor: 'pointer'
  },
  children: [
    {
      text: 'Link 1'
    },
    {
      text: 'Link 2'
    }
  ]
}
```

### ListingItem

```js
export const ListingItem = {
  display: 'flex',
  IconText: {
    color: 'paragraph',
    flow: 'column',
    gap: 'Z',
    padding: '0',
    tag: 'button',
    background: 'transparent',
    border: '0',
    fontSize: 'A',
    cursor: 'pointer',
    margin: 'W - -',
    Icon: {
      name: 'check',
      color: 'dim',
      '.isActive': {
        color: 'orange'
      }
    },
    '!isActive': {
      ':hover svg': {
        color: 'disabled'
      }
    },
    onClick: (ev, el, s) => {
      const isActive = s.isActive
      s.update({
        isActive: !isActive,
        upvotes: isActive ? s.upvotes - 1 : s.upvotes + 1
      })
    }
  },
  Hgroup: {
    H: {
      extends: 'Link',
      tag: 'h6',
      text: 'Flexbox in Editor',
      fontWeight: '700'
    },
    P: {
      text: null,
      childProps: {
        display: 'inline'
      },
      children: [
        'by ',
        {
          Link: {
            text: 'kiaynwang'
          }
        },
        ' ',
        {
          Link: {
            text: '3 hours ago'
          }
        },
        ' . ',
        {
          Link: {
            text: '49 commnts'
          }
        }
      ]
    }
  },
  gap: 'A2',

  alignItems: 'flex-start'
}
```

### LoadingGif

```js
export const LoadingGif = {
  extends: 'Img',
  src: 'https://assets.symbo.ls/loading.gif',
  width: '3.2em',
  pointerEvents: 'none',
  opacity: '.35',
  zIndex: '-1',
  inCenter: true,
  '.inCenter': {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate3d(-50%, -50%, 0)'
  }
}
```

### MessageModal

```js
export const MessageModal = {
  Hgroup: {
    gap: 'A',
    H: {
      text: 'Message'
    },
    P: {
      text: "Yes. If you change your mind and no longer wish to keep your iPhone, you have the option to return it to us. The returned iPhone must be in good condition and in the original packaging, which contains all accessories, manuals and instructions. Returns are subject to Apple's Sales and Refunds Policy."
    }
  },
  IconButton: {
    Icon: {
      name: 'x'
    }
  },
  extends: 'Modal',
  maxWidth: 'H'
}
```

### Modal

```js
export const Modal = {
  Hgroup: {
    gap: 'X1',
    H: {
      tag: 'h5',
      fontWeight: '700'
    },
    P: {}
  },
  IconButton: {
    position: 'absolute',
    right: 'X2',
    top: 'X2',
    round: '100%',
    $isSafari: {
      top: 'Z2',
      right: 'Z2'
    },
    Icon: {
      name: 'x'
    }
  },
  boxSize: 'fit-content',

  align: 'stretch flex-start',

  minWidth: 'G+B',

  position: 'relative',

  round: 'B',

  theme: 'dialog',

  flow: 'y',

  padding: 'A2 A2 A1 A2',

  borderStyle: 'none'
}
```

### NavigationArrows

```js
export const NavigationArrows = {
  display: 'flex',
  childExtends: 'IconButton',
  gap: 'Z',
  childProps: {
    round: '100%'
  },
  children: [
    {
      Icon: {
        name: 'chevronLeft'
      }
    },
    {
      Icon: {
        name: 'chevronRight'
      }
    }
  ]
}
```

### NavigationDots

```js
export const NavigationDots = {
  display: 'flex',
  tag: 'nav',
  childExtends: 'Link',
  gap: 'C1',
  childProps: {
    boxSize: 'Z',
    theme: 'dialog',
    round: '100%',
    cursor: 'pointer',
    text: '',
    '.isActive': {
      theme: 'primary'
    },
    ':active': {
      theme: 'primary'
    }
  },
  children: [
    {},
    {
      isActive: true
    }
  ]
}
```

### NotCounterParagraph

```js
export const NotCounterParagraph = {
  P: {
    margin: '0',
    text: `Hey team, I've finished the re...`,
    color: 'paragraph',
    maxWidth: 'E3+D1',
    overflow: 'hidden'
  },
  NotificationCounter: {},
  align: 'center space-between',

  gap: 'B'
}
```

### NotificationCounter

```js
export const NotificationCounter = {
  text: '3',
  widthRange: 'A',

  theme: 'primary',

  round: '100%',

  aspectRatio: '1 / 1',

  padding: 'W2',

  lineHeight: '1em',

  boxSizing: 'content-box',

  align: 'center center'
}
```

### NumberPicker

```js
export const NumberPicker = {
  state: {
    currentValue: 0
  },
  Minus: {
    extends: 'IconButton',
    Icon: {
      name: 'minus'
    },
    onClick: (event, element, state) => {
      if (state.currentValue <= 0) return
      state.update({
        currentValue: state.currentValue - 1
      })
    }
  },
  Value: {
    text: '{{ currentValue }}'
  },
  Plus: {
    extends: 'IconButton',
    Icon: {
      name: 'plus'
    },
    onClick: (event, element, state) => {
      state.update({
        currentValue: state.currentValue + 1
      })
    }
  },
  align: 'center flex-start',
  gap: 'Z',
  '> button': {
    theme: 'transparent'
  }
}
```

### P

```js
export const P = {
  extends: 'smbls.P',
  text: 'It was the last day for our tribe, the year ends'
}
```

### PackageFeatureItem

```js
export const PackageFeatureItem = {
  display: 'flex',
  tag: 'label',
  Input: {
    display: 'none',
    type: 'checkbox',
    ':checked + hgroup': {
      outline: '1.5px solid #0079FD'
    }
  },
  Hgroup: {
    width: '100%',
    padding: 'A1',
    round: 'A1',
    outline: '1.5px, solid, --color-line-dark',
    Icon: {
      order: '-1',
      margin: '- - A2',
      name: 'logo'
    }
  },
  cursor: 'pointer'
}
```

### Pagination

```js
export const Pagination = {
  Left: {
    extends: 'IconButton',
    Icon: {
      name: 'chevronLeft'
    },
    onClick: (event, element, state) => {
      state.update({})
    }
  },
  Flex: {
    gap: 'Z',
    childProps: {
      aspectRatio: '1 / 1',
      boxSize: 'C+Y2 C+Y2',
      round: '100%',
      padding: 'A',
      theme: 'field',
      isActive: (element, state) => state.active === parseInt(element.key),
      '.isActive': {
        theme: 'primary'
      }
    },
    childExtends: 'Button',
    children: [
      {
        text: '1'
      },
      {
        text: '2'
      },
      {
        text: '3'
      },
      {
        text: '4'
      },
      {
        text: '5'
      }
    ]
  },
  Right: {
    extends: 'IconButton',
    Icon: {
      name: 'chevronRight'
    },
    onClick: (event, element, state) => {
      state.update({})
    }
  },
  gap: 'A',

  align: 'center flex-start'
}
```

### Pills

```js
export const Pills = {
  display: 'flex',
  childExtends: 'Link',
  gap: 'C1',
  childProps: {
    boxSize: 'Z',
    round: '100%',
    cursor: 'pointer',
    text: '',
    '.isActive': {
      theme: 'primary'
    },
    '!isActive': {
      theme: 'tertiary'
    },
    ':active': {
      theme: 'primary'
    }
  },
  children: [
    {},
    {
      isActive: true
    }
  ],
  tag: 'nav'
}
```

### Progress

```js
export const Progress = {
  tag: 'progress',
  max: ({ props }) => props.max,
  progress: ({ props }) => props.progress,
  value: ({ props }) => props.value,
  height: 'X',
  minWidth: 'F3',
  round: 'Y',
  overflow: 'hidden',
  '::-webkit-progress-bar': {
    '@dark': {
      background: 'gray'
    },
    '@light': {
      background: 'hurricane'
    }
  },
  '::-webkit-progress-value': {
    borderRadius: 'Y',
    theme: 'primary'
  }
}
```

### ProgressStepSet

```js
export const ProgressStepSet = {
  display: 'flex',
  childExtends: 'Progress',
  gap: 'A',
  childProps: {
    minWidth: 'C'
  },
  children: [
    {
      value: 0.7
    },
    {}
  ]
}
```

### RadioCaption

```js
export const RadioCaption = {
  Caption: {
    text: 'Caption'
  },
  Radio: {
    Input: {},
    FLex: {
      ':after': {}
    }
  },
  align: 'center flex-start',

  gap: 'Z'
}
```

### RadioCaptionList

```js
export const RadioCaptionList = {
  childExtends: 'RadioCaption',
  flow: 'y',
  gap: 'B',
  childProps: {
    Caption: {
      text: 'Caption'
    },
    Radio: {
      Input: {},
      FLex: {
        ':after': {}
      }
    }
  },
  children: [{}, {}]
}
```

### RadioHgroup

```js
export const RadioHgroup = {
  display: 'flex',
  Hgroup: {
    gap: 'W2',
    H: {
      tag: 'h6'
    },
    P: {}
  },
  Radio: {
    Input: {},
    FLex: {
      ':after': {}
    }
  },
  gap: 'Z'
}
```

### RadioHgroupList

```js
export const RadioHgroupList = {
  childExtends: 'RadioHgroup',
  flow: 'y',
  gap: 'B',
  childProps: {
    Hgroup: {
      gap: 'W2',
      H: {
        tag: 'h6'
      },
      P: {}
    },
    Radio: {
      Input: {},
      FLex: {
        ':after': {}
      }
    }
  },
  children: [{}, {}]
}
```

### RadioMark

```js
export const RadioMark = {
  padding: 'Z1',
  theme: 'primary',
  round: '100%',
  boxSize: 'fit-content',
  ':after': {
    content: '""',
    boxSize: 'Z1',
    background: 'white',
    round: '100%',
    display: 'block'
  }
}
```

### RadioStep

```js
export const RadioStep = {
  RadioMark: {
    theme: 'field',
    '.isActive': {
      theme: 'primary'
    },
    ':after': {}
  },
  H6: {
    text: 'Step'
  },
  Progress: {
    minWidth: 'E',
    maxWidth: 'E',
    value: 0,
    height: 'V',
    margin: '- - - W',
    '.isActive': {
      value: 1
    }
  },
  align: 'center flex-start',

  gap: 'Y2'
}
```

### RadioSteps

```js
export const RadioSteps = {
  display: 'flex',
  childExtends: 'RadioStep',
  gap: 'Z1',
  childProps: {
    RadioMark: {},
    Progress: {},
    ':last-child > progress': {
      hide: true
    }
  },
  children: [
    {
      RadioMark: {
        isActive: true
      }
    },
    {}
  ]
}
```

### ScrollableList

```js
export const ScrollableList = {
  tag: 'nav',
  Flex: {
    maxHeight: 'D2',
    overflowY: 'auto',
    flow: 'y',
    padding: 'Z -',
    style: {
      listStyleType: 'none',
      '::-webkit-scrollbar': {
        display: 'none'
      }
    },
    childProps: {
      padding: 'Y1 A',
      cursor: 'pointer',
      align: 'flex-start',
      textAlign: 'left',
      fontWeight: '700',
      round: '0',
      theme: 'dialog',
      fontSize: 'C',
      ':hover': {
        theme: 'dialog-elevated'
      }
    },
    childExtends: 'Button',
    children: [
      {
        text: 'Item One'
      },
      {
        text: 'Item Two'
      }
    ]
  },
  position: 'relative',
  overflow: 'hidden',
  theme: 'field',
  round: 'A2',
  minWidth: 'F1',
  ':before, &:after': {
    content: '""',
    position: 'absolute',
    boxSize: 'B 100%',
    zIndex: '2',
    left: '0',
    pointerEvents: 'none'
  },
  ':before': {
    top: '0',
    '@light': {
      background: 'linear-gradient(to bottom,  #ebecf2 0%, transparent 100%)'
    },
    '@dark': {
      background: 'linear-gradient(to bottom, #171717 0%, transparent 100%)'
    }
  },
  ':after': {
    bottom: '-3px',
    '@light': {
      background: 'linear-gradient(to top,  #ebecf2 0%, transparent 100%)'
    },
    '@dark': {
      background: 'linear-gradient(to top, #171717 0%, transparent 100%)'
    }
  }
}
```

### Scrollbar

```js
export const Scrollbar = {
  display: 'flex',
  TrackContainer: {
    opacity: 1,
    transition: 'A defaultBezier opacity',
    flex: '1',
    margin: '- C1 - -',
    position: 'relative',
    background: 'red',
    height: 'fit-content',
    alignSelf: 'center',
    Track: {
      position: 'absolute',
      theme: 'field',
      round: 'A',
      height: '2px',
      background: '#d9d7d7 .5',
      left: '0',
      transformOrigin: 'left',
      width: '15%'
    }
  },
  NavigationArrows: {
    childProps: {
      padding: 'Z Z',
      Icon: {
        fontSize: 'B1'
      }
    }
  },
  minWidth: 'I'
}
```

### Search

```js
export const Search = {
  tag: 'search',
  Input: {
    type: 'search',
    placeholder: 'Type a command or search',
    width: '100%',
    padding: 'Z2 C+W2 Z2 A2',
    theme: 'transparent',
    ':focus ~ button': {
      opacity: '1'
    }
  },
  Icon: {
    name: 'search',
    position: 'absolute',
    right: 'Z+W2',
    fontSize: 'B'
  },
  minWidth: 'G+A2',

  gap: 'Z',

  theme: 'field',

  round: 'D2',

  align: 'center flex-start',

  position: 'relative'
}
```

### SearchDropdown

```js
export const SearchDropdown = {
  state: {
    isOpen: false,
    selected: 'Search and Select',
    data: ['Los Angeles', 'New York', 'San Fransisco', 'San Diego'],
    filtered: [],
    searchValue: ''
  },
  SelectedContainer: {
    text: '{{ selected }}',
    padding: 'Z A2',
    minHeight: 'B2',
    position: 'relative',
    cursor: 'pointer',
    color: 'caption',
    isSelected: (el, s) => s.selected !== 'Search and Select',
    '.isSelected': {
      color: 'blue'
    },
    onClick: (e, el, s) => s.toggle('isOpen')
  },
  Options: {
    show: (el, s) => s.isOpen,
    borderWidth: '1px 0 0 0',
    borderStyle: 'solid',
    borderColor: 'line .35',
    padding: 'Z Z2',
    theme: 'dialog',
    flexFlow: 'y',
    round: '0 0 A2 A2',
    Input: {
      theme: 'field-dialog',
      placeholder: 'Search and Select',
      padding: 'Y2 A',
      margin: '- -Y',
      display: 'block',
      minWidth: '',
      boxSizing: 'border-box',
      border: 'none',
      outline: 'none',
      onInput: (e, el, state) => {
        const value = e.target.value.trim().toLowerCase()
        const filtered = state.data.filter((item) =>
          item.toLowerCase().includes(value)
        )
        state.replace({
          searchValue: value,
          filtered: filtered
        })
      }
    },
    Results: {
      marginTop: 'X',
      show: (el, s) => !!s.searchValue && s.filtered.length,
      children: (el, s) => s.filtered,
      childrenAs: 'state',
      childProps: {
        padding: 'Z',
        text: '{{ value }}',
        onClick: (ev, el, s) => {
          s.parent.update({
            selected: s.value,
            isOpen: false,
            searchValue: ''
          })
        }
      }
    },
    Placeholder: {
      padding: 'Z',
      show: (el, s) => !s.searchValue,
      text: 'Enter name to search',
      color: 'disabled'
    },
    NoResults: {
      padding: 'Z',
      show: (el, s) => !!s.searchValue && !s.filtered.length,
      text: 'No results found',
      color: 'disabled'
    }
  },
  position: 'relative',

  width: 'G3',

  theme: 'field',

  round: 'A2'
}
```

### SearchDropdown_copy

```js
export const SearchDropdown_copy = {
  state: {
    isOpen: false,
    selected: 'Search and Select',
    data: ['Los Angeles', 'New York', 'San Fransisco', 'San Diego'],
    filtered: [],
    searchValue: ''
  },
  SelectedContainer: {
    text: '{{ selected }}',
    padding: 'Z A2',
    background: '#f5f5f5',
    color: 'black',
    borderBottom: '1px solid #ccc',
    minHeight: 'B2',
    position: 'relative',
    cursor: 'pointer',
    isSelected: (el, s) => s.selected !== 'Search and Select',
    '.isSelected': {
      color: 'title'
    },
    onClick: (e, el, s) => s.toggle('isOpen')
  },
  Options: {
    show: (el, s) => s.isOpen,
    borderWidth: '1px 0 0 0',
    borderStyle: 'solid',
    borderColor: 'line .35',
    padding: 'Z Z2',
    theme: 'dialog',
    flexFlow: 'y',
    round: '0 0 A2 A2',
    Input: {
      theme: 'field-dialog',
      placeholder: 'Search and Select',
      padding: 'Y2 A',
      margin: '- -Y',
      display: 'block',
      minWidth: '',
      boxSizing: 'border-box',
      border: 'none',
      outline: 'none',
      onInput: (e, el, state) => {
        const value = e.target.value.trim().toLowerCase()
        const filtered = state.data.filter((item) =>
          item.toLowerCase().includes(value)
        )
        state.replace({
          searchValue: value,
          filtered: filtered
        })
      }
    },
    Results: {
      marginTop: 'X',
      show: (el, s) => !!s.searchValue && s.filtered.length,
      children: (el, s) => s.filtered,
      childrenAs: 'state',
      childProps: {
        padding: 'Z',
        text: '{{ value }}',
        onClick: (ev, el, s) => {
          s.parent.update({
            selected: s.value,
            isOpen: false,
            searchValue: ''
          })
        }
      }
    },
    Placeholder: {
      padding: 'Z',
      show: (el, s) => !s.searchValue,
      text: 'Enter name to search',
      color: 'disabled'
    },
    NoResults: {
      padding: 'Z',
      show: (el, s) => !!s.searchValue && !s.filtered.length,
      text: 'No results found',
      color: 'disabled'
    }
  },
  color: 'black',

  position: 'relative',

  width: 'G3',

  theme: 'field',

  round: 'A2'
}
```

### SectionHeader

```js
export const SectionHeader = {
  display: 'flex',
  tag: 'header',
  Hgroup: {},
  IconButtonSet: {},
  gap: 'C1'
}
```

### Select

```js
export const Select = {
  extends: 'smbls.Select'
}
```

### SelectField

```js
export const SelectField = {
  Select: {
    children: [
      {
        value: '',
        text: 'Select one...'
      },
      {
        value: 'mazda',
        text: 'Mazda'
      },
      {
        value: 'bmw',
        text: 'BMW'
      }
    ]
  },
  Icon: {
    margin: '- Z2 - -'
  },
  extends: 'SelectPicker',
  theme: 'field',

  minWidth: 'G',

  padding: 'A A1',

  round: 'D'
}
```

### SelectHgroup

```js
export const SelectHgroup = {
  display: 'flex',
  Hgroup: {
    gap: 'V2',
    H: {
      tag: 'h6'
    },
    P: {}
  },
  SelectPicker: {
    margin: '- - - auto',
    Select: {
      children: () => [
        {
          value: 'Goat'
        },
        {
          value: 'Icon'
        }
      ]
    }
  },
  gap: 'C'
}
```

### SelectPicker

```js
export const SelectPicker = {
  tag: 'label',
  round: '0',
  align: 'center flex-start',
  position: 'relative',
  Select: {
    fontSize: 'A',
    boxSize: '100%',
    padding: '- B+V2 - -',
    cursor: 'pointer',
    outline: 'none',
    appearance: 'none',
    flex: '1',
    zIndex: '2',
    lineHeight: 1,
    border: 'none',
    background: 'none',
    pointerEvents: 'All',
    color: 'title',
    ':focus-visible': {
      outline: 'none'
    },
    children: [
      {
        text: 'Nikoloza',
        value: 'Nikoloza'
      },
      {
        text: 'Svinchy',
        value: 'Svinchy'
      }
    ],
    childProps: {
      tag: 'option'
    }
  },
  Icon: {
    name: 'chevronDown',
    position: 'absolute',
    right: '0',
    margin: 'V - - -',
    fontSize: 'B'
  }
}
```

### SquareButton

```js
export const SquareButton = {
  extends: 'Button',
  fontSize: 'A',
  width: 'A',
  padding: 'Z',
  aspectRatio: '1 / 1',
  icon: 'smile',
  boxSize: 'fit-content fit-content',
  justifyContent: 'center',
  round: 'Z2',
  boxSizing: 'content-box'
}
```

### Stars

```js
export const Stars = {
  display: 'flex',
  childExtends: 'Icon',
  fontSize: 'B',
  gap: 'W',
  children: [
    {
      name: 'star'
    },
    {
      name: 'star'
    },
    {
      name: 'star'
    },
    {
      name: 'star'
    },
    {
      name: 'star'
    }
  ]
}
```

### StatusDot

```js
export const StatusDot = {
  widthRange: 'A+W',
  aspectRatio: '1/1',
  theme: 'success',
  round: '100%',
  '@dark': {
    border: 'solid codGray',
    borderWidth: 'X1'
  },
  '@light': {
    border: 'solid concrete',
    borderWidth: 'X1'
  }
}
```

### StoryCard

```js
export const StoryCard = {
  display: 'flex',
  Img: {
    src: 'https://files-production-symbols-platform-development-en-d5-u3-p7x0.based.dev/fibd6dc13e/64be440c-ae12-4942-8da7-d772e06cb76c-b3013bf0-701c-4aff-b439-55d412265b2a-25215bc5-652d-40a7-8c99-af865865b74e.jpeg',
    boxSize: '100%',
    zIndex: '2',
    round: 'A'
  },
  Icon: {
    icon: 'smile',
    position: 'absolute',
    zIndex: '2',
    top: '35%',
    left: '50%',
    fontSize: 'J1+F1',
    transform: 'translate(-50%, -50%)',
    color: 'white'
  },
  HgroupSteps: {
    position: 'absolute',
    bottom: '0',
    left: '0',
    zIndex: '2',
    minWidth: '100%',
    maxWidth: '100%',
    round: '0',
    padding: 'B1',
    theme: 'field',
    Hgroup: {
      H: {
        text: 'Symbols'
      },
      P: {
        color: 'white .65'
      }
    },
    ProgressStepSet: {
      childProps: {
        theme: 'field-dialog'
      },
      children: () => [{}, {}]
    }
  },
  position: 'relative',

  round: 'B2',

  boxSize: 'H1 G3',

  alignSelf: 'flex-start',

  overflow: 'hidden'
}
```

### Strong

```js
export const Strong = {
  text: 'Strong text',
  extends: 'smbls.Strong'
}
```

### Subhead

```js
export const Subhead = {
  text: 'Subhead',
  extends: 'smbls.Subhead'
}
```

### SubmitButton

```js
export const SubmitButton = {
  extends: 'Input',
  type: 'submit',

  value: 'Submit',

  padding: 'Z2 B'
}
```

### TabSet

```js
export const TabSet = {
  display: 'flex',
  childExtends: 'Button',
  padding: 'V2+V2',
  round: 'D',
  background: 'gray .1',
  width: 'fit-content',
  children: [
    {
      text: 'build',
      isActive: true,
      theme: 'dialog-elevated'
    },
    {
      text: 'test'
    }
  ],
  childProps: {
    Icon: null,
    round: 'D',
    fontWeight: '400',
    padding: 'Z B1',
    textTransform: 'capitalize',
    '.isActive': {
      theme: 'document'
    },
    theme: 'transparent'
  }
}
```

### TextareaIconButton

```js
export const TextareaIconButton = {
  display: 'flex',
  Textarea: {
    minHeight: 'C+Y',
    maxHeight: 'C+Y',
    minWidth: 'G1',
    round: 'D',
    padding: 'A A A A2'
  },
  IconButton: {
    theme: 'primary',
    Icon: {
      name: 'send'
    }
  },
  gap: 'Y1'
}
```

### ToggleCaption

```js
export const ToggleCaption = {
  Caption: {
    text: 'Caption'
  },
  Toggle: {
    Input: {},
    Flex: {
      ':after': {}
    }
  },
  align: 'center flex-start',

  gap: 'Z'
}
```

### ToggleCaptionList

```js
export const ToggleCaptionList = {
  childExtends: 'ToggleCaption',
  flow: 'y',
  gap: 'B',
  childProps: {
    Caption: {
      text: 'Caption'
    },
    Toggle: {
      Input: {},
      Flex: {
        ':after': {}
      }
    }
  },
  children: [{}, {}]
}
```

### ToggleHgroup

```js
export const ToggleHgroup = {
  display: 'flex',
  Hgroup: {
    gap: 'W2',
    H: {
      tag: 'h6'
    },
    P: {}
  },
  Toggle: {
    margin: '- - - auto',
    Input: {},
    Flex: {
      after: {}
    }
  },
  gap: 'Z'
}
```

### ToggleHgroupList

```js
export const ToggleHgroupList = {
  childExtends: 'ToggleHgroup',
  flow: 'y',
  gap: 'B',
  childProps: {
    Hgroup: {
      gap: 'W2',
      H: {
        tag: 'h6'
      },
      P: {}
    },
    Toggle: {
      margin: '- - - auto',
      Input: {},
      Flex: {
        after: {}
      }
    }
  },
  children: [{}, {}]
}
```

### U

```js
export const U = {
  text: 'Underlined text',
  extends: 'smbls.Underline'
}
```

### UnitValue

```js
export const UnitValue = {
  Unit: {
    text: '$'
  },
  Value: {
    text: '73'
  },
  align: 'center flex-start',
  gap: 'V',
  childProps: {
    lineHeight: '1em',
    color: 'title'
  }
}
```

### UploadButton

```js
export const UploadButton = {
  text: 'Choose file',
  Input: {
    type: 'file',
    padding: '0',
    inset: '0 0 0 0',
    position: 'absolute',
    boxSize: '100% 100%',
    cursor: 'pointer',
    top: '0',
    left: '0',
    opacity: '0'
  },
  extends: 'Button',
  position: 'relative',

  padding: '0',

  cursor: 'pointer',

  theme: 'transparent',

  color: 'blue'
}
```

### UploadIconButton

```js
export const UploadIconButton = {
  Icon: {
    name: 'upload'
  },
  Input: {
    type: 'file',
    padding: '0',
    inset: '0 0 0 0',
    position: 'absolute',
    boxSize: '100% 100%',
    cursor: 'pointer',
    top: '0',
    left: '0',
    opacity: '0'
  },
  extends: 'IconButton',
  position: 'relative',

  padding: '0',

  cursor: 'pointer'
}
```

### UserNavbar

```js
export const UserNavbar = {
  AvatarStatus: {
    margin: '-W - - -',
    Avatar: {},
    Status: {}
  },
  Hgroup: {
    gap: 'W',
    H: {
      tag: 'h5',
      text: 'Nika Tomadze'
    },
    P: {
      text: 'active now'
    }
  },
  IconButtonSet: {
    margin: '- - - auto',
    childProps: {
      Icon: {}
    },
    children: () => [{}, {}]
  },
  minWidth: 'G2',

  align: 'center flex-start',

  gap: 'Z'
}
```

### ValueCircleProgress

```js
export const ValueCircleProgress = {
  CircleProgress: {
    ':after': {}
  },
  UnitValue: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    flow: 'row-reverse',
    zIndex: '5',
    gap: 'V',
    Value: {
      text: '73'
    },
    Unit: {
      text: '%'
    }
  },
  border: '2'
}
```

### ValueHeading

```js
export const ValueHeading = {
  H: {
    tag: 'h6',
    text: 'Kobe Bryant'
  },
  UnitValue: {
    margin: '- - - auto',
    Unit: {},
    Value: {}
  },
  minWidth: 'F3',

  align: 'center space-between'
}
```

### ValueProgress

```js
export const ValueProgress = {
  Progress: {
    maxWidth: '100%',
    flex: '1',
    value: 0.73
  },
  UnitValue: {
    flow: 'row-reverse',
    color: 'paragraph',
    Value: {
      text: '73'
    },
    Unit: {
      text: '%'
    }
  },
  align: 'center flex-start',

  gap: 'Y2'
}
```

### Video

```js
export const Video = {
  extends: 'smbls.Video',
  src: 'https://examplefiles.org/files/video/mp4-example-video-download-640x480.mp4'
}
```

---
