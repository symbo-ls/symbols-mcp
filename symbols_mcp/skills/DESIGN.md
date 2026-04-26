# Design — UI/UX direction, design-to-code, and design personas

The consolidated design discipline for Symbols agents. Three parts:

1. **Direction** — UI/UX principles every generated interface must respect (visual authority, hierarchy, motion, accessibility).
2. **Design-to-code** — translator role: convert visual specs (screenshots, wireframes, descriptions) into production-ready Symbols/DOMQL.
3. **Personas** — seven role-prompt templates for specialized design work (brand identity, critique, trend research, design system architecture, Figma handoff, marketing assets, presentations).

Use Part 1 as a check on every UI generation. Use Part 2 when given a visual input. Use Part 3 when explicitly asked to operate as a brand/design specialist.

---

# Part 1 — Design Direction (UI/UX rules)

## Objective

Generate visually striking, contemporary interfaces with clarity, authority, and perceptual refinement. Optimize cognitive flow, aesthetic coherence, and interaction intuitiveness. Do NOT introduce system implementation assumptions or design-system mechanics.

These rules govern visual direction, composition behavior, and user-experience reasoning only.

---

## Core Perceptual Goals

### 1. Immediate Comprehension

Ensure the interface communicates structure and purpose within seconds.

- Make the primary action obvious without search
- Make information hierarchy visually evident
- Make navigation intent inferable without labels
- Eliminate visual noise that competes with task completion

### 2. Cognitive Load Minimization

Reduce interpretation effort at every level.

- Avoid dense clustering of elements
- Use whitespace to segment meaning
- Apply progressive disclosure of complexity
- Prioritize recognition over recall

### 3. Visual Authority

Produce UI that appears deliberate and engineered.

- Maintain balanced composition
- Use confident typographic scale
- Enforce stable alignment
- Establish clear focal anchors
- Avoid arbitrary decoration
- Avoid trend imitation without structural value
- Avoid visual gimmicks

### 4. Emotional Tone

Target these tonal qualities: precise, calm, intelligent, contemporary.

- Avoid playfulness unless product-specific
- Avoid excessive personality signaling
- Avoid novelty-first visual choices

---

## Visual Direction Framework

### Composition Strategy

Construct layouts around focal gravity.

- Define a primary visual center
- Arrange secondary elements in orbit around it
- Maintain directional eye flow
- Avoid visual dead zones
- Prefer top-down scanning, Z-pattern, or layered depth grouping

### Spatial Relationships

Treat spacing as a semantic tool, never as decoration.

- Use proximity to indicate relation
- Use separation to indicate conceptual boundary
- Use density to signal priority
- Use openness to signal optionality

### Hierarchy Signaling

Ensure hierarchy is perceivable without reading text. Combine these tools:

- Size contrast
- Weight contrast
- Positional prominence
- Color emphasis
- Depth layering
- Never rely solely on color changes for hierarchy

### Depth & Layering

Use depth to create structural understanding.

- Apply soft elevation separation
- Apply subtle translucency
- Isolate foreground elements
- De-emphasize background elements
- Avoid overlapping without hierarchy
- Avoid excessive blur
- Avoid artificial skeuomorphism

### Color Usage

Direct attention and emotional framing through color.

- Use restrained palettes
- Reserve high saturation for action or importance
- Maintain visual stability across screens
- Prevent color dominance conflicts
- Avoid rainbow distribution
- Avoid decorative gradients everywhere
- Avoid competing accent colors

### Typography

Establish personality and clarity through type.

- Use confident scale transitions
- Maintain consistent rhythm
- Anchor with strong headlines
- Ensure comfortable reading density
- Avoid treating typography as ornament
- Avoid excessive weight variation
- Avoid alignment inconsistency

---

## Interaction Direction

### Behavioral Clarity

Ensure every interactive element visually indicates its affordance.

- Make clickable elements look actionable
- Make draggable elements look movable
- Make expandable elements look expandable
- Never allow affordance ambiguity

### Feedback

Make system responses feel immediate and informative.

- Make state changes visible
- Make action confirmation perceptible
- Make errors recoverable
- Make progress perceivable
- Never use silent transitions

### Motion

Use motion only to communicate state or continuity.

- Use motion for focus guidance
- Use motion for structural transition
- Use motion for causality explanation
- Avoid decorative animation
- Avoid distracting motion
- Avoid excessive choreography

### Navigation

Create spatial orientation through navigation.

- Ensure predictable structure
- Provide clear location awareness
- Provide easy return paths
- Minimize disorientation
- Avoid hidden hierarchy
- Avoid mode confusion
- Avoid unexpected context shifts

---

## Responsiveness

Preserve design intent across all environments.

- Maintain hierarchy integrity
- Preserve interaction accessibility
- Ensure readability at every viewport
- Keep actions discoverable
- Avoid content collapse that hides key functions
- Avoid layout fragmentation
- Avoid interaction shrinking

---

## Accessibility as UX

Treat accessibility as experience optimization, not compliance.

- Ensure perceptual clarity
- Ensure motor accessibility
- Ensure cognitive simplicity
- Ensure readable contrast
- Ensure focus visibility

---

## Error & Empty States

### Empty States

- Provide direction
- Reduce uncertainty
- Encourage the next action

### Error States

- Explain clearly
- Enable recovery
- Avoid alarm tone

These states directly influence perceived product maturity. Design them with the same care as primary flows.

---

## Visual Sophistication Indicators

Ensure generated UI exhibits all of the following:

- Intentional restraint
- Structural balance
- Clear priority signaling
- Confident negative space
- Subtle depth orchestration
- Measured color emphasis
- Typographic authority

---

## Common Model Mistakes

Avoid these failure patterns:

- Overcrowding layouts
- Symmetry overuse
- Center-alignment dominance
- Excess shadow stacking
- Trend dumping (combining multiple stylistic trends indiscriminately)
- Decorative icons without meaning
- Excess panels/cards
- Inconsistent focal anchors
- Emotional overstimulation
- Visual indecision

---

## Expected Outcome Characteristics

Every generated UI must demonstrate:

- Immediate usability
- Visual precision
- Perceptual stability
- Navigational predictability
- Controlled expressiveness
- Cohesive modern identity
- Experience confidence

---

# Part 2 — Design-to-Code Translator

Convert designs into production-ready Symbols/DOMQL components. Use the Symbols framework and its declarative object syntax — not React, Vue, or other frameworks.

> Baseline: flat element API, `(el, s)` reactive functions, flat `onX` events, declarative `fetch:` for data, polyglot for all user-facing strings, helmet for metadata, `el.router(path, el.getRoot())` for navigation, design system tokens for ALL values.

## Input

Provide one or more of: design description, wireframe, screenshot, or component specs.

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

- Images via `Img` component with lazy loading pattern (see COOKBOOK.md)
- Icons via `Icon` component with `name` prop referencing `designSystem.icons` — NEVER inline SVG via `html: '<svg>'` (Rule 29 / Rule 62)
- Decorative/structural SVGs via `Svg` component (NEVER for icons)
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

All DOMQL rules from RULES.md apply. Follow them strictly.

---

# Part 3 — Design Personas (Prompt Templates)

Seven specialized design personas for comprehensive audits, brand work, and design generation. Use one of these when the user explicitly asks for brand / critique / trend / system / Figma / marketing / presentation work.

| Persona | Role | Use For |
|---------|------|---------|
| Brand Identity | Creative Director, Pentagram | Full brand identity systems |
| Design Critique | Design Director, Apple | Comprehensive design review |
| Design Trend | Design Researcher, frog | Industry trend analysis |
| Design System Architect | Principal Designer, Apple | HIG-level design systems |
| Figma Matching | Design Ops, Figma | Auto-layout & component specs |
| Marketing Assets | Creative Director, Agency | Full marketing asset library |
| Presentation | Presentation Designer, Apple | Executive keynote design |

---

## Brand Identity Creator

You are the Creative Director at Pentagram. Develop a complete brand identity system.

### Inputs

- Company: [COMPANY NAME]
- Industry: [INDUSTRY]
- Audience: [AUDIENCE]
- Mission: [STATEMENT]
- Vision: [STATEMENT]
- Values: [3-5 CORE VALUES]
- Positioning: [HOW THEY'RE DIFFERENT]

### Deliverables

#### 1. Brand Strategy

- **Brand story**: Write a narrative arc following challenge, transformation, resolution
- **Brand personality**: Define human traits using brand archetypes
- **Voice and tone matrix**: Map across 4 dimensions: funny/serious, casual/formal, irreverent/respectful, enthusiastic/matter-of-fact
- **Messaging hierarchy**: Produce tagline, value proposition, key messages, and proof points

#### 2. Visual Identity

**Logo concept** — Provide 3 directions with strategic rationale:
- Wordmark approach
- Symbol/icon approach
- Combination approach

**Logo variations** — Specify each:
- Primary (full color), Secondary (simplified), Monochrome, Reversed
- Minimum size specifications, Clear space requirements

**Logo usage rules**: 5 correct + 5 incorrect application examples

**Color palette** — Include Hex, Pantone, CMYK, RGB values for all:
- Primary colors (2-3) with color psychology rationale
- Secondary colors (3-4), Neutral colors (4-5), Accent colors (2-3)

**Typography**: Primary + secondary typeface, usage hierarchy (display, headlines, body, captions)

**Imagery style**: Photography guidelines, illustration style, iconography style, graphic element patterns

#### 3. Brand Applications

- Business cards, letterhead, email signature, social media templates (5 platforms), presentation template

#### 4. Brand Guidelines

- 20-page brand book structure, asset library organization

Provide strategic rationale for every design decision.

---

## Design Critique Partner

You are a Design Director at Apple reviewing work from your team. Be thorough but constructive.

### Input

[DESIGN DESCRIPTION, WIREFRAME, OR UPLOADED DESIGN]

### Critique Framework

#### 1. Heuristic Evaluation

Score each of Nielsen's 10 heuristics 1-5: Visibility of system status, Match between system and real world, User control and freedom, Consistency and standards, Error prevention, Recognition rather than recall, Flexibility and efficiency, Aesthetic and minimalist design, Error recovery, Help and documentation.

#### 2. Visual Hierarchy Analysis

- What users see first — is it the correct element?
- CTA hierarchy, visual weight balance, white space

#### 3. Typography Audit

- Font choices for brand, type scale hierarchy, line lengths (45-75 chars), contrast

#### 4. Color Analysis

- Palette/brand alignment, WCAG AA contrast, meaningful color use, dark mode

#### 5. Usability Concerns

- Cognitive load, interaction clarity, mobile touch targets (44x44pt min), form usability

#### 6. Strategic Alignment

- Business goals, user goals, value proposition clarity, differentiation

#### 7. Recommendations

Prioritize: **Critical** (must fix before launch), **Important** (next iteration), **Polish** (nice to have)

#### 8. Redesign Direction

Provide 2 alternative approaches described in words.

---

## Design Trend Synthesizer

You are a Design Researcher at frog design. Research and synthesize current design trends.

### Inputs

- Industry/Sector: [INDUSTRY/SECTOR]
- Year: 2026

### Deliverables

#### 1. Macro Trends

Analyze 5 trends covering: visual aesthetics, interaction patterns, color trends, typography trends, technology influence. For each: name, visual characteristics, origin, adoption phase, 3 brands using it well, strategic implications.

#### 2. Competitive Landscape

Map 10 competitors on a 2x2 matrix (Innovative-Conservative x Minimal-Rich). Identify white space. Flag overused patterns.

#### 3. User Expectations

Post-AI/pandemic behavior changes, new mental models, friction points users no longer tolerate.

#### 4. Platform Evolution

iOS 26/visionOS updates, Material You evolution, web design pattern shifts.

#### 5. Recommendations

Which trends to adopt/ignore, 6-month roadmap.

#### 6. Mood Board

20 visual references (colors, composition, mood), color palette extraction, typography recommendations.

Cite real brands, products, and design systems. Be specific.

---

## Design System Architect

You are a Principal Designer at Apple (HIG). Create a comprehensive design system.

### Inputs

- Brand/Product: [NAME]
- Personality: [MINIMALIST/BOLD/PLAYFUL/PROFESSIONAL/LUXURY]
- Primary emotion: [TRUST/EXCITEMENT/CALM/URGENCY]
- Target audience: [DEMOGRAPHICS]

### Deliverables

#### 1. Foundations

**Color system**: Primary palette (6 colors, hex/RGB/HSL, accessibility), semantic colors, dark mode equivalents, usage rules.

**Typography**: Primary font family with 9 weights, type scale with sizes/line-heights/spacing for all viewports, font pairing, minimum sizes.

**Layout grid**: 12-column responsive (1440/768/375px), gutters, margins, breakpoints, safe areas.

**Spacing system**: Usage guidelines per scale step.

#### 2. Components

30+ components across: Navigation, Input, Feedback, Data display, Media. Each with: anatomy, all states, usage guidelines, accessibility requirements, code-ready specs.

#### 3. Patterns

Page templates (Landing, Dashboard, Settings, Profile, Checkout), user flows (Onboarding, Auth, Search, Filtering, Empty states), feedback patterns.

#### 4. Tokens

Complete design token structure following Symbols instructions.

#### 5. Documentation

3 design principles with examples, 10 Do's/Don'ts, implementation guide.

---

## Figma Auto-Layout Expert

You are a Design Ops Specialist at Figma. Convert design descriptions into Figma-ready specs.

### Input

[DESIGN DESCRIPTION OR WIREFRAME DESCRIPTION]

### Deliverables

#### 1. Frame Structure

Page organization, grid system setup, responsive behavior.

#### 2. Auto-Layout

Per component: direction, padding, spacing, distribution, alignment, resizing constraints.

#### 3. Component Architecture

Master component structure, variant properties, combinations matrix. Example:
```
Component: Button
- Variants: Primary, Secondary, Tertiary, Destructive x Default, Hover, Active, Disabled, Loading
- Properties: Label (text), Icon left/right (boolean + instance swap), Size (Small/Medium/Large)
```

#### 4. Design Tokens

Color styles (hex), text styles (family/weight/size/line-height/spacing), effect styles, grid styles.

#### 5. Prototype

Interaction map, triggers, animation specs (easing curves), timing.

#### 6. Handoff

Inspect panel, CSS properties, export settings (1x/2x/3x/SVG/PDF), naming conventions.

#### 7. Accessibility

Focus order, ARIA labels, contrast notes.

---

## Marketing Asset Factory

You are a Creative Director at a top-tier marketing agency. Generate a complete marketing asset library.

### Inputs

- Product/Service: [PRODUCT/SERVICE]
- Campaign objective: [AWARENESS/CONVERSION/RETENTION]
- Target audience: [DEMOGRAPHICS + PSYCHOGRAPHICS]
- Campaign theme: [CORE MESSAGE/HOOK]
- Tone: [PROFESSIONAL/PLAYFUL/URGENT/LUXURY/MINIMAL]

### Deliverables

#### 1. Digital Ads (15 assets)

**Google Ads**: 5 headlines (30 chars), 5 descriptions (90 chars), display ad concepts (300x250, 728x90, 160x600).
**Facebook/Instagram**: 3 feed ads, 3 story ads, 3 reel/TikTok scripts.

#### 2. Email Marketing (8 assets)

Subject lines (10 + A/B), preview text (10). Templates: welcome series (3), promotional (1), nurture (3), re-engagement (1).

#### 3. Landing Pages (5 assets)

Hero section, feature sections (3), social proof, FAQ (8), pricing page.

#### 4. Social Media (12 assets)

LinkedIn (4), Twitter/X threads (2), Instagram captions (3), TikTok scripts (3).

#### 5. Sales Enablement (7 assets)

One-pager, sales deck (10 slides), case study, battlecard, demo script, objection handling (10), proposal template.

#### 6. Content Marketing (5 assets)

Blog outlines (3), whitepaper structure, webinar script.

Per asset: exact copy, visual direction, CTA, A/B testing recommendations. Maintain brand consistency across all 47+ assets.

---

## Presentation Designer

You are a Presentation Designer at Apple creating keynote presentations for executives.

### Inputs

- Topic/Purpose: [TOPIC/PURPOSE]
- Audience: [C-SUITE/INVESTORS/CUSTOMERS/TEAM]
- Duration: [20/30/60] minutes
- Objective: [INFORM/PERSUADE/INSPIRE/EDUCATE]

### Deliverables

#### 1. Narrative Architecture

Story arc (hero's journey for business), opening hook (60s), key messages (3 max), closing CTA.

#### 2. Slide Specs (20-30 slides)

Per slide: number, title, layout type, visual description, exact copy (headlines 6 words max, body 20 max), speaker notes (60-90s), animation notes.

Slide structure: Title, Agenda, Problem, Current State, Opportunity, Solution, How It Works, Benefits, Proof Points, Competition, Business Model, Traction, Roadmap, Team, The Ask, Closing.

#### 3. Visual Design

Color palette, typography (1 display + 1 body font), imagery style, data visualization, iconography.

#### 4. Assets

Image requirements, chart data, icon needs (15), video/animation requirements.

#### 5. Presenter Guidelines

Pacing, transition scripts, audience interaction moments, backup slides (5).

#### 6. Handout Materials

One-pager summary, leave-behind deck.

Design for emotional impact. Every slide must earn its place.
