#!/usr/bin/env python3
"""Generate workflow 53 and its development-only n8n composition test."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
DEV_WORKFLOW_DIR = ROOT / "workflows" / "dev"


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=560, height=320, color=5):
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


def code_node(name, js, x, y):
    return {
        "parameters": {"jsCode": js.strip() + "\n"},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, y],
    }


def execute_workflow_node(name, target, x, y):
    return {
        "parameters": {"workflowId": "", "options": {}},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1,
        "position": [x, y],
        "notes": f"AFTER IMPORT: select {target}. No live workflow ID is committed.",
    }


def connections(edges):
    result = {}
    for source, target in edges:
        result.setdefault(source, {"main": [[]]})["main"][0].append(
            {"node": target, "type": "main", "index": 0}
        )
    return result


JS_INPUT = r"""
const payload = items[0]?.json;
if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
  throw new Error('53 input requires one canonical n8n item: { json: payload }');
}
for (const key of ['sources', 'evidence', 'findings', 'unknowns', 'contradictions']) {
  if (!Array.isArray(payload[key])) throw new Error(`53 input requires ${key}[]`);
}
if (!payload.run_context || typeof payload.run_context !== 'object' || !payload.run_context.run_id) {
  throw new Error('53 input requires run_context.run_id');
}
if (!payload.rag_metadata || typeof payload.rag_metadata !== 'object' || Array.isArray(payload.rag_metadata)) {
  throw new Error('53 input requires rag_metadata object');
}
const evidenceIds = payload.evidence.map(ev => ev?.evidence_id);
if (evidenceIds.some(id => typeof id !== 'string' || !/^EV-/.test(id))) {
  throw new Error('53 input evidence records require valid evidence_id values');
}
if (new Set(evidenceIds).size !== evidenceIds.length) throw new Error('53 input contains duplicate evidence IDs');
const findingIds = payload.findings.map(finding => finding?.finding_id);
if (findingIds.some(id => typeof id !== 'string' || !/^F-/.test(id))) {
  throw new Error('53 input findings require valid finding_id values');
}
if (new Set(findingIds).size !== findingIds.length) throw new Error('53 input contains duplicate finding IDs');
return [{ json: { context: payload } }];
"""


JS_DOMAIN_FILTER = r"""
const context = items[0].json.context;
const evidenceById = new Map(context.evidence.map(ev => [ev.evidence_id, ev]));
for (const ev of context.evidence) {
  for (const linkedId of ev.contradiction_ids || []) {
    if (!evidenceById.has(linkedId)) throw new Error(`Evidence ${ev.evidence_id} references missing contradiction evidence ${linkedId}`);
  }
}
const operationsEvidence = context.evidence.filter(ev => ev.domain === 'operations_cx');
const operationsEvidenceIds = new Set(operationsEvidence.map(ev => ev.evidence_id));
const operationsUnknowns = context.unknowns.filter(unknown =>
  unknown?.domain === 'operations_cx' ||
  (unknown?.evidence_ids || []).some(id => operationsEvidenceIds.has(id))
);
const operationsContradictions = context.contradictions.filter(contradiction => {
  const ids = [...(contradiction?.evidence_ids || []), ...(contradiction?.contradiction_ids || [])];
  return ids.some(id => operationsEvidenceIds.has(id));
});
for (const ev of operationsEvidence) {
  if (ev.status === 'contradicted' || (ev.contradiction_ids || []).length) {
    operationsContradictions.push({
      evidence_ids: [ev.evidence_id, ...(ev.contradiction_ids || [])],
      description: `Contradiction state attached to ${ev.evidence_id}`
    });
  }
}
return [{ json: {
  context,
  operations_evidence: operationsEvidence,
  operations_unknowns: operationsUnknowns,
  operations_contradictions: operationsContradictions
} }];
"""


JS_JOURNEY_SIGNALS = r"""
function journey(claim) {
  if (/\bvolunteer|volunteering\b/i.test(claim)) return 'volunteer';
  if (/\bdonor|donation|donate|giving|contribute\b/i.test(claim)) return 'donor';
  return 'stakeholder';
}
function stage(claim, journeyName) {
  if (/follow[- ]?up|first response|re-?engag/i.test(claim)) return 'follow_up';
  if (/acknowledg|confirm|receipt/i.test(claim)) return 'acknowledgement';
  if (/qualif|screen|interview|review/i.test(claim)) return 'qualification';
  if (/onboard|orientation/i.test(claim)) return 'onboarding';
  if (/feedback|survey/i.test(claim)) return 'feedback';
  if (/application|apply|form|submit/i.test(claim) && journeyName === 'volunteer') return 'application';
  if (/donat|donate|giving|contribute|payment/i.test(claim) && journeyName === 'donor') return 'donation';
  if (/impact (update|report)|newsletter/i.test(claim)) return 'impact_communication';
  if (/email|phone|contact|message|chat/i.test(claim)) return 'contact';
  if (/participat|program|role/i.test(claim)) return 'participation';
  return 'visible_signal';
}
function classification(ev) {
  const contradicted = ev.status === 'contradicted' || (ev.contradiction_ids || []).length > 0;
  if (contradicted || ev.evidence_type === 'unknown' || ev.status === 'unknown' || ev.status === 'insufficient_evidence') return 'unknown';
  if (ev.evidence_type === 'hypothesis') return 'hypothesis';
  if (ev.evidence_type === 'inference' || ev.status === 'partially_supported') return 'inferred';
  if (ev.evidence_type === 'fact' && ev.status === 'supported' && ev.requires_validation === false) return 'observed';
  return 'unknown';
}
const signals = items[0].json.operations_evidence.map(ev => {
  const journeyName = journey(ev.claim || '');
  const signalClass = classification(ev);
  return {
    evidence_id: ev.evidence_id,
    claim: ev.claim || '',
    journey: journeyName,
    stage: stage(ev.claim || '', journeyName),
    classification: signalClass,
    confidence: Number(ev.confidence || 0),
    requires_validation: signalClass !== 'observed' || ev.requires_validation === true
  };
});
return [{ json: { ...items[0].json, journey_signals: signals } }];
"""


JS_CLASSIFY_SIGNALS = r"""
const buckets = { observed: [], inferred: [], hypothesis: [], unknown: [] };
for (const signal of items[0].json.journey_signals) buckets[signal.classification].push(signal);
const journeyMap = items[0].json.journey_signals.map(signal => ({
  journey: signal.journey,
  stage: signal.stage,
  status: signal.classification,
  evidence_ids: [signal.evidence_id]
}));
return [{ json: { ...items[0].json, classified_signals: buckets, journey_map: journeyMap } }];
"""


JS_BUILD_OBSERVED = r"""
function statement(signal) {
  if (signal.journey === 'volunteer' && signal.stage === 'application') {
    return 'The organization provides a publicly visible digital entry point for prospective volunteers.';
  }
  if (signal.journey === 'donor' && signal.stage === 'donation') {
    return 'The organization provides a publicly visible donation entry point.';
  }
  if (signal.stage === 'contact') return 'The organization publishes a stakeholder contact route.';
  return `A publicly visible ${signal.journey} journey signal is present at the ${signal.stage} stage.`;
}
const grouped = new Map();
for (const signal of items[0].json.classified_signals.observed) {
  const key = `${signal.journey}:${signal.stage}`;
  if (!grouped.has(key)) grouped.set(key, []);
  grouped.get(key).push(signal);
}
const candidates = [];
for (const group of grouped.values()) {
  const first = group[0];
  candidates.push({
    domain: 'operations_cx',
    finding: statement(first),
    evidence_ids: [...new Set(group.map(signal => signal.evidence_id))],
    finding_type: 'observed',
    confidence: Math.min(0.9, ...group.map(signal => signal.confidence)),
    requires_validation: false,
    validation_question: null,
    journey: first.journey,
    journey_stage: first.stage,
    journey_stage_status: 'observed'
  });
}
return [{ json: { ...items[0].json, candidate_findings: candidates } }];
"""


JS_BUILD_UNCERTAIN = r"""
function question(journey, stage) {
  if (journey === 'volunteer' && ['application', 'acknowledgement', 'follow_up'].includes(stage)) {
    return 'What happens internally after a volunteer application is submitted, including assignment, acknowledgement, and follow-up?';
  }
  if (journey === 'donor') return 'What happens after a donation is received, including confirmation, follow-up, and re-engagement?';
  return `How does the ${journey} journey work internally at and after the ${stage} stage?`;
}
const candidates = [...items[0].json.candidate_findings];
const usedUnknownEvidence = new Set();
for (const signal of [...items[0].json.classified_signals.inferred, ...items[0].json.classified_signals.unknown]) {
  const type = signal.classification === 'inferred' ? 'inferred' : 'unknown';
  const text = type === 'inferred'
    ? `Public signals suggest a ${signal.journey} journey pattern at the ${signal.stage} stage, but the pattern requires validation.`
    : `Public evidence does not establish the internal ${signal.journey} process at the ${signal.stage} stage.`;
  candidates.push({
    domain: 'operations_cx', finding: text, evidence_ids: [signal.evidence_id], finding_type: type,
    confidence: Math.min(type === 'inferred' ? 0.6 : 0.55, signal.confidence || 0.4),
    requires_validation: true, validation_question: question(signal.journey, signal.stage),
    journey: signal.journey, journey_stage: signal.stage, journey_stage_status: type
  });
  if (type === 'unknown') usedUnknownEvidence.add(signal.evidence_id);
}
const actualEvidenceIds = new Set(items[0].json.operations_evidence.map(ev => ev.evidence_id));
for (const unknown of items[0].json.operations_unknowns) {
  const ids = [...new Set((unknown.evidence_ids || []).filter(id => actualEvidenceIds.has(id)))];
  if (!ids.length || ids.every(id => usedUnknownEvidence.has(id))) continue;
  candidates.push({
    domain: 'operations_cx',
    finding: `Public evidence leaves an Operations/CX process unknown: ${unknown.description}`,
    evidence_ids: ids, finding_type: 'unknown', confidence: 0.45, requires_validation: true,
    validation_question: 'What is the current internal process for this publicly unobservable part of the stakeholder journey?',
    journey: 'stakeholder', journey_stage: 'unknown_internal_process', journey_stage_status: 'unknown'
  });
}
for (const contradiction of items[0].json.operations_contradictions) {
  const ids = [...new Set([...(contradiction.evidence_ids || []), ...(contradiction.contradiction_ids || [])].filter(id => actualEvidenceIds.has(id)))];
  if (!ids.length) continue;
  candidates.push({
    domain: 'operations_cx', finding: 'Public Operations/CX evidence is contradictory, so the current process state cannot be determined.',
    evidence_ids: ids, finding_type: 'unknown', confidence: 0.35, requires_validation: true,
    validation_question: 'Which description of the current stakeholder process is accurate, and what explains the conflicting public signals?',
    journey: 'stakeholder', journey_stage: 'contradiction', journey_stage_status: 'unknown'
  });
}
return [{ json: { ...items[0].json, candidate_findings: candidates } }];
"""


JS_BUILD_HYPOTHESES = r"""
const candidates = [...items[0].json.candidate_findings];
const observed = items[0].json.classified_signals.observed;
const unknown = items[0].json.classified_signals.unknown;
const volunteerEntry = observed.find(signal => signal.journey === 'volunteer' && signal.stage === 'application');
const volunteerGap = unknown.find(signal => signal.journey === 'volunteer' && ['acknowledgement', 'qualification', 'onboarding', 'follow_up'].includes(signal.stage));
if (volunteerEntry && volunteerGap) {
  candidates.push({
    domain: 'operations_cx',
    finding: 'The handoffs between public volunteer application submission and first follow-up may involve internal coordination steps that are not visible in public evidence.',
    evidence_ids: [...new Set([volunteerEntry.evidence_id, volunteerGap.evidence_id])],
    finding_type: 'hypothesis', confidence: 0.42, requires_validation: true,
    validation_question: 'How are volunteer applications assigned, acknowledged, qualified, and followed up after submission?',
    journey: 'volunteer', journey_stage: 'application_to_follow_up', journey_stage_status: 'hypothesis'
  });
}
const donorEntry = observed.find(signal => signal.journey === 'donor' && signal.stage === 'donation');
const donorGap = unknown.find(signal => signal.journey === 'donor');
if (donorEntry && donorGap) {
  candidates.push({
    domain: 'operations_cx',
    finding: 'The handoffs after the public donation step may include internal coordination that is not visible in public evidence.',
    evidence_ids: [...new Set([donorEntry.evidence_id, donorGap.evidence_id])],
    finding_type: 'hypothesis', confidence: 0.4, requires_validation: true,
    validation_question: 'How are donations confirmed, assigned for follow-up, and connected to later donor communication?',
    journey: 'donor', journey_stage: 'donation_to_reengagement', journey_stage_status: 'hypothesis'
  });
}
return [{ json: { ...items[0].json, candidate_findings: candidates } }];
"""


JS_ASSIGN_IDS = r"""
const usedIds = new Set(items[0].json.context.findings.map(finding => finding.finding_id));
let counter = 0;
function nextId() {
  let id;
  do id = `F-OPS-${String(++counter).padStart(3, '0')}`; while (usedIds.has(id));
  usedIds.add(id);
  return id;
}
const seen = new Set();
const findings = [];
for (const candidate of items[0].json.candidate_findings) {
  const evidenceIds = [...new Set(candidate.evidence_ids)].sort();
  const key = `${candidate.finding_type}|${candidate.finding}|${evidenceIds.join(',')}`;
  if (seen.has(key)) continue;
  seen.add(key);
  findings.push({ finding_id: nextId(), ...candidate, evidence_ids: evidenceIds });
}
return [{ json: { ...items[0].json, findings } }];
"""


JS_VALIDATE = r"""
const payload = items[0].json;
const evidenceById = new Map(payload.context.evidence.map(ev => [ev.evidence_id, ev]));
const upstreamIds = new Set(payload.context.findings.map(finding => finding.finding_id));
const generatedIds = new Set();
const required = ['finding_id', 'domain', 'finding', 'evidence_ids', 'finding_type', 'confidence', 'requires_validation', 'validation_question'];
const allowedTypes = new Set(['observed', 'inferred', 'hypothesis', 'unknown']);
const technologyFirst = /\brecommend|\bimplement|\binstall|\badopt|\bpurchase|\bsalesforce|\bneeds? (?:a )?crm|\breplace (?:the )?system/i;
for (const finding of payload.findings) {
  if (!required.every(key => Object.prototype.hasOwnProperty.call(finding, key))) throw new Error('53 finding missing required contract field');
  if (!/^F-OPS-/.test(finding.finding_id) || upstreamIds.has(finding.finding_id) || generatedIds.has(finding.finding_id)) throw new Error(`53 finding ID collision: ${finding.finding_id}`);
  generatedIds.add(finding.finding_id);
  if (finding.domain !== 'operations_cx' || !allowedTypes.has(finding.finding_type)) throw new Error('53 finding domain or type invalid');
  if (typeof finding.finding !== 'string' || !finding.finding.trim()) throw new Error('53 finding text is required');
  if (!Number.isFinite(finding.confidence) || finding.confidence < 0 || finding.confidence > 1) throw new Error('53 finding confidence must be 0-1');
  if (typeof finding.requires_validation !== 'boolean') throw new Error('53 finding requires_validation must be boolean');
  if (!Array.isArray(finding.evidence_ids) || !finding.evidence_ids.length) throw new Error('53 findings require evidence traceability');
  for (const evidenceId of finding.evidence_ids) {
    const evidence = evidenceById.get(evidenceId);
    if (!evidence) throw new Error(`53 finding references missing evidence ${evidenceId}`);
    if (evidence.domain !== 'operations_cx') throw new Error(`53 finding references cross-domain evidence ${evidenceId}`);
  }
  if (finding.finding_type === 'observed') {
    if (finding.requires_validation || finding.validation_question !== null) throw new Error('Observed findings must remain directly observable');
    for (const evidenceId of finding.evidence_ids) {
      const evidence = evidenceById.get(evidenceId);
      if (evidence.evidence_type !== 'fact' || evidence.status !== 'supported' || evidence.requires_validation !== false || (evidence.contradiction_ids || []).length) {
        throw new Error('Observed finding is not supported by uncontradicted fact evidence');
      }
    }
  } else if (!finding.requires_validation || typeof finding.validation_question !== 'string' || !finding.validation_question.trim()) {
    throw new Error(`${finding.finding_type} findings must require a validation question`);
  }
  if (finding.finding_type === 'hypothesis' && !/\bmay\b|\bmight\b|\bcould\b/i.test(finding.finding)) throw new Error('Hypothesis wording must remain conditional');
  if (technologyFirst.test(finding.finding)) throw new Error('53 must not produce technology-first recommendations');
}
return [{ json: payload }];
"""


JS_OUTPUT = r"""
return [{ json: { findings: items[0].json.findings } }];
"""


def configure_53():
    nodes = [
        sticky(
            "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
            "PURPOSE\nConvert public Operations/CX evidence into traceable observed, inferred, hypothesis, and unknown findings.\n\nOWNER\nGRETEL TRACK B\n\nINPUT\nFlat Paola track handoff.\n\nOUTPUT\n{ findings: finding.schema.json[] }\n\nSTATUS\nPhase 2C repository-ready. Inactive. No credentials or workflow IDs.",
            -580, -420, 600, 390, 4,
        ),
        sticky(
            "NOTE__VISIBLE_OPERATIONS_PATH",
            "Evidence Input -> strict Operations/CX Domain Filter -> Journey Signal Extraction -> Observed / Inferred / Hypothesis / Unknown Classification -> modular Finding Construction -> ID + evidence validation -> Leaf Output.\n\nOBSERVABLE SIGNAL != INTERNAL PROCESS FACT\nJourney before technology. No recommendations.",
            -580, 20, 600, 360, 5,
        ),
        trigger(),
        code_node("EVIDENCE_INPUT__PAOLA_TRACK_HANDOFF", JS_INPUT, 260, 0),
        code_node("DOMAIN_FILTER__OPERATIONS_CX_ONLY", JS_DOMAIN_FILTER, 560, 0),
        code_node("JOURNEY_SIGNAL_EXTRACTION", JS_JOURNEY_SIGNALS, 860, 0),
        code_node("CLASSIFY__OBSERVED_INFERRED_HYPOTHESIS_UNKNOWN", JS_CLASSIFY_SIGNALS, 1160, 0),
        code_node("BUILD__OBSERVED_FINDINGS", JS_BUILD_OBSERVED, 1460, 0),
        code_node("BUILD__INFERRED_AND_UNKNOWN_FINDINGS", JS_BUILD_UNCERTAIN, 1760, 0),
        code_node("BUILD__VALIDATION_HYPOTHESES", JS_BUILD_HYPOTHESES, 2060, 0),
        code_node("ASSIGN__COLLISION_FREE_FINDING_IDS", JS_ASSIGN_IDS, 2360, 0),
        code_node("VALIDATE__FINDING_CONTRACT_AND_TRACEABILITY", JS_VALIDATE, 2660, 0),
        code_node("OUTPUT_CONTRACT__OPERATIONS_CX_FINDINGS", JS_OUTPUT, 2960, 0),
    ]
    path = [node["name"] for node in nodes if node["type"] != "n8n-nodes-base.stickyNote"]
    return {
        "name": "53_OPERATIONS_CX_AGENT",
        "nodes": nodes,
        "connections": connections(list(zip(path, path[1:]))),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def fixture_code(fixture):
    serialized = json.dumps(fixture, separators=(",", ":"), ensure_ascii=False)
    return f"// DEV fixture embedded from fixtures/paola_track_output.json.\nconst fixture = {serialized};\nreturn [{{ json: fixture }}];"


JS_COMPOSE_DEV = r"""
const leaf = items[0]?.json ?? {};
const original = $('DEV_INPUT__PAOLA_TRACK_FIXTURE').first().json;
if (!Array.isArray(leaf.findings)) throw new Error('DEV expected 53 leaf findings[]');
const allIds = [...original.findings.map(f => f.finding_id), ...leaf.findings.map(f => f.finding_id)];
if (new Set(allIds).size !== allIds.length) throw new Error('DEV composition found a finding ID collision');
const evidenceIds = new Set(original.evidence.map(ev => ev.evidence_id));
if (!leaf.findings.every(f => f.evidence_ids.every(id => evidenceIds.has(id)))) throw new Error('DEV composition found dangling evidence reference');
const composed = { ...original, findings: [...original.findings, ...leaf.findings] };
return [{ json: {
  leaf_output: leaf,
  composed_payload: composed,
  composition_check: {
    upstream_context_preserved: ['run_context','sources','evidence','unknowns','contradictions','rag_metadata'].every(key => composed[key] === original[key]),
    upstream_finding_count: original.findings.length,
    operations_finding_count: leaf.findings.length,
    composed_finding_count: composed.findings.length,
    finding_ids_unique: true,
    evidence_references_valid: true
  }
} }];
"""


JS_ASSERT_DEV = r"""
const result = items[0].json;
const findings = result.leaf_output.findings;
for (const type of ['observed', 'unknown', 'hypothesis']) {
  if (!findings.some(finding => finding.finding_type === type)) throw new Error(`DEV fixture requires one ${type} finding`);
}
if (!result.composition_check.upstream_context_preserved) throw new Error('DEV composition lost Paola context');
return items;
"""


def configure_dev_53():
    fixture = json.loads((ROOT / "fixtures" / "paola_track_output.json").read_text(encoding="utf-8"))
    nodes = [
        sticky(
            "00_README__DEV_WORKFLOW",
            "DEV_GRETEL_53_OPERATIONS_CX_TEST\nImport after 53, link its Execute Sub-workflow node, then run manually.\nThe test proves leaf output and later composition with the unchanged Paola envelope.\nNo workflow IDs, credentials, or production data are committed.",
            -520, -360, 580, 350, 4,
        ),
        manual_trigger(),
        code_node("DEV_INPUT__PAOLA_TRACK_FIXTURE", fixture_code(fixture), 260, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "53_OPERATIONS_CX_AGENT", 560, 0),
        code_node("COMPOSE__53_FINDINGS_WITH_ORIGINAL_ENVELOPE", JS_COMPOSE_DEV, 860, 0),
        code_node("FINAL__ASSERT_53_AND_COMPOSITION", JS_ASSERT_DEV, 1160, 0),
    ]
    path = [node["name"] for node in nodes if node["type"] != "n8n-nodes-base.stickyNote"]
    return {
        "name": "DEV_GRETEL_53_OPERATIONS_CX_TEST",
        "nodes": nodes,
        "connections": connections(list(zip(path, path[1:]))),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure_gretel_53_workflows(root=ROOT):
    global ROOT, WORKFLOW_DIR, DEV_WORKFLOW_DIR
    ROOT = Path(root)
    WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
    DEV_WORKFLOW_DIR = ROOT / "workflows" / "dev"
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    DEV_WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    (WORKFLOW_DIR / "53_OPERATIONS_CX_AGENT.json").write_text(
        json.dumps(configure_53(), indent=2) + "\n", encoding="utf-8"
    )
    (DEV_WORKFLOW_DIR / "DEV_GRETEL_53_OPERATIONS_CX_TEST.json").write_text(
        json.dumps(configure_dev_53(), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    configure_gretel_53_workflows()
    print("Configured workflow 53 and DEV_GRETEL_53_OPERATIONS_CX_TEST.")
