# Paola P0 Vertical Slice

Scope:

`21_WEB_SEARCH -> 30_EVIDENCE_PIPELINE -> 40_RAG_RETRIEVAL_PIPELINE -> 51_REVENUE_RESILIENCE_AGENT`

Architecture v1 remains frozen. No new workflows, shared schema changes, paid provider selection, credentials, Salesforce, WhatsApp, Telegram, frontend, dashboard, or future-scope implementation were added.

Phase 2B status:

- The n8n exports now own the visible execution path.
- `21_WEB_SEARCH` uses an n8n HTTP Request node for DuckDuckGo Lite.
- Code nodes are limited to deterministic parsing, mapping, local retrieval scoring, and output validation.
- The Python runner remains a reproducible local test harness; n8n does not call it.

## External Provider Used

The P0 web-search provider is DuckDuckGo Lite HTML search:

- Provider label: `duckduckgo_html`
- Endpoint pattern: `https://lite.duckduckgo.com/lite/?q=...`
- Credentials: none
- Fallback behavior in the local runner: Bing HTML is attempted only if DuckDuckGo Lite returns no parseable results or fails.
- n8n behavior: DuckDuckGo Lite request failure and empty-search states are visible branches inside `21_WEB_SEARCH`.

## Credentials Required

Current P0 slice:

- No credentials required for web search.
- No API keys are stored in workflow JSON or run outputs.

Future structured extraction/evaluation:

- An LLM credential will be required if Paola chooses to replace deterministic extraction with a model call.
- Placeholder environment variable: `OPENAI_API_KEY` or a future provider-specific secret managed in n8n credentials.
- Do not commit any secret value.

Future RAG/vector retrieval:

- No vector database credential is required in P0.
- P0 uses `knowledge/revenue_resilience_corpus.json` as a transparent local corpus.
- A future vector store may require provider credentials, but that is outside this slice.

## Environment Variables

None are required for the current P0 run.

## Workflow Behavior

### 21_WEB_SEARCH

Input: organization/run context plus optional query hint.

Behavior:

- Builds an organization-aware search query.
- Calls DuckDuckGo Lite HTML search.
- Parses title, URL, and snippet.
- Filters for organization or revenue relevance.
- Normalizes results into `source.schema.json` shape.
- Handles empty search and provider failure with controlled states.

### 30_EVIDENCE_PIPELINE

Input: normalized sources.

Behavior:

- Extracts deterministic revenue-resilience evidence from public search result title, URL, and snippet.
- Prioritizes `fact` extraction for the P0 slice.
- Every supported evidence object references `source_ids`.
- If no material evidence is found, emits an `unknown` evidence object instead of inventing a claim.

### 40_RAG_RETRIEVAL_PIPELINE

Input: revenue evidence.

Behavior:

- Keeps organization evidence separate from framework knowledge.
- Retrieves relevant Revenue Resilience context from `knowledge/revenue_resilience_corpus.json`.
- Covers funding concentration, diversification, recurring revenue, and evidence limitations.

### 51_REVENUE_RESILIENCE_AGENT

Input: revenue evidence plus retrieved framework context.

Behavior:

- Produces contract-valid `finding.schema.json` output.
- References evidence IDs.
- Keeps missing financial evidence visible as unknown.
- Does not invent revenue numbers, baselines, donor concentration, reserves, or scores.

## Exact Test Organization

Organization: GiveDirectly

Website: `https://www.givedirectly.org`

Country: United States

Query hint:

`annual report revenue funding grants donations financial statements`

## Exact Test Results

Happy path output:

- File: `runs/paola_p0_givedirectly.json`
- Controlled state: `ok`
- Search provider: `duckduckgo_html`
- Normalized sources: 5
- Evidence objects: 5
- RAG contexts: 3
- Revenue findings: 1

Failure path output:

- File: `runs/paola_p0_empty_search.json`
- Controlled state: `empty_search`
- Normalized sources: 0
- Evidence objects: 1
- RAG contexts: 3
- Revenue findings: 1 unknown finding

## Known Limitations

- P0 evidence extraction uses search metadata only; it does not fetch and parse full source pages.
- Source `publication_date` and `freshness` remain unknown unless available in search metadata.
- Search snippets can mention financial facts, but the runner does not infer amounts into findings.
- Missing financial evidence does not create a negative finding.
- This slice does not configure `22_WEBSITE_EXTRACTION`, `23_DOCUMENT_PUBLIC_DATA_RESEARCH`, `24_NEWS_EXTERNAL_CONTEXT`, `52_IMPACT_EVIDENCE_AGENT`, or `54_EVIDENCE_GAP_RESEARCH`.

## Commands

Happy path:

```powershell
python scripts\paola_p0_vertical_slice.py --org-name "GiveDirectly" --website "https://www.givedirectly.org" --country "United States" --query "annual report revenue funding grants donations financial statements" --output runs\paola_p0_givedirectly.json
```

Failure path:

```powershell
python scripts\paola_p0_vertical_slice.py --org-name "GiveDirectly" --website "https://www.givedirectly.org" --country "United States" --query "annual report revenue funding grants donations financial statements" --simulate-failure empty_search --output runs\paola_p0_empty_search.json
```

Validation:

```powershell
python scripts\validate_paola_p0_output.py runs\paola_p0_givedirectly.json
python scripts\validate_paola_p0_output.py runs\paola_p0_empty_search.json
python scripts\validate_n8n_skeletons.py
python scripts\validate_fixtures.py
```
