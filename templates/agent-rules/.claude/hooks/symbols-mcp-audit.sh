#!/usr/bin/env bash
# PostToolUse hook for Edit|Write|MultiEdit.
#
# After any *.js / *.mjs edit inside a Symbols project, runs frank-audit on
# the modified file and surfaces any FA-rule violations back to Claude as a
# correction signal.
#
# Hook contract:
#   - stdin: JSON { tool_name, tool_input, tool_response, ... }
#   - stdout: text appended as additional context for the next turn
#   - exit 0

# `set -uo pipefail` only — the hook is full of conditional `grep ... | wc -l`
# pipelines where exit 1 (no match) is a normal outcome, not an error. With
# `set -e` the script would terminate on the first benign no-match, suppressing
# all the audit output we wanted to surface.
set -uo pipefail

INPUT=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

TOOL=$(echo "$INPUT"  | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

case "$TOOL" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  *.js|*.mjs) ;;
  *) exit 0 ;;
esac

[ ! -f "$FILE_PATH" ] && exit 0

# Walk up for symbols.json
DIR=$(dirname -- "$FILE_PATH")
SYMBOLS_PROJECT=""
while [ "$DIR" != "/" ] && [ -n "$DIR" ]; do
  if [ -f "$DIR/symbols.json" ]; then
    SYMBOLS_PROJECT="$DIR"
    break
  fi
  PARENT=$(dirname -- "$DIR")
  [ "$PARENT" = "$DIR" ] && break
  DIR="$PARENT"
done

[ -z "$SYMBOLS_PROJECT" ] && exit 0

# Allow user to silence
[ "${SYMBOLS_MCP_POST_AUDIT:-1}" = "0" ] && exit 0

# Try frank-audit if available; fall back to a fast inline pattern check.
# Limit to single-file audit by default; whole-project audit would be too slow per write.
OUT=""
if command -v npx >/dev/null 2>&1; then
  OUT=$(cd "$SYMBOLS_PROJECT" && npx -y --no-install @symbo.ls/frank-audit audit "$SYMBOLS_PROJECT" --rule FA001,FA101,FA102,FA103,FA104,FA105,FA106,FA206,FA207 2>&1 | grep -E "$(basename "$FILE_PATH")" || true)
fi

# Inline lightweight checks (run regardless — fast, deterministic, no network).
INLINE=""
add() { INLINE="${INLINE}  • $1"$'\n'; }

if grep -qE '\bel\.props\.' "$FILE_PATH"; then
  add "FA101 — el.props.X found; flatten to el.X"
fi
if grep -qE '\bel\.on\.[a-z]' "$FILE_PATH"; then
  add "FA102 — el.on.event found; flatten to el.onEvent"
fi
if grep -qE '^\s*(props|on)\s*:\s*\{' "$FILE_PATH"; then
  add "FA103/FA104 — props:{} or on:{} wrapper; flatten to top-level"
fi
if grep -qE '^\s*attr\s*:\s*\{[^}]*(placeholder|type|name|value|disabled|title|href|src|alt|role|tabindex)' "$FILE_PATH"; then
  add "FA105 — attr:{ ... } wrapping flat HTML attrs; lift to top-level"
fi
if grep -qE '\(\s*\{\s*(state|props|key)\s*[,}]' "$FILE_PATH"; then
  add "FA106 — destructured handler signature; use (el, s)"
fi
if grep -qE 'function\s+[A-Za-z_]+\s*\([^)]*\)\s*\{' "$FILE_PATH"; then
  # Catch only inside lifecycle handlers — heuristic
  if grep -qE 'on(Render|Click|Init|Input|Change|Submit|Mount|Update)\s*:\s*(async\s+)?\([^)]*\)\s*=>' "$FILE_PATH"; then
    add "FA207 — possible nested 'function name () {}' inside a handler; use const x = () => {}"
  fi
fi
if grep -qE "^\s*(import\s+\{[^}]*\}|import\s+[A-Za-z_]+)\s+from\s+['\"][^./@][^'\"]*['\"]" "$FILE_PATH"; then
  if grep -qE 'on(Render|Click|Init|Input|Change|Submit|Mount|Update)' "$FILE_PATH"; then
    add "FA206 — top-level static import in a file with handlers; use dynamic await import('pkg') inside the handler"
  fi
fi
if grep -qE '\b(window|document)\.update\s*\(' "$FILE_PATH"; then
  add "FA513 — window.update()/document.update() banned; declare onScroll/onClick on the element"
fi
if grep -qE 'window\.__[A-Za-z]' "$FILE_PATH"; then
  add "FA514 — module-side-effect bridge (window.__X = ...); use globalScope.js bare reference"
fi

# ── Project-level + shared-library duplication detector ───────────────────
# If the just-edited file exports a component, scan local components AND any
# resolved shared-library components for high textual overlap, surfacing both
# "you may be redefining a library export" and "near-duplicate of existing".
DUP_OUT=""
LIB_OUT=""
case "$FILE_PATH" in
  *"$SYMBOLS_PROJECT"/components/*|*"$SYMBOLS_PROJECT"/pages/*|*"$SYMBOLS_PROJECT"/snippets/*)
    NEW_NAME=$(grep -oE '^export const [A-Z][A-Za-z0-9_]+' "$FILE_PATH" | head -1 | awk '{print $3}')
    if [ -n "$NEW_NAME" ]; then
      FP=$(grep -oE '^\s+[A-Z][A-Za-z0-9_]*:\s*\{' "$FILE_PATH" | sed 's/[[:space:]]//g' | sort -u | head -20 | tr '\n' '|')
      MIN_TOK=4

      # Resolve potential library locations: .symbols_local/libs/*/*/components/
      # (local mode) and node_modules/*/components/ + node_modules/@*/*/components/
      # (npm mode). Glob expansion handles "no matches" with set +o nullglob default
      # (returning literal path) — we filter via -d in the loop.
      LIB_DIRS=""
      for d in "$SYMBOLS_PROJECT"/.symbols_local/libs/*/*/components \
               "$SYMBOLS_PROJECT"/node_modules/*/components \
               "$SYMBOLS_PROJECT"/node_modules/@*/*/components; do
        [ -d "$d" ] && LIB_DIRS="$LIB_DIRS $d"
      done

      # 1. Check if the user just redefined a library export with the same name.
      if [ -n "$LIB_DIRS" ] && [ -n "$NEW_NAME" ]; then
        for LIBDIR in $LIB_DIRS; do
          LIB_HIT=$(grep -rlE "^export const $NEW_NAME\b" "$LIBDIR" 2>/dev/null | head -3)
          if [ -n "$LIB_HIT" ]; then
            for f in $LIB_HIT; do
              REL=$(echo "$f" | sed "s|$SYMBOLS_PROJECT/||")
              LIB_OUT="${LIB_OUT}  • $NEW_NAME already exists in shared library: $REL"$'\n'
            done
          fi
        done
      fi

      # 2. Local-component duplication (within current project).
      if [ -n "$FP" ] && [ -d "$SYMBOLS_PROJECT/components" ]; then
        for PEER in $(find "$SYMBOLS_PROJECT/components" -maxdepth 3 -name '*.js' -not -path "$FILE_PATH" 2>/dev/null); do
          PEER_NAME=$(grep -oE '^export const [A-Z][A-Za-z0-9_]+' "$PEER" 2>/dev/null | head -1 | awk '{print $3}')
          [ -z "$PEER_NAME" ] && continue
          [ "$PEER_NAME" = "$NEW_NAME" ] && continue
          PEER_FP=$(grep -oE '^\s+[A-Z][A-Za-z0-9_]*:\s*\{' "$PEER" 2>/dev/null | sed 's/[[:space:]]//g' | sort -u | head -20 | tr '\n' '|')
          [ -z "$PEER_FP" ] && continue
          SHARED=$(echo "$FP" | tr '|' '\n' | grep -F -f <(echo "$PEER_FP" | tr '|' '\n') 2>/dev/null | wc -l | tr -d ' ')
          if [ "${SHARED:-0}" -ge "$MIN_TOK" ]; then
            REL=$(echo "$PEER" | sed "s|$SYMBOLS_PROJECT/||")
            DUP_OUT="${DUP_OUT}  • $NEW_NAME shares $SHARED top-level keys with $PEER_NAME ($REL)"$'\n'
          fi
        done
      fi
    fi
    ;;
esac

# Decide whether to emit anything. Under `set -euo pipefail`, `grep -c | head`
# can break the pipeline (grep exits 1 on no match), so use a boolean test.
HAS_FA_OUT=0
if echo "$OUT" | grep -qE 'FA[0-9]+|critical' 2>/dev/null; then
  HAS_FA_OUT=1
fi
if [ -n "$INLINE" ] || [ "$HAS_FA_OUT" -gt 0 ] || [ -n "$DUP_OUT" ] || [ -n "$LIB_OUT" ]; then
  echo "[symbols-mcp post-write audit — $FILE_PATH]"
  if [ -n "$INLINE" ]; then
    echo "Inline FA-rule checks flagged:"
    printf '%s' "$INLINE"
  fi
  if [ "$HAS_FA_OUT" -gt 0 ]; then
    echo
    echo "frank-audit output:"
    echo "$OUT" | head -40
  fi
  if [ -n "$LIB_OUT" ]; then
    echo
    echo "🔁 Reuse — name collision with a shared library:"
    printf '%s' "$LIB_OUT"
    echo "  → If overriding intentionally, this is fine — but use 'extends: \"$NEW_NAME\"'"
    echo "    to inherit from the library version rather than redefining from scratch."
    echo "  → If you didn't realize the library already defines this, drop your file"
    echo "    and reference the library export by bare key: \"$NEW_NAME: { ... }\"."
  fi
  if [ -n "$DUP_OUT" ]; then
    echo
    echo "🔁 Project-level reuse — possible duplication detected:"
    printf '%s' "$DUP_OUT"
    echo "  → Consider: extend an existing component, override props on the bare key,"
    echo "    OR (if 3+ near-duplicates) lift the shared shape into ONE canonical"
    echo "    components/<Name>.js and reference by bare key from each consumer."
  fi
  echo
  echo "Fix BEFORE the next edit. Use mcp__symbols-mcp__audit_and_fix_frankability"
  echo "for auto-fixes, or rewrite per FRANKABILITY.md / project-reuse rules."
fi

exit 0
