#!/usr/bin/env bash
# Run the documented runtime examples against a built smbls and, when they
# pass, write the stamp the rules quote ("checked against smbls <version>").
#
#   scripts/check-runtime-examples.sh <smbls-tree>
#
# <smbls-tree>: a smbls monorepo checkout with packages/smbls/dist built
# (`bun run build` or the package's build script) and jsdom installed.
# Writes symbols_mcp/skills/runtime-checked.json only on a green run; the
# examples themselves live in tests/runtime_examples/run.mjs. Re-run it on
# every smbls release and commit the stamp with any doc fixes it forces.
set -euo pipefail
cd "$(dirname "$0")/.."

TREE="${1:-${SYMBOLS_SMBLS_TREE:-}}"
if [ -z "$TREE" ]; then
  echo "usage: scripts/check-runtime-examples.sh <smbls-tree>" >&2
  exit 2
fi

OUT=$(node tests/runtime_examples/run.mjs "$TREE") || {
  echo "$OUT"
  echo "runtime examples FAILED — stamp not written" >&2
  exit 1
}
echo "$OUT"

STAMP=symbols_mcp/skills/runtime-checked.json
printf '%s' "$OUT" | node -e '
let s = ""
process.stdin.on("data", d => { s += d }).on("end", () => {
  const r = JSON.parse(s)
  const stamp = {
    smbls: r.smbls.version,
    commit: r.smbls.commit,
    checked: new Date().toISOString().slice(0, 10),
    examples: r.cases.map(c => c.name)
  }
  process.stdout.write(JSON.stringify(stamp, null, 2) + "\n")
})' > "$STAMP"
echo "wrote $STAMP"
