# Gretel Workflow 60 n8n Import and Live Test

`60_TRANSFORMATION_ORCHESTRATOR` is orchestration only. It validates the Paola handoff, conditionally calls workflow 53, merges findings, and calls workflows 61-66 in sequence. It does not reproduce specialist reasoning.

## Compatibility baseline

The previous repository export used `n8n-nodes-base.executeWorkflow` with `typeVersion: 1` and a plain string `workflowId`. Current n8n source deliberately displays the out-of-date warning for versions `<= 1.1`.

Workflow 60 and its DEV runner now use:

```json
{
  "type": "n8n-nodes-base.executeWorkflow",
  "typeVersion": 1.3,
  "parameters": {
    "source": "database",
    "workflowId": {
      "__rl": true,
      "value": "",
      "mode": "list",
      "cachedResultName": ""
    },
    "mode": "once",
    "options": {
      "waitForSubWorkflow": true
    }
  }
}
```

The empty resource-locator value is intentional. Select the real imported workflow from the list after import; do not paste or commit an environment-specific workflow ID. `workflowInputs` is omitted because the existing child triggers accept the incoming item as-is.

Workflow 60's seven child nodes also set `onError: "continueErrorOutput"`. In Execute Sub-workflow version 1.3, n8n routes errors through one supported error output. The repository connections already route that output to the matching controlled-failure node.

Current n8n references:

- [Execute Sub-workflow source](https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/ExecuteWorkflow/ExecuteWorkflow/ExecuteWorkflow.node.ts)
- [Execute Sub-workflow documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow/)

## Exact files and import order

Import in this order:

1. `workflows/skeletons/53_OPERATIONS_CX_AGENT.json`
2. `workflows/skeletons/61_HYPOTHESIS_BUILDER.json`
3. `workflows/skeletons/62_ROOT_CAUSE_DIAGNOSIS.json`
4. `workflows/skeletons/63_ACTION_DESIGN.json`
5. `workflows/skeletons/64_KPI_DESIGN.json`
6. `workflows/skeletons/65_CLIENT_VALIDATION_QUESTIONS.json`
7. `workflows/skeletons/66_90_DAY_ROADMAP.json`
8. `workflows/skeletons/60_TRANSFORMATION_ORCHESTRATOR.json`
9. `workflows/dev/DEV_GRETEL_60_TRANSFORMATION_TEST.json`

Do not import or configure workflow 70 during this phase.

## Seven manual child selections

In workflow 60, open each existing Execute Sub-workflow node and select the corresponding imported workflow. Do not delete or recreate nodes or connections.

1. `TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX` -> `53_OPERATIONS_CX_AGENT`
2. `TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER` -> `61_HYPOTHESIS_BUILDER`
3. `TODO_LINK_SUBWORKFLOW__62_ROOT_CAUSE_DIAGNOSIS` -> `62_ROOT_CAUSE_DIAGNOSIS`
4. `TODO_LINK_SUBWORKFLOW__63_ACTION_DESIGN` -> `63_ACTION_DESIGN`
5. `TODO_LINK_SUBWORKFLOW__64_KPI_DESIGN` -> `64_KPI_DESIGN`
6. `TODO_LINK_SUBWORKFLOW__65_CLIENT_VALIDATION_QUESTIONS` -> `65_CLIENT_VALIDATION_QUESTIONS`
7. `TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP` -> `66_90_DAY_ROADMAP`

Save workflow 60. In the DEV workflow, select the imported `60_TRANSFORMATION_ORCHESTRATOR` in its three existing Execute Sub-workflow nodes: normal, insufficient evidence, and controlled failure.

## Orchestration behavior

```text
Paola handoff
-> validate upstream payload
-> Operations/CX applicable?
   -> yes: Execute 53
   -> no: explicit safe skip
-> merge upstream + 53 findings
-> Execute 61 -> validate hypotheses[]
-> Execute 62 -> validate hypotheses[] + diagnoses[]
-> Execute 63 -> validate hypotheses[] + diagnoses[] + recommendations[]
-> Execute 64 -> validate prior collections + kpis[]
-> Execute 65 -> validate prior collections + validation_questions[]
-> Execute 66 -> validate all six collections and traceability
-> final six-collection runtime contract gate
-> exact Gretel Track output
```

Successful output contains exactly:

- `hypotheses[]`
- `diagnoses[]`
- `recommendations[]`
- `kpis[]`
- `validation_questions[]`
- `roadmap_actions[]`

The merge preserves `run_context`, `sources[]`, `evidence[]`, `findings[]`, `unknowns[]`, `contradictions[]`, and `rag_metadata`. It appends Operations/CX findings and rejects duplicate finding IDs, dangling evidence references, and cross-domain Operations/CX evidence references.

## Controlled child failures

Each child call has this prebuilt routing:

```text
Execute child
├ success -> validate child output -> next child
└ error   -> controlled partial-failure output
```

Each post-child validator is cumulative: it verifies both the new collection and every collection produced by earlier children. If a collection disappears, the guard uses the same controlled-failure route; downstream children do not execute. A separate gate immediately before the success output verifies that all six collections still exist and are arrays.

A failure stops dependent downstream stages. The output keeps all six Gretel collections at the top level and adds:

- `orchestration_status: "partial_failure"`
- `run_id`
- `failed_workflow`
- `completed_workflows[]`
- `missing_collections[]`, populated with the exact missing cumulative collections for a runtime-contract failure
- `error.message`
- `upstream_payload`, containing the partial valid state: valid upstream data and surviving completed transformation outputs

The six collection schemas are unchanged. A handled parent execution may appear technically completed in n8n, so never use the execution color alone: inspect `orchestration_status` and the DEV assertions.

## Three-case live test

Run `DEV_GRETEL_60_TRANSFORMATION_TEST` once after its three workflow 60 selections are saved.

### Normal

Expected:

- 53 runs and its findings merge without collisions.
- 61-66 complete.
- Hypotheses remain validation-dependent.
- Unknown KPI baselines remain `null / unknown`.
- Final output has all six collections.

### Insufficient evidence

Expected:

- 53 is explicitly skipped because no Operations/CX input exists.
- Diagnosis remains `unknown` or evidence-limited.
- Recommendations require human review.
- KPI baseline remains `null` with `baseline_status: "unknown"`.
- Roadmap remains discovery/validation-first.

### Controlled child failure

The embedded development-only fixture includes an untraceable finding with an empty evidence-reference array. Workflow 53 completes, then workflow 61 rejects the missing traceability.

Expected:

- `orchestration_status` is `partial_failure`.
- `failed_workflow` is `61_HYPOTHESIS_BUILDER`.
- `completed_workflows` records completion of the 53-or-skip stage.
- Error information is present.
- Original and 53-generated findings remain available in `upstream_payload`.
- Workflows 62-66 do not run on this branch.

The terminal node `FINAL__ALL_60_CASES_PASSED` must return `status: "passed"` with three scenario summaries.

## Verifying live execution

1. Confirm no Execute Sub-workflow node displays an out-of-date warning.
2. Confirm all seven child selections remain populated after save/reopen.
3. Run the DEV workflow.
4. Confirm the normal and insufficient branches traverse their expected child executions.
5. Confirm the failure branch stops at 61 and returns explicit `partial_failure` rather than a normal Gretel result.
6. Inspect the final DEV item for three passing scenario summaries.
7. Inspect nested executions to confirm the expected children actually ran.
8. Confirm the normal execution traverses `FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS` before `OUTPUT_CONTRACT__GRETEL_TRACK`.

Only after these checks pass in the team instance may workflow 60 and workflows 61-66 be called live-n8n verified.

## Exporting a confirmed live workflow back to Git

If n8n changes the workflow JSON during live verification:

1. Download/export the saved workflow 60 and DEV workflow from n8n.
2. Compare their node `type`, `typeVersion`, `parameters`, `onError`, positions, and connections with the repository exports.
3. Do not commit real workflow IDs, credentials, `versionId`, instance metadata, or other environment-specific values.
4. Update `scripts/configure_gretel_60_n8n_exports.py` first so the generator remains the source of truth.
5. Keep each repository `workflowId.value` empty and `mode: "list"` unless the team explicitly adopts portable IDs later.
6. Regenerate with `python3 scripts/configure_gretel_60_n8n_exports.py`.
7. Run the full repository validation below and review the diff before committing.

Do not replace only the generated JSON without updating its generator.

## Repository validation

```bash
python3 scripts/test_n8n_60_transformation.py
python3 scripts/test_n8n_53_operations_cx.py
python3 scripts/test_n8n_gretel_p0.py
python3 scripts/validate_fixtures.py
python3 scripts/validate_n8n_skeletons.py
git diff --check
```

These checks prove repository/export compatibility only. They do not replace execution in the team n8n instance.
