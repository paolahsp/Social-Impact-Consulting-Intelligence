# Future research workflow integration contract

This document defines the typed boundary between the guided Intellectus UI and
a future research workflow. The current adapter returns schema-validated local
sample data. It makes no network request and does not simulate remote progress.

## Replacement point

The UI calls one interface:

```ts
prepareDiagnostic(input: DiagnosticInput): Promise<DiagnosticResult>
```

`FixtureDiagnosticRepository` is instantiated in `src/app/App.tsx`. Future
integration replaces that adapter with a workflow-backed implementation while
the provider and five pages continue to depend only on
`DiagnosticRepository`.

## Input

```ts
interface DiagnosticInput {
  organization_name: string
  website: string
  country: string
  current_challenge: string
  research_window: {
    start_date: string
    end_date: string
  }
  uploaded_document_refs: string[]
}
```

Dates use `YYYY-MM-DD`. `country` uses an ISO 3166-1 alpha-2 code. The real
adapter must derive the associated country name from the centralized lookup
when the shared contract requires both values; the current external schema has
only `country`, so a `country_name` result field remains to verify rather than
being invented here. The recent
context window is inclusive and limited to 90 calendar days. It limits recent
external context; relevant official reports, annual reports and financial
statements may be older and must not be excluded automatically.

`uploaded_document_refs` is empty in the current UI and is reserved for future
document ingestion. Selected browser `File` objects remain session-only and are
not presented as references. Before live integration, the workflow owner must confirm
reference format, consent, file limits and retention rules.

## Run states

The typed run states and their UI translations are:

| Contract state | Plain-language UI |
| --- | --- |
| `created` | Preparing your diagnostic |
| `researching` | Reviewing public sources |
| `analyzing` | Organizing the evidence |
| `qa` | Preparing your brief |
| `completed` | Ready for review |
| `failed` | We couldn’t complete the diagnostic |

The current local adapter returns `completed` or throws. The UI does not show
percentages, timed loaders or invented activity. A future adapter must map real
workflow state only.

## Result

`DiagnosticResult` contains the run status, the validated diagnostic aggregate
and `final_package`. The package supports:

- `run_context`;
- `organization_snapshot`;
- `public_evidence_map`;
- `evidence_ledger`;
- `findings`;
- `hypotheses`;
- `diagnoses`;
- `recommendations`;
- `kpis`;
- `client_validation_questions`;
- `roadmap_90_day`;
- `missing_information`;
- `confidence_limitations`.

The guided interface deliberately displays only the subset needed for the
overview, conversation preparation, next step and final brief. Hidden fields
remain available at the typed boundary for future workflow results.

## Live adapter responsibilities still unresolved

- Real transport and authentication.
- Workflow run identifier and idempotency rules.
- Polling, callback or event delivery for real state changes.
- Partial-result and failure envelopes.
- Source provenance, excerpts and evidence-quality fields.
- Retry, timeout and cancellation rules.
- Uploaded-document reference lifecycle.
- Data retention, deletion, access control and audit requirements.
