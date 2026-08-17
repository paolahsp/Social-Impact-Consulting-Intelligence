# Track Integration Contract

This document defines the handoff between Paola's research/evidence track and Gretel's operations/transformation track. It does not create new competing schemas; it composes the existing contracts.

## Paola Track Input

Paola starts from the organization/run context produced by `10_INTAKE_AND_ORG_RESOLVER`.

```json
{
  "run_id": "RUN-FICTIONAL-001",
  "organization": {
    "name": "Fictional River Learning Collective",
    "website": "https://fictional-river-learning.example.org",
    "country": "Germany",
    "mission_area": "youth education"
  },
  "current_challenge": "Preparing for a pre-engagement diagnostic workshop",
  "status": "created",
  "started_at": "2026-08-09T09:00:00Z",
  "errors": []
}
```

## Paola Track Output

Paola returns one object with these fields:

- `run_context`: `run_context.schema.json`
- `sources`: array of `source.schema.json`
- `evidence`: array of `evidence.schema.json`
- `findings`: array of `finding.schema.json`
- `unknowns`: array of evidence gaps or unavailable public-data areas
- `contradictions`: array of contradiction summaries linked to evidence IDs
- `rag_metadata`: retrieval metadata needed by downstream analysis

### Workflow 23 document handoff

`23_DOCUMENT_PUBLIC_DATA_RESEARCH` reuses the existing source contract. It adds document metadata through permitted additional source properties rather than creating a competing shared schema. Its direct sub-workflow output contains `run_context`, `sources`, `documents`, `controlled_state`, and `errors`.

Each `documents[]` entry references exactly one `sources[].source_id`. The downstream `30_EVIDENCE_PIPELINE` must convert only attributable document statements into evidence; workflow 23 does not create consulting conclusions. `partial_success` preserves successful sources and documents while exposing failed candidates in `errors`.

## Gretel Track Input

Gretel receives the exact Paola output shape. This lets Gretel configure transformation workflows from fixtures while Paola is still connecting live research APIs.

## Gretel Track Output

Gretel returns one object with these fields:

- `hypotheses`: array of `hypothesis.schema.json`
- `diagnoses`: array of `diagnosis.schema.json`
- `recommendations`: array of `recommendation.schema.json`
- `kpis`: array of `kpi.schema.json`
- `validation_questions`: array of `validation_question.schema.json`
- `roadmap_actions`: array of `roadmap_action.schema.json`

## Shared Final Output

The shared final output is `final_package.schema.json`.

## Complete JSON Example

```json
{
  "paola_output": {
    "run_context": {
      "run_id": "RUN-FICTIONAL-001",
      "organization": {
        "name": "Fictional River Learning Collective",
        "website": "https://fictional-river-learning.example.org",
        "country": "Germany",
        "mission_area": "youth education"
      },
      "current_challenge": "Preparing for a pre-engagement diagnostic workshop",
      "status": "analyzing",
      "started_at": "2026-08-09T09:00:00Z",
      "errors": []
    },
    "sources": [
      {
        "source_id": "SRC-001",
        "title": "Fictional River Learning Collective Volunteer Page",
        "url": "https://fictional-river-learning.example.org/volunteer",
        "source_type": "official_website",
        "publisher": "Fictional River Learning Collective",
        "publication_date": null,
        "retrieved_at": "2026-08-09T09:10:00Z",
        "authority_level": "official",
        "freshness": "current",
        "is_official": true
      }
    ],
    "evidence": [
      {
        "evidence_id": "EV-001",
        "run_id": "RUN-FICTIONAL-001",
        "claim": "Volunteer applications are collected through a public website form.",
        "source_ids": ["SRC-001"],
        "domain": "operations_cx",
        "evidence_type": "fact",
        "confidence": 0.86,
        "status": "supported",
        "contradiction_ids": [],
        "requires_validation": false
      }
    ],
    "findings": [
      {
        "finding_id": "F-001",
        "domain": "operations_cx",
        "finding": "The public volunteer journey includes an online application form.",
        "evidence_ids": ["EV-001"],
        "finding_type": "observed",
        "confidence": 0.82,
        "requires_validation": false,
        "validation_question": null
      }
    ],
    "unknowns": [
      {
        "unknown_id": "UNK-001",
        "domain": "operations_cx",
        "description": "The internal follow-up process after volunteer form submission is not publicly visible."
      }
    ],
    "contradictions": [],
    "rag_metadata": {
      "retrieval_run_id": "RAG-FICTIONAL-001",
      "domains": ["revenue_resilience", "operations_cx"],
      "retrieved_context_ids": ["FRAMEWORK-REV-001", "FRAMEWORK-OPS-001"]
    }
  },
  "gretel_output": {
    "hypotheses": [
      {
        "hypothesis_id": "HYP-001",
        "run_id": "RUN-FICTIONAL-001",
        "domain": "operations_cx",
        "evidence_ids": ["EV-001"],
        "finding_ids": ["F-001"],
        "hypothesis": "Volunteer follow-up may rely on manual handoffs after form submission.",
        "confidence": 0.48,
        "requires_validation": true,
        "validation_gap": "Public sources do not describe the internal follow-up process."
      }
    ],
    "diagnoses": [
      {
        "diagnosis_id": "DX-001",
        "domain": "operations_cx",
        "diagnosis_type": "likely_cause",
        "statement": "The volunteer journey may contain manual coordination steps that should be validated with staff.",
        "finding_ids": ["F-001"],
        "hypothesis_ids": ["HYP-001"],
        "evidence_ids": ["EV-001"],
        "confidence": 0.45,
        "requires_validation": true
      }
    ],
    "recommendations": [
      {
        "recommendation_id": "REC-001",
        "finding_ids": ["F-001"],
        "diagnosis_ids": ["DX-001"],
        "diagnosis": "Volunteer follow-up may depend on manual handoffs.",
        "action": "Map the volunteer intake handoff during the first client workshop before recommending automation.",
        "priority": "medium",
        "kpi": {
          "name": "Volunteer follow-up time",
          "baseline": null,
          "baseline_status": "unknown",
          "target": null,
          "timeframe": "After baseline is confirmed",
          "measurement_method": "Review timestamp from form submission to first staff response"
        },
        "confidence": 0.46,
        "requires_human_review": true
      }
    ],
    "kpis": [
      {
        "name": "Volunteer follow-up time",
        "baseline": null,
        "baseline_status": "unknown",
        "target": null,
        "timeframe": "After baseline is confirmed",
        "measurement_method": "Review timestamp from form submission to first staff response"
      }
    ],
    "validation_questions": [
      {
        "question_id": "Q-001",
        "finding_ids": ["F-001"],
        "hypothesis_ids": ["HYP-001"],
        "question": "What happens internally after someone submits the volunteer form?",
        "purpose": "Validate whether follow-up depends on manual handoffs.",
        "domain": "operations_cx",
        "priority": "high"
      }
    ],
    "roadmap_actions": [
      {
        "roadmap_action_id": "RA-001",
        "time_bucket": "30_days",
        "action": "Validate the volunteer follow-up process during the client workshop.",
        "action_type": "validation",
        "recommendation_ids": ["REC-001"],
        "hypothesis_ids": ["HYP-001"],
        "validation_question_ids": ["Q-001"]
      }
    ]
  }
}
```
