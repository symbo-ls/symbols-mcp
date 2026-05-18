# @symbo.ls/mcp

## 3.14.101

## 3.14.100

## 3.14.35

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.34

### Patch Changes

- Manual patch bump triggered via workflow_dispatch (scope: all).
  No source change behind this bump — released to refresh dist or
  coordinate a cross-package version line.

## 3.14.33

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.32

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.31

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.30

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.29

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.28

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.27

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.26

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.25

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.24

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.23

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.22

### Patch Changes

- d8b899b: Bump `@symbo.ls/mcp` to drive the cross-bump + PyPI/MCP-registry publish
  through end-to-end. Previous run's PyPI step skipped because the secrets
  were missing in Infisical; secrets are configured now, so this round
  catches PyPI + the MCP registry up to the npm version line.

## 3.14.21

### Patch Changes

- d8b899b: Bump `@symbo.ls/mcp` to drive the cross-bump + PyPI/MCP-registry publish
  through end-to-end. Previous run's PyPI step skipped because the secrets
  were missing in Infisical; secrets are configured now, so this round
  catches PyPI + the MCP registry up to the npm version line.

## 3.14.20

### Patch Changes

- d8b899b: Bump `@symbo.ls/mcp` to drive the cross-bump + PyPI/MCP-registry publish
  through end-to-end. Previous run's PyPI step skipped because the secrets
  were missing in Infisical; secrets are configured now, so this round
  catches PyPI + the MCP registry up to the npm version line.

## 3.14.19

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.18

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.17

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.16

### Patch Changes

- Manual patch bump triggered via workflow_dispatch (scope: @symbo.ls).
  No source change behind this bump — released to refresh dist or
  coordinate a cross-package version line.

## 3.14.15

### Patch Changes

- Manual patch bump triggered via workflow_dispatch (scope: @symbo.ls).
  No source change behind this bump — released to refresh dist or
  coordinate a cross-package version line.

## 3.14.14

### Patch Changes

- Manual patch bump triggered via workflow_dispatch (scope: @symbo.ls).
  No source change behind this bump — released to refresh dist or
  coordinate a cross-package version line.

## 3.14.13

### Patch Changes

- Manual patch bump triggered via workflow_dispatch (scope: @symbo.ls).
  No source change behind this bump — released to refresh dist or
  coordinate a cross-package version line.

## 3.14.12

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.11

### Patch Changes

- Manual patch bump triggered via workflow_dispatch (scope: @symbo.ls).
  No source change behind this bump — released to refresh dist or
  coordinate a cross-package version line.

## 3.14.10

### Patch Changes

- Manual patch bump triggered via workflow_dispatch (scope: @symbo.ls).
  No source change behind this bump — released to refresh dist or
  coordinate a cross-package version line.

## 3.14.9

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.8

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.7

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.6

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.5

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.4

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.3

### Patch Changes

- Auto-generated cross-repo patch release.

## 3.14.2

### Patch Changes

- Auto-generated cross-repo patch release.

---

## PyPI-only releases (pre-unification, 2026-05-11 → 2026-05-12)

Backfilled. These four versions shipped only to PyPI + the MCP registry
via the local `publish.sh` flow, before the release-manager wired the
three-registry publish (after which npm + PyPI + MCP registry all ship
on the same unified `3.14.x` version line — so 1.1.x is closed forever).

### 1.1.10 (2026-05-12)

- Bundle the full `@symbo.ls/frank-audit` rule catalog (64 rules,
  FA001–FA904) so agents reading `get_project_rules` see brief docs for
  every rule, not just the ~24 with hand-written context in
  `FRANKABILITY.md`.
- `bin/sync-frankability-catalog` regenerates `FRANKABILITY_CATALOG.md`
  from `frank-audit explain`, grouped by FA0xx / FA1xx / … / FA9xx
  category.
- `publish.sh` runs the sync before each release so the bundled
  catalog tracks whatever `frank-audit` currently ships.
- `get_project_rules` now concatenates `FRANKABILITY_CATALOG.md`
  alongside the conceptual `FRANKABILITY.md`.

### 1.1.9 (2026-05-12)

- Suppress the noisy `mcp.server.lowlevel` ERROR triggered when stdin
  receives a whitespace-only line (terminal Enter, buggy clients).
  Per the stdio spec clients MUST NOT send blank lines, but the
  resulting pydantic traceback drowns out real errors. Only the
  specific blank-line case is dropped — actual parse errors still
  surface.

### 1.1.8 (2026-05-12)

- Catch `KeyboardInterrupt` in `main()` so `Ctrl-C` on `uvx
symbols-mcp` exits cleanly instead of dumping a 40-line asyncio
  traceback ending in `raise KeyboardInterrupt()`.

### 1.1.7 (2026-05-11)

- Banner on stderr at server startup so `uvx symbols-mcp` no longer
  looks hung in a terminal.
- Drop npm entry from MCP-registry `server.json` (npm package is
  private; registry can only validate public package entries).
