# Intellectus Project 3 Demo Runbook

Target duration: 6 minutes 30 seconds. The presenter should use the live n8n
execution and React application when available. If a live service fails, show
the retained artifacts and state clearly that the fallback is repository
evidence, not a new live run.

## 0:00–0:40 — Problem and product

Explain that consultants often begin with scattered websites, reports, and
public records. Intellectus turns bounded evidence into a reviewable starting
map for a client conversation. It separates observed facts, inferences,
hypotheses, and unknowns instead of filling gaps with confident text.

## 0:40–1:20 — Stack decision

Show `stack_decision.md` and the workflow map.

- n8n is primary because the MVP is integration-heavy and benefits from visible
  triggers, branches, sub-workflows, validation, and error paths.
- It also supports parallel ownership of research and transformation modules.
- LangGraph remains secondary for a future version requiring more complex,
  stateful reasoning.

## 1:20–2:40 — Autonomous workflow path

Show the live n8n workflow and explain:

```text
web trigger -> workflow 71 -> DEV_PROJECT3_END_TO_END
            -> evidence/specialist processing -> validated response
```

Use a safe test organization. Trigger the flow once. Show that the parent
execution completes, invokes the child workflow, and returns a structured
response. Point out that no credential appears in the repository export.

Evidence to show:

- parent execution `3015` and child execution `3016`, or a newer clearly
  identified live run;
- HTTP status and terminal workflow status;
- a redacted request and response;
- the matching workflow names and IDs.

## 2:40–4:10 — Structured report and human review

Open the React application and move through the five steps:

1. intake;
2. diagnostic overview;
3. client questions;
4. bounded next step and measures;
5. reviewed conversation brief.

Use the Fictional River Learning Collective example. Show:

- the observed digital volunteer entry point;
- the unknown internal follow-up process;
- the hypothesis about possible handoffs;
- the validation question;
- the action to map the process before recommending automation;
- the KPI with an unknown baseline.

State that a consultant reviews the output before client use.

## 4:10–5:10 — Second report and tools

Open `samples/02_givedirectly_revenue_resilience.md`. Explain that this retained
P0 run used public search, evidence normalization, local RAG context, and the
Revenue Resilience agent. The system surfaced relevant financial sources but
did not infer funding concentration from search snippets.

Name at least three tools/capabilities: n8n, DuckDuckGo Lite search, HTTP/public
web retrieval, local RAG, and the React review interface.

## 5:10–6:05 — Future GTM sprints

Show `gtm_future_sprints.md`:

1. test one real pre-engagement workflow;
2. observe self-initiated repeat use and the human-review burden;
3. test a bounded paid commitment and document the buying path.

Explain that technical feasibility is not proof of buyer demand.

## 6:05–6:30 — Close

Close with:

> Intellectus does not replace consulting judgment. It gives the consultant a
> faster, clearer, and more defensible starting point while keeping uncertainty
> and human accountability visible.

## Before presenting or recording

- Run `npm run verify` in `apps/intellectus-web`.
- Run the workflow and fixture validators from the root README.
- Confirm the webhook URL is not visible in the recording.
- Confirm no credentials, personal data, or private client data are visible.
- Capture the workflow and execution screenshots described in
  `docs/screenshots/README.md`.
- Keep the final presentation between five and seven minutes.

