# Architecture Freeze

Architecture version: v1

Primary stack: n8n

Freeze status: frozen for Phase 2 parallel configuration.

Validated baseline:

- 23 workflow skeleton JSON files.
- 11 JSON contract schemas.
- Paola and Gretel ownership tracks defined.
- Workflows remain inactive by default.
- APIs, agents, credentials, databases, RAG providers, storage targets, notifications, and live sub-workflow IDs remain intentionally unconfigured.

Phase 2 rule:

New product ideas go to `docs/FUTURE_BACKLOG.md`, not into the current workflow skeletons. The architecture may not be redesigned during Phase 2 unless a genuine technical blocker makes the frozen design impossible to configure.

Configured implementations may replace TODO logic inside their frozen workflow boundary, add a DEV test export, and document provider/runtime evidence. `23_DOCUMENT_PUBLIC_DATA_RESEARCH` follows this rule: it keeps the existing trigger and source/evidence handoff, reuses upstream candidates from workflows 21/22, and does not add a competing shared contract or new orchestrator.
