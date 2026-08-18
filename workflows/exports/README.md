# Verified Live n8n Exports

This directory contains the exact workflow JSON downloaded from the published
n8n instance on 18 August 2026.

| File | Workflow ID | Verified execution | Purpose |
| --- | --- | --- | --- |
| `INTELLECTUS_LIVE_WEBHOOK.json` | `tBC3Pb82V2g5epzC` | `3015` | HTTP trigger, request validation, child-workflow call, and structured transport response |
| `DEV_PROJECT3_END_TO_END.json` | `62QlFvCwJ8b3weif` | `3016` | Research, evidence processing, specialist analysis, transformation, and final diagnostic assembly |

The parent execution returned HTTP 200 with status `completed`. The child
execution completed the trace from source through evidence, finding,
hypothesis, diagnosis, recommendation, KPI, and roadmap action.

These exports contain no credential objects or secrets. They preserve
`active: true` because they are runtime evidence. Deactivate and review the
webhook path and referenced sub-workflow IDs before importing them into another
n8n instance.

An HTTP 422 `needs_evidence` response is expected when a request provides an
unreachable or non-evidentiary website. The system must not fabricate a report
when no source-linked evidence is available.
