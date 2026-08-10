# Gretel P0 n8n Import and Test Guide

This guide configures the repository-side Phase 2B Gretel transformation chain. Architecture v1 and all shared contracts remain unchanged. The workflows are inactive by default, contain no credentials, and execute deterministic development logic directly in n8n Code, IF, and Merge nodes. They do not invoke the local Python transformation script.

## 1. JSON files to import

Import these repository exports from `workflows/skeletons/`:

1. `61_HYPOTHESIS_BUILDER.json`
2. `62_ROOT_CAUSE_DIAGNOSIS.json`
3. `63_ACTION_DESIGN.json`
4. `64_KPI_DESIGN.json`
5. `65_CLIENT_VALIDATION_QUESTIONS.json`
6. `66_90_DAY_ROADMAP.json`

Then import the development runner:

7. `workflows/dev/DEV_GRETEL_P0_LIVE_TEST.json`

Do not import or configure workflow 53, workflow 60, or workflow 70 as part of this test.

## 2. Import order

Import workflows 61 through 66 in numeric order, followed by `DEV_GRETEL_P0_LIVE_TEST`.

Each of workflows 61-66 is a leaf sub-workflow with an Execute Sub-workflow Trigger. The development runner is imported last so its six Execute Sub-workflow nodes can be linked to real n8n workflow IDs.

## 3. Manual sub-workflow linking

The repository deliberately contains no fabricated n8n workflow IDs. In `DEV_GRETEL_P0_LIVE_TEST`, open each node below and select the corresponding imported workflow:

| Development runner node | Select imported workflow |
| --- | --- |
| `TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER` | `61_HYPOTHESIS_BUILDER` |
| `TODO_LINK_SUBWORKFLOW__62_ROOT_CAUSE_DIAGNOSIS` | `62_ROOT_CAUSE_DIAGNOSIS` |
| `TODO_LINK_SUBWORKFLOW__63_ACTION_DESIGN` | `63_ACTION_DESIGN` |
| `TODO_LINK_SUBWORKFLOW__64_KPI_DESIGN` | `64_KPI_DESIGN` |
| `TODO_LINK_SUBWORKFLOW__65_CLIENT_VALIDATION_QUESTIONS` | `65_CLIENT_VALIDATION_QUESTIONS` |
| `TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP` | `66_90_DAY_ROADMAP` |

Keep each Execute Sub-workflow node configured to wait for the child workflow to complete. Do not activate any workflow for the manual development test.

## 4. Expected first test

In `DEV_SELECT_TEST_CASE`, leave:

```javascript
return [{ json: { selected_case: 'normal' } }];
```

Run the workflow manually. The visible path is:

```text
Manual Trigger
-> normal fixture selection
-> DEV_INPUT__PAOLA_TRACK_FIXTURE
-> 61_HYPOTHESIS_BUILDER
-> 62_ROOT_CAUSE_DIAGNOSIS
-> 63_ACTION_DESIGN
-> 64_KPI_DESIGN
-> 65_CLIENT_VALIDATION_QUESTIONS
-> 66_90_DAY_ROADMAP
-> FINAL_GRETEL_TRACK_OUTPUT
```

The development input is embedded from `fixtures/paola_track_output.json` and is clearly labelled as fixture data. It is not production data.

## 5. Expected normal output

`FINAL_GRETEL_TRACK_OUTPUT` returns exactly these top-level arrays:

```json
{
  "hypotheses": [],
  "diagnoses": [],
  "recommendations": [],
  "kpis": [],
  "validation_questions": [],
  "roadmap_actions": []
}
```

For the current normal fixture, the deterministic repository export produces:

- 2 hypotheses, both with `requires_validation: true` and finding/evidence traceability.
- 2 diagnoses: one `likely_cause` and one `unknown`; neither is `validated_cause`.
- 2 validation-first recommendations.
- 2 KPIs with `baseline: null` and `baseline_status: "unknown"`.
- 2 neutral validation questions linked to findings and hypotheses.
- 2 30-day roadmap actions: one `validation` and one `discovery`.

## 6. Insufficient-evidence test

Change only `DEV_SELECT_TEST_CASE` to:

```javascript
return [{ json: { selected_case: 'insufficient_evidence' } }];
```

Run the development workflow again. The false branch selects `DEV_INPUT__INSUFFICIENT_EVIDENCE_FIXTURE`, embedded from `fixtures/paola_track_insufficient_evidence.json`.

Expected result:

- 1 low-confidence hypothesis requiring validation.
- 1 `unknown` diagnosis.
- 1 validation-first recommendation with human review required.
- 1 KPI with `baseline: null` and `baseline_status: "unknown"`.
- 1 neutral question linked to both a source finding and hypothesis.
- 1 `30_days` roadmap action with `action_type: "discovery"`.
- No invented numerical baseline or target.
- No implementation task derived from the unvalidated hypothesis.

## 7. Export configured workflows back to the repository

After successful execution inside n8n:

1. Export each configured workflow as JSON from n8n.
2. Preserve the repository filenames listed in section 1.
3. Replace only the matching files under `workflows/skeletons/` and `workflows/dev/`.
4. Inspect the diff and verify that no credentials, credential IDs, secrets, or unrelated n8n instance metadata were exported.
5. Keep workflows inactive in repository JSON.
6. Run:

```bash
python3 scripts/validate_n8n_skeletons.py
python3 scripts/validate_fixtures.py
python3 scripts/test_n8n_gretel_p0.py
```

7. If the configured export changes repository logic intentionally, update `scripts/configure_gretel_p0_n8n_exports.py` to reproduce the same JSON. The repository and its configuration script remain the source of truth.

The local test harness emulates the JavaScript in the exported n8n Code nodes and validates its contract output. It does not replace an actual import-and-run test in n8n, and its success must not be reported as live n8n verification.
