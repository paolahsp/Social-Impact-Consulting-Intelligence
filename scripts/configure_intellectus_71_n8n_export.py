#!/usr/bin/env python3
"""Generate the inactive, importable Intellectus web adapter workflow.

The generated export never contains a live workflow ID, credential, endpoint,
or secret. Demo mode embeds only the repository's validated Paola handoff
fixture and keeps it explicitly separated from live requests.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "skeletons" / "71_INTELLECTUS_WEB_ADAPTER.json"
PAOLA_FIXTURE_PATH = ROOT / "fixtures" / "paola_track_output.json"
LIVE_REQUEST_PATH = ROOT / "fixtures" / "intellectus_71_live_request.json"
DEMO_REQUEST_PATH = ROOT / "fixtures" / "intellectus_71_demo_request.json"
SUCCESS_RESPONSE_PATH = ROOT / "fixtures" / "intellectus_71_success_response.json"
OPERATIONS_OUTPUT_PATH = ROOT / "runs" / "n8n_53_operations_cx_test_output.json"
PAOLA_LIVE_RUN_PATH = ROOT / "runs" / "paola_p0_givedirectly.json"


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=620, height=380, color=5):
    return {
        "parameters": {"content": content, "height": height, "width": width, "color": color},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
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
                    "id": f"{slug(name)}_condition",
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


def respond_node(name, status, x, y):
    return {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ $json.response }}",
            "options": {"responseCode": status},
        },
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.4,
        "position": [x, y],
    }


def connect(connections, source, target, output=0):
    groups = connections.setdefault(source, {"main": []})["main"]
    while len(groups) <= output:
        groups.append([])
    groups[output].append({"node": target, "type": "main", "index": 0})


JS_NORMALIZE_TEMPLATE = r"""
const webhookItem = items[0]?.json;
const raw = webhookItem && typeof webhookItem === 'object' && !Array.isArray(webhookItem)
  ? (webhookItem.body ?? webhookItem)
  : null;
const CONTRACT_VERSION = '1.0';
const MAX_BYTES = 256 * 1024;
const demoFixture = __DEMO_FIXTURE__;
const publicMessage = {
  invalid: 'We couldn\'t prepare the diagnostic. Try again or continue with the local demo.',
  evidence: 'Evidence is required before this analysis can run.'
};

function envelope(status, correlationId, runId, demo, extra = {}) {
  return { contract_version: CONTRACT_VERSION, status, correlation_id: correlationId, run_id: runId, demo, ...extra };
}
function own(value, key) { return Object.prototype.hasOwnProperty.call(value, key); }
function isObject(value) { return Boolean(value) && typeof value === 'object' && !Array.isArray(value); }
function nonEmpty(value) { return typeof value === 'string' && value.trim().length > 0; }
function unique(values) { return new Set(values).size === values.length; }
function httpUrl(value) {
  try { return ['http:', 'https:'].includes(new URL(value).protocol); } catch { return false; }
}
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (isObject(value)) return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}
function generatedId(prefix) {
  const executionId = typeof $execution !== 'undefined' && $execution?.id ? String($execution.id) : crypto.randomUUID();
  return `${prefix}-${executionId}`;
}
function sameOrganization(intake, handoff) {
  const organization = handoff?.run_context?.organization;
  if (!isObject(organization)) return false;
  const normalizeName = value => String(value || '').trim().toLowerCase().replace(/\s+/g, ' ');
  if (normalizeName(intake.organization_name) !== normalizeName(organization.name)) return false;
  try {
    return new URL(intake.website).hostname.toLowerCase() === new URL(organization.website).hostname.toLowerCase();
  } catch { return false; }
}
function validateIntake(intake) {
  if (!isObject(intake)) return false;
  if (!nonEmpty(intake.organization_name) || !nonEmpty(intake.current_challenge)) return false;
  if (!/^[A-Z]{2}$/.test(intake.country || '')) return false;
  if (!isObject(intake.research_window) || !/^\d{4}-\d{2}-\d{2}$/.test(intake.research_window.start_date || '') || !/^\d{4}-\d{2}-\d{2}$/.test(intake.research_window.end_date || '')) return false;
  if (!Array.isArray(intake.uploaded_document_refs) || !intake.uploaded_document_refs.every(nonEmpty)) return false;
  try { if (!['http:', 'https:'].includes(new URL(intake.website).protocol)) return false; } catch { return false; }
  return true;
}
function validateHandoff(handoff) {
  if (!isObject(handoff) || !isObject(handoff.run_context) || !nonEmpty(handoff.run_context.run_id)) return false;
  if (!isObject(handoff.run_context.organization) || !nonEmpty(handoff.run_context.organization.name) || !httpUrl(handoff.run_context.organization.website) || !nonEmpty(handoff.run_context.organization.country)) return false;
  if (!['created','researching','analyzing','qa','completed','failed'].includes(handoff.run_context.status) || !nonEmpty(handoff.run_context.started_at) || !Array.isArray(handoff.run_context.errors)) return false;
  if (!isObject(handoff.rag_metadata)) return false;
  for (const key of ['sources', 'evidence', 'findings', 'unknowns', 'contradictions']) if (!Array.isArray(handoff[key])) return false;
  const sourceIds = handoff.sources.map(source => source?.source_id);
  const evidenceIds = handoff.evidence.map(evidence => evidence?.evidence_id);
  const findingIds = handoff.findings.map(finding => finding?.finding_id);
  if (!unique(sourceIds) || !unique(evidenceIds) || !unique(findingIds)) return false;
  if (handoff.sources.some(source => !isObject(source) || !/^SRC-/.test(source.source_id || '') || !nonEmpty(source.title) || !httpUrl(source.url) || !nonEmpty(source.source_type) || !nonEmpty(source.retrieved_at) || typeof source.is_official !== 'boolean')) return false;
  const sourceSet = new Set(sourceIds);
  if (handoff.evidence.some(evidence => !isObject(evidence) || !/^EV-/.test(evidence.evidence_id || '') || !nonEmpty(evidence.run_id) || !nonEmpty(evidence.claim) || !Array.isArray(evidence.source_ids) || evidence.source_ids.some(id => !sourceSet.has(id)) || !nonEmpty(evidence.domain) || !['fact','inference','hypothesis','unknown'].includes(evidence.evidence_type) || !Number.isFinite(evidence.confidence) || evidence.confidence < 0 || evidence.confidence > 1 || !['supported','partially_supported','contradicted','insufficient_evidence','unknown'].includes(evidence.status) || !Array.isArray(evidence.contradiction_ids) || typeof evidence.requires_validation !== 'boolean')) return false;
  const evidenceSet = new Set(evidenceIds);
  if (handoff.evidence.some(evidence => evidence.contradiction_ids.some(id => !evidenceSet.has(id)))) return false;
  if (handoff.findings.some(finding => !isObject(finding) || !/^F-/.test(finding.finding_id || '') || !nonEmpty(finding.domain) || !nonEmpty(finding.finding) || !Array.isArray(finding.evidence_ids) || finding.evidence_ids.some(id => !evidenceSet.has(id)) || !['observed','inferred','hypothesis','unknown'].includes(finding.finding_type) || !Number.isFinite(finding.confidence) || finding.confidence < 0 || finding.confidence > 1 || typeof finding.requires_validation !== 'boolean' || !(finding.validation_question === null || nonEmpty(finding.validation_question)))) return false;
  return true;
}

let correlationId = generatedId('CORR');
let runId = generatedId('RUN');
let mode = 'live';
try {
  if (!isObject(raw)) throw new Error('invalid');
  const size = new TextEncoder().encode(JSON.stringify(raw)).length;
  if (size > MAX_BYTES) throw new Error('invalid');
  if (raw.contract_version !== CONTRACT_VERSION || !['live', 'demo'].includes(raw.mode)) throw new Error('invalid');
  if (!validateIntake(raw.intake)) throw new Error('invalid');
  mode = raw.mode;
  correlationId = nonEmpty(raw.correlation_id) ? raw.correlation_id : (nonEmpty(raw.run_id) ? raw.run_id : correlationId);
  let handoff;
  if (mode === 'demo') {
    if (own(raw, 'evidence_handoff') || raw.intake.uploaded_document_refs.length > 0) throw new Error('invalid');
    handoff = demoFixture;
  } else {
    handoff = raw.evidence_handoff;
  }
  if (mode === 'live' && handoff == null) {
    return [{ json: {
      request_valid: true,
      evidence_ready: false,
      correlation_id: correlationId,
      run_id: nonEmpty(raw.run_id) ? raw.run_id : runId,
      demo: false,
      response: envelope('needs_evidence', correlationId, nonEmpty(raw.run_id) ? raw.run_id : runId, false, {
        message: publicMessage.evidence,
        error: { code: 'evidence_required' }
      })
    } }];
  }
  if (!validateHandoff(handoff)) throw new Error('invalid');
  if (mode === 'live' && canonical(handoff) === canonical(demoFixture)) throw new Error('invalid');
  runId = handoff.run_context.run_id;
  if (nonEmpty(raw.run_id) && raw.run_id !== runId) throw new Error('invalid');
  if (!sameOrganization(raw.intake, handoff)) throw new Error('invalid');
  const operationsEvidence = handoff.evidence.filter(evidence => evidence.domain === 'operations_cx');
  const sufficient = operationsEvidence.length > 0 && operationsEvidence.every(evidence => evidence.source_ids.length > 0);
  if (!sufficient) {
    return [{ json: {
      request_valid: true,
      evidence_ready: false,
      correlation_id: correlationId,
      run_id: runId,
      demo: mode === 'demo',
      response: envelope('needs_evidence', correlationId, runId, mode === 'demo', {
        message: publicMessage.evidence,
        error: { code: 'evidence_required' }
      })
    } }];
  }
  return [{ json: {
    request_valid: true,
    evidence_ready: true,
    correlation_id: correlationId,
    run_id: runId,
    demo: mode === 'demo',
    intake: raw.intake,
    evidence_handoff: handoff
  } }];
} catch {
  return [{ json: {
    request_valid: false,
    evidence_ready: false,
    correlation_id: correlationId,
    run_id: runId,
    demo: mode === 'demo',
    response: envelope('error', correlationId, runId, mode === 'demo', {
      message: publicMessage.invalid,
      error: { code: 'invalid_request' }
    })
  } }];
}
"""


JS_ADAPT = r"""
const normalized = items[0]?.json;
if (!normalized?.request_valid || !normalized?.evidence_ready || !normalized.evidence_handoff) {
  throw new Error('Adapter gate did not provide a validated evidence handoff');
}
const handoff = normalized.evidence_handoff;
return [{ json: {
  run_context: handoff.run_context,
  sources: handoff.sources,
  evidence: handoff.evidence,
  findings: handoff.findings,
  unknowns: handoff.unknowns,
  contradictions: handoff.contradictions,
  rag_metadata: handoff.rag_metadata
} }];
"""


JS_VALIDATE_OUTPUT = r"""
const leaf = items[0]?.json;
const normalized = $('NORMALIZE_AND_VALIDATE_REQUEST').first().json;
const handoff = normalized.evidence_handoff;
const responseBase = {
  contract_version: '1.0', correlation_id: normalized.correlation_id,
  run_id: normalized.run_id, demo: normalized.demo
};
try {
  if (!leaf || typeof leaf !== 'object' || Array.isArray(leaf) || !Array.isArray(leaf.findings) || Object.keys(leaf).some(key => key !== 'findings')) throw new Error('invalid');
  const evidenceById = new Map(handoff.evidence.map(evidence => [evidence.evidence_id, evidence]));
  const ids = new Set();
  for (const finding of leaf.findings) {
    if (!finding || typeof finding !== 'object' || !/^F-OPS-/.test(finding.finding_id || '') || ids.has(finding.finding_id)) throw new Error('invalid');
    ids.add(finding.finding_id);
    if (finding.domain !== 'operations_cx' || !['observed','inferred','hypothesis','unknown'].includes(finding.finding_type)) throw new Error('invalid');
    if (typeof finding.finding !== 'string' || !finding.finding.trim() || !Array.isArray(finding.evidence_ids) || !finding.evidence_ids.length) throw new Error('invalid');
    if (!Number.isFinite(finding.confidence) || finding.confidence < 0 || finding.confidence > 1 || typeof finding.requires_validation !== 'boolean') throw new Error('invalid');
    for (const evidenceId of finding.evidence_ids) if (evidenceById.get(evidenceId)?.domain !== 'operations_cx') throw new Error('invalid');
    if (finding.finding_type === 'observed' && (finding.requires_validation || finding.validation_question !== null)) throw new Error('invalid');
    if (finding.finding_type !== 'observed' && (!finding.requires_validation || typeof finding.validation_question !== 'string' || !finding.validation_question.trim())) throw new Error('invalid');
  }
  return [{ json: { output_valid: true, response: {
    ...responseBase,
    status: 'completed',
    message: 'Diagnostic prepared for review.',
    completed_at: new Date().toISOString(),
    data: {
      intake: normalized.intake,
      sources: handoff.sources,
      evidence: handoff.evidence,
      findings: leaf.findings,
      unknowns: handoff.unknowns,
      contradictions: handoff.contradictions,
      rag_metadata: handoff.rag_metadata
    }
  } } }];
} catch {
  return [{ json: { output_valid: false, response: {
    ...responseBase,
    status: 'error',
    message: 'We couldn\'t prepare the diagnostic. Try again or continue with the local demo.',
    error: { code: 'invalid_upstream_response' }
  } } }];
}
"""


JS_MAP_SUBWORKFLOW_ERROR = r"""
const normalized = $('NORMALIZE_AND_VALIDATE_REQUEST').first().json;
return [{ json: { response: {
  contract_version: '1.0',
  status: 'error',
  correlation_id: normalized.correlation_id,
  run_id: normalized.run_id,
  demo: normalized.demo,
  message: 'We couldn\'t prepare the diagnostic. Try again or continue with the local demo.',
  error: { code: 'upstream_failure' }
} } }];
"""


def configure_workflow(demo_fixture):
    normalize_js = JS_NORMALIZE_TEMPLATE.replace(
        "__DEMO_FIXTURE__", json.dumps(demo_fixture, separators=(",", ":"), ensure_ascii=False)
    )
    nodes = [
        sticky(
            "00_README__INTELLECTUS_ADAPTER_BOUNDARY",
            "PURPOSE\nValidate the Intellectus transport envelope, require a Paola evidence handoff, adapt only compatible fields to 53, validate the leaf output, and return a stable HTTP response.\n\nSECURITY\nInactive by default. Configure authorization, CORS, proxy rate limits, payload limits, and retention before activation. No credential, endpoint, or live workflow ID is committed.\n\nDEMO\nUses only fixtures/paola_track_output.json, requires mode=demo, returns demo=true, and rejects uploaded document references or a supplied handoff.",
            -720, -500, 660, 500, 4,
        ),
        {
            "parameters": {
                "httpMethod": "POST",
                "path": "intellectus-diagnostic",
                "responseMode": "responseNode",
                "options": {},
            },
            "id": "webhook__post_intellectus_diagnostic",
            "name": "WEBHOOK__POST_INTELLECTUS_DIAGNOSTIC",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [0, 0],
            "webhookId": "",
            "notes": "AFTER IMPORT: configure the production/test webhook URL in Intellectus. Keep inactive until authorization, CORS, proxy limits, and 53 selection are complete.",
        },
        code_node("NORMALIZE_AND_VALIDATE_REQUEST", normalize_js, 280, 0),
        if_node("DECISION__REQUEST_VALID", "={{ $json.request_valid }}", 580, 0),
        respond_node("RESPOND__INVALID_REQUEST_400", 400, 880, 240),
        if_node("DECISION__EVIDENCE_READY", "={{ $json.evidence_ready }}", 880, -80),
        respond_node("RESPOND__NEEDS_EVIDENCE_422", 422, 1180, 120),
        code_node("ADAPT__PAOLA_HANDOFF_TO_53_INPUT", JS_ADAPT, 1180, -180),
        {
            "parameters": {
                "source": "database",
                "workflowId": {"__rl": True, "value": "", "mode": "list", "cachedResultName": ""},
                "mode": "once",
                "options": {"waitForSubWorkflow": True},
            },
            "id": "todo_link_subworkflow__53_operations_cx",
            "name": "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX",
            "type": "n8n-nodes-base.executeWorkflow",
            "typeVersion": 1.3,
            "position": [1480, -180],
            "notes": "BLOCKING AFTER IMPORT: select 53_OPERATIONS_CX_AGENT from the Workflow list. No live workflow ID is committed.",
            "onError": "continueErrorOutput",
        },
        code_node("VALIDATE_AND_NORMALIZE_53_OUTPUT", JS_VALIDATE_OUTPUT, 1780, -260),
        if_node("DECISION__OUTPUT_VALID", "={{ $json.output_valid }}", 2080, -260),
        respond_node("RESPOND__SUCCESS_200", 200, 2380, -360),
        respond_node("RESPOND__UPSTREAM_OUTPUT_ERROR_502", 502, 2380, -140),
        code_node("MAP__SUBWORKFLOW_ERROR", JS_MAP_SUBWORKFLOW_ERROR, 1780, 0),
        respond_node("RESPOND__SUBWORKFLOW_ERROR_502", 502, 2080, 0),
    ]
    connections = {}
    connect(connections, "WEBHOOK__POST_INTELLECTUS_DIAGNOSTIC", "NORMALIZE_AND_VALIDATE_REQUEST")
    connect(connections, "NORMALIZE_AND_VALIDATE_REQUEST", "DECISION__REQUEST_VALID")
    connect(connections, "DECISION__REQUEST_VALID", "DECISION__EVIDENCE_READY", 0)
    connect(connections, "DECISION__REQUEST_VALID", "RESPOND__INVALID_REQUEST_400", 1)
    connect(connections, "DECISION__EVIDENCE_READY", "ADAPT__PAOLA_HANDOFF_TO_53_INPUT", 0)
    connect(connections, "DECISION__EVIDENCE_READY", "RESPOND__NEEDS_EVIDENCE_422", 1)
    connect(connections, "ADAPT__PAOLA_HANDOFF_TO_53_INPUT", "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX")
    connect(connections, "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "VALIDATE_AND_NORMALIZE_53_OUTPUT", 0)
    connect(connections, "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "MAP__SUBWORKFLOW_ERROR", 1)
    connect(connections, "VALIDATE_AND_NORMALIZE_53_OUTPUT", "DECISION__OUTPUT_VALID")
    connect(connections, "DECISION__OUTPUT_VALID", "RESPOND__SUCCESS_200", 0)
    connect(connections, "DECISION__OUTPUT_VALID", "RESPOND__UPSTREAM_OUTPUT_ERROR_502", 1)
    connect(connections, "MAP__SUBWORKFLOW_ERROR", "RESPOND__SUBWORKFLOW_ERROR_502")
    return {
        "name": "71_INTELLECTUS_WEB_ADAPTER",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure(root=ROOT):
    global ROOT, WORKFLOW_PATH, PAOLA_FIXTURE_PATH, LIVE_REQUEST_PATH, DEMO_REQUEST_PATH
    global SUCCESS_RESPONSE_PATH, OPERATIONS_OUTPUT_PATH, PAOLA_LIVE_RUN_PATH
    ROOT = Path(root)
    WORKFLOW_PATH = ROOT / "workflows" / "skeletons" / "71_INTELLECTUS_WEB_ADAPTER.json"
    PAOLA_FIXTURE_PATH = ROOT / "fixtures" / "paola_track_output.json"
    LIVE_REQUEST_PATH = ROOT / "fixtures" / "intellectus_71_live_request.json"
    DEMO_REQUEST_PATH = ROOT / "fixtures" / "intellectus_71_demo_request.json"
    SUCCESS_RESPONSE_PATH = ROOT / "fixtures" / "intellectus_71_success_response.json"
    OPERATIONS_OUTPUT_PATH = ROOT / "runs" / "n8n_53_operations_cx_test_output.json"
    PAOLA_LIVE_RUN_PATH = ROOT / "runs" / "paola_p0_givedirectly.json"
    demo_fixture = json.loads(PAOLA_FIXTURE_PATH.read_text(encoding="utf-8"))
    operations_output = json.loads(OPERATIONS_OUTPUT_PATH.read_text(encoding="utf-8"))
    paola_live_handoff = json.loads(PAOLA_LIVE_RUN_PATH.read_text(encoding="utf-8"))["paola_track_output"]
    demo_intake = {
        "organization_name": "Fictional River Learning Collective",
        "website": "https://fictional-river-learning.example.org",
        "country": "DE",
        "current_challenge": "Preparing for a pre-engagement diagnostic workshop",
        "research_window": {"start_date": "2026-05-12", "end_date": "2026-08-09"},
        "uploaded_document_refs": [],
    }
    live_intake = {
        "organization_name": "GiveDirectly",
        "website": "https://www.givedirectly.org",
        "country": "US",
        "current_challenge": "Preparing for a pre-engagement diagnostic workshop",
        "research_window": {"start_date": "2026-05-12", "end_date": "2026-08-09"},
        "uploaded_document_refs": [],
    }
    live_request = {
        "contract_version": "1.0",
        "mode": "live",
        "correlation_id": "CORR-PAOLA-P0-001",
        "run_id": paola_live_handoff["run_context"]["run_id"],
        "intake": live_intake,
        "evidence_handoff": paola_live_handoff,
    }
    demo_request = {
        "contract_version": "1.0",
        "mode": "demo",
        "correlation_id": "CORR-DEMO-001",
        "intake": demo_intake,
    }
    success_response = {
        "contract_version": "1.0",
        "status": "completed",
        "correlation_id": demo_request["correlation_id"],
        "run_id": demo_fixture["run_context"]["run_id"],
        "demo": True,
        "message": "Diagnostic prepared for review.",
        "completed_at": "2026-08-14T12:00:00.000Z",
        "data": {
            "intake": demo_intake,
            "sources": demo_fixture["sources"],
            "evidence": demo_fixture["evidence"],
            "findings": operations_output["findings"],
            "unknowns": demo_fixture["unknowns"],
            "contradictions": demo_fixture["contradictions"],
            "rag_metadata": demo_fixture["rag_metadata"],
        },
    }
    WORKFLOW_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW_PATH.write_text(json.dumps(configure_workflow(demo_fixture), indent=2) + "\n", encoding="utf-8")
    LIVE_REQUEST_PATH.write_text(json.dumps(live_request, indent=2) + "\n", encoding="utf-8")
    DEMO_REQUEST_PATH.write_text(json.dumps(demo_request, indent=2) + "\n", encoding="utf-8")
    SUCCESS_RESPONSE_PATH.write_text(json.dumps(success_response, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    configure()
    print("Configured inactive 71_INTELLECTUS_WEB_ADAPTER with an empty 53 selector.")
