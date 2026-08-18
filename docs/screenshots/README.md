# Verified n8n Screenshot Evidence

These PNG files were captured from the published n8n instance on 18 August
2026. They correspond to the exact workflow exports in
`workflows/exports/`.

1. [INTELLECTUS_LIVE_WEBHOOK canvas](01-intellectus-live-webhook-workflow.png)
   - Published parent workflow `tBC3Pb82V2g5epzC`.
   - Shows the HTTP trigger, request validation, child-workflow call, response
     mapping, and controlled error path.
2. [Parent execution 3015](02-parent-execution-3015-success.png)
   - `INTELLECTUS_LIVE_WEBHOOK` completed successfully in 16.38 seconds.
   - The selected response shows HTTP 200 and status `completed`.
3. [Child execution 3016](03-child-execution-3016-success.png)
   - `DEV_PROJECT3_END_TO_END` completed successfully in 14.986 seconds.
   - Shows the live research-to-structured-diagnostic orchestration.

The captures do not show credentials, authorization headers, webhook tokens,
personal data, or private client inputs. GiveDirectly information visible in
the successful run is public demonstration data.

Execution `3163` is intentionally not used as the happy-path evidence. It
submitted the unreachable placeholder `https://example.test` and correctly
returned HTTP 422 with `needs_evidence`; the system did not fabricate a report.
