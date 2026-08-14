# Intellectus environment baseline

## Purpose

This document records the Phase 1 technical baseline. The phase validates the
application foundation without reconstructing the ten product experiences.

## Stack and installed versions

| Package | Version |
| --- | --- |
| React | 19.2.8 |
| React DOM | 19.2.8 |
| TypeScript | 6.0.3 |
| Vite | 8.2.1 |
| Tailwind CSS | 4.3.3 |
| `@tailwindcss/vite` | 4.3.3 |
| React Router DOM | 7.18.2 |
| Lucide React | 1.31.0 |
| Zod | 4.4.3 |
| Inter Variable | 5.3.0 |
| Newsreader Variable | 5.3.0 |
| Vitest | 4.1.10 |
| jsdom | 30.0.1 |
| Testing Library React | 16.3.2 |
| Testing Library jest-dom | 7.0.1 |
| axe-core | 4.13.0 |

## Configuration decisions

- Tailwind v4 runs through the official Vite plugin and the CSS-first
  `@import "tailwindcss"` entry point. There is no `tailwind.config.js`.
- Inter Variable and Newsreader Variable are bundled locally through Fontsource.
- Initial color, typography, spacing, radius, shadow and content-width tokens
  live in `src/styles/index.css` using `@theme` and CSS custom properties.
- Zod schemas are the model source of truth. Public TypeScript types are inferred
  with `z.infer` rather than maintained independently.
- Relationships between analytical records use stable IDs and are checked at the
  aggregate `Diagnostic` boundary.
- The repository contract is asynchronous so a future data adapter can replace
  the fixture without changing the page contract. The fixture implementation has
  no network delay, browser persistence or endpoint.
- React Router is initialized with one catch-all baseline route. Product routes
  will be defined in a later phase.
- Automated accessibility coverage uses axe-core in jsdom. The color-contrast
  rule is disabled in that environment because jsdom has no canvas rendering;
  contrast remains a required manual browser check. This automation is a
  regression check, not proof of WCAG 2.2 AA compliance.

## Structure created

```text
src/
  app/                 Application entry component and tests
  components/
    layout/            Minimal brand header
    ui/                EpistemicBadge and tests
  fixtures/            One validated methodological diagnostic
  pages/               Technical baseline page
  repositories/        Repository contract and fixture implementation
  schemas/             Zod domain schemas and integrity tests
  styles/              Tailwind entry point, tokens and global styles
  test/                Vitest setup
  types/               Types inferred from Zod schemas
docs/
  ENVIRONMENT_BASELINE.md
```

## Implemented

- Local brand typography and initial design tokens.
- Tailwind v4 compilation.
- `EpistemicStatus`, `ReviewStatus`, `EvidenceSource`, `AnalyticalItem` and the
  root `Diagnostic` aggregate.
- Validation for duplicate IDs, missing source references, missing analytical
  references, self-references and demo-source export eligibility.
- A single fixture containing one demo public source, public-evidence record,
  unknown, hypothesis and unapproved recommendation.
- `DiagnosticRepository` and `FixtureDiagnosticRepository`.
- A semantic baseline page with skip link and loading, success and error states.
- Unit, component, repository and automated accessibility checks.

## Not implemented

- The ten product screens, sidebar, drawers or final navigation hierarchy.
- Client evidence or claims about any real organization.
- Authentication, API calls, endpoints, persistence or n8n workflows.
- Final responsive behavior, visual QA or production monitoring.
- Full WCAG 2.2 AA verification.

The source named `Demo source — not client evidence` is a local methodological
fixture. Its `clientEvidenceEligible` value is false, the schema prevents a demo
source from being marked eligible, and it must never be included in a client
evidence export.

## Commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the local Vite development server |
| `npm run lint` | Run ESLint |
| `npm run typecheck` | Run TypeScript project checks without emitting app code |
| `npm run test` | Run Vitest in watch mode |
| `npm run test:run` | Run the test suite once |
| `npm run build` | Type-check and build the production bundle |
| `npm run preview` | Preview a completed production build |

## Manual checks pending

- Keyboard-only navigation and focus order in a real browser.
- Screen-reader announcements with VoiceOver or an equivalent assistive tool.
- Color contrast confirmation against final product states and content.
- Reflow and zoom checks at 200% and 400%.
- Responsive inspection at the agreed mobile, tablet and desktop breakpoints.
- Reduced-motion behavior in a real browser.

These checks must be repeated as the product interface is introduced in Phase 2.
