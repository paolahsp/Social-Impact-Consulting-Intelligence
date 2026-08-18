# Intellectus — Social Impact Intelligence

Intellectus is a consultant-facing, human-reviewed diagnostic system for
social-impact organizations. It turns bounded public evidence into a structured
starting point for a client conversation while keeping facts, inferences,
hypotheses, and unknowns visibly separate.

## Project 3 MVP

The primary stack is **n8n**. The demonstrated path is:

```text
Web intake
  -> INTELLECTUS_LIVE_WEBHOOK (workflow 71)
  -> DEV_PROJECT3_END_TO_END
  -> evidence and specialist analysis
  -> validated response
  -> consultant review in the React application
```

The MVP demonstrates trigger -> research/tools -> structured report. It does
not claim autonomous client diagnosis or production readiness. A consultant
must review the evidence, unknowns, hypotheses, questions, and proposed actions
before anything is used with a client.

The stack rationale is documented in [stack_decision.md](stack_decision.md).

## Evidence boundary

The retained live evidence records:

- parent workflow: `INTELLECTUS_LIVE_WEBHOOK` (`tBC3Pb82V2g5epzC`);
- parent execution: `3015`, HTTP 200, completed, `demo: false`;
- child workflow: `DEV_PROJECT3_END_TO_END` (`62QlFvCwJ8b3weif`);
- child execution: `3016`, successful;
- protected golden run: `2935`.

See [docs/INTELLECTUS_AUDIT_GUIDE.md](docs/INTELLECTUS_AUDIT_GUIDE.md) for the
distinction between live evidence and reproducible offline checks. The public
repository does not contain credentials, private client data, or a production
gateway.

## Tools and APIs

| Tool or capability | MVP use | Credentials |
| --- | --- | --- |
| n8n | Visual workflow orchestration, webhook trigger, branching, sub-workflows, and response delivery | Configured outside GitHub |
| DuckDuckGo Lite HTML search | Public web discovery in the Revenue Resilience P0 slice | None |
| HTTP Request / public web sources | Retrieves public search and organization information | None for the retained P0 run |
| Local RAG corpus | Retrieves transparent Revenue Resilience framework context from `knowledge/revenue_resilience_corpus.json` | None |
| React, TypeScript, and Vite | Consultant review interface and printable brief | None |

No secrets are committed. Future model or data providers must use n8n
credentials or server-side environment variables, never browser-exposed
variables.

## Setup and run

### Requirements

- Node.js 20 or later and npm
- Python 3.11 or later
- n8n for importing and demonstrating the workflow JSON

### 1. Run the consultant web application

```bash
cd apps/intellectus-web
npm install
cp .env.example .env.local
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

To use the validated n8n adapter, set the following value in `.env.local`:

```text
VITE_DIAGNOSTIC_WEBHOOK_URL=<approved n8n webhook URL>
```

Leave it empty to use the explicit local demo. Never place a token or secret in
a `VITE_*` variable because Vite exposes it to the browser.

### 2. Verify the web application

```bash
cd apps/intellectus-web
npm run verify
```

This runs linting, strict type checking, tests, runtime guardrails, and the
production build.

### 3. Verify the workflow artifacts

From the repository root:

```bash
python scripts/validate_n8n_skeletons.py
python scripts/validate_fixtures.py
python scripts/test_n8n_71_intellectus_web_adapter.py
python scripts/test_n8n_53_operations_cx.py
python scripts/validate_paola_p0_output.py runs/paola_p0_givedirectly.json
```

### 4. Regenerate the sample reports

```bash
python scripts/generate_sample_reports.py
```

The command deterministically creates the two Markdown reports in `samples/`
from the retained JSON artifacts. It does not call an external model or invent
missing evidence.

### 5. Import the n8n workflow

The submitted Intellectus webhook export is
[workflows/skeletons/71_INTELLECTUS_WEB_ADAPTER.json](workflows/skeletons/71_INTELLECTUS_WEB_ADAPTER.json).
It is inactive by default and contains no credentials. Follow
[docs/INTELLECTUS_71_N8N_IMPORT.md](docs/INTELLECTUS_71_N8N_IMPORT.md) and
[workflows/IMPORT_ORDER.md](workflows/IMPORT_ORDER.md). Confirm the child
workflow ID in the target n8n environment before activation.

## Sample reports

- [Fictional River Learning Collective — Operations & CX](samples/01_fictional_river_learning_collective.md)
- [GiveDirectly — Revenue Resilience P0](samples/02_givedirectly_revenue_resilience.md)

Both reports state their provenance and limitations. The first is a fictional
controlled demonstration. The second is a retained public-search P0 run and is
not a complete organizational diagnosis.

## Future GTM sprints

The post-MVP validation plan is in
[gtm_future_sprints.md](gtm_future_sprints.md). It covers design-partner
validation, self-initiated repeat use, and a bounded paid-pilot test.

## Demo

The planned submission format is a **live 5–7 minute demonstration**. The
timed sequence, evidence to show, and fallback path are documented in
[demo/DEMO_RUNBOOK.md](demo/DEMO_RUNBOOK.md).

If the course requires an asynchronous recording instead, add the recording
URL here before submission.

Live n8n screenshots must be placed in `docs/screenshots/` using the capture
instructions in [docs/screenshots/README.md](docs/screenshots/README.md).

## File map

| Path | Purpose |
| --- | --- |
| `README.md` | Setup, execution, architecture, evidence, and submission map |
| `stack_decision.md` | Why n8n is primary and LangGraph is secondary |
| `gtm_future_sprints.md` | Three post-MVP GTM and validation sprints |
| `samples/` | Two reproducibly generated sample reports |
| `demo/DEMO_RUNBOOK.md` | Timed 5–7 minute demonstration guide |
| `workflows/skeletons/` | Sanitized n8n workflow JSON exports |
| `workflows/dev/` | Deterministic development/test workflows |
| `contracts/` | JSON contracts for evidence, findings, recommendations, and reports |
| `fixtures/` | Controlled inputs and expected response envelopes |
| `runs/` | Retained bounded run outputs |
| `scripts/` | Configuration, tests, validation, and report generation |
| `apps/intellectus-web/` | React/TypeScript consultant review experience |
| `docs/` | Architecture, integration, audit, and configuration documentation |

## Current limitations

- Most architecture workflows remain inactive templates; the verified live
  boundary is the documented 71 -> child workflow path.
- The default web demo uses local sample data and does not perform remote
  research.
- The repository does not prove production authorization, rate limiting,
  retention, or client-data governance.
- KPI baselines and targets remain unknown until validated with a client.
- Technical proof does not establish buyer demand, commercial value, or
  diagnostic accuracy for real organizations.

