# Workflow 71 — Intellectus web adapter import and runbook

Status: inactive, repository-ready, offline-tested, not live end-to-end
verified.

## Import and link

1. Import `workflows/skeletons/53_OPERATIONS_CX_AGENT.json` if it is not already
   present in the target n8n instance.
2. Import `workflows/skeletons/71_INTELLECTUS_WEB_ADAPTER.json`.
3. Keep 71 inactive.
4. Open `TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX`.
5. In **Workflow**, select the imported `53_OPERATIONS_CX_AGENT` from the list.
   The repository intentionally leaves the resource locator value empty; do
   not paste a guessed ID into the JSON.
6. Confirm **Run once with all items**, **Wait for Sub-Workflow Completion** and
   the error output remain enabled.
7. Save 71. Do not export or commit the environment-specific workflow ID.

## Security configuration before activation

1. Put n8n behind the approved BFF/reverse proxy for production. The direct
   Vite-to-n8n route is suitable only for a restricted demonstration
   environment because Vite cannot protect a credential.
2. Require authenticated consultant access at that boundary. If n8n Header
   Auth is used in a restricted environment, create/select the credential in
   n8n; never add it to the export or `.env.example`.
3. Restrict CORS to the exact Intellectus origin.
4. Enforce a 256 KiB request limit before n8n, plus rate limits per user and IP.
5. Configure TLS, metadata-only/redacted logs, n8n execution-data retention,
   access control and a run-ID deletion/cancellation procedure.
6. Add a durable idempotency store before enabling automatic retries.

## Test before activation

Use the n8n test webhook URL, not a production URL. The demo fixture path is:

```bash
export INTELLECTUS_WEBHOOK_URL='https://replace-with-test-host.example/webhook-test/intellectus-diagnostic'
export INTELLECTUS_WEBHOOK_TOKEN='replace-locally-if-header-auth-is-enabled'

curl --fail-with-body --silent --show-error \
  --request POST \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer ${INTELLECTUS_WEBHOOK_TOKEN}" \
  --data @fixtures/intellectus_71_demo_request.json \
  "${INTELLECTUS_WEBHOOK_URL}"
```

Expected: HTTP 200, `status: "completed"`, `demo: true`, and three validated
Operations/CX findings from the existing fictional fixture. This proves only a
demo execution; it is never live evidence.

Then send `fixtures/intellectus_71_live_request.json`. Expected: HTTP 422 and
`status: "needs_evidence"`, because the validated GiveDirectly P0 handoff
contains Revenue evidence but no Operations/CX evidence.

## Connect Intellectus

1. Copy the environment-specific 71 production/test webhook URL from n8n.
2. Set it locally or in the deployment environment only:

   ```bash
   VITE_DIAGNOSTIC_WEBHOOK_URL='https://replace-with-approved-host.example/path'
   ```

3. Never put a token in a `VITE_*` variable.
4. Run `cd apps/intellectus-web && npm run verify`.
5. With a real Paola Operations/CX handoff available through the approved BFF,
   execute web -> 71 -> 53 -> web and retain the redacted run IDs, HTTP status
   and assertion results as evidence.

The missing server-side mechanism that associates web intake with Paola's
completed evidence handoff is **To verify against shared research contract**.
Until it exists and a live run passes, the integration must not be described
as active end to end.
