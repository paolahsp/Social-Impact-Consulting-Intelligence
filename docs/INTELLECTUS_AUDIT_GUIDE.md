# Intellectus Audit Guide

This guide separates live n8n evidence from repository-offline verification.

## Live Evidence

Retained facts from the final verified implementation:

- Parent workflow: `INTELLECTUS_LIVE_WEBHOOK`
- Parent workflow ID: `tBC3Pb82V2g5epzC`
- Parent execution: `3015`
- Parent result: HTTP `200`, `status: "completed"`, `demo: false`
- Parent duration: `16.38 s`
- Child workflow: `DEV_PROJECT3_END_TO_END`
- Child workflow ID: `62QlFvCwJ8b3weif`
- Child execution: `3016`
- Child result: successful

Audit interpretation: execution 3015 is the live web boundary proof. Execution
3016 is the nested child proof. Together they support the final path:

```text
web -> INTELLECTUS_LIVE_WEBHOOK -> DEV_PROJECT3_END_TO_END -> response web
```

## Golden Run

Golden run `2935` must remain intact. Do not replace it with execution 3015,
3016, local fixture runs, screenshots, or generated test artifacts. New audit
notes may reference 2935, but should not mutate the original evidence.

## Offline Verification

Offline repository checks validate committed code and contracts only:

- `scripts/test_n8n_71_intellectus_web_adapter.py` validates the final webhook
  export, canonical workflow IDs, `$json.valid` IF conditions, request contract,
  response validator, and sanitized error paths.
- `scripts/validate_n8n_skeletons.py` validates workflow JSON structure,
  required docs/fixtures/contracts, absence of credential blocks, and secret
  patterns.
- Web tests validate that the browser sends the live request without
  `evidence_handoff` and refuses demo responses as live results.

Offline checks do not prove n8n runtime availability, credentials, external
research behavior, or production gateway controls.

## Evidence Capture Checklist

For future live changes, retain:

- parent execution ID, status, HTTP status, duration, and timestamp;
- child execution ID and terminal status;
- redacted request envelope with no secrets;
- redacted response envelope showing `status` and `demo`;
- workflow IDs and names;
- git commit SHA of the matching repository state;
- note distinguishing live, test-webhook, and offline fixture evidence.
