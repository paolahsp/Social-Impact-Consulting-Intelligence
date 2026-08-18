# Intellectus

Intellectus — Social Impact Intelligence turns available public information
into a focused, consultant-reviewed starting point for the next client
conversation.

## Guided demo

The application supports five session-only steps:

1. provide the organization and conversation objective;
2. review a concise diagnostic overview;
3. select questions for the client;
4. review a bounded next step, measures and validation sequence;
5. review and mark the conversation brief ready.

The demo uses local sample material. It does not perform remote research and
does not establish that any public claim is approved for client use. Starting
information, selected questions, the chosen next step and review status reset
when the page reloads.

## Commands

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run test:run
npm run guardrails
npm run build
npm run verify
npm run preview
```

`npm run verify` runs lint, strict type checking, tests, runtime guardrails and
the production build.

## Workflow adapter

Set `VITE_DIAGNOSTIC_WEBHOOK_URL` to activate the validated workflow adapter.
Leave it unset to use the explicit local demo. Never put tokens in `VITE_*`
variables. See [the integration contract](docs/N8N_INTEGRATION_CONTRACT.md) for
the request/response boundary and production limitations.

## Current limits

- The public workflow IDs are documented; no credential or secret is committed.
- The live webhook delegates research and transformation to
  `DEV_PROJECT3_END_TO_END`.
- Direct browser-to-workflow deployment cannot protect a secret; production
  requires an authenticated backend/BFF or equivalent gateway.
- KPI baselines and targets are not established.
- Automated accessibility checks do not establish WCAG conformance. Browser,
  assistive-technology, zoom and reflow checks remain manual QA work.

A secure consultant workspace with authentication, saved diagnostics, document
storage and history belongs to a future persistence phase.

See [Information Architecture](docs/INFORMATION_ARCHITECTURE.md), the
[UX QA Checklist](docs/UX_QA_CHECKLIST.md), and the
[n8n Integration Contract](docs/N8N_INTEGRATION_CONTRACT.md).
