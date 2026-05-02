# `.claude/` — Symbols-MCP enforcement layer for Claude Code

This directory ships with every Symbols project (installed by `npx -y @symbo.ls/mcp init-rules`). It contains a `settings.json` that wires three hooks Claude Code runs around every tool call. Together, they make `symbols-mcp` rule-loading **non-bypassable** for any Symbols project edit.

If you're reading this in the templates folder of `symbols-mcp` itself, this is the master copy that gets copied into user projects.

---

## What's here

```
.claude/
├── README.md                          ← this file
├── settings.json                      ← wires the three hooks below
└── hooks/
    ├── README.md                      ← hook-by-hook reference
    ├── symbols-mcp-require.sh         ← PreToolUse — blocks Edit/Write
    ├── symbols-mcp-reminder.sh        ← UserPromptSubmit — injects directive
    └── symbols-mcp-audit.sh           ← PostToolUse — runs frank-audit
```

---

## Why this exists

`symbols-mcp` exposes a strict ruleset (DOMQL flat syntax, design tokens, frankability FA-rules). Three layers try to get the agent to load it:

| Layer | Mechanism | Reliability |
|---|---|---|
| 1 | MCP server `instructions` field (auto-loaded on connect) | best-effort — model may ignore |
| 2 | `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/symbols.md` | best-effort — diluted in long contexts |
| 3 | **Hooks (this directory)** | **non-bypassable — enforced by the harness** |

Layers 1+2 are advice. Layer 3 is a gate. Without the hooks, an agent under context pressure can drift, edit DOMQL without loading rules, and produce code that breaks under `frank.toJSON` (silent prod-only failures).

---

## Project-level vs user-global install

**Default: project-level** — this directory lives in your Symbols project root. `init-rules` writes it; `git` tracks it; the team's editors all get the same enforcement.

```bash
# from a Symbols project root
npx -y @symbo.ls/mcp init-rules
```

**Alternative: user-global** — install to `~/.claude/` once; works for every Symbols project you ever open. The hooks self-detect a Symbols project by walking up for `symbols.json` and no-op elsewhere, so this is safe even if you also work on non-Symbols repos.

```bash
# install hooks globally for the current user
npx -y @symbo.ls/mcp init-rules --global
```

When both exist, project-level settings override user-global (Claude Code merges, project-last-wins).

---

## Disabling

**Skip install:** `init-rules --no-hooks`.

**Disable a single hook at runtime** (export before launching Claude Code):

```bash
export SYMBOLS_MCP_REQUIRE_RULES=0   # PreToolUse  — allows Edit/Write without rules loaded
export SYMBOLS_MCP_REMINDER=0        # UserPromptSubmit — drops the per-turn injection
export SYMBOLS_MCP_POST_AUDIT=0      # PostToolUse  — no frank-audit on writes
```

**Permanently:** delete `.claude/hooks/<name>.sh` (or the entire `.claude/` dir). The settings.json reference will silently fail open if the script is missing.

---

## Replicating from scratch

If you can't run `init-rules`, copy this whole directory into your project root and:

1. Make the hook scripts executable: `chmod +x .claude/hooks/*.sh`
2. Confirm `bash` and `jq` are on `PATH` (`brew install jq` if not).
3. Restart Claude Code in the project. The next session picks up the hooks.

---

## Verifying

In a Claude Code session, ask the agent to edit a `.js` file directly without invoking any `mcp__symbols-mcp__*` tool first. You should see:

```
🚫 BLOCKED — Symbols project edit without rules loaded.
Project: /path/to/your/symbols/project
File:    /path/.../components/Foo.js
You MUST call these BEFORE editing any DOMQL / smbls code:
  1. mcp__symbols-mcp__get_project_context
  2. mcp__symbols-mcp__get_project_rules
...
```

Once the agent calls one of those tools, subsequent edits proceed.

---

## Maintaining the hooks

These templates live at `symbols-mcp/templates/agent-rules/.claude/`. To update a hook for all future `init-rules` runs, edit the file in the templates dir, bump the `symbols-mcp` package version, and republish. Existing projects can pull the latest with:

```bash
npx -y @symbo.ls/mcp init-rules --force
```
