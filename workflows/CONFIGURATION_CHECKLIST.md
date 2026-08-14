# Configuration Checklist

Use this checklist per workflow during n8n setup.

## 00_MAIN_ORCHESTRATOR

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 10_INTAKE_AND_ORG_RESOLVER

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 20_CONTEXT_RESEARCH_ORCHESTRATOR

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 21_WEB_SEARCH

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 22_WEBSITE_EXTRACTION

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 23_DOCUMENT_PUBLIC_DATA_RESEARCH

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 24_NEWS_EXTERNAL_CONTEXT

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 30_EVIDENCE_PIPELINE

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 40_RAG_RETRIEVAL_PIPELINE

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 50_ANALYSIS_ORCHESTRATOR

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 51_REVENUE_RESILIENCE_AGENT

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 52_IMPACT_EVIDENCE_AGENT

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 53_OPERATIONS_CX_AGENT

- [ ] Retained evidence that workflow 53 was imported into n8n; execution through
  71 is reported in PR #1 but is not independently auditable
- [ ] Retained n8n trigger execution evidence
- [x] Input contract validated offline
- [x] No API or credential required by the committed deterministic workflow
- [x] Repository workflow logic configured
- [x] Output contract validated offline
- [x] Error and rejection paths validated offline
- [x] Offline 71 -> 53 composition harness passed
- [ ] Retained evidence of a configured n8n parent link
- [ ] Retained n8n integration execution artifact

## 54_EVIDENCE_GAP_RESEARCH

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 60_TRANSFORMATION_ORCHESTRATOR

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 61_HYPOTHESIS_BUILDER

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 62_ROOT_CAUSE_DIAGNOSIS

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 63_ACTION_DESIGN

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 64_KPI_DESIGN

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 65_CLIENT_VALIDATION_QUESTIONS

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 66_90_DAY_ROADMAP

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 70_REPORT_QA_DELIVERY

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed

## 71_INTELLECTUS_WEB_ADAPTER

- [ ] Retained evidence that 71 was imported after `53_OPERATIONS_CX_AGENT`;
  controlled execution is reported in PR #1 but is not independently auditable
- [ ] Retained evidence that `TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX` was
  selected in n8n; the repository export intentionally remains unlinked
- [x] No workflow ID or credential exported to the repository
- [ ] Authorization boundary configured
- [ ] Exact-origin CORS configured
- [ ] Proxy/BFF rate and 256 KiB body limits configured
- [x] Input, evidence handoff and output contracts validated offline
- [x] Offline 400, 422, 502 and 200 demo branch logic and response-code
  configuration validated
- [ ] Retained n8n HTTP captures for 400, 422, 502 and 200 demo responses
- [x] Offline demo result contains `demo: true`
- [x] Offline live fixture without Operations/CX evidence returns
  `needs_evidence`
- [ ] Retained workflow 71 Test Webhook execution artifact; execution is
  reported in PR #1 but is not independently auditable
- [ ] Retention, redacted logging, cancellation and idempotency controls agreed
- [ ] Live browser -> public research -> validated handoff -> 71 -> 53 -> web
  run artifact retained before any active claim

## 99_GLOBAL_ERROR_HANDLER

- [ ] Imported
- [ ] Trigger works
- [ ] Input contract validated
- [ ] API configured
- [ ] Agent configured
- [ ] Output matches contract
- [ ] Error path tested
- [ ] Connected to parent workflow
- [ ] Integration test passed
