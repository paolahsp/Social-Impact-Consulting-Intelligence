# Workflow 53 — Operations/CX n8n Import and Test

Scope: `53_OPERATIONS_CX_AGENT` and `DEV_GRETEL_53_OPERATIONS_CX_TEST` only.

Architecture v1 and all shared contracts remain unchanged. Workflow 53 is an
inactive leaf sub-workflow with no credentials or committed live workflow ID.

## Input

Workflow 53 consumes one canonical n8n item whose `json` value is the flat
Paola track handoff:

- `run_context`
- `sources[]`
- `evidence[]`
- `findings[]`
- `unknowns[]`
- `contradictions[]`
- `rag_metadata`

Only evidence whose explicit `domain` is `operations_cx` enters analysis.
Keyword overlap does not admit Revenue or Impact evidence.

## Visible execution path

```text
Evidence Input
-> Operations/CX Domain Filter
-> Journey Signal Extraction
-> Observed / Inferred / Hypothesis / Unknown Classification
-> Observed Finding Construction
-> Inferred / Unknown Finding Construction
-> Validation Hypothesis Construction
-> Collision-Free ID Assignment
-> Contract + Referential Validation
-> Leaf Findings Output
```

The leaf output is exactly:

```json
{
  "findings": []
}
```

Each finding conforms to `finding.schema.json`. Optional journey metadata is
permitted by the frozen schema's `additionalProperties: true` setting.

## Safety behavior

- Observed findings require supported, uncontradicted fact evidence.
- Inferred, hypothesis, unknown, contradicted, and insufficient-evidence paths
  require validation questions.
- Every emitted `evidence_id` must resolve to an actual Operations/CX evidence
  record in the input.
- Generated IDs use `F-OPS-NNN` and skip IDs already present upstream.
- Explicit upstream unknowns and contradiction state remain visible.
- Internal handoffs, assignment, qualification, follow-up, integration, and
  automation are never promoted to observed facts without evidence.
- The workflow produces no technology recommendation.

## Development composition test

Import in this order:

1. `workflows/skeletons/53_OPERATIONS_CX_AGENT.json`
2. `workflows/dev/DEV_GRETEL_53_OPERATIONS_CX_TEST.json`

In the DEV workflow, open `TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX` and select
the imported `53_OPERATIONS_CX_AGENT`. Keep the workflow inactive and run it
manually.

The DEV workflow uses the repository's Paola fixture, calls the 53 leaf, then
composes the returned Operations/CX findings with the original Paola envelope.
It asserts that:

- observed, unknown, and hypothesis findings are present;
- upstream run context, sources, evidence, unknowns, contradictions, and RAG
  metadata remain unchanged;
- finding IDs remain unique;
- evidence references resolve.

This is a development demonstration of the later 50/60 composition boundary.
It does not implement workflow 60 or change a shared contract.

## Repository validation

```bash
python3 -B scripts/configure_gretel_53_n8n_exports.py
python3 -B scripts/test_n8n_53_operations_cx.py
python3 -B scripts/validate_n8n_skeletons.py
python3 -B scripts/validate_fixtures.py
```

The offline test executes the JavaScript embedded in the exported workflow. It
is not live n8n verification. Live status must be recorded only after an actual
n8n execution.
