/**
 * ESLint flat config — single source of lint truth for this repo.
 *
 * Minimal on purpose: an ignores block only — no rules are invented here.
 * Matches the monorepo-wide approach (flat config everywhere; run via
 * `npm run lint`, which sets ESLINT_USE_FLAT_CONFIG=true so the same
 * script works on eslint 8, 9, and 10).
 */

/** @type {import('eslint').Linter.Config[]} */
export default [
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/.parcel-cache/**'
    ]
  }
]
