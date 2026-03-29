# Symbols / DOMQL v3 — Full Audit Protocol

Follow this protocol exactly. Execute each phase in order. Do not skip steps.

---

## 1. Install the MCP Server

Run the following command to install:

```bash
pip install symbols-mcp
```

---

## 2. Configure the MCP Server

Add this configuration to your MCP settings:

```json
{
  "mcpServers": {
    "symbols": {
      "command": "uvx",
      "args": ["symbols-mcp"]
    }
  }
}
```

---

## 3. Apply the Authority Model

Use the MCP server for all analysis. Treat every file as required. Treat every rule as mandatory.

Resolve conflicts in this priority order:

1. DOMQL v3 conventions (highest)
2. Architectural direction
3. Design system integrity (lowest)

---

## 4. Load All Mandatory Skills

Before auditing, confirm that every skill below has been consulted. Do not proceed without full coverage.

### Rules & Project Setup
- RULES
- PROJECT_STRUCTURE
- RUNNING_APPS

### Syntax & Migration
- SYNTAX
- MIGRATION
- SSR-BRENDER

### Design System
- DESIGN_SYSTEM
- DEFAULT_LIBRARY
- DEFAULT_STYLES

### UI / UX / Direction
- PATTERNS
- DESIGN_DIRECTION
- DESIGN_TO_CODE
- DESIGN_PERSONAS (includes: Brand Identity, Design Critique, Design Trend, Design System Architect, Figma Matching, Marketing Assets, Presentation)

### Components
- COMPONENTS
- DEFAULT_COMPONENTS

### SEO
- SEO-METADATA

### Reference & Learning
- COOKBOOK
- SNIPPETS
- LEARNINGS

---

## 5. Define the Audit Scope

Scan the entire `smbls/` directory. Cover every file without exception.

- Do not perform partial scans.
- Do not apply selective fixes.
- Audit everything.

---

## 6. Execute the 7 Audit Phases

Complete each phase fully before moving to the next.

### Phase 1 — Structural & Syntax Integrity

1. Scan for and eliminate all critical syntax errors.
2. Identify and remove all legacy DOMQL v2 patterns.
3. Enforce DOMQL v3 structure on every component.
4. Normalize all event handler conventions.
5. Standardize all shorthand props.
6. Verify correct atom usage throughout.
7. Enforce proper state patterns.
8. Validate all dynamic children handling.

### Phase 2 — Design System Enforcement

1. Find and replace all hardcoded styles with design tokens.
2. Enforce design tokens in all props.
3. Validate spacing, typography, radii, color, and shadow values against the token system.
4. Align all visual output with DESIGN_SYSTEM.md and DEFAULT_LIBRARY.md.
5. Eliminate all visual drift from the design system.

### Phase 3 — Component Discipline

1. Identify custom implementations that duplicate built-in components.
2. Replace those with the correct built-in component per COMPONENTS.md.
3. Align all component usage with DEFAULT_COMPONENTS.md.
4. Remove all component duplication.

### Phase 4 — Accessibility Compliance

1. Validate semantic HTML across all components.
2. Verify keyboard navigation compliance.
3. Check all ARIA attributes for correctness.
4. Apply auditory accessibility best practices.
5. Enforce contrast ratios.
6. Confirm interaction feedback is present and correct.

### Phase 5 — Icons & Visual Consistency

1. Standardize the icon system across the codebase.
2. Remove all mixed or inconsistent icon sets.
3. Align icon scale and weight with the design system.

### Phase 6 — SEO & Metadata

1. Enforce structured metadata on all applicable pages.
2. Validate semantic markup for search engines.
3. Apply all rules from SEO-METADATA.md.

### Phase 7 — UI / UX Coherence

1. Align all layouts and flows with DESIGN_DIRECTION.md.
2. Enforce visual hierarchy discipline.
3. Fix all layout inconsistencies.
4. Validate Figma-to-code fidelity per DESIGN_PERSONAS (Figma Matching section).
5. Remove all visual noise.

---

## 7. Follow This Execution Order

Perform these steps sequentially. Do not start a later step until the previous one is complete.

1. Run a full static audit of the codebase.
2. Extract and categorize all issues found.
3. Generate a refactor plan from the categorized issues.
4. Apply structural fixes (Phase 1).
5. Apply design system fixes (Phase 2).
6. Apply accessibility fixes (Phase 4).
7. Apply visual polish (Phases 3, 5, 7).
8. Run a final consistency sweep across the entire codebase.

Do not make cosmetic adjustments before structural compliance is achieved.

---

## 8. Extract Thread-Wide Findings

Review the entire conversation history. Collect and normalize every instance of:

- Reported bugs
- Recurring friction points
- Misuse of Symbols patterns
- Unclear API usage
- Architectural inconsistencies
- Design complaints
- Ambiguity in documentation

Deduplicate all findings. Classify each one using the severity levels in Section 10.

---

## 9. Produce Feedback Documentation

Generate or update two files. Keep their scopes strictly separated.

### symbols-feedback.md — Framework-Level Issues Only

Include only framework-level findings:

- DOMQL v3 violations
- UPPERCASE design system keys (COLOR, THEME, etc. — must be lowercase)
- Event handler misuse
- Atom/state mispatterns
- Shorthand inconsistencies
- Dynamic children misuse
- Design system misuse
- Migration errors
- Accessibility framework gaps
- Architectural inconsistencies
- Documentation ambiguity
- Agent friction

Do not include project-specific issues in this file.

### project-feedback.md — Project-Level Issues Only

Include only project-specific findings:

- Design direction inconsistencies
- UX confusion
- Visual imbalance
- Layout flaws
- Component misuse specific to the project
- Brand drift
- Interaction flaws
- Missing states
- SEO implementation errors
- Bug reports

Do not include framework-level issues in this file.

---

## 10. Classify Severity

Assign exactly one severity level to every finding. Do not mix categories.

| Severity | Definition |
|---|---|
| **Critical** | Breaking, unsafe, or structurally invalid. Must fix immediately. |
| **Structural** | Architecture misalignment. Fix before any polish work. |
| **Systemic** | Pattern-level or repeated misuse across multiple files. |
| **Cosmetic** | Visual or minor consistency issues. Fix last. |

---

## 11. Deliver the Final Output

Produce the following deliverables:

1. **Executive audit summary** — High-level overview of codebase health.
2. **Severity breakdown** — Count and list of findings per severity level.
3. **Refactor roadmap** — Ordered plan for resolving all issues.
4. **Separated issue lists:**
   - Framework issues (Symbols-level) in symbols-feedback.md
   - Project issues (implementation-level) in project-feedback.md

Enforce full DOMQL v3 purity across the entire codebase. No exceptions.

**CRITICAL: There is NO concept of "known debt", "accepted violations", or "technical debt exceptions" in Symbols audits. Every violation MUST be fixed. Never label a violation as "known debt" or suggest it can be deferred. If the audit finds a Rule 30 violation (direct DOM manipulation), it must be rewritten using DOMQL declarative syntax — not acknowledged and kept. The same applies to ALL rules (27-33). Zero tolerance.**
