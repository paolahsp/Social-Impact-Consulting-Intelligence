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
9. 71_INTELLECTUS_WEB_ADAPTER
10. 54_EVIDENCE_GAP_RESEARCH
11. 40_RAG_RETRIEVAL_PIPELINE
12. 30_EVIDENCE_PIPELINE
13. 61_HYPOTHESIS_BUILDER
14. 62_ROOT_CAUSE_DIAGNOSIS
15. 63_ACTION_DESIGN
16. 64_KPI_DESIGN
17. 65_CLIENT_VALIDATION_QUESTIONS
18. 66_90_DAY_ROADMAP
19. 60_TRANSFORMATION_ORCHESTRATOR
20. 50_ANALYSIS_ORCHESTRATOR
21. 20_CONTEXT_RESEARCH_ORCHESTRATOR
22. 10_INTAKE_AND_ORG_RESOLVER
23. 70_REPORT_QA_DELIVERY
24. 00_MAIN_ORCHESTRATOR

Why this order:

- Import leaf workflows first so parent placeholders can later be replaced with real Execute Workflow nodes.
- Import shared error handling before normal workflows so it can be attached during configuration.
- Import transformation child workflows before 60_TRANSFORMATION_ORCHESTRATOR.
- Import 53 before 71, then select 53 manually in 71 after import.
- Import orchestrators after their children.
- Import the main orchestrator last because it links the whole architecture.

No workflow IDs are hardcoded in these skeletons. Link sub-workflows manually after import.
