# Paola 23 — Document and Public Data Research

## Scope

`23_DOCUMENT_PUBLIC_DATA_RESEARCH` turns bounded public document candidates into traceable `source.schema.json` records and document metadata for the downstream Evidence Pipeline. It extracts what documents state; it does not produce consulting diagnoses, recommendations, or performance judgments.

Architecture v1 remains frozen. Workflow 22 is an upstream discovery source and is not modified by this implementation.

## Provider decision

| Item | Decision |
| --- | --- |
| Development extractor | Jina Reader |
| Endpoint | `https://r.jina.ai/{public_document_url}` |
| Credentials | None required for the public Reader endpoint used here |
| n8n integration | HTTP Request node returning text |
| Paid provider | None selected |
| Production candidate | Evaluate a supported/SLA-backed document service later; not configured here |

Jina Reader is the smallest credential-free option already compatible with the Paola research track. It can extract text from public digital PDFs and document-like HTML. It is not treated as an OCR service, has no project-controlled service-level guarantee, and may fail on blocked, very large, scanned, image-only, or dynamically protected documents. Those failures are returned explicitly.

## Input

```json
{
  "run_context": {},
  "organization": {
    "name": "GiveDirectly",
    "website": "https://www.givedirectly.org",
    "country": "United States"
  },
  "document_candidates": [
    {
      "url": "https://www.givedirectly.org/example-report.pdf",
      "title": "Example report",
      "discovered_by": "website_extraction"
    }
  ]
}
```

The workflow accepts at most eight candidates per run. `discovered_by` is bounded to `web_search`, `website_extraction`, or `public_data`.

## Canvas path

`START__SUB_WORKFLOW_TRIGGER`

→ `INPUT_VALIDATION`

→ `DOCUMENT_CANDIDATES`

→ `DOCUMENT_RELEVANCE_FILTER`

→ `ORGANIZATION_MATCH_CHECK`

→ `DECISION__FETCHABLE`

→ `DOCUMENT_FETCH__JINA_READER`

→ `FILE_TYPE_AND_RESPONSE_CHECK`

→ `DOCUMENT_TYPE_CLASSIFICATION`

→ `USEFUL_SECTION_EXTRACTION`

→ `METADATA_NORMALIZATION`

→ `MERGE__CANDIDATE_RESULTS`

→ `AGGREGATE_DOCUMENT_RESULTS`

→ explicit terminal branch.

Rejected or unsupported candidates bypass the external request and enter the same aggregate through `NORMALIZE_REJECTED_CANDIDATE`.

## Output

The terminal output contains:

- `run_context`
- `controlled_state`
- `extraction_provider` and non-secret provider metadata
- `candidates_attempted`
- `documents[]`
- `sources[]`
- `useful_sections_count`
- `errors[]`

Each successful document has one traceable source record. Document types are restricted to:

- `annual_report`
- `impact_report`
- `financial_report`
- `audited_financial_statement`
- `program_report`
- `strategy_document`
- `public_registry_document`
- `other_public_document`

Extracted sections are bounded to eight sections per document and 1,200 characters per section. Unknown publisher or publication date remains `null`.

## Controlled behavior

| State | Meaning |
| --- | --- |
| `success` | One or more documents extracted; no candidate errors |
| `partial_success` | Successful documents are preserved alongside explicit candidate errors |
| `no_documents_found` | No candidates were supplied |
| `unsupported_document` | Every supplied candidate lacks a supported document signal/type |
| `request_failure` | Input, organization match, request, or extraction failed and no document succeeded |

## DEV workflow

`DEV_PAOLA_23_DOCUMENT_RESEARCH_TEST` contains four visible branches:

1. GiveDirectly FY2023 audited financial statements.
2. MSF International Financial Report 2023.
3. GiveDirectly valid document plus an intentionally missing document to verify `partial_success`.
4. GiveDirectly `/about` as an unsupported non-document candidate.

After import, every Execute Sub-workflow node must be linked to the stored `23_DOCUMENT_PUBLIC_DATA_RESEARCH` workflow using the n8n database selector. The repository export intentionally contains no live workflow ID.

## Validation

Run:

```bash
python scripts/generate_n8n_skeletons.py
python scripts/validate_n8n_skeletons.py
python scripts/validate_fixtures.py
python scripts/validate_paola_22_output.py runs/paola_22_givedirectly.json runs/paola_22_invalid_website.json
python scripts/validate_paola_23_output.py runs/paola_23_givedirectly.json runs/paola_23_msf.json runs/paola_23_partial_success.json runs/paola_23_unsupported_document.json
```

## Live verification status

Repository-ready. Live n8n workflow IDs, execution IDs, exact results, and final verification status will be recorded after import and execution.

## Limitations

- No OCR path is configured.
- Candidate discovery is reused from upstream workflows; workflow 23 does not recrawl the internet.
- Third-party documents can be accepted only when an organization-name match is present, and they are never labeled official without an official-domain match.
- Publication dates are emitted only when an exact date is supplied by the extraction response; otherwise they remain `null`.
- Extracted text can contain source claims or source opinions. Downstream evidence classification must preserve their source attribution.
