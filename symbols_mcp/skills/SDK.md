# Symbols SDK Reference (`@symbo.ls/sdk`)

Official SDK for the Symbols design platform. Manage projects, collaborate in real-time, handle branches, pull requests, and more.

**Install:** `npm install @symbo.ls/sdk`
**Version:** 3.7.3

---

## Initialization

```javascript
import { SDK } from '@symbo.ls/sdk'

const sdk = new SDK({
  apiUrl: 'https://api.symbols.app',
  socketUrl: 'https://api.symbols.app',
  timeout: 30000,
  retryAttempts: 3,
  debug: false
})

await sdk.initialize({
  authToken: 'your-auth-token',
  appKey: 'your-app-key'
})
```

### SDK Instance Methods
- `sdk.initialize(context)` — initialize all services
- `sdk.getService(name)` — get a service instance
- `sdk.updateContext(context)` — update context for all services
- `sdk.isReady()` — check if SDK is initialized
- `sdk.getStatus()` — get status of all services
- `sdk.destroy()` — cleanup all services and resources

All service methods are also available as direct proxy methods on the SDK instance (e.g., `sdk.login()`, `sdk.getProjects()`).

---

## AuthService

Authentication, user management, and permissions.

### Authentication
- `register(userData, options?)` — register new user
- `login(email, password, options?)` — login with email/password
- `logout()` — logout current user
- `refreshToken(refreshToken)` — refresh auth token
- `googleAuth(idToken, inviteToken?, options?)` — Google OAuth
- `githubAuth(code, inviteToken?, options?)` — GitHub OAuth
- `googleAuthCallback(code, redirectUri, inviteToken?, options?)` — Google OAuth callback
- `requestPasswordReset(email)` — request password reset
- `confirmPasswordReset(token, password)` — confirm password reset
- `confirmRegistration(token)` — confirm registration
- `requestPasswordChange()` — request password change
- `confirmPasswordChange(currentPassword, newPassword, code)` — confirm password change

### User Profile
- `getMe(options?)` — get current user profile
- `getUserProfile()` — get authenticated user's profile
- `updateUserProfile(profileData)` — update user profile
- `getUserProjects()` — get user's projects with icons
- `getUser(userId)` — get user by ID
- `getUserByEmail(email)` — get user by email

### Token & State
- `getAuthToken()` — get current auth token
- `getStoredAuthState()` — get stored auth state
- `isAuthenticated()` — check if authenticated
- `hasValidTokens()` — check if tokens are valid
- `getCurrentUser()` — get current user

### Permissions
- `getMyProjectRole(projectId)` — get role in project (cached)
- `getMyProjectRoleByKey(projectKey)` — get role by project key (cached)
- `clearProjectRoleCache(projectId?)` — clear role cache
- `hasPermission(requiredPermission)` — check global permission
- `hasGlobalPermission(globalRole, requiredPermission)` — check global role permission
- `checkProjectPermission(projectRole, requiredPermission)` — check project permission
- `checkProjectFeature(projectTier, feature)` — check if tier has feature
- `canPerformOperation(projectId, operation, options?)` — check if operation is allowed
- `withPermission(projectId, operation, action)` — execute action with permission check

---

## ProjectService

Project CRUD, members, libraries, versions, and environments.

### Project CRUD
- `createProject(projectData)` — create new project
- `getProjects(params?)` — get projects with pagination
- `listProjects(params?)` — alias for getProjects
- `listPublicProjects(params?)` — get public projects (no auth)
- `getProject(projectId)` — get project by ID
- `getPublicProject(projectId)` — get public project (no auth)
- `getProjectByKey(key)` — get project by key
- `getProjectDataByKey(key, options?)` — get project data by key
- `updateProject(projectId, data)` — update project metadata
- `updateProjectName(projectId, name)` — update project name
- `duplicateProject(projectId, newName, newKey, targetUserId)` — duplicate project
- `removeProject(projectId)` — delete project
- `checkProjectKeyAvailability(key)` — check if key is available

### Project Data
- `updateProjectComponents(projectId, components)` — update components
- `updateProjectSettings(projectId, settings)` — update settings
- `updateProjectPackage(projectId, pkg)` — update package
- `setProjectAccess(projectId, access)` — set access level (account/team/organization/public)
- `setProjectVisibility(projectId, visibility)` — set visibility (public/private/password-protected)

### Members
- `getProjectMembers(projectId)` — get all members
- `inviteMember(projectId, email, role?, options?)` — invite member
- `createMagicInviteLink(projectId, options?)` — create shareable invite link
- `acceptInvite(token)` — accept invitation
- `updateMemberRole(projectId, memberId, role)` — change member role
- `removeMember(projectId, memberId)` — remove member

### Permissions
- `getProjectRolePermissionsConfig(projectId, options?)` — get role-permissions mapping
- `updateProjectRolePermissionsConfig(projectId, rolePermissions, options?)` — update permissions

### Libraries
- `getAvailableLibraries(params?)` — get available libraries
- `getProjectLibraries(projectId)` — get project's libraries
- `addProjectLibraries(projectId, libraryIds)` — add libraries
- `removeProjectLibraries(projectId, libraryIds)` — remove libraries

### Versions & Changes
- `applyProjectChanges(projectId, changes, options?)` — apply changes (creates new version)
- `getProjectData(projectId, options?)` — get current project data for branch
- `getProjectVersions(projectId, options?)` — get version history with pagination
- `restoreProjectVersion(projectId, version, options?)` — restore to previous version

### Environments
- `listEnvironments(projectId, options?)` — list all environments
- `activateMultipleEnvironments(projectId, options?)` — enable multi-environment support
- `upsertEnvironment(projectId, envKey, config, options?)` — create/update environment
- `updateEnvironment(projectId, envKey, updates, options?)` — update environment config
- `publishToEnvironment(projectId, envKey, payload, options?)` — publish to environment
- `deleteEnvironment(projectId, envKey, options?)` — delete environment
- `promoteEnvironment(projectId, fromEnvKey, toEnvKey, options?)` — promote between environments

### Favorites & Recent
- `getFavoriteProjects()` — get favorites
- `addFavoriteProject(projectId)` — add to favorites
- `removeFavoriteProject(projectId)` — remove from favorites
- `getRecentProjects(options?)` — get recently accessed projects

### Item-Level Operations
- `updateProjectItem(projectId, path, value, options?)` — update single item
- `deleteProjectItem(projectId, path, options?)` — delete item
- `setProjectValue(projectId, path, value, options?)` — set value
- `addProjectItems(projectId, items, options?)` — add multiple items
- `getProjectItemByPath(projectId, path, options?)` — get item by path

---

## BranchService

Version control branches.

### Branch Management
- `listBranches(projectId)` — get all branches
- `createBranch(projectId, branchData)` — create branch from source
- `deleteBranch(projectId, branchName)` — delete branch (cannot delete main)
- `renameBranch(projectId, branchName, newName)` — rename branch
- `getBranchChanges(projectId, branchName?, options?)` — get diff for branch
- `mergeBranch(projectId, branchName, mergeData?)` — merge branch (preview or commit)
- `resetBranch(projectId, branchName)` — reset branch to clean state
- `publishVersion(projectId, publishData)` — publish version as live

### Helpers
- `createBranchWithValidation(projectId, name, source?)` — create with validation
- `branchExists(projectId, branchName)` — check if branch exists
- `previewMerge(projectId, sourceBranch, targetBranch?)` — preview merge
- `commitMerge(projectId, sourceBranch, options?)` — commit after preview
- `createFeatureBranch(projectId, featureName)` — create feature branch
- `createHotfixBranch(projectId, hotfixName)` — create hotfix branch
- `getBranchStatus(projectId, branchName)` — get branch status
- `deleteBranchSafely(projectId, branchName, options?)` — delete with safety checks
- `getBranchesWithStatus(projectId)` — get all branches with status
- `validateBranchName(branchName)` — validate branch name
- `sanitizeBranchName(branchName)` — normalize branch name

---

## PullRequestService

Code review and merging.

### Pull Request Operations
- `createPullRequest(projectId, pullRequestData)` — create PR (source, target, title required)
- `listPullRequests(projectId, options?)` — list PRs with filtering/pagination
- `getPullRequest(projectId, prId)` — get PR details
- `reviewPullRequest(projectId, prId, reviewData)` — submit review (approved/requested_changes/feedback)
- `addPullRequestComment(projectId, prId, commentData)` — add comment
- `mergePullRequest(projectId, prId)` — merge approved PR
- `getPullRequestDiff(projectId, prId)` — get PR diff
- `closePullRequest(projectId, prId)` — close without merging
- `reopenPullRequest(projectId, prId)` — reopen closed PR

### Helpers
- `approvePullRequest(projectId, prId, comment?)` — approve PR
- `requestPullRequestChanges(projectId, prId, threads?)` — request changes
- `getOpenPullRequests(projectId, options?)` — filter open PRs
- `getClosedPullRequests(projectId, options?)` — filter closed PRs
- `getMergedPullRequests(projectId, options?)` — filter merged PRs
- `isPullRequestMergeable(projectId, prId)` — check if mergeable
- `getPullRequestStatusSummary(projectId, prId)` — get status overview
- `getPullRequestStats(projectId, options?)` — get PR statistics

---

## CollabService

Real-time collaboration via WebSocket.

- `connect(options?)` — connect to collaborative editing socket

Features:
- Real-time document synchronization via Yjs
- Undo/redo stack management
- Pending operations for offline mode
- Connection recovery
- Presence and cursor tracking

---

## FileService

File uploads and management.

- `uploadFile(file, options?)` — upload file with metadata/tags
- `updateProjectIcon(projectId, iconFile)` — upload project icon
- `uploadFileWithValidation(file, options?)` — upload with size/type validation
- `uploadImage(imageFile, options?)` — upload with image constraints
- `uploadDocument(documentFile, options?)` — upload with document constraints
- `getFileUrl(fileId)` — generate public file URL
- `validateFile(file, options?)` — validate file before upload
- `uploadMultipleFiles(files, options?)` — upload multiple files

---

## DnsService

Custom domain management.

### DNS Records
- `createDnsRecord(domain, options?)` — create DNS record
- `getDnsRecord(domain)` — get DNS record
- `getCustomHost(hostname)` — get custom host info
- `removeDnsRecord(domain)` — delete DNS record

### Project Domains
- `addProjectCustomDomains(projectId, customDomains, options?)` — add custom domains
- `getProjectDomains(projectId)` — get project's custom domains
- `removeProjectCustomDomain(projectId, domain)` — remove custom domain

### Helpers
- `validateDomain(domain)` — validate domain format
- `isDomainAvailable(domain)` — check availability
- `getDomainStatus(domain)` — get domain status
- `verifyDomainOwnership(domain)` — verify ownership

---

## IntegrationService

Third-party integrations and API keys.

- `integrationWhoami(apiKey, options?)` — validate API key
- `listIntegrations(options?)` — list integrations
- `createIntegration(data)` — create integration
- `updateIntegration(integrationId, update)` — update integration
- `createIntegrationApiKey(integrationId, data?)` — create API key
- `listIntegrationApiKeys(integrationId)` — list API keys
- `revokeIntegrationApiKey(integrationId, keyId)` — revoke API key

---

## FeatureFlagService

Feature flag management.

### User
- `getFeatureFlags(params?)` — get flags for current user
- `getFeatureFlag(key)` — get single flag

### Admin
- `getAdminFeatureFlags(params?)` — get all flags
- `createFeatureFlag(flagData)` — create flag
- `updateFeatureFlag(id, patch)` — update flag
- `archiveFeatureFlag(id)` — delete flag

Flag format:
```javascript
{
  flags: {
    "flag_key": {
      enabled: boolean,
      variant: string | null,
      payload: any
    }
  }
}
```

---

## MetricsService

Contribution statistics.

- `getContributions(options?)` — get contribution heat-map stats
  - Options: `projectId`, `userId`, `from`, `to`

---

## ScreenshotService

Screenshot and thumbnail management.

### Project-Level
- `createScreenshotProject(payload)` — create screenshot project
- `getProjectScreenshots(projectKey, params?)` — get screenshots
- `reprocessProjectScreenshots(projectKey, body?)` — reprocess screenshots
- `recreateProjectScreenshots(projectKey, body?)` — recreate all
- `deleteProjectScreenshots(projectKey)` — delete all

### Thumbnails
- `getThumbnailCandidate(projectKey, options?)` — get best candidate
- `updateProjectThumbnail(projectKey, body?)` — update thumbnail
- `refreshThumbnail(projectKey, options?)` — debounced refresh (15s)

### Individual
- `getPageScreenshot(screenshotId, format?)` — get page screenshot
- `getComponentScreenshot(screenshotId, format?)` — get component screenshot
- `getScreenshotByKey(projectKey, type, key, format?)` — get by key
- `getQueueStatistics()` — get queue stats

---

## TrackingService

Analytics via Grafana Faro.

- `configureTracking(options?)` — configure tracking
- `setUser(user, options?)` — set tracking user
- `setGlobalAttributes(attrs)` — set global attributes
- `trackEvent(name, attributes?)` — track custom event
- `trackPageView(name, attributes?)` — track page view
- `trackError(error, context?)` — track error

---

## BaseService (Foundation)

All services extend BaseService:

- `init(context)` — initialize service
- `updateContext(context)` — update context
- `getStatus()` — get service status
- `isReady()` — check if ready
- `destroy()` — cleanup

HTTP features:
- Automatic token management (refresh before expiration)
- Storage: localStorage, sessionStorage, or memory
- FormData support for uploads
- Error tracking integration

Methods that don't require auth: `register`, `login`, `googleAuth`, `githubAuth`, `requestPasswordReset`, `confirmPasswordReset`, `confirmRegistration`, `listPublicProjects`, `getPublicProject`.

---

## Usage Examples

### Authenticate and list projects
```javascript
import { SDK } from '@symbo.ls/sdk'

const sdk = new SDK({ apiUrl: 'https://api.symbols.app' })
await sdk.initialize({})

const result = await sdk.login('user@example.com', 'password')
const projects = await sdk.getProjects()
```

### Create a project and add a library
```javascript
const project = await sdk.createProject({
  name: 'My App',
  key: 'pr_myapp',
  visibility: 'private'
})

const libs = await sdk.getAvailableLibraries()
await sdk.addProjectLibraries(project.data._id, [libs.data[0]._id])
```

### Branch workflow
```javascript
await sdk.createFeatureBranch(projectId, 'new-header')
// ... make changes ...
const preview = await sdk.previewMerge(projectId, 'feature/new-header')
await sdk.commitMerge(projectId, 'feature/new-header')
```

### Pull request workflow
```javascript
const pr = await sdk.createPullRequest(projectId, {
  source: 'feature/new-header',
  target: 'main',
  title: 'Add new header component'
})

await sdk.approvePullRequest(projectId, pr.data._id, 'Looks good!')
await sdk.mergePullRequest(projectId, pr.data._id)
```

### File upload
```javascript
const file = new File(['content'], 'design.png', { type: 'image/png' })
const result = await sdk.uploadImage(file, {
  tags: ['design', 'header'],
  visibility: 'project'
})
const url = sdk.getFileUrl(result.data._id)
```

### CLI access via `smbls sdk`
```bash
smbls sdk --list                              # List all methods
smbls sdk --list --service auth               # Filter by service
smbls sdk getProjects                         # Call method
smbls sdk getProjectByKey '{"key":"myapp"}'   # Call with JSON args
```
