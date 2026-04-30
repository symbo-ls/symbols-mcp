# Frank-fix workflow — agent reference card

Audience: any agent (Claude Code, Cursor, custom MCP client) consuming `@symbo.ls/frank-audit` prescriptions through Symbols MCP. This is the contract you follow when fixing Symbols-project findings the mechanical fixer can't or won't auto-apply.

frank-audit detects, fixes, and verifies. It already mechanically resolves high-confidence findings. Your role is medium/low-confidence cases plus structural rules without auto-fix. The fixer verifies every op against `frank.toJSON` and rolls back regressions automatically — your job is to emit good ops, not to verify them.

---

## The agent loop

```
1. audit_and_fix_frankability(symbols_dir, mode='safe-fix')
   → mechanical fixes applied first; shrinks the prescription surface

2. prescribe_frankability_fixes(symbols_dir)
   → returns prescriptions for everything safe-fix didn't handle

3. For each prescription:
     a. inspect rx.proposedOps — IF non-null, the rule already produced
        ready-to-apply ops (palette similarity, spacing-scale mapping,
        polyglot key generation, kebab→camelCase componentName, etc.).
        Submit verbatim, OR modify if you have reason.
     b. IF rx.proposedOps is null OR you reject the suggestion, construct
        ops yourself from the 12-kind contract using rx.sourceContext +
        rx.relatedFiles + rx.explanation.

4. apply_frankability_edit_ops(symbols_dir, { ops: [...] })
   → validates, snapshots, applies, runs frank.toJSON, rolls back on regression
   → returns structured per-op error details for retries

5. Inspect result.skipped — each skip has details.code with retry hints.

6. Repeat 2–5 until prescriptions stop shrinking.
```

---

## Tools you have

| Tool | When to call |
|---|---|
| `audit_and_fix_frankability(dir, mode)` | Always first. `mode` ∈ `report` (read-only) / `safe-fix` (mechanical) / `full` (mechanical + sampling). |
| `prescribe_frankability_fixes(dir)` | After safe-fix. Returns the residue with `proposedOps`. |
| `apply_frankability_edit_ops(dir, ops_json)` | Apply your batch. Always verify-or-rollback. |
| `verify_frankability(dir)` | Standalone bundleability check. Use to confirm a baseline before/after. |
| `rollback_frankability(dir, op_id)` | Manually undo a specific past op. |
| `snapshots_frankability(dir)` | List opIds available for rollback. |
| `frankability_log(dir, limit=50)` | Tail audit log — see what was applied / rolled back recently. |
| `explain_frankability_rule(rule_id)` | Get docs for an unfamiliar rule (FA001–FA902). |

---

## Top-level response shape

`prescribe_frankability_fixes` returns:

```json
{
  "schema": "frank-audit/1.0",
  "opId": "rx-...",
  "startedAt": "...",
  "completedAt": "...",
  "cwd": "/abs/path/symbols",
  "projectMeta": {
    "spacing": {
      "base": 16,
      "cfg": { "base": 16, "ratio": 1.618, "range": [-5, 15], "subSequence": true },
      "scalePx": { "V": 1.44, "Z": 9.89, "A1": 11.93, "A2": 13.96, "A": 16, "B1": 19.3, "B": 25.89, "C": 41.89, "...": "..." }
    },
    "color": {
      "tokens": { "primary": "#0474f2", "neutral800": "#222", "...": "..." }
    }
  },
  "prescriptions": [...]
}
```

`projectMeta` lets you construct ops without re-deriving the project's
spacing scale or palette. For FA304: look up the closest token in
`projectMeta.spacing.scalePx`. For FA301/302/303: search
`projectMeta.color.tokens` for an exact-match or visually-close hex.

## Prescription shape

Every prescription:

```json
{
  "id": "rx-FA304-Card.js-23",
  "finding": {
    "ruleId": "FA304",
    "ruleName": "raw-px-rem",
    "severity": "critical",
    "confidence": "high",
    "risk": "medium",
    "file": "/abs/path/components/Card.js",
    "fileSlot": "components",
    "line": 23,
    "message": "padding: '36px' — use a spacing/sizing token instead of raw px",
    "refusalReason": null
  },
  "sourceContext": [
    { "line": 21, "text": "Card: {" },
    { "line": 22, "text": "  background: 'white'," },
    { "line": 23, "text": "  padding: '36px',", "isFinding": true },
    { "line": 24, "text": "  ..." }
  ],
  "relatedFiles": [
    { "file": "components/Card.js", "line": 14, "role": "declaration" }
  ],
  "proposedOps": [
    {
      "kind": "replaceTokenValue",
      "file": "/abs/path/components/Card.js",
      "line": 23,
      "oldValue": "'36px'",
      "newValue": "'C2'",
      "_rationale": "closest-token=C2 (36.55px) source=36px delta=0.55px"
    }
  ],
  "explanation": "# FA304 — raw-px-rem\n...",
  "safetyCheck": {
    "command": "frank-audit verify",
    "expectNoRegression": true,
    "schema": "frank-audit/1.0"
  }
}
```

**`fileSlot`** tells you where the file lives in the project layout
(`components`, `functions`, `methods`, `pages`, `designSystem`, `index`,
or `null` for orphans). This is **load-bearing** for some fixes:

- Files in `functions/` and `methods/` get **stringified** by frank at
  bundle time. Imports captured from those files don't survive — the
  symbol becomes a free-var ReferenceError at runtime.
- Don't emit `addImport` ops on `functions`/`methods` slot files. Either
  refactor the function to use `this.context.<x>` lookups, or move the
  logic to a component file.
- `setAttribute('data-theme', X)` → `changeGlobalTheme(X)` is safe in
  components but unsafe in functions (without a different way to import).

**`proposedOps` is the load-bearing field.** Rules with `proposedFix()` populate it with ready-to-apply ops:

| Rule | What proposedOps contains |
|---|---|
| **FA301** (hex-color) | `addDesignToken` (if needed) + `replaceTokenValue` with closest palette token, semantic name fallback |
| **FA302** (rgb-color) | rgb→hex conversion, then same as FA301 |
| **FA303** (hsl-color) | hsl→hex conversion, then same as FA301 |
| **FA304** (raw-px-rem) | `replaceTokenValue` with closest spacing token from project's actual generated scale (8% tolerance, skips 1px borders + complex `calc()`) |
| **FA701** (hardcoded text) | `replaceTokenValue` wrapping in polyglot template, with quote-style detection from source |
| **FA801** (page must extend Page) | `setObjectProperty` with kebab→camelCase componentName |
| **FA806** (auto-extend wrapper) | `renameObjectKey` with line-based disambiguation |

For these rules, the agent's job is **acceptance, not construction**. Forwarding `proposedOps` verbatim is the correct call ~95% of the time.

For rules WITHOUT `proposedFix()` (FA2xx multifile, FA5xx DOM bans, FA4xx structural refactors), `proposedOps` is `null`. You must construct ops yourself.

---

## The 12 op kinds

Every op an agent submits must be one of these. Field names are exact. Extra fields are ignored. Missing required fields fail validation.

```json
{ "kind": "removeImport",       "file": "...", "specifier": "...", "source": "..." }
{ "kind": "moveFile",           "from": "...", "to": "..." }
{ "kind": "addToIndexFile",     "dir": "...",  "filename": "..." }
{ "kind": "addToGlobalScope",   "name": "...", "value": <json>, "valueIsCode": false }
{ "kind": "removeTopLevelDecl", "file": "...", "name": "..." }
{ "kind": "addElementScope",    "file": "...", "componentName": "...", "key": "...", "value": <json>, "valueIsCode": false }
{ "kind": "replaceTokenValue",  "file": "...", "line": <n>, "oldValue": "...", "newValue": "..." }
{ "kind": "renameObjectKey",    "file": "...", "componentName": "...", "keyPath": "...", "newKey": "...", "line": <n>? }
{ "kind": "removeObjectKey",    "file": "...", "componentName": "...", "keyPath": "...", "line": <n>? }
{ "kind": "setObjectProperty",  "file": "...", "componentName": "...", "keyPath": "", "propertyKey": "...", "value": <json>, "valueIsCode": false, "position": "start"|"end" }
{ "kind": "addDesignToken",     "file": "...", "name": "...", "value": "..." }
{ "kind": "skip",               "reason": "..." }
```

### When to use each kind

| Kind | When |
|---|---|
| `removeImport` | Sibling import (FA001) whose symbol resolves elsewhere — frank registry, `el.call('fnName')`, `globalScope.js`, or PascalCase component key. |
| `moveFile` | Orphan file (FA006) under `utils/`/`lib/`/`helpers/` that should live in a frank-discovered slot. Move to `functions/<name>.js` or `methods/`. |
| `addToIndexFile` | Component/function file (FA008) that exists on disk but is missing from its sibling `index.js`. Adds `export * from './<filename>'`. |
| `addToGlobalScope` | Multi-file constant or helper (FA202, FA203) that should be promoted to `globalScope.js`. Use `valueIsCode: true` for JS expressions. |
| `removeTopLevelDecl` | Module-scope `let`/`var` (FA201) or single-component `const` (FA204) you've already moved. |
| `addElementScope` | Factory closure (FA205) or single-component constant (FA204) that should ride on the component as `scope: { <key>: <value> }`. Use `valueIsCode: true` for JS expressions. |
| `replaceTokenValue` | Raw design value (FA301–FA304), polyglot wrapping (FA701), expression rewrite (FA401 `window.location.href = X` → `el.router(X, el.getRoot())`). Pass exact line and old text; applier does literal `String#replace` once. |
| `renameObjectKey` | Auto-extend wrapper (FA806): `Header: { extends: 'Navbar' }` → `Navbar: {}`. `componentName` scopes to one top-level component; `keyPath` is dot-separated. Optional `line` disambiguates when keyPath matches multiple places. |
| `removeObjectKey` | Redundant atom extends (FA803/804/805): drop `extends: 'Box'/'Flex'/'Text'`. |
| `setObjectProperty` | Add a property at a key path. Used for FA801 (`extends: 'Page'` on pages). `keyPath: ""` addresses the component itself. `position` controls insertion order. |
| `addDesignToken` | Add a token to `designSystem/color.js` etc. Idempotent — no-op if same value already exists; rejects on collision. Always paired with `replaceTokenValue` that swaps the raw value for the new token name. |
| `skip` | Intent unclear, false positive, would need shared-library edit, or you don't trust the suggestion. ALWAYS prefer `skip` over guessing. |

### Field semantics

- `file`, `from`, `to`, `dir` — absolute paths. Do NOT rewrite to relative.
- `value` — JSON literal by default. Set `valueIsCode: true` and pass a string of valid JS to opt into an expression — the validator parses `(<value>)` and rejects malformed code.
- `oldValue` / `newValue` — must be exact source-character strings INCLUDING quote chars. `'foo'` and `"foo"` are different — the source quote style matters. Rules with `proposedFix()` already detect quote style from source; if you construct ops yourself, you must too.
- `line` (optional, for `renameObjectKey` / `removeObjectKey`) — disambiguator when keyPath matches multiple places. The applier picks the match closest to this line.
- `reason` (for `skip`) — required, short. Surfaces in the response so the orchestrator can log it.

---

## Decision protocol

For each prescription:

1. **Check `proposedOps`** — if non-null, default to forwarding it verbatim.
2. **If you reject `proposedOps` or it's null:**
   - Read `finding`, `sourceContext`, `relatedFiles`, `explanation`.
   - Decide one (or more) of the 12 op kinds.
   - If you cannot decide with confidence, choose `skip` — never guess.
3. **Emit ONLY the contract shape** — array of ops:
   ```json
   { "ops": [ <op>, <op>, ... ] }
   ```
4. **Do not invent new op kinds.** The validator rejects anything outside the 12.
5. **Do not embed raw JS in `value` unless `valueIsCode: true`.**
6. **Do not bundle unrelated prescriptions in one batch.** Verify-or-rollback discards the entire batch on regression — keeping batches small narrows the rollback blast radius. (Unrelated batches that are independent are fine; one-batch-per-prescription is paranoid but safe.)

---

## Validation feedback (pre-IO)

`apply_frankability_edit_ops` validates every op before any IO. On schema failure:

```json
{
  "ok": false,
  "error": {
    "code": "E_OPS_INVALID",
    "message": "one or more edit ops failed validation",
    "details": [
      { "idx": 2, "op": {...}, "error": { "code": "E_OP_MISSING_FIELD", "message": "..." } }
    ]
  }
}
```

Common pre-IO error codes:

- `E_OP_NO_KIND` — missing `kind` field.
- `E_OP_UNKNOWN_KIND` — `kind` is not one of the 12.
- `E_OP_MISSING_FIELD` — required field absent (`details.requiredFields` lists what was expected).
- `E_OP_BAD_TYPE` — wrong type (e.g. `line` not a number).
- `E_OP_INVALID_CODE` — `valueIsCode:true` but `value` does not parse as JS.

You get **one retry** to fix validation errors. After that the prescription is marked skipped.

---

## Per-op skip details (post-IO retry hints)

When an op passes validation but fails to apply, the response carries structured `details` you can use to retry intelligently:

```json
{
  "skipped": [
    {
      "op": {...},
      "reason": "oldValue not found on line 23",
      "details": {
        "code": "E_OLDVALUE_NOT_FOUND",
        "line": 23,
        "expected": "'36px'",
        "actualLine": "  padding: \"36px\","
      }
    }
  ]
}
```

Common per-op skip codes:

| Code | What it means | Retry hint |
|---|---|---|
| `E_FILE_NOT_IN_INPUT` | The file isn't in the project (path typo, file deleted) | Don't retry — the file is gone. |
| `E_LINE_OUT_OF_RANGE` | `line` exceeds file's line count | Re-fetch prescriptions; the file shifted. |
| `E_OLDVALUE_NOT_FOUND` | `oldValue` not on the prescribed line | Read `details.actualLine` — usually the source uses different quote style (`"x"` vs `'x'`) or whitespace. Reconstruct oldValue from the actual line. |
| `E_COMPONENT_NOT_FOUND` | `componentName` not exported from file | Read `details.availableComponents` — usually a kebab-case vs camelCase mismatch (file `admin-bi.js` exports `adminBi`, not `admin-bi`). |
| `E_KEY_NOT_FOUND` | `keyPath` not in the component | Read `details.availableKeys` — pick the right path from what's actually there. |
| `E_CONTAINER_NOT_FOUND` | `keyPath` doesn't resolve to an object container (for `setObjectProperty`) | Same as `E_KEY_NOT_FOUND` — use `availableKeys` to find a container. |
| `E_VALUE_NODE_BUILD_FAILED` | `value` (with `valueIsCode: true`) failed to parse as JS | Fix the syntax of the JS expression and resubmit. |

After retrying, anything still skipped should be either `skip`-op'd or escalated to a human.

---

## Verify-or-rollback safety

Every batch you submit is verified end-to-end:

1. `applyEditOps` snapshots every file an op references, plus `globalScope.js`.
2. Measures a baseline (`bundleFailed?`, `scanIssues` count).
3. Applies your ops to disk (AST mutations + source-line replacements).
4. Re-runs `frank.toJSON({scanAndFix:true})`.
5. If the result regressed (bundle now fails, or scan issues count went up), restores every snapshot.

You do not need to verify yourself. Do not write defensive code. Emit one focused batch, trust the rollback.

Response shape on success:

```json
{
  "schema": "frank-audit/1.0",
  "opId": "edit-mojxxx-yyy",
  "ok": true,
  "applied": 3,
  "skipped": [],
  "rolledBack": false,
  "baseline":   { "bundleFailed": false, "scanIssues": 7 },
  "finalState": { "bundleFailed": false, "scanIssues": 4 },
  "mutatedFiles": ["..."],
  "createdFiles": [],
  "deletedFiles": []
}
```

`rolledBack: true` means your batch was discarded — the project is untouched. Read `baseline` vs `finalState`, look at `frankability_log` for clues, then either re-prescribe more conservatively or `skip`.

---

## Worked example — accept proposedOps verbatim

Most common case. The rule's helper logic already produced a complete fix.

**Prescription excerpt:**

```json
{
  "id": "rx-FA304-Card.js-23",
  "finding": { "ruleId": "FA304", "file": "/abs/components/Card.js", "line": 23,
               "message": "padding: '36px' — use a spacing/sizing token instead of raw px" },
  "proposedOps": [
    { "kind": "replaceTokenValue", "file": "/abs/components/Card.js", "line": 23,
      "oldValue": "'36px'", "newValue": "'C2'",
      "_rationale": "closest-token=C2 (36.55px) source=36px delta=0.55px" }
  ]
}
```

**Correct response** — pass it through:

```json
{
  "ops": [
    { "kind": "replaceTokenValue", "file": "/abs/components/Card.js", "line": 23,
      "oldValue": "'36px'", "newValue": "'C2'" }
  ]
}
```

The `_rationale` field is informational; you can drop or keep it (the validator ignores unknown fields).

---

## Worked example — construct ops for a structural rule

When `proposedOps` is `null` (FA2xx, FA5xx, FA4xx mostly).

**Prescription excerpt:**

```json
{
  "finding": {
    "ruleId": "FA205",
    "ruleName": "factory-closure",
    "file": "/abs/components/Counter.js",
    "line": 12,
    "message": "factory captures [start] inside returned-object handlers — move to scope:{} on the returned object",
    "refusalReason": "ambiguous: factory parameter `start` is also used outside the returned object"
  },
  "sourceContext": [
    { "line": 10, "text": "export const Counter = (start) => ({" },
    { "line": 12, "text": "  count: () => start,", "isFinding": true },
    { "line": 13, "text": "  onClick: (e, el) => el.update({ count: el.count + 1 })" }
  ],
  "proposedOps": null
}
```

**Correct response:**

```json
{
  "ops": [
    {
      "kind": "addElementScope",
      "file": "/abs/components/Counter.js",
      "componentName": "Counter",
      "key": "start",
      "value": "start",
      "valueIsCode": true
    }
  ]
}
```

**What to AVOID:**

- Inventing an op like `{ "kind": "rewriteHandler", … }` — only the 12 kinds exist.
- Sending `"value": "start"` without `"valueIsCode": true` — that writes the literal string `"start"` instead of a reference.
- Adding a second op to "remove the closure" — the handler stays as written; frank does the rewrite at bundle time.

---

## Worked example — retry on per-op failure

You submitted an op, got back:

```json
{
  "skipped": [{
    "op": { "kind": "renameObjectKey", "file": "/abs/pages/admin-bi.js",
            "componentName": "admin-bi", "keyPath": "Header", "newKey": "Navbar" },
    "reason": "key 'Header' not found (or ambiguous) in component 'admin-bi'",
    "details": {
      "code": "E_COMPONENT_NOT_FOUND",
      "componentName": "admin-bi",
      "availableComponents": ["adminBi"]
    }
  }]
}
```

**Retry:** the file's actual export is `adminBi` (camelCase), not `admin-bi` (kebab). Resubmit with corrected `componentName: "adminBi"`.

---

## Quick checklist before you reply

- [ ] Response is a single JSON object with an `ops` array.
- [ ] Every op uses one of the 12 documented kinds.
- [ ] Every required field is present, named exactly, with the right type.
- [ ] `valueIsCode` is set whenever `value` is a JS expression.
- [ ] `oldValue` quote style matches what's actually on the source line (single vs double).
- [ ] If unsure, the op is `skip` with a useful `reason`.
- [ ] You're forwarding `proposedOps` verbatim when present (unless you have a reason to modify).

That is the entire contract. The mechanical fixer + verify-or-rollback handle the rest.
