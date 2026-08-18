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

- [ ] Retained evidence that workflow 53 was imported into n8n where required
  by the transformation stack
- [ ] Retained n8n trigger execution evidence
- [x] Input contract validated offline
- [x] No API or credential required by the committed deterministic workflow
- [x] Repository workflow logic configured
- [x] Output contract validated offline
- [x] Error and rejection paths validated offline
- [x] Offline workflow 53 harness passed
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

- [x] Repository export represents `INTELLECTUS_LIVE_WEBHOOK`
  (`tBC3Pb82V2g5epzC`)
- [x] Child workflow selector points to `DEV_PROJECT3_END_TO_END`
  (`62QlFvCwJ8b3weif`)
- [x] No credential exported to the repository
- [ ] Authorization boundary configured
- [ ] Exact-origin CORS configured
- [ ] Proxy/BFF rate and 256 KiB body limits configured
- [x] Request and final response contracts validated offline
- [x] IF nodes read `$json.valid`
- [x] Offline 400, 502 and 200 response-code configuration validated
- [x] Offline validator rejects legacy `evidence_handoff`
- [x] Retained parent execution evidence: 3015, HTTP 200, completed,
  `demo: false`, 16.38 s
- [x] Retained child execution evidence: 3016 successful
- [x] Golden run 2935 remains intact
- [ ] Retention, redacted logging, cancellation and idempotency controls agreed
- [ ] Production gateway evidence retained before broad activation

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
