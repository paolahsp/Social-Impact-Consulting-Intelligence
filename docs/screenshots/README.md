# Required n8n Screenshot Evidence

The Project 3 submission requires screenshots of the live n8n workflow. These
images must be captured from the actual n8n instance; diagrams or recreated
mockups are not substitutes.

Add the following PNG files to this directory before submission:

1. `01-intellectus-live-webhook-workflow.png`
   - Show the complete `INTELLECTUS_LIVE_WEBHOOK` canvas.
   - Node names and connections must be readable.
   - Hide the production/test webhook URL and all credential details.
2. `02-parent-execution-3015-success.png`
   - Show execution `3015`, its successful terminal status, and the workflow
     name.
   - Keep request/response bodies collapsed if they could expose sensitive
     data.
3. `03-child-execution-3016-success.png`
   - Show execution `3016`, successful status, and
     `DEV_PROJECT3_END_TO_END`.

If newer executions are used, update the filenames and
`docs/INTELLECTUS_AUDIT_GUIDE.md` so the IDs remain consistent.

## Capture quality

- Use PNG, not a phone photograph.
- Capture at normal browser zoom with readable node and status labels.
- Crop unrelated browser chrome where practical.
- Do not show credentials, authorization headers, webhook tokens, personal
  data, or private client inputs.
- Confirm the screenshot matches the workflow export committed in GitHub.

