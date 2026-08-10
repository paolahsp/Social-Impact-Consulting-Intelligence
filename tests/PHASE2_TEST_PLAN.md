# Phase 2 Test Plan

## First Vertical Slice Acceptance Test

Input:

Fictional or approved NGO organization input.

Expected path:

```text
organization
-> real web search
-> source
-> evidence
-> RAG retrieval
-> revenue finding
-> hypothesis
-> diagnosis
-> action
-> KPI
-> validation question
-> final JSON
```

Acceptance criteria:

1. Search uses a real external capability.
2. At least one source is stored.
3. At least one evidence object references that source.
4. Evidence type is explicit.
5. RAG retrieves evaluation context.
6. Revenue assessment produces a structured finding.
7. Hypothesis does not become fact.
8. Recommendation traces back to finding/evidence.
9. KPI does not invent an unknown baseline.
10. Client question is neutral and specific.
11. Output validates against contracts.
12. No secrets are committed.

## Fixture-Based Preflight

Before live services are configured, use `fixtures/paola_track_output.json` as Gretel's input fixture and confirm that Gretel's transformation workflows can produce objects shaped like `fixtures/gretel_track_output.json`.

## Safety Checks

- No credentials in workflow JSON.
- No live Salesforce, WhatsApp, Telegram, CRM, or internal-data integrations.
- Unknown public evidence remains `unknown` or `requires_validation`.

