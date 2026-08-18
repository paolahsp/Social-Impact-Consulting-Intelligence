# Workflow Map

All workflows are skeletons, inactive by default, and intentionally use TODO placeholders for APIs, agents, storage, RAG, and sub-workflow links.

| Workflow | Owner | Purpose | Input | Output | Dependencies | Future configuration |
| --- | --- | --- | --- | --- | --- | --- |
| 00_MAIN_ORCHESTRATOR | SHARED | Coordinates full run | Initial run request | Final package | 10,20,30,40,50,60,70 | Sub-workflow links |
| 10_INTAKE_AND_ORG_RESOLVER | SHARED | Normalizes intake and run context | Organization request | Run context | None | Organization resolver |
| 20_CONTEXT_RESEARCH_ORCHESTRATOR | PAOLA TRACK A | Plans and coordinates public research | Run context | Context pack | 21,22,23,24 | Research planner plus channel links |
| 21_WEB_SEARCH | PAOLA TRACK A | Public web discovery | Research task | Sources | None | Web search API |
| 22_WEBSITE_EXTRACTION | PAOLA TRACK A | Official site extraction | Official URL | Sources/content | None | Extraction API/provider |
| 23_DOCUMENT_PUBLIC_DATA_RESEARCH | PAOLA TRACK A | Public reports and registry data | Document/public data task | Sources/documents | None | Fetch/extraction tools |
| 24_NEWS_EXTERNAL_CONTEXT | PAOLA TRACK A | Recent external context | News task | Sources | None | News/search API |
| 30_EVIDENCE_PIPELINE | PAOLA TRACK A | Turns context into traceable evidence | Context pack | Evidence ledger | 54 optional later | Evidence extraction agent/storage |
| 40_RAG_RETRIEVAL_PIPELINE | PAOLA TRACK A | Retrieves framework context | Evidence/domain | RAG context | Knowledge base | Vector store |
| 50_ANALYSIS_ORCHESTRATOR | SHARED | Dispatches specialist analysis | Evidence + RAG | Findings | 51,52,53 | Sub-workflow links |
| 51_REVENUE_RESILIENCE_AGENT | PAOLA TRACK A | Revenue resilience analysis | Revenue evidence/RAG | Revenue findings | 40 | Revenue agent |
| 52_IMPACT_EVIDENCE_AGENT | PAOLA TRACK A | Impact and evidence analysis | Impact evidence/RAG | Impact findings | 40 | Impact agent |
| 53_OPERATIONS_CX_AGENT | GRETEL TRACK B | Operations and CX analysis | Operations evidence/RAG | Operations findings | 40 | Operations/CX agent |
| 54_EVIDENCE_GAP_RESEARCH | PAOLA TRACK A | Targeted evidence gap research | Missing evidence request | New evidence/unknown | Research providers | Targeted research API |
| 60_TRANSFORMATION_ORCHESTRATOR | GRETEL TRACK B | Coordinates transformation child workflows | Paola handoff | Gretel Track output | 53,61,62,63,64,65,66 | Sub-workflow links |
| 61_HYPOTHESIS_BUILDER | GRETEL TRACK B | Builds explicit hypotheses without upgrading them to facts | Findings/evidence | Hypotheses | 50,30 | Hypothesis builder agent |
| 62_ROOT_CAUSE_DIAGNOSIS | GRETEL TRACK B | Distinguishes observed problems, likely causes, validated causes, and unknowns | Findings/hypotheses | Diagnoses | 61 | Root cause agent |
| 63_ACTION_DESIGN | GRETEL TRACK B | Designs justified actions only where supported | Diagnoses/priorities | Actions | 62 | Action design agent |
| 64_KPI_DESIGN | GRETEL TRACK B | Defines KPIs without inventing baselines | Actions/findings | KPIs | 63 | KPI agent |
| 65_CLIENT_VALIDATION_QUESTIONS | GRETEL TRACK B | Turns gaps and hypotheses into consultant questions | Gaps/hypotheses/diagnoses | Validation questions | 61,62 | Client questions agent |
| 66_90_DAY_ROADMAP | GRETEL TRACK B | Organizes supported work into 30/60/90 day roadmap | Actions/KPIs/questions | Roadmap actions | 63,64,65 | Roadmap agent |
| 70_REPORT_QA_DELIVERY | GRETEL TRACK B | Assembles and QAs diagnostic pack | Report components | Final package | All upstream | Storage/export |
| 71_INTELLECTUS_WEB_ADAPTER / INTELLECTUS_LIVE_WEBHOOK | SHARED INTEGRATION | Validates the web boundary and calls the final project workflow | Intellectus live intake envelope | Stable HTTP envelope | DEV_PROJECT3_END_TO_END (`62QlFvCwJ8b3weif`) | Production security boundary, gateway controls and audit retention |
| 99_GLOBAL_ERROR_HANDLER | SHARED | Normalizes errors | n8n error event | Error event/log | All workflows may attach | Logging/notification |

Core principle: every stage must preserve the distinction between fact, inference, hypothesis, and unknown.
