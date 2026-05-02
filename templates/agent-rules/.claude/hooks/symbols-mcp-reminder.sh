#!/usr/bin/env bash
# UserPromptSubmit hook.
#
# Injects a per-turn directive into the conversation when the cwd is inside a
# Symbols project. CLAUDE.md instructions get diluted across long contexts;
# a per-turn reminder doesn't.
#
# Hook contract:
#   - stdin: JSON { cwd, prompt, ... }
#   - stdout: text appended as additional context for this turn
#   - exit 0

set -euo pipefail

INPUT=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
[ -z "$CWD" ] && CWD=$(pwd)

# Walk up looking for symbols.json
DIR="$CWD"
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

# Allow user to silence with env var (for paste-heavy workflows)
[ "${SYMBOLS_MCP_REMINDER:-1}" = "0" ] && exit 0

cat <<EOF
[symbols-mcp directive — cwd is inside a Symbols project: $SYMBOLS_PROJECT]

MUST-DO sequence for ANY DOMQL / smbls task:
  1. mcp__symbols-mcp__get_project_context  (FIRST, every session)
  2. mcp__symbols-mcp__get_project_rules    (before generating/editing)
                                             — bundles ALL skill .md files:
                                               FRAMEWORK + DESIGN_SYSTEM + RULES +
                                               COMPONENTS + DEFAULT_COMPONENTS +
                                               SYNTAX + PATTERNS + SNIPPETS +
                                               SHARED_LIBRARIES + FRANKABILITY +
                                               FRANK_FIX_WORKFLOW + COMMON_MISTAKES +
                                               LEARNINGS + DEFAULT_PROJECT.
                                             READ ALL OF IT. Don't skim past
                                             COMPONENTS.md / DEFAULT_COMPONENTS.md.
  3. mcp__symbols-mcp__generate_component / generate_page  (new code)
  4. mcp__symbols-mcp__audit_component(code)               (after each component)
  5. mcp__symbols-mcp__audit_and_fix_frankability(dir)     (before committing)

🧱 BUILT-IN COMPONENTS — REUSE, DO NOT REDEFINE
Every Symbols project inherits @symbo.ls/default-config:
  Atoms     Block, Box, Flex, Grid, Hgroup, Img, Picture, Video, Iframe,
            Text, Form, Svg, Shape, Theme, InteractiveComponent
  Components Avatar, Button, Dialog, Dropdown, Link, Notification, Range,
            Select, Tooltip, Icon, Input
DOMQL auto-extends by key. Just write the bare key:
  ✅ Avatar: { src: 'me.jpg' }                  ← renders built-in
  ✅ Avatar_1: {...}, Avatar_2: {...}           ← multi-instance
  ❌ Avatar: { tag: 'div', borderRadius: ... }  ← redefining = wrong
  ❌ Avatar: { extends: 'Avatar', src: ... }    ← redundant extends
The DESIGN SYSTEM (colors, typography, spacing, themes) IS meant to be
branded per project via designSystem/ token files. Components are NOT.

🔁 REUSE — 3-TIER SEARCH ORDER (BEFORE CREATING)
DOMQL bare-key resolver walks: (1) framework built-ins → (2) shared
libraries (linked in sharedLibraries.js) → (3) current project. Card: {}
works whichever tier defines Card.
Discovery before writing:
  • cat sharedLibraries.js                                  ← what's linked?
  • grep -E 'sharedLibrariesMode' symbols.json              ← npm or local mode?
  • Library files (READ-ONLY — never edit; override locally instead):
      npm mode    → node_modules/<package>/components/
      local mode  → .symbols_local/libs/<owner>/<key>/components/
      destDir     → custom path per entry in sharedLibraries.js
  • Local: grep -rE '^export const [A-Z]' components/ snippets/
  • Functions: grep -rE '^export (const|function) ' functions/ methods/
  • Semantic: mcp__symbols-mcp__search_symbols_docs(query)
Most projects use system/default (~127 components). Check there first.
Override pattern (when library component needs a tweak):
  components/Card.js → export const Card = { extends: 'Card', ... }
Reuse rules:
  • Any tier covers ~80% → bare-key reference + override differing props
  • Writing the 3rd near-duplicate (local) → STOP, extract to
    components/<Name>.js, replace duplicates with bare-key references
  • Two pages compute the same thing → extract to functions/<name>.js,
    invoke via el.call('name', ...). NEVER import between project files.
Frank-discovered folders (anything else is silently dropped at publish):
  components/, snippets/, pages/, functions/, methods/, designSystem/,
  files/, assets/. NEVER use utils/ lib/ helpers/.

Frankability hard rules (FA0xx–FA5xx — full list in FRANKABILITY.md):
  • FA001  no sibling-imports — use el.call('fnName') or PascalCase key refs
  • FA101  el.X (NEVER el.props.X)        FA102  el.onClick (NEVER el.on.click)
  • FA105  flat HTML attrs                FA106  (el, s) signature, no destructure
  • FA201  mutable state in globalScope.js  FA204  one-shot const → scope: { X }
  • FA206  dynamic await import('pkg') in handlers (NEVER top-level static)
  • FA207  nested helpers: const x = () => {}  (NEVER function x () {})
  • FA208  globalScope.js never cross-imports from peers
  • FA209  dependencies.js = runtime importmap only
  • FA210  bypass-mode handlers guard el.node and s.parent?/s.root?
  • FA513  no window.update() / document.update()
  • FA514  no window.__projectInit module-side-effect bridges

Pre-edit hook will BLOCK Edit/Write on *.js inside this project until step 2 runs.
EOF

exit 0
