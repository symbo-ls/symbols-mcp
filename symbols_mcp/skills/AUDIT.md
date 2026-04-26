# Symbols Project Audit — Executable Playbook

A reusable, multi-phase audit workflow for any Symbols project. Goal: every component, every page, every line follows the strict ruleset; the agent generates publish-ready code in one shot. Anything the agent can't generate cleanly becomes a clearly-explained framework bug logged to `audit/framework_audit_results.md` for the framework team to debug.

> **Invoke:**
> - In Claude Code: `/symbols-audit [path]`
> - From the MCP: call `mcp__symbols-mcp__audit_project` (returns this playbook)
> - From a shell (CI / pre-commit): `npx @symbo.ls/mcp symbols-audit ./symbols`
>
> Output lands in `<project>/audit/`.

---

## Strict mode — the contract

**Strict mode is the default. Strict means EXHAUSTIVE — the agent does not stop until every finding is resolved or escalated.**

Specifically, in strict mode every finding ends in exactly one of:

- `resolved` — fix applied; re-running `bin/symbols-audit` confirms the violation is gone.
- `framework_bug` — moved to `audit/framework_audit_results.md` after **three** failed fix attempts that each broke the framework or shared library. Entry MUST include repro steps + a hypothesis traced into smbls/ source (when `--deep-framework-audit` is on, which it is by default).
- `ask_user` — the agent surfaced a `🟢 ASK USER` block to the user and is waiting on input. The agent resumes immediately when the user answers.

**No finding stays `open` at the end of a strict run.** "Recommended follow-up tasks" is NOT an acceptable terminal state in strict mode — every recommended follow-up either becomes a `resolved` entry or a clearly-explained `framework_bug` / `ask_user` escalation.

### Mode flags (set on the CLI; agent reads them from the run log)

| Flag | Default in strict | What it controls |
|---|---|---|
| `--allow-findings` | OFF (strict on) | Disables strict — exit 0 with findings. Skips deep modes. |
| `--no-deep-fix` | OFF (deep-fix on) | Turn off the "don't stop at first blocker" behavior. |
| `--no-deep-framework-audit` | OFF (deep-framework-audit on) | Turn off automatic tracing of framework bugs into smbls/ source. |

**`--deep-fix` (default ON in strict):** the agent does NOT stop at the first publish blocker, missing CLI subcommand, missing test credential, or auth wall. Every blocker becomes either:
- a `🟢 ASK USER` block (if user input could unblock it), OR
- a documented fallback (e.g. "publish blocked → ran local frank + brender → preview lives at dist-brender/").

**`--deep-framework-audit` (default ON in strict):** for every finding that becomes a `framework_bug`, the agent traces the failure into smbls/ / plugins/ / shared library source via Read+Grep, identifies the suspected function, and writes a hypothesis under "Suggested framework patch" in `framework_audit_results.md`. This makes the bug actually fixable by the framework team — a vague "doesn't work" entry is not acceptable.

### ASK-USER protocol

When the agent surfaces a question, it uses the literal token `🟢 ASK USER` so the user (or any orchestrator) can find it instantly:

```
🟢 ASK USER — <one-line summary>

<context — what was attempted, what's blocking>

Options:
  (a) <concrete option, e.g. "provide project key — paste it here">
  (b) <fallback, e.g. "skip publish, run local frank + brender preview">
  (c) <skip / abort>

I'll resume the audit immediately when you reply.
```

Use this for: missing project key, missing creds for auth-protected routes, design decisions inside ambiguous findings, framework-vs-project classification disputes, decisions about destructive actions (e.g. `--force` on a republish).

### Authority order

The audit treats every rule in **RULES.md** as mandatory. **FRAMEWORK.md** + **DESIGN_SYSTEM.md** are the upstream-mirrored authoritative references. Resolve conflicts in this priority order:

1. DOMQL conventions (highest) — flat element API, signal-based reactivity, `(el, s)` reactive functions, flat `onX` events
2. Modern smbls stack discipline — declarative `fetch:`, polyglot for all user-facing strings, helmet metadata, `el.router(...)` for navigation, `changeGlobalTheme()` for theme
3. Architectural direction (project-specific design)
4. Design system integrity (token coverage, theme parity)

> **No hacks, no workarounds.** If a violation can be papered over with raw CSS or a DOM API call, fix the underlying cause instead. There is NO "known debt", "accepted violations", or "deferred fix" in this audit. Zero tolerance.

### Severity classification

Every finding gets exactly one severity:

| Severity | Definition |
|---|---|
| **Critical** | Breaking, unsafe, or structurally invalid. Must fix immediately. (e.g. forbidden `el.props.X` access, `extends: 'Flex'` removed without `flow:` replacement, `window.fetch` in component, hardcoded user-facing strings, `document.title` writes.) |
| **Structural** | Architecture misalignment. Fix before any polish work. (e.g. module-level helpers outside export, imports between project files, `extends: 'Box'` redundancy, frank-invisible folders.) |
| **Systemic** | Pattern-level or repeated misuse across multiple files. (e.g. consistent missing polyglot wrap, consistent raw px values, consistent missing helmet metadata.) |
| **Cosmetic** | Visual or minor consistency issues. Fix last. |

### Origin classification — project vs framework vs ambiguous

Every finding has an `origin` field set initially by `bin/symbols-audit`:

| Origin | Meaning | Where the file lives |
|---|---|---|
| `project` | User's code violates a rule. Fix in user's code. | `<project>/symbols/` |
| `framework` | Issue lives in installed framework code. | `node_modules/` |
| `shared` | Issue lives in a shared library or local cache. | `.symbols_local/`, shared-libraries/ |

The agent may **reclassify** a finding during Phase 2: if the rule is correct but applying the recommended fix breaks the framework after 3 tries, the agent flips `origin: 'framework'` AND `status: 'framework_bug'`, then writes a full entry into `framework_audit_results.md`. With `--deep-framework-audit` on, that entry includes a Read+Grep trace into the suspected smbls/ function.

### Two report files — stop confusing them

- `audit/symbols_audit_results.md` — **PROJECT** findings + resolutions. Every finding the agent fixed, with before/after snippets.
- `audit/framework_audit_results.md` — **FRAMEWORK** bugs + repro + hypothesis. Each entry is targeted at the framework team.

The CLI emits BOTH templates on first run. The agent appends to each as it works.

---

## Transport awareness — stdio vs SSE/HTTPS/CDN

This playbook assumes **stdio MCP transport** (the agent runs on the user's machine, with filesystem access, can run shell commands, can read `symbols.json`). For **SSE / HTTPS / CDN** transports (where the MCP server is remote and the agent has no direct filesystem access on the user's machine):

- `get_project_context`, `bin/symbols-audit`, build/publish/render commands cannot run server-side.
- The agent surfaces those steps as **shell commands for the user to run locally**, then asks the user to paste the output back via `🟢 ASK USER` blocks.
- `audit_component(code)` (string in → violations out) and `audit_project()` (returns this playbook) DO work over SSE — they're stateless and need no filesystem.

If you're an agent running over a non-stdio transport: read the system context to detect this, surface filesystem-dependent steps as instructions for the user to run themselves, then continue Phase 2 / Phase 3c with the pasted output. Don't silently skip — that violates strict mode.

---

## Output artifacts (created on first run)

```
audit/
├── findings.json                # full findings list with origin field; status preserved across runs
├── symbols_audit_results.md     # PROJECT findings + resolutions (agent appends per fix)
├── framework_audit_results.md   # FRAMEWORK bugs + repro + hypothesis (agent appends)
├── before.snapshot.json         # baseline metrics (first run only)
├── after.snapshot.json          # post-audit metrics (final iteration)
├── creds.json                   # (optional, gitignored) test creds for authenticated routes
├── runs/
│   ├── 2026-04-26T17-30-00.log  # per-run log incl. mode flags
│   └── ...
└── report.md                    # human-readable final summary written in Phase 5
```

Re-runnable: each invocation appends a new run log; `findings.json` is updated in place (existing `status: resolved/framework_bug` preserved); both markdown reports accumulate across runs.

The `audit/` directory **must** be in `.gitignore` (or at least `audit/creds.json`).

---

## Phase 0 — Setup & baseline

1. **Resolve project context** — call `mcp__symbols-mcp__get_project_context` (no args = uses cwd). It returns `owner`, `key`, `dir`, `bundler`, `sharedLibraries`, `brender`, `env_type`, `token_present`, plus a `next_step` hint. Treat the result as the source of truth — NEVER hardcode owner/key/credentials, NEVER reuse values from another project.
   - If `found: false` → in strict mode this is an `ask_user` block, not an abort. Surface: _"No `symbols.json` found in or above the cwd. Should I (a) scaffold one with `smbls init`, (b) treat a different path as the project root, or (c) abort?"_ — and resume on the user's answer.
   - If `owner` or `key` is missing → `🟢 ASK USER` for the missing field. NEVER invent. The audit cannot proceed to Phase 3b without a key (publish needs it), so resolve this in Phase 0 to avoid blocking late.
2. Verify project structure with `mcp__symbols-mcp__detect_environment` (or use the `env_type` field from step 1). If env is `unknown` → `ask_user` for the project type. Don't abort.
3. Create `audit/` directory if missing.
4. Capture baseline metrics into `audit/before.snapshot.json`:
   ```json
   {
     "timestamp": "<iso>",
     "owner": "<from get_project_context>",
     "key": "<from get_project_context>",
     "fileCount": <int>,
     "componentCount": <int>,
     "pageCount": <int>,
     "lineCount": <int>,
     "designSystemTokens": { "color": <int>, "typography": <int>, "spacing": <int>, ... }
   }
   ```
5. Initialize `audit/symbols_audit_results.md` with frontmatter (template at end of this doc) if missing.
6. Initialize `audit/findings.json` as `{ "items": [] }` if missing.
7. Add `audit/` to `.gitignore` if not present.
8. **Auth handling — only when needed:** if Phase 3c will hit authenticated routes OR you'll call `save_to_project` / `publish` / `push`:
   - Check `token_present` from step 1 — if true, you're set.
   - If false: ask the user to log in (via `login` tool, `smbls login` CLI, or `SYMBOLS_TOKEN` env var). Never assume creds.
   - For per-site test creds (login forms on the project's own pages): check `audit/creds.json` first, then ask the user. Persist to `audit/creds.json` only — never anywhere else.

If `audit/` already exists (re-run), do NOT clobber `symbols_audit_results.md`. Findings updates merge by id (preserving `status` from prior runs).

---

## Phase 1 — Local static audit (deterministic, fast)

Run `bin/symbols-audit <project>/symbols` (the bundled CLI). It produces `audit/findings.json` with one entry per violation:

```json
{
  "id": "<short-hash>",
  "file": "components/Header.js",
  "line": 23,
  "rule": "Rule 27",
  "severity": "critical | structural | systemic | cosmetic",
  "category": "design-tokens | flat-api | dom-bans | polyglot | fetch | helmet | router | theme | reusability | frank | structure | forbidden-syntax",
  "snippet": "padding: '16px'",
  "suggested_fix": "use design-system spacing token (likely 'A')",
  "status": "open | in_progress | resolved | framework_bug",
  "discovered_at": "<iso>",
  "resolved_at": null,
  "attempts": 0,
  "notes": []
}
```

The CLI runs these check categories (each maps to one or more rules in RULES.md):

### A. Forbidden syntax (regex-based)
- `extend:` (singular) → forbidden
- `childExtend:` (singular) → forbidden
- `props: {` wrapper → forbidden
- `on: {` wrapper → forbidden
- `el.props.X` → forbidden
- `el.on.X` → forbidden
- `({ props })`, `({ state })`, `({ props, state })`, `({ key, state })` destructured signatures → forbidden

### B. Hardcoded values
- `padding|margin|gap|width|height|fontSize|borderRadius|...: ['"]?\d+(?:\.\d+)?(px|rem)\b` → no raw px/rem (Rule 28)
- `color|background|borderColor|...: ['"]#[0-9a-fA-F]{3,8}` → no hex colors (Rule 27)
- `color|background|...: ['"]rgb` / `['"]hsl` → no rgb/hsl

### C. Modern stack bypass
- `window.fetch(` in a component file → forbidden (Rule 47)
- `axios.X(` in a component file → forbidden (Rule 47)
- `document.title =` → forbidden (Rule 49)
- `document.documentElement.setAttribute('data-theme', …)` → forbidden (Rule 50)
- `matchMedia('(prefers-color-scheme: …)')` reads → forbidden (Rule 50)
- `window.location.href =` / `.assign(` / `.replace(` → forbidden (Rule 42)
- `el.call('t' | 'tr' | 'i18n' | '__t' | '_t')` → forbidden (Rule 48 — those functions don't exist; only `polyglot` is registered)
- Hardcoded user-facing strings in `text:` / `placeholder:` / `aria-label:` / `title:` props that don't use `{{ X | polyglot }}` → flag (Rule 48)
- `XMLHttpRequest`, `navigator.sendBeacon`, raw `EventSource`/`WebSocket` constructors at module top → forbidden

### D. DOM manipulation (Rules 30/32/40/42)
- `document.querySelector` / `getElementById` / `querySelectorAll` → forbidden
- `.appendChild(` / `.removeChild(` / `.insertBefore(` → forbidden
- `.innerHTML =` (writing) → forbidden
- `.classList.(add|remove|toggle)(` → forbidden
- `.setAttribute(` (in component code) → forbidden
- `.addEventListener(` (except in functions/ helpers with cleanup) → forbidden
- `el.node.style.X =` (writing) → forbidden
- `parentNode|childNodes|nextSibling|previousSibling` traversal → forbidden

Reading `el.node.X` is fine (focus, blur, scrollTop, selectionStart, etc.). Writing is not.

### E. Structural rules (file-system + AST-light)
- Files in `lib/`, `helpers/`, `utils/`, `services/`, `models/`, `hooks/`, etc. inside `symbols/` → frank-invisible (Rule 58)
- `components/index.js` uses `export * as` → forbidden (must use `export *`) (Rule 3)
- Imports between files outside `index.js`, `context.js`, `app.js`, `dependencies.js`, `sharedLibraries.js` → forbidden (Rule 2)
- `extends: <variable>` (unquoted reference) → forbidden (Rule 10)
- `childExtends: { ... }` inline object → forbidden (Rule 10/61)
- Lowercase top-level child keys (`h1:`, `nav:`, `form:`, etc.) → forbidden (Rule 6 — never render)
- `extends: 'Flex'` / `'Box'` / `'Text'` → flag (Rule 26 — atom auto-extends by key)
- Pages not extending `'Page'` → forbidden (Rule 4)

### F. Reusability heuristics (Rule 61)
- Same `extends: 'X'` value appearing 3+ times across siblings of one parent → suggest `childExtends: 'X'`
- Identical inline-style cluster (>5 props matching) appearing in 2+ files → suggest extraction to `components/<Name>.js`
- `Foo: { extends: 'Foo', ... }` (same name on both sides) → flag as redundant — rename and drop extends (Rule 6/61)
- Inline-object `childExtends` → flag (must extract to named component)
- 3+ siblings with identical theme/font/spacing trio → move to `childProps: { … }` on parent

### G. Frank serialization risks
- `extends: <ImportName>` from a top-of-file import → flag (breaks after frank serialization, Rule 10)
- Module-level `const`/`let`/`var` outside the export → flag (Rule 33)
- `db.createClient` passed in `config.js` / `context.db` → flag (Rule 59 — bundle strips it)

### H. Theme + design system coverage
- Walk `designSystem/index.js`, build the set of registered tokens (color, theme, spacing, typography, timing, ...).
- For every CSS prop value used in components/pages, verify it resolves to a registered token.
- Missing tokens → flag with the file/line of the unresolved use AND the missing token name to add.

### I. Polyglot coverage (Rule 48)
- Build the set of keys in `context.polyglot.translations` or root-level `lang.js`.
- For every `text:` / `placeholder:` / `aria-label:` / `title:` / `alt:` that uses a `{{ X | polyglot }}` template, verify `X` is registered.
- Missing keys → flag.

### J. Helmet coverage (Rule 49)
- Every page (file in `pages/`) must declare `metadata: { ... }` with at least `title`.
- Missing → flag.

After the CLI finishes, **Claude reads `audit/findings.json`** and groups by severity. Critical first.

---

## Phase 2 — Fix loop (Claude executes, with self-test)

For each finding in `findings.json` ordered by severity (critical → structural → systemic → cosmetic):

### Fix protocol

1. Read the file.
2. Apply the suggested fix (or a better fix if Claude judges differently).
3. Re-run `mcp__symbols-mcp__audit_component` on the changed file. New violations? → revert and try a different fix.
4. Re-run `bin/symbols-audit` on the project to verify finding count went down (and no new findings appeared elsewhere).
5. If `smbls start` is running, hit the affected page in chrome-mcp to verify it still renders.
6. Mark the finding `resolved` in `findings.json`.

### When a fix breaks the framework

If after **3 attempts** a fix introduces new failures (`smbls start` errors, page renders blank, console errors that didn't exist before, brender hydration mismatches):

1. Revert.
2. Mark the finding `framework_bug` in `findings.json` AND set `origin: 'framework'`.
3. Append to `audit/framework_audit_results.md` (NOT `symbols_audit_results.md`) using the per-bug template at the top of that file:

   ```markdown
   ### [<rule>] <one-line summary>

   - **Finding ID:** `<id from findings.json>`
   - **Origin file (project):** `path/to/file.js:<line>`
   - **Suspected framework file:** `<deep-trace target — where the agent thinks the bug lives>`
   - **What the rule says should work:** <quote from RULES.md>
   - **What actually happens when you apply the fix:** <error / silent failure / wrong render>
   - **Repro:**
     1. <step>
     2. <step>
   - **Stack / log evidence:** ```<paste>```
   - **Hypothesis (deep audit):** <Read+Grep trace into smbls/ — required when --deep-framework-audit is on>
   - **Suggested framework patch:** <if known>
   ```

4. With `--deep-framework-audit` ON (default in strict): trace the failure into smbls/ source. Use `Grep` to find the responsible function name from the stack/error, `Read` it, follow callers via `Grep` again. Write the hypothesis. A vague "doesn't work" entry is NOT acceptable in strict mode.
5. **Append the resolution side to `audit/symbols_audit_results.md` too** — but as an `escalated_to_framework` entry, not a fix. Keeps the project-side log complete.
6. Continue to the next finding.

### Reusability findings (Rule 61) — handle carefully

Reusability findings are extraction operations, not regex fixes. Protocol:

1. Confirm the duplication is real (3+ uses, not just structural similarity).
2. Decide the extraction shape: shared component vs `childExtends` vs `childProps`.
3. Create `components/<NewName>.js` with the shared shape.
4. Update every consumer to use `extends: 'NewName'` or `childExtends: 'NewName'`.
5. Run `bin/symbols-audit` again — should show fewer findings, not more.
6. If user-visible behavior changes, revert and downgrade the finding to `framework_bug` only if the framework prevents the extraction (e.g. shared-package tree-shaking issue from Rule 57).

---

## Phase 3 — Build, publish, remote test

After all in-scope `findings.json` entries are `resolved` or `framework_bug`:

### 3a. Build-time gates (local)

Run the gates that exist in the project's installed CLI version. Some commands are optional or version-dependent — strict mode handles "command not in this CLI version" via fallback, NEVER silent skip.

```bash
rm -rf .parcel-cache dist
smbls validate-domql --strict        # ← preferred; may not exist in older @symbo.ls/cli
smbls frank to-json                  # ← only if the project's published artifact is JSON
smbls build                          # ← bundler succeeds
smbls brender                        # ← only if symbols.json has "brender": true
```

For each command:
- Exit code 0? → pass.
- Non-zero exit? → log to `audit/runs/<run>.log`, treat as a finding, fix, re-run.
- **Command not found / "unknown subcommand"** → do NOT silently skip. Either:
  - Run the closest equivalent (`smbls validate` if `validate-domql` is unavailable; `smbls --version` to confirm CLI age), OR
  - Surface a `🟢 ASK USER` block: _"`smbls validate-domql` is not in your CLI v<N>. Should I (a) skip this gate, (b) install latest @symbo.ls/cli, or (c) run `smbls validate` instead?"_ — and resume on the user's answer.

For `smbls brender`: after success, inspect output for `Linked: N elements / Unlinked: 0 elements`. Any non-zero `Unlinked` = SSR/client divergence — that's a critical finding.

### 3b. Publish to staging — with fallbacks (DO NOT SILENTLY SKIP)

The happy path:

```bash
smbls publish --non-interactive --yes --env staging -m "audit pass <iso>"
```

Capture the staging URL from output. Use that URL for Phase 3c side-by-side comparison.

**Strict-mode fallback ladder when publish is blocked:**

| Blocker | First fallback | Second fallback |
|---|---|---|
| `symbols.json` has no `key` | `🟢 ASK USER` for the key (or to run `smbls project link` / `smbls project create`); apply, retry | If user can't provide a key → render locally with `smbls frank to-json` + `smbls brender` and use `dist-brender/` for Phase 3c instead of staging URL |
| `AUTH_REQUIRED` | `🟢 ASK USER` to run `smbls login` (or set `SYMBOLS_TOKEN`) | If user declines → local render fallback (same as above) |
| `Project ${owner}/${key} not found on server` | `🟢 ASK USER` to confirm project exists / create it | Local render fallback |
| `--env staging` env doesn't exist | Try `--env dev` or `--env preview`; if all enabled envs reject → `🟢 ASK USER` for the right env name | Local render fallback |
| `ECONNREFUSED` / channel mismatch | Switch channel via `SYMBOLS_API_CHANNEL=next` or `--next`; retry | `🟢 ASK USER` |
| `commander unknown subcommand` | Read `smbls --help-all`, pick equivalent | `🟢 ASK USER` |

**Local-render fallback (the "we still want a preview" path):**

```bash
smbls frank to-json     # bundle FS → JSON (idempotent — won't break anything)
smbls brender           # SSR pre-render every static route → dist-brender/
python3 -m http.server 4750 --directory dist-brender   # serve locally for Phase 3c
```

When Phase 3c uses the local fallback, set `<stagingURL>` to `http://localhost:4750/<route>` for the side-by-side comparison. Document this clearly in the Phase 5 report — it's a successful local audit but the publish leg was deferred.

**The whole point of strict + deep-fix: the audit ALWAYS produces a viewable artifact.** Either staging is published, or `dist-brender/` is locally served. Never both legs blocked.

### 3c. STRICT UI testing protocol — local-vs-remote side-by-side, every clickable, icon rendering, theme/lang/active/forms/responsive

The audit requires Chrome MCP tools. If unavailable, skip 3c with a note and continue to Phase 4.

For EVERY route in `pages/index.js`, execute the entire A→H protocol below. Skip nothing. Failed checks become new findings with category `remote-runtime`. Fix in same loop and re-publish.

#### A. Local-vs-remote side-by-side comparison (MANDATORY after publish)

Open TWO chrome tabs:
- **Tab 1:** `http://localhost:<port>/<route>` (local dev — `smbls start`)
- **Tab 2:** `<stagingURL><route>` (published staging)

For each route, capture from BOTH tabs and compare:
- HTTP status (must be 200)
- Console errors (must be 0; warnings OK if pre-existing locally too)
- Network request list (every fetch must be 200/304; no 4xx/5xx)
- Visible text (no raw `{{ key | polyglot }}` leaked through — means polyglot didn't resolve)
- DOM body has content (`document.body.children.length > 0`)
- Computed CSS for the page root: `getComputedStyle(document.body).backgroundColor`, `color`, `font-family`
- Page screenshot via `mcp__claude-in-chrome__gif_creator` (single frame)

**Local vs remote MUST match on:**
- Layout — no shifted elements, no missing sections
- Colors — no wrong theme, no missing tokens (atomic class with empty body in production = missing token)
- Fonts — no FOUT / wrong font on remote
- Icon rendering — every Icon renders SVG content (no `?` placeholders, no empty `<svg></svg>` shells)
- Spacing — no different padding/margins between local and remote

Any mismatch = critical finding (publish-time-failures). Add to `findings.json`, fix, re-publish.

#### B. Click every clickable element

```js
mcp__claude-in-chrome__javascript_tool(`
  Array.from(document.querySelectorAll('button, a, [role=button], [onclick]'))
    .map(el => ({ tag: el.tagName, text: el.textContent?.trim()?.slice(0, 40), href: el.href, dataset: {...el.dataset} }))
    .filter(el => el.text || el.href)
`)
```

For each, click and verify:
- No console error appeared
- If it should navigate: URL updated correctly + page rendered (no full reload)
- If it should toggle UI: target element changed visibly (capture before/after computed styles)
- If it should fetch: network request fired with expected method + URL
- No layout shift on clickable elements that aren't supposed to navigate

#### C. Icon rendering verification — CRITICAL (Rule 29 / Rule 62)

```js
mcp__claude-in-chrome__javascript_tool(`
  const icons = Array.from(document.querySelectorAll('svg, [data-key*=Icon], [data-icon]'))
  return icons.map(el => ({
    tag: el.tagName,
    dataKey: el.getAttribute('data-key'),
    dataIcon: el.getAttribute('data-icon'),
    hasUseRef: !!el.querySelector('use'),
    hasPath: !!el.querySelector('path, circle, rect, polygon, line'),
    width: el.getBoundingClientRect().width,
    height: el.getBoundingClientRect().height,
    visible: el.getBoundingClientRect().width > 0 && el.getBoundingClientRect().height > 0
  }))
`)
```

Every icon MUST:
- Have either a `<use>` reference (sprite mode) OR concrete SVG primitives (`<path>`, `<circle>`, etc.)
- Have non-zero width + height
- Not be an empty shell (`<svg></svg>` with no content)

Empty/broken icons = `html: '<svg ...>'` was used somewhere (BANNED — Rule 62), OR the icon name doesn't exist in `designSystem/icons` (missing-token finding), OR the sprite isn't loaded (`useIconSprite: false` regression). Trace and fix at the source.

#### D. Theme toggle test

Click the theme toggle and verify:
- `document.documentElement.getAttribute('data-theme')` flips (e.g. `'dark'` ↔ `'light'`)
- No flash (no white frame between dark→light, no FOUC)
- CSS vars update — capture `getComputedStyle(document.body).getPropertyValue('--theme-document-background')` before/after
- Icons that depend on theme (sun/moon swaps) update correctly via `@dark`/`@light` blocks

#### E. Language switcher test (if polyglot configured)

Change language and verify:
- Visible text changes immediately (e.g. headings switch language)
- `state.root.lang` updates
- Subsequent network requests include `Accept-Language` header (`mcp__claude-in-chrome__read_network_requests`)
- localStorage persists (`smbls_lang` or project's `storageLangKey`)

#### F. Active navigation state

Navigate between routes via Link components (NOT direct URL) and verify:
- URL updates without full page reload (no flash, no `<head>` blink)
- The current route's nav item shows active state (background, font weight, underline — whatever the design system uses)
- Other nav items show inactive state
- `aria-current="page"` is set on the active link (a11y)
- Browser back/forward arrows work — `popstate` triggers route change

#### G. Forms / interactive widgets

For every form on the page:
- Submit empty → verify validation errors appear
- Submit with invalid data → verify error states render
- Submit with valid data → verify network request fires + success state appears
- Form fields handle keyboard navigation (Tab order makes sense)
- Inputs have visible focus states

#### H. Responsive viewport test

Resize chrome via `mcp__claude-in-chrome__resize_window`:
- 375px (mobileXS)
- 768px (mobileL)
- 1024px (tabletS)
- 1920px (desktop)

For each viewport, verify:
- Layout adapts (no horizontal scroll, no overlapping elements)
- Active media-query rules apply (`@mobileL`, `@tabletS`, etc.)
- Responsive nav (hamburger appears on mobile, full nav on desktop)
- No content cut off

Record all results in `audit/runs/<run>.log`. Failed checks → new finding entries with category `remote-runtime`. Fix in same loop, re-publish.

### 3d. Fix the remote-only findings

Same fix loop as Phase 2.

### 3e. Re-publish

Once remote findings are resolved, re-publish to confirm the fix took.

---

## Phase 4 — Triple-iterate + deep-fix loop

Run Phase 1 → Phase 2 → Phase 3 again. Then again. Then once more. Three full iterations after the first complete pass.

**Stopping condition:** Two consecutive iterations with:
- Zero new `open` findings
- Zero `ask_user` blocks awaiting input
- Phase 3b produced a viewable artifact (staging URL OR local `dist-brender/` fallback)

If any of those isn't true, run another iteration. Strict mode does NOT exit on iteration 3 if there are still open items — it loops until convergence.

### Deep-fix loop (when `--deep-fix` is on, default)

Between iterations, the agent re-visits:

1. **Every `framework_bug` entry** with `--deep-framework-audit` on — does the entry have a Read+Grep trace into smbls/ source? A repro? A "Suggested framework patch"? If the entry is thin ("doesn't work"), strengthen it. The framework team must be able to fix the bug from the entry alone.
2. **Every `ask_user` block** that timed out — re-surface with refined options.
3. **Every blocker that triggered a fallback in Phase 3b** — try the primary path again now that other findings are fixed (e.g. publish may succeed once auth was provided).
4. **Recommended-follow-up items the agent itself wrote** — in strict mode these are NOT a punt list. The agent picks each one up in this loop and either resolves it, escalates to `ask_user`, or moves it to `framework_bug` with full context.

If the third iteration still surfaces new findings, that's a signal the rules + judgment aren't yet generating publish-ready code on first pass. Append to `audit/framework_audit_results.md` under `## STRICTNESS GAPS` with the specific pattern still emerging — those become the next set of rule strengthenings in `RULES.md`.

---

## Phase 5 — Generate report

Write `audit/report.md`. **In strict mode, the report is a record of resolutions, NOT a TODO list.** Every "follow-up" the agent thought of during the audit was either resolved or escalated in Phase 4. Don't end the report with passive "Recommended follow-up tasks" entries — that's a strict-mode violation.

```markdown
# Symbols Project Audit — <owner>/<key>

**Date:** <iso>
**Mode:** strict=<bool>, deep-fix=<bool>, deep-framework-audit=<bool>
**Runs:** <N> iterations until convergence

## Final state

| Status | Count |
|---|---|
| resolved | <n> |
| framework_bug | <n> |
| ask_user (still pending) | <n>  ← MUST be 0 in a clean strict run |
| open | <n>  ← MUST be 0 in a clean strict run |

## Phase 3b outcome

- Publish attempted: <yes/no>
- Result: <staging URL> OR <local-fallback path: dist-brender/ served at http://localhost:NNNN>
- Blockers resolved: <list with how>

## Before / After

| Metric | Before | After | Δ |
|---|---|---|---|
| Files | … | … | … |
| Components | … | … | … |
| Lines | … | … | … |
| Rule violations | … | 0 | … |

## Findings by category

(group from findings.json — all entries now `resolved` or `framework_bug` or escalated `ask_user`)

## Framework bugs logged

Pointer to `framework_audit_results.md`. Number of bugs: <n>. Top categories: <…>.

## Resolved escalations

For every `🟢 ASK USER` block that fired during the run: what was asked, how the user answered, what the agent did with the answer. Single source of truth for the audit's interactive history.

## Strictness gaps observed

(if any patterns are still emerging on iteration 3 — log to framework_audit_results.md → STRICTNESS GAPS section)

## Time per phase

| Phase | Iterations | Time |
|---|---|---|

## What the user should review

A short, action-oriented list — but ONLY items the user needs to make a decision on (e.g. "framework_audit_results.md has 12 entries; please file them upstream"). NOT a punt list of unfinished audit work.
```

---

## Common publish-time failures (diagnostic table)

When a published deploy goes wrong, match the symptom in this table before debugging. These are the recurring failure modes (verified across many projects) — fixes are usually mechanical once the cause is identified.

| Symptom | Cause | Fix |
|---|---|---|
| Page renders blank in deployed env | Brender failed silently → client render path expected hydration markers | Run `smbls build` locally with `BRENDER=true`; check console for the brender warning |
| Theme flashes wrong color on first paint | Project-side `setAttribute('data-theme', …)` racing `resolveAndApplyTheme`, OR `useDocumentTheme: false` skipping the design-system's document background/color application | Remove any project-side theme `setAttribute` (framework owns it). Keep `useDocumentTheme: true` so the design system's `document` block applies on `<body>` |
| `db.createClient is not a function` at runtime | Project shipped a `createClient` reference in JSON. Mermaid bundle strips it; supabase adapter's dynamic-import fallback needs `@supabase/supabase-js` to be importable | Add `@supabase/supabase-js` to `symbols/dependencies.js` so the runtime importmap can resolve it. Stop passing `createClient` from `config.js` |
| Routes 404 in deployed env | `pages/index.js` default export not in expected `{ '/': X, '/about': Y }` shape | Frank only picks up the default export of `pages/index.js`. Named exports must be re-exported there |
| Font flicker / FOUT | `useFontImport: false` or design system `font` block missing `fontFace` | Set `useFontImport: true` and define `fontFace` for every font family |
| CSS vars missing in iframe | Multi-app secondary not getting its own document on `config.document` | Use the framework's `prepareDesignSystem` flow — pass `context.document` (and `themeRoot`) to the iframe app's `create()` call |
| `[smbls/router] no content matched for path /` warning | Router fired before pages were registered | Verify `context.pages` exists (frank picks it up from `pages/index.js`'s default export). Check `context.router !== false` |
| Parcel dev server crash: `ENOENT … .parcel-cache/<hash>` | Race in Parcel's dev cache write/read after a fresh build | Clear `.parcel-cache` AND `dist`, restart. For framework-level changes, monorepo-wide nuke: `find <your-monorepo-root> -name ".parcel-cache" -type d -exec rm -rf {} +` |
| Text leaking into the page from an inline `childExtends` object | css-in-props edge case with inline-object `childExtends` | Extract the inline `childExtends` to a named component referenced by string |
| `backdropFilter` value bleeds into text content | css-in-props bug on this specific property | Wrap in a `style: { backdropFilter: '...' }` block instead of a top-level prop |
| External package `Cannot find module` at runtime | Listed in `package.json` but not in `symbols/dependencies.js` (or vice-versa) | Both lists are required. `package.json` is for `npm install`; `symbols/dependencies.js` is what the Symbols runtime resolves via importmap |
| Atomic class resolves to empty body in production (`._c-neutral900 { }`) but works locally | Design-system token missing from published bundle | Re-run `frank` to recompile the published JSON, then republish. Diagnose: walk `document.styleSheets`, grep for class name, inspect rule body |
| Branded base color (`color.black: '#10241A'`) bleeds into dark-mode page background | `theme.document` falls back to bare `'black'`/`'white'`/`'neutral'` tokens, which resolve to the brand's tinted versions | Always pair branded core tokens with explicit `theme.document.@dark` / `@light` blocks in `designSystem/theme.js`. Use modifier system (`neutral+45`/`neutral-45`/`neutral=50`) to step away from the tinted base |
| Shared-package component renders as `<div data-key="Foo"></div>` (empty shell) | Parcel tree-shake stripped a runtime-only string-key reference | Add `package.json` with `"sideEffects": true` at the shared-package root; clear `.parcel-cache`; full restart (Rule 57) |

---

## Pre-publish checklist

Before running `smbls publish`:

1. **Run frank** — recompile JSON if the published artifact is a frank-bundled JSON.
2. **Audit components** — `mcp__symbols-mcp__audit_component` on changed components.
3. **Verify design system tokens are present** — every color/spacing/typography token used in components must be defined in `designSystem/`. Missing tokens cause silent visual fallbacks in production.
4. **Check `dependencies.js`** — any package referenced from project code must be in `dependencies.js` so mermaid can resolve it via importmap.
5. **`config.js` flags** — `useReset`, `useVariable`, `useFontImport`, `useIconSprite`, `useSvgSprite`, `useDefaultConfig`, `useDocumentTheme` should all be `true` for normal projects.
6. **No `db.createClient` in published JSON** — let the supabase adapter's dynamic-import fallback handle it; `@supabase/supabase-js` in `dependencies.js`.
7. **No browser-only top-level code in modules** — see SSR rules. Lazy-load packages like leaflet/mapbox via `el.call(...)` inside event handlers.
8. **Test with `channel=production`** — `smbls deploy --channel production` (or mermaid with `BRENDER=true`) catches SSR regressions early.

---

## Authorization & secrets handling

The audit may need to test authenticated routes. Conventions:

1. Project's `audit/` directory **must** include a `.gitignore` excluding `creds.json`.
2. Optional `audit/creds.json` (gitignored) holds:
   ```json
   {
     "email": "test@example.com",
     "password": "...",
     "loginRoute": "/login",
     "loginButtonSelector": "[data-test=login-submit]"
   }
   ```
3. If creds are provided + project has authenticated routes, Phase 3c includes a login step before navigating to authenticated routes.
4. Never log credentials to `audit/runs/`.

---

## symbols_audit_results.md template (framework-bug log)

```markdown
---
project: <name>
audit-runs: 1
created: <iso>
---

# Framework bugs found during audit

This file logs cases where the strict rules from RULES.md / FRAMEWORK.md / DESIGN_SYSTEM.md are correct, but applying them caused failures because of bugs in the framework itself (smbls/, plugins/). Each entry is a specific symptom + recommended-fix-attempted + why it broke + likely framework module.

These should be triaged into actual `smbls/` issues for the framework team.

## STRICTNESS GAPS

(Patterns that emerged in iteration 3+ — signals the rule set isn't strict enough yet. Each entry becomes a candidate rule strengthening in RULES.md.)

---

## [<iso>] Example: `el.fetch` declarative cache key collision

**File:** `components/ArticleList.js:42`
**Rule:** Rule 47 (declarative fetch)
**Symptom:** When two ArticleList instances mount with different `params`, both share the same cache entry — second one overwrites first's data.
**Recommended fix attempted:** Use `cache: { key: 'articles-' + params.id }` per-instance.
**Why the fix breaks it:** `cache.key` option appears to be ignored by the supabase adapter — verified by adding `console.log` inside `plugins/fetch/index.js`.
**Affected framework module:** `smbls/plugins/fetch/adapters/supabase.js`
**Workaround applied:** Use distinct `state:` keys per instance and let auto-derived cache key differ. Marked finding as `framework_bug` in `findings.json`.
```

---

## findings.json schema

```json
{
  "$schema": "symbols-mcp findings v1",
  "items": [
    {
      "id": "f_a1b2c3",
      "file": "components/Header.js",
      "line": 23,
      "rule": "Rule 27",
      "severity": "critical",
      "category": "design-tokens",
      "snippet": "padding: '16px'",
      "suggested_fix": "padding: 'A'",
      "status": "open",
      "discovered_at": "2026-04-26T17:30:00Z",
      "resolved_at": null,
      "attempts": 0,
      "notes": []
    }
  ]
}
```

---

## How to invoke

### Full audit (Claude Code session)

```
/symbols-audit
```

The slash command:
1. Asks for project path (default: cwd's `./symbols`).
2. Calls `mcp__symbols-mcp__audit_project` to load this playbook.
3. Runs Phase 0 → 5 with no further prompts (only ASK-USER stops).

### Static-only audit (CI / pre-commit)

```bash
npx @symbo.ls/mcp symbols-audit ./symbols
# or with --strict for non-zero exit on findings:
npx @symbo.ls/mcp symbols-audit --strict ./symbols
# or --json for machine output:
npx @symbo.ls/mcp symbols-audit --json ./symbols
```

Exits 0 if open findings == 0 (post-filter), non-zero with `--strict`. Useful as a pre-commit hook.

### Re-run a specific phase

```
/symbols-audit phase=3       # only build + publish + remote test
```

Or via the MCP tool directly:
```
mcp__symbols-mcp__audit_project(phase='3')
```

### View existing findings

```bash
cat audit/findings.json | jq '.items[] | select(.status == "open")'
```

---

## Final deliverables

When the audit completes (Phase 4 stopping condition met + Phase 5 report written):

1. **`audit/report.md`** — executive summary + before/after metrics + findings by category + framework bugs + strictness gaps.
2. **`audit/findings.json`** — every finding accounted for as `resolved` or `framework_bug` (zero `open`).
3. **`audit/symbols_audit_results.md`** — every framework limitation logged with full repro steps for the framework team.
4. **`audit/runs/`** — chronological log of each audit run.

**Goal achieved when:** running `bin/symbols-audit --strict` exits 0, `smbls build` + `smbls brender` succeed without warnings, `smbls publish --env production` deploys cleanly, and chrome-mcp golden-path tests pass with zero console errors.
