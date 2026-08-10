import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
CONTRACT_DIR = ROOT / "contracts"


REQUIRED_WORKFLOWS = [
    "00_MAIN_ORCHESTRATOR.json",
    "10_INTAKE_AND_ORG_RESOLVER.json",
    "20_CONTEXT_RESEARCH_ORCHESTRATOR.json",
    "21_WEB_SEARCH.json",
    "22_WEBSITE_EXTRACTION.json",
    "23_DOCUMENT_PUBLIC_DATA_RESEARCH.json",
    "24_NEWS_EXTERNAL_CONTEXT.json",
    "30_EVIDENCE_PIPELINE.json",
    "40_RAG_RETRIEVAL_PIPELINE.json",
    "50_ANALYSIS_ORCHESTRATOR.json",
    "51_REVENUE_RESILIENCE_AGENT.json",
    "52_IMPACT_EVIDENCE_AGENT.json",
    "53_OPERATIONS_CX_AGENT.json",
    "54_EVIDENCE_GAP_RESEARCH.json",
    "60_TRANSFORMATION_ORCHESTRATOR.json",
    "61_HYPOTHESIS_BUILDER.json",
    "62_ROOT_CAUSE_DIAGNOSIS.json",
    "63_ACTION_DESIGN.json",
    "64_KPI_DESIGN.json",
    "65_CLIENT_VALIDATION_QUESTIONS.json",
    "66_90_DAY_ROADMAP.json",
    "70_REPORT_QA_DELIVERY.json",
    "99_GLOBAL_ERROR_HANDLER.json",
]

REQUIRED_CONTRACTS = [
    "run_context.schema.json",
    "source.schema.json",
    "evidence.schema.json",
    "finding.schema.json",
    "hypothesis.schema.json",
    "diagnosis.schema.json",
    "validation_question.schema.json",
    "kpi.schema.json",
    "roadmap_action.schema.json",
    "recommendation.schema.json",
    "final_package.schema.json",
]

REQUIRED_DOCS = [
    ROOT / "workflows" / "WORKFLOW_MAP.md",
    ROOT / "workflows" / "IMPORT_ORDER.md",
    ROOT / "workflows" / "CONFIGURATION_CHECKLIST.md",
    ROOT / "contracts" / "README.md",
    ROOT / "docs" / "ARCHITECTURE_FREEZE.md",
    ROOT / "docs" / "FUTURE_BACKLOG.md",
    ROOT / "docs" / "TRACK_INTEGRATION_CONTRACT.md",
    ROOT / "docs" / "PHASE2_CONFIGURATION_MATRIX.md",
    ROOT / "docs" / "GIT_PARALLEL_WORK.md",
    ROOT / "docs" / "PAOLA_P0_VERTICAL_SLICE.md",
    ROOT / "docs" / "PAOLA_P0_N8N_IMPORT.md",
    ROOT / "tests" / "PHASE2_TEST_PLAN.md",
    ROOT / "stack_decision.md",
]

REQUIRED_DEV_WORKFLOWS = [
    ROOT / "workflows" / "dev" / "DEV_PAOLA_P0_LIVE_TEST.json",
]

REQUIRED_FIXTURES = [
    ROOT / "fixtures" / "organization_input.json",
    ROOT / "fixtures" / "source_example.json",
    ROOT / "fixtures" / "evidence_example.json",
    ROOT / "fixtures" / "finding_example.json",
    ROOT / "fixtures" / "paola_track_output.json",
    ROOT / "fixtures" / "gretel_track_output.json",
    ROOT / "fixtures" / "final_package_example.json",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE),
    re.compile(r"password\s*[:=]\s*['\"][^'\"]{4,}['\"]", re.IGNORECASE),
    re.compile(r"token\s*[:=]\s*['\"][^'\"]{12,}['\"]", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"][^'\"]{12,}['\"]", re.IGNORECASE),
]


def fail(errors, message):
    errors.append(message)


def walk_for_key(value, target_key):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == target_key:
                yield value
            yield from walk_for_key(child, target_key)
    elif isinstance(value, list):
        for child in value:
            yield from walk_for_key(child, target_key)


def node_names(workflow):
    return [node.get("name") for node in workflow.get("nodes", [])]


def has_trigger(workflow):
    trigger_types = {
        "n8n-nodes-base.manualTrigger",
        "n8n-nodes-base.executeWorkflowTrigger",
        "n8n-nodes-base.errorTrigger",
        "n8n-nodes-base.webhook",
    }
    return any(node.get("type") in trigger_types for node in workflow.get("nodes", []))


def has_terminal_output(workflow):
    for node in workflow.get("nodes", []):
        name = node.get("name", "")
        js_code = node.get("parameters", {}).get("jsCode", "")
        if (
            name.startswith("OUTPUT")
            or name.startswith("RETURN")
            or name.startswith("FINAL")
            or "TERMINAL_OUTPUT_NODE" in js_code
        ):
            return True
    return False


def validate_workflow(path, workflow, errors):
    if not isinstance(workflow, dict):
        fail(errors, f"{path.name}: workflow JSON must be an object")
        return

    if workflow.get("active") is not False:
        fail(errors, f"{path.name}: active must be false")

    names = node_names(workflow)
    if not names:
        fail(errors, f"{path.name}: no nodes found")
    if len(names) != len(set(names)):
        fail(errors, f"{path.name}: duplicate node names found")

    if not has_trigger(workflow):
        fail(errors, f"{path.name}: no explicit trigger/start path found")

    if not has_terminal_output(workflow):
        fail(errors, f"{path.name}: no explicit output/terminal node found")

    if list(walk_for_key(workflow, "credentials")):
        fail(errors, f"{path.name}: credential block present")

    serialized = json.dumps(workflow)
    for pattern in SECRET_PATTERNS:
        if pattern.search(serialized):
            fail(errors, f"{path.name}: possible secret matched pattern {pattern.pattern}")

    existing = set(names)
    connections = workflow.get("connections", {})
    for source_name, outputs in connections.items():
        if source_name not in existing:
            fail(errors, f"{path.name}: connection source missing node {source_name}")
        main_outputs = outputs.get("main", [])
        for output_index, output_group in enumerate(main_outputs):
            for connection in output_group:
                target = connection.get("node")
                if target not in existing:
                    fail(
                        errors,
                        f"{path.name}: connection from {source_name} output {output_index} references missing node {target}",
                    )


def main():
    errors = []

    for filename in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / filename
        if not path.exists():
            fail(errors, f"Missing workflow file: {path}")

    expected_workflow_files = set(REQUIRED_WORKFLOWS)
    for path in WORKFLOW_DIR.glob("*.json"):
        if path.name not in expected_workflow_files:
            fail(errors, f"Unexpected workflow file: {path}")

    for filename in REQUIRED_CONTRACTS:
        path = CONTRACT_DIR / filename
        if not path.exists():
            fail(errors, f"Missing contract file: {path}")

    expected_contract_files = set(REQUIRED_CONTRACTS)
    for path in CONTRACT_DIR.glob("*.schema.json"):
        if path.name not in expected_contract_files:
            fail(errors, f"Unexpected contract file: {path}")

    for path in REQUIRED_DOCS:
        if not path.exists():
            fail(errors, f"Missing documentation file: {path}")

    for path in REQUIRED_DEV_WORKFLOWS:
        if not path.exists():
            fail(errors, f"Missing dev workflow file: {path}")

    for path in REQUIRED_FIXTURES:
        if not path.exists():
            fail(errors, f"Missing fixture file: {path}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"{path.name}: invalid fixture JSON: {exc}")

    workflow_names = {}
    for path in sorted(WORKFLOW_DIR.glob("*.json")):
        try:
            workflow = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"{path.name}: invalid JSON: {exc}")
            continue

        name = workflow.get("name")
        if not name:
            fail(errors, f"{path.name}: workflow name missing")
        elif name in workflow_names:
            fail(errors, f"{path.name}: duplicate workflow name also used by {workflow_names[name]}")
        else:
            workflow_names[name] = path.name

        validate_workflow(path, workflow, errors)

    for path in REQUIRED_DEV_WORKFLOWS:
        if not path.exists():
            continue
        try:
            workflow = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"{path.name}: invalid dev workflow JSON: {exc}")
            continue
        validate_workflow(path, workflow, errors)

    for path in sorted(CONTRACT_DIR.glob("*.schema.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"{path.name}: invalid schema JSON: {exc}")

    if errors:
        print("n8n skeleton validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("n8n skeleton validation PASSED")
    print(f"- workflows checked: {len(REQUIRED_WORKFLOWS)}")
    print(f"- contracts checked: {len(REQUIRED_CONTRACTS)}")
    print(f"- docs checked: {len(REQUIRED_DOCS)}")
    print(f"- fixtures checked: {len(REQUIRED_FIXTURES)}")
    print(f"- dev workflows checked: {len(REQUIRED_DEV_WORKFLOWS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
