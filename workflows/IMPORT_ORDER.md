# Import Order

Recommended sequence:

1. 99_GLOBAL_ERROR_HANDLER
2. 21_WEB_SEARCH
3. 22_WEBSITE_EXTRACTION
4. 23_DOCUMENT_PUBLIC_DATA_RESEARCH
5. 24_NEWS_EXTERNAL_CONTEXT
6. 51_REVENUE_RESILIENCE_AGENT
7. 52_IMPACT_EVIDENCE_AGENT
8. 53_OPERATIONS_CX_AGENT
9. 54_EVIDENCE_GAP_RESEARCH
10. 40_RAG_RETRIEVAL_PIPELINE
11. 30_EVIDENCE_PIPELINE
12. 61_HYPOTHESIS_BUILDER
13. 62_ROOT_CAUSE_DIAGNOSIS
14. 63_ACTION_DESIGN
15. 64_KPI_DESIGN
16. 65_CLIENT_VALIDATION_QUESTIONS
17. 66_90_DAY_ROADMAP
18. 60_TRANSFORMATION_ORCHESTRATOR
19. 50_ANALYSIS_ORCHESTRATOR
20. 20_CONTEXT_RESEARCH_ORCHESTRATOR
21. 10_INTAKE_AND_ORG_RESOLVER
22. 70_REPORT_QA_DELIVERY
23. 00_MAIN_ORCHESTRATOR

Why this order:

- Import leaf workflows first so parent placeholders can later be replaced with real Execute Workflow nodes.
- Import shared error handling before normal workflows so it can be attached during configuration.
- Import transformation child workflows before 60_TRANSFORMATION_ORCHESTRATOR.
- Import orchestrators after their children.
- Import the main orchestrator last because it links the whole architecture.

No workflow IDs are hardcoded in these skeletons. Link sub-workflows manually after import.
