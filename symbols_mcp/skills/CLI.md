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
| `symbols.json` | Project identity (key, owner, version, branch, dir, sharedLibraries) | ✅ git-tracked — the canonical project pointer |
| `.symbols_local/config.json` | Tooling + API config (apiBaseUrl OR `channel`, projectKey, projectId, bundler, packageManager, runtime, deploy) | ✅ git-tracked — local overrides + auto-link state |
| `.symbols_local/lock.json` | Snapshot metadata (etag, version, projectId, pulledAt) | ⛔ gitignored — refreshed by every `push`/`pull` |
| `.symbols_local/project.json` | Full project snapshot from server | ⛔ gitignored |
| `.symbols_local/libs/` | Scaffolded shared libraries (read-only) | ⛔ gitignored |
| `.symbols_local/snapshots/` | Pre-write source snapshots for `restore` | ⛔ gitignored |

API URL resolution order (verified `helpers/config.js:128-167`):

1. `SYMBOLS_API_BASE_URL` env var
2. `.symbols_local/config.json` `channel` field → `apiUrl(channel)` from `@symbo.ls/channels`
3. `.symbols_local/config.json` `apiBaseUrl` literal (legacy)
4. Legacy `.smblsrc` `apiUrl` (legacy)
5. `useLocal: true` in `symbols.json` → channel `local`
6. `useNext: true` in `symbols.json` (default) → channel `next`
7. Global credential manager (set by `smbls login`)
8. Channel `production` (final fallback)

Env-var URL overrides (always win, no editing files needed):

- `SYMBOLS_API_URL` — direct URL override
- `SYMBOLS_API_CHANNEL` — channel name (`local`, `development`, `next`, `test`, `upcoming`, `staging`, `preview`, `production`)
- `SYMBOLS_PROJECT_KEY`, `SYMBOLS_PROJECT_ID`, `SYMBOLS_BRANCH`, `SYMBOLS_OWNER` — per-process project pin

Auth tokens live in the OS keychain via `CredentialManager` (`helpers/credentialManager.js`); not in `.symbols_local/`. Wipe with `smbls logout`.

---

## Common flag conventions

Every command that hits the API accepts these. Prefer them over editing `.symbols_local/config.json` for ad-hoc runs.

| Flag | Effect |
|---|---|
| `--local` | Target `http://localhost:8080` (channel `local`) |
| `--next` | Target `https://next.api.symbols.app` (channel `next`) — current default |
| `--no-next` | Target `https://api.symbols.app` (channel `production`) |
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

### Sync data with platform

```
smbls push                      Push local changes to platform
smbls pull / fetch              Fetch project snapshot from platform
smbls sync                      Two-way sync (merge / remote-wins / local-wins)
smbls collab                    Live websocket collab; mirrors local edits to remote and vice-versa
smbls publish                   Push + version + republish all enabled environments (one shot)
```

`push` writes the new content into the project's main branch. `publish` is push → mark new version as published → republish each environment so it picks up the version. See "Publish flow" below.

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

smbls project libs list                       List linked shared libs
smbls project libs available                  List available shared libs on platform
smbls project libs add <lib...>               Add one or more shared libs
smbls project libs remove <lib...>            Remove one or more shared libs

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

Flags: `to-json` accepts `-o, --output <path>`, `--no-stringify`, `-v, --verbose`. `to-fs` accepts `--overwrite`.

### Dev / build / deploy

```
smbls start [entry]                           Start dev server (parcel default)
smbls build [entry]                           Build for production
smbls brender                                 Pre-render every static route to dist-brender/
smbls deploy                                  Deploy to a hosting provider
smbls tunnel [port]                           Expose local port via tunnel.symbo.ls
```

`start` flags:

- `-p, --port <port>` (defaults to `symbols.json.port` or 1234)
- `--no-cache`, `--open`, `--bundler <parcel|vite|browser>`
- `--collab` (start with realtime collab) / `--no-collab` (skip prompt, run local)

`build` flags: `--no-cache`, `--no-optimize`, `--no-brender`, `--out-dir <dir>`, `--bundler`.

`brender` flags: `--out-dir <dir>` (defaults to `brenderDistDir` from symbols.json or `dist-brender`), `--no-isr`, `--no-hydrate`, `--no-prefetch`, `-w, --watch`. Param routes (`/blog/:id`) are auto-skipped because they need runtime data.

`deploy --provider <X>` accepts `symbols`, `cloudflare`, `vercel`, `netlify`, `github-pages`. Auto-creates the provider's config (`wrangler.jsonc`, `vercel.json`, `netlify.toml`, etc.) if missing. `--init` initializes config without deploying.

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
smbls servers                                 List + switch active CLI server (API base URL)
smbls config                                  Configure project settings (interactive or flag-driven)
smbls install                                 Install Symbols
smbls upgrade                                 Upgrade all Symbols deps to latest
smbls completion                              Generate shell completion script
smbls link-packages                           Links all smbls packages into the project
```

`ask` flags: `--provider <claude|openai|gemini|ollama>`, `--model <name>`, `--init` (configure AI/MCP).

`upgrade` flags: `--global-only`, `--local-only`, `--skip-mcp`, `--dry-run`.

---

## Publish flow (most-used scripted path)

The one-shot:

```bash
smbls publish                              # push current project + publish to all enabled envs
smbls publish --env staging                # push + publish only staging
smbls publish --env dev,staging            # CSV (or --env dev --env staging)
smbls publish --no-push                    # skip push; publish an existing version
smbls publish --version <id>               # publish a specific version (implies --no-push)
smbls publish --mode <mode>                # override env mode (latest|published|version|branch)
smbls publish --dry-run                    # print planned operations without executing
```

Per-env mode default: prod-like envs (`prod`, `production`) → `published`; everything else → `latest`. Override with `--mode`.

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
2. **Always pass `-y, --yes`** for any command that has a "Are you sure?" confirmation gate (publish, delete, restore, project create, github connect, integrations purchase). Different flag from `--non-interactive` — this one APPROVES, that one DISABLES prompts.
3. **Pin the channel explicitly** with `SYMBOLS_API_CHANNEL=<name>` env var (or `--local`/`--next`/`--no-next` flag). Don't rely on the `next` default — agents may be running against `production` in deployment.
4. **Authenticate via token, not browser.** Agent flows can't open a browser. Use:
   ```bash
   SYMBOLS_AUTH_TOKEN=<token> smbls <cmd>
   # OR pre-login with:
   smbls login --non-interactive --token <token>
   ```
5. **Always check `--dry-run` first** for destructive ops (publish, delete, restore, env publish). They print the API calls; comparing dry-run output to actual is your safety net.
6. **Use the granular commands when you need branch logic.** `smbls publish` is one shot; if a step fails midway you have to manually unwind. `push` → `versions publish` → `environments publish` lets you retry just the failing leg.

**Recommended agent invocation skeleton:**

```bash
# Set channel + auth once per session
export SYMBOLS_API_CHANNEL=next
export SYMBOLS_AUTH_TOKEN=<from-secret-store>

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
| `Cannot reach API server at <host>:<port>` | `bin/index.js:49-53` (ECONNREFUSED) | Wrong channel or server down. Override with `SYMBOLS_API_URL` or `--next/--no-next` |
| `Authentication required` (`code: 'AUTH_REQUIRED'`) | `helpers/authEnsure.js:272` | Need `smbls login` or `SYMBOLS_AUTH_TOKEN` env var |
| `Missing app key in symbols.json` | `helpers/symbolsConfig.js:29` | Run `smbls init` or hand-write `symbols.json` with `{ owner, key }` |
| `Project ${owner}/${key} not found on server` (with `--non-interactive`) | `bin/publish.js:89-92` | Run `smbls project create` first OR `smbls workspace create-missing` |
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
- Don't pass auth tokens via `--token` flag in shared logs. Use `SYMBOLS_AUTH_TOKEN` env var instead — it doesn't appear in `ps`/process listings.
- Don't use `--no-next` casually. It targets `api.symbols.app` (production), and any push/publish there is real-user-visible. Default to `next` for development.
- Don't rely on the global `smbls` binary version matching the monorepo `@symbo.ls/cli@4.0.0` — they may drift. Use `smbls --version` to check.
- Don't combine `--all` with `--env` on `smbls publish`. `--env` overrides `--all`; the combination silently uses `--env` only.

---

## Cross-references

- Framework + plugin rules: `FRAMEWORK.md`
- Design system + theme contract: `DESIGN_SYSTEM.md`
- Modern smbls stack: `MODERN_STACK.md`
- SDK reference: `SDK.md` (`@symbo.ls/sdk`)
- Channel resolution + plugin source: smbls monorepo (`server/packages/channels/`, `plugins/{router, fetch, polyglot, helmet, brender, frank, mermaid}/`)
- Per-command help: `smbls <command> --help`
- All help in one shot: `smbls --help-all` (commander's `outputHelp({ helpAll: true })` if registered)
