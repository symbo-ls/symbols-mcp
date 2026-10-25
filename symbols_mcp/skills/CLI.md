# `smbls` CLI — MCP reference

Single source for the Symbols CLI surface. Optimized for agents picking the right command without trial-and-error.

> Audience: Claude (and other MCP agents) working in any Symbols project. Skim-and-act format.
> Also see: `FRAMEWORK.md` (framework rules), `DESIGN_SYSTEM.md` (design system contract), `MODERN_STACK.md` (fetch / polyglot / helmet / router / scratch / brender), `SDK.md` (`@symbo.ls/sdk` reference).

---

## Install

```bash
npm i -g @symbo.ls/cli            # publishes the global `smbls` binary
# or use one-shot:
npx @symbo.ls/cli <command>
bunx @symbo.ls/cli <command>
```

The CLI is a workspace member of the smbls monorepo and ships from `packages/cli/`. Local dev: link it via `npm link` from `smbls/packages/cli`. Source entry: `bin/index.js` (registers all commands, then `program.parseAsync(args)`).

---

## Configuration files

The CLI looks at three files in priority order, walking up from CWD until it hits a git boundary or finds either marker:

| File | Purpose | Tracked |
|---|---|---|
| `symbols.json` | Project identity (key, owner, version, branch, dir, sharedLibraries); also frank options, e.g. `"frank": { "importMetaUrls": "all" }`, and `smbls build` options (`brender`, `build`) | ✅ git-tracked — the canonical project pointer |
| `.symbols_local/config.json` | Tooling + API config (apiBaseUrl OR `channel`, projectKey, projectId, bundler, packageManager, runtime, deploy) | ✅ git-tracked — local overrides + auto-link state |
| `.symbols_local/lock.json` | Snapshot metadata (etag, version, projectId, pulledAt) | ⛔ gitignored — refreshed by every `push`/`pull` |
| `.symbols_local/project.json` | Full project snapshot from server | ⛔ gitignored |
| `.symbols_local/libs/` | Scaffolded shared libraries (read-only) | ⛔ gitignored |
| `.symbols_local/snapshots/` | Pre-write source snapshots for `restore` | ⛔ gitignored |

API URL resolution order (`helpers/config.js` `loadCliConfig`; `push` and `publish` print which one decided):

1. `SYMBOLS_API_BASE_URL` env var — the one per-call pin that always wins
2. `--local` / `SYMBOLS_LOCAL=true` → channel `local`
3. `.symbols_local/config.json` `channel` field → `apiUrl(channel)` from `@symbo.ls/channels`
4. `.symbols_local/config.json` `apiBaseUrl` literal (legacy)
5. Legacy project `.smblsrc` `apiUrl`
6. `useLocal: true` in `symbols.json` → channel `local`
7. This machine's ACTIVE channel — `~/.smblsrc` `currentApiBaseUrl`, shared by every shell and agent on the machine. Set by `smbls channels`, `smbls login --use`, or the first sign-in; never by a token refresh or a plain `smbls login`
8. `@symbo.ls/channels` `defaultChannel` (production) — only when no active channel is recorded

`NODE_ENV` changes only step 8. `SYMBOLS_API_URL` replaces the URL a channel NAME resolves to (steps 2, 3, 6, 8), never a literal URL (steps 1, 4, 5, 7). So neither moves a target that comes from the machine's active channel: pin a call with `SYMBOLS_API_BASE_URL`.

- `SYMBOLS_PROJECT_KEY`, `SYMBOLS_PROJECT_ID`, `SYMBOLS_BRANCH`, `SYMBOLS_OWNER` — per-process project pin

**Project identity is OWNER + KEY** (`helpers/projectIdentity.js`; the CLI release after 3.14.812). A key is unique per owner only — `fly` is dfli/fly, keepz/fly and vault/fly — and the server's bare-key routes answer with the first match of ANY owner, so no command resolves the tree's project by its key alone. In order:

1. `--project <id>` / `SYMBOLS_PROJECT_ID` names the record outright;
2. else `.symbols_local/lock.json`'s `projectId`, only while the lock is stamped with this tree's `key`, `owner` and `apiBase`;
3. else `GET /core/projects/key/<owner>/<key>` — and the record must name that owner and key;
4. else a cached id (an unstamped lock's, `.symbols_local/config.json`'s) only when its record, read by id, shows this owner and key.

A `symbols.json` with a key but no `owner` is refused, never guessed. `push`, `publish`, `sync` and `fetch` refuse a record that names another owner. A bare key typed as an argument (`smbls project delete fly`) resolves only when it is the ONE project with that exact key your token can see.

**In a project tree, identity fails closed (cli 3.14.816).** In a tree whose `symbols.json` has an `owner` and a `key`, every command resolves only that owner's project. An exported `SYMBOLS_PROJECT_ID` or a `--project` that names another project stops the command. Run such a command outside the tree. An owner route that answers with another owner's record is refused.

Credentials live in `~/.smblsrc` (one profile per API base URL), via `CredentialManager` (`helpers/credentialManager.js`); not in `.symbols_local/`. Wipe with `smbls logout`. `smbls whoami` shows the active channel.

---

## Common flag conventions

Every command that hits the API accepts these. Prefer them over editing `.symbols_local/config.json` for ad-hoc runs.

| Flag | Effect |
|---|---|
| `--local` | Target `http://localhost:8080` (channel `local`) |
| `--next` / `--no-next` | Only on `smbls channels`: switch this machine's ACTIVE channel to `next` / `production`. No other command takes them — pin one call with `SYMBOLS_API_BASE_URL` |
| `--api-base-url <url>` | Explicit URL override (login/signup) |
| `--non-interactive` | Disable all prompts; fail rather than asking. Required for CI/MCP/agents |
| `-y`, `--yes` | Auto-confirm "are you sure?" prompts (different from `--non-interactive`; this approves, that disables) |
| `-v`, `--verbose` | Verbose output |

`--non-interactive` paired with required `--<flag>` arguments is the only safe shape for scripted/MCP usage. Without it, any missing flag triggers an `inquirer` prompt that hangs indefinitely if there's no TTY.

---

## Top-level command map

Generated from `bin/index.js` registrations + each command's `.command()` / `.description()`.

### Project lifecycle

```
smbls init [dest]               Initialize or add Symbols to a project
smbls create [dir]              Create + initialize a new project (alias for `project create`)
smbls migrate                   Migrate a v2 Symbols project to v3
smbls eject                     Eject from @symbo.ls/runner to explicit deps
```

Both `smbls init` and `smbls create` automatically run `npx -y @symbo.ls/mcp init-rules` at the end of scaffolding — drops `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/symbols.md`, `.windsurfrules`, `.clinerules`, plus the Claude Code enforcement hooks (`.claude/settings.json` + `.claude/hooks/symbols-mcp-{require,reminder,audit}.sh`). Flags:

```
--no-agent-rules                Skip the entire AI-rules + hooks install
--global-hooks                  Install Claude Code hooks to ~/.claude/ instead of
                                project-level (.claude/). Hooks self-detect Symbols
                                projects via symbols.json walk and no-op elsewhere.
```

Standalone command (drop into an existing project):

```
npx -y @symbo.ls/mcp init-rules               # idempotent; project-level
npx -y @symbo.ls/mcp init-rules --force       # overwrite existing files
npx -y @symbo.ls/mcp init-rules --global      # user-global ~/.claude/ instead
npx -y @symbo.ls/mcp init-rules --no-hooks    # rule files only, no hooks
npx -y @symbo.ls/mcp init-rules --only=cursor,claude   # restrict editors
npx -y @symbo.ls/mcp init-rules --list        # dry-run
```

On a `@symbo.ls/mcp` release without the package's `mcp` bin, npx cannot pick an executable for `npx -y @symbo.ls/mcp <subcommand>`; name the package and the bin instead: `npx -y -p @symbo.ls/mcp symbols-mcp-init-rules`, `npx -y -p @symbo.ls/mcp symbols-audit ./symbols`.

Disable individual hooks at runtime:

```
SYMBOLS_MCP_REQUIRE_RULES=0     # PreToolUse — allow Edit/Write without rules loaded
SYMBOLS_MCP_REMINDER=0          # UserPromptSubmit — drop the per-turn directive
SYMBOLS_MCP_POST_AUDIT=0        # PostToolUse — skip frank-audit on writes
```

### Auth

```
smbls login                     Sign in to Symbols (browser-based by default)
smbls signup                    Create a new Symbols account (opens browser)
smbls logout                    Sign out (clears local credentials)
```

Non-interactive login (CI/MCP/agents):

```
smbls login --non-interactive --token <token>
smbls login --non-interactive --email <email> --password <password>
```

A sign-in saves that API base's profile and leaves the ACTIVE channel as it was — `smbls login --api-base-url https://api.symbols.app` signs in to production without making it the machine's channel, and says which channel stays active. `--use` switches too; the first sign-in on a machine sets it. Login never pins the current directory's project (`.symbols_local/config.json`).

Long-lived tokens (CI / service accounts, e.g. a release pipeline that needs a durable credential instead of a short-lived session token):

```
smbls login --magic-link --long-lived
```

`--long-lived` opts into a durable static token (server-config `pluginAuth.cliTokenExpiresIn`, e.g. 365 days) instead of the normal short-lived CLI access token. It's gated server-side on a valid CLI session key — the prompt asks for one and persists it per API base URL so you don't have to re-enter it on every login to the same server. Only asked when requested; a routine interactive login is unaffected.

### Sync data with platform

```
smbls push                      Push local changes to platform
smbls pull / fetch              Fetch project snapshot from platform
smbls sync                      Two-way sync (merge / remote-wins / local-wins)
smbls collab                    Live websocket collab; mirrors local edits to remote and vice-versa
smbls publish                   Push + version + republish enabled environments (one shot; a pinned env is skipped)
```

`smbls fetch` writes `sharedLibraries.js` whole, with one writer (cli 3.14.819 / frank 3.14.806): frank writes the project files first, then the CLI writes the import module atomically (temp file + rename), and `fetch` waits for the write. A repeat fetch into an existing `--dist-dir` is safe (older CLIs could leave the module followed by NUL bytes or old library data). frank `toFS(data, dir, { externalKeys })` keeps a key wired into the index and context but does not write its file.

`push` writes the new content into the project's main branch. `publish` is push → mark new version as published → republish each environment so it picks up the version. See "Publish flow" below.

`push`'s differ is idempotent: an unchanged project reports "No changes to push" on every consecutive run — it does not re-report the same delete/update set forever or mint a junk version each time. (The differ specifically accounts for server-side read-path conveniences — e.g. missing design-system namespaces getting default-filled on read, or environment-export flags always being present on the fetched side — so those never show up as phantom deletes; and key-order drift inside a property bag like `attr`/`style`/`state` no longer counts as a real change unless it's a genuine reorder of child elements, where order IS meaningful DOM order.) If you ever see the same change set reported twice in a row with truly nothing edited locally, that's a regression worth filing, not expected behavior.

Every command that SENDS the local project — `push`, `sync`, `collab` and `github sync` — ships frank's stringified emission, never a raw `fn.toString()` of the live build. A handler's `await import('<pkg>')` arrives as that literal `import('<pkg>')` (the raw build carried esbuild's `init_X(), X_exports` wiring, which throws at runtime). frank's emission gate stands in front of every send: a globalScope defect blocks (`push`, `sync` and `github sync` exit 1; `collab` prints `[collab] Local change NOT sent` and keeps watching), and per-function debt is printed as a named warning. `SMBLS_NO_VERIFY_SERIALIZATION=1` bypasses the gate for all four; `push` also takes `--no-verify-serialization`.

**Self-hosted assets — `new URL('<relative path>', import.meta.url)`.** A value that names a project file this way (a font `url` in `designSystem`, an image in a component's `scope`) is published as a platform URL: `push` uploads the file to the project (public, keyed by its path from the project root, e.g. `assets/fonts/x.woff2`) or reuses the asset the platform already holds with the same sha256, so an unchanged file keeps its URL and uploads nothing; the assets join the project's `assets` map. By default only calls that run while the project loads are resolved; `"frank": { "importMetaUrls": "all" }` in `symbols.json` also resolves calls inside function bodies and in `app.js`. `smbls frank to-json` inlines such files as `data:` URLs and never uploads; `sync`, `collab` and `github sync` do not upload them and fail with an error naming the file and line. `smbls start` / `smbls build` (parcel) keep their own hashed assets; a later `smbls fetch` writes the published URL as a plain string.

**A package `dependencies.js` declares need not be installed for push.** frank stubs a declared runtime package that `node_modules` lacks and publishes its `import('<pkg>')` for the browser to load through the importmap (e.g. `await import('quill')` in a handler). A package nothing declares still fails to resolve (`package.json` dependencies never reach the platform's importmap), and a value computed from such a stub while the project loads fails the build (`FRANK_UNINSTALLED_DEPENDENCY_VALUE`).

**Next release (after cli 3.14.820 / smbls 3.14.853; not in those versions):** the owner backstop below. `smbls collab` already refuses to start without a verified project id (run `smbls push` or `smbls sync` first to stamp `lock.json`). Its websocket handshake then names the project by `projectId` **and** `owner` (from `symbols.json`'s `owner` field) as a backstop — never a bare key, which is not unique across owners. If the server still answers `error { code: 'ambiguous_key', candidates }` (a key shared by more than one owner), the CLI prints the candidates once, as `owner/key`, and disconnects — it does not retry the same ambiguous join. Fix: add `"owner"` to `symbols.json`.

### Project management (server-side)

```
smbls project list              List your projects
smbls project create [dir]      Create a new project (or link existing)
smbls project link [dir]        Link a local folder to existing platform project
smbls project relink [dir]      Safely re-link (preserves local + creates conflict branch on divergence)
smbls project update <key>      Update project metadata, content, or key
smbls project duplicate <src>   Duplicate a project on the platform
smbls project delete <key>      Delete a platform project
smbls project restore           Restore a project to a previous version state

smbls project versions list                   List versions
smbls project versions latest                 Get latest version
smbls project versions get <id>               Fetch a version by id
smbls project versions create                 Create a new version
smbls project versions update <id>            Update version metadata
smbls project versions publish <id>           Mark a version as the project's published one
smbls project versions snapshot <id>          Create a snapshot for a version

smbls project environments list               List env slots
smbls project environments upsert <env>       Create/update an environment slot
smbls project environments update <env>       Patch an env slot
smbls project environments delete <env>       Delete an env slot
smbls project environments publish <env>      Publish project to a specific environment

smbls project pipeline promote <from> <to>    Promote content between environments

smbls project libs list                       List linked shared libs (cloud project record)
smbls project libs available                  List available shared libs on platform
smbls project libs add <lib...>               Add lib(s) by owner/key or id — cloud project record only
smbls project libs remove <lib...>            Remove lib(s) by owner/key or id — cloud project record only
                                              (a bare key resolves only when one owner uses it; else lists owners, exits)
```

### Shared libraries (local + cloud, two-file sync)

The top-level `smbls libs` group edits BOTH `symbols.json.sharedLibraries` AND `sharedLibraries.js` in lockstep, and best-effort syncs the cloud project record when authed. Prefer this over `smbls project libs ...` for new flows — it's a strict superset.

```
smbls libs status                             Show declared libs, JS imports, and drift
smbls libs link <path>                        Link a sibling project as a shared library
smbls libs unlink <key>                       Remove a linked entry
smbls libs add <key>[@version]                Add cloud lib + run fetch + cloud-sync (if authed)
smbls libs remove <key>                       Remove a lib (cloud or linked)
smbls libs list                               List declared libs with their mode (linked/cloud)

smbls project members list                    List project members
smbls project members add <email>             Add existing user by email
smbls project members invite <email>          Invite (sends invite email)
smbls project members invite-link             Create magic invite link
smbls project members accept-invite <token>   Accept an invite (must be logged in)
smbls project members role <id> <role>        Set role: guest|editor|admin|owner
smbls project members remove <id>             Remove a member
```

### Workspace (org-level)

```
smbls workspace list                          List workspaces you can access
smbls workspace create                        Create new workspace under an org
smbls workspace get <id>                      Get workspace details
smbls workspace members <id>                  List workspace members
smbls workspace billing <id>                  Show billing/subscription
smbls workspace credits <id>                  Show credit balance

# Local batch ops over every project member of the workspace:
smbls workspace init                          Scaffold/adopt a local workspace dir
smbls workspace link [dir]                    Link current dir to a server workspace
smbls workspace pull                          Scaffold/link/fetch every server-side project
smbls workspace push                          Push every project in the workspace
smbls workspace fetch                         Fetch every project
smbls workspace sync                          Sync every project
smbls workspace publish                       Publish every project
smbls workspace collab                        Start `smbls collab` per project
smbls workspace relink                        Safely relink every member project
smbls workspace status                        Local-only status of every project (no server calls)
smbls workspace list-projects                 List member projects in the local workspace
smbls workspace create-missing                Create server-side projects for local members that 404
```

### Files & assets

```
smbls files list                              List project-linked files
smbls files upload                            Upload + add to project files map
smbls files download                          Download a project file (interactive picker)
smbls files rm                                Remove from project files map (record stays)

smbls assets list                             List project-linked assets
smbls assets show <key>                       Show asset metadata
smbls assets upload                           Upload + add to assets map
smbls assets download                         Download asset (interactive picker)
smbls assets rm                               Remove from assets map
smbls assets prune                            Soft-delete server assets missing locally
smbls assets sync                             Scan local <distDir>/assets/ + upload new/changed
```

`smbls files upload` keeps the case of each file key in `files/index.js` (cli 3.14.815): the import path is the name on disk, so case-sensitive hosts resolve it. It refuses a key that differs from an existing key only by case, before the upload.

### Integrations & marketplace

```
smbls integrations list                       List integrations in scope
smbls integrations install <kind>             Install/update integration at scope
smbls integrations test <kind> [slug]         Invoke a capability on an installed integration
smbls integrations remove <kind> [slug]       Delete installed integration
smbls integrations purchase <kind>            Purchase a paid marketplace integration (Stripe)
```

### GitHub integration

```
smbls github connect                          Create Integration + API key + GitHub connector
smbls github sync                             Build full project state + upload via connector
smbls github init-actions                     Generate GitHub Actions workflow for `smbls github sync`
```

### Frank — JSON ↔ FS bundling

```
smbls frank to-json [dir]                     Bundle FS project → single JSON object
smbls frank to-fs <jsonPath> [outDir]         Materialize JSON → symbols/ directory
```

Flags: `to-json` accepts `-o, --output <path>`, `--no-stringify`, `-v, --verbose`. `to-fs` accepts `--overwrite`. `to-json` inlines `new URL('<path>', import.meta.url)` project files as `data:` URLs (no upload).

**Function text is the author's** (frank 3.14.804). `to-json` and `smbls push` serialize each function as the text in its source file (comments, quotes, spacing, names), not esbuild's re-print. A fetched tree pushes back byte for byte: `smbls fetch` → `smbls push` no longer renames bindings (`getLightboxSrc2` → `getLightboxSrc23`) or drops comments. The first push after the upgrade changes the text of most functions once (same programs, author's formatting). When esbuild changed the function beyond formatting (an import read through the bundle, `define`, a folded constant, lowered syntax) the bundle text stays. `toJSON(dir, { authoredSource: false })` or `SMBLS_FRANK_BUNDLE_FUNCTION_TEXT=1` gives the old text; `FRANK_DEBUG_AUTHORED_SOURCE=1` names each function that keeps the bundle text, and why.

### Dev / build / deploy

```
smbls start [entry]                           Start dev server (parcel default)
smbls build [entry]                           Build for production
smbls brender                                 Pre-render every static route to dist-brender/
smbls deploy                                  Deploy to a hosting provider
smbls redirects [--out-dir <dir>]             Rewrite the build's _redirects block from the output as it is now
smbls tunnel [port]                           Expose local port via tunnel.symbo.ls
```

`start` flags:

- `-p, --port <port>` (defaults to `symbols.json.port` or 1234)
- `--no-cache`, `--open`, `--bundler <parcel|vite|browser>`
- `--collab` (start with realtime collab) / `--no-collab` (skip prompt, run local)
- `--fresh` (wipe the caches first; `lock.json` and `config.json` stay)
- Any other flag goes to the bundler (`parcel serve` / `vite serve`) with the value after it; `start`'s own flags never do.

`build` flags: `--no-cache`, `--no-optimize`, `--no-brender`, `--strict`, `--out-dir <dir>`, `--bundler`. `build` copies `public/` (or `symbols.json` `publicDir`) into the output root and never replaces a file the bundler wrote. With brender on, `build` pre-renders each route into the bundler's `index.html`: `/x` → `x.html`, `/*` → `404.html` (rendered at the address `/404`), and exits 1 when no route renders (`--no-brender` opts out). Two routes that would write one file (`/404` and `/*`) are written once and the other is reported.

- **`200.html`** is the bundler's own document, kept before `/` overwrites `index.html`. Serve `200.html` for client-side routes — never `index.html`, which is now the home page with the home page's canonical and og tags (see Routes without their own page, below).
- **`_redirects`** in the output: each route without its own page → `/200`, status 200 (read by Cloudflare Workers static assets, Cloudflare Pages and Netlify). The project's own rules from `public/_redirects` stay first; a rebuild replaces only the build's block; `brender.redirects: false` writes none.
- **`smbls-ds.<sha>.json`**: the design system the pre-render prepared, written once next to the bundles, with a `<link rel="preload" as="fetch" data-smbls="design-system">` in every pre-rendered page. Client-rendered pages (`200.html`, the `index.html` of a build without a pre-render) get only `<meta name="smbls-design-system" content="…">`: the boot requests it at low priority after the app script and never waits for it (`build.prepareDesignSystem: false` leaves that reference out; `false` means `{ shell: false }`). `build.prepareDesignSystem: { pages: false }` (opt-in, cli 3.14.814) also leaves the preload out of the pre-rendered pages: their client then prepares the design system itself (210 KB raw / 35 KB brotli less per first visit on a measured app). Both together: `{ "shell": false, "pages": false }`. The app adopts it instead of processing its design system (FRAMEWORK.md §8 → The design system prepared at build time). A design system that holds a function gets no file. With `build.treeShakeIcons` on, the file leaves out the default icons the build dropped (cli 3.14.820), so a dropped icon logs the same loud error on a built page as in the app shell; icons the project's own design system registers stay.
- **Build-time data.** Every page carries the data answers of the build time until the next build, and one stamp per build: `<meta name="brender-stamp" content="<stamp>" data-time="<ms>">`. The stamp is `symbols.json` `brender.stamp` (a string or a number), else `config.js` `brender.stamp` — a value, or a function `({ time, data }) => stamp` run once per build (it may be async: the data's own version) — else the build time. A stamp function that throws fails the build. How a page learns its data is stale: SYNTAX.md → Data Fetching → A pre-built page's data.
- **Assets.** A `file:` URL in a page (`new URL('…', import.meta.url)`, evaluated on the build machine) is mapped to the file the bundler emitted from the same source, or copied into the output under a content hash. A `file:` URL that names no project file fails the build.
- **`--strict`** (or `symbols.json` `brender.strict`) fails the build when a page was made with failed data or label requests, or shows raw label keys. Without it those pages are listed as warnings.
- **`symbols.json` `brender` as an object** (still on): `context` — the module the build's entry boots with (e.g. `symbols/siteContext.js`), so its pages are the ones pre-rendered; `exclude` — page keys to leave out (`"/admin*"` matches every key that starts with `/admin`); `paths` — addresses for routes with parameters (`{ "/:lang/about": ["/en/about"] }` → `en/about.html`); `strict`; `eagerImages` (default 2: later images get `loading="lazy"` unless they set `loading`); `timeout` — each page's render time limit in ms (default 30000; `0`: none): pages render one at a time, and a page past its limit fails with `BRENDER_RENDER_TIMEOUT` while the next page renders; `stamp` — the build's data stamp (above); `redirects: false` — no `_redirects` block. A page with `prerender: false` is never pre-rendered.
- **Built `<html data-theme>`** (brender 3.14.670). When `globalTheme` is a fixed theme (`light`, `dark` or a named scheme), every built page carries `<html data-theme="<theme>">`, so first paint uses the project theme and not the OS scheme. `auto`, `system` or unset write nothing: the `prefers-color-scheme` fallback rules apply until boot, as before. A config with its own `themeRoot` writes nothing. Both schemes' CSS stay in the page for a later `changeGlobalTheme()`.
- **Page weight** (brender 3.14.671 / cli 3.14.814). `smbls build` trims what a built page carries before boot (the client adds the rest when it boots). On by default, each with an off switch in `symbols.json` `brender`:
  - the inline icon sprite holds only the icons the page uses — `"spriteIcons": "all"` keeps every icon;
  - the atomic CSS holds only the rules of classes in the page's markup — `"cssClasses": "all"` keeps every rule;
  - the element-path registry ships as a tree when the client smbls can read it — `"registryFormat": "paths"` keeps the flat paths format.

  **Release note — the registry tag changed** (brender 3.14.672). The tree ships as `<script type="application/json" data-brender="registry-tree">` (content `{ "f": "tree", "e": [...] }`), not the old `data-brender="registry"` tag. A post-build step that looks for the old tag does not find it. To find the end of the page markup, match every first data block after it: `/<script type="application\/json" data-(?:brender="registry(?:-tree)?"|fetch-seed\b)/` (a `brender.hydrate: false` page has no registry block; a page with no anonymous request has no fetch-seed block). Or read the elements that carry `data-br`. `"brender": { "registryFormat": "paths" }` keeps the old tag.

  Opt-in: `"cssVariables": "page"` keeps only the CSS variables the page's own CSS and markup read. Not safe when a stylesheet the page links (`public/` CSS, a CDN file) reads design-system variables before boot: the trim does not see that stylesheet. Default `"all"`.

  ```json
  { "brender": { "cssVariables": "page" }, "build": { "prepareDesignSystem": { "pages": false } } }
  ```
- **Font faces in their own sheet** (brender 3.14.672 / smbls 3.14.850). A built page carries its `@font-face` rules in `<style data-smbls-faces>`, before `<style data-brender>`, not in `<style data-emotion="smbls">`. The takeover does not remove that sheet, so the faces stay loaded and the text never falls back to the system font. A post-build step that moved `@font-face` rules out of the server styles finds none there now: leave `<style data-smbls-faces>` where it is.
- **`symbols.json` `build`**: `"compileHints"` (on unless `false`) puts `//# allFunctionsCalledOnLoad` as the first line of each local module script the page loads at start (the app script, a project's own early script) and shifts its source map by one line: Chrome 136+ then compiles the bundle's functions while the script streams in, not on the main thread at first call. Measured on a built empty app (headless Chrome, medians of 9): first task 51.7 → 26.6 ms at 1x CPU, 270 → 135 ms at 4x. Lazily loaded files stay as the bundler wrote them; with `false` the output is byte-identical to the bundler's. `"modulePreload": true` (off by default) adds a `<link rel="modulepreload">` after the page's import map for every `smbls/core` lazy module `config.js` switches on (fetch when `fetch` is set; the windows, dropdown and tooltip kits unless `false`; `shorthand`, `analyze`, `inspect` when set). It is opt-in because no measurement shows a gain yet: the kits started at about 10 ms instead of about 90 ms, but the A/B ran on a machine under heavy load, never on a throttled phone profile. With it off the built page is byte-identical.

**Production build, dev diagnostics.** A parcel `smbls build` (production mode) strips the framework's dev-only warnings (author mistakes, e.g. an unknown design-system token) from the app bundle; since cli 3.14.813 that covers 62 more warnings, all behind `globalThis.__SMBLS_DEV_DIAGNOSTICS_OFF__`. `smbls start` keeps every warning. Parcel only: a Vite build keeps them all. Errors that report a runtime failure stay in every build (FRAMEWORK.md §10 → `smbls build`).

#### `symbols.json` `build` — size options of a production build (opt-in)

Options of a production parcel `smbls build` (cli 3.14.813 / 3.14.814, smbls 3.14.847 / 3.14.848; `treeShakeFeatures.drop` and the exact feature triggers: cli 3.14.817, smbls 3.14.849; `drop` refused for a needed feature: cli 3.14.818). Each is off unless set. With none set, the bundle is the same as before they existed.

| Option | Value | What it does |
|---|---|---|
| `treeShakeComponents` | `true` \| `{ "keep": [...] }` | Keeps only the default components (`@symbo.ls/default-config`) the app names, what they name in turn, and `keep` |
| `treeShakeIcons` | `true` \| `{ "keep": [...] }` | The same for the default icon set |
| `treeShakeLibraries` | `true` | For a project with no shared library (no `sharedLibraries.js` entry, no `symbols.json` `sharedLibraries`): no shared-library machinery in the bundle |
| `lazyServerUtils` | `true` | The server-only utils `generateMetaTags`, `getPageMetadata`, `getImportMapScript`, `polyglotStartupScript`, `objectToString`, `deepStringifyFunctions` load on demand from their own file. Called in the browser (`el.call(...)`), each returns a **Promise** of its value — `await` it |
| `treeShakeFeatures` | `true` \| `{ "keep": [...], "drop": [...] }` | Drops the optional framework features the project never names (names below). `drop` forces a feature out |

`treeShakeFeatures` feature names (use these in `keep` and `drop`): `autoGrow`, `inertOutside`, `bridge` (`onBridgeMount` hooks), `viewEvents` (`onInView` / `onLeaveView`), `lazyRoutes` (lazy route groups, `loadLazy`), `viewTransition` (`designSystem.viewTransition`), `liveSync` (live sync / notifications), `prerender` (the boot over a pre-rendered page; always kept when the build pre-renders, i.e. `brender` is not `false`), `safeInk` (`getSafeInk` / `getSafeInkInfo`).

**What keeps a feature.** The framework itself uses it, a default component the build keeps uses it, `keep` lists it, or the app source names one of its triggers. Each trigger is the setting that switches the feature on, not a bare word:

- `liveSync` — `socketUrl` as a key or member (`editor.socketUrl`, `settings.socketUrl`), `notifications: true`, `verbose: true`, or the runner (`'runner'`). A member named `editor` (a text-editor instance at `scope.editor`) does not keep it. `livesync` / `liveSync` alone does not keep it. `notifications` / `verbose` with another value, or a read (`state.notifications`), does not keep it.
- `lazyRoutes` — `lazy` as an object key or an assigned member with a non-literal value (`lazy: { … }`, `ctx.lazy = groups`), or `loadLazy`. `React.lazy(`, `z.lazy(`, `lazy: true`, `lazy: 'admin'`, `loading: 'lazy'` and a read of `ctx.lazy` do not keep it.
- The other features keep their trigger names: `autoGrow`, `inertOutside`, `onBridgeMount`, `onInView` / `onLeaveView`, `viewTransition`, `getSafeInk` / `getSafeInkInfo`; `prerender` by the build option `brender`.

**`drop` — force a feature out.** When the app spells a trigger for something else (the scan cannot tell), list the feature in `drop`. The build refuses the drop, with a warning that names the reason, and keeps the feature when:

- the framework itself uses the feature, or `keep` also lists it;
- a build option or the project config needs it (cli 3.14.818): `prerender` while the build pre-renders (`brender` on); `lazyRoutes` when `context.lazy` is an object; `viewTransition` when `designSystem.viewTransition` is set; `liveSync` when a `socketUrl`, the runner, `notifications: true` or `verbose: true` is set. A context the build cannot read refuses the drop too.

A scan hit alone (the app only spells a trigger) still gives way to `drop`. Otherwise `drop` wins over the scan and a kept default component. An unknown name in `keep` or `drop` gets a warning. A dropped feature that the app asks for at runtime logs its one `console.error`, as below.

**Loud errors, never silent.** A left-out name that the app still asks for at runtime (a key that came from a database or a fetched payload) logs one `console.error` that names the key and the option, in production too; a dropped component renders as an empty element. Example: `[smbls] "autoGrow" is not in this build: symbols.json build.treeShakeFeatures left it out … Add "autoGrow" to build.treeShakeFeatures.keep.` A shared library that reaches the runtime in a `treeShakeLibraries` build is not merged and is reported the same way. Put every data-driven key (a component, icon or feature named only in DB records) in `keep`.

**What the scan reads.** All tree-shake options share one name scan (cli 3.14.814). It reads only what the app bundle can reach: the source files of the symbols dir (`symbols.json` `dir`) without tests (`__tests__/`, `*.test.*`, `*.spec.*`), the entry document (`symbols.json` `entry`, and its script/link references), `symbols.json`, and every module, shared library and package those import, transitively. It never reads `scripts/`, `tests/`, tool configs (`eslint.config.js`, …), worker files or other files outside the app source, so those cannot keep a component alive or change the build output. The scan over-includes on purpose: a name in a comment or string keeps its component. A shared library fetched at runtime with no import (`sharedLibrary('owner/key')`) turns tree shaking off for that build, with a warning.

```json
{
  "build": {
    "treeShakeComponents": { "keep": ["Dialog"] },
    "treeShakeIcons": true,
    "treeShakeLibraries": true,
    "lazyServerUtils": true,
    "treeShakeFeatures": { "keep": ["viewEvents"], "drop": ["liveSync"] }
  }
}
```

Verify a tree-shaken build in a browser: open each page and read the console for `[smbls]` errors that name a `build.*` option.

**Lazy groups under parcel.** `smbls start` and a parcel `smbls build` run parcel with smbls's own JS runtime: after a failed lazy-group load, the next `import()` of that chunk requests it again as `<chunk>.js?smbls-retry=<n>`, only when the app asks (SYNTAX.md → Router → Lazy routes). A project `.parcelrc` that sets its own `runtimes` keeps them and loses this.

**`smbls redirects` — a step that adds files after `smbls build`.** Cloudflare (Workers static assets and Pages) follows a `_redirects` rule even where a file matches, so the build gives each file a route pattern also matches (`/:lang` matches `/favicon.ico`) a rule to itself, first — but only for the files in the output when the rules are written. A postbuild step that adds files (precompressed `*.js.br`, a manifest, icons) leaves them to the pattern, and the app document answers them. End such a step with `smbls redirects [--out-dir <dir>]`: it writes the build's block again from the output's files as they are now (the project's own rules stay above it; routes go to `/200` when the output has a `200.html`, else to `/`). With `symbols.json` `brender.redirects: false` it writes nothing, prints one line and exits 0 (cli 3.14.812).

```json
{ "scripts": { "build": "smbls build", "postbuild": "node scripts/compress.js && smbls redirects" } }
```

#### Routes without their own page

Serve `200.html`, never another page, for a route without its own page: a `:param` route `brender.paths` does not list, a page with `prerender: false`, an excluded or failed one. A host fallback that serves `index.html` shows the HOME page first; the client then throws its nodes away and draws the right page. A host's 404 handling serves the pre-rendered not-found page, status 404, under the right page's client. A pre-rendered address that a route pattern also matches gets a `_redirects` rule to itself first, because Cloudflare follows a rule even where a file matches.

| Host | The rule | Written by |
|---|---|---|
| Cloudflare Workers (static assets) | `_redirects`: each route without its own page → `/200`, status 200 (`/200`, not `/200.html`: Cloudflare answers that with a 307); `assets.not_found_handling`: `"404-page"` with a 404 page, else `"none"` — never `"single-page-application"` on a pre-rendered build | `smbls build` (`_redirects`), `smbls deploy --target workers` (`wrangler.jsonc`) |
| Cloudflare Pages | the same `_redirects`; every other address gets `404.html`. Without one Pages falls back to `index.html`: give the project a `/*` page | `smbls build` |
| Netlify | the same `_redirects` (a file always wins over a rewrite) | `smbls build` |
| Vercel | `vercel.json`: `"cleanUrls": true`, `"rewrites": [{ "source": "/(.*)", "destination": "/200" }]` — the filesystem goes first, so every pre-rendered page keeps its file; an unknown address gets the app's not-found page with status 200 | `smbls deploy --provider vercel` (when `vercel.json` is missing) |
| GitHub Pages | no rewrites: an address with no file gets `404.html` (status 404). The workflow copies `200.html` to `404.html` when the project has no not-found page; better, list the `:param` addresses in `brender.paths` | `smbls deploy --provider github-pages` |
| Surge | serves `200.html` for every unknown address by itself | — |
| Your own server or Worker | the file, then `<path>.html`, then `200.html` — nginx `try_files $uri $uri.html /200.html;`, a Worker `env.ASSETS.fetch(new URL('/200', request.url))` | — |

`"smblsEntry": "core"` in `symbols.json` (parcel `start` / `build`): every bare `smbls` import resolves to `smbls/core` — the framework without the platform registry, its kits and platform plugins in files loaded only when switched on. Only for an app that runs no published or fetched project code: frank-serialized functions read the registry. Default `"full"`.

`brender` flags: `--out-dir <dir>` (defaults to `brenderDistDir` from symbols.json or `dist-brender`), `--no-isr`, `--no-hydrate`, `--no-prefetch` (no table/RPC labels fetched first, no wait for each page's requests; the page's own `fetch` still runs during the render), `--strict` (as in `build`; also `brender.strict`), `-w, --watch`. Route `/x` → `x/index.html`, `/*` → `404.html`. `smbls brender` runs the route loop `smbls build` runs: `brender.context`, `exclude`, `paths`, `strict`, `eagerImages`, `timeout` and `stamp` apply, `file:` URLs are mapped into the output (one that names no project file fails its route), and pages made without some of their data or labels are reported. `:param` routes (`/blog/:id`) and nested `*` routes have no single URL: they are skipped and listed, unless `brender.paths` lists addresses for them. Exits 1 when no route renders. Its pages carry no element registry: with the ISR client bundle the app boots over the server markup and replaces it; `build` pages are the ones made for adoption (FRAMEWORK.md §8).

`deploy --provider <X>` accepts `symbols`, `cloudflare`, `vercel`, `netlify`, `github-pages`. Auto-creates the provider's config (`wrangler.jsonc`, `vercel.json`, `netlify.toml`, etc.) if missing. `--init` initializes config without deploying.

`smbls deploy --provider cloudflare [--target pages|workers] [--dry-run] [--no-brender]` runs the full `smbls build` pipeline (bundle, `public/`, `fetch.early`, brender) and deploys the output. `--target pages` (default) uses Cloudflare Pages; `--target workers` writes Workers Static Assets config, with `not_found_handling: '404-page'` when the output has `404.html`, else `'none'` on a pre-rendered build (the build's `_redirects` sends routes to `200.html`), and `'single-page-application'` only on a build without a pre-render, where `index.html` is the app's document. An existing wrangler config that falls back to `index.html` on a pre-rendered build gets a warning; the CLI never rewrites it. `--dry-run` builds and validates, and deploys nothing.

### Code transformation & validation

```
smbls convert                                 Convert all DOMQL components under a directory
smbls validate                                Validate generated Symbols/DOMQL code
smbls validate-domql                          Validate generated DOMQL with extend-resolution
smbls cleanup                                 Find + remove stale files not in project snapshot
smbls clean                                   Clean Symbols temp files
smbls restore                                 Restore local source from a pre-write snapshot
```

`convert` flags: `--react`, `--angular`, `--vue2`, `--vue3`; `-t, --tmp-dir <path>`, `-o, --only <components>`, `-m, --merge <dir>`, `-v, --verbose`.

### SDK + ask + servers + meta

```
smbls sdk                                     Proxy SDK service methods (debugging)
smbls sdk --list                              List all available SDK methods
smbls sdk --service <name>                    Filter methods by service
smbls ask [question...]                       Chat with AI about your project
smbls channels                                List + switch active CLI channel, with per-channel auth state
smbls config                                  Configure project settings (interactive or flag-driven)
smbls install                                 Install Symbols
smbls upgrade                                 Upgrade all Symbols deps to latest
smbls completion                              Generate shell completion script
smbls link-packages                           Links all smbls packages into the project
```

`ask` flags: `--provider <symbols|claude|openai|gemini|ollama>` (default `symbols` — the hosted Symbols Service, no API key), `--model <name>`, `--code` (Symbols-aware codegen lane, symbols provider only), `--init` (configure AI/MCP). The `symbols` provider's model lane: a named model (`--model` / the one saved by `--init`) keeps the lane that serves it; otherwise the platform's default AI (`defaultProvider` of `GET /core/ai/providers` on the active channel); otherwise `ai.simoneProvider` in `~/.smblsrc`, else Gemini.

`channels` (agents read this): the bare command is INTERACTIVE. In a TTY it
waits for the choice and applies it. Without a TTY (or with
`--non-interactive`, or `CI` set) it prints the list, explains that it cannot
prompt, names the non-interactive flags and **exits 1** — it never picks a
channel silently, and never falls back to production. Non-interactive flags:
`--list` (print and exit 0, never prompts — use this in scripts),
`--server <url>`, `--local`, `--dev`, `--next`, `--no-next` (production).
The listing shows each channel's auth state from the stored session —
signed in + expiry date, `auth expired <date>` with the exact
`smbls login --api-base-url <url>` to run, or not signed in; `--verify` adds a
status-code-only `/core/auth/me` probe. Token values are never printed.

`upgrade` flags: `--global-only`, `--local-only`, `--skip-mcp`, `--dry-run`.

---

## Publish flow (most-used scripted path)

The one-shot:

```bash
smbls publish                              # push current project + publish to all enabled envs
smbls publish --env staging                # push + publish only staging
smbls publish --env development,staging    # CSV (or --env development --env staging); only development|staging|production are accepted
smbls publish --no-push                    # skip push; publish an existing version
smbls publish --version <id|value>         # the LATEST version only (implies --no-push); an older one is refused before any write
smbls publish --version <old> --mode version --env <env>  # pin <env> to an older version; the published version stays
smbls publish --mode <mode>                # set this mode on every target, pinned envs included (latest|published|version|branch)
smbls publish --dry-run                    # print planned operations without executing
smbls publish --ssr                        # also pre-render every static route for the platform renderer
```

**Publish-time pre-render (`--ssr`).** Off by default. `smbls publish --ssr`, or `"prerender": true` in `symbols.json`, pre-renders every static route after the push and stores the result on the platform for the version it pushed: one row per route, outside the project content. The platform renderer serves it. `--no-ssr` wins over the config, and `brender: false` keeps it off.

- Static routes only. Pages render WITHOUT fetched data: a page that fetches shows its loading state until the client loads the data.
- Each route keeps its own icons: the sprite with the symbols its markup uses, AFTER its content, and no shared sprite (not released yet; it needs the `@symbo.ls/brender` release that exports the page trims). The page's text paints before its icons; an icon keeps its box until its symbol arrives, and the client adds every other icon of the design system when it boots. With an older brender, or a sprite that holds an element other than a symbol, every route shares one full sprite in front of its body, as before.
- Limits: 512 KB per route (its icons included), 16 MB for all routes ('/' first, then the page order), 120 s. A route whose render does not finish within 20 s is abandoned and skipped, and the next route renders at once.
- `--dry-run` writes the map to `.symbols_local/ssr-cache.json` and pushes nothing.
- A later content push without a fresh pre-render drops the stored map; the site falls back to the client render until the next `smbls publish --ssr`.

Per-env mode: each environment is republished in the mode it is configured with on the platform. An environment with no stored mode falls back to `published` for prod-like keys (`prod`, `production`) and `latest` for everything else.

A **held** environment is skipped when you do not name it: one pinned to a version (`mode: version`), or a `mode: branch` environment that tracks a branch other than the one you publish. Republishing it would move it off its configuration (the server drops the pinned `version` on any publish in another mode). The output names the skip, and `--dry-run` prints the same line:

```
  - staging pinned to 1.5.1 — skipped; pass --env staging to move it
```

To move a held environment, name it on the call (`--env staging`, or tick it in the interactive picker, where a held env is labelled and not pre-selected). It then publishes in its default mode (`latest` for staging). `--mode <mode>` moves every target, held ones included; `--mode version` re-pins to the version being published. A `symbols.json` `smbls.publish` default (`env`, `mode`) never moves a held environment. A CLI older than this behavior republishes every enabled environment in the default mode and drops the pin, so on an older CLI pass `--env` with only the environments you mean to move.

**`--version` publishes the latest version only.** A `--version` (id or value) that is not the branch's latest is refused before any write, and the error prints the pin command. `--dry-run` gives the same refusal. To serve an older version, pin environments: `smbls publish --version <old> --mode version --env <env>` pins each target env to that version's value (an id is resolved to its value) and leaves the project's published version unchanged. The platform publishes the branch head as the next minor (`1.6.0` → `1.7.0`), and the CLI prints the version the server answered, never the one passed. If the version mark fails, each `mode: published` env is reported failed (it keeps serving the previous published version) and the command exits 1; `latest` / `version` / `branch` envs still publish. To bring old content back, use `smbls project restore`, not a publish. An older CLI publishes the latest version under any `--version` and prints the requested one.

Granular equivalent (if you need to inspect/intervene between steps):

```bash
smbls push                                 # → server-side push
smbls project versions list                # see new version
smbls project versions publish <versionId> # mark as published
smbls project environments list            # see what's enabled
smbls project environments publish <env>   # republish each env to pick up new version
```

`smbls publish --dry-run` is the safest first run. Use it in any uncertainty — it walks the same flow and prints the API calls it WOULD make.

For full pre-publish checklist + common failures table see `FRAMEWORK.md` §10.

---

## MCP / agent usage rules

These are **hard requirements** when the CLI is invoked from a non-TTY agent (MCP, CI, automation):

1. **Always pass `--non-interactive`.** Without it, any missing required input opens an `inquirer` prompt that blocks forever. The CLI does not auto-answer.
2. **Always pass `-y, --yes`** for any command that has a "Are you sure?" confirmation gate (publish, delete, restore, project create, github connect, integrations purchase). Different flag from `--non-interactive` — this one APPROVES, that one DISABLES prompts. Every command that writes to the platform prints its target first (`Target: <channel> · <API base> · branch … (from <setting>)`) — `push`, `publish`, `sync`, `collab`, `files upload` / `rm`, `assets upload` / `rm` / `prune` / `sync`, `project environments publish|upsert|update|delete`, `project pipeline promote`, `project restore`, `project versions publish`, `project update --changes`, and `deploy` with the `symbols` provider (it runs a push) — and the destructive project writes: `project delete`, `project members add|remove|role|invite|invite-link|accept-invite`, `project versions create|update|snapshot`, `project libs add|remove`, `project update --shared-library|--no-shared-library` (or a `--meta` with `isSharedLibrary` / `libraryOptions`), `libs add|link|remove` (unless `--no-cloud-sync`) and `libs mark-shared`. `project create` is not gated. A PRODUCTION target needs `--yes` on the call (a terminal user types `production` instead) — without it the command exits 1 before auth. A `yes` default in `symbols.json` does not confirm production. The write helpers carry the same gate, and a process confirms a target once. `smbls collab --yes` confirms the target only (its initial sync still asks); `smbls start --collab` needs `--yes` without a terminal and passes it to the collab it spawns; `smbls workspace collab --yes` passes it to each child. On `smbls deploy`, `--save` saves the provider as the default; `-y` / `--yes` is the consent there too.
3. **Pin the channel explicitly** with `SYMBOLS_API_BASE_URL=<url>` on the call. `NODE_ENV` / `SYMBOLS_API_URL` do not move a target that comes from the machine's active channel, and that channel is shared by every shell — another session may have switched it.
4. **Authenticate via token, not browser.** Agent flows can't open a browser. Use:
   ```bash
   SYMBOLS_TOKEN=<token> smbls <cmd>
   # OR pre-login with:
   smbls login --non-interactive --token <token>
   ```
5. **Always check `--dry-run` first** for destructive ops (publish, delete, restore, env publish). They print the API calls; comparing dry-run output to actual is your safety net.
6. **Use the granular commands when you need branch logic.** `smbls publish` is one shot; if a step fails midway you have to manually unwind. `push` → `versions publish` → `environments publish` lets you retry just the failing leg.

**Recommended agent invocation skeleton:**

```bash
# Set channel + auth once per session
export SYMBOLS_API_BASE_URL=https://dev.api.symbols.app
export SYMBOLS_TOKEN=<from-secret-store>

# Then run with hard non-interactive + auto-confirm:
smbls push --non-interactive --yes
smbls publish --non-interactive --yes --env staging
smbls project versions list --non-interactive
```

If a command fails because of authentication, the CLI exits with `code: 'AUTH_REQUIRED'` (see `helpers/authEnsure.js:265-322`). Agents should treat this as a hard stop — re-running with the same env will re-fail. Re-issue the token via the secrets system, then retry.

---

## Error-handling contracts

Errors the CLI surfaces:

| Symptom | Source | Fix |
|---|---|---|
| `Cannot reach API server at <host>:<port>` | `bin/index.js:49-53` (ECONNREFUSED) | Wrong channel or server down. Pin the call with `SYMBOLS_API_BASE_URL=<url>`, or switch the machine's channel with `smbls channels` |
| `Authentication required` (`code: 'AUTH_REQUIRED'`) | `helpers/authEnsure.js:272` | Need `smbls login` or `SYMBOLS_TOKEN` env var |
| `Missing app key in symbols.json` | `helpers/symbolsConfig.js:29` | Run `smbls init` or hand-write `symbols.json` with `{ owner, key }` |
| `Project ${owner}/${key} not found on server` (with `--non-interactive`) | `bin/publish.js:89-92` | Run `smbls project create` first OR `smbls workspace create-missing` |
| `symbols.json names the key 'x' but no "owner"` | `helpers/projectIdentity.js` (`missingOwnerMessage`) | Add `"owner": "<org or user slug>"` to `symbols.json`, or name the record with `--project <id>` / `SYMBOLS_PROJECT_ID` |
| `… answered owner/key with the project 'other/key' — refusing` / `Identity mismatch` | `helpers/projectIdentity.js` (`identityMismatch`), `helpers/pushSync.js` | The server answered for another owner: nothing was written. Check `owner`/`key` in `symbols.json` against the platform record |
| `Bare key 'x' matches projects under MULTIPLE owners — refusing to guess.` | `bin/project/shared.js` | Use the `<owner>/<key>` form or a project id |
| Empty `inquirer` prompt that hangs | Missing required input + no `--non-interactive` | Always pass `--non-interactive` for scripted runs |

Ctrl+C / ESC during interactive prompts gracefully exits (handled at `bin/index.js:46-48`).

---

## Where the CLI source lives

| Concern | File |
|---|---|
| Command registration | `bin/index.js` (one import per command) |
| Top-level Commander config | `bin/program.js` (monkey-patches old commander compat) |
| Auth | `helpers/authEnsure.js`, `helpers/credentialManager.js` |
| Config resolution | `helpers/config.js` (loadCliConfig, saveCliConfig, getApiUrl, getProjectKeyOrId) |
| `symbols.json` parsing | `helpers/symbolsConfig.js` |
| Push pipeline | `helpers/pushSync.js`, used by both `push` and `publish` |
| API HTTP client | `helpers/apiRequest.js` + per-resource files (`projectsApi.js`, `organizationsApi.js`, etc.) |
| Subcommand families | `bin/project/commands/`, `bin/workspace/commands/`, `bin/github/commands/` |

Each subcommand file is registered by importing it in the `bin/<family>.js` parent. To add a new command:

1. Create `bin/<name>.js` exporting nothing (it self-registers via `program.command(...)`)
2. Add `import './<name>.js'` to `bin/index.js`
3. Done — no central registry.

---

## What never to do (CLI-specific)

- Don't run `smbls publish` as the first command in a fresh session without `--dry-run`. If your local config is wrong, you publish to the wrong project.
- Don't manually `rm -rf .symbols_local/`. Use `smbls clean` (preserves credentials, removes stale snapshots/locks).
- Don't pass auth tokens via `--token` flag in shared logs. Use `SYMBOLS_TOKEN` env var instead — it doesn't appear in `ps`/process listings.
- Don't run `smbls channels --no-next` casually. It makes `api.symbols.app` (production) the active channel of every shell on the machine, and any push/publish there is real-user-visible. Default to `next` for development.
- Don't rely on the global `smbls` binary version matching the monorepo `@symbo.ls/cli@3.14.0` — they may drift. Use `smbls --version` to check.
- A subcommand's own `--version <v>` option (e.g. `smbls publish --version <id>`, `smbls config --version <v>`) is a normal per-command flag, not the global `-V/--version` — Commander's positional-options handling means the two no longer collide; the subcommand's own flag reaches its `.action()` correctly as long as it appears after the subcommand name (`smbls publish --version <id>`, not `smbls --version publish <id>`).
- Don't combine `--all` with `--env` on `smbls publish`. `--env` overrides `--all`; the combination silently uses `--env` only.

---

## Cross-references

- Framework + plugin rules: `FRAMEWORK.md`
- Design system + theme contract: `DESIGN_SYSTEM.md`
- Modern smbls stack: `MODERN_STACK.md`
- SDK reference: `SDK.md` (`@symbo.ls/sdk`)
- Channel resolution + plugin source: the `@symbo.ls/channels` package and the smbls plugins (`@symbo.ls/{router, fetch, polyglot, helmet, brender, frank, mermaid}`)
- Per-command help: `smbls <command> --help`
- All help in one shot: `smbls --help-all` (commander's `outputHelp({ helpAll: true })` if registered)
