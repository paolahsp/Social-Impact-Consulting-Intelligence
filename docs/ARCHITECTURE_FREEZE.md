# Architecture Freeze

Architecture version: v1

Primary stack: n8n

Freeze status: frozen for Phase 2 parallel configuration.

Validated baseline:

- Original frozen baseline: 23 workflow skeleton JSON files.
- 11 JSON contract schemas.
- Paola and Gretel ownership tracks defined.
- Workflows remain inactive by default.
- APIs, agents, credentials, databases, RAG providers, storage targets, notifications, and live sub-workflow IDs remain intentionally unconfigured.

Phase 2 rule:

New product ideas go to `docs/FUTURE_BACKLOG.md`, not into the current workflow skeletons. The architecture may not be redesigned during Phase 2 unless a genuine technical blocker makes the frozen design impossible to configure.

Branch-scoped integration exception: `71_INTELLECTUS_WEB_ADAPTER` adds an
inactive HTTP boundary around the unchanged 53 leaf. It does not redesign 53,
replace Paola's research workflows or change a shared JSON schema.
