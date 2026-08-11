# Paola 52 - Impact Evidence

## Status

Repository-ready on 2026-08-11.

LIVE n8n verification is blocked in this Codex session because no n8n CLI, n8n API environment variables, or n8n connector tool are available. The repository exports are ready to import, but no live workflow URL, DEV workflow URL, or live execution IDs can be truthfully recorded yet.

## Purpose

`52_IMPACT_EVIDENCE_AGENT` analyzes structured public evidence about how a social-impact organization describes and demonstrates its impact. It helps a consultant separate:

- activities;
- outputs and reach;
- outcomes;
- long-term impact;
- public impact claims;
- indicators;
- unknowns and evidence limitations.

It does not decide whether an NGO is good or bad. It does not invent internal practices, implementation recommendations, baselines, sample sizes, methods, or root causes.

## Evidence Rules

Activity, output, outcome, and impact are distinct.

A public statement by the organization is a claim or signal, not automatic proof that the stated impact occurred.

Absence of public evidence is not evidence of absence. The workflow uses language such as "not identified in the public sources reviewed" and "could not be determined from the public evidence reviewed."

RAG context may explain conceptual distinctions, but it must not add organization-specific facts.

## Input

The workflow accepts one item containing:

```json
{
  "run_context": {},
  "sources": [],
  "evidence": [],
  "documents": [],
  "rag_context": {}
}
```

`documents[]` is optional and exists to consume the structured output produced by `23_DOCUMENT_PUBLIC_DATA_RESEARCH`. When the evidence ledger already contains impact-related evidence, workflow 52 filters it. When workflow 23 provides structured document sections, workflow 52 can derive traceable impact evidence records from `section_type = "impact"` sections only.

Workflow 52 does not perform broad web search.

## Taxonomy

Bounded classification values:

- `activity`
- `output`
- `outcome`
- `impact`
- `indicator`
- `unknown`
- `impact_claim`
- `impact_evidence`

The workflow uses `impact_claim` when a mission or impact-oriented statement is publicly stated but the cited public evidence does not demonstrate the impact occurred.

## Canvas Path

`START__SUB_WORKFLOW_TRIGGER`

-> `INPUT_CONTRACT`

-> `DECISION__INPUT_FAILURE`

-> `FILTER_IMPACT_EVIDENCE`

-> `DECISION__INSUFFICIENT_EVIDENCE`

-> `CLASSIFY_IMPACT_LEVEL`

-> `ASSESS_EVIDENCE_CHARACTERISTICS`

-> `DETECT_UNKNOWNS`

-> `BUILD_FINDINGS`

-> `TRACEABILITY_CHECK`

-> `DECISION__TRACEABILITY_FAILURE`

-> explicit terminal output.

The insufficient-evidence branch has its own visible unknown/finding/traceability/output path.

## Output

The terminal output contains:

- `run_context`
- `controlled_state`
- `impact_taxonomy`
- `sources`
- original `evidence`
- `impact_evidence`
- `evidence_characteristics`
- `findings`
- `unknowns`
- `contradictions`
- `rag_metadata`
- `guardrails`
- `errors`

Material findings reuse `finding.schema.json` fields:

- `finding_id`
- `domain = impact_evidence`
- `finding`
- `evidence_ids`
- `finding_type`
- `confidence`
- `requires_validation`
- `validation_question`

## Controlled States

| State | Meaning |
| --- | --- |
| `success` | Impact-related structured evidence was identified and traceable findings were built |
| `insufficient_evidence` | Structured inputs did not contain enough impact-related public evidence for meaningful findings |
| `request_failure` | Input or traceability validation failed |

## GiveDirectly Repository Result

Source fixture:

- `runs/paola_23_givedirectly.json`
- live workflow 23 sub-execution: `1397`
- source: official GiveDirectly FY2023 audited financial statements extracted by workflow 23

Repository-local 52 output:

- file: `runs/paola_52_givedirectly.json`
- controlled state: `success`
- impact evidence records: 4
- findings: 5
- unknowns: 6

Evidence classifications:

| Evidence ID | Classification | Trace |
| --- | --- | --- |
| `EV-IMP-001` | `impact_claim` | `SRC-DOC-001` |
| `EV-IMP-002` | `activity` | `SRC-DOC-001` |
| `EV-IMP-003` | `output` | `SRC-DOC-001` |
| `EV-IMP-004` | `output` | `SRC-DOC-001` |

Findings include:

- Program activities or service delivery steps are publicly described.
- Public reporting reviewed contains output or reach signals.
- An impact-oriented claim or mission statement is publicly stated, but it is not treated as proof that long-term impact occurred.
- Public reporting reviewed emphasizes activities, outputs, or claims more clearly than measured outcomes or long-term impact evidence.
- Some impact evidence characteristics remain unknown from the public sources reviewed.

Unknowns include:

- Outcome evidence was not identified in the public sources reviewed.
- Long-term impact evidence was not identified in the public sources reviewed.
- Methodology visibility could not be determined from the public evidence reviewed.
- Baseline visibility could not be determined from the public evidence reviewed.
- Denominator or sample visibility could not be determined from the public evidence reviewed.
- Target visibility could not be determined from the public evidence reviewed.

## Insufficient-Evidence Repository Result

Source fixture:

- `runs/paola_p0_givedirectly.json`
- revenue-focused P0 evidence only

Repository-local 52 output:

- file: `runs/paola_52_insufficient_evidence.json`
- controlled state: `insufficient_evidence`
- impact evidence records: 0
- findings: 1 unknown finding
- unknowns: 1

The insufficient-evidence output does not invent outcomes, impact, methodology, baselines, or negative conclusions.

## DEV Workflow

`workflows/dev/DEV_PAOLA_52_IMPACT_EVIDENCE_TEST.json` contains two visible branches:

1. GiveDirectly structured document evidence.
2. Insufficient-evidence input.

After import, each Execute Sub-workflow node must be linked to the stored `52_IMPACT_EVIDENCE_AGENT` workflow using the n8n database selector. The repository export intentionally contains no live workflow ID.

## Validation

Commands run:

```bash
python scripts/generate_n8n_skeletons.py
python scripts/configure_paola_52_impact_evidence.py
python scripts/paola_52_impact_evidence_test.py --write-runs
python scripts/validate_n8n_skeletons.py
python scripts/validate_fixtures.py
python scripts/validate_paola_p0_output.py runs/paola_p0_givedirectly.json
python scripts/validate_paola_p0_output.py runs/paola_p0_empty_search.json
python scripts/validate_paola_22_output.py runs/paola_22_givedirectly.json
python scripts/validate_paola_22_output.py runs/paola_22_invalid_website.json
python scripts/validate_paola_23_output.py runs/paola_23_givedirectly.json runs/paola_23_msf.json runs/paola_23_partial_success.json runs/paola_23_unsupported_document.json
python scripts/validate_paola_52_output.py runs/paola_52_givedirectly.json runs/paola_52_insufficient_evidence.json
python -m compileall scripts
```

Current validation results:

```text
n8n skeleton validation PASSED
- workflows checked: 23
- contracts checked: 11
- docs checked: 16
- fixtures checked: 7
- dev workflows checked: 4

fixture validation PASSED
- fixtures checked: 7
- schemas loaded: 11

Paola P0 output validation PASSED
- controlled_state: ok
- sources: 5
- evidence: 5
- findings: 1
- rag_contexts: 3

Paola P0 output validation PASSED
- controlled_state: empty_search
- sources: 0
- evidence: 1
- findings: 1
- rag_contexts: 3

Paola 22 output validation PASSED: runs\paola_22_givedirectly.json
- controlled_state: success
- pages_attempted: 8
- sources: 6
- errors: 2

Paola 22 output validation PASSED: runs\paola_22_invalid_website.json
- controlled_state: request_failure
- pages_attempted: 8
- sources: 0
- errors: 8

Paola 23 output validation PASSED for GiveDirectly, MSF, partial success, and unsupported-document outputs.

Paola 52 output validation PASSED: runs\paola_52_givedirectly.json
- controlled_state: success
- impact_evidence: 4
- findings: 5
- unknowns: 6
Paola 52 output validation PASSED: runs\paola_52_insufficient_evidence.json
- controlled_state: insufficient_evidence
- impact_evidence: 0
- findings: 1
- unknowns: 1

compileall passed for scripts after rerun with a 30-second timeout.
```

## Live n8n Verification

Blocked as of 2026-08-11 in this Codex session.

Checks performed:

- `Get-Command n8n` returned no installed CLI.
- `Get-ChildItem Env:` found no `N8N`, `WEBHOOK`, or `WORKFLOW` environment variables.
- Tool discovery did not surface an n8n connector.

Required next live steps:

1. Import or update `workflows/skeletons/52_IMPACT_EVIDENCE_AGENT.json`.
2. Import or update `workflows/dev/DEV_PAOLA_52_IMPACT_EVIDENCE_TEST.json`.
3. Link DEV Execute Sub-workflow nodes to the stored workflow 52 through the n8n database selector.
4. Execute GiveDirectly and insufficient-evidence branches.
5. Copy exact terminal-node outputs to `runs/paola_52_*.json`.
6. Record live workflow IDs, URLs, and execution IDs here.

## Limitations

- Current 52 implementation is deterministic and does not call an LLM.
- It relies on structured upstream objects from workflows 23/30/40; it does not discover new sources.
- The GiveDirectly repository fixture comes from an audited financial statement, so it supports activity, output, and claim classification but not public outcome or long-term impact evidence.
- Unknowns are preserved as public-evidence limitations and do not reduce an organizational quality score.
