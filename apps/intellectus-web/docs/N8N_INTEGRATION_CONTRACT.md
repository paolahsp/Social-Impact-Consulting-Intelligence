# Intellectus n8n Integration Contract

Status: final live architecture documented. Repository tests validate the web
transport schema and the committed workflow export offline. Live execution
evidence is recorded in `docs/INTELLECTUS_AUDIT_GUIDE.md`.

Contract version: `1.0`.

The boundary is:

```text
Intellectus web
-> POST INTELLECTUS_LIVE_WEBHOOK
-> DEV_PROJECT3_END_TO_END
-> final response validator
-> Intellectus repository adapter
-> human-review brief
```

Canonical workflow IDs:

- `INTELLECTUS_LIVE_WEBHOOK`: `tBC3Pb82V2g5epzC`
- `DEV_PROJECT3_END_TO_END`: `62QlFvCwJ8b3weif`

The web request does not send `evidence_handoff`. Public research, evidence
assembly, transformation, and final response preparation belong to
`DEV_PROJECT3_END_TO_END`.

## Request

```json
{
  "contract_version": "1.0",
  "mode": "live",
  "correlation_id": "CORR-...",
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
  }
}
```

The browser sends JSON only. Selected browser files remain session-only until a
server-side upload and research boundary exists.

## Response

Successful live response:

```json
{
  "contract_version": "1.0",
  "status": "completed",
  "correlation_id": "CORR-...",
  "run_id": "RUN-...",
  "demo": false,
  "message": "Diagnostic prepared for review.",
  "completed_at": "2026-08-14T12:00:00.000Z",
  "data": {
    "intake": {},
    "sources": [],
    "evidence": [],
    "findings": [],
    "unknowns": [],
    "contradictions": [],
    "rag_metadata": {}
  }
}
```

Error responses use the same envelope with `status: "error"` and a stable
public code: `invalid_request`, `upstream_failure`, or
`invalid_upstream_response`. Public errors must not include node names,
workflow IDs, stack traces, credentials, raw prompts, or raw upstream errors.

The final n8n validator emits `valid`. The IF node must read `$json.valid`.

## Browser Adapter

`VITE_DIAGNOSTIC_WEBHOOK_URL` is the sole activation switch. Leave it unset to
use the explicit local demo repository. The app validates the URL, sends JSON,
sets `X-Correlation-ID`, and aborts after 15 seconds. POST retries are manual.

The UI refuses completed responses marked `demo: true`. The golden demo fixture
remains a local validation artifact and is not treated as live evidence.

## Security Limits

- Never put tokens or credentials in `VITE_*` variables.
- Use an authenticated BFF/reverse proxy or equivalent gateway for production.
- Restrict CORS to the exact deployed Intellectus origin.
- Enforce per-user and per-IP rate limits before n8n.
- Enforce the 256 KiB body limit before n8n as well as in workflow validation.
- Use metadata-only/redacted logs and restrict n8n execution access.
- Define run-ID deletion/cancellation and execution-data retention.
- Add durable idempotency before automatic retries.

Execution 3015 confirms a live HTTP 200 `completed` response with `demo: false`
in 16.38 seconds, with child execution 3016 also successful. See the audit
guide for the evidence boundary and retained offline checks.
