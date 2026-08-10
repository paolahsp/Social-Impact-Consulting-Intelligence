# Paola P0 n8n Import

Status:

- Repository ready.
- Not live-n8n verified yet.
- No credentials required.
- Architecture v1 remains frozen.

## 1. Import These JSON Files

Import in this exact order:

1. `workflows/skeletons/21_WEB_SEARCH.json`
2. `workflows/skeletons/30_EVIDENCE_PIPELINE.json`
3. `workflows/skeletons/40_RAG_RETRIEVAL_PIPELINE.json`
4. `workflows/skeletons/51_REVENUE_RESILIENCE_AGENT.json`
5. `workflows/dev/DEV_PAOLA_P0_LIVE_TEST.json`

Do not import or configure workflows `22`, `23`, `24`, `52`, or `54` for this task.

## 2. Copy Workflow IDs After Import

After importing the first four workflows, open each workflow settings page and copy the n8n workflow ID for:

- `21_WEB_SEARCH`
- `30_EVIDENCE_PIPELINE`
- `40_RAG_RETRIEVAL_PIPELINE`
- `51_REVENUE_RESILIENCE_AGENT`

Keep those IDs only in your local n8n instance. Do not commit live IDs unless the team explicitly decides the exported configured IDs are safe for the target environment.

## 3. Link Execute Sub-Workflow Nodes

Open `DEV_PAOLA_P0_LIVE_TEST` and configure these nodes:

| Node | Set workflow to |
| --- | --- |
| `TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH` | `21_WEB_SEARCH` |
| `TODO_LINK_SUBWORKFLOW__30_EVIDENCE_PIPELINE` | `30_EVIDENCE_PIPELINE` |
| `TODO_LINK_SUBWORKFLOW__40_RAG_RETRIEVAL` | `40_RAG_RETRIEVAL_PIPELINE` |
| `TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE` | `51_REVENUE_RESILIENCE_AGENT` |

No workflow IDs are hardcoded in the repo export.

## 4. Manual Node Verification

In `21_WEB_SEARCH`, verify:

- `HTTP_REQUEST__DUCKDUCKGO_LITE` uses `GET`.
- URL expression is `={{ $json.search.search_url }}`.
- Headers include `User-Agent: Mozilla/5.0 Project3PaolaP0/1.0`.
- Response output property is `html`.
- `continueOnFail` is enabled.
- Branches exist for `OUTPUT_REQUEST_FAILURE`, `OUTPUT_EMPTY_SEARCH`, and `OUTPUT_SUCCESS__SOURCES`.

In `30_EVIDENCE_PIPELINE`, verify:

- `SOURCE_INPUT`
- `SOURCE_DEDUPLICATION`
- `SOURCE_QUALITY`
- `EVIDENCE_EXTRACTION_MAPPING`
- `EVIDENCE_CLASSIFICATION`
- `EVIDENCE_VALIDATION`
- `OUTPUT_CONTRACT__EVIDENCE_LEDGER`

In `40_RAG_RETRIEVAL_PIPELINE`, verify:

- `ORGANIZATION_EVIDENCE_INPUT`
- `BUILD_RETRIEVAL_QUERY`
- `LOAD_LOCAL_FRAMEWORK_CORPUS`
- `SCORE_AND_SELECT_CONTEXTS`
- `VALIDATE_RETRIEVAL`
- `OUTPUT_CONTRACT__RAG_CONTEXT`

In `51_REVENUE_RESILIENCE_AGENT`, verify:

- `INPUT_CONTRACT__REVENUE_EVIDENCE_AND_RAG`
- `REVENUE_EVALUATION`
- `EVIDENCE_TRACE_CHECK`
- `UNKNOWN_LIMITATIONS`
- `OUTPUT_CONTRACT__PAOLA_TRACK_OUTPUT`

## 5. Execute GiveDirectly Test

Open `DEV_PAOLA_P0_LIVE_TEST`.

The `DEV_INPUT__GIVEDIRECTLY` node emits:

```json
{
  "organization_name": "GiveDirectly",
  "website": "https://www.givedirectly.org",
  "country": "United States",
  "query": "annual report revenue funding grants donations financial statements"
}
```

Run the workflow manually.

Expected path:

```text
START__MANUAL_TEST_TRIGGER
-> DEV_INPUT__GIVEDIRECTLY
-> TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH
-> TODO_LINK_SUBWORKFLOW__30_EVIDENCE_PIPELINE
-> TODO_LINK_SUBWORKFLOW__40_RAG_RETRIEVAL
-> TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE
-> FINAL_PAOLA_TRACK_OUTPUT
```

## 6. Successful Output Should Contain

The final output should include:

- `run_context`
- `sources`
- `evidence`
- `findings`
- `unknowns`
- `contradictions`
- `rag_metadata`
- `rag_context`
- `controlled_state`
- `errors`

For the GiveDirectly test, a successful result should have:

- `controlled_state: "ok"`
- at least one `source`
- at least one `evidence` object with explicit `evidence_type`
- at least one supported evidence object referencing `source_ids`
- at least one `rag_context.contexts` entry
- at least one Revenue Resilience finding
- no invented revenue concentration or negative score

## 7. Test Empty Search

The true empty-search branch exists in `21_WEB_SEARCH`:

```text
PARSE_HTML_RESULTS
-> DECISION__EMPTY_SEARCH
-> OUTPUT_EMPTY_SEARCH
```

To test it deterministically without depending on a search provider returning no results:

1. In `DEV_PAOLA_P0_LIVE_TEST`, temporarily disconnect `DEV_INPUT__GIVEDIRECTLY` from `TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH`.
2. Connect `START__MANUAL_TEST_TRIGGER` to `DEV_INPUT__SIMULATED_EMPTY_SEARCH_FOR_30`.
3. Connect `DEV_INPUT__SIMULATED_EMPTY_SEARCH_FOR_30` to `TODO_LINK_SUBWORKFLOW__30_EVIDENCE_PIPELINE`.
4. Leave the rest of the chain as:

```text
30_EVIDENCE_PIPELINE
-> 40_RAG_RETRIEVAL_PIPELINE
-> 51_REVENUE_RESILIENCE_AGENT
-> FINAL_PAOLA_TRACK_OUTPUT
```

Expected empty-search output:

- `controlled_state: "empty_search"`
- `sources: []`
- one `unknown` revenue evidence object
- one `unknown` Revenue Resilience finding
- `requires_validation: true`
- no negative revenue assessment

After the test, reconnect the GiveDirectly happy path.

## 8. Export Configured Workflows Back To Repo

After live n8n verification:

1. Export each configured workflow from n8n.
2. Save exports over:
   - `workflows/skeletons/21_WEB_SEARCH.json`
   - `workflows/skeletons/30_EVIDENCE_PIPELINE.json`
   - `workflows/skeletons/40_RAG_RETRIEVAL_PIPELINE.json`
   - `workflows/skeletons/51_REVENUE_RESILIENCE_AGENT.json`
   - `workflows/dev/DEV_PAOLA_P0_LIVE_TEST.json`
3. Do not export credentials.
4. Run:

```powershell
python scripts\validate_n8n_skeletons.py
python scripts\validate_fixtures.py
python scripts\validate_paola_p0_output.py runs\paola_p0_givedirectly.json
python scripts\validate_paola_p0_output.py runs\paola_p0_empty_search.json
```

5. Confirm no secrets are present before committing or sharing.

