# Design-to-Code Translator for Symbols

Convert designs into production-ready Symbols/DOMQL components. Use the Symbols framework and its declarative object syntax — not React, Vue, or other frameworks.

---

## Input

Provide one or more of: design description, wireframe, screenshot, or component specs.

---

## Deliverables

### 1. Component Architecture

- Component hierarchy tree (using Symbols PascalCase key nesting)
- State shape definition (plain object, not TypeScript interfaces)
- Data flow: parent state vs. child state vs. root state
- `extends` chain for each component

### 2. Production Code

- Complete, copy-paste ready Symbols component objects
- Responsive implementation using Symbols breakpoint syntax (`@tabletS`, `@mobileL`, etc.)
- Accessibility: semantic `tag` values, ARIA attributes via `aria: {}` shorthand / camelCase (`ariaLabel`) / kebab-case (`aria-label`)
- Loading states via `if` conditionals and state flags
- Animation via CSS transition properties on the component object

### 3. Styling Specifications

- CSS-in-props on each component (no separate CSS files)
- Design token usage: spacing tokens (`A`, `B`, `C`...), font size tokens, color tokens
- Theme integration via `theme: 'themeName'` referencing `designSystem/theme.js`
- Conditional styles via `.propName` (truthy) and `!propName` (falsy) syntax
- Hover/focus/active via `:hover`, `:focus`, `:active` keys

### 4. Design Token Integration

- Map colors to `designSystem/color.js` entries
- Map typography to `designSystem/typography.js` (font sizes use letter tokens: `Y`, `Z`, `A`, `B`, `C`, `D`, `E`)
- Map spacing to Symbols spacing tokens (`X`, `Z`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`)
- Map border radius to `round` property with tokens
- Define themes in `designSystem/theme.js` for reusable style groups

### 5. Asset Optimization

- Images via `Img` component with lazy loading pattern (see Cookbook recipe 21)
- Icons via `Icon` component with `name` prop referencing `designSystem.icons`
- Decorative/structural SVGs via `Svg` component (not for icons)
- Font loading handled by designSystem font/font_family tokens

### 6. Performance Considerations

- Use `childExtends` + `children` for repeated elements (avoid manual duplication)
- Use `if` for conditional rendering (removes from DOM when false)
- Use `scope` for component-local data that does not trigger re-renders
- Keep state minimal — derive computed values in function props

### 7. Testing Strategy

- Verify state transitions: toggle, update, replace behaviors
- Verify responsive breakpoints render correctly
- Verify `children` arrays render the correct number of items
- Verify conditional `if` shows/hides correctly based on state

### 8. Documentation

- Add "Designer's Intent" comments explaining why code decisions preserve the design vision
- Provide 3 usage variations showing different state/prop configurations
- List do's and don'ts specific to the component

---

## Rules

- All components are plain objects with `export const ComponentName = { ... }`
- Never use JSX, templates, or framework-specific syntax
- Never import between component files — reference by PascalCase key name
- Use `extends` to inherit from UIKit or default library components
- Use `state.update()` for state changes, never direct mutation (except `state.toggle()`)
- Use Symbols spacing/sizing tokens, not raw pixel values
- Place CSS properties directly on the component object (CSS-in-props)
