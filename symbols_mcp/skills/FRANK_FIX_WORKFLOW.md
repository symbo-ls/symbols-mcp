# Frank-fix workflow — LLM reference card

Audience: the LLM that consumes `@symbo.ls/frank-audit` prescriptions through Symbols MCP. This is the contract you must follow when you are asked to fix Symbols-project findings the mechanical fixer refused.

frank-audit is the source-level audit and verify-or-rollback fixer for Symbols projects. It already knows how to mechanically fix high-confidence findings. You exist to handle the medium- and low-confidence cases the mechanical fixer wouldn't touch. The fixer will verify everything you propose against `frank.toJSON` and roll back regressions automatically — your job is to emit good ops, not to verify them.

---

## The 3-tool flow

Always run the tools in this order.

1. **`audit_and_fix_frankability(symbols_dir, mode='safe-fix')`** — first. This runs every mechanical fix that is safe to apply (verify-or-rollback per fix). It costs nothing if there is nothing to fix, and it shrinks the prescription surface for step 2. With `aggressive=True` it also applies medium-confidence rules.

2. **`prescribe_frankability_fixes(symbols_dir)`** — second. Returns the findings the mechanical fixer refused (factory closures requiring intent, multi-file constants the audit can't safely promote, advisory rules without auto-fix, etc.) as structured prescriptions. Each prescription contains:

   - `finding` — `{ ruleId, ruleName, severity, confidence, risk, file, line, message, refusalReason }`
   - `sourceContext` — `~30` lines around the finding with the offending line marked
   - `relatedFiles` — other places in the project that mention the same symbol
   - `proposedFix` — the rule's sketch of what it considered before refusing (may be `null`)
   - `explanation` — the rule's `--explain` output
   - `safetyCheck` — the verify command the orchestrator will run after you apply

3. **`apply_frankability_edit_ops(symbols_dir, ops)`** — third. Pass the JSON you produced. frank-audit validates every op, snapshots affected files, applies them, runs `frank.toJSON`, and rolls back the whole batch if the bundle regresses.

Repeat steps 2–3 until prescriptions are exhausted, the audit converges, or you stop making progress.

---

## The edit-op contract — STRICT JSON, 10 kinds

Every prescription must be answered with one of these op kinds. Field names are exact. Extra fields are ignored. Missing required fields fail validation.

```json
{ "kind": "removeImport",       "file": "...", "specifier": "...", "source": "..." }
{ "kind": "moveFile",           "from": "...", "to": "..." }
{ "kind": "addToIndexFile",     "dir": "...",  "filename": "..." }
{ "kind": "addToGlobalScope",   "name": "...", "value": <json>, "valueIsCode": false }
{ "kind": "removeTopLevelDecl", "file": "...", "name": "..." }
{ "kind": "addElementScope",    "file": "...", "componentName": "...", "key": "...", "value": <json>, "valueIsCode": false }
{ "kind": "replaceTokenValue",  "file": "...", "line": <n>, "oldValue": "...", "newValue": "..." }
{ "kind": "renameObjectKey",    "file": "...", "componentName": "...", "keyPath": "...", "newKey": "..." }
{ "kind": "removeObjectKey",    "file": "...", "componentName": "...", "keyPath": "..." }
{ "kind": "skip",               "reason": "..." }
```

### When to use each kind

| Kind | When |
| -- | -- |
| `removeImport` | A sibling import (FA001) whose symbol resolves elsewhere — frank's registry, `el.call('fnName')`, `globalScope.js`, or a PascalCase component key. Drop the import line. |
| `moveFile` | An orphan file (FA006) under `utils/`, `lib/`, `helpers/` etc. that should live in a frank-discovered slot. Move to `functions/<name>.js` (default) or `methods/` (if it needs `this`-binding). |
| `addToIndexFile` | A component/function file (FA008) that exists on disk but is missing from its sibling `index.js`. Adds `export * from './<filename>'`. |
| `addToGlobalScope` | A multi-file constant or helper (FA202, FA203) that should be promoted to `globalScope.js`. The applier writes `{ <name>: <value> }` into the default-exported object. Use `valueIsCode: true` if `value` is a JS expression rather than a JSON literal. |
| `removeTopLevelDecl` | A module-scope `let`/`var` (FA201) or single-component `const` (FA204) that you've already moved into the right place — drop the original declaration. |
| `addElementScope` | A factory closure (FA205) or single-component constant (FA204) that should ride on the component as `scope: { <key>: <value> }`. The applier creates the `scope` object if missing and merges the key. Use `valueIsCode: true` for a JS expression. |
| `replaceTokenValue` | A raw design value (FA301–FA304: hex color, rgb/hsl, raw px/rem) that maps to a known design-system token. Pass the exact line and old text; the applier does a literal `replace` on that one line. Also handles polyglot wrapping (FA701): pass `"oldValue": "Submit"` → `"newValue": "{{ submit | polyglot }}"`. |
| `renameObjectKey` | Auto-extend wrapper redundancy (FA806): `Header: { extends: 'Navbar' }` → `Navbar: {}`. `componentName` scopes the search to one top-level component; `keyPath` is dot-separated for nested keys (e.g. `'Inner.HeaderBar'`); `newKey` becomes the new property name. The applier also drops a now-redundant `extends: '<newKey>'` from inside the value object. |
| `removeObjectKey` | Redundant atom extends (FA803/804/805): drop `extends: 'Box'` / `'Flex'` / `'Text'` from a component. `componentName` + `keyPath` (e.g. `'extends'`) addresses the property to delete. |
| `skip` | Intent is unclear, the prescription needs human review, the finding is a false positive, or fixing it would require touching shared-library code. ALWAYS prefer `skip` over guessing. |

### Field semantics

- `file`, `from`, `to`, `dir` — absolute paths as they appear in the prescription. Do NOT rewrite to relative.
- `value` — a JSON literal by default (number, string, boolean, null, array, object). Set `valueIsCode: true` and pass a string of valid JS to opt into an expression — the validator parses `(<value>)` and rejects malformed code.
- `oldValue` — must appear literally on the prescribed `line`. The applier does `String#replace` once.
- `reason` (for `skip`) — required, short. Surfaces in the response so the orchestrator can log it.

---

## Decision protocol

For each prescription:

1. **Read** the `finding`, then `sourceContext`, then `relatedFiles`. Skim `proposedFix` and `explanation` if present.
2. **Decide** one of the 10 op kinds. If you cannot decide with confidence, choose `skip` — never guess a fix.
3. **Emit ONLY the contract shape**:
   ```json
   { "ops": [ <op>, <op>, ... ], "reasoning": "<one short paragraph>" }
   ```
4. **Do not write prose outside the JSON.** The orchestrator parses the response as a single JSON object. Any leading or trailing text breaks the parse.
5. **Do not invent new op kinds.** The validator rejects anything outside the 8 listed. There is no `editLine`, `addProp`, `replaceText`, etc.
6. **Do not embed raw JS in `value` unless `valueIsCode: true`.** Strings are strings — `"value": "() => 42"` becomes the literal string `"() => 42"`. To pass a function expression, set `"valueIsCode": true` and the validator will parse it.
7. **Do not ship multiple prescriptions per `ops` array unless they are clearly related**. The fixer rolls back the entire batch on regression — keeping batches small narrows the rollback blast radius.

---

## Validation feedback

`apply_frankability_edit_ops` validates every op before any IO. On failure you get back:

```json
{
  "ok": false,
  "error": {
    "code": "E_OPS_INVALID",
    "message": "one or more edit ops failed validation",
    "details": [ { "idx": 2, "op": {...}, "error": { "code": "E_OP_MISSING_FIELD", "message": "..." } }, ... ]
  }
}
```

Common error codes:

- `E_OP_NO_KIND` — missing `kind` field.
- `E_OP_UNKNOWN_KIND` — `kind` is not one of the 8.
- `E_OP_MISSING_FIELD` — required field absent (`details.requiredFields` lists what was expected).
- `E_OP_BAD_TYPE` — wrong type (e.g. `line` not a number).
- `E_OP_INVALID_CODE` — `valueIsCode:true` but `value` does not parse as JS.

You get **one retry** to fix validation errors. After that, the prescription is marked skipped and the orchestrator moves on. If you cannot answer cleanly, prefer `skip` from the start.

---

## Verify-or-rollback safety

Every batch you submit is verified end-to-end against `frank.toJSON`:

1. `applyEditOps` snapshots every file an op references, plus `globalScope.js`.
2. Measures a baseline (`bundleFailed?`, `scanIssues` count).
3. Applies your ops to disk via the AST.
4. Re-runs `frank.toJSON({scanAndFix:true})`.
5. If the result regressed (bundle now fails, or scan issues count went up), restores every snapshot.

You do not need to verify yourself. Do not write defensive code, do not propose multiple ops "in case one fails", do not try to re-invent the round-trip. Emit one focused batch, trust the rollback.

The response shape on success:

```json
{
  "schema": "frank-audit/1.0",
  "opId": "edit-…",
  "ok": true,
  "applied": 3,
  "skipped": [],
  "rolledBack": false,
  "baseline":   { "bundleFailed": false, "scanIssues": 7 },
  "finalState": { "bundleFailed": false, "scanIssues": 4 },
  "mutatedFiles": [...],
  "createdFiles": [...],
  "deletedFiles": [...]
}
```

`rolledBack: true` means your batch was discarded — read `baseline` vs `finalState`, look at the orchestrator's log, then either re-prescribe more conservatively or `skip`.

---

## Worked example

**Prescription** (truncated):

```json
{
  "id": "rx-FA205-Counter.js-12",
  "finding": {
    "ruleId": "FA205",
    "ruleName": "factory-closure",
    "severity": "critical",
    "confidence": "high",
    "risk": "medium",
    "file": "components/Counter.js",
    "line": 12,
    "message": "factory captures [start] inside returned-object handlers — move to scope:{} on the returned object",
    "refusalReason": "ambiguous: factory parameter `start` is also used outside the returned object"
  },
  "sourceContext": [
    { "line": 10, "text": "export const Counter = (start) => ({" },
    { "line": 11, "text": "  text: 'Counter'," },
    { "line": 12, "text": "  count: () => start,", "isFinding": true },
    { "line": 13, "text": "  onClick: (e, el) => el.update({ count: el.count + 1 })" },
    { "line": 14, "text": "})" }
  ],
  "explanation": "FA205 — factory function captures factory parameters inside returned-object handlers …"
}
```

**Correct response**:

```json
{
  "ops": [
    {
      "kind": "addElementScope",
      "file": "components/Counter.js",
      "componentName": "Counter",
      "key": "start",
      "value": "start",
      "valueIsCode": true
    }
  ],
  "reasoning": "Factory captures `start` inside the returned-object handler at line 12. Promote `start` to scope:{} on the returned object so the value travels with the element through serialization. The handler can keep referencing `start` bare — frank rewrites it to el.scope.start at toJSON time."
}
```

**What to AVOID** in the same scenario:

- Inventing an op like `{ "kind": "rewriteHandler", … }` — only the 10 kinds exist.
- Sending `"value": "start"` without `"valueIsCode": true` — that would write the literal string `"start"` into the scope object instead of a reference.
- Adding a second op to "remove the closure" — there is nothing to remove. The handler stays as written; frank does the rewrite at bundle time.
- Wrapping the response in markdown code fences or appending prose — the orchestrator expects a bare JSON object.

---

## Quick checklist before you reply

- [ ] Response is a single JSON object with `ops` (array) and `reasoning` (string).
- [ ] Every op uses one of the 8 documented kinds.
- [ ] Every required field is present, named exactly, with the right type.
- [ ] `valueIsCode` is set whenever `value` is a JS expression.
- [ ] No prose outside the JSON. No markdown fences.
- [ ] If unsure, the op is `skip` with a useful `reason`.

That is the entire contract. The mechanical fixer handles the rest.
