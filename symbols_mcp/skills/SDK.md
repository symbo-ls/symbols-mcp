# SDK_FOR_MCP — `@symbo.ls/sdk` v3.14.0

Authoritative reference for any MCP server, automation agent, or programmatic
consumer that drives `@symbo.ls/sdk`. Lists every public method on every
service, the SDK lifecycle, the auth/token model, the environment matrix, the
event bus, and the validation surface.

> Source of truth: source files under `src/`. When this file disagrees with the
> code, the code wins — open a PR to update this doc.

---

## Quick reference

- **Package**: `@symbo.ls/sdk` (v3.14.0)
- **Entry**: `src/index.js` exports `SDK` (default) + factory functions per service + `environment`
- **Subpath exports**: `@symbo.ls/sdk/environment`, `@symbo.ls/sdk/utils/services` (plus `createCrossAppAuth` from the main entry)
- **Backends**: HTTP via `${apiUrl}/core/*`, WebSocket via `socketUrl`, Workspace data via `${apiUrl}/workspace/*`
- **Auth**: JWT bearer token managed by `TokenManager` (singleton, auto-refresh)
- **Event bus**: `sdk.rootBus` (global cross-service pub/sub with last-payload replay)
- **Total services**: 24 general-purpose services documented in full below (see [Service map](#service-map)), plus ~30+ additional domain-model services (tickets, docs, AI chat, commerce/catalog, scheduling, party/directory, workspace records — see "Additional domain services" at the end of the service map) registered the same way but not individually cataloged in this file. `src/services/index.js` is the authoritative full list.
- **Total proxied SDK methods**: 250+ across all services (full list in `src/utils/services.js`)

---

## Initialization

```js
import { SDK } from '@symbo.ls/sdk'

const sdk = new SDK({
  apiUrl: 'https://next.api.symbols.app',  // optional; defaults to environment.apiUrl
  socketUrl: 'https://next.api.symbols.app',
  timeout: 30000,
  debug: false,                             // toggles logger output
  useNewServices: true,                     // default; selects modern service implementations
  tracking: { enabled: false }              // see Tracking
})

await sdk.initialize({
  authToken: '<JWT>',     // optional — TokenManager seeds itself if present
  appKey: '<APP_KEY>',    // optional — used for app-level identity
  state: rootState        // required if you intend to call collab.connect()
})
```

`initialize()` instantiates and warms up every registered service (24
general-purpose + the additional domain services, 50+ total) in parallel via
`Promise.all`. Every service shares the same `_context` reference, so
`sdk.updateContext({...})` propagates instantly.

### SDK instance methods

| Method | Description |
| --- | --- |
| `getService(name)` | Returns the named service (`'auth'`, `'project'`, …). Throws if unknown. |
| `updateContext(ctx)` | Merges new keys into context for every service (does **not** persist `authToken` — `TokenManager` owns it). |
| `isReady()` | `true` once every initialized service reports ready. |
| `getStatus()` | `{ ready, services: [{ name, ready, error, context }], context }` |
| `destroy()` | Tears down every service and clears the singleton TokenManager. |

### Direct service access (no `getService`)

Every method registered in `src/utils/services.js` is mounted as a proxy on the
SDK instance. These three calls are equivalent:

```js
sdk.getService('project').getProject(id)
sdk.project.getProject(id)               // not provided — see note
sdk.getProject(id)                        // proxy method
```

The proxy is built by `_createServiceProxies()` and dispatches to whichever
service registered the method name in `SERVICE_METHODS`. **Note**: only the
proxy form is supported — `sdk.<serviceName>` is not exposed as a property,
always use `sdk.getService(name)` or the proxy method.

---

## Service map

| Service name | Class | File | Endpoint root |
| --- | --- | --- | --- |
| `auth` | `AuthService` | `services/AuthService.js` | `/core/auth/*` |
| `boot` | `BootService` | `services/BootService.js` | `/core/boot` |
| `collab` | `CollabService` | `services/CollabService.js` | WebSocket |
| `project` | `ProjectService` | `services/ProjectService.js` | `/core/projects/*` |
| `plan` | `PlanService` | `services/PlanService.js` | `/core/plans/*` |
| `subscription` | `SubscriptionService` | `services/SubscriptionService.js` | `/core/subscriptions/*` |
| `file` | `FileService` | `services/FileService.js` | `/core/files/*` |
| `payment` | `PaymentService` | `services/PaymentService.js` | `/core/payments/*` |
| `dns` | `DnsService` | `services/DnsService.js` | `/core/dns/*` (+ `dnsWorkerUrl`) |
| `branch` | `BranchService` | `services/BranchService.js` | `/core/projects/:id/branches/*` |
| `pullRequest` | `PullRequestService` | `services/PullRequestService.js` | `/core/projects/:id/pull-requests/*` |
| `admin` | `AdminService` | `services/AdminService.js` | `/core/admin/*` |
| `screenshot` | `ScreenshotService` | `services/ScreenshotService.js` | `/core/screenshots/*` |
| `tracking` | `TrackingService` | `services/TrackingService.js` | Grafana Faro (no API) |
| `waitlist` | `WaitlistService` | `services/WaitlistService.js` | `/core/waitlist/*` |
| `metrics` | `MetricsService` | `services/MetricsService.js` | `/core/metrics/*` |
| `integration` | `IntegrationService` | `services/IntegrationService.js` | `/core/integrations/*` |
| `featureFlag` | `FeatureFlagService` | `services/FeatureFlagService.js` | `/core/feature-flags/*`, `/core/admin/feature-flags/*` |
| `organization` | `OrganizationService` | `services/OrganizationService.js` | `/core/orgs/*` |
| `workspace` | `WorkspaceService` | `services/WorkspaceService.js` | `/core/workspaces/*` |
| `workspaceData` | `WorkspaceDataService` | `services/WorkspaceDataService.js` | `${apiUrl}/workspace/*` (typed) |
| `kv` | `KvService` | `services/KvService.js` | `kvUrl` (cloudflare worker) |
| `allocationRule` | `AllocationRuleService` | `services/AllocationRuleService.js` | `/core/allocation-rules/*` |
| `sharedAsset` | `SharedAssetService` | `services/SharedAssetService.js` | `/core/shared-assets/*` |
| `credits` | `CreditsService` | `services/CreditsService.js` | `/core/credits/*` |
| `storefront` | `StorefrontService` | `services/StorefrontService.js` | `/core/storefront/:workspaceId/*` |

### Additional domain services (not individually cataloged below)

Registered and proxied the same way as everything above, added as the platform's Mongo-native workspace data model grew: AI chat/assistant (`aiChat`, `ai`), documents (`doc`), tickets (`ticket`), analyzed logs (`analyzed`), resource links (`resourceLink`), canvas layouts (`canvasLayout`), builds (`builds`), meetings (`meet`), calendar (`calendar`), workspace-project data (`workspaceProject`), and the broader workspace record model — proposed actions, workflows, field definitions, record collections, party/directory (party, interaction, segment), commerce (product, price, company profile, agreements, invoices, transactions), cross-entity capabilities (comments, attachments, watchers, activity entries, tags), and scheduling (bookings, availability rules, conversations, recurrences). Each follows the same `BaseService` contract (tenant-scope defaulting, `_call`/`_request`, envelope handling) documented above. For the authoritative method-by-method list, read the service's own file under `src/services/` — each is a thin, well-commented HTTP wrapper around a `/core/*` route family, following the exact same patterns as the services documented in full below.

---

## BaseService contract

Every service extends `BaseService` (`src/services/BaseService.js`).

- `init({ context })` — wires up `_apiUrl` from `context.apiUrl` (or
  `environment.apiUrl`) and creates/seeds the singleton `TokenManager`. Sets
  `_ready = true`. Override only to add subclass init steps.
- `updateContext(ctx)` — mutates `_context` in place to keep references shared.
- `isReady()` / `getStatus()` — readiness signals.
- `_request(endpoint, { method, body, headers, methodName })` — low-level
  fetch helper. Always prefixes with `${apiUrl}/core`. Auto-injects bearer
  auth when `_requiresInit(methodName)` is true (i.e. method is **not** in the
  no-auth allow-list: `register`, `login`, `googleAuth`, `googleAuthCallback`,
  `githubAuth`, `requestPasswordReset`, `confirmPasswordReset`,
  `confirmRegistration`, `verifyEmail`, `getPlans`, `getPlan`,
  `listPublicProjects`, `getPublicProject`).
- `_call(methodName, endpoint, opts)` — envelope-aware wrapper. Server is
  expected to return `{ success, data, message }`; returns `data` on success,
  throws `Error(message)` on failure. Tolerates bare payloads too.
- `_createSubdomainRecords(name)` — registers `<name>.symbo.ls` +
  `*.<name>.symbo.ls` against the cloudflare DNS worker.
- `destroy()` — tears down `TokenManager` and flips ready off.

Errors are auto-tracked through `TrackingService` via `_trackServiceError()`
when tracking is enabled (the tracking service itself is excluded to avoid
loops).

### Tenant-scope defaulting

Every workspace/org-scoped service resolves its implicit scope the same way
via two shared `BaseService` helpers (hoisted from several hand-rolled,
subtly-drifted per-service versions):

- `_resolveWorkspaceId(explicit, { fallbackToStorage })` — explicit arg wins,
  then the live SDK context (`_context.activeWorkspaceId`, kept fresh by
  `sdk.switchOrg` / `sdk.switchWorkspace`), then — only when opted in — a
  persisted storage fallback (`sessionStorage` first for per-tab scoping,
  `localStorage` as the shared last-default) for callers that may run before
  context is seeded. Returns `undefined` (or storage's own `null`) when
  nothing resolves, so the caller can omit the param and the request just
  won't carry a workspace filter.
- `_resolveScope(explicit)` — resolves the `{ orgId, workspaceId }` PAIR a
  call should carry: each key defaults independently — explicit per-key value
  wins, otherwise `_context.activeOrgId` / `_context.activeWorkspaceId`. No
  storage fallback (context is expected to be live by call time).

Individual services (`TicketService`, `AiChatService`, etc.) keep their own
thin, purpose-named wrapper around these for call-site readability and
back-compat — the defaulting logic itself lives once in `BaseService`.

---

## Auth & TokenManager

`TokenManager` (`src/utils/TokenManager.js`) is a process singleton via
`getTokenManager(options)`.

- **Storage**: `localStorage` (browser default), `sessionStorage`, or
  `memory` (Node, tests). Auto-falls back to `memory` when storage throws
  (opaque origins, sandbox).
- **Refresh**: refreshes the access token `refreshBuffer` ms before expiry
  (default 60 s). Calls `${apiUrl}/auth/refresh` with the refresh token.
- **Storage keys**: prefixed `symbols_` (`symbols_access_token`,
  `symbols_refresh_token`, `symbols_expires_at`, `symbols_expires_in`).
- **Callbacks**: `onTokenRefresh(tokens)`, `onTokenExpired()`,
  `onTokenError(err)`.

```js
import { getTokenManager, createTokenManager } from '@symbo.ls/sdk'

const tm = getTokenManager({
  storageType: 'localStorage',
  refreshBuffer: 60_000,
  apiUrl: '/api',
  onTokenRefresh: ({ accessToken }) => { /* … */ },
  onTokenExpired: () => { /* redirect to login */ }
})

tm.getAccessToken()      // raw JWT or null
tm.getAuthHeader()       // 'Bearer <jwt>' or null
await tm.ensureValidToken()
```

Every authenticated SDK call goes through `BaseService._request()`, which
calls `tm.ensureValidToken()` before each request. **Do not** stash auth
tokens in SDK context — `TokenManager` is the source of truth.

---

## Environment

`src/config/environment.js` exports a singleton `environment` object resolved
at module load. Channel URLs (`apiUrl`, `socketUrl`) come from
`@symbo.ls/channels`; everything else is per-env in `CONFIG`.

| Env name | Channel | Notes |
| --- | --- | --- |
| `local` | `local` | `http://localhost:8080`, beta features on, tracking off |
| `development` | `development` | `https://api.dev.symbols.app` |
| `next` | `next` | `https://next.api.symbols.app` (default channel) |
| `test` | `test` | `https://test.api.symbols.app` (alias `testing`) |
| `upcoming` | `upcoming` | `https://api.upcoming.symbols.app` |
| `staging` | `staging` | `https://api.staging.symbols.app` |
| `preview` | `preview` | `https://api.symbols.app` (Faro tracking enabled) |
| `production` | `production` | `https://api.symbols.app` (Faro tracking enabled) |

Resolved by `process.env.NODE_ENV`. Override
URLs with `SYMBOLS_APP_API_URL` / `SYMBOLS_APP_SOCKET_URL`. Other env-var
escape hatches: `SYMBOLS_APP_GITHUB_CLIENT_ID`, `SYMBOLS_APP_GRAFANA_URL`,
`SYMBOLS_KV_URL`, `SYMBOLS_DNS_WORKER_URL`, `SYMBOLS_DNS_API_KEY`,
`TYPESENSE_*`.

```js
import environment from '@symbo.ls/sdk/environment'
// or: import { environment } from '@symbo.ls/sdk'

environment.apiUrl
environment.socketUrl
environment.channel
environment.features    // { trackingEnabled, betaFeatures, newUserOnboarding }
environment.googleClientId
environment.githubClientId
environment.kvUrl
environment.dnsWorkerUrl
environment.grafanaUrl
environment.isProduction / .isDevelopment / .isTest / .isStaging / .isPreview
```

---

## Root event bus

`sdk.rootBus` (also exportable via `src/state/rootEventBus.js`) is a global
singleton (`globalThis.__SMBLS_ROOT_BUS__`) with **last-payload replay** —
late subscribers immediately receive the most recently emitted payload for
each event.

```js
sdk.rootBus.on('checkpoint:done', ({ version, origin }) => { /* … */ })
sdk.rootBus.on('clients:updated', clients => { /* … */ })
sdk.rootBus.on('bundle:done', ({ project, ticket }) => { /* … */ })
sdk.rootBus.on('bundle:error', ({ project, ticket, error }) => { /* … */ })

sdk.rootBus.off(event, handler)
sdk.rootBus.emit(event, payload)
```

Currently emitted by `CollabService` (`checkpoint:done` auto + manual,
`clients:updated`, `bundle:done`, `bundle:error`).

---

# Service surface

All async methods unless noted. `[no-auth]` marks public endpoints. Helper
methods that wrap a primary call (validation wrappers, paged list helpers)
are listed under each service.

## auth — `AuthService`

### Authentication

- `register(userData, options)` `[no-auth]`
- `login(email, password, options)` `[no-auth]`
- `logout()`
- `refreshToken(refreshToken)`
- `googleAuth(idToken, inviteToken?, options)` `[no-auth]`
- `googleAuthCallback(code, redirectUri, inviteToken?, options)` `[no-auth]`
- `githubAuth(code, inviteToken?, options)` `[no-auth]`
- `exchangeNativeAuthToken(xt, state, inviteToken?)` — redeems a native-shell (e.g. a Tauri-wrapped iOS/desktop build) OAuth deep-link exchange token for a normal session. `state` must be the same nonce the shell generated for the authorize request — the server binds the token to it at mint time. Single-use, short TTL (≤60s): replay, expiry, or a nonce mismatch answers 401. Wires the session the same way `googleAuth` does (`response.data.tokens` → `TokenManager.setTokens`). Rethrows with `error.status` preserved so shell UI can feature-detect route availability (404 = server predates the flow).
- `requestPasswordReset(email)` `[no-auth]`
- `confirmPasswordReset(token, password)` `[no-auth]`
- `confirmRegistration(token)` `[no-auth]`
- `requestPasswordChange()`
- `confirmPasswordChange(currentPassword, newPassword, code)`
- `resendVerification()`
- `verifyEmail(token)` `[no-auth]`

### Identity & profile

- `getMe(options)`
- `getStoredAuthState()`
- `getAuthToken()` *(sync)*
- `isAuthenticated()` *(sync)*
- `hasValidTokens()` *(sync)*
- `getCurrentUser()`
- `getTokenDebugInfo()` *(sync)*
- `getUserProfile()`
- `updateUserProfile(profileData)`
- `getUser(userId)`
- `getUserByEmail(email)`
- `getUserProjects()`

### Cross-org reads (NEEDED_FOR_INTRANET)

- `getMyOrgNotifications()` — fails-soft to `{counts:{}}`
- `getMyFreebusy({ from, to })` — ISO 8601 window
- `getMyProjects()` — every project across every org
- `getMyTeams()` — direct fetch (avoids stale free-tier claims)
- `getMyOrgMemberships()` — workspace-switcher source
- `getOrgMemberRoles(orgId)` — People-page role enrichment

### Project roles (cached)

- `getMyProjectRole(projectId)`
- `getMyProjectRoleByKey(keyOrSpec)`
- `getProjectRoleWithFallback(projectId, userProjects?)`
- `getProjectRoleByKeyWithFallback(projectKey, userProjects?)`
- `clearProjectRoleCache(projectId?)` *(sync)*

### Permissions

Sync helpers backed by `src/utils/permission.js`:

- `hasPermission(requiredPermission)`
- `hasGlobalPermission(globalRole, requiredPermission)`
- `checkProjectPermission(projectRole, requiredPermission)`
- `checkProjectFeature(projectTier, feature)` — returns the tier-limit (e.g. `5` for `aiCopilot:5`)
- `canPerformOperation(projectId, operation, options)`
- `withPermission(projectId, operation, action)`

Constants exported via `src/utils/permission.js`: `PERMISSION_MAP`,
`ROLE_PERMISSIONS`, `PROJECT_ROLE_PERMISSIONS`, `TIER_FEATURES`.

### Validation wrappers

- `registerWithValidation(userData, options)`
- `loginWithValidation(email, password, options)`
- `validateRegistrationData(userData)` *(sync)*

### Plugin session passthrough

- `setPluginSession(session)` *(sync)*

---

## boot — `BootService`

Single-round-trip composite boot read — `GET /core/boot`. Collapses the
workspace shell's multi-wave boot sequence (`getMe` → `getOrganization` +
`listWorkspaces` + `getWorkspace` → members + prefs) into one call.

- `boot({ workspaceId? })` — `workspaceId` is an optional explicit scope pin
  (useful for a multi-tab shell where the tab's chosen workspace should win
  over the caller's stored active workspace). Omit it to use the normal
  resolution order every other workspace-scoped route already uses: explicit
  param → auth claim → the user's stored active workspace.

  Returns `{ data, errors }`. Each section of `data` (`me`, `org`,
  `workspaces`, `workspace`, `members`, `prefs`) is byte-equivalent to what
  calling that section's own individual endpoint would return — never
  reshaped. A failed/rejected section resolves to `data.<section> = null` +
  `errors.<section> = <message>` rather than failing the whole call, so a
  boot with one flaky section still returns everything else. `data.workspaceProject`
  is always `null` (see `errors.workspaceProject`) — resolving + validating a
  workspace's installed module is a client-side pipeline, not a single
  reusable core service, so it isn't folded into this composite.

---

## collab — `CollabService`

Real-time collaboration over Socket.IO + Yjs. Requires `context.state` (root
state tree) before `connect()`.

**`CollabClient` (yjs + lib0, ~360 KB dev) is lazy-loaded**, not bundled into
the service eagerly — it's dynamically `import()`-ed on the first `connect()`
call, keeping collab out of a consumer's initial bundle if collab is never
used. The import promise is cached (repeated `connect()` calls reuse the same
loaded module); a failed import clears the cache so a later retry can
succeed instead of the failure being permanent.

### Connection

- `connect({ projectId, branch?, authToken?, pro? })`
- `disconnect()`
- `isConnected()`
- `getConnectionInfo()`
- `toggleLive(flag)`

### Data mutations

- `updateData(tuples, options)`
- `addItem(type, data, opts)`
- `addMultipleItems(items, opts)`
- `updateItem(type, data, opts)`
- `deleteItem(type, key, opts)`

Each mutation form pushes through Yjs and broadcasts to all connected peers.

### Undo / redo

- `undo()` / `redo()`
- `canUndo()` / `canRedo()`
- `getUndoStackSize()` / `getRedoStackSize()`
- `clearUndoHistory()`

### Versioning

- `checkpoint()` — emits `rootBus` `checkpoint:done` `{ version, origin: 'manual' }`

### Presence

- `sendCursor(data)`
- `sendPresence(data)`

### Accessors

- `collab.ydoc` — underlying Yjs document
- `collab.socket` — underlying Socket.IO client

### Emitted events (rootBus)

| Event | Payload |
| --- | --- |
| `checkpoint:done` | `{ version, origin: 'auto' \| 'manual' }` |
| `clients:updated` | `Array<{ id, name, … }>` |
| `bundle:done` | `{ project, ticket }` |
| `bundle:error` | `{ project, ticket, error }` |

---

## project — `ProjectService`

### CRUD

- `createProject(projectData)`
- `getProjects(params)` / `listProjects(params)` (alias)
- `listPublicProjects(params)` `[no-auth]`
- `getProject(projectId)`
- `getPublicProject(projectId)` `[no-auth]`
- `getProjectByKey(keyOrSpec)`
- `getProjectDataByKey(keyOrSpec, options)`
- `getPublicProjectDataByKey(keyOrSpec, { envKey })`
- `resolveAppkey(appkey)`
- `updateProject(projectId, data)`
- `updateProjectComponents(projectId, components)`
- `updateProjectSettings(projectId, settings)`
- `updateProjectName(projectId, name)`
- `updateProjectPackage(projectId, pkg)`
- `duplicateProject(projectId, newName, newKey, targetUserId?)`
- `removeProject(projectId)`
- `transferProjectOwnership(projectId, { targetType, userId, organizationId })`
- `transferProjectToWorkspace(projectId, targetWorkspaceId)`
- `checkProjectKeyAvailability(key)`

### Granular reads

- `getProjectComponents(projectId)`
- `getProjectFunctions(projectId)`
- `getProjectPages(projectId)`
- `getProjectComponentsByKey(projectKey)`
- `getProjectFunctionsByKey(projectKey)`
- `getProjectPagesByKey(projectKey)`

### Access control

- `setProjectSourceAccess(projectId, sourceAccess)` — values from `PROJECT_SOURCE_ACCESS`: `public | org | workspace | restricted`
- `setProjectAccess(projectId, access)` — `account | team | organization | public`
- `setProjectVisibility(projectId, visibility)` — `public | private | password-protected`

### Role permissions config

- `getProjectRolePermissionsConfig(projectId, options)`
- `updateProjectRolePermissionsConfig(projectId, rolePermissions, options)`

### Members & invites

- `getProjectMembers(projectId)`
- `inviteMember(projectId, email, role='guest', options)`
- `createMagicInviteLink(projectId, options)`
- `acceptInvite(token)`
- `updateMemberRole(projectId, memberId, role)`
- `removeMember(projectId, memberId)`

### Libraries

- `getAvailableLibraries(params)`
- `getProjectLibraries(projectId)`
- `addProjectLibraries(projectId, libraryIds)`
- `removeProjectLibraries(projectId, libraryIds)`

### Versioning / data store

- `applyProjectChanges(projectId, changes, options)` — `changes` = tuples like `[['update', ['components', 'Button'], { color: 'blue' }], ['delete', ['pages', 'old']]]`. `options.message`, `options.type` (`patch` default).
- `getProjectData(projectId, options)`
- `getProjectVersions(projectId, options)`
- `restoreProjectVersion(projectId, version, options)`
- `updateProjectItem(projectId, path, value, options)`
- `deleteProjectItem(projectId, path, options)`
- `setProjectValue(projectId, path, value, options)`
- `addProjectItems(projectId, items, options)`
- `getProjectItemByPath(projectId, path, options)`

### Environments

- `listEnvironments(projectId, options)`
- `upsertEnvironment(projectId, envKey, config, options)`
- `updateEnvironment(projectId, envKey, updates, options)`
- `publishToEnvironment(projectId, envKey, payload, options)`
- `deleteEnvironment(projectId, envKey, options)`
- `promoteEnvironment(projectId, fromEnvKey, toEnvKey, options)`

### Favorites & recents

- `getFavoriteProjects()`
- `addFavoriteProject(projectId)`
- `removeFavoriteProject(projectId)`
- `getRecentProjects(options)`

### Admin: project ownership

- `listProjectOwnership(params)`
- `assignProjectOwner(args)`
- `autoAssignProjectOwners(args)`

---

## branch — `BranchService`

### Core

- `listBranches(projectId)`
- `createBranch(projectId, branchData)`
- `deleteBranch(projectId, branchName)`
- `renameBranch(projectId, branchName, newName)`
- `getBranchChanges(projectId, branchName='main', options)`
- `mergeBranch(projectId, branchName, mergeData)`
- `resetBranch(projectId, branchName)`
- `publishVersion(projectId, publishData)`

### Helpers

- `createBranchWithValidation(projectId, name, source='main')`
- `branchExists(projectId, branchName)`
- `previewMerge(projectId, sourceBranch, targetBranch='main')`
- `commitMerge(projectId, sourceBranch, options)`
- `createFeatureBranch(projectId, featureName)` → `feature/<name>`
- `createHotfixBranch(projectId, hotfixName)` → `hotfix/<name>`
- `getBranchStatus(projectId, branchName)`
- `deleteBranchSafely(projectId, branchName, options)`
- `getBranchesWithStatus(projectId)`
- `validateBranchName(branchName)` *(sync)*
- `sanitizeBranchName(branchName)` *(sync)*

---

## pullRequest — `PullRequestService`

- `createPullRequest(projectId, pullRequestData)`
- `listPullRequests(projectId, options)`
- `getPullRequest(projectId, prId)`
- `reviewPullRequest(projectId, prId, reviewData)`
- `addPullRequestComment(projectId, prId, commentData)`
- `mergePullRequest(projectId, prId)`
- `getPullRequestDiff(projectId, prId)`
- `closePullRequest(projectId, prId)`
- `reopenPullRequest(projectId, prId)`

### Helpers

- `createPullRequestWithValidation(projectId, data)`
- `approvePullRequest(projectId, prId, comment)`
- `requestPullRequestChanges(projectId, prId, threads)`
- `getOpenPullRequests(projectId, options)`
- `getClosedPullRequests(projectId, options)`
- `getMergedPullRequests(projectId, options)`
- `isPullRequestMergeable(projectId, prId)`
- `getPullRequestStatusSummary(projectId, prId)`
- `getPullRequestStats(projectId, options)`

---

## file — `FileService`

- `uploadFile(file, options)`
- `uploadFileWithValidation(file, options)`
- `uploadImage(imageFile, options)`
- `uploadDocument(documentFile, options)`
- `uploadMultipleFiles(files, options)`
- `uploadProjectFile(file, options)`
- `uploadMultipleProjectFiles(files, options)`
- `uploadMarketplaceThumbnail(thumbnailFile, { itemId, kind })`
- `updateProjectIcon(projectId, iconFile)`
- `getFile(fileId)`
- `updateFile(fileId, updates)`
- `deleteFile(fileId)`
- `listMyUploads({ page, limit, sortBy, sortOrder })`
- `getFileUrl(fileId)` *(sync)*
- `validateFile(file, options)` *(sync)*
- `createFileFormData(file, metadata)` *(sync)*

---

## payment — `PaymentService`

- `checkout(options)` — Stripe checkout session
- `checkoutWithValidation(options)`
- `checkoutForPlan(projectId, planKey, options)`
- `checkoutForTeam(projectId, seats, options)`
- `getSubscriptionStatus(projectId)`
- `getSubscriptionStatusWithValidation(projectId)`
- `hasActiveSubscription(projectId)`
- `getSubscriptionDetails(projectId)`
- `getSubscriptionSummary(projectId)`

> Prefer `subscription.*` for new code. Payment service is retained for the
> legacy Stripe-checkout entry points.

---

## plan — `PlanService`

### Public `[no-auth]`

- `getPlans()`
- `getPlan(planId)`
- `getPlansWithPricing()`
- `getPlanByKey(key)`
- `getActivePlans()`
- `getPlansByPriceRange(minPrice=0, maxPrice=Infinity)`

### Admin

- `getAdminPlans()`
- `createPlan(planData)`
- `updatePlan(planId, planData)`
- `deletePlan(planId)`
- `initializePlans()`

### Validation wrappers

- `getPlansWithValidation()`
- `getPlanWithValidation(planId)`
- `createPlanWithValidation(planData)`
- `updatePlanWithValidation(planId, planData)`

---

## subscription — `SubscriptionService`

- `createSubscription(subscriptionData)`
- `getProjectStatus(projectId)`
- `getUsage(subscriptionId)`
- `cancelSubscription(subscriptionId)`
- `listInvoices(subscriptionId, options)`
- `getInvoicesWithPagination(subscriptionId, options)`
- `getPortalUrl(subscriptionId, returnUrl)`
- `hasActiveSubscription(projectId)`
- `isSubscriptionActive(subscriptionId)`
- `getProjectSubscription(projectId)`
- `getProjectUsage(projectId)`
- `getSubscriptionLimits(subscriptionId)`
- `getPricingOptions(subscriptionId)`
- `changeSubscription(changeData)` / `changeSubscriptionWithValidation(changeData)`
- `downgrade(downgradeData)` / `downgradeWithValidation(downgradeData)`
- `createSubscriptionWithValidation(subscriptionData)`
- `canAccessProjectFeature(projectId, featureKey)`
- `grantProjectFeature(projectId, featureKey)`
- `revokeProjectFeature(projectId, featureKey)`

---

## dns — `DnsService`

- `createDnsRecord(domain, options)`
- `getDnsRecord(domain)`
- `getCustomHost(hostname)`
- `removeDnsRecord(domain)`
- `addProjectCustomDomains(projectId, customDomains, options)`

### Validation wrappers

- `createDnsRecordWithValidation(domain, options)`
- `getDnsRecordWithValidation(domain)`
- `removeDnsRecordWithValidation(domain)`
- `addProjectCustomDomainsWithValidation(projectId, customDomains, options)`

### Domain ops

- `isDomainAvailable(domain)`
- `getDomainStatus(domain)`
- `verifyDomainOwnership(domain)`
- `getProjectDomains(projectId)`
- `removeProjectCustomDomain(projectId, domain)`

### Sync helpers

- `validateDomain(domain)`
- `formatDomain(domain)`
- `extractDomainFromUrl(url)`

---

## admin — `AdminService`

- `getAdminUsers(params)`
- `searchAdminUsers(searchQuery, options)`
- `getAdminUsersByEmails(emails, options)`
- `getAdminUsersByIds(ids, options)`
- `updateUser(userId, userData)`
- `updateUserWithValidation(userId, userData)`
- `validateUserData(userData)` *(sync)*
- `bulkUpdateUsers(userUpdates)`
- `getUsersByRole(role, options)`
- `getUsersByStatus(status, options)`
- `activateUser(userId)` / `deactivateUser(userId)` / `suspendUser(userId)`
- `promoteToAdmin(userId)` / `demoteFromAdmin(userId)`
- `assignProjectsToUser(userId, options)`
- `assignSpecificProjectsToUser(userId, projectIds, role='guest')`
- `assignAllProjectsToUser(userId, role='guest')`
- `getUserStats()`
- `getRateLimitStats()`
- `getProjectKeyStats()`

---

## screenshot — `ScreenshotService`

- `createScreenshotProject(payload)`
- `getProjectScreenshots(projectKey, params)`
- `reprocessProjectScreenshots(projectKey, body)`
- `recreateProjectScreenshots(projectKey, body)`
- `refreshForEnvironment(projectKey, environment='production', extra)`
- `deleteProjectScreenshots(projectKey)`
- `getThumbnailCandidate(projectKey, options)`
- `updateProjectThumbnail(projectKey, body)`
- `refreshThumbnail(projectKey, options)`
- `getPageScreenshot(screenshotId, format='json')`
- `getComponentScreenshot(screenshotId, format='json')`
- `getScreenshotByKey(projectKey, type, key, format='json')`
- `getQueueStatistics()`

---

## tracking — `TrackingService` (Grafana Faro)

Tracking is **disabled by default**, on localhost, and when `grafanaUrl` is
empty (preview/production only). Enable per-caller:

```js
new SDK({
  tracking: {
    enabled: true,
    url: 'https://faro-collector-prod-…',
    appName: 'Symbols Platform',
    environment: 'production',
    appVersion: '1.0.0',
    sessionTracking: true,
    enableTracing: true,
    globalAttributes: { region: 'us-east-1' }
  }
})
```

### Async

- `init({ context, options })` *(called by SDK)*
- `_loadFaroClient(runtimeConfig)` *(internal)*
- `_resolveInstrumentations({ … })` *(internal)*

### Sync — events

- `trackEvent(name, attributes, options)`
- `trackError(error, options)`
- `captureException(error, options)`
- `trackMeasurement(type, values, options)`
- `trackView(name, attributes)`

### Sync — logging & breadcrumbs

- `logMessage(message, level='info', context?)`
- `logDebug(message, context)`
- `logInfo(message, context)`
- `logWarning(message, context)` / `logWarn(...)`
- `logError(message, context)` / `logErrorMessage(...)`
- `addBreadcrumb(message, attributes)`

### Sync — user / session

- `setUser(user, options)` / `clearUser()`
- `setSession(session, options)` / `clearSession()`

### Sync — global attributes & runtime

- `setGlobalAttributes(attributes)` / `setGlobalAttribute(key, value)` / `removeGlobalAttribute(key)`
- `flushQueue()`
- `getClient()`
- `isEnabled()` / `isInitialized()`
- `configureTracking(trackingOptions)`
- `destroy()`

---

## waitlist — `WaitlistService`

- `joinWaitlist(data)` `[no-auth]`
- `listWaitlistEntries(options)` *(admin)*
- `updateWaitlistEntry(id, update)` *(admin)*
- `inviteWaitlistEntry(id)` *(admin)*

---

## metrics — `MetricsService`

- `getContributions(options)` — heat-map stats
- `getProjectUsage(projectId)`

---

## integration — `IntegrationService`

### Integrations

- `integrationWhoami(apiKey, options)`
- `listIntegrations(options)`
- `createIntegration(data)`
- `updateIntegration(integrationId, update)`

### API Keys

- `createIntegrationApiKey(integrationId, data)`
- `listIntegrationApiKeys(integrationId)`
- `revokeIntegrationApiKey(integrationId, keyId)`

### Webhooks

- `createIntegrationWebhook(integrationId, data)`
- `listIntegrationWebhooks(integrationId)`
- `updateIntegrationWebhook(integrationId, webhookId, update)`
- `deleteIntegrationWebhook(integrationId, webhookId)`
- `listIntegrationWebhookDeliveries(integrationId, webhookId, options)`
- `replayIntegrationWebhookDelivery(integrationId, webhookId, deliveryId)`

### GitHub Connectors

- `listGitHubConnectors(integrationId)`
- `createGitHubConnector(integrationId, data)`
- `updateGitHubConnector(integrationId, connectorId, update)`
- `deleteGitHubConnector(integrationId, connectorId)`
- `getGitHubRepo({ owner, repo })`
- `listGitHubRepos({ orgId })`
- `syncGitHubIntegration({ orgId, slug='default', scopeType='org', scopeId=null })`

### Org-integration CRUD + scoping (`/org-integrations/*`)

An org can install a given integration `kind` at multiple scopes (the org
itself, or a narrower `scopeType`/`scopeId` — e.g. per-workspace); these
methods manage that scoped-config layer, distinct from the raw `Integration`
CRUD above.

- `listOrgIntegrations({ orgId, scopeType?, scopeId?, includeParents? })`
- `upsertOrgIntegration({ orgId, kind, ... })`
- `deleteOrgIntegration({ orgId, kind, slug?, scopeType?, scopeId? })`
- `assignOrgIntegrationScope({ orgId, kind, ... })`
- `reorderOrgIntegrations({ orgId, kind, ... })`
- `listOrgIntegrationKinds()`

### Capability invocation

`callOrgIntegrationCapability` is the per-kind data-plane call — invoking a
specific capability an installed integration kind's catalogue declares
(e.g. "send message", "create issue"), as opposed to the CRUD methods above
which only manage the integration's own config.

- `callOrgIntegrationCapability({ orgId, capability, args?, workspaceId?, idOrSlug?, kind?, slug?, scopeType?, scopeId? })`
  — `capability` is required and must be one of the kind's catalogue
  `capabilities`. Identify the target integration either by `idOrSlug` (with
  `kind` required alongside it) or by `kind` + optional `slug` +
  `scopeType`/`scopeId`.

### Marketplace integrations (`/marketplace/integrations/*`)

Distinct from the org-integration CRUD above — this is the
entitlement/install layer for **paid marketplace kinds**, gated by
`WorkspaceMarketplaceEntitlement` records server-side (installing a paid kind
without an active entitlement is rejected). Server-side: listing/checking is
open to any org member; install/uninstall require owner/admin.

- `listMarketplaceEntitlements(workspaceId, { status? })`
- `checkMarketplaceEntitlement({ workspaceId, kind })`
- `installMarketplaceIntegration({ orgId, workspaceId, kind, ... })` — free
  kinds install directly; paid kinds require an active entitlement
- `uninstallMarketplaceIntegration({ orgId, workspaceId, kind, ... })`

---

## featureFlag — `FeatureFlagService`

User-facing reads + admin CRUD. Full recipes (kill switch, allowlist,
percentage rollout, A/B variants) live in the `@symbo.ls/sdk` source repo at `src/docs/FeatureFlags.md`.

### User

- `getFeatureFlags(params)` — `params.keys?: string[]`
- `getFeatureFlag(key)` — `{ key, enabled, variant, payload }`

### Admin (admin/owner)

- `getAdminFeatureFlags(params)` — `params.includeArchived?: boolean`
- `createFeatureFlag(flagData)`
- `updateFeatureFlag(id, patch)`
- `archiveFeatureFlag(id)`

---

## organization — `OrganizationService`

### Org CRUD

- `createOrganization({ name, slug })`
- `listOrganizations()`
- `getOrganization(orgId)`
- `updateOrganization(orgId, updates)`
- `transferOrgOwnership(orgId, { userId })`
- `deleteOrganization(orgId)`
- `ensureOrgStripeCustomer(orgId)`

### Org members

- `listOrgMembers(orgId)`
- `addOrgMember(orgId, { userId, role='member' })`
- `updateOrgMember(orgId, memberId, { role })`
- `removeOrgMember(orgId, memberId)`
- `getMemberEffectiveRole(orgId, memberId)`

### Teams

- `createTeam(orgId, { name, slug, parentTeam })`
- `listTeams(orgId)`
- `updateTeam(orgId, teamId, updates)`
- `deleteTeam(orgId, teamId)`

### Team members

- `listTeamMembers(orgId, teamId)`
- `addTeamMember(orgId, teamId, { userId, role='member' })`
- `updateTeamMember(orgId, teamId, teamMemberId, { role })`
- `removeTeamMember(orgId, teamId, teamMemberId)`

### Invitations

- `createOrgInvitation(orgId, { email, role='member', teams })`
- `listOrgInvitations(orgId)`
- `revokeOrgInvitation(orgId, inviteId)`
- `acceptOrgInvitation({ token })`
- `listTeamInvitations(orgId, teamId)`
- `createTeamInvitation(orgId, teamId, { email, recipientName })`
- `revokeTeamInvitation(orgId, teamId, inviteId)`
- `acceptTeamInvitation({ token })`

### Project permissions

- `getOrgProjectPermissions(orgId)`
- `updateOrgProjectPermissions(orgId, permissions)`

### Team-to-project access

- `listTeamAccess(orgId, teamId)`
- `grantTeamAccess(orgId, teamId, { projectId, role='editor' })`
- `updateTeamAccess(orgId, teamId, accessId, { role })`
- `revokeTeamAccess(orgId, teamId, accessId)`

### Team-to-workspace access

- `listTeamWorkspaceAccess(orgId, teamId)`
- `grantTeamWorkspaceAccess(orgId, teamId, { workspaceId, role='guest' })`
- `updateTeamWorkspaceAccess(orgId, teamId, accessId, { role })`
- `revokeTeamWorkspaceAccess(orgId, teamId, accessId)`

### Roles

- `listOrgRoles(orgId)`
- `createOrgRole(orgId, role)`
- `updateOrgRole(orgId, roleKey, updates)`
- `deleteOrgRole(orgId, roleKey)`

### Billing & credit pool

- `listOrgPayments(orgId)`
- `getCreditPool(orgId)` / `updateCreditPool(orgId, pooledCredits)`

### SSO / SCIM

- `getSso(orgId)` / `updateSso(orgId, sso)`
- `getScim(orgId)` / `updateScim(orgId, { enabled, rotateToken })`

### Org-scoped projects

- `createOrgProject(orgId, projectData)`

### Admin overrides

- `adminListOrganizations(params)`
- `adminListAllTeams(orgId)`
- `adminOverrideTeam(orgId, teamId)`

---

## workspace — `WorkspaceService`

Workspace-org CRUD (`/core/workspaces`). Distinct from `workspaceData`.

- `createWorkspace({ organization, displayName, slug })`
- `listWorkspaces({ organization, page, limit })`
- `getWorkspace(workspaceId)`
- `updateWorkspace(workspaceId, updates)`
- `deleteWorkspace(workspaceId)`

### Members

- `listWorkspaceMembers(workspaceId)`
- `addWorkspaceMember(workspaceId, { userId, role='editor' })`
- `updateWorkspaceMemberRole(workspaceId, userId, { role })`
- `removeWorkspaceMember(workspaceId, userId)`

### Team grants

- `grantWorkspaceTeamAccess(workspaceId, { teamId, role='guest' })`
- `revokeWorkspaceTeamAccess(workspaceId, teamId)`

### Billing / credits

- `getBilling(workspaceId)`
- `getCreditBalance(workspaceId)`
- `getCreditLedger(workspaceId, { limit, before, reason })`
- `getSpendControls(workspaceId)`
- `updateSpendControls(workspaceId, controls)`

### Permissions / projects

- `getWorkspacePermissions(workspaceId)`
- `createWorkspaceProject(workspaceId, projectData)`

### Invitations

- `listWorkspaceInvitations(workspaceId)`
- `createWorkspaceInvitation(workspaceId, { email, role='editor', recipientName })`
- `revokeWorkspaceInvitation(workspaceId, inviteId)`
- `acceptWorkspaceInvitation({ token })`

Allowed role values come from `src/constants/roles.js`:

- `WORKSPACE_MEMBER_ROLES` = `['owner','admin','editor','viewer','guest']`
- `TEAM_GRANT_ROLES` = `['admin','editor','guest','viewer']` (no `owner`)

---

## workspaceData — `WorkspaceDataService`

Typed surface against `${apiUrl}/workspace/*` (the `@symbo.ls/server-workspace`
wrapper). **Auth model is different from other services** — calls go through
`_resolveAuthHeader()` which prefers `context.workspaceTokenProvider()` (an
async fn returning `{ token }` | string) and falls back to the SDK
`TokenManager`. The wrapper resolves the caller's workspace scope from Mongo
via the token's `sub` claim.

All methods are exposed as **namespaced sync getters** that return promises
when invoked (not registered on the SDK proxy):

```js
const ws = sdk.getService('workspaceData')

await ws.tickets.list(filter, options)
await ws.tickets.get(number)
await ws.tickets.create(payload)
await ws.tickets.update(number, payload)
await ws.tickets.remove(number)
await ws.tickets.epicCounts()
await ws.tickets.assign(id, assigneeEmail)

await ws.chat.listChannels()
await ws.chat.createChannel(payload)
await ws.chat.listMessages(channelId)
await ws.chat.sendMessage(channelId, payload)
await ws.chat.listMembers(channelId)

await ws.calendar.listEvents(filter)
await ws.calendar.createEvent(payload)
await ws.calendar.updateEvent(id, payload)
await ws.calendar.deleteEvent(id)
await ws.calendar.sync(params)

await ws.meet.listRooms()
await ws.meet.createRoom(payload)
await ws.meet.getRoom(id)
await ws.meet.listMembers(id)
await ws.meet.listTranscripts(id)
await ws.meet.waitingRoom()
await ws.meet.issueToken(params)

await ws.documents.list()
await ws.documents.create(payload)
await ws.documents.get(id)
await ws.documents.update(id, payload)
await ws.documents.listKb()
await ws.documents.listResourceLinks()
await ws.documents.addResourceLink(payload)

await ws.presence.online()
await ws.presence.heartbeat()

await ws.notifications.list()
await ws.notifications.unreadCount()
await ws.notifications.markRead(id)
await ws.notifications.markAllRead()

await ws.search(q, opts)

await ws.permissions.me()
await ws.permissions.check(action, resource)

await ws.system.status()
await ws.system.featureFlags()

await ws.people.list()
await ws.people.get(id)
await ws.people.me()

await ws.activity.listNotes()
await ws.activity.addNote(payload)
await ws.activity.scoringConfig()

await ws.query(body)   // generic escape hatch
```

---

## kv — `KvService`

Cloudflare KV worker proxy. URL from `environment.kvUrl`.

- `get(key, { env='production' })`
- `put(key, value, { env='production', expirationTtl, metadata })`
- `delete(key, { env='production' })`
- `list({ env='production', prefix, limit, cursor })`

---

## allocationRule — `AllocationRuleService`

Org-level credit-allocation rules.

- `listRules(orgId)`
- `getRule(ruleId)`
- `createRule({ organizationId, workspaceId, policy, monthlyAllocation, priority })`
- `updateRule(ruleId, patch)`
- `deleteRule(ruleId)`

---

## sharedAsset — `SharedAssetService`

Cross-workspace shared assets.

- `createAsset(body)`
- `listAssets(query)`
- `getAsset(id)`
- `updateAsset(id, patch)`
- `deleteAsset(id)`

---

## credits — `CreditsService`

Project-scoped credit ledger + Stripe top-ups.

- `getRates()`
- `getProjectBalance(projectId)`
- `getProjectLedger(projectId, { limit, cursor, reason })`
- `getProjectSpendControls(projectId)`
- `updateProjectSpendControls(projectId, controls)`
- `topupProjectCredits(projectId, { packs=1, returnUrl })`

---

## storefront — `StorefrontService`

Wraps the main server's **public, unauthenticated** `/core/storefront/:workspaceId/*`
routes — a public storefront/catalog read API for workspaces running an
e-commerce or marketplace surface. Unlike every other workspace-scoped
service, there is no membership/session identity on the catalog-read methods
by design: the storefront serves anonymous visitors, so those calls never
attach an `Authorization` header. Every read is server-side allowlisted and
business-rule-filtered (published items only, cost/internal fields stripped,
computed availability) — this service is a thin HTTP wrapper, it does not
re-implement any of that filtering client-side.

### Catalog (public, unauthenticated)

- `listStorefrontProducts(workspaceId, { category, limit, page })`
- `getStorefrontProduct(workspaceId, id)`
- `listStorefrontCollection(workspaceId, collection, { limit, page })`
- `listStorefrontJobs(workspaceId, { limit, page })`
- `getStorefrontJob(workspaceId, id)`
- `applyToStorefrontJob(workspaceId, id, { fullName, email, phone, coverLetter, cvUrl })`

### Storefront customer identity (also public/unauthenticated — this IS the anonymous-visitor-becomes-a-customer surface)

- `registerStorefrontCustomer(workspaceId, { phone, email, fullName, password, birthDate, identificationNumber })`
- `loginStorefrontCustomer(workspaceId, { email, phone, identifier, password })`
- `requestStorefrontCustomerOtp(workspaceId, { phone, email, purpose })`
- `verifyStorefrontCustomerOtp(workspaceId, { phone, email, code, purpose })`
- `resetStorefrontCustomerPassword(workspaceId, { phone, email, code, newPassword })`

### Storefront customer session (authenticated — but with a DIFFERENT identity plane)

- `getStorefrontCustomerMe(workspaceId, customerToken)` — the one
  authenticated method on this service. `customerToken` is the token
  returned by `loginStorefrontCustomer`, a storefront-customer session that
  is completely separate from the SDK's own signed-in-platform-user session.
  It is passed explicitly and attached as a one-off header — it does **not**
  go through the shared `TokenManager`, so it never rides along on other SDK
  calls for the signed-in platform user (or vice versa).

---

# Validation surface

`src/validations/index.js` exposes a generic registry:

```js
import { validate, validators } from '@symbo.ls/sdk'

validate('component', componentData)   // accepts singular or plural
validate('pages', pagesData)

validators.components / validators.pages / validators.functions
validators.files / validators.dependencies
```

Each validator class lives in `src/validations/{component,page,function,file,dependencies}.js`
and exposes `validateAll()` returning `{ isValid, errors }`. `BaseValidator`
in `src/validations/base.js` is the shared parent.

---

# MCP integration notes

When exposing this SDK through an MCP server:

1. **Single SDK instance per session.** `TokenManager` is a process
   singleton; sharing the SDK keeps the auth state aligned across tools.
2. **Pass `apiUrl` explicitly** if the MCP runs in an environment where
   `process.env.NODE_ENV` isn't set — otherwise the SDK falls back to
   the `next` channel.
3. **Never persist `authToken` outside `TokenManager`.** Use
   `sdk.updateContext({ authToken })` once at session start; `BaseService`
   seeds the singleton from context on init.
4. **Tracking off by default** — leave it disabled unless your MCP host has a
   working Faro endpoint and CORS-allowed origin.
5. **`workspaceData` requires the Symbols SDK token.** If your MCP calls
   those tools, supply `context.workspaceTokenProvider` returning
   `{ token }` — workspace scope is resolved server-side from Mongo.
6. **For long-running tools, listen to `rootBus`** for `bundle:done`,
   `bundle:error`, `checkpoint:done`, `clients:updated` to surface async
   collab state without polling.
7. **Methods marked `[no-auth]`** can be called before `sdk.initialize` or
   without a token — useful for marketplace browsing, plan listings, public
   project reads.
8. **Read `src/utils/services.js`** for the canonical map of which proxy
   method belongs to which service. That file is the source of truth for
   discovery.
