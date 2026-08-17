# Paola 54 - Evidence Gap Research

## Status

Repository-ready on 2026-08-13.

LIVE n8n verification is blocked in this Codex session because no n8n CLI, n8n API environment variables, or n8n connector tool are available. The repository exports are ready to import and wire through n8n database selectors, but no live workflow URL, DEV workflow URL, or live execution IDs can be truthfully recorded yet.

## Purpose

`54_EVIDENCE_GAP_RESEARCH` resolves a specific evidence gap only when additional public research can reasonably help. It is a controller, not a broad research workflow.

It answers:

Can this UNKNOWN reasonably be resolved with additional public research?

If yes, it creates a focused query, reuses `21_WEB_SEARCH`, validates whether returned sources are new and relevant, and returns the result for downstream re-evaluation.

If no, it preserves the UNKNOWN and marks it for client validation.

## Core Rules

Absence of public evidence is not evidence of absence.

If targeted research finds nothing, 54 returns:

`The evidence gap remains unresolved from the public sources reviewed.`

It does not conclude that the organization lacks the practice, data, method, or evidence.

Finding a URL is not the same thing as resolving a gap. Workflow 54 preserves:

- `new_sources`: newly discovered, relevant sources for downstream re-evaluation.
- `new_evidence`: empty unless a fact is genuinely attributable and validated.

The current implementation deliberately returns new sources, not gap-resolving evidence.

## Input

Workflow-local input shape:

```json
{
  "run_context": {},
  "sources": [],
  "evidence": [],
  "missing_evidence_request": {
    "gap_id": "GAP-001",
    "domain": "revenue_resilience",
    "question": "Can funding concentration be determined from additional public financial information?",
    "gap_type": "public_financial_information",
    "current_evidence_ids": [],
    "retry_count": 0,
    "max_retries": 1,
    "reason_for_retry": "Existing evidence does not show funding concentration."
  }
}
```

No new shared schema was introduced.

Required local fields:

- `gap_id`
- `domain`
- `question` or `description`
- `retry_count`
- `max_retries`
- `reason_for_retry`

## Answerability Logic

Publicly researchable signals include:

- annual reports;
- audited financial statements;
- public financial reports and Form 990 filings;
- public funding, grant, donor, and revenue information;
- impact reports;
- published outcome, methodology, indicator, KPI, and evaluation material;
- public partnerships;
- strategy documents;
- public program reach.

Generally non-public/private signals include:

- internal workflow ownership;
- internal handoffs;
- CRM configuration;
- staff workload;
- internal response times;
- unpublished KPI baselines;
- beneficiary-level private data;
- internal team sentiment;
- undocumented process friction.

If a gap looks private/internal, 54 does not call workflow 21 just to search broadly. It returns `unknown_preserved` with `requires_client_validation = true`.

## Retry Control

54 checks retry state before answerability or research.

If:

`retry_count >= max_retries`

then:

- `controlled_state = retry_exhausted`
- `research_attempted = false`
- `retry_count` is not incremented
- UNKNOWN is preserved
- client validation is required

When targeted research runs, 54 increments `retry_count` once and passes the targeted query to `21_WEB_SEARCH`.

No recursive uncontrolled search is implemented.

## Targeted Query Behavior

54 builds a focused query containing:

- organization identity;
- gap subject;
- source hint.

Example:

`GiveDirectly United States Can funding concentration be determined from additional public financial information public_financial_information audited statements annual report form 990`

The workflow passes this query to `21_WEB_SEARCH` through an Execute Sub-workflow node. It does not create a second DuckDuckGo or HTTP search implementation.

## Canvas Path

`START__SUB_WORKFLOW_TRIGGER`

-> `INPUT_CONTRACT__MISSING_EVIDENCE_REQUEST`

-> `DECISION__INVALID_INPUT`

-> `DECISION__RETRY_EXHAUSTED`

-> `CAN_PUBLIC_RESEARCH_ANSWER`

-> `DECISION__PUBLIC_ANSWERABLE`

Public-answerable branch:

`BUILD_TARGETED_QUERY`

-> `PREPARE_21_SEARCH_REQUEST`

-> `EXECUTE_SUBWORKFLOW__21_WEB_SEARCH`

-> `VALIDATE_NEW_SOURCE`

-> explicit terminal output.

Non-public/retry branches:

`MARK_UNKNOWN__...`

-> explicit terminal output.

## Output

The terminal output contains:

- `run_context`
- `missing_evidence_request`
- `controlled_state`
- `can_public_research_answer`
- `answerability_reason`
- `targeted_query`
- `query_strategy`
- `search_controlled_state`
- `new_sources`
- `new_evidence`
- `rejected_sources`
- `unknown_marker`
- `retry_count`
- `max_retries`
- `reason_for_retry`
- `research_attempted`
- `rerun_required`
- `rerun_domain`
- `requires_client_validation`
- `source_evidence_boundary`
- `errors`

Controlled states:

| State | Meaning |
| --- | --- |
| `new_source_found` | Targeted public research found at least one new relevant source |
| `unknown_preserved` | Gap is not reasonably answerable through public research |
| `no_new_evidence` | Targeted public research ran but found no new relevant source |
| `retry_exhausted` | Retry limit was already reached; no research attempted |
| `research_failure` | Workflow 21 failed |
| `invalid_input` | Required input fields were missing or invalid |

## DEV Workflow

`workflows/dev/DEV_PAOLA_54_EVIDENCE_GAP_TEST.json` contains three visible branches:

1. GiveDirectly answerable public financial gap.
2. Internal/non-public stakeholder application handoff gap.
3. Retry exhausted.

After import, each Execute Sub-workflow node must be linked to the stored `54_EVIDENCE_GAP_RESEARCH` workflow using the n8n database selector.

Inside workflow 54, `EXECUTE_SUBWORKFLOW__21_WEB_SEARCH` must be linked to the stored `21_WEB_SEARCH` workflow using the n8n database selector. The repository export intentionally contains no live workflow IDs.

## Repository Test A - Answerable Public Gap

Input gap:

`Can funding concentration be determined from additional public financial information?`

Targeted query:

`GiveDirectly United States Can funding concentration be determined from additional public financial information public_financial_information audited statements annual report form 990`

Repository-local output:

- file: `runs/paola_54_givedirectly_answerable_gap.json`
- source fixture for 21 result: `runs/paola_p0_givedirectly.json`
- `controlled_state`: `new_source_found`
- `research_attempted`: true
- `retry_count`: 1
- `max_retries`: 1
- `new_sources`: 5
- `new_evidence`: 0
- `rerun_required`: true
- `rerun_domain`: `revenue_resilience`

New targeted sources:

- `https://www.givedirectly.org/financials-by-year`
- `https://www.givedirectly.org/financials`
- `https://projects.propublica.org/nonprofits/organizations/271661997`
- `https://www.roundpaper.com/nonprofits/org/givedirectly-inc-271661997`
- `https://projects.propublica.org/nonprofits/display_audit/2024-12-GSAFAC-0000381190`

These are returned as sources for downstream re-evaluation, not as proof that funding concentration is resolved.

## Repository Test B - Non-Public Gap

Input gap:

`What happens internally after a stakeholder submits an application form?`

Repository-local output:

- file: `runs/paola_54_internal_gap.json`
- `controlled_state`: `unknown_preserved`
- `can_public_research_answer`: false
- `research_attempted`: false
- `requires_client_validation`: true
- `new_sources`: 0
- `new_evidence`: 0

No broad research was performed.

## Repository Test C - Retry Exhausted

Input:

- `retry_count`: 1
- `max_retries`: 1

Repository-local output:

- file: `runs/paola_54_retry_exhausted.json`
- `controlled_state`: `retry_exhausted`
- `research_attempted`: false
- `retry_count`: 1
- `new_sources`: 0
- `new_evidence`: 0
- UNKNOWN preserved

## Failure Handling

Repository-local empty-search simulation:

- file: `runs/paola_54_empty_search.json`
- `controlled_state`: `no_new_evidence`
- `research_attempted`: true
- `retry_count`: 1
- `new_sources`: 0
- `new_evidence`: 0
- `requires_client_validation`: true
- UNKNOWN preserved

No evidence is fabricated when workflow 21 returns no sources.

## Validation

Commands run:

```bash
python scripts/generate_n8n_skeletons.py
python scripts/configure_paola_54_evidence_gap_research.py
python scripts/paola_54_evidence_gap_test.py --write-runs
python scripts/validate_n8n_skeletons.py
python scripts/validate_fixtures.py
python scripts/validate_paola_p0_output.py runs/paola_p0_givedirectly.json
python scripts/validate_paola_p0_output.py runs/paola_p0_empty_search.json
python scripts/validate_paola_22_output.py runs/paola_22_givedirectly.json
python scripts/validate_paola_22_output.py runs/paola_22_invalid_website.json
python scripts/validate_paola_23_output.py runs/paola_23_givedirectly.json runs/paola_23_msf.json runs/paola_23_partial_success.json runs/paola_23_unsupported_document.json
python scripts/validate_paola_52_output.py runs/paola_52_givedirectly.json runs/paola_52_insufficient_evidence.json
python scripts/validate_paola_54_output.py runs/paola_54_givedirectly_answerable_gap.json runs/paola_54_internal_gap.json runs/paola_54_retry_exhausted.json runs/paola_54_empty_search.json
python -m compileall scripts
```

Current validation result:

```text
n8n skeleton validation PASSED
- workflows checked: 23
- contracts checked: 11
- docs checked: 17
- fixtures checked: 7
- dev workflows checked: 5

fixture validation PASSED
- fixtures checked: 7
- schemas loaded: 11

Paola P0 output validation PASSED for GiveDirectly and empty-search outputs.
Paola 22 output validation PASSED for GiveDirectly and invalid-website outputs.
Paola 23 output validation PASSED for GiveDirectly, MSF, partial-success, and unsupported-document outputs.
Paola 52 output validation PASSED for GiveDirectly and insufficient-evidence outputs.

Paola 54 output validation PASSED: runs\paola_54_givedirectly_answerable_gap.json
- controlled_state: new_source_found
- research_attempted: True
- new_sources: 5
- retry_count: 1/1

Paola 54 output validation PASSED: runs\paola_54_internal_gap.json
- controlled_state: unknown_preserved
- research_attempted: False
- new_sources: 0
- retry_count: 0/1

Paola 54 output validation PASSED: runs\paola_54_retry_exhausted.json
- controlled_state: retry_exhausted
- research_attempted: False
- new_sources: 0
- retry_count: 1/1

Paola 54 output validation PASSED: runs\paola_54_empty_search.json
- controlled_state: no_new_evidence
- research_attempted: True
- new_sources: 0
- retry_count: 1/1

compileall passed for scripts.
```

## Live n8n Verification

Blocked as of 2026-08-13 in this Codex session.

Checks performed:

- `Get-Command n8n` returned no installed CLI.
- `Get-ChildItem Env:` found no `N8N`, `WEBHOOK`, or `WORKFLOW` environment variables.
- Tool discovery did not surface an n8n connector.

Checks to perform in n8n:

1. Import/update `54_EVIDENCE_GAP_RESEARCH`.
2. Import/update `DEV_PAOLA_54_EVIDENCE_GAP_TEST`.
3. Link workflow 54 `EXECUTE_SUBWORKFLOW__21_WEB_SEARCH` to stored workflow 21 with the database selector.
4. Link DEV workflow Execute Sub-workflow nodes to stored workflow 54 with the database selector.
5. Execute:
   - GiveDirectly answerable public gap.
   - internal/non-public gap.
   - retry-exhausted gap.
6. Record real workflow IDs, URLs, and execution IDs here.

Do not mark this workflow LIVE VERIFIED until those executions are inspected.

## Limitations

- 54 is a deterministic controller and does not call an LLM.
- It reuses workflow 21 for web search and does not perform document extraction itself.
- New sources require downstream extraction/evidence processing before any gap can be considered resolved.
- Public researchability is conservative by design; private/internal gaps are preserved for client validation.
