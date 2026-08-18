# Intellectus live webhook import and runbook

Status: final architecture aligned with the confirmed live implementation.

Canonical workflow IDs:

- `INTELLECTUS_LIVE_WEBHOOK`: `tBC3Pb82V2g5epzC`
- `DEV_PROJECT3_END_TO_END`: `62QlFvCwJ8b3weif`

Final path:

```text
web -> INTELLECTUS_LIVE_WEBHOOK -> DEV_PROJECT3_END_TO_END -> response web
```

## Import and Verify

1. Import or confirm `DEV_PROJECT3_END_TO_END` in n8n with ID
   `62QlFvCwJ8b3weif`.
2. Import `workflows/skeletons/71_INTELLECTUS_WEB_ADAPTER.json`.
3. Confirm the imported workflow is `INTELLECTUS_LIVE_WEBHOOK` with ID
   `tBC3Pb82V2g5epzC`.
4. Confirm `CALL__DEV_PROJECT3_END_TO_END` points to workflow ID
   `62QlFvCwJ8b3weif`.
5. Confirm `DECISION__WEB_REQUEST_VALID` and
   `DECISION__FINAL_RESPONSE_VALID` both read `$json.valid`.
6. Confirm no credentials or secrets are exported.

The repository export intentionally commits the confirmed workflow IDs because
they are workflow identifiers, not credentials. It does not commit auth headers,
API keys, n8n credentials, webhook tokens, or environment-specific secrets.

## Request

Use `fixtures/intellectus_71_live_request.json` as the shape reference. The
request contains `contract_version`, `mode: "live"`, `correlation_id`, and
`intake`. It does not contain `evidence_handoff`.

## Live Evidence

The confirmed live run is:

- Parent execution: `3015`
- Child execution: `3016`
- Parent result: HTTP `200`, `status: "completed"`, `demo: false`
- Parent duration: `16.38 s`
- Child result: successful

The golden run `2935` is historical audit evidence and must remain intact. Do
not overwrite it with new dry-run or demo artifacts.

## Security Before Production

1. Put n8n behind the approved authenticated gateway.
2. Restrict CORS to the exact Intellectus origin.
3. Enforce 256 KiB request limits before n8n.
4. Add per-user and per-IP rate limits.
5. Use metadata-only/redacted logging.
6. Configure retention, cancellation, and deletion by run ID.
7. Add durable idempotency before enabling automatic retries.

## Local Verification

Repository verification is offline and structural:

```bash
python scripts/test_n8n_71_intellectus_web_adapter.py
python scripts/validate_n8n_skeletons.py
cd apps/intellectus-web && npm run verify
```

Offline tests prove the committed export and web contract. They do not replay
executions 3015 or 3016.
