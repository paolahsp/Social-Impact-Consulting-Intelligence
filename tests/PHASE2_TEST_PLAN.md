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

## Workflow 60 Orchestration Tests

- Run `python3 scripts/test_n8n_60_transformation.py` to exercise workflow 60's input, applicability, merge, cumulative post-child guards, final six-collection gate, exact output, and controlled-failure behavior while calling the existing workflow 53 and 61-66 offline harnesses as child boundaries. The harness removes one previously produced collection at every 61-66 boundary and verifies the exact missing collection, failed child, completed workflows, and surviving partial state.
- Import `DEV_GRETEL_60_TRANSFORMATION_TEST` after linking workflow 60 to 53 and 61-66. Link its three current Execute Sub-workflow nodes to workflow 60; one manual execution must pass normal, insufficient-evidence, and controlled-child-failure branches.
- Repository validation is not live n8n validation. Record live success only after the DEV workflow and all nested executions complete successfully in the target n8n instance.

## Safety Checks

- No credentials in workflow JSON.
- No live Salesforce, WhatsApp, Telegram, CRM, or internal-data integrations.
- Unknown public evidence remains `unknown` or `requires_validation`.

## Intellectus Live Webhook

- Run `python scripts/test_n8n_71_intellectus_web_adapter.py` to validate the
  committed `INTELLECTUS_LIVE_WEBHOOK` export, canonical child workflow ID,
  `$json.valid` IF conditions, public request contract, final response
  validator and sanitized error paths.
- Treat execution 3015 and child execution 3016 as live n8n evidence, not
  replayable repository fixtures.
- Keep golden run 2935 intact.
