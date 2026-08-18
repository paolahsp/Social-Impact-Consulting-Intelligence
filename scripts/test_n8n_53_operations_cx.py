#!/usr/bin/env python3
"""Offline execution and safety test for JavaScript embedded in workflow 53.

The harness executes the exported Code-node source with canonical n8n items. It
does not claim that an n8n instance imported or executed the workflow.
"""

import copy
import json
import subprocess
from pathlib import Path

from validate_fixtures import load_schemas, validate_value


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "skeletons" / "53_OPERATIONS_CX_AGENT.json"
DEV_PATH = ROOT / "workflows" / "dev" / "DEV_GRETEL_53_OPERATIONS_CX_TEST.json"
FIXTURE_PATH = ROOT / "fixtures" / "paola_track_output.json"

NODE_PATH = [
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


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def node(workflow, name):
    return next(candidate for candidate in workflow["nodes"] if candidate["name"] == name)


def run_code(workflow, name, items):
    code = node(workflow, name)["parameters"]["jsCode"]
    harness = r"""
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
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
        input=json.dumps({"code": code, "items": items}),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        message = completed.stderr.strip().splitlines()[0]
        raise RuntimeError(f"{name}: {message}")
    return json.loads(completed.stdout)


def run_workflow(workflow, payload):
    items = [{"json": payload}]
    for name in NODE_PATH:
        items = run_code(workflow, name, items)
        assert isinstance(items, list) and items, f"{name}: expected n8n item array"
        assert isinstance(items[0], dict) and isinstance(items[0].get("json"), dict), (
            f"{name}: expected canonical {{ json: payload }} item"
        )
    return items[0]["json"]


def assert_rejected(workflow, payload, expected_fragment):
    try:
        run_workflow(workflow, payload)
    except RuntimeError as exc:
        assert expected_fragment in str(exc), str(exc)
        return
    raise AssertionError(f"Expected workflow to reject payload containing {expected_fragment!r}")


def validate_exports(workflow, dev):
    assert workflow["name"] == "53_OPERATIONS_CX_AGENT"
    assert workflow["active"] is False
    assert [n["name"] for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.code"] == NODE_PATH
    serialized = json.dumps(workflow)
    for placeholder in ["SKELETON_PLACEHOLDER", "TODO_AGENT", "TODO_API"]:
        assert placeholder not in serialized
    assert "$input.all()[0].evidence" not in serialized
    assert not any("credentials" in n for n in workflow["nodes"])

    assert dev["name"] == "DEV_GRETEL_53_OPERATIONS_CX_TEST"
    assert dev["active"] is False
    links = [n for n in dev["nodes"] if n["type"] == "n8n-nodes-base.executeWorkflow"]
    assert len(links) == 1
    assert links[0]["parameters"].get("workflowId") == ""
    compose = node(dev, "COMPOSE__53_FINDINGS_WITH_ORIGINAL_ENVELOPE")["parameters"]["jsCode"]
    assert "DEV_INPUT__PAOLA_TRACK_FIXTURE" in compose
    assert "...original" in compose and "...original.findings" in compose


def validate_normal_output(output, fixture):
    assert set(output) == {"findings"}, "53 must remain a leaf findings output"
    findings = output["findings"]
    assert findings
    by_type = {kind: [f for f in findings if f["finding_type"] == kind] for kind in [
        "observed", "inferred", "hypothesis", "unknown"
    ]}
    assert by_type["observed"], "fixture must produce an observed finding"
    assert by_type["unknown"], "fixture must preserve an unknown"
    assert by_type["hypothesis"], "fixture must produce a validation hypothesis"
    assert all(f["requires_validation"] and f["validation_question"] for f in by_type["hypothesis"])

    upstream_ids = {f["finding_id"] for f in fixture["findings"]}
    generated_ids = [f["finding_id"] for f in findings]
    assert len(generated_ids) == len(set(generated_ids))
    assert upstream_ids.isdisjoint(generated_ids)
    assert all(finding_id.startswith("F-OPS-") for finding_id in generated_ids)

    evidence_by_id = {ev["evidence_id"]: ev for ev in fixture["evidence"]}
    for finding in findings:
        assert finding["domain"] == "operations_cx"
        assert finding["evidence_ids"]
        assert all(evidence_id in evidence_by_id for evidence_id in finding["evidence_ids"])
        assert all(evidence_by_id[evidence_id]["domain"] == "operations_cx" for evidence_id in finding["evidence_ids"])
        assert not any(term in finding["finding"].lower() for term in [
            "recommend a crm", "implement a crm", "install", "salesforce"
        ])

    schemas = load_schemas()
    for index, finding in enumerate(findings):
        validate_value(
            finding,
            schemas["finding.schema.json"],
            schemas,
            f"workflow53.findings[{index}]",
        )

    composed = {**fixture, "findings": [*fixture["findings"], *findings]}
    for key in ["run_context", "sources", "evidence", "unknowns", "contradictions", "rag_metadata"]:
        assert composed[key] == fixture[key], f"composition changed upstream {key}"
    composed_ids = [f["finding_id"] for f in composed["findings"]]
    assert len(composed_ids) == len(set(composed_ids))
    return by_type, composed


def main():
    workflow = load_json(WORKFLOW_PATH)
    dev = load_json(DEV_PATH)
    fixture = load_json(FIXTURE_PATH)
    validate_exports(workflow, dev)

    output = run_workflow(workflow, copy.deepcopy(fixture))
    by_type, composed = validate_normal_output(output, fixture)

    cross_domain = copy.deepcopy(fixture)
    cross_domain["evidence"] = [ev for ev in cross_domain["evidence"] if ev["domain"] == "revenue_resilience"]
    cross_domain_output = run_workflow(workflow, cross_domain)
    assert cross_domain_output["findings"] == [], "Revenue evidence leaked into Operations/CX"

    collision = copy.deepcopy(fixture)
    collision["findings"].append({
        "finding_id": "F-OPS-001",
        "domain": "operations_cx",
        "finding": "Existing Operations/CX finding.",
        "evidence_ids": ["EV-001"],
        "finding_type": "observed",
        "confidence": 0.8,
        "requires_validation": False,
        "validation_question": None,
    })
    collision_output = run_workflow(workflow, collision)
    assert "F-OPS-001" not in {f["finding_id"] for f in collision_output["findings"]}

    dangling_unknown = copy.deepcopy(fixture)
    dangling_unknown["unknowns"].append({
        "unknown_id": "UNK-DANGLING",
        "domain": "operations_cx",
        "description": "Untraceable unknown must not become a finding.",
        "evidence_ids": ["EV-MISSING"],
    })
    dangling_output = run_workflow(workflow, dangling_unknown)
    assert all("EV-MISSING" not in f["evidence_ids"] for f in dangling_output["findings"])

    contradicted = copy.deepcopy(fixture)
    contradicted["evidence"][0]["status"] = "contradicted"
    contradicted["evidence"][0]["contradiction_ids"] = ["EV-003"]
    contradiction_output = run_workflow(workflow, contradicted)
    assert not any(f["finding_type"] == "observed" for f in contradiction_output["findings"])
    assert all(f["requires_validation"] for f in contradiction_output["findings"])

    malformed = copy.deepcopy(fixture)
    del malformed["rag_metadata"]
    assert_rejected(workflow, malformed, "rag_metadata object")

    duplicate_evidence = copy.deepcopy(fixture)
    duplicate_evidence["evidence"].append(copy.deepcopy(duplicate_evidence["evidence"][0]))
    assert_rejected(workflow, duplicate_evidence, "duplicate evidence IDs")

    print("Workflow 53 n8n export validation PASSED")
    print(f"- leaf finding counts: {json.dumps({key: len(value) for key, value in by_type.items()}, sort_keys=True)}")
    print(f"- observed: {by_type['observed'][0]['finding']}")
    print(f"- unknown: {by_type['unknown'][0]['finding']}")
    print(f"- hypothesis: {by_type['hypothesis'][0]['finding']}")
    print(f"- journey: {by_type['observed'][0]['journey']} / {by_type['observed'][0]['journey_stage']} / observed")
    print(f"- composed finding count: {len(composed['findings'])}")
    print("- cross-domain, collision, dangling-reference, contradiction, malformed-input tests: PASSED")
    print("- live n8n execution: NOT RUN by this offline harness")


if __name__ == "__main__":
    main()
