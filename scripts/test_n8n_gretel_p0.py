#!/usr/bin/env python3
"""Offline execution and contract test for the JavaScript embedded in n8n workflows 61-66.

This emulates Code-node item passing and IF/Merge routing. It does not claim that an
n8n instance imported or executed the exports; live verification remains a manual step.
"""

import json
import subprocess
from pathlib import Path

from validate_fixtures import GRETEL_COLLECTIONS, load_schemas, validate_value


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
DEV_WORKFLOW = ROOT / "workflows" / "dev" / "DEV_GRETEL_P0_LIVE_TEST.json"


def load_workflow(number, name):
    path = WORKFLOW_DIR / f"{number}_{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


WORKFLOWS = {
    "61": load_workflow("61", "HYPOTHESIS_BUILDER"),
    "62": load_workflow("62", "ROOT_CAUSE_DIAGNOSIS"),
    "63": load_workflow("63", "ACTION_DESIGN"),
    "64": load_workflow("64", "KPI_DESIGN"),
    "65": load_workflow("65", "CLIENT_VALIDATION_QUESTIONS"),
    "66": load_workflow("66", "90_DAY_ROADMAP"),
}


def node(workflow, name):
    return next(candidate for candidate in workflow["nodes"] if candidate["name"] == name)


def run_code(workflow, name, items):
    code = node(workflow, name)["parameters"]["jsCode"]
    harness = """
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
        raise RuntimeError(f"{workflow['name']} / {name}: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def split(items, field):
    yes = [item for item in items if item["json"].get(field) is True]
    no = [item for item in items if item["json"].get(field) is not True]
    return yes, no


def run_61(payload):
    workflow = WORKFLOWS["61"]
    expanded = run_code(workflow, "INPUT_CONTRACT__FINDINGS_EVIDENCE_UNKNOWNS", [{"json": payload}])
    observed, uncertain = split(expanded, "can_observe_internal_reality")
    merged = []
    if observed:
        merged += run_code(workflow, "PRESERVE_OBSERVED_INTERPRETATION", observed)
    if uncertain:
        merged += run_code(workflow, "BUILD_HYPOTHESIS_FROM_GAP", uncertain)
    checked = run_code(workflow, "CONFIDENCE_AND_VALIDATION_GAP", merged)
    structured = run_code(workflow, "STRUCTURE_HYPOTHESIS_RECORDS", checked)
    return run_code(workflow, "OUTPUT_CONTRACT__HYPOTHESES", structured)[0]["json"]


def run_62(payload):
    workflow = WORKFLOWS["62"]
    expanded = run_code(workflow, "INPUT_CONTRACT__FINDINGS_HYPOTHESES", [{"json": payload}])
    scored = run_code(workflow, "EVALUATE_EVIDENCE_STRENGTH", expanded)
    validated, public = split(scored, "direct_validation_present")
    merged = []
    if validated:
        merged += run_code(workflow, "CLASSIFY__VALIDATED_CAUSE", validated)
    if public:
        merged += run_code(workflow, "CLASSIFY__PUBLIC_EVIDENCE", public)
    checked = run_code(workflow, "TRACEABILITY_AND_VALIDATION_BOUNDARY_CHECK", merged)
    return run_code(workflow, "OUTPUT_CONTRACT__DIAGNOSES", checked)[0]["json"]


def run_63(payload):
    workflow = WORKFLOWS["63"]
    expanded = run_code(workflow, "INPUT_CONTRACT__DIAGNOSES_FINDINGS", [{"json": payload}])
    validation, improvement = split(expanded, "validation_required")
    merged = []
    if validation:
        merged += run_code(workflow, "BUILD__VALIDATION_OR_DISCOVERY_ACTION", validation)
    if improvement:
        merged += run_code(workflow, "BUILD__IMPROVEMENT_ACTION", improvement)
    checked = run_code(workflow, "MISSION_AND_PROPORTIONALITY_CHECK", merged)
    structured = run_code(workflow, "STRUCTURE_RECOMMENDATIONS", checked)
    return run_code(workflow, "OUTPUT_CONTRACT__RECOMMENDATIONS", structured)[0]["json"]


def run_64(payload):
    workflow = WORKFLOWS["64"]
    expanded = run_code(workflow, "INPUT_CONTRACT__RECOMMENDATIONS_DIAGNOSES", [{"json": payload}])
    outcomes = run_code(workflow, "DEFINE_DESIRED_OUTCOME", expanded)
    known, unknown = split(outcomes, "baseline_known")
    merged = []
    if known:
        merged += run_code(workflow, "PRESERVE_KNOWN_BASELINE", known)
    if unknown:
        merged += run_code(workflow, "SET_UNKNOWN_BASELINE_TO_NULL", unknown)
    measured = run_code(workflow, "DEFINE_MEASUREMENT_METHOD", merged)
    structured = run_code(workflow, "STRUCTURE_KPIS_AND_SYNC_RECOMMENDATIONS", measured)
    return run_code(workflow, "OUTPUT_CONTRACT__KPIS", structured)[0]["json"]


def run_65(payload):
    workflow = WORKFLOWS["65"]
    items = run_code(workflow, "INPUT_CONTRACT__HYPOTHESES_UNKNOWNS_DIAGNOSES", [{"json": payload}])
    items = run_code(workflow, "DETERMINE_VALIDATION_GAP", items)
    items = run_code(workflow, "GENERATE_NEUTRAL_QUESTION", items)
    items = run_code(workflow, "LEADING_LANGUAGE_CHECK", items)
    items = run_code(workflow, "TRACEABILITY_CHECK", items)
    return run_code(workflow, "OUTPUT_CONTRACT__VALIDATION_QUESTIONS", items)[0]["json"]


def run_66(payload):
    workflow = WORKFLOWS["66"]
    expanded = run_code(workflow, "INPUT_CONTRACT__TRANSFORMATION_COMPONENTS", [{"json": payload}])
    validation, improvement = split(expanded, "validation_first")
    merged = []
    if validation:
        merged += run_code(workflow, "BUILD__VALIDATION_OR_DISCOVERY_TASK", validation)
    if improvement:
        merged += run_code(workflow, "BUILD__IMPROVEMENT_TASK", improvement)
    sequenced = run_code(workflow, "SEQUENCE__30_60_90_DAYS", merged)
    structured = run_code(workflow, "STRUCTURE_AND_VALIDATE_ROADMAP", sequenced)
    return run_code(workflow, "OUTPUT_CONTRACT__GRETEL_TRACK", structured)[0]["json"]


def run_pipeline(fixture_name):
    payload = json.loads((ROOT / "fixtures" / fixture_name).read_text(encoding="utf-8"))
    for runner in [run_61, run_62, run_63, run_64, run_65, run_66]:
        payload = runner(payload)
    return payload


def validate_contracts(output, label):
    schemas = load_schemas()
    assert set(output) == set(GRETEL_COLLECTIONS), f"{label}: unexpected top-level keys"
    for key, schema_name in GRETEL_COLLECTIONS.items():
        assert isinstance(output[key], list), f"{label}.{key} must be an array"
        for index, item in enumerate(output[key]):
            validate_value(item, schemas[schema_name], schemas, f"{label}.{key}[{index}]")


def validate_exports():
    for number, workflow in WORKFLOWS.items():
        serialized = json.dumps(workflow)
        assert "SKELETON_PLACEHOLDER" not in serialized, f"{number}: skeleton placeholder remains"
        assert "TODO_AGENT" not in serialized, f"{number}: agent placeholder remains"
        assert any(n["type"] == "n8n-nodes-base.executeWorkflowTrigger" for n in workflow["nodes"])
        assert any(n["type"] == "n8n-nodes-base.code" for n in workflow["nodes"])
        assert workflow["active"] is False
    for number in ["61", "62", "63", "64", "66"]:
        assert any(n["type"] == "n8n-nodes-base.if" for n in WORKFLOWS[number]["nodes"])
        assert any(n["type"] == "n8n-nodes-base.merge" for n in WORKFLOWS[number]["nodes"])

    dev = json.loads(DEV_WORKFLOW.read_text(encoding="utf-8"))
    links = [n for n in dev["nodes"] if n["type"] == "n8n-nodes-base.executeWorkflow"]
    assert len(links) == 6
    assert all(link["parameters"].get("workflowId") == "" for link in links)
    assert [link["name"].split("__", 1)[1][:2] for link in links] == ["61", "62", "63", "64", "65", "66"]


def counts(output):
    return {key: len(output[key]) for key in GRETEL_COLLECTIONS}


def main():
    validate_exports()
    normal = run_pipeline("paola_track_output.json")
    insufficient = run_pipeline("paola_track_insufficient_evidence.json")
    validate_contracts(normal, "normal")
    validate_contracts(insufficient, "insufficient")

    assert counts(normal) == {
        "hypotheses": 2,
        "diagnoses": 2,
        "recommendations": 2,
        "kpis": 2,
        "validation_questions": 2,
        "roadmap_actions": 2,
    }
    assert [d["diagnosis_type"] for d in normal["diagnoses"]] == ["likely_cause", "unknown"]
    assert all(kpi["baseline"] is None and kpi["baseline_status"] == "unknown" for kpi in normal["kpis"])
    assert [action["action_type"] for action in normal["roadmap_actions"]] == ["validation", "discovery"]
    assert all(action["time_bucket"] == "30_days" for action in normal["roadmap_actions"])

    assert counts(insufficient) == {key: 1 for key in GRETEL_COLLECTIONS}
    assert insufficient["diagnoses"][0]["diagnosis_type"] == "unknown"
    assert insufficient["recommendations"][0]["requires_human_review"] is True
    assert insufficient["kpis"][0]["baseline"] is None
    assert insufficient["kpis"][0]["baseline_status"] == "unknown"
    assert insufficient["validation_questions"][0]["finding_ids"]
    assert insufficient["validation_questions"][0]["hypothesis_ids"]
    assert insufficient["roadmap_actions"][0]["action_type"] == "discovery"
    assert insufficient["roadmap_actions"][0]["time_bucket"] == "30_days"

    print("Gretel n8n export validation PASSED")
    print(f"- normal output counts: {json.dumps(counts(normal), sort_keys=True)}")
    print(f"- normal diagnosis types: {[d['diagnosis_type'] for d in normal['diagnoses']]}")
    print(f"- normal roadmap types: {[a['action_type'] for a in normal['roadmap_actions']]}")
    print(f"- insufficient output counts: {json.dumps(counts(insufficient), sort_keys=True)}")
    print(f"- insufficient diagnosis type: {insufficient['diagnoses'][0]['diagnosis_type']}")
    print(f"- insufficient KPI baseline: {insufficient['kpis'][0]['baseline']!r} / {insufficient['kpis'][0]['baseline_status']}")
    print(f"- insufficient roadmap: {insufficient['roadmap_actions'][0]['time_bucket']} / {insufficient['roadmap_actions'][0]['action_type']}")
    print("- live n8n execution: NOT RUN (n8n CLI/runtime unavailable in this environment)")


if __name__ == "__main__":
    main()
