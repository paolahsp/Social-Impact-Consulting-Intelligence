#!/usr/bin/env python3
"""Generate workflow 60 and its three-scenario development-only n8n runner."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
DEV_WORKFLOW_DIR = ROOT / "workflows" / "dev"
EXECUTE_SUBWORKFLOW_TYPE_VERSION = 1.3


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=600, height=360, color=5):
    return {
        "parameters": {"content": content, "height": height, "width": width, "color": color},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
    }


def trigger(x=0, y=0):
    return {
        "parameters": {},
        "id": "start__sub_workflow_trigger",
        "name": "START__SUB_WORKFLOW_TRIGGER",
        "type": "n8n-nodes-base.executeWorkflowTrigger",
        "typeVersion": 1,
        "position": [x, y],
    }


def manual_trigger(x=0, y=0):
    return {
        "parameters": {},
        "id": "start__manual_test_trigger",
        "name": "START__MANUAL_TEST_TRIGGER",
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "position": [x, y],
    }


def code_node(name, js, x, y, error_output=False):
    result = {
        "parameters": {"jsCode": js.strip() + "\n"},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, y],
    }
    if error_output:
        result["onError"] = "continueErrorOutput"
    return result


def if_node(name, left_value, x, y):
    return {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2,
                },
                "conditions": [{
                    "id": slug(name + "_condition"),
                    "leftValue": left_value,
                    "operator": {"type": "boolean", "operation": "true", "singleValue": True},
                }],
                "combinator": "and",
            },
            "options": {},
        },
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [x, y],
    }


def merge_node(name, x, y):
    return {
        "parameters": {"mode": "append", "options": {}},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.merge",
        "typeVersion": 3,
        "position": [x, y],
    }


def execute_workflow_node(name, target, x, y, error_output=True):
    result = {
        "parameters": {
            "source": "database",
            "workflowId": {
                "__rl": True,
                "value": "",
                "mode": "list",
                "cachedResultName": "",
            },
            "mode": "once",
            "options": {"waitForSubWorkflow": True},
        },
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": EXECUTE_SUBWORKFLOW_TYPE_VERSION,
        "position": [x, y],
        "notes": f"AFTER IMPORT: select {target} from the Workflow list. No live workflow ID is committed.",
    }
    if error_output:
        result["onError"] = "continueErrorOutput"
    return result


def connections(edges):
    result = {}
    for edge in edges:
        source, target = edge[0], edge[1]
        source_index = edge[2] if len(edge) > 2 else 0
        target_index = edge[3] if len(edge) > 3 else 0
        result.setdefault(source, {"main": []})
        while len(result[source]["main"]) <= source_index:
            result[source]["main"].append([])
        result[source]["main"][source_index].append(
            {"node": target, "type": "main", "index": target_index}
        )
    return result


JS_INPUT = r"""
const payload = items[0]?.json;
if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
  throw new Error('60 input requires one canonical n8n item: { json: payload }');
}
for (const key of ['sources', 'evidence', 'findings', 'unknowns', 'contradictions']) {
  if (!Array.isArray(payload[key])) throw new Error(`60 input requires ${key}[]`);
}
if (!payload.run_context?.run_id) throw new Error('60 input requires run_context.run_id');
if (!payload.rag_metadata || typeof payload.rag_metadata !== 'object' || Array.isArray(payload.rag_metadata)) {
  throw new Error('60 input requires rag_metadata object');
}
function unique(records, key, label) {
  const values = records.map(record => record?.[key]);
  if (values.some(value => typeof value !== 'string' || !value)) throw new Error(`60 ${label} require ${key}`);
  if (new Set(values).size !== values.length) throw new Error(`60 input contains duplicate ${label} IDs`);
  return new Set(values);
}
const evidenceIds = unique(payload.evidence, 'evidence_id', 'evidence');
unique(payload.findings, 'finding_id', 'finding');
for (const finding of payload.findings) {
  if (!Array.isArray(finding.evidence_ids) || finding.evidence_ids.some(id => !evidenceIds.has(id))) {
    throw new Error(`60 finding ${finding.finding_id} has a dangling evidence reference`);
  }
}
for (const unknown of payload.unknowns) {
  if (unknown.evidence_ids && (!Array.isArray(unknown.evidence_ids) || unknown.evidence_ids.some(id => !evidenceIds.has(id)))) {
    throw new Error(`60 unknown ${unknown.unknown_id || '(unidentified)'} has a dangling evidence reference`);
  }
}
const operationsApplicable = payload.evidence.some(ev => ev?.domain === 'operations_cx') ||
  payload.unknowns.some(unknown => unknown?.domain === 'operations_cx');
return [{ json: { payload, operations_cx_applicable: operationsApplicable } }];
"""


JS_PREPARE_53 = r"""
return [{ json: items[0].json.payload }];
"""


JS_VALIDATE_53 = r"""
const leaf = items[0]?.json;
if (!leaf || !Array.isArray(leaf.findings)) throw new Error('53 returned no findings[] leaf output');
const upstream = $('INPUT_CONTRACT__PAOLA_HANDOFF').first().json.payload;
const evidenceById = new Map(upstream.evidence.map(ev => [ev.evidence_id, ev]));
const upstreamIds = new Set(upstream.findings.map(finding => finding.finding_id));
const generatedIds = new Set();
for (const finding of leaf.findings) {
  if (!finding?.finding_id || upstreamIds.has(finding.finding_id) || generatedIds.has(finding.finding_id)) {
    throw new Error(`53 returned colliding or invalid finding ID ${finding?.finding_id}`);
  }
  generatedIds.add(finding.finding_id);
  if (finding.domain !== 'operations_cx') throw new Error(`53 returned cross-domain finding ${finding.finding_id}`);
  if (!Array.isArray(finding.evidence_ids) || finding.evidence_ids.length === 0) {
    throw new Error(`53 finding ${finding.finding_id} lacks evidence_ids`);
  }
  for (const evidenceId of finding.evidence_ids) {
    const evidence = evidenceById.get(evidenceId);
    if (!evidence || evidence.domain !== 'operations_cx') {
      throw new Error(`53 finding ${finding.finding_id} has invalid evidence reference ${evidenceId}`);
    }
  }
}
return [{ json: leaf }];
"""


JS_SKIP_53 = r"""
return [{ json: { findings: [], skipped: true, reason: 'No Operations/CX evidence or unknown was supplied.' } }];
"""


JS_MERGE_FINDINGS = r"""
const original = $('INPUT_CONTRACT__PAOLA_HANDOFF').first().json.payload;
const leaf = items[0]?.json ?? {};
if (!Array.isArray(leaf.findings)) throw new Error('60 merge requires 53 findings[] or an explicit empty skip result');
const mergedFindings = [...original.findings, ...leaf.findings];
const findingIds = mergedFindings.map(finding => finding.finding_id);
if (new Set(findingIds).size !== findingIds.length) throw new Error('60 merge produced duplicate finding IDs');
const evidenceIds = new Set(original.evidence.map(ev => ev.evidence_id));
for (const finding of mergedFindings) {
  if (!Array.isArray(finding.evidence_ids) || finding.evidence_ids.some(id => !evidenceIds.has(id))) {
    throw new Error(`60 merge found dangling evidence reference on ${finding.finding_id}`);
  }
}
return [{ json: { ...original, findings: mergedFindings } }];
"""


def stage_validator(stage, collections):
    expected = json.dumps(collections, separators=(",", ":"))
    return f"""
const payload = items[0]?.json;
const expected = {expected};
const missing = expected.filter(key => !Array.isArray(payload?.[key]));
if (missing.length) {{
  throw new Error(`RUNTIME_CONTRACT_MISSING|{stage}|${{missing.join(',')}}`);
}}
return [{{ json: payload }}];
"""


JS_VALIDATE_66 = r"""
const payload = items[0]?.json;
const keys = ['hypotheses', 'diagnoses', 'recommendations', 'kpis', 'validation_questions', 'roadmap_actions'];
const missing = keys.filter(key => !Array.isArray(payload?.[key]));
if (missing.length) {
  throw new Error(`RUNTIME_CONTRACT_MISSING|66_90_DAY_ROADMAP|${missing.join(',')}`);
}
const source = $('MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS').first().json;
const evidenceIds = new Set(source.evidence.map(ev => ev.evidence_id));
const findingIds = new Set(source.findings.map(finding => finding.finding_id));
const hypothesisIds = new Set(payload.hypotheses.map(record => record.hypothesis_id));
const diagnosisIds = new Set(payload.diagnoses.map(record => record.diagnosis_id));
const recommendationIds = new Set(payload.recommendations.map(record => record.recommendation_id));
const questionIds = new Set(payload.validation_questions.map(record => record.question_id));
function allKnown(ids, known) { return Array.isArray(ids) && ids.every(id => known.has(id)); }
for (const hypothesis of payload.hypotheses) {
  if (!allKnown(hypothesis.evidence_ids, evidenceIds) || !allKnown(hypothesis.finding_ids, findingIds) || hypothesis.requires_validation !== true) {
    throw new Error(`60 traceability failure at hypothesis ${hypothesis.hypothesis_id}`);
  }
}
for (const diagnosis of payload.diagnoses) {
  if (!allKnown(diagnosis.evidence_ids, evidenceIds) || !allKnown(diagnosis.finding_ids, findingIds) || !allKnown(diagnosis.hypothesis_ids, hypothesisIds)) {
    throw new Error(`60 traceability failure at diagnosis ${diagnosis.diagnosis_id}`);
  }
}
for (const recommendation of payload.recommendations) {
  if (!allKnown(recommendation.finding_ids, findingIds) || !allKnown(recommendation.diagnosis_ids || [], diagnosisIds)) {
    throw new Error(`60 traceability failure at recommendation ${recommendation.recommendation_id}`);
  }
  if (recommendation.kpi?.baseline_status === 'unknown' && recommendation.kpi?.baseline !== null) {
    throw new Error(`60 uncertainty failure: ${recommendation.recommendation_id} invented a baseline`);
  }
}
for (const question of payload.validation_questions) {
  if (!allKnown(question.finding_ids, findingIds) || !allKnown(question.hypothesis_ids, hypothesisIds)) {
    throw new Error(`60 traceability failure at validation question ${question.question_id}`);
  }
}
for (const action of payload.roadmap_actions) {
  if (!allKnown(action.recommendation_ids, recommendationIds) || !allKnown(action.hypothesis_ids, hypothesisIds) || !allKnown(action.validation_question_ids, questionIds)) {
    throw new Error(`60 traceability failure at roadmap action ${action.roadmap_action_id}`);
  }
}
return [{ json: payload }];
"""


JS_FINAL_RUNTIME_CONTRACT = r"""
const payload = items[0]?.json;
const keys = ['hypotheses', 'diagnoses', 'recommendations', 'kpis', 'validation_questions', 'roadmap_actions'];
const missing = keys.filter(key => !Array.isArray(payload?.[key]));
if (missing.length) {
  throw new Error(`RUNTIME_CONTRACT_MISSING|FINAL_GRETEL_TRACK|${missing.join(',')}`);
}
return [{ json: payload }];
"""


JS_OUTPUT = r"""
const payload = items[0].json;
return [{ json: {
  hypotheses: payload.hypotheses,
  diagnoses: payload.diagnoses,
  recommendations: payload.recommendations,
  kpis: payload.kpis,
  validation_questions: payload.validation_questions,
  roadmap_actions: payload.roadmap_actions
} }];
"""


def failure_js(stage, checkpoint_node, child_node, expected_collections, completed, nested_payload=False):
    checkpoint = f"$('{'INPUT_CONTRACT__PAOLA_HANDOFF' if nested_payload else checkpoint_node}').first().json"
    payload = f"{checkpoint}.payload" if nested_payload else checkpoint
    expected_json = json.dumps(expected_collections, separators=(",", ":"))
    completed_json = json.dumps(completed, separators=(",", ":"))
    return f"""
const checkpoint = {payload};
const raw = items[0]?.json ?? {{}};
const message = raw.error?.message || raw.message || (typeof raw.error === 'string' ? raw.error : null) ||
  '{stage} failed or returned an incompatible payload';
const expected = {expected_json};
let childOutput = null;
try {{ childOutput = $('{child_node}').first().json; }} catch (_error) {{ childOutput = null; }}
const transformationCollections = new Set(['hypotheses', 'diagnoses', 'recommendations', 'kpis', 'validation_questions', 'roadmap_actions']);
const childHasState = childOutput && typeof childOutput === 'object' && !childOutput.error &&
  expected.some(key => transformationCollections.has(key) && Object.prototype.hasOwnProperty.call(childOutput, key));
const marker = message.match(/RUNTIME_CONTRACT_MISSING\|[^|]+\|([A-Za-z0-9_,]+)/);
const missingCollections = marker ? marker[1].split(',').filter(Boolean) :
  (childHasState ? expected.filter(key => !Array.isArray(childOutput[key])) : []);
const partial = childHasState ? childOutput : checkpoint;
return [{{ json: {{
  hypotheses: Array.isArray(partial.hypotheses) ? partial.hypotheses : [],
  diagnoses: Array.isArray(partial.diagnoses) ? partial.diagnoses : [],
  recommendations: Array.isArray(partial.recommendations) ? partial.recommendations : [],
  kpis: Array.isArray(partial.kpis) ? partial.kpis : [],
  validation_questions: Array.isArray(partial.validation_questions) ? partial.validation_questions : [],
  roadmap_actions: Array.isArray(partial.roadmap_actions) ? partial.roadmap_actions : [],
  orchestration_status: 'partial_failure',
  run_id: partial.run_context?.run_id || null,
  failed_workflow: '{stage}',
  completed_workflows: {completed_json},
  missing_collections: missingCollections,
  error: {{ message }},
  upstream_payload: partial
}} }}];
"""


CHILDREN = [
    ("61", "HYPOTHESIS_BUILDER", ["hypotheses"]),
    ("62", "ROOT_CAUSE_DIAGNOSIS", ["hypotheses", "diagnoses"]),
    ("63", "ACTION_DESIGN", ["hypotheses", "diagnoses", "recommendations"]),
    ("64", "KPI_DESIGN", ["hypotheses", "diagnoses", "recommendations", "kpis"]),
    ("65", "CLIENT_VALIDATION_QUESTIONS", ["hypotheses", "diagnoses", "recommendations", "kpis", "validation_questions"]),
    ("66", "90_DAY_ROADMAP", ["hypotheses", "diagnoses", "recommendations", "kpis", "validation_questions", "roadmap_actions"]),
]


def configure_60():
    nodes = [
        sticky(
            "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
            "PURPOSE\nOrchestrate 53 and 61-66 without duplicating specialist logic.\n\nOWNER\nGRETEL TRACK B\n\nINPUT\nExact flat Paola track handoff.\n\nSUCCESS OUTPUT\nExact Gretel Track six-array object.\n\nCHILD CALL FORMAT\nExecute Sub-workflow v1.3; database list selector; once; wait for completion; current error output.\n\nSTATUS\nPhase 2D repository-ready. Inactive. Manually select imported child workflows; no IDs or credentials are committed.",
            -650, -500, 640, 440, 4,
        ),
        sticky(
            "NOTE__VISIBLE_ORCHESTRATION_PATH",
            "Paola handoff -> Operations/CX applicable? -> 53 or explicit skip -> merge findings -> Execute 61 -> 62 -> 63 -> 64 -> 65 -> 66 -> exact Gretel output.\n\nEach child is called through Execute Sub-workflow. Code nodes only validate, merge, and control routing.",
            -650, -20, 640, 350, 5,
        ),
        sticky(
            "NOTE__CONTROLLED_CHILD_FAILURES",
            "Every Execute Sub-workflow and cumulative post-call guard uses its current n8n error output. A child failure or missing cumulative collection stops the specialist chain and returns the six Gretel collections plus orchestration_status=partial_failure, failed_workflow, completed_workflows, missing_collections, error, and upstream_payload (the partial valid state). Failures are never silently discarded.",
            -650, 370, 640, 340, 3,
        ),
        trigger(),
        code_node("INPUT_CONTRACT__PAOLA_HANDOFF", JS_INPUT, 260, 0),
        if_node("DECISION__OPERATIONS_CX_APPLICABLE", "={{ $json.operations_cx_applicable }}", 560, 0),
        code_node("PREPARE__53_INPUT", JS_PREPARE_53, 860, -180),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "53_OPERATIONS_CX_AGENT", 1160, -180),
        code_node("VALIDATE__53_FINDINGS", JS_VALIDATE_53, 1460, -180, True),
        code_node("SKIP__53_NOT_APPLICABLE", JS_SKIP_53, 1460, 180),
        code_node("MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS", JS_MERGE_FINDINGS, 1760, 0),
    ]

    x = 2060
    for number, name, collections in CHILDREN:
        target = f"{number}_{name}"
        nodes.append(execute_workflow_node(f"TODO_LINK_SUBWORKFLOW__{target}", target, x, 0))
        validator = JS_VALIDATE_66 if number == "66" else stage_validator(target, collections)
        nodes.append(code_node(f"VALIDATE__{number}_OUTPUT", validator, x + 300, 0, True))
        x += 600
    nodes.append(code_node("FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS", JS_FINAL_RUNTIME_CONTRACT, x, 0, True))
    nodes.append(code_node("OUTPUT_CONTRACT__GRETEL_TRACK", JS_OUTPUT, x + 300, 0))

    failure_specs = [
        ("53_OPERATIONS_CX_AGENT", "INPUT_CONTRACT__PAOLA_HANDOFF", "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", ["findings"], [], True),
        ("61_HYPOTHESIS_BUILDER", "MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS", "TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER", ["hypotheses"], ["53_OPERATIONS_CX_AGENT_OR_SKIP"], False),
        ("62_ROOT_CAUSE_DIAGNOSIS", "VALIDATE__61_OUTPUT", "TODO_LINK_SUBWORKFLOW__62_ROOT_CAUSE_DIAGNOSIS", ["hypotheses", "diagnoses"], ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER"], False),
        ("63_ACTION_DESIGN", "VALIDATE__62_OUTPUT", "TODO_LINK_SUBWORKFLOW__63_ACTION_DESIGN", ["hypotheses", "diagnoses", "recommendations"], ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS"], False),
        ("64_KPI_DESIGN", "VALIDATE__63_OUTPUT", "TODO_LINK_SUBWORKFLOW__64_KPI_DESIGN", ["hypotheses", "diagnoses", "recommendations", "kpis"], ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS", "63_ACTION_DESIGN"], False),
        ("65_CLIENT_VALIDATION_QUESTIONS", "VALIDATE__64_OUTPUT", "TODO_LINK_SUBWORKFLOW__65_CLIENT_VALIDATION_QUESTIONS", ["hypotheses", "diagnoses", "recommendations", "kpis", "validation_questions"], ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS", "63_ACTION_DESIGN", "64_KPI_DESIGN"], False),
        ("66_90_DAY_ROADMAP", "VALIDATE__65_OUTPUT", "TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP", ["hypotheses", "diagnoses", "recommendations", "kpis", "validation_questions", "roadmap_actions"], ["53_OPERATIONS_CX_AGENT_OR_SKIP", "61_HYPOTHESIS_BUILDER", "62_ROOT_CAUSE_DIAGNOSIS", "63_ACTION_DESIGN", "64_KPI_DESIGN", "65_CLIENT_VALIDATION_QUESTIONS"], False),
    ]
    for index, (stage, checkpoint, child, expected, completed, nested) in enumerate(failure_specs):
        nodes.append(code_node(
            f"OUTPUT__CONTROLLED_FAILURE__{stage.split('_', 1)[0]}",
            failure_js(stage, checkpoint, child, expected, completed, nested),
            1460 + index * 600,
            520,
        ))

    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__PAOLA_HANDOFF"),
        ("INPUT_CONTRACT__PAOLA_HANDOFF", "DECISION__OPERATIONS_CX_APPLICABLE"),
        ("DECISION__OPERATIONS_CX_APPLICABLE", "PREPARE__53_INPUT", 0),
        ("DECISION__OPERATIONS_CX_APPLICABLE", "SKIP__53_NOT_APPLICABLE", 1),
        ("PREPARE__53_INPUT", "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX"),
        ("TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "VALIDATE__53_FINDINGS", 0),
        ("TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "OUTPUT__CONTROLLED_FAILURE__53", 1),
        ("VALIDATE__53_FINDINGS", "MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS", 0),
        ("VALIDATE__53_FINDINGS", "OUTPUT__CONTROLLED_FAILURE__53", 1),
        ("SKIP__53_NOT_APPLICABLE", "MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS"),
        ("MERGE__UPSTREAM_AND_OPERATIONS_FINDINGS", "TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER"),
    ]
    for index, (number, name, _collections) in enumerate(CHILDREN):
        target = f"TODO_LINK_SUBWORKFLOW__{number}_{name}"
        validator = f"VALIDATE__{number}_OUTPUT"
        failure = f"OUTPUT__CONTROLLED_FAILURE__{number}"
        edges.extend([
            (target, validator, 0),
            (target, failure, 1),
            (validator, failure, 1),
        ])
        if index + 1 < len(CHILDREN):
            next_number, next_name, _ = CHILDREN[index + 1]
            edges.append((validator, f"TODO_LINK_SUBWORKFLOW__{next_number}_{next_name}", 0))
        else:
            edges.extend([
                (validator, "FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS", 0),
                ("FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS", "OUTPUT_CONTRACT__GRETEL_TRACK", 0),
                ("FINAL_RUNTIME_CONTRACT__SIX_COLLECTIONS", "OUTPUT__CONTROLLED_FAILURE__66", 1),
            ])

    return {
        "name": "60_TRANSFORMATION_ORCHESTRATOR",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def fixture_code(fixture, label):
    serialized = json.dumps(fixture, separators=(",", ":"), ensure_ascii=False)
    return f"// {label}: embedded from the repository fixture.\nconst fixture = {serialized};\nreturn [{{ json: fixture }}];"


JS_ASSERT_NORMAL = r"""
const output = items[0]?.json;
const keys = ['hypotheses', 'diagnoses', 'recommendations', 'kpis', 'validation_questions', 'roadmap_actions'];
if (!output || keys.some(key => !Array.isArray(output[key]) || output[key].length === 0)) throw new Error('Normal 60 test returned incomplete Gretel output');
if (!output.hypotheses.some(record => record.domain === 'operations_cx')) throw new Error('Normal 60 test lost Operations/CX reasoning');
if (!output.hypotheses.every(record => record.requires_validation === true)) throw new Error('Normal 60 test promoted a hypothesis to fact');
if (!output.kpis.every(kpi => kpi.baseline_status !== 'unknown' || kpi.baseline === null)) throw new Error('Normal 60 test invented a KPI baseline');
return [{ json: { test_case: 'normal', status: 'passed', counts: Object.fromEntries(keys.map(key => [key, output[key].length])) } }];
"""


JS_ASSERT_INSUFFICIENT = r"""
const output = items[0]?.json;
const keys = ['hypotheses', 'diagnoses', 'recommendations', 'kpis', 'validation_questions', 'roadmap_actions'];
if (!output || keys.some(key => !Array.isArray(output[key]) || output[key].length === 0)) throw new Error('Insufficient-evidence 60 test returned incomplete Gretel output');
if (!output.diagnoses.every(record => record.diagnosis_type === 'unknown' && record.requires_validation === true)) throw new Error('Insufficient-evidence diagnosis exceeded the evidence');
if (!output.recommendations.every(record => record.requires_human_review === true)) throw new Error('Insufficient-evidence recommendation lost human review');
if (!output.kpis.every(kpi => kpi.baseline === null && kpi.baseline_status === 'unknown')) throw new Error('Insufficient-evidence test invented a KPI baseline');
if (!output.roadmap_actions.every(action => action.action_type === 'discovery' && action.time_bucket === '30_days')) throw new Error('Insufficient-evidence roadmap did not remain discovery-first');
return [{ json: { test_case: 'insufficient_evidence', status: 'passed', counts: Object.fromEntries(keys.map(key => [key, output[key].length])) } }];
"""


JS_ASSERT_FAILURE = r"""
const output = items[0]?.json;
const keys = ['hypotheses', 'diagnoses', 'recommendations', 'kpis', 'validation_questions', 'roadmap_actions'];
if (!output || keys.some(key => !Array.isArray(output[key]))) throw new Error('Controlled-failure test lost Gretel collections');
if (output.orchestration_status !== 'partial_failure') throw new Error('Controlled child failure appeared successful');
if (output.failed_workflow !== '61_HYPOTHESIS_BUILDER') throw new Error('Controlled child failure did not identify workflow 61');
if (!Array.isArray(output.completed_workflows) || !output.completed_workflows.includes('53_OPERATIONS_CX_AGENT_OR_SKIP')) {
  throw new Error('Controlled child failure lost completed workflow state');
}
if (!output.error?.message) throw new Error('Controlled child failure lost error information');
if (!Array.isArray(output.missing_collections)) throw new Error('Controlled child failure lost missing-collection diagnostics');
if (!output.upstream_payload || !Array.isArray(output.upstream_payload.findings)) throw new Error('Controlled child failure lost upstream data');
if (!output.upstream_payload.findings.some(finding => finding.finding_id === 'F-DEV-FAIL-001')) throw new Error('Controlled child failure lost the triggering upstream finding');
if (!output.upstream_payload.findings.some(finding => /^F-OPS-/.test(finding.finding_id))) throw new Error('Controlled child failure lost completed 53 findings');
return [{ json: {
  test_case: 'controlled_child_failure',
  status: 'passed',
  failed_workflow: output.failed_workflow,
  completed_workflows: output.completed_workflows,
  preserved_finding_count: output.upstream_payload.findings.length,
  counts: Object.fromEntries(keys.map(key => [key, output[key].length]))
} }];
"""


JS_FINAL_DEV = r"""
const results = items.map(item => item.json).sort((a, b) => a.test_case.localeCompare(b.test_case));
if (results.length !== 3 || results.some(result => result.status !== 'passed')) throw new Error('All three 60 scenarios must pass in one execution');
return [{ json: { status: 'passed', scenarios: results } }];
"""


def configure_dev_60():
    normal = json.loads((ROOT / "fixtures" / "paola_track_output.json").read_text(encoding="utf-8"))
    insufficient = json.loads((ROOT / "fixtures" / "paola_track_insufficient_evidence.json").read_text(encoding="utf-8"))
    controlled_failure = json.loads(json.dumps(normal))
    controlled_failure["run_context"]["run_id"] = "RUN-CONTROLLED-CHILD-FAILURE"
    controlled_failure["run_context"]["current_challenge"] = "Verify controlled workflow 61 failure routing"
    for evidence in controlled_failure["evidence"]:
        evidence["run_id"] = controlled_failure["run_context"]["run_id"]
    controlled_failure["rag_metadata"]["retrieval_run_id"] = "RAG-CONTROLLED-CHILD-FAILURE"
    controlled_failure["findings"].append({
        "finding_id": "F-DEV-FAIL-001",
        "domain": "impact_evidence",
        "finding": "This development-only finding intentionally has no evidence references so workflow 61 rejects it instead of fabricating traceability.",
        "evidence_ids": [],
        "finding_type": "unknown",
        "confidence": 0.2,
        "requires_validation": True,
        "validation_question": "What evidence would be required to assess this development-only test finding?",
    })
    nodes = [
        sticky(
            "00_README__DEV_WORKFLOW",
            "DEV_GRETEL_60_TRANSFORMATION_TEST\nImport after 60. Link all three current Execute Sub-workflow nodes to the imported 60 workflow, then run manually.\nOne execution runs normal, insufficient-evidence, and controlled-child-failure cases and only passes after all assertions complete.\nNo workflow IDs, credentials, or production data are committed.",
            -560, -420, 620, 400, 4,
        ),
        sticky(
            "NOTE__EXPECTED_TESTS",
            "NORMAL\n53 runs, findings merge without collisions, and 61-66 return traceable transformation arrays.\n\nINSUFFICIENT EVIDENCE\n53 is explicitly skipped; uncertainty stays discovery-first and KPI baselines stay null/unknown.\n\nCONTROLLED CHILD FAILURE\n53 completes, then a development-only untraceable finding makes 61 fail. 60 must return partial_failure and preserve merged upstream findings.",
            -560, 30, 620, 460, 5,
        ),
        manual_trigger(),
        code_node("DEV_INPUT__NORMAL_PAOLA_FIXTURE", fixture_code(normal, "NORMAL"), 300, -260),
        code_node("DEV_INPUT__INSUFFICIENT_EVIDENCE_FIXTURE", fixture_code(insufficient, "INSUFFICIENT EVIDENCE"), 300, 0),
        code_node("DEV_INPUT__CONTROLLED_CHILD_FAILURE", fixture_code(controlled_failure, "CONTROLLED CHILD FAILURE"), 300, 260),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__60_NORMAL", "60_TRANSFORMATION_ORCHESTRATOR", 620, -260, False),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__60_INSUFFICIENT", "60_TRANSFORMATION_ORCHESTRATOR", 620, 0, False),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__60_CONTROLLED_FAILURE", "60_TRANSFORMATION_ORCHESTRATOR", 620, 260, False),
        code_node("ASSERT__NORMAL_PATH", JS_ASSERT_NORMAL, 940, -260),
        code_node("ASSERT__INSUFFICIENT_EVIDENCE_PATH", JS_ASSERT_INSUFFICIENT, 940, 0),
        code_node("ASSERT__CONTROLLED_CHILD_FAILURE", JS_ASSERT_FAILURE, 940, 260),
        merge_node("MERGE__SUCCESS_TEST_RESULTS", 1240, -120),
        merge_node("MERGE__ALL_TEST_RESULTS", 1480, 0),
        code_node("FINAL__ALL_60_CASES_PASSED", JS_FINAL_DEV, 1780, 0),
    ]
    edges = [
        ("START__MANUAL_TEST_TRIGGER", "DEV_INPUT__NORMAL_PAOLA_FIXTURE"),
        ("START__MANUAL_TEST_TRIGGER", "DEV_INPUT__INSUFFICIENT_EVIDENCE_FIXTURE"),
        ("START__MANUAL_TEST_TRIGGER", "DEV_INPUT__CONTROLLED_CHILD_FAILURE"),
        ("DEV_INPUT__NORMAL_PAOLA_FIXTURE", "TODO_LINK_SUBWORKFLOW__60_NORMAL"),
        ("DEV_INPUT__INSUFFICIENT_EVIDENCE_FIXTURE", "TODO_LINK_SUBWORKFLOW__60_INSUFFICIENT"),
        ("DEV_INPUT__CONTROLLED_CHILD_FAILURE", "TODO_LINK_SUBWORKFLOW__60_CONTROLLED_FAILURE"),
        ("TODO_LINK_SUBWORKFLOW__60_NORMAL", "ASSERT__NORMAL_PATH"),
        ("TODO_LINK_SUBWORKFLOW__60_INSUFFICIENT", "ASSERT__INSUFFICIENT_EVIDENCE_PATH"),
        ("TODO_LINK_SUBWORKFLOW__60_CONTROLLED_FAILURE", "ASSERT__CONTROLLED_CHILD_FAILURE"),
        ("ASSERT__NORMAL_PATH", "MERGE__SUCCESS_TEST_RESULTS", 0, 0),
        ("ASSERT__INSUFFICIENT_EVIDENCE_PATH", "MERGE__SUCCESS_TEST_RESULTS", 0, 1),
        ("MERGE__SUCCESS_TEST_RESULTS", "MERGE__ALL_TEST_RESULTS", 0, 0),
        ("ASSERT__CONTROLLED_CHILD_FAILURE", "MERGE__ALL_TEST_RESULTS", 0, 1),
        ("MERGE__ALL_TEST_RESULTS", "FINAL__ALL_60_CASES_PASSED"),
    ]
    return {
        "name": "DEV_GRETEL_60_TRANSFORMATION_TEST",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure_gretel_60_workflows(root=ROOT):
    global ROOT, WORKFLOW_DIR, DEV_WORKFLOW_DIR
    ROOT = Path(root)
    WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
    DEV_WORKFLOW_DIR = ROOT / "workflows" / "dev"
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    DEV_WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    (WORKFLOW_DIR / "60_TRANSFORMATION_ORCHESTRATOR.json").write_text(
        json.dumps(configure_60(), indent=2) + "\n", encoding="utf-8"
    )
    (DEV_WORKFLOW_DIR / "DEV_GRETEL_60_TRANSFORMATION_TEST.json").write_text(
        json.dumps(configure_dev_60(), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    configure_gretel_60_workflows()
    print("Configured workflow 60 and DEV_GRETEL_60_TRANSFORMATION_TEST.")
