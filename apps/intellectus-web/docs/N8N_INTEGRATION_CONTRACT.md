# Intellectus web adapter contract

Status: repository-ready and offline-tested. The 71 -> 53 composition is reproducibly validated offline using fictional evidence. PR #1 reports a controlled n8n Test Webhook execution of the same path, but no corresponding workflow 71 execution artifact is retained in the repository. Live public-research end-to-end integration remains unverified.

Contract version: `1.0`.

The boundary is:

```text
Intellectus
-> POST 71_INTELLECTUS_WEB_ADAPTER
-> request and evidence-handoff validation
-> exact flat Paola-to-53 adaptation
-> 53_OPERATIONS_CX_AGENT
-> leaf-output validation
-> stable HTTP envelope
-> Intellectus repository adapter
-> human-review brief
```

Workflow 71 does not research, fetch sources, process selected documents or
duplicate workflow 53. The browser intake is context only and is never
promoted to evidence.

## Request

```json
{
  "contract_version": "1.0",
  "mode": "live",
  "correlation_id": "CORR-...",
  "run_id": "RUN-...",
  "intake": {
    "organization_name": "...",
    "website": "https://...",
    "country": "US",
    "current_challenge": "...",
    "research_window": {
      "start_date": "2026-05-12",
      "end_date": "2026-08-09"
    },
    "uploaded_document_refs": []
  },
  "evidence_handoff": {
    "run_context": {},
    "sources": [],
    "evidence": [],
    "findings": [],
    "unknowns": [],
    "contradictions": [],
    "rag_metadata": {}
  }
}
```

The real 53 input is the flat value of `evidence_handoff`, with exactly these
seven top-level fields. The adapter checks source/evidence/finding IDs,
referential integrity, organization name and website, run ID, required arrays,
and at least one source-linked `operations_cx` evidence record before calling
53. It preserves a supplied correlation ID, otherwise a supplied run ID, or
generates an execution-scoped value.

How the browser receives the completed Paola handoff is **To verify against
shared research contract**. The current web call sends intake only, so a live
request returns `422 needs_evidence` until a trusted server-side research
handoff is connected. Selected browser `File` objects remain session-only and
are not transmitted or analysed.

## Responses

All responses contain `contract_version`, `status`, `correlation_id`, `run_id`,
`demo` and a plain-language `message`.

- `200 completed`: validated 53 findings plus the original sources, evidence,
  unknowns, contradictions and retrieval metadata needed for web mapping.
- `400 error`: invalid version, fields, references, organization/run mismatch,
  oversize application payload or forbidden live/demo mixing.
- `422 needs_evidence`: missing or insufficient Operations/CX evidence.
- `502 error`: 53 failed or returned an invalid leaf contract.

The public error envelope contains only a stable code. It never includes node
names, workflow IDs, stack traces or raw upstream errors.

Workflow 53 returns only `{ "findings": [] }`. The web maps those findings,
their validation questions and their source traceability into the existing
review experience. It does not claim that 53 produced recommendations, KPIs,
diagnoses or a roadmap. The displayed next step is a human-review control, not
an analytical recommendation.

## Demo integrity

`mode: "demo"` is the only route that can load
`fixtures/paola_track_output.json`. It always returns `demo: true`; rejects a
supplied evidence handoff; rejects document references; and is blocked if the
same fixture is submitted as live evidence. The Vite adapter itself sends only
`mode: "live"` and refuses a completed response marked as demo. With no webhook
URL, the existing local repository remains the explicit demo fallback.

## Browser adapter

`VITE_DIAGNOSTIC_WEBHOOK_URL` is the sole activation switch. The URL is
validated, and `fetch` exists only in the infrastructure repository. Requests
use JSON, a correlation header and `AbortController` with a 15-second timeout.
Both request and response are validated with Zod. POST retries are not
automatic; the consultant can retry from the form.

## Security and production limitations

- Authorization: the committed workflow is inactive and contains no
  credential. Configure an n8n Header Auth credential or, preferably, require
  authentication at a backend-for-frontend/reverse proxy before activation.
- Vite risk: every `VITE_*` value is public client code. A browser cannot keep
  a webhook token secret, and a public webhook URL can be copied and abused.
  Do not place bearer tokens or credentials in Vite variables.
- CORS: allow only the exact deployed Intellectus origin. CORS is not
  authorization and must be paired with authentication.
- Rate limiting: enforce per-user and per-IP limits at the proxy/BFF. Workflow
  71 contains no durable rate-limit store.
- Size: workflow validation rejects a serialized application body above 256
  KiB, but the proxy and n8n global payload setting must reject it before the
  body reaches a Code node. Documents must use a separate controlled upload
  path in a future phase.
- Idempotency: correlation and run IDs are preserved, but workflow 71 has no
  durable deduplication store. A BFF/store must enforce uniqueness and replay a
  prior terminal response before production retries are enabled.
- Timeouts and retries: the browser aborts after 15 seconds. The subworkflow is
  synchronous. Do not use `202` unless a real persisted asynchronous job and
  status endpoint are introduced.
- Data and logs: do not log request bodies or public evidence by default. Use
  metadata-only logs, redact URLs/query strings when sensitive, restrict n8n
  execution access and encrypt transport and storage.
- Retention and cancellation: define execution-data retention in n8n and the
  proxy. Browser abort does not guarantee server cancellation after delivery;
  operators need a run-ID-based cancellation and deletion procedure before
  production use.
- Future architecture: move submission, authentication, evidence-handoff
  lookup, idempotency, audit and cancellation to a backend/BFF. Keep the
  browser-facing response contract stable.

## Fixtures

- `fixtures/intellectus_71_demo_request.json`: fictional demo request exercised
  by the offline composition harness; must return `demo: true`.
- `fixtures/intellectus_71_live_request.json`: real Paola P0 GiveDirectly
  handoff. It is a valid live envelope but has no Operations/CX evidence, so it
  correctly returns `422 needs_evidence`.
- `fixtures/intellectus_71_success_response.json`: static demo success envelope
  based only on validated repository fixtures; it is not a workflow execution
  artifact.

An actual `200 demo: false` fixture does not exist because the repository has
no validated live Operations/CX handoff. Creating one would invent evidence.
