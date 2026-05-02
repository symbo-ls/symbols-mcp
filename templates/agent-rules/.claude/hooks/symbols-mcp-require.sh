#!/usr/bin/env bash
# PreToolUse hook for Edit|Write|MultiEdit.
#
# When Claude tries to edit a *.js / *.mjs / *.ts(x) / *.jsx file inside a
# Symbols project (any ancestor directory contains symbols.json), this hook
# blocks the edit unless the session has already called
# mcp__symbols-mcp__get_project_rules OR mcp__symbols-mcp__get_project_context.
#
# Rationale: editing DOMQL / smbls code without first loading the canonical
# rules produces non-frankable code that breaks under frank.toJSON serialization.
# The hook forces Claude to discover rules before writing.
#
# Hook contract:
#   - stdin: JSON { tool_name, tool_input, transcript_path, ... }
#   - exit 0 = allow
#   - exit 2 = block (stderr is shown to Claude as a tool result)

set -euo pipefail

INPUT=$(cat)

# jq is required for parsing. If missing, fail open (don't break the user's session).
if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

TOOL=$(echo "$INPUT"  | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

# Only enforce on Edit/Write/MultiEdit
case "$TOOL" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

# Only enforce on JS-ish files
case "$FILE_PATH" in
  *.js|*.mjs|*.cjs|*.ts|*.tsx|*.jsx) ;;
  *) exit 0 ;;
esac

# Walk up looking for symbols.json
DIR=$(dirname -- "$FILE_PATH")
SYMBOLS_PROJECT=""
while [ "$DIR" != "/" ] && [ "$DIR" != "." ] && [ -n "$DIR" ]; do
  if [ -f "$DIR/symbols.json" ]; then
    SYMBOLS_PROJECT="$DIR"
    break
  fi
  PARENT=$(dirname -- "$DIR")
  [ "$PARENT" = "$DIR" ] && break
  DIR="$PARENT"
done

# Not inside a Symbols project — allow
[ -z "$SYMBOLS_PROJECT" ] && exit 0

# Symbols project — verify rules were loaded this session
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  if grep -qE 'mcp__symbols-mcp__(get_project_rules|get_project_context|generate_component|generate_page|audit_component)' "$TRANSCRIPT"; then
    exit 0
  fi
fi

cat >&2 <<EOF
🚫 BLOCKED — Symbols project edit without rules loaded.

Project: $SYMBOLS_PROJECT
File:    $FILE_PATH

You MUST call these BEFORE editing any DOMQL / smbls code:

  1. mcp__symbols-mcp__get_project_context
     (resolves owner/key/env from symbols.json)

  2. mcp__symbols-mcp__get_project_rules
     (loads FRAMEWORK + DESIGN_SYSTEM + RULES + FRANKABILITY)

After loading, also use:
  • mcp__symbols-mcp__generate_component / generate_page  for new code
  • mcp__symbols-mcp__audit_component(code)               after every component
  • mcp__symbols-mcp__audit_and_fix_frankability(dir)     before committing

Why: editing without rules produces code that breaks under frank.toJSON
(silent module-scope capture loss, lowercase children that never render,
raw px/hex tokens, FA206 npm-import-in-handler, etc.).

To bypass once (NOT recommended): set SYMBOLS_MCP_REQUIRE_RULES=0 before
launching Claude Code.
EOF

# Honour env-var bypass
if [ "${SYMBOLS_MCP_REQUIRE_RULES:-1}" = "0" ]; then
  echo "(bypass: SYMBOLS_MCP_REQUIRE_RULES=0 — allowing despite missing rules)" >&2
  exit 0
fi

exit 2
