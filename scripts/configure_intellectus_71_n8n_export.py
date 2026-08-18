#!/usr/bin/env python3
"""Validate the committed final Intellectus live webhook export.

The final canonical export is maintained in
workflows/skeletons/71_INTELLECTUS_WEB_ADAPTER.json. This script intentionally
does not regenerate the previous 71 -> 53 adapter.
"""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "skeletons" / "71_INTELLECTUS_WEB_ADAPTER.json"
LIVE_REQUEST_PATH = ROOT / "fixtures" / "intellectus_71_live_request.json"
LIVE_WORKFLOW_ID = "tBC3Pb82V2g5epzC"
CHILD_WORKFLOW_ID = "62QlFvCwJ8b3weif"


def main():
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    request = json.loads(LIVE_REQUEST_PATH.read_text(encoding="utf-8"))
    errors = []

    if workflow.get("id") != LIVE_WORKFLOW_ID:
        errors.append("INTELLECTUS_LIVE_WEBHOOK ID mismatch")
    if workflow.get("name") != "INTELLECTUS_LIVE_WEBHOOK":
        errors.append("workflow name mismatch")
    execute_nodes = [
        node for node in workflow.get("nodes", [])
        if node.get("type") == "n8n-nodes-base.executeWorkflow"
    ]
    if len(execute_nodes) != 1:
        errors.append("expected exactly one Execute Workflow node")
    elif execute_nodes[0].get("parameters", {}).get("workflowId", {}).get("value") != CHILD_WORKFLOW_ID:
        errors.append("DEV_PROJECT3_END_TO_END ID mismatch")
    serialized = json.dumps(workflow)
    if "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX" in serialized or '"value": ""' in serialized:
        errors.append("obsolete empty 53 selector remains")
    if request.get("mode") != "live" or "evidence_handoff" in request:
        errors.append("live request fixture does not match final public request")

    if errors:
        print("Intellectus final export validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Intellectus final export validation PASSED")
    print(f"- live webhook ID: {LIVE_WORKFLOW_ID}")
    print(f"- child workflow ID: {CHILD_WORKFLOW_ID}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
