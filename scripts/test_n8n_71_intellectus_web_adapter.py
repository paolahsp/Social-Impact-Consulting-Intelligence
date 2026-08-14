#!/usr/bin/env python3
"""Offline contract and branch tests for workflow 71.

This harness executes exported Code-node JavaScript and composes it with the
existing workflow 53 harness. It proves repository behavior, not a live n8n
webhook execution.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_71 = ROOT / "workflows" / "skeletons" / "71_INTELLECTUS_WEB_ADAPTER.json"
WORKFLOW_53 = ROOT / "workflows" / "skeletons" / "53_OPERATIONS_CX_AGENT.json"
LIVE_REQUEST = ROOT / "fixtures" / "intellectus_71_live_request.json"
DEMO_REQUEST = ROOT / "fixtures" / "intellectus_71_demo_request.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def node(workflow, name):
    return next(candidate for candidate in workflow["nodes"] if candidate["name"] == name)


def run_code(workflow, name, items, contexts=None):
    code = node(workflow, name)["parameters"]["jsCode"]
    # A fresh VM context intentionally omits Node/browser Web API globals such
    # as URL and TextEncoder, matching the isolation boundary of n8n Code nodes.
    harness = r"""
const fs = require('fs');
const vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const context = vm.createContext({
  items: input.items,
  $execution: { id: 'offline-test-execution' },
  __contexts: input.contexts,
});
context.$ = name => ({ first: () => ({ json: context.__contexts[name] }) });
try {
  const result = new vm.Script(`(() => {${input.code}\n})()`).runInContext(context);
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
}
"""
    completed = subprocess.run(
        ["node", "-e", harness],
        input=json.dumps({"code": code, "items": items, "contexts": contexts or {}}),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(f"{name}: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def normalize(workflow, request):
    webhook_item = {
        "headers": {"content-type": "application/json"},
        "params": {},
        "query": {},
        "body": request,
        "webhookUrl": "https://n8n.example/webhook-test/intellectus-diagnostic",
        "executionMode": "test",
    }
    return run_code(workflow, "NORMALIZE_AND_VALIDATE_REQUEST", [{"json": webhook_item}])[0]["json"]


def run_53(workflow, payload):
    path = [
        "EVIDENCE_INPUT__PAOLA_TRACK_HANDOFF",
        "DOMAIN_FILTER__OPERATIONS_CX_ONLY",
        "JOURNEY_SIGNAL_EXTRACTION",
        "CLASSIFY__OBSERVED_INFERRED_HYPOTHESIS_UNKNOWN",
        "BUILD__OBSERVED_FINDINGS",
        "BUILD__INFERRED_AND_UNKNOWN_FINDINGS",
        "BUILD__VALIDATION_HYPOTHESES",
        "ASSIGN__COLLISION_FREE_FINDING_IDS",
        "VALIDATE__FINDING_CONTRACT_AND_TRACEABILITY",
        "OUTPUT_CONTRACT__OPERATIONS_CX_FINDINGS",
    ]
    items = [{"json": payload}]
    for name in path:
        items = run_code(workflow, name, items)
    return items[0]["json"]


def validate_export(workflow):
    assert workflow["name"] == "71_INTELLECTUS_WEB_ADAPTER"
    assert workflow["active"] is False
    webhook = node(workflow, "WEBHOOK__POST_INTELLECTUS_DIAGNOSTIC")
    assert webhook["parameters"]["httpMethod"] == "POST"
    assert webhook["parameters"]["responseMode"] == "responseNode"
    assert webhook.get("webhookId") == ""
    execute = node(workflow, "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX")
    assert execute["typeVersion"] == 1.3
    assert execute["parameters"]["source"] == "database"
    assert execute["parameters"]["workflowId"] == {
        "__rl": True, "value": "", "mode": "list", "cachedResultName": ""
    }
    assert execute["parameters"]["mode"] == "once"
    assert execute["parameters"]["options"]["waitForSubWorkflow"] is True
    assert execute["onError"] == "continueErrorOutput"
    assert not any("credentials" in candidate for candidate in workflow["nodes"])
    responses = {
        candidate["name"]: candidate["parameters"]["options"]["responseCode"]
        for candidate in workflow["nodes"]
        if candidate["type"] == "n8n-nodes-base.respondToWebhook"
    }
    assert responses == {
        "RESPOND__INVALID_REQUEST_400": 400,
        "RESPOND__NEEDS_EVIDENCE_422": 422,
        "RESPOND__SUCCESS_200": 200,
        "RESPOND__UPSTREAM_OUTPUT_ERROR_502": 502,
        "RESPOND__SUBWORKFLOW_ERROR_502": 502,
    }
    serialized = json.dumps(workflow)
    assert "Diagnostic prepared for review." in serialized
    assert "Evidence is required before this analysis can run." in serialized
    assert "53_OPERATIONS_CX_AGENT" in execute["notes"]


def main():
    workflow_71 = load(WORKFLOW_71)
    workflow_53 = load(WORKFLOW_53)
    live = load(LIVE_REQUEST)
    demo = load(DEMO_REQUEST)
    validate_export(workflow_71)
    normalize_code = node(workflow_71, "NORMALIZE_AND_VALIDATE_REQUEST")["parameters"]["jsCode"]
    assert "TextEncoder" not in normalize_code
    assert "new URL(" not in normalize_code

    normalized = normalize(workflow_71, live)
    assert normalized["request_valid"] is True and normalized["evidence_ready"] is False
    assert normalized["demo"] is False
    assert normalized["run_id"] == live["evidence_handoff"]["run_context"]["run_id"]
    assert normalized["response"]["status"] == "needs_evidence"

    invalid = copy.deepcopy(live)
    invalid["contract_version"] = "9.9"
    invalid_result = normalize(workflow_71, invalid)
    assert invalid_result["request_valid"] is False
    assert invalid_result["response"]["status"] == "error"
    assert invalid_result["response"]["error"] == {"code": "invalid_request"}

    missing = copy.deepcopy(live)
    missing.pop("evidence_handoff")
    missing.pop("run_id")
    missing_result = normalize(workflow_71, missing)
    assert missing_result["request_valid"] is True
    assert missing_result["evidence_ready"] is False
    assert missing_result["response"]["status"] == "needs_evidence"
    assert missing_result["response"]["message"] == "Evidence is required before this analysis can run."

    demo_result = normalize(workflow_71, demo)
    assert demo_result["request_valid"] is True and demo_result["evidence_ready"] is True
    assert demo_result["demo"] is True
    assert demo_result["correlation_id"] == "CORR-DEMO-001"

    unicode_oversize = copy.deepcopy(demo)
    unicode_oversize["intake"]["current_challenge"] = "é" * 131_000
    assert normalize(workflow_71, unicode_oversize)["request_valid"] is False

    mixed_demo = copy.deepcopy(demo)
    mixed_demo["evidence_handoff"] = live["evidence_handoff"]
    assert normalize(workflow_71, mixed_demo)["request_valid"] is False
    demo_with_document = copy.deepcopy(demo)
    demo_with_document["intake"]["uploaded_document_refs"] = ["DOC-001"]
    assert normalize(workflow_71, demo_with_document)["request_valid"] is False

    demo_labeled_live = copy.deepcopy(demo)
    demo_labeled_live["mode"] = "live"
    demo_labeled_live["evidence_handoff"] = demo_result["evidence_handoff"]
    assert normalize(workflow_71, demo_labeled_live)["request_valid"] is False

    adapted = run_code(
        workflow_71,
        "ADAPT__PAOLA_HANDOFF_TO_53_INPUT",
        [{"json": demo_result}],
    )[0]["json"]
    assert adapted == demo_result["evidence_handoff"]
    assert set(adapted) == {
        "run_context", "sources", "evidence", "findings", "unknowns", "contradictions", "rag_metadata"
    }

    leaf = run_53(workflow_53, adapted)
    assert set(leaf) == {"findings"} and leaf["findings"]
    output = run_code(
        workflow_71,
        "VALIDATE_AND_NORMALIZE_53_OUTPUT",
        [{"json": leaf}],
        {"NORMALIZE_AND_VALIDATE_REQUEST": demo_result},
    )[0]["json"]
    assert output["output_valid"] is True
    response = output["response"]
    assert response["status"] == "completed" and response["demo"] is True
    assert response["data"]["findings"] == leaf["findings"]
    assert response["data"]["sources"] == demo_result["evidence_handoff"]["sources"]

    bad_leaf = {"findings": [{"finding_id": "F-OPS-001"}]}
    bad_output = run_code(
        workflow_71,
        "VALIDATE_AND_NORMALIZE_53_OUTPUT",
        [{"json": bad_leaf}],
        {"NORMALIZE_AND_VALIDATE_REQUEST": demo_result},
    )[0]["json"]
    assert bad_output["output_valid"] is False
    assert bad_output["response"]["error"] == {"code": "invalid_upstream_response"}

    error_output = run_code(
        workflow_71,
        "MAP__SUBWORKFLOW_ERROR",
        [{"json": {"error": "sensitive internal stack"}}],
        {"NORMALIZE_AND_VALIDATE_REQUEST": demo_result},
    )[0]["json"]["response"]
    assert error_output["status"] == "error"
    assert error_output["error"] == {"code": "upstream_failure"}
    assert "sensitive" not in json.dumps(error_output)

    print("Workflow 71 offline validation PASSED")
    print("- valid live envelope, invalid request, and 422 needs_evidence branches: PASSED")
    print("- demo labeling and live/demo separation: PASSED")
    print("- exact Paola-to-53 adaptation and 53 output validation: PASSED")
    print("- subworkflow and invalid-output error sanitization: PASSED")
    print(f"- generated Operations/CX findings: {len(leaf['findings'])}")
    print("- live n8n webhook execution: NOT RUN by this offline harness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
