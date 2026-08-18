#!/usr/bin/env python3
"""Offline structure and contract tests for the final Intellectus webhook.

This harness executes exported Code-node JavaScript and verifies the committed
workflow boundary. It does not replay live n8n executions 3015 or 3016.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_71 = ROOT / "workflows" / "skeletons" / "71_INTELLECTUS_WEB_ADAPTER.json"
LIVE_REQUEST = ROOT / "fixtures" / "intellectus_71_live_request.json"
SUCCESS_RESPONSE = ROOT / "fixtures" / "intellectus_71_success_response.json"
LIVE_WORKFLOW_ID = "tBC3Pb82V2g5epzC"
CHILD_WORKFLOW_ID = "62QlFvCwJ8b3weif"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def node(workflow, name):
    return next(candidate for candidate in workflow["nodes"] if candidate["name"] == name)


def run_code(workflow, name, items, contexts=None):
    code = node(workflow, name)["parameters"]["jsCode"]
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


def validate_request(workflow, request):
    webhook_item = {
        "headers": {"content-type": "application/json"},
        "params": {},
        "query": {},
        "body": request,
        "webhookUrl": "https://n8n.example/webhook-test/intellectus-diagnostic",
        "executionMode": "test",
    }
    return run_code(workflow, "VALIDATE__WEB_REQUEST", [{"json": webhook_item}])[0]["json"]


def validate_export(workflow):
    assert workflow["id"] == LIVE_WORKFLOW_ID
    assert workflow["name"] == "INTELLECTUS_LIVE_WEBHOOK"
    assert workflow["active"] is False

    webhook = node(workflow, "WEBHOOK__POST_INTELLECTUS_DIAGNOSTIC")
    assert webhook["parameters"]["httpMethod"] == "POST"
    assert webhook["parameters"]["responseMode"] == "responseNode"
    assert webhook.get("webhookId") == LIVE_WORKFLOW_ID

    execute = node(workflow, "CALL__DEV_PROJECT3_END_TO_END")
    assert execute["typeVersion"] == 1.3
    assert execute["parameters"]["source"] == "database"
    assert execute["parameters"]["workflowId"] == {
        "__rl": True,
        "value": CHILD_WORKFLOW_ID,
        "mode": "list",
        "cachedResultName": "DEV_PROJECT3_END_TO_END",
    }
    assert execute["parameters"]["mode"] == "once"
    assert execute["parameters"]["options"]["waitForSubWorkflow"] is True
    assert execute["onError"] == "continueErrorOutput"

    decision_request = node(workflow, "DECISION__WEB_REQUEST_VALID")
    decision_response = node(workflow, "DECISION__FINAL_RESPONSE_VALID")
    for decision in (decision_request, decision_response):
        condition = decision["parameters"]["conditions"]["conditions"][0]
        assert condition["leftValue"] == "={{ $json.valid }}"

    responses = {
        candidate["name"]: candidate["parameters"]["options"]["responseCode"]
        for candidate in workflow["nodes"]
        if candidate["type"] == "n8n-nodes-base.respondToWebhook"
    }
    assert responses == {
        "RESPOND__INVALID_REQUEST_400": 400,
        "RESPOND__SUCCESS_200": 200,
        "RESPOND__INVALID_CHILD_RESPONSE_502": 502,
        "RESPOND__CHILD_WORKFLOW_ERROR_502": 502,
    }

    serialized = json.dumps(workflow)
    assert "TODO_LINK_SUBWORKFLOW" not in serialized
    assert '"value": ""' not in serialized
    assert "evidence_handoff" in serialized
    assert not any("credentials" in candidate for candidate in workflow["nodes"])


def main():
    workflow = load(WORKFLOW_71)
    live = load(LIVE_REQUEST)
    success = load(SUCCESS_RESPONSE)
    validate_export(workflow)

    valid_request = validate_request(workflow, live)
    assert valid_request["valid"] is True
    assert valid_request["demo"] is False
    assert valid_request["correlation_id"] == live["correlation_id"]
    assert valid_request["intake"] == live["intake"]

    invalid = copy.deepcopy(live)
    invalid["contract_version"] = "9.9"
    invalid_result = validate_request(workflow, invalid)
    assert invalid_result["valid"] is False
    assert invalid_result["response"]["status"] == "error"
    assert invalid_result["response"]["error"] == {"code": "invalid_request"}

    legacy = copy.deepcopy(live)
    legacy["evidence_handoff"] = {"run_context": {}}
    assert validate_request(workflow, legacy)["valid"] is False

    demo = copy.deepcopy(live)
    demo["mode"] = "demo"
    assert validate_request(workflow, demo)["valid"] is False

    oversized = copy.deepcopy(live)
    oversized["intake"]["current_challenge"] = "e" * 270_000
    assert validate_request(workflow, oversized)["valid"] is False

    live_success = copy.deepcopy(success)
    live_success["demo"] = False
    live_success["correlation_id"] = valid_request["correlation_id"]
    live_success["run_id"] = valid_request["run_id"]
    live_success["data"]["intake"] = live["intake"]
    output = run_code(
        workflow,
        "VALIDATE__FINAL_RESPONSE",
        [{"json": live_success}],
        {"VALIDATE__WEB_REQUEST": valid_request},
    )[0]["json"]
    assert output["valid"] is True
    assert output["response"]["status"] == "completed"
    assert output["response"]["demo"] is False

    bad_child = copy.deepcopy(live_success)
    bad_child["demo"] = True
    bad_output = run_code(
        workflow,
        "VALIDATE__FINAL_RESPONSE",
        [{"json": bad_child}],
        {"VALIDATE__WEB_REQUEST": valid_request},
    )[0]["json"]
    assert bad_output["valid"] is False
    assert bad_output["response"]["error"] == {"code": "invalid_upstream_response"}

    error_output = run_code(
        workflow,
        "MAP__CHILD_WORKFLOW_ERROR",
        [{"json": {"error": "sensitive internal stack"}}],
        {"VALIDATE__WEB_REQUEST": valid_request},
    )[0]["json"]["response"]
    assert error_output["status"] == "error"
    assert error_output["error"] == {"code": "upstream_failure"}
    assert "sensitive" not in json.dumps(error_output)

    print("Final Intellectus webhook offline validation PASSED")
    print("- architecture ids and child workflow selector: PASSED")
    print("- request validator produces valid and rejects legacy evidence_handoff: PASSED")
    print("- final response validator reads valid and enforces demo=false: PASSED")
    print("- live n8n executions 3015/3016: NOT REPLAYED by this offline harness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
