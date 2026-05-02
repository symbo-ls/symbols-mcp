# `.claude/hooks/` — symbols-mcp enforcement scripts

Three bash scripts that make `symbols-mcp` rule-loading non-bypassable in Claude Code. Each implements one of Claude Code's hook events. Wired up by the sibling `../settings.json`.

> Hook contract: stdin is JSON (Claude Code-supplied), stdout is text appended to the conversation, exit code 0 = allow / 2 = block.

---

## `symbols-mcp-require.sh` — PreToolUse `Edit|Write|MultiEdit`

**Purpose:** prevent the agent from editing Symbols code without first loading the rules.

**When it runs:** before every `Edit`, `Write`, or `MultiEdit` tool call.

**What it does:**
1. Parses `tool_name` and `tool_input.file_path` from stdin.
2. Returns immediately if the tool isn't an editor or the file isn't `.js`/`.mjs`/`.cjs`/`.ts`/`.tsx`/`.jsx`.
3. Walks up from the file path looking for `symbols.json`. If none, returns (not a Symbols project).
4. Greps the session transcript for any of:
   - `mcp__symbols-mcp__get_project_rules`
   - `mcp__symbols-mcp__get_project_context`
   - `mcp__symbols-mcp__generate_component`
   - `mcp__symbols-mcp__generate_page`
   - `mcp__symbols-mcp__audit_component`
5. If found → exit 0 (allow). If not → exit 2 with a `🚫 BLOCKED` message naming the project, the file, and the MUST-DO sequence.

**Bypass:** `SYMBOLS_MCP_REQUIRE_RULES=0`.

**Failure modes:**
- Missing `jq` on `PATH` → fails open (exits 0, silent).
- Empty `transcript_path` → treats as "rules not loaded yet" → blocks.

---

## `symbols-mcp-reminder.sh` — UserPromptSubmit

**Purpose:** inject a per-turn directive so the agent doesn't drift away from the rules across long contexts. CLAUDE.md is read once per session and gets diluted; this fires on every prompt.

**When it runs:** every time the user submits a prompt.

**What it does:**
1. Parses `cwd` from stdin (falls back to the shell's `pwd`).
2. Walks up looking for `symbols.json`. If not found, exits silently.
3. If found, prints to stdout:
   - The MUST-DO sequence (`get_project_context` → `get_project_rules` → `generate_component`/`generate_page` → `audit_component` → `audit_and_fix_frankability`).
   - Frankability cheatsheet covering FA001 / FA101 / FA102 / FA105 / FA106 / FA201 / FA204 / FA206 / FA207 / FA208 / FA209 / FA210 / FA513 / FA514.
   - Reminder that the PreToolUse hook will block Edit/Write until step 2 runs.

**Bypass:** `SYMBOLS_MCP_REMINDER=0`.

**Cost:** one extra ~1 KB block per turn. Negligible.

---

## `symbols-mcp-audit.sh` — PostToolUse `Edit|Write|MultiEdit`

**Purpose:** force a fix loop after every JS edit by surfacing FA-rule violations back to Claude immediately.

**When it runs:** after every successful `Edit`, `Write`, or `MultiEdit` tool call.

**What it does:**
1. Parses `tool_name` and `tool_input.file_path` from stdin.
2. Returns if not an editor tool or not `.js`/`.mjs`.
3. Walks up for `symbols.json`. If not found, exits silently.
4. Runs `npx -y --no-install @symbo.ls/frank-audit <file>` from the project root (silent skip if not installed).
5. Runs an inline regex pattern check covering:
   - **FA101** `el.props.X`
   - **FA102** `el.on.event`
   - **FA103/FA104** `props: {}` / `on: {}` wrappers
   - **FA105** `attr: { placeholder | type | name | … }` wrapping flat HTML attrs
   - **FA106** destructured handler signatures `({state}) =>`
   - **FA206** top-level static npm imports in handler-bearing files
   - **FA207** `function name () {}` inside lifecycle handlers
   - **FA513** `window.update()` / `document.update()`
   - **FA514** `window.__projectInit` module-side-effect bridges
6. If anything triggers, prints a `[symbols-mcp post-write audit]` block listing FA-IDs and pointing at the auto-fix tool.

**Bypass:** `SYMBOLS_MCP_POST_AUDIT=0`.

**Cost:** one `npx` invocation per write. Cached after first run; ~200 ms steady state.

---

## Hook anatomy — adapting these for your own enforcement

If you want to add more checks (e.g. block edits inside `node_modules`, run a lint pass on schema changes), the pattern is:

```bash
#!/usr/bin/env bash
set -euo pipefail
INPUT=$(cat)
command -v jq >/dev/null 2>&1 || exit 0           # fail-open if jq missing

TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# guard clauses — exit 0 to allow, exit 2 to block
case "$TOOL" in Edit|Write) ;; *) exit 0 ;; esac

# emit text to stdout to inject context, or to stderr + exit 2 to block
echo "<your message>" >&2
exit 2
```

Wire it into `../settings.json`:

```json
"hooks": {
  "PreToolUse": [
    { "matcher": "Edit|Write|MultiEdit", "hooks": [
      { "type": "command", "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/your-hook.sh" }
    ]}
  ]
}
```

---

## Testing a hook in isolation

```bash
# simulate a PreToolUse Edit invocation
echo '{
  "tool_name": "Edit",
  "tool_input": { "file_path": "/path/to/your/symbols/project/components/Foo.js" },
  "transcript_path": "/tmp/empty.jsonl"
}' | bash .claude/hooks/symbols-mcp-require.sh
echo "exit: $?"
```

Expected: exit 2, BLOCKED message on stderr.

```bash
# simulate with a transcript that DOES have get_project_rules
echo 'mcp__symbols-mcp__get_project_rules' > /tmp/with-rules.jsonl
echo '{"tool_name":"Edit","tool_input":{"file_path":"/proj/x.js"},"transcript_path":"/tmp/with-rules.jsonl"}' \
  | bash .claude/hooks/symbols-mcp-require.sh
echo "exit: $?"
```

Expected: exit 0, no output.
