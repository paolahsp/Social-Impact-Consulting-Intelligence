# Git Parallel Work

Recommended branches:

- Paola: `feature/research-evidence-engine`
- Gretel: `feature/operations-transformation-engine`
- Integration: `integration/project3`
- Main: protected conceptual release branch

## Paola Primary Files

- `workflows/skeletons/20_CONTEXT_RESEARCH_ORCHESTRATOR.json`
- `workflows/skeletons/21_WEB_SEARCH.json`
- `workflows/skeletons/22_WEBSITE_EXTRACTION.json`
- `workflows/skeletons/23_DOCUMENT_PUBLIC_DATA_RESEARCH.json`
- `workflows/skeletons/24_NEWS_EXTERNAL_CONTEXT.json`
- `workflows/skeletons/30_EVIDENCE_PIPELINE.json`
- `workflows/skeletons/40_RAG_RETRIEVAL_PIPELINE.json`
- `workflows/skeletons/51_REVENUE_RESILIENCE_AGENT.json`
- `workflows/skeletons/52_IMPACT_EVIDENCE_AGENT.json`
- `workflows/skeletons/54_EVIDENCE_GAP_RESEARCH.json`

## Gretel Primary Files

- `workflows/skeletons/53_OPERATIONS_CX_AGENT.json`
- `workflows/skeletons/60_TRANSFORMATION_ORCHESTRATOR.json`
- `workflows/skeletons/61_HYPOTHESIS_BUILDER.json`
- `workflows/skeletons/62_ROOT_CAUSE_DIAGNOSIS.json`
- `workflows/skeletons/63_ACTION_DESIGN.json`
- `workflows/skeletons/64_KPI_DESIGN.json`
- `workflows/skeletons/65_CLIENT_VALIDATION_QUESTIONS.json`
- `workflows/skeletons/66_90_DAY_ROADMAP.json`
- `workflows/skeletons/70_REPORT_QA_DELIVERY.json`

## Shared Files Requiring Coordination

- `contracts/*`
- `fixtures/*`
- `docs/TRACK_INTEGRATION_CONTRACT.md`
- `workflows/skeletons/00_MAIN_ORCHESTRATOR.json`
- `workflows/skeletons/10_INTAKE_AND_ORG_RESOLVER.json`
- `workflows/skeletons/50_ANALYSIS_ORCHESTRATOR.json`
- `workflows/skeletons/99_GLOBAL_ERROR_HANDLER.json`
- `scripts/validate_n8n_skeletons.py`
- `scripts/validate_fixtures.py`

## Contract Discipline

Contracts may not be changed unilaterally. If a workflow needs a contract change, document the proposed change, update fixtures, run validation, and merge through `integration/project3`.

## Integration Flow

1. Paola and Gretel work on their own branches.
2. Each branch keeps fixtures passing locally.
3. Contract-impacting changes are discussed before implementation.
4. Merge Paola and Gretel into `integration/project3`.
5. Run `python scripts\validate_n8n_skeletons.py` and `python scripts\validate_fixtures.py`.
6. Import into n8n only after validation passes.

Do not perform destructive branch operations automatically. Branch creation and protection can happen later when the repository is under active Git management.

