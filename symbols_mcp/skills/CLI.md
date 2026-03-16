# Symbols CLI Reference (`@symbo.ls/cli`)

The `smbls` command-line interface for the Symbols design platform.

**Install:** `npm install -g @symbo.ls/cli`
**Version:** 3.7.5
**Global command:** `smbls`

---

## Project Setup

### `smbls init [dest]`
Initialize or add Symbols to a project.
- `--non-interactive` — disable prompts (requires flags)
- `--name <name>` — project name
- `--location <location>` — where to init: root or subfolder
- `--v2-action <action>` — v2 project action: migrate, root, or subfolder
- `-y, --yes` — skip confirmation prompts

Auto-detects v2 projects and offers migration path.

### `smbls create [dir]`
Create and scaffold a new project.
- `--workspace` — scaffold only symbols source files (no full repo, dir: ".")
- `--create-new` — force create new platform project
- `--link-existing` — force link to existing platform project
- `--local-only` — local-only (no platform)
- `--non-interactive` — disable prompts (requires flags)
- `--project-name <name>` — platform project name
- `--type <projectType>` — platform projectType
- `--key <projectKey>` — platform project key
- `--id <projectId>` — platform project id (for link mode)
- `--visibility <visibility>` — platform visibility (default: private)
- `--language <language>` — platform language (default: javascript)
- `--branch <branch>` — local branch (default: main)
- `--template <gitUrl>` — override template git repo URL
- `--package-manager <manager>` — npm or yarn (default: npm)
- `--no-dependencies` — skip installing dependencies
- `--no-clone` — create folder instead of cloning from git
- `--blank-shared-libraries` — create project with blank shared libraries
- `--domql` — use DOMQL template (default: true)
- `--remote` — clone feature/remote branch (default: true)
- `--clean-from-git` — remove starter-kit git repository (default: true)
- `-v, --verbose` — verbose output

### `smbls install`
Install Symbols into an existing project.
- `-d, --dev` — run against local server
- `-f, --fetch` — fetch config after install (default: true)
- `--framework <framework>` — framework: domql or react
- `-v, --verbose` — verbose output

### `smbls eject`
Eject from `@symbo.ls/runner` to explicit bundler dependencies.
- `--no-install` — skip npm install after ejecting

Updates package.json, removes @symbo.ls/runner, adds bundler deps, expands .parcelrc for parcel.

---

## Development

### `smbls start [entry]`
Start development server.
- `-p, --port <port>` — port to use (default from symbols.json or 1234)
- `--no-cache` — disable build cache
- `--open` — open browser on start
- `--bundler <bundler>` — force bundler: parcel, vite, or browser

Supports pass-through args to underlying bundler. Auto-selects free port if specified port is busy. Browser mode injects importmap and globals script.

### `smbls build [entry]`
Build project for production.
- `--no-cache` — disable build cache
- `--no-optimize` — disable optimization
- `--no-brender` — skip brender pre-rendering
- `--out-dir <dir>` — output directory (default from symbols.json or dist)
- `--bundler <bundler>` — force bundler: parcel, vite, or browser

### `smbls brender [entry]`
Pre-render static pages to HTML using server-side rendering.
- `--out-dir <dir>` — output directory (default: brenderDistDir from symbols.json, or dist-brender)
- `--no-isr` — disable ISR (skip client SPA bundle)
- `--no-prefetch` — disable SSR data prefetching
- `-w, --watch` — watch for changes and re-render

Output: `dist-brender/` with static HTML, metadata, CSS, optional client bundle.

### `smbls deploy`
Deploy project to hosting providers.
- `--provider <provider>` — deploy target: symbols, cloudflare, vercel, netlify, github-pages
- `--init` — initialize deployment config without deploying
- `--out-dir <dir>` — output directory for build
- `--bundler <bundler>` — force bundler: parcel, vite, or browser

Creates provider-specific config files (wrangler.jsonc, vercel.json, netlify.toml, GitHub Actions workflow).

---

## Sync & Configuration

### `smbls fetch`
Pull design system and project config from the Symbols platform.
- `-d, --dev` — run against local server
- `-v, --verbose` — verbose output
- `--convert` — convert fetched config (default: true)
- `--schema` — include schema (default: false)
- `--force` — force override local changes
- `--update` — override local changes from platform
- `-y, --yes` — skip confirmation prompts
- `--dist-dir <dir>` — directory to import files to
- `--skip-confirm` — skip confirmation for local changes
- `--non-interactive` — disable interactive prompts

Includes git-based or mtime heuristic detection of local changes.

### `smbls sync`
Bidirectional sync with remote server (two-way merge with conflict resolution).
- `-b, --branch <branch>` — branch to sync
- `-m, --message <message>` — commit message
- `-d, --dev` — run against local server
- `-v, --verbose` — verbose output
- `--mode <mode>` — sync mode: merge, remote, local, cancel
- `--conflict-resolution <mode>` — conflict resolution: local or remote
- `--non-interactive` — disable interactive prompts
- `-y, --yes` — skip confirmation prompts

Uses 3-way merge: local, remote, and base comparison.

### `smbls push`
Push local changes to the Symbols platform.
- `-m, --message <message>` — commit message
- `-v, --verbose` — verbose output
- `-d, --dev` — run against local server
- `--non-interactive` — disable interactive prompts
- `-y, --yes` — skip confirmation prompts

Shows diffs before confirmation.

### `smbls publish`
Build and publish project to preview environments.
- `--env <envs...>` — environments to publish to (development, staging, production)
- `--all` — publish to all environments
- `--non-interactive` — disable prompts (requires --env or --all)
- `-v, --verbose` — verbose output

Preview URLs are auto-generated for each environment.

### `smbls config`
Interactively configure Symbols project settings.
- `--non-interactive` — disable prompts
- `--dist-dir <dir>` — set distribution directory
- `--owner <owner>` — Symbols username
- `--key <key>` — project key
- `--branch <branch>` — default branch
- `--version <version>` — version
- `--dir <dir>` — Symbols source directory
- `--runtime <runtime>` — environment: node, bun, deno, browser
- `--bundler <bundler>` — build tool: parcel, vite, turbopack, webpack, rollup
- `--package-manager <pm>` — npm, yarn, pnpm, bun
- `--api-base-url <url>` — API base URL
- `--deploy <target>` — deploy target: symbols, cloudflare, vercel, netlify, github-pages

Updates `symbols.json` and `.symbols_local/config.json`.

---

## Collaboration & Authentication

### `smbls login`
Sign in to Symbols. Opens browser for OAuth/auth flow, stores credentials in `~/.smblsrc`.

### `smbls signup`
Create a new Symbols account.

### `smbls logout`
Sign out of Symbols (clears local credentials).

### `smbls collab`
Connect to real-time collaboration socket and live-sync changes.
- `-b, --branch <branch>` — branch to collaborate on
- `--no-sync-first` — skip initial sync (not recommended)
- `-l, --live` — enable live collaboration mode (default: false)
- `-d, --debounce-ms <ms>` — local changes debounce (default: 200ms)
- `-v, --verbose` — verbose output

---

## Project Management

### `smbls project <subcommand>`
Project lifecycle management with subcommands:

| Subcommand | Description |
|---|---|
| `create` | Create a new project |
| `link` | Link local project to platform |
| `delete` | Delete a project |
| `update` | Update project metadata |
| `list` | List projects |
| `duplicate` | Duplicate a project |
| `restore` | Restore a project |
| `libs` | Library management (add, remove, list, available) |
| `members` | Members management (add, remove, list, invite, role, acceptInvite, inviteLink) |
| `versions` | Versions management (create, get, list, latest, publish, snapshot, update) |
| `environments` | Environments management (list, activate, publish, upsert, update, delete) |
| `pipeline` | Pipeline management (promote) |

---

## File Management

### `smbls files <subcommand>`
Upload, download, and manage project files.

| Subcommand | Description | Key Options |
|---|---|---|
| `list` | List project-linked files | `--remote`, `--uploads`, `--limit <n>`, `--search <q>` |
| `upload <paths...>` | Upload files to project | `--key`, `--visibility`, `--tags`, `--metadata`, `--mime`, `--overwrite` |
| `download` | Download a file | `--key`, `--out <path>`, `--remote` |
| `rm` | Remove file from project | `--key`, `--local-only`, `--force-remote` |

---

## AI Assistant

### `smbls ask [question...]`
Chat with AI about your Symbols project.
- `--provider <provider>` — AI provider: claude, openai, gemini, ollama, symbols
- `--model <model>` — model name
- `--init` — configure AI settings and MCP

**Supported providers and models:**
| Provider | Models |
|---|---|
| Claude | claude-sonnet-4-6, claude-opus-4-6, claude-haiku-4-5-20251001 |
| OpenAI | gpt-4o, gpt-4o-mini, o3-mini |
| Gemini | gemini-2.5-pro, gemini-2.5-flash |
| Ollama | llama3.3, codellama, mistral, deepseek-coder-v2 (local) |

Config stored in `~/.smblsrc`. Environment variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`.

---

## Utilities

### `smbls convert [src] [dest]`
Convert DOMQL components to other frameworks.
- `--react` — convert to React
- `--angular` — convert to Angular
- `--vue2` — convert to Vue 2
- `--vue3` — convert to Vue 3
- `-o, --only <components>` — only convert specific components (comma-separated)
- `-m, --merge <dir>` — recursive merge files into dest
- `-v, --verbose` — verbose mode

### `smbls migrate`
Migrate a v2 Symbols project to v3.
- `--yes` — skip confirmation
- `--non-interactive` — disable all prompts

Renames `.symbols/` to `.symbols_local/`, `smbls/` to `symbols/`, creates missing `symbols/app.js`, rewrites `symbols/index.js` to v3 format.

### `smbls validate [target]`
Validate DOMQL syntax in source files.
- Uses esbuild to check JS/TS/JSX/TSX syntax
- Reports violations, warnings, and compliance scores

### `smbls clean`
Clean Symbols temporary files.

### `smbls sdk [method] [args...]`
Proxy SDK service methods from the terminal.
- `-l, --list` — list all available SDK methods
- `-s, --service <name>` — filter methods by service name

```bash
smbls sdk --list                              # List all methods
smbls sdk --list --service auth               # Filter by service
smbls sdk getProjects                         # Call method
smbls sdk getProjectByKey '{"key":"myapp"}'   # Call with arguments
```

### `smbls link-packages`
Link all smbls packages into the project.
- `-c, --capture` — capture and write all package names
- `-j, --join` — join all links into one command (default: true)

### `smbls servers`
List and switch CLI servers (API base URLs).
- `-s, --select` — interactively select active server

### `smbls completion [shell]`
Generate shell completion script.
- `--install` — print install instructions

### `smbls github <subcommand>`
GitHub integration helpers.
- `connect` — connect GitHub repository
- `initActions` — initialize GitHub Actions workflow
- `sync` — sync with GitHub

---

## Configuration Files

### `symbols.json` (project root)
Main project configuration:
- `owner` — Symbols username
- `key` — project identifier
- `dir` — symbols source directory
- `branch` — git branch (default: main)
- `entry` — bundler entry point
- `port` — dev server port
- `distDir` — build output directory
- `brenderDistDir` — brender output directory
- `brender` — enable pre-rendering
- `runtime` — node, bun, deno, or browser
- `bundler` — parcel, vite, etc.
- `packageManager` — npm, yarn, pnpm, bun
- `libraries` / `librariesDir` — shared library config
- `designSystem` — design system with buckets

### `.symbols_local/config.json` (local)
Local machine configuration:
- `owner` — local username
- `branch` — active branch
- `projectKey` — linked project key
- `projectId` — platform project ID
- `apiBaseUrl` — API endpoint

### `~/.smblsrc` (global)
Global credentials and AI configuration.

---

## Common Workflows

### New project from scratch
```bash
smbls create my-app
cd my-app
smbls start
```

### Add Symbols to existing project
```bash
cd existing-project
smbls init
smbls install
smbls start
```

### Fetch, edit, push cycle
```bash
smbls fetch          # pull latest from platform
# ... edit components ...
smbls push -m "updated header"
```

### Deploy to production
```bash
smbls build
smbls deploy --provider cloudflare
# or
smbls publish --env production
```

### Migrate v2 to v3
```bash
smbls migrate --yes
smbls start
```
