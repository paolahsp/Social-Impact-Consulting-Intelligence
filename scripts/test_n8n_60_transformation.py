#!/usr/bin/env python3
"""Offline orchestration, contract, and export test for workflow 60.

This calls the existing workflow 53 and 61-66 export harnesses as child-workflow
boundaries. It does not claim that an n8n instance imported or executed workflow 60.
"""

import copy
import json
import subprocess
from pathlib import Path

from test_n8n_53_operations_cx import run_workflow as run_53
from test_n8n_gretel_p0 import (
    run_61,
    run_62,
    run_63,
    run_64,
    run_65,
    run_66,
    validate_contracts,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "skeletons" / "60_TRANSFORMATION_ORCHESTRATOR.json"
WORKFLOW_53_PATH = ROOT / "workflows" / "skeletons" / "53_OPERATIONS_CX_AGENT.json"
DEV_PATH = ROOT / "workflows" / "dev" / "DEV_GRETEL_60_TRANSFORMATION_TEST.json"
GRETEL_KEYS = [
    "hypotheses",
    "diagnoses",
    "recommendations",
    "kpis",
    "validation_questions",
    "roadmap_actions",
]
CHILD_NAMES = {
    "61": "HYPOTHESIS_BUILDER",
    "62": "ROOT_CAUSE_DIAGNOSIS",
    "63": "ACTION_DESIGN",
    "64": "KPI_DESIGN",
    "65": "CLIENT_VALIDATION_QUESTIONS",
    "66": "90_DAY_ROADMAP",
}
EXECUTE_SUBWORKFLOW_TYPE_VERSION = 1.3


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def node(workflow, name):
    return next(candidate for candidate in workflow["nodes"] if candidate["name"] == name)


def run_code(workflow, name, items, references=None):
    code = node(workflow, name)["parameters"]["jsCode"]
    harness = r"""
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
global.$ = (name) => {
  if (!Object.prototype.hasOwnProperty.call(input.references, name)) throw new Error(`Missing test reference ${name}`);
  return { first: () => ({ json: input.references[name] }) };
};
try {
  const result = new Function('items', input.code)(input.items);
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
}
"""
    completed = subprocess.run(
        ["node", "-e", harness],
        input=json.dumps({"code": code, "items": items, "references": references or {}}),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"60 / {name}: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def run_pipeline(workflow, workflow_53, fixture):
    references = {}
    wrapped = run_code(workflow, "INPUT_CONTRACT__PAOLA_HANDOFF", [{"json": copy.deepcopy(fixture)}])
    references["INPUT_CONTRACT__PAOLA_HANDOFF"] = wrapped[0]["json"]
    if wrapped[0]["json"]["operations_cx_applicable"]:
        prepared = run_code(workflow, "PREPARE__53_INPUT", wrapped)
        leaf = run_53(workflow_53, prepared[0]["json"])
        branch = run_code(workflow, "VALIDATE__53_FINDINGS", [{"json": leaf}], references)
    else:
        branch = run_code(workflow, "SKIP__53_NOT_APPLICABLE", wrapped)

    merged = run_code(workflow, "MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS", branch, references)
    payload = merged[0]["json"]
    references["MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS"] = payload

    runners = [run_61, run_62, run_63, run_64, run_65, run_66]
    for number, runner in zip(["61", "62", "63", "64", "65", "66"], runners):
        payload = runner(payload)
        references[f"TODO_LINK_SUBWORKFLOW__{number}_{CHILD_NAMES[number]}"] = payload
        payload = run_code(workflow, f"VALIDATE__{number}_OUTPUT", [{"json": payload}], references)[0]["json"]
        references[f"VALIDATE__{number}_OUTPUT"] = payload

    payload = run_code(workflow, "FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS", [{"json": payload}], references)[0]["json"]
    references["FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS"] = payload
    return run_code(workflow, "OUTPUT_CONTRACT__GRETEL_TRACK", [{"json": payload}])[0]["json"], references


def output_counts(output):
    return {key: len(output[key]) for key in GRETEL_KEYS}


def assert_current_execute_node(candidate):
    parameters = candidate["parameters"]
    selector = parameters.get("workflowId")
    assert candidate["type"] == "n8n-nodes-base.executeWorkflow"
    assert candidate["typeVersion"] == EXECUTE_SUBWORKFLOW_TYPE_VERSION
    assert parameters.get("source") == "database"
    assert isinstance(selector, dict), "Current Execute Sub-workflow requires a workflow selector object"
    assert selector.get("__rl") is True
    assert selector.get("value") == "", "Repository export must not fabricate a workflow ID"
    assert selector.get("mode") == "list"
    assert parameters.get("mode") == "once"
    assert parameters.get("options", {}).get("waitForSubWorkflow") is True
    assert "workflowInputs" not in parameters, "Accept-all-data child triggers must not emit a stale mapper"


def validate_export(workflow, dev):
    assert workflow["name"] == "60_TRANSFORMATION_ORCHESTRATOR"
    assert workflow["active"] is False
    serialized = json.dumps(workflow)
    assert "SKELETON_PLACEHOLDER" not in serialized
    assert "TODO_AGENT" not in serialized
    assert not any("credentials" in candidate for candidate in workflow["nodes"])

    execute_nodes = [candidate for candidate in workflow["nodes"] if candidate["type"] == "n8n-nodes-base.executeWorkflow"]
    assert len(execute_nodes) == 7
    for candidate in execute_nodes:
        assert_current_execute_node(candidate)
    assert all(candidate.get("onError") == "continueErrorOutput" for candidate in execute_nodes)
    assert [candidate["name"].split("__", 1)[1][:2] for candidate in execute_nodes] == ["53", "61", "62", "63", "64", "65", "66"]

    code_names = {candidate["name"] for candidate in workflow["nodes"] if candidate["type"] == "n8n-nodes-base.code"}
    for number in ["53", "61", "62", "63", "64", "65", "66"]:
        assert f"VALIDATE__{number}_{'FINDINGS' if number == '53' else 'OUTPUT'}" in code_names
        assert f"OUTPUT__CONTROLLED_FAILURE__{number}" in code_names
    for forbidden in [
        "BUILD_HYPOTHESIS_FROM_GAP",
        "CLASSIFY__PUBLIC_EVIDENCE",
        "BUILD__VALIDATION_OR_DISCOVERY_ACTION",
        "DEFINE_DESIRED_OUTCOME",
        "GENERATE_NEUTRAL_QUESTION",
        "SEQUENCE__30_60_90_DAYS",
    ]:
        assert forbidden not in code_names, f"60 duplicates child specialist node {forbidden}"

    connections = workflow["connections"]
    for execute in execute_nodes:
        outputs = connections[execute["name"]]["main"]
        assert len(outputs) == 2 and outputs[0] and outputs[1], f"{execute['name']} lacks explicit error output"
    for number in ["53", "61", "62", "63", "64", "65", "66"]:
        validator = f"VALIDATE__{number}_{'FINDINGS' if number == '53' else 'OUTPUT'}"
        outputs = connections[validator]["main"]
        assert len(outputs) == 2 and outputs[0] and outputs[1], f"{validator} lacks normal/error routing"
        assert outputs[1][0]["node"] == f"OUTPUT__CONTROLLED_FAILURE__{number}"

    final_gate = node(workflow, "FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS")
    assert final_gate.get("onError") == "continueErrorOutput"
    final_outputs = connections[final_gate["name"]]["main"]
    assert len(final_outputs) == 2 and final_outputs[0] and final_outputs[1]
    assert final_outputs[0][0]["node"] == "OUTPUT_CONTRACT__GRETEL_TRACK"
    assert final_outputs[1][0]["node"] == "OUTPUT__CONTROLLED_FAILURE__66"
    assert connections["VALIDATE__66_OUTPUT"]["main"][0][0]["node"] == final_gate["name"]

    assert dev["name"] == "DEV_GRETEL_60_TRANSFORMATION_TEST"
    assert dev["active"] is False
    dev_executes = [candidate for candidate in dev["nodes"] if candidate["type"] == "n8n-nodes-base.executeWorkflow"]
    assert len(dev_executes) == 3
    for candidate in dev_executes:
        assert_current_execute_node(candidate)
    assert {candidate["name"] for candidate in dev_executes} == {
        "TODO_LINK_SUBWORKFLOW__60_NORMAL",
        "TODO_LINK_SUBWORKFLOW__60_INSUFFICIENT",
        "TODO_LINK_SUBWORKFLOW__60_CONTROLLED_FAILURE",
    }
    assert node(dev, "FINAL__ALL_60_CASES_PASSED")


def validate_late_failure_state(workflow, references):
    partial = references["VALIDATE__63_OUTPUT"]
    failure = run_code(
        workflow,
        "OUTPUT__CONTROLLED_FAILURE__64",
        [{"json": {"error": {"message": "Synthetic child failure for repository test"}}}],
        {"VALIDATE__63_OUTPUT": partial},
    )[0]["json"]
    assert failure["orchestration_status"] == "partial_failure"
    assert failure["failed_workflow"] == "64_KPI_DESIGN"
    assert "Synthetic child failure" in failure["error"]["message"]
    assert all(key in failure for key in GRETEL_KEYS)
    assert failure["hypotheses"]
    assert failure["diagnoses"]
    assert failure["recommendations"]
    assert failure["kpis"] == []
    assert failure["validation_questions"] == []
    assert failure["roadmap_actions"] == []
    assert failure["upstream_payload"]["findings"]


def expect_guard_failure(workflow, validator, payload, references, missing):
    try:
        run_code(workflow, validator, [{"json": payload}], references)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError(f"{validator} accepted missing cumulative collection {missing}")
    assert "RUNTIME_CONTRACT_MISSING" in message
    assert missing in message
    return message


def validate_runtime_state_loss_guards(workflow, references):
    cases = [
        ("61", "hypotheses", ["53_OPERATIONS_CX_AGENT_OR_SKIP"]),
        ("62", "hypotheses", ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER"]),
        ("63", "diagnoses", ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS"]),
        ("64", "recommendations", ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS", "63_ACTION_DESIGN"]),
        ("65", "kpis", ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS", "63_ACTION_DESIGN", "64_KPI_DESIGN"]),
        ("66", "validation_questions", ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS", "63_ACTION_DESIGN", "64_KPI_DESIGN", "65_CLIENT_VALIDATION_QUESTIONS"]),
    ]
    results = []
    for number, missing, completed in cases:
        child_name = f"TODO_LINK_SUBWORKFLOW__{number}_{CHILD_NAMES[number]}"
        malformed = copy.deepcopy(references[child_name])
        del malformed[missing]
        guard_refs = dict(references)
        guard_refs[child_name] = malformed
        message = expect_guard_failure(
            workflow,
            f"VALIDATE__{number}_OUTPUT",
            malformed,
            guard_refs,
            missing,
        )
        failure = run_code(
            workflow,
            f"OUTPUT__CONTROLLED_FAILURE__{number}",
            [{"json": {"error": {"message": message}}}],
            guard_refs,
        )[0]["json"]
        assert failure["orchestration_status"] == "partial_failure"
        assert failure["failed_workflow"] == f"{number}_{CHILD_NAMES[number]}"
        assert failure["missing_collections"] == [missing]
        assert failure["completed_workflows"] == completed
        assert failure["upstream_payload"] == malformed or number == "61"
        for key in GRETEL_KEYS:
            if key in malformed and isinstance(malformed[key], list):
                assert failure[key] == malformed[key], f"{number} failed to preserve surviving {key}[]"
        results.append(f"{number}:{missing}")

    final_payload = copy.deepcopy(references["VALIDATE__66_OUTPUT"])
    del final_payload["roadmap_actions"]
    message = expect_guard_failure(
        workflow,
        "FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS",
        final_payload,
        references,
        "roadmap_actions",
    )
    final_refs = dict(references)
    final_refs["TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP"] = final_payload
    final_failure = run_code(
        workflow,
        "OUTPUT__CONTROLLED_FAILURE__66",
        [{"json": {"error": {"message": message}}}],
        final_refs,
    )[0]["json"]
    assert final_failure["missing_collections"] == ["roadmap_actions"]
    assert final_failure["failed_workflow"] == "66_90_DAY_ROADMAP"
    assert final_failure["completed_workflows"] == cases[-1][2]
    assert final_failure["hypotheses"] and final_failure["validation_questions"]
    assert final_failure["roadmap_actions"] == []
    return results


def controlled_failure_fixture(normal_fixture):
    payload = copy.deepcopy(normal_fixture)
    payload["run_context"]["run_id"] = "RUN-CONTROLLED-CHILD-FAILURE"
    payload["run_context"]["current_challenge"] = "Verify controlled workflow 61 failure routing"
    for evidence in payload["evidence"]:
        evidence["run_id"] = payload["run_context"]["run_id"]
    payload["rag_metadata"]["retrieval_run_id"] = "RAG-CONTROLLED-CHILD-FAILURE"
    payload["findings"].append({
        "finding_id": "F-DEV-FAIL-001",
        "domain": "impact_evidence",
        "finding": "This development-only finding intentionally has no evidence references so workflow 61 rejects it instead of fabricating traceability.",
        "evidence_ids": [],
        "finding_type": "unknown",
        "confidence": 0.2,
        "requires_validation": True,
        "validation_question": "What evidence would be required to assess this development-only test finding?",
    })
    return payload


def run_controlled_child_failure(workflow, workflow_53, normal_fixture):
    fixture = controlled_failure_fixture(normal_fixture)
    references = {}
    wrapped = run_code(workflow, "INPUT_CONTRACT__PAOLA_HANDOFF", [{"json": fixture}])
    references["INPUT_CONTRACT__PAOLA_HANDOFF"] = wrapped[0]["json"]
    prepared = run_code(workflow, "PREPARE__53_INPUT", wrapped)
    leaf = run_53(workflow_53, prepared[0]["json"])
    branch = run_code(workflow, "VALIDATE__53_FINDINGS", [{"json": leaf}], references)
    merged = run_code(workflow, "MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS", branch, references)[0]["json"]
    try:
        run_61(merged)
    except RuntimeError as exc:
        failure = run_code(
            workflow,
            "OUTPUT__CONTROLLED_FAILURE__61",
            [{"json": {"error": str(exc)}}],
            {"MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS": merged},
        )[0]["json"]
    else:
        raise AssertionError("Development failure fixture did not make workflow 61 fail")
    assert failure["orchestration_status"] == "partial_failure"
    assert failure["failed_workflow"] == "61_HYPOTHESIS_BUILDER"
    assert failure["completed_workflows"] == ["53_OPERATIONS_CX_AGENT_OR_SKIP"]
    assert failure["missing_collections"] == []
    assert failure["error"]["message"]
    assert all(key in failure and isinstance(failure[key], list) for key in GRETEL_KEYS)
    assert failure["upstream_payload"]["run_context"]["run_id"] == "RUN-CONTROLLED-CHILD-FAILURE"
    assert any(record["finding_id"] == "F-DEV-FAIL-001" for record in failure["upstream_payload"]["findings"])
    assert any(record["finding_id"].startswith("F-OPS-") for record in failure["upstream_payload"]["findings"])
    return failure


def main():
    workflow = load_json(WORKFLOW_PATH)
    workflow_53 = load_json(WORKFLOW_53_PATH)
    dev = load_json(DEV_PATH)
    normal_fixture = load_json(ROOT / "fixtures" / "paola_track_output.json")
    insufficient_fixture = load_json(ROOT / "fixtures" / "paola_track_insufficient_evidence.json")

    validate_export(workflow, dev)
    normal, normal_references = run_pipeline(workflow, workflow_53, normal_fixture)
    insufficient, insufficient_references = run_pipeline(workflow, workflow_53, insufficient_fixture)
    controlled_failure = run_controlled_child_failure(workflow, workflow_53, normal_fixture)
    validate_contracts(normal, "workflow60.normal")
    validate_contracts(insufficient, "workflow60.insufficient")
    validate_contracts(
        {key: controlled_failure[key] for key in GRETEL_KEYS},
        "workflow60.controlled_failure.partial_output",
    )

    assert normal_references["INPUT_CONTRACT__PAOLA_HANDOFF"]["operations_cx_applicable"] is True
    merged_normal = normal_references["MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS"]
    assert len(merged_normal["findings"]) > len(normal_fixture["findings"])
    assert len({finding["finding_id"] for finding in merged_normal["findings"]}) == len(merged_normal["findings"])
    assert normal["hypotheses"] and all(record["requires_validation"] is True for record in normal["hypotheses"])
    assert all(kpi["baseline"] is None for kpi in normal["kpis"] if kpi["baseline_status"] == "unknown")

    assert insufficient_references["INPUT_CONTRACT__PAOLA_HANDOFF"]["operations_cx_applicable"] is False
    assert insufficient_references["MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS"]["findings"] == insufficient_fixture["findings"]
    assert output_counts(insufficient) == {key: 1 for key in GRETEL_KEYS}
    assert insufficient["diagnoses"][0]["diagnosis_type"] == "unknown"
    assert insufficient["recommendations"][0]["requires_human_review"] is True
    assert insufficient["kpis"][0]["baseline"] is None
    assert insufficient["kpis"][0]["baseline_status"] == "unknown"
    assert insufficient["roadmap_actions"][0]["action_type"] == "discovery"

    validate_late_failure_state(workflow, normal_references)
    runtime_guard_cases = validate_runtime_state_loss_guards(workflow, normal_references)

    print("Workflow 60 n8n export validation PASSED")
    print(f"- orchestration children: 53 -> merge -> 61 -> 62 -> 63 -> 64 -> 65 -> 66")
    print(f"- normal output counts: {json.dumps(output_counts(normal), sort_keys=True)}")
    print(f"- insufficient output counts: {json.dumps(output_counts(insufficient), sort_keys=True)}")
    print("- insufficient path: 53 skipped; diagnosis unknown; KPI baseline null/unknown; roadmap discovery-first")
    print(f"- controlled child failure: {controlled_failure['failed_workflow']} / {controlled_failure['orchestration_status']}")
    print(f"- controlled failure preserved findings: {len(controlled_failure['upstream_payload']['findings'])}")
    print("- synthetic late 64 failure: hypotheses, diagnoses, and recommendations preserved")
    print(f"- cumulative runtime state-loss guards: {', '.join(runtime_guard_cases)}")
    print("- final six-collection runtime contract gate: passed and failure-routed")
    print("- live n8n execution: NOT RUN by this offline harness")


if __name__ == "__main__":
    main()
