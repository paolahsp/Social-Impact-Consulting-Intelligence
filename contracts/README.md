# Contracts

These JSON Schemas define the shared data contracts for the n8n skeleton architecture.

- `run_context.schema.json`: canonical run and organization state.
- `source.schema.json`: public source metadata.
- `evidence.schema.json`: traceable claim record with fact/inference/hypothesis/unknown typing.
- `finding.schema.json`: structured specialist analysis finding.
- `hypothesis.schema.json`: public-data-first hypothesis with evidence IDs, confidence, validation requirement, and validation gap.
- `diagnosis.schema.json`: observed problem, likely cause, validated cause, or unknown.
- `validation_question.schema.json`: consultant-facing validation questions tied to findings or hypotheses.
- `kpi.schema.json`: KPI definition with baseline status and measurement method.
- `roadmap_action.schema.json`: 30/60/90 day action, validation, or discovery step.
- `recommendation.schema.json`: diagnosis, action, KPI, priority, and review flag.
- `final_package.schema.json`: canonical Pre-Engagement Diagnostic Pack.

Contract rules:

- A hypothesis must never silently become a fact.
- Missing public evidence should be represented as `unknown` or `insufficient_evidence`.
- Public evidence should normally create `likely_cause`, not `validated_cause`.
- Baselines must not be invented; use `baseline_status: "unknown"` when needed.
- Recommendations must trace back to finding IDs and, through findings, to evidence IDs.
- Validation questions must be specific, neutral, non-leading, and tied to a finding or hypothesis.
- JSON is the canonical final output format; Markdown, HTML, and PDF are future exports.
