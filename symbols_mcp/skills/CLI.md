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

**Project identity is OWNER + KEY** (`helpers/projectIdentity.js`; the CLI release after 3.14.812). A key is unique per owner only — `web` can be acme/web, globex/web and initech/web — and the server's bare-key routes answer with the first match of ANY owner, so no command resolves the tree's project by its key alone. In order:

1. `--project <id>` / `SYMBOLS_PROJECT_ID` names the record outright;
2. else `.symbols_local/lock.json`'s `projectId`, only while the lock is stamped with this tree's `key`, `owner` and `apiBase`;
3. else `GET /core/projects/key/<owner>/<key>` — and the record must name that owner and key;
4. else a cached id (an unstamped lock's, `.symbols_local/config.json`'s) only when its record, read by id, shows this owner and key.

A `symbols.json` with a key but no `owner` is refused, never guessed. `push`, `publish`, `sync` and `fetch` refuse a record that names another owner. A bare key typed as an argument (`smbls project delete web`) resolves only when it is the ONE project with that exact key your token can see.

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

`smbls fetch` writes the project's runtime config back into `config.js` (frank after 3.14.810, which the CLI loads through its frank dependency): `polyglot`, `fetch`, `db`, `router`, `routerOptions`, `define`, `themeStorageKey`, `packageManager`, `editor`, `sync` and `notifications` (frank's `RUNTIME_CONFIG_KEYS`), read from the record's root — or from an older record's `config.<key>` — with functions as source text and the polyglot `translationsFrom` pointer as a string. An older CLI wrote only the design-system flags: the fetched tree lost the app's language setup, and the next `smbls push` sent the project without it. The record's other root keys stay out of `config.js`, because the root also holds the platform's own fields; a key of your own in `config.js` beyond the list (an app constant, a manifest) is not written back by a fetch. A fetch into a folder that already holds the tree (with or without `--update`) keeps the local `config.js` as it is: the CLI compares that tree file by file, and `config.js` is not in the comparison. A tree fetched with an older frank gets its runtime config back from a fetch into a new folder.

`push` writes the new content into the project's main branch. `publish` is push → mark new version as published → republish each environment so it picks up the version. See "Publish flow" below.

`push`'s differ is idempotent: an unchanged project reports "No changes to push" on every consecutive run — it does not re-report the same delete/update set forever or mint a junk version each time. (The differ specifically accounts for server-side read-path conveniences — e.g. missing design-system namespaces getting default-filled on read, or environment-export flags always being present on the fetched side — so those never show up as phantom deletes; and key-order drift inside a property bag like `attr`/`style`/`state` no longer counts as a real change unless it's a genuine reorder of child elements, where order IS meaningful DOM order.) If you ever see the same change set reported twice in a row with truly nothing edited locally, that's a regression worth filing, not expected behavior.

Every command that SENDS the local project — `push`, `sync`, `collab` and `github sync` — ships frank's stringified emission, never a raw `fn.toString()` of the live build. A handler's `await import('<pkg>')` arrives as that literal `import('<pkg>')` (the raw build carried esbuild's `init_X(), X_exports` wiring, which throws at runtime). frank's emission gate stands in front of every send: a globalScope defect blocks (`push`, `sync` and `github sync` exit 1; `collab` prints `[collab] Local change NOT sent` and keeps watching), and per-function debt is printed as a named warning. `SMBLS_NO_VERIFY_SERIALIZATION=1` bypasses the gate for all four; `push` also takes `--no-verify-serialization`.

**Self-hosted assets — `new URL('<relative path>', import.meta.url)`.** A value that names a project file this way (a font `url` in `designSystem`, an image in a component's `scope`) is published as a platform URL: `push` uploads the file to the project (public, keyed by its path from the project root, e.g. `assets/fonts/x.woff2`) or reuses the asset the platform already holds with the same sha256, so an unchanged file keeps its URL and uploads nothing; the assets join the project's `assets` map. By default only calls that run while the project loads are resolved; `"frank": { "importMetaUrls": "all" }` in `symbols.json` also resolves calls inside function bodies and in `app.js`. `smbls frank to-json` inlines such files as `data:` URLs and never uploads; `sync`, `collab` and `github sync` do not upload them and fail with an error naming the file and line. `smbls start` / `smbls build` (parcel) keep their own hashed assets; a later `smbls fetch` writes the published URL as a plain string.

**A package `dependencies.js` declares need not be installed for push.** frank stubs a declared runtime package that `node_modules` lacks and publishes its `import('<pkg>')` for the browser to load through the importmap (e.g. `await import('quill')` in a handler). A package nothing declares still fails to resolve (`package.json` dependencies never reach the platform's importmap), and a value computed from such a stub while the project loads fails the build (`FRANK_UNINSTALLED_DEPENDENCY_VALUE`).

**Since cli 3.14.829 / smbls 3.14.865:** the owner backstop below. `smbls collab` already refuses to start without a verified project id (run `smbls push` or `smbls sync` first to stamp `lock.json`). Its websocket handshake then names the project by `projectId` **and** `owner` (from `symbols.json`'s `owner` field) as a backstop — never a bare key, which is not unique across owners. If the server still answers `error { code: 'ambiguous_key', candidates }` (a key shared by more than one owner), the CLI prints the candidates once, as `owner/key`, and disconnects — it does not retry the same ambiguous join (`collab refused: the key 'x' names more than one project (…)`). Fix: add `"owner"` to `symbols.json`. The asset uploads of a collab session name the owner and the project id too; before, they named only the key and were skipped.

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

**Web Worker files and the SDK on demand** (since cli 3.14.826). `to-json` and `smbls push` ship each `workers/<name>.js` bundled (one ES module, imports inlined) in a `workers` section, and point every published caller's `new URL('…/workers/<name>.js', import.meta.url)` at `/__smbls/workers/<name>.js`, which the platform serves same-origin; `to-fs` writes a worker back only where the tree lacks it (FRAMEWORK.md §9 → Web Worker files). A literal `import('@symbo.ls/sdk')` in code publishes as the on-demand marker, so the published page loads the SDK on the first call; an older CLI publishes the `import()` as written, which a browser rejects (FRAMEWORK.md §10 → Host packages on demand).

**Function text is the author's** (frank 3.14.804). `to-json` and `smbls push` serialize each function as the text in its source file (comments, quotes, spacing, names), not esbuild's re-print. A fetched tree pushes back byte for byte: `smbls fetch` → `smbls push` no longer renames bindings (`getLightboxSrc2` → `getLightboxSrc23`) or drops comments. The first push after the upgrade changes the text of most functions once (same programs, author's formatting). When esbuild changed the function beyond formatting (an import read through the bundle, `define`, a folded constant, lowered syntax) the bundle text stays. `toJSON(dir, { authoredSource: false })` or `SMBLS_FRANK_BUNDLE_FUNCTION_TEXT=1` gives the old text; `FRANK_DEBUG_AUTHORED_SOURCE=1` names each function that keeps the bundle text, and why.

### Dev / build / deploy

```
smbls start [entry]                           Start dev server (symbols-runner default)
smbls build [entry]                           Build for production
smbls brender                                 Pre-render every static route to dist-brender/
smbls deploy                                  Deploy to a hosting provider
smbls redirects [--out-dir <dir>]             Rewrite the build's _redirects block from the output as it is now
smbls csp [--json] [--built [dir]] [--out <file>]  List the CSP script-src hashes the built pages can need (no build), or those they carry (--built)
smbls tunnel [port]                           Expose local port via tunnel.symbo.ls
```

`start` flags:

- `-p, --port <port>` (defaults to `symbols.json.port` or 1234)
- `--no-cache`, `--open`, `--bundler <symbols-runner|parcel|vite|browser>` (default: the `bundler` of `.symbols_local/config.json`, else of `symbols.json`, else `symbols-runner`)
- `--collab` (start with realtime collab) / `--no-collab` (skip prompt, run local)
- `--fresh` (wipe the caches first; `lock.json` and `config.json` stay)
- Any other flag goes to the bundler (`parcel serve` / `vite serve`) with the value after it; `start`'s own flags never do.

**The page's API** (runner {{RUNNER_SITES4}} / cli {{CLI_SITES4}}). A page that `smbls start` (or `smbls runner serve`) serves declares the API it talks to before the runtime starts — `window.__SYMBOLS_CHANNEL__` and `window.__SYMBOLS_ENV__ = { channel, projectEnv, apiUrl, socketUrl }`, the identity a published page gets from the platform — so the SDK, the `symbols` fetch adapter and the shared-library fallback all use one API. It is the API the run, the project or the CLI already names, in this order; with nothing named, production:

| Named by | Page API |
|---|---|
| `SYMBOLS_CHANNEL=<channel> smbls start` | that channel's API (`development`, `staging`, `production`, …) |
| `SYMBOLS_API_BASE_URL=<url>` (also `SYMBOLS_API_URL`, `SMBLS_API_URL`) | that API; it serves the socket too |
| `SYMBOLS_LOCAL=true` | `http://localhost:8080` (local) |
| the project: `.symbols_local/config.json` `channel` / `apiBaseUrl`, a legacy project `.smblsrc` `apiUrl`, `symbols.json` `useLocal` | the API the CLI uses in this directory |
| this machine's active channel (`smbls login --use`, `smbls channels`) | that channel's API |
| nothing | `https://api.symbols.app` (production) |

`NODE_ENV` never changes it. The start output prints the page's API under the URL, with what named it (`page API …`; in yellow when it is production, which is live data). To work against development data, run `SYMBOLS_CHANNEL=development smbls start`. `smbls build` output declares none: where it is deployed decides.

`build` flags: `--no-cache`, `--no-optimize`, `--no-brender`, `--strict`, `--out-dir <dir>`, `--bundler`. `build` copies `public/` (or `symbols.json` `publicDir`) into the output root and never replaces a file the bundler wrote. With brender on, `build` pre-renders each route into the bundler's `index.html`: `/x` → `x.html`, `/*` → `404.html` (rendered at the address `/404`), and exits 1 when no route renders (`--no-brender` opts out). Two routes that would write one file (`/404` and `/*`) are written once and the other is reported.

- **`200.html`** is the bundler's own document, kept before `/` overwrites `index.html`. Serve `200.html` for client-side routes — never `index.html`, which is now the home page with the home page's canonical and og tags (see Routes without their own page, below).
- **`_redirects`** in the output: each route without its own page → `/200`, status 200 (read by Cloudflare Workers static assets, Cloudflare Pages and Netlify). The project's own rules from `public/_redirects` stay first; a rebuild replaces only the build's block; `brender.redirects: false` writes none.
- **`smbls-ds.<sha>.json`**: the design system the pre-render prepared, written once next to the bundles, with a `<link rel="preload" as="fetch" data-smbls="design-system">` in every pre-rendered page. Client-rendered pages (`200.html`, the `index.html` of a build without a pre-render) get only `<meta name="smbls-design-system" content="…">`: the boot requests it at low priority after the app script and never waits for it (`build.prepareDesignSystem: false` leaves that reference out; `false` means `{ shell: false }`). `build.prepareDesignSystem: { pages: false }` (opt-in, cli 3.14.814) also leaves the preload out of the pre-rendered pages: their client then prepares the design system itself (210 KB raw / 35 KB brotli less per first visit on a measured app). Both together: `{ "shell": false, "pages": false }`. The app adopts it instead of processing its design system (FRAMEWORK.md §8 → The design system prepared at build time). A design system that holds a function gets no file. With `build.treeShakeIcons` on, the file leaves out the default icons the build dropped (cli 3.14.820), so a dropped icon logs the same loud error on a built page as in the app shell; icons the project's own design system registers stay.
- **`__smbls/host/sdk.<sha16>.js`** (since cli 3.14.826, symbols-runner bundler): the `@symbo.ls/sdk` file of a page whose code reads the SDK only on demand (`await import('@symbo.ls/sdk')` inside a function; FRAMEWORK.md §10 → Host packages on demand). `smbls build` writes it beside `index.html`, at the path the page declares, only when the page names it; a static or SDK-free build is byte-identical to before. `smbls start` serves it at `/__smbls/host/sdk.<sha256-16hex>.js` as immutable (`Cache-Control: public, max-age=31536000, immutable`, `nosniff`), also during the first build; any other file under `/__smbls/host/` is a 404, so a stale hash never gets another version's bytes. Deploy the folder with the rest of the output: the platform's page runtime serves the same path for a published project.
- **`symbols.json` `build.prepareDesignSystem`** (on by default) — which built documents reference the prepared design-system file. `false` (= `{ shell: false }`): the app shell (`200.html`) does not; pre-rendered pages keep theirs. `{ pages: false }`: the pre-rendered pages do not request it either (their client prepares the design system itself, as a page without the file always did; on a measured site it saved about 210 KB raw / 35 KB transferred per first visit). `{ shell: false, pages: false }` writes no file. The build log says what the setting did (cli 3.14.822): `build.prepareDesignSystem.pages is false: the pre-rendered pages do not reference a design-system file; the client builds the design system itself`, plus `(no design-system file written: no page references one)` when no file is written, and for the shell `build.prepareDesignSystem turns the app shell off: 200.html does not reference the design-system file; …`. These lines are information, not warnings.
- **Build-time data.** Every page carries the data answers of the build time until the next build, and one stamp per build: `<meta name="brender-stamp" content="<stamp>" data-time="<ms>">`. The stamp is `symbols.json` `brender.stamp` (a string or a number), else `config.js` `brender.stamp` — a value, or a function `({ time, data }) => stamp` run once per build (it may be async: the data's own version) — else the build time. A stamp function that throws fails the build. Since cli 3.14.826 the build also finds `config.js` `brender.stamp` when a `brender.context` module spreads config.js into the context, and reads it from the build-only `brender.module` too (Built-page options, below). How a page learns its data is stale: SYNTAX.md → Data Fetching → A pre-built page's data.
- **Assets.** A `file:` URL in a page (`new URL('…', import.meta.url)`, evaluated on the build machine) is mapped to the file the bundler emitted from the same source, or copied into the output under a content hash. A `file:` URL that names no project file fails the build.
- **`--strict`** (or `symbols.json` `brender.strict`) fails the build when a page was made with failed data or label requests, or shows raw label keys. Without it those pages are listed as warnings.
- **`symbols.json` `brender` as an object** (still on): `context` — the module the build's entry boots with (e.g. `symbols/siteContext.js`), so its pages are the ones pre-rendered; `exclude` — page keys to leave out (`"/admin*"` matches every key that starts with `/admin`); `paths` — addresses for routes with parameters (`{ "/:lang/about": ["/en/about"] }` → `en/about.html`); `strict`; `eagerImages` (default 2: later images get `loading="lazy"` unless they set `loading`); `timeout` — each page's render time limit in ms (default 30000; `0`: none): pages render one at a time, and a page past its limit fails with `BRENDER_RENDER_TIMEOUT` while the next page renders; `stamp` — the build's data stamp (above); `redirects: false` — no `_redirects` block. A page with `prerender: false` is never pre-rendered.
- **`brender.lazyGroups`** (a lazy route built as its group's real page) and the opt-in **built-page options** (`module`, `paths` as a function, `onProblem`, `report`, `paint`, `faces`, `app`, `pageScript`, `preloadImage`, `beforeWrite`): since cli 3.14.826 / brender 3.14.676 (`preloadImage`: since cli 3.14.831), the two sections below. `smbls csp` (since cli 3.14.831) lists the CSP hashes the built pages can need, with no build.
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
  **Its marks** (brender 3.14.678 / cli 3.14.827), for a host that serves a returning reader the faces it keeps by address, and the rest inline. `data-smbls-faces-version`: 12 hex characters of a SHA-256 of the sheet's rules — equal rules in the same order give the same version on every page and every build; any change to a rule, a rule more or less, or another order gives a new one. `data-smbls-faces-files`: per `@font-face` rule, in rule order, its file address — the first `url()` of its `src` (a `local()` before it is skipped) — space-separated, a space in an address written `%20`, and `-` for a rule that names no file (only `local()`, or a `data:` URL). `smbls build` writes the marks after the `file:` URLs point into the build output, so they name the files the page ships (every page of a build has the same version when the font URLs are site-root or absolute). `faces.inline` keeps both marks as they are, so an inlined face still names its file. No faces file is written. A step that changes the sheet's rules marks it again: `markFacesSheet(html)` from `@symbo.ls/brender/faces` (`facesSheetMarks(rules)` gives `{ version, files }`).
- **`symbols.json` `build`**: `"compileHints"` (on unless `false`) puts `//# allFunctionsCalledOnLoad` as the first line of each local module script the page loads at start (the app script, a project's own early script) and shifts its source map by one line: Chrome 136+ then compiles the bundle's functions while the script streams in, not on the main thread at first call. Measured on a built empty app (headless Chrome, medians of 9): first task 51.7 → 26.6 ms at 1x CPU, 270 → 135 ms at 4x. Lazily loaded files stay as the bundler wrote them; with `false` the output is byte-identical to the bundler's. `"modulePreload": true` (off by default) adds a `<link rel="modulepreload">` after the page's import map for every `smbls/core` lazy module `config.js` switches on (fetch when `fetch` is set; the windows, dropdown and tooltip kits unless `false`; `shorthand`, `analyze`, `inspect` when set). It is opt-in because no measurement shows a gain yet: the kits started at about 10 ms instead of about 90 ms, but the A/B ran on a machine under heavy load, never on a throttled phone profile. With it off the built page is byte-identical.

**Production build, dev diagnostics.** A parcel `smbls build` (production mode) strips the framework's dev-only warnings (author mistakes, e.g. an unknown design-system token) from the app bundle; since cli 3.14.813 that covers 62 more warnings, all behind `globalThis.__SMBLS_DEV_DIAGNOSTICS_OFF__`. `smbls start` keeps every warning. Parcel only: a Vite build keeps them all. Errors that report a runtime failure stay in every build (FRAMEWORK.md §10 → `smbls build`).

#### Lazy groups built ahead — `brender.lazyGroups`

Since smbls 3.14.859 / cli 3.14.826 / brender 3.14.676. The build writes a route of a `context.lazy` group as what its render shows at the end. `"lazyGroups": "load"` (every group) or `["texts", …]` (those groups) makes the render's first navigation load the group and then render the route, so the page is the group's REAL page, not its placeholder. The build reads `lazy` from the module `brender.context` names (else `symbols/context.js`): declare the group there. The group's `when` runs at build time too: false (or a failed load) builds the placeholder, so a staff-only group stays out of the built pages. Without `lazyGroups` the render does not wait: a route whose group loaded during the render (a context that declares `lazy`, for example through `brender.context`) is built as the group's page, else as its placeholder. Either way a page that shows a group's page names the group, `<meta name="brender-lazy" content="texts">`, and gets one `<link rel="modulepreload">` for the group's chunk after the page's own preloads (found through the chunk's source map; `"build": { "modulePreload": "strict" }` fails the build when it finds none). In the browser the boot reads the tag into `context.lazyFirstView`: the first navigation loads those groups and renders their pages, and the takeover adopts the built markup instead of mounting the placeholder over it. So public pages can move into a group, out of the main bundle, and still arrive built (SYNTAX.md → Router → Lazy routes).

```json
{ "brender": { "context": "symbols/context.js", "lazyGroups": ["texts"] } }
```

#### Built-page options (opt-in)

Since cli 3.14.826 / brender 3.14.676. A build without them writes the same pages as before. `paths`, `stamp`, `onProblem`, `report`, `paint`, `faces`, `app`, `pageScript`, `preloadImage`, `beforePaint` and `beforeWrite` are read from `symbols.json` `brender` first, then from the module `brender.module` names, then from `config.js` `brender` (also when a `brender.context` module spreads config.js into the context). Put functions in the module: config.js is bundled into the app, so a function there reaches every visitor; the build alone reads the module.

| Setting | Shape | What it does |
|---|---|---|
| `module` | `"scripts/brender.build.mjs"` | A build-only module (path from the project root) whose default export is brender settings, functions allowed. Never part of the app |
| `paths` | `{ route: [addresses] }`, or `({ data, routes, time }) => ({ … })` (may be async) | The addresses of each route with parameters. `data` is the project data, `routes` its page keys. The function runs once per build, before the first render (`smbls redirects` runs it too); a throw, or a value that is not an object of address lists, fails the pre-render |
| `onProblem` | `'write'` (default) \| `'skip'` \| `'fail'` | A page made with a failed request or a raw label key: written and reported; left out, so its address falls to `200.html` and the build goes on; or the build fails. `--strict` / `strict: true` mean `'fail'` and win |
| `report` | `true` \| `"path/report.json"` | A JSON report of every page (`true`: `<outDir>/brender-report.json`), written also when the build fails: `{ version: 1, ok, stamp, time, onProblem, pages: [{ route, pathname, file, status: 'written' \| 'skipped' \| 'failed', failedRequests: [{ url, reason }], rawLabelKeys, error?, faces?, facesRead?, image?, ms }], notPrerendered: [{ route, reason }], groupShells?: [{ group, file, routes }] }` (`groupShells`: since cli 3.14.828, a lazy group's shell copy; `facesRead`: whether the build read which faces the page draws; `image`: since cli 3.14.831, the address of the image `preloadImage` asked for). Fields are only ever added. Read it instead of the log |
| `paint` | `{ whole: true }` | The first paint waits until the page's markup is in: `<link rel="expect" href="#smbls-whole" blocking="render">` after the charset declaration and `<template id="smbls-whole">` after the markup. No script. The wait also ends when the parser finishes the document, so a page never stays blank; a browser without `rel=expect` paints as before |
| `faces` | `{ inline, wait, ready }` | `inline`: the page's own faces (`<style data-smbls-faces>`) as `data:` URLs — `true` (a family the page's styles name, whose `unicode-range` covers a character of the page), `['Family', …]` (those families, by the page's characters), or `(face, page) => boolean` (`face`: `{ family, weight, style, display, unicodeRange, href, bytes, used, hit }`, `page`: `{ route, pathname, file, lang, text }`). Since cli 3.14.828 / brender 3.14.679: `true` and the list take the faces the page DRAWS — `@symbo.ls/brender`'s `drawnFaces` reads each element's family, weight and style from the cascade (`!important`, specificity, order, inheritance, `var()`, the `font` shorthand, the browser's bold headings and system-font form controls) and puts each character of its text in the face the browser picks (style, weight, `unicode-range`); `@media` / state rules (`:hover`, …) count as possibilities, `::placeholder` and `::before` / `::after` strings count. A page with a stylesheet the build cannot read keeps the rule above. The function's `face` gains `drawn` (the characters drawn in it, `null` when the page was not read). The log prints `Faces drawn: read on N of M pages`; the report gains `pages[].facesRead`. Only files in the build output (the rest stay by address); a `<link rel="preload" as="font">` of an inlined file goes. `wait: true` (3000 ms) or `<ms>` (at most 10000): the page stays unseen (`opacity: 0`) until those faces load, at most that long, so no frame is drawn in another face's measures (no layout shift). The hold is CSS with its own cap. Since cli 3.14.833 the hold also waits for the faces the page keeps by address (a family `inline` leaves out, a file on another origin): the page's script loads them at once, a face that fails counts as loaded, and the cap still ends the hold; a page that draws no face has no hold. `inline: []` inlines no face and holds for every face by address (`inline: false` is not a value: leave `faces` out for no faces step). `ready` (since cli 3.14.828): `true` puts `window.__smblsFacesReady` (below) on every page with the script, `false` on none (an error with `app.after: 'faces'`); unset, a page has it when something names it |
| `app` | `'eager'` (default) \| `'afterFirstView'` \| `{ start: 'afterFirstView', wait: <ms>, after: <names> }` | `'afterFirstView'`: the app's scripts, their preloads and the design system's preload wait in `<template data-smbls-app>` before `</body>`. They go in a frame after the first view is in (the inline faces and the eager images), at once on the first `pointerdown`, `keydown` or `scroll`, and after `wait` ms (3000) at the latest. The app starts that much later; the import map stays. `after` (cli 3.14.827): `'faces'` (the page's faces, `window.__smblsFacesReady`, below), the name of a `window` property that holds a promise of the project's (for example one its `fetch.early` module sets), or a list of them — the files then also wait until each one settles (a rejection counts as settled); the first input and the `wait` cap still start them. A name the page has not set yet is watched: the project's later `window.<name> = promise` is the one waited for. `after` with `start: 'eager'` fails the build |
| `pageScript` | `'file'` (default) \| `'inline'` | How the small script that `faces` and `app` need ships (its settings are a `<script type="application/json" data-smbls-paint>` block). Since cli 3.14.828: a page's script holds only the parts that page uses — the faces' loads, the end of the hold (with `window.__smblsPaintReady`, below, since cli 3.14.831), the app's start and its `after` waits, the AVIF fallback (a page with a `<source type="image/avif">`), `window.__smblsFacesReady` (when something names it) — from 805 B (349 B Brotli) for the hold alone to 3,844 B (1,327 B Brotli) with every part (cli 3.14.831: the paint-ready promise added 110 B / 42 B Brotli to the hold); before cli 3.14.828, every page had the whole script (about 4 KB, 1.4 KB Brotli). `'file'`: `smbls-built.<hash>.js` next to the bundles (one per set of parts the pages use), an `async` tag after the faces sheet, preloaded from the top of the head; `script-src 'self'` runs it with no hash. It is one more request on a first visit (measured on a real app over slow 4G: first view 1.18 s with the file, 1.08 s inline); a repeat visit has it cached. `'inline'`: the script in the page; a policy without `'unsafe-inline'` allows it by its hash, which the build logs and `report` holds (`pageScript: { mode, hash }`; since cli 3.14.828: one hash per set of parts, `pageScript: { mode, hashes, scripts: [{ name, hash, bytes, parts, pages }] }`, with `hash` while every page has the same script). A hash changes only with a CLI release; `smbls csp` (below) lists every hash the settings can give, with no build |
| `preloadImage` | `true` \| `false` (default) | Since cli 3.14.831. The first view's image asked for from the head: `<link rel="preload" as="image" fetchpriority="high">` right after `<meta name="viewport">` (above it, a phone reads `imagesizes` against the 980 px default viewport and fetches a larger copy), else after the charset declaration. The image: the page's first `<img fetchpriority="high">`, else its first image that loads eagerly (the build makes all but the first `eagerImages` lazy) and is not `fetchpriority="low"` — how a page says "not this one" (a logo). From a `<picture>`: its first `<source>` with a `srcset` (`imagesrcset`, `imagesizes`, `type`, `media`), the one a browser that knows the type takes; a browser that does not know the type skips the preload, so no browser fetches a second copy. A plain `<img>`: its `srcset`, `sizes` and `src`. Its `crossorigin` and `referrerpolicy` go along (a preload whose request differs from the image's is fetched twice). A head that already preloads the image keeps its own link. Markup only: no script, no new CSP hash. The build logs the pages that have no such image; `report` names each page's (`pages[].image`). Measured on a real app (mobile, slow 4G, 4× CPU) whose ~70 KB of inline faces came before the `<img>`: the first view's photo came 0.36–0.64 s sooner on every page |
| `beforePaint` | `"scripts/fit.js"` | Since cli 3.14.832. A classic script file of the project (a path from the project root) that must run before the page's first paint — for example a script that fits titles to their boxes and measures text in its own face. Its code goes right after each page's markup, on every built page (with or without `faces` and `app`): inline (`pageScript: 'inline'`) as `<script data-smbls-before-paint>…</script>`, its hash in the build log, the report and `smbls csp`; else as `<script data-smbls-before-paint src="/smbls-built.<hash>.js">`, which blocks the parser at that point (so it runs there) and which `script-src 'self'` runs. On a page held by `faces.wait` the hold ends only after the file has run AND the faces are in (or at the cap), in either `pageScript` mode, so the file measures before the visitor sees the page; the file finds `window.__smblsPaintReady` in both modes and can wait on it to measure again in the final faces. The hold waits for the file's own run, not for work it starts (a promise, a timer); a file that throws still lets the hold end; a file that never runs (a failed load, a blocked script) lets it end when the parser has finished the page; the cap ends it whatever the file does. The first view also waits for the parser to reach the end of the markup (within the cap). The build puts one line on the file's first line (180 B inline, 365 B as a file; 120 / 189 B Brotli): line numbers stay, no function goes around the code, its top-level names stay global, a strict file stays strict. A missing file, a file that is not a classic script (`import`, a syntax error) and, inline, a text holding `</script` or `<!--` fail the build, naming the file |
| `beforeWrite` | `(html, page) => html` (may be async) | The project's last word on each written page (not a skipped one, not `200.html`). `page`: `{ route, pathname, file, stamp, time, afterMarkup(html, markup) }` — `afterMarkup` puts `markup` right after the page's markup (after a `beforePaint` file). Return the page as a string; a throw or anything else fails that page. Use it instead of a step after the build that parses the files again. A script that must run before the first paint is `beforePaint`: markup added here has no place in the `faces.wait` hold, so a script added here can run after the page is shown |

```js
// scripts/brender.build.mjs — symbols.json: { "brender": { "module": "scripts/brender.build.mjs", "report": true } }
export default {
  onProblem: 'skip',
  faces: { inline: true, wait: true },
  app: 'afterFirstView',
  preloadImage: true,
  beforePaint: 'scripts/fit-titles.js',
  beforeWrite: (html, page) => page.afterMarkup(html, '<script src="/after-markup.js" defer></script>')
}
```

**`window.__smblsFacesReady`** (cli 3.14.827). A page with the script (`faces` or `app` on) has a promise of the faces it draws (since cli 3.14.828: only when something asks for it — `app.after: 'faces'`, `faces.ready: true`, an inline script of the page or a `.js` file of the build output that names it; never with `faces.ready: false`): its inline faces and the ones its faces sheet keeps by address (a family the page's styles name whose `unicode-range` covers a character of the page — every weight and style the sheet declares for that family, as `inline: true` took them before cli 3.14.828; since then only the faces the page draws, as `inline: true` takes them, each loaded with a character drawn in it), loaded with `document.fonts.load` per family, weight and style. It resolves with the `FontFace` objects that loaded; at its time limit (the `faces.wait` cap, else 3000 ms) with the ones in so far; at once with `[]` when the page draws no faces or the browser has no `document.fonts`. It never rejects. The faces by address load only when something reads the promise (`app.after: 'faces'`, or the project's code), so a page that does not ask loads what it loaded before. A promise the page already holds under that name is kept. With `pageScript: 'file'` the script is `async`, so code that runs before the app's files may run before it: use `app.after`, or read the promise from the app.

**`window.__smblsPaintReady`** (since cli 3.14.831). A page held by `faces.wait` has a promise of the hold's end, resolved in the task that shows the page (its faces are in, or the cap). Code that waits on it runs before the page's first visible frame: a script that fits titles to their boxes measures in the faces the visitor sees, and the visitor never sees the titles move. Ship such a script as the `beforePaint` file (since cli 3.14.832): the hold waits for its run. A script added with `beforeWrite`'s `afterMarkup` is outside the hold and can run after the page is shown; then the promise is already resolved and the titles move in view. It never rejects. A page without the hold has none: `Promise.resolve(window.__smblsPaintReady)` is in at once there. `<html data-smbls-paint-wait>` is the hold's state from the page's first byte (the hold itself is CSS); the script removes it in the same call that resolves the promise. A script that can run before the page's script (with `pageScript: 'file'` that script is `async`) reads the attribute first: while it is there, the page is held. A promise the page already holds under that name is kept.

**A failed AVIF falls back** (cli 3.14.827). A browser skips a `<source type="image/avif">` only when it does not know the type, never when the file fails (a 404, a decode error). On a page with the script (since cli 3.14.828: and an AVIF `<source>`, the only pages that get this part), when an `<img>` fails on the AVIF its `<picture>` offers, the script removes that `<source>` once, and the browser picks the next source (WebP) or the `<img>`'s own `src`. An image that failed before the script ran is handled when it runs; an image that loads is never touched. No project image-error handler is needed for this.

#### `smbls csp` — the CSP hashes of the built pages, with no build

Since cli 3.14.831. Lists the `script-src` hashes the project's built pages can need, read from its settings as `smbls build` reads them (`symbols.json` `brender`, the build-only module, `config.js`), with no build: every inline page script its `brender` settings can give (`pageScript: 'inline'`, one per set of parts — the faces' loads, the hold, the hold's wait for the `beforePaint` file, the faces promise, the AVIF fallback, the app's start and its waits), the `beforePaint` file's script (inline; since cli 3.14.832) and the inline `fetch.early` script (`fetch.early.inline`, FRAMEWORK.md → Early requests). A build's `report` lists only the scripts of the pages it wrote: a page built later can carry another set of parts, and a CLI release (or an edit of the `beforePaint` file) changes the scripts' text. Write the policy from `smbls csp` in the deploy step, so a CLI release or a new page never meets a policy that lacks its script's hash.

```bash
smbls csp          # one 'sha256-…' per line, each followed by a note of the script it allows
smbls csp --json   # { hashes, pageScript, early } — `hashes` is what script-src needs
smbls csp --built                  # after a build: the inline scripts the built pages carry, the bundler's import map too
smbls csp --built --out csp.json   # the JSON in a file, for the deploy step that writes the policy
```

`--json`: `pageScript` is `{ mode, scripts: [{ hash, bytes, parts, path? }] }` (`path`: the `beforePaint` file's script; `null` without `faces`, `app` and `beforePaint`); `early` is `{ mode: 'inline', hash, bytes }` or `{ mode: 'file' | 'none', why? }` (`null` without `fetch.early`); `hashes` holds only the inline ones. Scripts that ship as files (`pageScript: 'file'`, an early script that is not inline) need no hash: `script-src 'self'` runs them. Settings that do not parse, or a project that does not load, exit with status 1 and the reason.

**`--built [dir]`** (since cli 3.14.833) reads the built pages themselves, after the build (default: the build's output folder). A list made from the settings cannot know the bundler's own inline script: Parcel writes the bundles' names into an inline `<script type="importmap">` in each page, and a policy without `'unsafe-inline'` must allow it by its hash, or the browser drops the map and the app's first import of a bundle fails ("Failed to resolve module specifier"). `--built` lists each inline script a browser runs — classic, `module`, `importmap`, `speculationrules`; a data block such as `application/json` needs no hash — hashed as the browser hashes it, with how many pages carry it and the first one. The build's page report (`brender-report.json`) names what each one is (`from`): `pageScript` (with its `parts`), `beforePaint` (its `path`), `early`, `importMap`, or `page` (the project's `index.html`, its `beforeWrite`, a step after the build). `--json`: `{ dir, pages, report, hashes, scripts: [{ hash, type, bytes, pages, first, from, parts?, path? }] }`. **`--out <file>`** writes the JSON `--json` prints to a file (its folder made), in both modes.

`smbls csp` lists `script-src` only. Inline faces (`brender.faces.inline`) are `data:` URLs in the page's faces sheet, so a policy that names `font-src` (or `default-src` alone) needs `data:` there too (`font-src 'self' data:`); without it the browser refuses each inline face and the page draws in the fallback face.

#### `symbols.json` `build` — size options of a production build (opt-in)

Options of a production parcel `smbls build` (cli 3.14.813 / 3.14.814, smbls 3.14.847 / 3.14.848; `treeShakeFeatures.drop` and the exact feature triggers: cli 3.14.817, smbls 3.14.849; `drop` refused for a needed feature: cli 3.14.818; the `smbls/core` kits, `capsize`, the channels and shadowed-icon rules: since smbls 3.14.858 / cli 3.14.825; lazy group parts: since smbls 3.14.859 / cli 3.14.826). Each is off unless set. With none set, the bundle is the same as before they existed.

| Option | Value | What it does |
|---|---|---|
| `treeShakeComponents` | `true` \| `{ "keep": [...] }` | Keeps only the default components (`@symbo.ls/default-config`) the app names, what they name in turn, and `keep` |
| `treeShakeIcons` | `true` \| `{ "keep": [...] }` | The same for the default icon set. A default icon that the project's own `designSystem.icons` replaces under the same name is dropped whatever names it (the project's icon renders either way); `keep` still keeps it. The build line counts them: `(N replaced by the project's own: a, b)` (since smbls 3.14.858 / cli 3.14.825) |
| `treeShakeLibraries` | `true` | For a project with no shared library (no `sharedLibraries.js` entry, no `symbols.json` `sharedLibraries`): no shared-library machinery in the bundle, and (since smbls 3.14.858 / cli 3.14.825) no `@symbo.ls/channels` in the boot |
| `lazyServerUtils` | `true` | The server-only utils `generateMetaTags`, `getPageMetadata`, `getImportMapScript`, `polyglotStartupScript`, `objectToString`, `deepStringifyFunctions` load on demand from their own file. Called in the browser (`el.call(...)`), each returns a **Promise** of its value — `await` it |
| `treeShakeFeatures` | `true` \| `{ "keep": [...], "drop": [...] }` | Drops the optional framework features the project never names (names below). `drop` forces a feature out |

`treeShakeFeatures` feature names (use these in `keep` and `drop`): `autoGrow`, `inertOutside`, `bridge` (`onBridgeMount` hooks), `viewEvents` (`onInView` / `onLeaveView`), `lazyRoutes` (lazy route groups, `loadLazy`), `viewTransition` (`designSystem.viewTransition`), `liveSync` (live sync / notifications), `prerender` (the boot over a pre-rendered page; always kept when the build pre-renders, i.e. `brender` is not `false`), `safeInk` (`getSafeInk` / `getSafeInkInfo`), `containerVw` (`vw` lengths that follow a `breakpointsFrom` container; trigger `breakpointsFrom`, smbls 3.14.857), `capsize` (the capsize font-metrics plugin; since smbls 3.14.858 / cli 3.14.825), `routeHead` (since smbls 3.14.862 / cli 3.14.828: a route entry's own head — `'/x': { extends: 'X', metadata: {…} }` — and the router's one page across such entries; no word decides it: the build reads the loaded pages, the app's `routes`, every nested `routes` table and each lazy group's pages, and keeps it for an entry that adds only a head to the component it names, two entries of one component (`'X'` beside `{ extends: 'X' }`), an own head that merges with its component chain's metadata, a head set as `helmet`, or routes it cannot read — a computed `routes`, a lazy group that does not load; the build log names the route; a build without it routes and shows heads as before, and a route it could not read that needs the feature logs the one `console.error`), `themeColorList` (since smbls 3.14.862 / cli 3.14.828: the `'theme-color'` list `[{ content, media }, …]`, one meta per entry; kept when the source sets `'theme-color'` to a list, a name or a call — not for a plain colour; a list met at runtime writes no tag and logs the one `console.error`), `faceWait` (since smbls 3.14.865: the `faceWait` prop, `designSystem.faceWait` and `el.facesReady()`; triggers `faceWait`, `facesReady`; DESIGN_SYSTEM.md → fonts), `faceWaitLinks` (since smbls 3.14.869 / cli 3.14.832: the part of `faceWait` that waits for a family stylesheet still on its way — the `<link data-smbls-font>` smbls writes for a design-system font served by Google Fonts. No word decides it: a build that keeps `faceWait` leaves it out when the loaded configuration names no Google Fonts address in the design system's `font` table — any key spelling, any depth of the entry (`url`, a weight list, a `url` list); `keep` keeps it for a design system the build cannot read, and a configuration that names one refuses `drop`. A build without it that meets a Google Fonts family at run time logs the one `console.error`; the family still loads. With self-hosted faces only, faceWait's chunk is 676 B smaller minified, 255 B Brotli; a build that keeps the wait has the same chunk as before, byte for byte). Measured on a small app (smbls 3.14.862 / cli 3.14.828): `routeHead` and `themeColorList` both left out take −2,974 B raw / −743 B Brotli out of the main bundle. With `liveSync` dropped, the boot also leaves out the sync applier's page tests (smbls 3.14.858). With `"smblsEntry": "core"` the option also leaves out the kits the configuration never switches on and moves group-only parts out of the main bundle (`smbls/core` kits, Lazy group parts: below).

**What keeps a feature.** The framework itself uses it, a default component the build keeps uses it, `keep` lists it, or the app source names one of its triggers. Each trigger is the setting that switches the feature on, not a bare word:

- `liveSync` — `socketUrl` as a key or member (`editor.socketUrl`, `settings.socketUrl`), `notifications: true`, `verbose: true`, or the runner (`'runner'`). A member named `editor` (a text-editor instance at `scope.editor`) does not keep it. `livesync` / `liveSync` alone does not keep it. `notifications` / `verbose` with another value, or a read (`state.notifications`), does not keep it.
- `lazyRoutes` — `lazy` as an object key or an assigned member with a non-literal value (`lazy: { … }`, `ctx.lazy = groups`), or `loadLazy`. `React.lazy(`, `z.lazy(`, `lazy: true`, `lazy: 'admin'`, `loading: 'lazy'` and a read of `ctx.lazy` do not keep it.
- `capsize` — `useCapsize` or `metrics` as a key, the plugin API (`capsizePlugin`, `capsizeHandler`, `computeCapsize`), or a `fontFamily` / `font_family` / `fontfamily` key set to a font of capsize's system metrics table (`fontFamily: 'Inter'`; case and quotes ignored). A family's `value` list never keeps it. capsize writes CSS only for an element whose font has metrics, so a project with none loses nothing.
- The other features keep their trigger names: `autoGrow`, `inertOutside`, `onBridgeMount`, `onInView` / `onLeaveView`, `viewTransition`, `getSafeInk` / `getSafeInkInfo`; `prerender` by the build option `brender`.

**`drop` — force a feature out.** When the app spells a trigger for something else (the scan cannot tell), list the feature in `drop`. The build refuses the drop, with a warning that names the reason, and keeps the feature when:

- the framework itself uses the feature, or `keep` also lists it;
- a build option or the project config needs it (cli 3.14.818): `prerender` while the build pre-renders (`brender` on); `lazyRoutes` when `context.lazy` is an object; `viewTransition` when `designSystem.viewTransition` is set; `liveSync` when a `socketUrl`, the runner, `notifications: true` or `verbose: true` is set; `capsize` when a design-system font family carries `metrics` (unless `typography.useCapsize: false`). A context the build cannot read refuses the drop too.

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

#### `smbls/core` kits — `treeShakeFeatures` with `"smblsEntry": "core"`

Since smbls 3.14.858 / cli 3.14.825. With `treeShakeFeatures` and `"smblsEntry": "core"`, the build also leaves out each kit the project's `create()` configuration never switches on, so the output has no file for it (measured on a real app: 16 fewer files, −81 KB of js, −662 KB of source maps). The kits: `windows`, `dropdown`, `tooltip` (on unless set `false`); `shorthand`, `analyze`, `inspect` (on when set); `fetchOnCreate` (the remote project fetch, only with an `editor` configuration); `local` (the `@symbo.ls/fetch` local adapter). The build reads the loaded configuration, not a word scan. A kit stays when the configuration switches it on, `keep` lists it, a string of the project names it (`adapter: 'local'`), or the build cannot read the configuration. The kit names work in `keep` and `drop`; a `drop` that the configuration contradicts is refused: `⚠ build.treeShakeFeatures.drop: kit <name> stays (<reason>)`. Build line: `Tree shaking (build.treeShakeFeatures, smbls/core kits): keeps N/M (name: why; …), leaves out …`. A left-out kit that the app asks for at runtime logs its one `console.error` (Loud errors, above) and resolves to nothing.

#### Lazy group parts — `treeShakeFeatures` with `context.lazy`

Since smbls 3.14.859 / cli 3.14.826. Framework parts that only `context.lazy` groups use leave the main bundle. Conditions: `treeShakeFeatures` on, `"smblsEntry": "core"`, `lazyRoutes` kept, and `context.lazy` groups whose loaders are plain `() => import('./file.js')`. The build scans the main code and each group's own code apart (comments do not count). The parts: `inertOutside`, the bridge hooks (`onBridgeMount`) and `TooltipLayer`. When only group code uses a part, the build moves it into one file, `smbls.core.lazyParts-*.js`. smbls loads that file together with the first group load, and installs the parts before the group merges, whether that load comes before or after the first render. A part stays in the main bundle, with no extra request, when the main code names it, `keep` names it, a default component of the main bundle uses it, or the framework, a build option or the configuration needs it. When the build cannot name a group's entry file, every part stays; a group entry that the main code also imports statically counts as main code. Measured on a real app: main bundle −2,495 B Brotli; the first group load makes one more request (4.2 KB Brotli). Build line: `Lazy group parts (<groups>): loaded with the first group load: <parts>` (or `none moved`), then `; <part> stays …` with each reason; or `Lazy group parts: every part stays in the main bundle (<reason>)`.

Since smbls 3.14.862 / cli 3.14.828 (per group): the build also reads each group's own code apart. A group whose own code names none of the moved parts loads only its own chunk; the parts load with the first load of a group that uses them. The build writes those groups into the bundle as one number (a bit per group name, 31 bits). Two names can share a bit, and that group then loads the parts too, as every group did before 3.14.862. When a moved part is named by no single group's code, every group loads the parts. A page built with a group's page (`brender.lazyGroups`) whose group loads the parts also preloads `smbls.core.lazyParts-*.js`, after the group's chunk; a build with no such file warns, and `build.modulePreload: "strict"` fails it. Build line: `Lazy group parts (<groups>): loaded with the first load of a group that uses them: <parts> by <group>, <group> (no part: its own chunk only)`.

Since cli 3.14.828 (a shell copy per group): beside `200.html` the build writes `200-<group>.html` for each `context.lazy` group that has routes (pages with `lazy: '<group>'`). The copy is `200.html` with a `<link rel="modulepreload">` of the group's chunk, and of `smbls.core.lazyParts-*.js` when the group loads the parts; no script and no CSP change. The group's routes without their own page answer with `/200-<group>` instead of `/200` (`_redirects`, vercel.json rewrites, `smbls redirects`). The build writes the copies also with `brender.redirects: false`, and the page report lists them: `groupShells: [{ group, file, routes }]` (the routes as the pages map declares them, `/:lang` forms included), so a Worker that serves the shell itself can pick the copy. A group whose chunk the build cannot find (no source maps) or whose name is not a file name (letters, digits, `_`, `-`) gets no copy and a warning; its routes keep `200.html`. A file already there is never written over.

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
smbls publish --ssr --ssr-variant-budget 8 --ssr-variant-route-cap 1024   # the agent-view renders' own size budgets (MB for all, KB for one)
```

**Publish-time pre-render (`--ssr`).** Off by default. `smbls publish --ssr`, or `"prerender": true` in `symbols.json`, pre-renders every static route after the push and stores the result on the platform for the version it pushed: one row per route, outside the project content. The platform renderer serves it. `--no-ssr` wins over the config, and `brender: false` keeps it off. A CLI write keeps `prerender` in `symbols.json` since cli 3.14.827; an older CLI dropped it (with `smbls`, `name`, `framework` and other read keys) in the version stamp after every push or sync, so with an older CLI pass `--ssr` on the publish.

- Static routes only. Pages render WITHOUT fetched data: a page that fetches shows its loading state until the client loads the data.
- A page with `prerender: false` (a top-level key of the page object), and each page key that symbols.json `brender.exclude` names (an exact key, or a trailing `*` for every key that starts with what comes before it), is left out, as `smbls build` leaves it out: no render, no share of the limits. The report lists it as `not pre-rendered (prerender: false)` or `(excluded)`. Keep a page that only redirects in the browser out this way (since cli 3.14.827).
- Each route keeps its own icons: the sprite with the symbols its markup uses, AFTER its content, and no shared sprite (since cli 3.14.826 / brender 3.14.676). The page's text paints before its icons; an icon keeps its box until its symbol arrives, and the client adds every other icon of the design system when it boots. With an older brender, or a sprite that holds an element other than a symbol, every route shares one full sprite in front of its body, as before.
- Each route is served with the CSS its first view needs (not deployed yet): the atomic rules its markup can match and the CSS variables its CSS and markup read. The client adds the rest as it boots. Every variable stays when the page can load a stylesheet the platform cannot read: a `<link rel="stylesheet">` in the project's `index.html` or in the page, or an `@import`.
- Limits: 512 KB per route (its icons included), 16 MB for all routes ('/' first, then the page order), 120 s. A route whose render does not finish within 20 s is abandoned and skipped, and the next route renders at once. At most 500 routes per version, agent-view renders included (since cli 3.14.832): the platform refuses a larger write as a whole.
- **Agent view** (since cli 3.14.832). A project whose `config.js` declares `agentView` — `{ param: 'view', on: 'agent', off: 'human' }`, or `true` (or `{}`) for those three — gets each stored route rendered once more at the view's query and stored as `<route>?<param>=<on>` (`/pricing?view=agent`, `/?view=agent`), the key the platform renderer reads a page's agent view from (it serves that view to AI crawlers, which read only the served HTML). The page reads the query from `location.search` at init, as in the browser, so it renders that view. Rules (the platform renderer's): `param` a letter, then up to 31 letters, digits, `_` or `-`, not starting with `__smbls`; `on` / `off` 1–32 of those, and different. A declaration outside them is printed (`agent view not pre-rendered: …`) and the publish stores the pages alone. The renders come after every page ('/' first, then the page order), within the publish's 120 s, so one never takes a page's place; a route whose own render was not stored gets none. They have size budgets of their own: 8 MB for all of them (`--ssr-variant-budget <MB>`, or `symbols.json` `brender.variantBudgetMB`) and 1 MB for one (`--ssr-variant-route-cap <KB>`, or `brender.variantRouteKB`; 1024 is also the most, the platform's cap per stored row). A flag wins over symbols.json; a value that is not a number above 0, or that passes the platform's cap, stops the publish with a message that names it. The write also stays inside the platform's 20 MB per version (the styles included), so with pages that fill their 16 MB the renders get what is left: leave out pages crawlers do not need (`prerender: false`, `brender.exclude`) to give them more. The report counts them apart (`N of M static routes stored and K of L variant renders (?view=agent; X KB)`) and warns once when one is left out, with the count, the first route left out and the reasons (`⚠ 12 of 57 variant renders not stored, from /pricing?view=agent: 12 variant budget spent (8 MB)`).
- Page code that throws after its render (in a timer, or in a promise it never handles) is reported once per message, as a browser reports it, and the publish goes on (since cli 3.14.827 / brender 3.14.678). It still breaks that code's own work: check `el.context.ssr === true` before code that measures (FRAMEWORK.md §8 → In the server render).
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
| `symbols.json names the key 'x' but no "owner"` | `helpers/projectIdentity.js` (`missingOwnerMessage`) | Add `"owner": "<org or user slug>"` to `symbols.json`. The commands that take `--project` (`assets`, `files`, `project`) also name it: `--project <id>` / `SYMBOLS_PROJECT_ID`. `fetch`, `sync`, `push` and `collab` have no `--project` option and name only the `owner` fix (since cli 3.14.829; before, they named `--project` too) |
| `… answered owner/key with the project 'other/key' — refusing` / `Identity mismatch` | `helpers/projectIdentity.js` (`identityMismatch`), `helpers/pushSync.js` | The server answered for another owner: nothing was written. Check `owner`/`key` in `symbols.json` against the platform record |
| `Bare key 'x' matches projects under MULTIPLE owners — refusing to guess.` | `bin/project/shared.js` | Use the `<owner>/<key>` form or a project id |
| `collab refused: the key 'x' names more than one project (…)` | `bin/collab.js` (server `ambiguous_key`; since cli 3.14.829) | Add `"owner"` to `symbols.json` |
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
