# Phase 2 Configuration Matrix

P0 = vertical slice. P1 = required expansion. P2 = hardening.

| Workflow | Owner | Priority | Needs API? | Needs LLM? | Needs RAG? | Needs storage? | Depends on | Phase 2 status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00_MAIN_ORCHESTRATOR | Shared | P2 | No | No | No | No | 10,20,30,40,50,60,70 | Frozen skeleton; link after track work |
| 10_INTAKE_AND_ORG_RESOLVER | Shared | P1 | No | No | No | Optional | None | Ready for input validation |
| 20_CONTEXT_RESEARCH_ORCHESTRATOR | Paola | P1 | No | Optional | No | No | 21,22,23,24 | Ready for channel linking |
| 21_WEB_SEARCH | Paola | P0 | Yes | No | No | Optional | 10 | n8n-native repo-ready with HTTP Request and branch paths |
| 22_WEBSITE_EXTRACTION | Paola | P1 | Yes | Optional | No | Optional | 10 | LIVE n8n VERIFIED with GiveDirectly success and controlled invalid-domain failure |
| 23_DOCUMENT_PUBLIC_DATA_RESEARCH | Paola | P1 | Yes | No | No | No | 10,21,22 | LIVE n8n VERIFIED: official GiveDirectly/MSF documents, partial success, and unsupported-document branch |
| 24_NEWS_EXTERNAL_CONTEXT | Paola | P2 | Yes | No | No | Optional | 10 | Placeholder only |
| 30_EVIDENCE_PIPELINE | Paola | P0 | No | Future optional | No | Optional | 20 or fixtures | n8n-native repo-ready deterministic P0 evidence extraction |
| 40_RAG_RETRIEVAL_PIPELINE | Paola | P0 | No | No | Local corpus | No | 30 | n8n-native repo-ready transparent Revenue Resilience retrieval |
| 50_ANALYSIS_ORCHESTRATOR | Shared | P1 | No | No | No | No | 51,52,53 | Link specialists after track work |
| 51_REVENUE_RESILIENCE_AGENT | Paola | P0 | No | Future optional | Yes | No | 30,40 | n8n-native repo-ready deterministic P0 revenue finding |
| 52_IMPACT_EVIDENCE_AGENT | Paola | P1 | No | Yes | Yes | No | 30,40 | Required expansion |
| 53_OPERATIONS_CX_AGENT | Gretel | P1 | No | Yes | Yes | No | 30,40 | Required expansion |
| 54_EVIDENCE_GAP_RESEARCH | Paola | P2 | Yes | Optional | No | Optional | 30 | Hardening |
| 60_TRANSFORMATION_ORCHESTRATOR | Gretel | P1 | No | No | No | No | 61,62,63,64,65,66 | Link child workflows |
| 61_HYPOTHESIS_BUILDER | Gretel | P0 | No | Yes | Optional | No | Paola output fixture | P0 transformation |
| 62_ROOT_CAUSE_DIAGNOSIS | Gretel | P0 | No | Yes | Optional | No | 61 | P0 transformation |
| 63_ACTION_DESIGN | Gretel | P0 | No | Yes | Optional | No | 62 | P0 transformation |
| 64_KPI_DESIGN | Gretel | P0 | No | Yes | Optional | No | 63 | P0 transformation |
| 65_CLIENT_VALIDATION_QUESTIONS | Gretel | P0 | No | Yes | No | No | 61,62 | Core MVP workflow |
| 66_90_DAY_ROADMAP | Gretel | P0 | No | Yes | Optional | No | 63,64,65 | P0 transformation |
| 70_REPORT_QA_DELIVERY | Gretel / Shared integration | P0 | No | Optional | No | Yes | Paola + Gretel outputs | Shared P0 after tracks work |
| 99_GLOBAL_ERROR_HANDLER | Shared | P2 | No | No | No | Optional | All workflows | Hardening |
