import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
DEV_WORKFLOW_DIR = ROOT / "workflows" / "dev"


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=520, height=280, color=5):
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


def if_node(name, left_value, right_value, x, y, value_type="boolean"):
    operation = "true" if value_type == "boolean" and right_value is True else "equals"
    condition = {
        "id": slug(name + "_condition"),
        "leftValue": left_value,
        "rightValue": right_value,
        "operator": {"type": value_type, "operation": operation, "singleValue": operation == "true"},
    }
    if operation == "true":
        condition.pop("rightValue")
    return {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2,
                },
                "conditions": [condition],
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


def execute_workflow_node(name, target_workflow_name, x, y):
    return {
        "parameters": {"workflowId": "", "options": {}},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1,
        "position": [x, y],
        "notes": f"AFTER IMPORT: select {target_workflow_name}. Repository JSON intentionally contains no fabricated workflow ID.",
    }


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


def workflow(name, purpose, input_contract, output_contract, nodes, edges, canvas_note):
    return {
        "name": name,
        "nodes": [
            sticky(
                "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
                f"PURPOSE\n{purpose}\n\nOWNER\nGRETEL TRACK B\n\nINPUT CONTRACT\n{input_contract}\n\nOUTPUT CONTRACT\n{output_contract}\n\nSTATUS\nPhase 2B repository-ready. Inactive by default. No credentials. Deterministic fixture path; no Python execution.",
                -520,
                -380,
                560,
                390,
                4,
            ),
            sticky("NOTE__VISIBLE_TRANSFORMATION_PATH", canvas_note, -520, 40, 560, 320, 5),
            *nodes,
        ],
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


JS_61_INPUT = r"""
const payload = items[0]?.json ?? {};
for (const key of ['evidence', 'findings', 'unknowns']) {
  if (!Array.isArray(payload[key])) throw new Error(`61 input requires ${key}[]`);
}
const runId = payload.run_context?.run_id;
if (!runId) throw new Error('61 input requires run_context.run_id');
if (payload.findings.length === 0) {
  return [{ json: { context: payload, skip: true, can_observe_internal_reality: true } }];
}
return payload.findings.map((finding, index) => {
  const findingEvidence = payload.evidence.filter(ev => (finding.evidence_ids || []).includes(ev.evidence_id));
  const relatedUnknowns = payload.unknowns.filter(unknown =>
    unknown.domain === finding.domain ||
    (unknown.evidence_ids || []).some(id => (finding.evidence_ids || []).includes(id))
  );
  const allDirectFacts = findingEvidence.length > 0 && findingEvidence.every(ev =>
    ev.evidence_type === 'fact' && ev.status === 'supported' && ev.requires_validation === false
  );
  const canObserve = finding.finding_type === 'observed' && finding.requires_validation === false &&
    relatedUnknowns.length === 0 && allDirectFacts;
  return { json: {
    context: payload,
    index,
    finding,
    finding_evidence: findingEvidence,
    related_unknowns: relatedUnknowns,
    can_observe_internal_reality: canObserve
  } };
});
"""

JS_61_OBSERVED = r"""
return items.map(item => ({ json: { ...item.json, interpretation: 'observed', hypothesis_record: null } }));
"""

JS_61_HYPOTHESIS = r"""
const templates = {
  operations_cx: 'The internal stakeholder journey may include handoffs or coordination steps that are not visible in public information.',
  revenue_resilience: 'Revenue resilience may depend on funding concentration or dependencies that are not visible in public information.',
  impact_evidence: 'Impact measurement may rely on internal methods or reporting steps that are not visible in public information.'
};
return items.map(item => {
  if (item.json.skip) return { json: { ...item.json, hypothesis_record: null } };
  const { context, finding, related_unknowns: unknowns, index } = item.json;
  const unknownEvidenceIds = unknowns.flatMap(unknown => unknown.evidence_ids || []);
  const evidenceIds = [...new Set([...(finding.evidence_ids || []), ...unknownEvidenceIds])];
  const gap = unknowns[0]?.description || finding.validation_question ||
    `Public information does not validate the internal reality behind finding ${finding.finding_id}.`;
  const confidence = Math.max(0.2, Math.min(0.65, Number((Number(finding.confidence || 0) * 0.6).toFixed(2))));
  return { json: { ...item.json, interpretation: 'hypothesis', hypothesis_record: {
    hypothesis_id: `HYP-${String(index + 1).padStart(3, '0')}`,
    run_id: context.run_context.run_id,
    domain: finding.domain,
    evidence_ids: evidenceIds,
    finding_ids: [finding.finding_id],
    hypothesis: templates[finding.domain] || 'Internal organizational reality may differ from what is visible in public information.',
    confidence,
    requires_validation: true,
    validation_gap: gap
  } } };
});
"""

JS_61_CONFIDENCE = r"""
return items.map(item => {
  const hypothesis = item.json.hypothesis_record;
  if (!hypothesis) return item;
  if (hypothesis.requires_validation !== true) throw new Error('Hypothesis must require validation');
  if (!hypothesis.validation_gap) throw new Error('Hypothesis requires a validation_gap');
  if (!hypothesis.evidence_ids.length || !hypothesis.finding_ids.length) throw new Error('Hypothesis traceability is required');
  return item;
});
"""

JS_61_STRUCTURE = r"""
const context = items[0]?.json?.context ?? {};
const hypotheses = items.map(item => item.json.hypothesis_record).filter(Boolean)
  .sort((a, b) => a.hypothesis_id.localeCompare(b.hypothesis_id));
return [{ json: { ...context, hypotheses } }];
"""

JS_61_OUTPUT = r"""
const payload = items[0].json;
for (const hypothesis of payload.hypotheses || []) {
  if (!/^HYP-/.test(hypothesis.hypothesis_id) || hypothesis.requires_validation !== true) {
    throw new Error('61 output violates hypothesis contract');
  }
}
return [{ json: payload }];
"""


JS_62_INPUT = r"""
const payload = items[0]?.json ?? {};
if (!Array.isArray(payload.findings) || !Array.isArray(payload.evidence) || !Array.isArray(payload.hypotheses)) {
  throw new Error('62 input requires findings[], evidence[], and hypotheses[]');
}
if (payload.hypotheses.length === 0) return [{ json: { context: payload, skip: true, direct_validation_present: false } }];
return payload.hypotheses.map((hypothesis, index) => ({ json: {
  context: payload,
  index,
  hypothesis,
  findings: payload.findings.filter(finding => (hypothesis.finding_ids || []).includes(finding.finding_id)),
  evidence: payload.evidence.filter(ev => (hypothesis.evidence_ids || []).includes(ev.evidence_id)),
  direct_validation_present: Boolean(payload.client_validation?.validated_hypothesis_ids?.includes(hypothesis.hypothesis_id))
} }));
"""

JS_62_STRENGTH = r"""
return items.map(item => {
  if (item.json.skip) return { json: { ...item.json, evidence_strength: 'none' } };
  const scores = item.json.evidence.map(ev => Number(ev.confidence || 0));
  const average = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
  const supportedFacts = item.json.evidence.filter(ev => ev.evidence_type === 'fact' && ev.status === 'supported').length;
  const strength = supportedFacts > 0 && average >= 0.75 ? 'strong' : average >= 0.5 ? 'moderate' : 'weak';
  return { json: { ...item.json, evidence_strength: strength } };
});
"""

JS_62_VALIDATED = r"""
return items.map(item => {
  const hypothesis = item.json.hypothesis;
  return { json: { ...item.json, diagnosis_record: {
    diagnosis_id: `DX-${String(item.json.index + 1).padStart(3, '0')}`,
    domain: hypothesis.domain,
    diagnosis_type: 'validated_cause',
    statement: `Client validation confirms: ${hypothesis.hypothesis}`,
    finding_ids: hypothesis.finding_ids,
    hypothesis_ids: [hypothesis.hypothesis_id],
    evidence_ids: hypothesis.evidence_ids,
    confidence: Math.max(0.8, hypothesis.confidence),
    requires_validation: false
  } } };
});
"""

JS_62_PUBLIC = r"""
return items.map(item => {
  if (item.json.skip) return { json: { ...item.json, diagnosis_record: null } };
  const hypothesis = item.json.hypothesis;
  const confidence = Number(hypothesis.confidence || 0);
  const findingObserved = item.json.findings.some(f => f.finding_type === 'observed' && f.requires_validation === false);
  let type = confidence >= 0.4 ? 'likely_cause' : 'unknown';
  if (findingObserved && item.json.evidence_strength === 'strong' && hypothesis.requires_validation === false) type = 'observed_problem';
  const statement = type === 'unknown'
    ? `The cause cannot be determined from public evidence. ${hypothesis.hypothesis}`
    : `A likely contributing factor is: ${hypothesis.hypothesis}`;
  return { json: { ...item.json, diagnosis_record: {
    diagnosis_id: `DX-${String(item.json.index + 1).padStart(3, '0')}`,
    domain: hypothesis.domain,
    diagnosis_type: type,
    statement,
    finding_ids: hypothesis.finding_ids,
    hypothesis_ids: [hypothesis.hypothesis_id],
    evidence_ids: hypothesis.evidence_ids,
    confidence,
    requires_validation: true
  } } };
});
"""

JS_62_CHECK = r"""
const context = items[0]?.json?.context ?? {};
const diagnoses = items.map(item => item.json.diagnosis_record).filter(Boolean)
  .sort((a, b) => a.diagnosis_id.localeCompare(b.diagnosis_id));
for (const diagnosis of diagnoses) {
  if (!diagnosis.finding_ids.length || !diagnosis.hypothesis_ids.length || !diagnosis.evidence_ids.length) {
    throw new Error('Diagnosis traceability check failed');
  }
  if (diagnosis.diagnosis_type === 'validated_cause' && diagnosis.requires_validation) {
    throw new Error('Public evidence cannot silently become validated cause');
  }
}
return [{ json: { ...context, diagnoses } }];
"""

JS_62_OUTPUT = r"""
const allowed = new Set(['observed_problem', 'likely_cause', 'validated_cause', 'unknown']);
if (!(items[0].json.diagnoses || []).every(diagnosis => allowed.has(diagnosis.diagnosis_type))) {
  throw new Error('62 output violates diagnosis contract');
}
return items;
"""


JS_63_INPUT = r"""
const payload = items[0]?.json ?? {};
if (!Array.isArray(payload.diagnoses) || !Array.isArray(payload.findings)) throw new Error('63 input requires diagnoses[] and findings[]');
if (payload.diagnoses.length === 0) return [{ json: { context: payload, skip: true, validation_required: true } }];
return payload.diagnoses.map((diagnosis, index) => ({ json: {
  context: payload,
  index,
  diagnosis,
  validation_required: diagnosis.requires_validation === true || diagnosis.diagnosis_type === 'unknown' || Number(diagnosis.confidence || 0) < 0.7
} }));
"""

JS_63_VALIDATION_ACTION = r"""
const templates = {
  operations_cx: 'Map the current stakeholder journey and validate each handoff with staff before considering technology changes.',
  revenue_resilience: 'Validate funding sources, concentration, and dependencies with the client before designing a resilience intervention.',
  impact_evidence: 'Review the current impact measurement journey with staff before proposing changes to tools or reporting.'
};
return items.map(item => {
  if (item.json.skip) return { json: { ...item.json, recommendation_record: null } };
  const diagnosis = item.json.diagnosis;
  return { json: { ...item.json, recommendation_record: {
    recommendation_id: `REC-${String(item.json.index + 1).padStart(3, '0')}`,
    finding_ids: diagnosis.finding_ids,
    diagnosis_ids: [diagnosis.diagnosis_id],
    diagnosis: diagnosis.statement,
    action: templates[diagnosis.domain] || 'Validate the current journey with the client before selecting an intervention.',
    priority: diagnosis.diagnosis_type === 'unknown' ? 'high' : 'medium',
    kpi: { name: 'Validation outcome', baseline: null, baseline_status: 'unknown', target: null, timeframe: 'After baseline is confirmed', measurement_method: 'Confirm the measurement method with the client' },
    confidence: diagnosis.confidence,
    requires_human_review: true
  } } };
});
"""

JS_63_IMPROVEMENT_ACTION = r"""
const templates = {
  operations_cx: 'Improve the validated stakeholder journey, beginning with the highest-friction handoff and only then assessing enabling technology.',
  revenue_resilience: 'Implement the agreed revenue resilience improvement based on validated funding dependencies.',
  impact_evidence: 'Implement the agreed impact measurement improvement using the validated reporting journey.'
};
return items.map(item => {
  const diagnosis = item.json.diagnosis;
  return { json: { ...item.json, recommendation_record: {
    recommendation_id: `REC-${String(item.json.index + 1).padStart(3, '0')}`,
    finding_ids: diagnosis.finding_ids,
    diagnosis_ids: [diagnosis.diagnosis_id],
    diagnosis: diagnosis.statement,
    action: templates[diagnosis.domain] || 'Implement a proportionate improvement based on the validated diagnosis.',
    priority: 'medium',
    kpi: { name: 'Improvement outcome', baseline: null, baseline_status: 'unknown', target: null, timeframe: '30-90 days', measurement_method: 'Agree a measurement method with the client' },
    confidence: diagnosis.confidence,
    requires_human_review: false
  } } };
});
"""

JS_63_PROPORTIONALITY = r"""
return items.map(item => {
  const recommendation = item.json.recommendation_record;
  if (!recommendation) return item;
  const technologyFirst = /automate|new platform|replace system/i.test(recommendation.action) && !/journey|handoff|validated/i.test(recommendation.action);
  if (technologyFirst) throw new Error('Journey-before-technology proportionality check failed');
  if (!recommendation.finding_ids.length || !recommendation.diagnosis_ids.length) throw new Error('Recommendation traceability check failed');
  return item;
});
"""

JS_63_STRUCTURE = r"""
const context = items[0]?.json?.context ?? {};
const recommendations = items.map(item => item.json.recommendation_record).filter(Boolean)
  .sort((a, b) => a.recommendation_id.localeCompare(b.recommendation_id));
return [{ json: { ...context, recommendations } }];
"""

JS_63_OUTPUT = r"""
for (const recommendation of items[0].json.recommendations || []) {
  if (!recommendation.action || !recommendation.kpi || typeof recommendation.requires_human_review !== 'boolean') {
    throw new Error('63 output violates recommendation contract');
  }
}
return items;
"""


JS_64_INPUT = r"""
const payload = items[0]?.json ?? {};
if (!Array.isArray(payload.recommendations) || !Array.isArray(payload.diagnoses)) throw new Error('64 input requires recommendations[] and diagnoses[]');
if (payload.recommendations.length === 0) return [{ json: { context: payload, skip: true, baseline_known: false } }];
return payload.recommendations.map((recommendation, index) => {
  const diagnosis = payload.diagnoses.find(d => (recommendation.diagnosis_ids || []).includes(d.diagnosis_id)) || {};
  const scaffold = recommendation.kpi || {};
  return { json: {
    context: payload,
    index,
    recommendation,
    domain: diagnosis.domain,
    baseline_known: scaffold.baseline_status === 'known' && scaffold.baseline !== null && scaffold.baseline !== undefined
  } };
});
"""

JS_64_OUTCOME = r"""
const outcomes = {
  operations_cx: 'A clearer, faster stakeholder journey with fewer unverified handoffs',
  revenue_resilience: 'A better-understood and more resilient funding mix',
  impact_evidence: 'A usable and credible impact measurement journey'
};
return items.map(item => ({ json: { ...item.json, desired_outcome: outcomes[item.json.domain] || 'A measurable improvement tied to the validated diagnosis' } }));
"""

JS_64_PRESERVE = r"""
return items.map(item => ({ json: { ...item.json, baseline: item.json.recommendation.kpi.baseline, baseline_status: 'known' } }));
"""

JS_64_UNKNOWN = r"""
return items.map(item => ({ json: { ...item.json, baseline: null, baseline_status: 'unknown' } }));
"""

JS_64_MEASURE = r"""
const definitions = {
  operations_cx: { name: 'Stakeholder journey follow-up time', method: 'Measure elapsed time between the defined journey start and the first completed follow-up using agreed timestamps.' },
  revenue_resilience: { name: 'Funding concentration visibility', method: 'Review verified income by funding source and calculate concentration after the baseline data is supplied.' },
  impact_evidence: { name: 'Impact measurement coverage', method: 'Review the share of active programs with an agreed outcome, indicator, owner, and reporting cadence.' }
};
return items.map(item => {
  if (item.json.skip) return { json: { ...item.json, kpi_record: null } };
  const definition = definitions[item.json.domain] || { name: 'Validated improvement indicator', method: 'Agree the data source, owner, and reporting cadence with the client.' };
  const scaffold = item.json.recommendation.kpi || {};
  const known = item.json.baseline_status === 'known';
  return { json: { ...item.json, kpi_record: {
    name: definition.name,
    baseline: known ? item.json.baseline : null,
    baseline_status: known ? 'known' : 'unknown',
    target: known ? (scaffold.target ?? null) : null,
    timeframe: scaffold.timeframe || 'After baseline is confirmed',
    measurement_method: definition.method
  } } };
});
"""

JS_64_STRUCTURE = r"""
const context = items[0]?.json?.context ?? {};
const records = items.filter(item => item.json.kpi_record).sort((a, b) => a.json.index - b.json.index);
const kpis = records.map(item => item.json.kpi_record);
const byRecommendationId = new Map(records.map(item => [item.json.recommendation.recommendation_id, item.json.kpi_record]));
const recommendations = (context.recommendations || []).map(rec => ({ ...rec, kpi: byRecommendationId.get(rec.recommendation_id) || rec.kpi }));
for (const kpi of kpis) {
  if (kpi.baseline_status === 'unknown' && kpi.baseline !== null) throw new Error('Unknown KPI baseline must be null');
}
return [{ json: { ...context, recommendations, kpis } }];
"""

JS_64_OUTPUT = r"""
const required = ['name', 'baseline', 'baseline_status', 'target', 'timeframe', 'measurement_method'];
if (!(items[0].json.kpis || []).every(kpi => required.every(key => Object.prototype.hasOwnProperty.call(kpi, key)))) {
  throw new Error('64 output violates KPI contract');
}
return items;
"""


JS_65_INPUT = r"""
const payload = items[0]?.json ?? {};
if (!Array.isArray(payload.hypotheses) || !Array.isArray(payload.unknowns) || !Array.isArray(payload.diagnoses)) {
  throw new Error('65 input requires hypotheses[], unknowns[], and diagnoses[]');
}
if (payload.hypotheses.length === 0) return [{ json: { context: payload, skip: true } }];
return payload.hypotheses.map((hypothesis, index) => {
  const diagnosis = payload.diagnoses.find(d => (d.hypothesis_ids || []).includes(hypothesis.hypothesis_id)) || {};
  const relatedUnknown = payload.unknowns.find(unknown =>
    unknown.domain === hypothesis.domain ||
    (unknown.evidence_ids || []).some(id => (hypothesis.evidence_ids || []).includes(id))
  );
  return { json: { context: payload, index, hypothesis, diagnosis, related_unknown: relatedUnknown || null } };
});
"""

JS_65_GAP = r"""
return items.map(item => {
  if (item.json.skip) return item;
  const gap = item.json.related_unknown?.description || item.json.hypothesis.validation_gap ||
    `Validate hypothesis ${item.json.hypothesis.hypothesis_id}.`;
  return { json: { ...item.json, validation_gap: gap } };
});
"""

JS_65_QUESTION = r"""
const templates = {
  operations_cx: 'What happens internally after someone enters this stakeholder journey, and which handoffs occur before the next response?',
  revenue_resilience: 'How is annual income distributed across funding sources, and how has that mix changed over the most recent reporting period?',
  impact_evidence: 'How do you currently measure and report impact, and which steps or methods are used across active programs?'
};
return items.map(item => {
  if (item.json.skip) return { json: { ...item.json, question_record: null } };
  const hypothesis = item.json.hypothesis;
  return { json: { ...item.json, question_record: {
    question_id: `Q-${String(item.json.index + 1).padStart(3, '0')}`,
    finding_ids: hypothesis.finding_ids,
    hypothesis_ids: [hypothesis.hypothesis_id],
    question: templates[hypothesis.domain] || 'Can you describe how this process currently works in practice?',
    purpose: `Validate: ${item.json.validation_gap}`,
    domain: hypothesis.domain,
    priority: item.json.diagnosis.diagnosis_type === 'unknown' ? 'high' : 'medium'
  } } };
});
"""

JS_65_LEADING = r"""
const leadingPatterns = [/\bdon't you\b/i, /\bisn't it true\b/i, /\bwouldn't you agree\b/i, /\bobviously\b/i];
return items.map(item => {
  const question = item.json.question_record;
  if (!question) return item;
  if (leadingPatterns.some(pattern => pattern.test(question.question))) throw new Error('Leading-language check failed');
  if (!question.question.trim().endsWith('?')) throw new Error('Validation question must be explicit and end with a question mark');
  return item;
});
"""

JS_65_TRACE = r"""
const context = items[0]?.json?.context ?? {};
const validation_questions = items.map(item => item.json.question_record).filter(Boolean)
  .sort((a, b) => a.question_id.localeCompare(b.question_id));
for (const question of validation_questions) {
  if (!question.finding_ids.length && !question.hypothesis_ids.length) throw new Error('Validation question traceability check failed');
}
return [{ json: { ...context, validation_questions } }];
"""

JS_65_OUTPUT = r"""
if (!(items[0].json.validation_questions || []).every(question => /^Q-/.test(question.question_id))) {
  throw new Error('65 output violates validation question contract');
}
return items;
"""


JS_66_INPUT = r"""
const payload = items[0]?.json ?? {};
for (const key of ['recommendations', 'diagnoses', 'hypotheses', 'validation_questions', 'kpis']) {
  if (!Array.isArray(payload[key])) throw new Error(`66 input requires ${key}[]`);
}
if (payload.recommendations.length === 0) return [{ json: { context: payload, skip: true, validation_first: true } }];
return payload.recommendations.map((recommendation, index) => {
  const diagnoses = payload.diagnoses.filter(d => (recommendation.diagnosis_ids || []).includes(d.diagnosis_id));
  const hypothesisIds = [...new Set(diagnoses.flatMap(d => d.hypothesis_ids || []))];
  const questions = payload.validation_questions.filter(question =>
    (question.finding_ids || []).some(id => (recommendation.finding_ids || []).includes(id)) ||
    (question.hypothesis_ids || []).some(id => hypothesisIds.includes(id))
  );
  const validationFirst = recommendation.requires_human_review === true || diagnoses.some(d => d.requires_validation === true);
  return { json: { context: payload, index, recommendation, diagnoses, hypothesis_ids: hypothesisIds, questions, validation_first: validationFirst } };
});
"""

JS_66_VALIDATION = r"""
return items.map(item => {
  if (item.json.skip) return { json: { ...item.json, roadmap_record: null } };
  const unknown = item.json.diagnoses.some(d => d.diagnosis_type === 'unknown');
  return { json: { ...item.json, roadmap_record: {
    roadmap_action_id: `RA-${String(item.json.index + 1).padStart(3, '0')}`,
    time_bucket: '30_days',
    action: unknown
      ? `Discover the missing internal context before intervention: ${item.json.recommendation.action}`
      : `Validate the diagnosis with the client before intervention: ${item.json.recommendation.action}`,
    action_type: unknown ? 'discovery' : 'validation',
    recommendation_ids: [item.json.recommendation.recommendation_id],
    hypothesis_ids: item.json.hypothesis_ids,
    validation_question_ids: item.json.questions.map(question => question.question_id)
  } } };
});
"""

JS_66_IMPROVEMENT = r"""
return items.map(item => ({ json: { ...item.json, roadmap_record: {
  roadmap_action_id: `RA-${String(item.json.index + 1).padStart(3, '0')}`,
  time_bucket: item.json.recommendation.priority === 'high' ? '60_days' : '90_days',
  action: item.json.recommendation.action,
  action_type: 'implementation',
  recommendation_ids: [item.json.recommendation.recommendation_id],
  hypothesis_ids: item.json.hypothesis_ids,
  validation_question_ids: item.json.questions.map(question => question.question_id)
} } }));
"""

JS_66_SEQUENCE = r"""
const order = { '30_days': 1, '60_days': 2, '90_days': 3 };
return items.sort((a, b) => (order[a.json.roadmap_record?.time_bucket] || 99) - (order[b.json.roadmap_record?.time_bucket] || 99) || a.json.index - b.json.index);
"""

JS_66_STRUCTURE = r"""
const context = items[0]?.json?.context ?? {};
const roadmap_actions = items.map(item => item.json.roadmap_record).filter(Boolean);
const allowed = new Set(['implementation', 'validation', 'discovery']);
for (const action of roadmap_actions) {
  if (!allowed.has(action.action_type)) throw new Error('Roadmap action_type violates contract');
  const relatedHypotheses = (context.hypotheses || []).filter(h => action.hypothesis_ids.includes(h.hypothesis_id));
  if (relatedHypotheses.some(h => h.requires_validation) && action.action_type === 'implementation') {
    throw new Error('Unvalidated hypothesis cannot become an implementation task');
  }
}
return [{ json: { ...context, roadmap_actions } }];
"""

JS_66_OUTPUT = r"""
const payload = items[0].json;
return [{ json: {
  hypotheses: payload.hypotheses || [],
  diagnoses: payload.diagnoses || [],
  recommendations: payload.recommendations || [],
  kpis: payload.kpis || [],
  validation_questions: payload.validation_questions || [],
  roadmap_actions: payload.roadmap_actions || []
} }];
"""


def configure_61():
    nodes = [
        trigger(),
        code_node("INPUT_CONTRACT__FINDINGS_EVIDENCE_UNKNOWNS", JS_61_INPUT, 260, 0),
        if_node("DECISION__CAN_INTERNAL_REALITY_BE_OBSERVED", "={{ $json.can_observe_internal_reality }}", True, 560, 0),
        code_node("PRESERVE_OBSERVED_INTERPRETATION", JS_61_OBSERVED, 860, -140),
        code_node("BUILD_HYPOTHESIS_FROM_GAP", JS_61_HYPOTHESIS, 860, 140),
        merge_node("MERGE__OBSERVED_AND_HYPOTHESIS", 1160, 0),
        code_node("CONFIDENCE_AND_VALIDATION_GAP", JS_61_CONFIDENCE, 1460, 0),
        code_node("STRUCTURE_HYPOTHESIS_RECORDS", JS_61_STRUCTURE, 1760, 0),
        code_node("OUTPUT_CONTRACT__HYPOTHESES", JS_61_OUTPUT, 2060, 0),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__FINDINGS_EVIDENCE_UNKNOWNS"),
        ("INPUT_CONTRACT__FINDINGS_EVIDENCE_UNKNOWNS", "DECISION__CAN_INTERNAL_REALITY_BE_OBSERVED"),
        ("DECISION__CAN_INTERNAL_REALITY_BE_OBSERVED", "PRESERVE_OBSERVED_INTERPRETATION", 0),
        ("DECISION__CAN_INTERNAL_REALITY_BE_OBSERVED", "BUILD_HYPOTHESIS_FROM_GAP", 1),
        ("PRESERVE_OBSERVED_INTERPRETATION", "MERGE__OBSERVED_AND_HYPOTHESIS", 0, 0),
        ("BUILD_HYPOTHESIS_FROM_GAP", "MERGE__OBSERVED_AND_HYPOTHESIS", 0, 1),
        ("MERGE__OBSERVED_AND_HYPOTHESIS", "CONFIDENCE_AND_VALIDATION_GAP"),
        ("CONFIDENCE_AND_VALIDATION_GAP", "STRUCTURE_HYPOTHESIS_RECORDS"),
        ("STRUCTURE_HYPOTHESIS_RECORDS", "OUTPUT_CONTRACT__HYPOTHESES"),
    ]
    return workflow(
        "61_HYPOTHESIS_BUILDER",
        "Build explicit hypotheses from public findings without turning internal unknowns into facts.",
        "Paola track output: run_context, findings[], evidence[], unknowns[]",
        "Accumulated payload plus hypotheses[] conforming to hypothesis.schema.json",
        nodes,
        edges,
        "VISIBLE PATH\nInput findings + evidence + unknowns -> Can internal reality be observed?\nYES -> preserve observed interpretation\nNO -> build hypothesis -> confidence + validation gap -> structured hypotheses\nEvery hypothesis requires validation and carries finding/evidence IDs.",
    )


def configure_62():
    nodes = [
        trigger(),
        code_node("INPUT_CONTRACT__FINDINGS_HYPOTHESES", JS_62_INPUT, 260, 0),
        code_node("EVALUATE_EVIDENCE_STRENGTH", JS_62_STRENGTH, 560, 0),
        if_node("DECISION__DIRECT_CLIENT_VALIDATION_PRESENT", "={{ $json.direct_validation_present }}", True, 860, 0),
        code_node("CLASSIFY__VALIDATED_CAUSE", JS_62_VALIDATED, 1160, -140),
        code_node("CLASSIFY__PUBLIC_EVIDENCE", JS_62_PUBLIC, 1160, 140),
        merge_node("MERGE__DIAGNOSIS_CLASSIFICATIONS", 1460, 0),
        code_node("TRACEABILITY_AND_VALIDATION_BOUNDARY_CHECK", JS_62_CHECK, 1760, 0),
        code_node("OUTPUT_CONTRACT__DIAGNOSES", JS_62_OUTPUT, 2060, 0),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__FINDINGS_HYPOTHESES"),
        ("INPUT_CONTRACT__FINDINGS_HYPOTHESES", "EVALUATE_EVIDENCE_STRENGTH"),
        ("EVALUATE_EVIDENCE_STRENGTH", "DECISION__DIRECT_CLIENT_VALIDATION_PRESENT"),
        ("DECISION__DIRECT_CLIENT_VALIDATION_PRESENT", "CLASSIFY__VALIDATED_CAUSE", 0),
        ("DECISION__DIRECT_CLIENT_VALIDATION_PRESENT", "CLASSIFY__PUBLIC_EVIDENCE", 1),
        ("CLASSIFY__VALIDATED_CAUSE", "MERGE__DIAGNOSIS_CLASSIFICATIONS", 0, 0),
        ("CLASSIFY__PUBLIC_EVIDENCE", "MERGE__DIAGNOSIS_CLASSIFICATIONS", 0, 1),
        ("MERGE__DIAGNOSIS_CLASSIFICATIONS", "TRACEABILITY_AND_VALIDATION_BOUNDARY_CHECK"),
        ("TRACEABILITY_AND_VALIDATION_BOUNDARY_CHECK", "OUTPUT_CONTRACT__DIAGNOSES"),
    ]
    return workflow(
        "62_ROOT_CAUSE_DIAGNOSIS",
        "Classify diagnoses while maintaining the boundary between public evidence and client-validated causes.",
        "Accumulated payload with findings[], evidence[], hypotheses[]",
        "Accumulated payload plus diagnoses[] conforming to diagnosis.schema.json",
        nodes,
        edges,
        "VISIBLE PATH\nFinding + hypothesis -> evidence strength -> direct client validation?\nYES -> validated_cause\nNO -> observed_problem / likely_cause / unknown\nTraceability and boundary check prevents public evidence from silently becoming validated cause.",
    )


def configure_63():
    nodes = [
        trigger(),
        code_node("INPUT_CONTRACT__DIAGNOSES_FINDINGS", JS_63_INPUT, 260, 0),
        if_node("DECISION__VALIDATION_REQUIRED", "={{ $json.validation_required }}", True, 560, 0),
        code_node("BUILD__VALIDATION_OR_DISCOVERY_ACTION", JS_63_VALIDATION_ACTION, 860, -140),
        code_node("BUILD__IMPROVEMENT_ACTION", JS_63_IMPROVEMENT_ACTION, 860, 140),
        merge_node("MERGE__ACTION_PATHS", 1160, 0),
        code_node("MISSION_AND_PROPORTIONALITY_CHECK", JS_63_PROPORTIONALITY, 1460, 0),
        code_node("STRUCTURE_RECOMMENDATIONS", JS_63_STRUCTURE, 1760, 0),
        code_node("OUTPUT_CONTRACT__RECOMMENDATIONS", JS_63_OUTPUT, 2060, 0),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__DIAGNOSES_FINDINGS"),
        ("INPUT_CONTRACT__DIAGNOSES_FINDINGS", "DECISION__VALIDATION_REQUIRED"),
        ("DECISION__VALIDATION_REQUIRED", "BUILD__VALIDATION_OR_DISCOVERY_ACTION", 0),
        ("DECISION__VALIDATION_REQUIRED", "BUILD__IMPROVEMENT_ACTION", 1),
        ("BUILD__VALIDATION_OR_DISCOVERY_ACTION", "MERGE__ACTION_PATHS", 0, 0),
        ("BUILD__IMPROVEMENT_ACTION", "MERGE__ACTION_PATHS", 0, 1),
        ("MERGE__ACTION_PATHS", "MISSION_AND_PROPORTIONALITY_CHECK"),
        ("MISSION_AND_PROPORTIONALITY_CHECK", "STRUCTURE_RECOMMENDATIONS"),
        ("STRUCTURE_RECOMMENDATIONS", "OUTPUT_CONTRACT__RECOMMENDATIONS"),
    ]
    return workflow(
        "63_ACTION_DESIGN",
        "Create proportionate recommendations that validate uncertain diagnoses before intervention.",
        "Accumulated payload with diagnoses[] and findings[]",
        "Accumulated payload plus recommendations[] conforming to recommendation.schema.json",
        nodes,
        edges,
        "VISIBLE PATH\nDiagnosis -> validation required?\nYES -> discovery/validation action\nNO -> improvement action\nMission + proportionality gate -> structured recommendation\nJourney before technology is enforced.",
    )


def configure_64():
    nodes = [
        trigger(),
        code_node("INPUT_CONTRACT__RECOMMENDATIONS_DIAGNOSES", JS_64_INPUT, 260, 0),
        code_node("DEFINE_DESIRED_OUTCOME", JS_64_OUTCOME, 560, 0),
        if_node("DECISION__BASELINE_KNOWN", "={{ $json.baseline_known }}", True, 860, 0),
        code_node("PRESERVE_KNOWN_BASELINE", JS_64_PRESERVE, 1160, -140),
        code_node("SET_UNKNOWN_BASELINE_TO_NULL", JS_64_UNKNOWN, 1160, 140),
        merge_node("MERGE__BASELINE_PATHS", 1460, 0),
        code_node("DEFINE_MEASUREMENT_METHOD", JS_64_MEASURE, 1760, 0),
        code_node("STRUCTURE_KPIS_AND_SYNC_RECOMMENDATIONS", JS_64_STRUCTURE, 2060, 0),
        code_node("OUTPUT_CONTRACT__KPIS", JS_64_OUTPUT, 2360, 0),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__RECOMMENDATIONS_DIAGNOSES"),
        ("INPUT_CONTRACT__RECOMMENDATIONS_DIAGNOSES", "DEFINE_DESIRED_OUTCOME"),
        ("DEFINE_DESIRED_OUTCOME", "DECISION__BASELINE_KNOWN"),
        ("DECISION__BASELINE_KNOWN", "PRESERVE_KNOWN_BASELINE", 0),
        ("DECISION__BASELINE_KNOWN", "SET_UNKNOWN_BASELINE_TO_NULL", 1),
        ("PRESERVE_KNOWN_BASELINE", "MERGE__BASELINE_PATHS", 0, 0),
        ("SET_UNKNOWN_BASELINE_TO_NULL", "MERGE__BASELINE_PATHS", 0, 1),
        ("MERGE__BASELINE_PATHS", "DEFINE_MEASUREMENT_METHOD"),
        ("DEFINE_MEASUREMENT_METHOD", "STRUCTURE_KPIS_AND_SYNC_RECOMMENDATIONS"),
        ("STRUCTURE_KPIS_AND_SYNC_RECOMMENDATIONS", "OUTPUT_CONTRACT__KPIS"),
    ]
    return workflow(
        "64_KPI_DESIGN",
        "Define measurable KPIs without inventing numerical baselines or targets.",
        "Accumulated payload with recommendations[] and diagnoses[]",
        "Accumulated payload plus kpis[] conforming to kpi.schema.json; recommendation KPI objects synchronized",
        nodes,
        edges,
        "VISIBLE PATH\nAction -> desired outcome -> baseline known?\nYES -> preserve supplied baseline\nNO -> baseline null / unknown\nDefine measurement method -> structured KPI output.",
    )


def configure_65():
    nodes = [
        trigger(),
        code_node("INPUT_CONTRACT__HYPOTHESES_UNKNOWNS_DIAGNOSES", JS_65_INPUT, 260, 0),
        code_node("DETERMINE_VALIDATION_GAP", JS_65_GAP, 560, 0),
        code_node("GENERATE_NEUTRAL_QUESTION", JS_65_QUESTION, 860, 0),
        code_node("LEADING_LANGUAGE_CHECK", JS_65_LEADING, 1160, 0),
        code_node("TRACEABILITY_CHECK", JS_65_TRACE, 1460, 0),
        code_node("OUTPUT_CONTRACT__VALIDATION_QUESTIONS", JS_65_OUTPUT, 1760, 0),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__HYPOTHESES_UNKNOWNS_DIAGNOSES"),
        ("INPUT_CONTRACT__HYPOTHESES_UNKNOWNS_DIAGNOSES", "DETERMINE_VALIDATION_GAP"),
        ("DETERMINE_VALIDATION_GAP", "GENERATE_NEUTRAL_QUESTION"),
        ("GENERATE_NEUTRAL_QUESTION", "LEADING_LANGUAGE_CHECK"),
        ("LEADING_LANGUAGE_CHECK", "TRACEABILITY_CHECK"),
        ("TRACEABILITY_CHECK", "OUTPUT_CONTRACT__VALIDATION_QUESTIONS"),
    ]
    return workflow(
        "65_CLIENT_VALIDATION_QUESTIONS",
        "Turn hypotheses, unknowns, and likely causes into neutral, traceable client questions.",
        "Accumulated payload with hypotheses[], unknowns[], diagnoses[]",
        "Accumulated payload plus validation_questions[] conforming to validation_question.schema.json",
        nodes,
        edges,
        "VISIBLE PATH\nHypothesis / unknown / likely cause -> validation gap -> neutral question -> leading-language check -> traceability check -> question output.\nEvery emitted question links to a finding and hypothesis.",
    )


def configure_66():
    nodes = [
        trigger(),
        code_node("INPUT_CONTRACT__TRANSFORMATION_COMPONENTS", JS_66_INPUT, 260, 0),
        if_node("DECISION__VALIDATION_FIRST", "={{ $json.validation_first }}", True, 560, 0),
        code_node("BUILD__VALIDATION_OR_DISCOVERY_TASK", JS_66_VALIDATION, 860, -140),
        code_node("BUILD__IMPROVEMENT_TASK", JS_66_IMPROVEMENT, 860, 140),
        merge_node("MERGE__ROADMAP_PATHS", 1160, 0),
        code_node("SEQUENCE__30_60_90_DAYS", JS_66_SEQUENCE, 1460, 0),
        code_node("STRUCTURE_AND_VALIDATE_ROADMAP", JS_66_STRUCTURE, 1760, 0),
        code_node("OUTPUT_CONTRACT__GRETEL_TRACK", JS_66_OUTPUT, 2060, 0),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__TRANSFORMATION_COMPONENTS"),
        ("INPUT_CONTRACT__TRANSFORMATION_COMPONENTS", "DECISION__VALIDATION_FIRST"),
        ("DECISION__VALIDATION_FIRST", "BUILD__VALIDATION_OR_DISCOVERY_TASK", 0),
        ("DECISION__VALIDATION_FIRST", "BUILD__IMPROVEMENT_TASK", 1),
        ("BUILD__VALIDATION_OR_DISCOVERY_TASK", "MERGE__ROADMAP_PATHS", 0, 0),
        ("BUILD__IMPROVEMENT_TASK", "MERGE__ROADMAP_PATHS", 0, 1),
        ("MERGE__ROADMAP_PATHS", "SEQUENCE__30_60_90_DAYS"),
        ("SEQUENCE__30_60_90_DAYS", "STRUCTURE_AND_VALIDATE_ROADMAP"),
        ("STRUCTURE_AND_VALIDATE_ROADMAP", "OUTPUT_CONTRACT__GRETEL_TRACK"),
    ]
    return workflow(
        "66_90_DAY_ROADMAP",
        "Sequence recommendations into validation-first or implementation roadmap actions.",
        "Accumulated payload with recommendations[], kpis[], validation_questions[], hypotheses[], diagnoses[]",
        "Exact Gretel track object with hypotheses, diagnoses, recommendations, kpis, validation_questions, roadmap_actions",
        nodes,
        edges,
        "VISIBLE PATH\nActions -> validation status -> validation first?\nYES -> 30-day validation/discovery task\nNO -> 60/90-day implementation task\nSequence -> roadmap contract check.\nUnvalidated hypotheses cannot become implementation actions.",
    )


def fixture_code(fixture, label):
    serialized = json.dumps(fixture, separators=(",", ":"), ensure_ascii=False)
    return f"// {label}: development data embedded from repository fixture.\nconst fixture = {serialized};\nreturn [{{ json: fixture }}];"


def configure_dev():
    normal = json.loads((ROOT / "fixtures" / "paola_track_output.json").read_text(encoding="utf-8"))
    insufficient = json.loads((ROOT / "fixtures" / "paola_track_insufficient_evidence.json").read_text(encoding="utf-8"))
    nodes = [
        sticky(
            "00_README__DEV_WORKFLOW",
            "DEV_GRETEL_P0_LIVE_TEST\nDevelopment-only runner for repository fixtures.\nImport after workflows 61-66, then manually select each imported workflow in its Execute Sub-workflow node.\nNo workflow IDs or production data are embedded.\nChange selected_case in DEV_SELECT_TEST_CASE to normal or insufficient_evidence.",
            -520,
            -360,
            580,
            360,
            4,
        ),
        sticky(
            "NOTE__EXPECTED_TESTS",
            "NORMAL\nTwo evidence-backed hypotheses proceed through diagnosis, validation-first recommendations, unknown-baseline KPIs, neutral questions, and 30-day validation tasks.\n\nINSUFFICIENT EVIDENCE\nLow-confidence unknown -> validation-first recommendation -> null/unknown KPI -> neutral question -> 30-day discovery task.",
            -520,
            40,
            580,
            340,
            5,
        ),
        manual_trigger(),
        code_node("DEV_SELECT_TEST_CASE", "return [{ json: { selected_case: 'normal' } }];", 260, 0),
        if_node("DECISION__NORMAL_FIXTURE", "={{ $json.selected_case }}", "normal", 560, 0, "string"),
        code_node("DEV_INPUT__PAOLA_TRACK_FIXTURE", fixture_code(normal, "DEV NORMAL FIXTURE"), 860, -140),
        code_node("DEV_INPUT__INSUFFICIENT_EVIDENCE_FIXTURE", fixture_code(insufficient, "DEV INSUFFICIENT-EVIDENCE FIXTURE"), 860, 140),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER", "61_HYPOTHESIS_BUILDER", 1160, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__62_ROOT_CAUSE_DIAGNOSIS", "62_ROOT_CAUSE_DIAGNOSIS", 1460, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__63_ACTION_DESIGN", "63_ACTION_DESIGN", 1760, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__64_KPI_DESIGN", "64_KPI_DESIGN", 2060, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__65_CLIENT_VALIDATION_QUESTIONS", "65_CLIENT_VALIDATION_QUESTIONS", 2360, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP", "66_90_DAY_ROADMAP", 2660, 0),
        code_node("FINAL_GRETEL_TRACK_OUTPUT", "return items;", 2960, 0),
    ]
    edges = [
        ("START__MANUAL_TEST_TRIGGER", "DEV_SELECT_TEST_CASE"),
        ("DEV_SELECT_TEST_CASE", "DECISION__NORMAL_FIXTURE"),
        ("DECISION__NORMAL_FIXTURE", "DEV_INPUT__PAOLA_TRACK_FIXTURE", 0),
        ("DECISION__NORMAL_FIXTURE", "DEV_INPUT__INSUFFICIENT_EVIDENCE_FIXTURE", 1),
        ("DEV_INPUT__PAOLA_TRACK_FIXTURE", "TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER"),
        ("DEV_INPUT__INSUFFICIENT_EVIDENCE_FIXTURE", "TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER"),
        ("TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER", "TODO_LINK_SUBWORKFLOW__62_ROOT_CAUSE_DIAGNOSIS"),
        ("TODO_LINK_SUBWORKFLOW__62_ROOT_CAUSE_DIAGNOSIS", "TODO_LINK_SUBWORKFLOW__63_ACTION_DESIGN"),
        ("TODO_LINK_SUBWORKFLOW__63_ACTION_DESIGN", "TODO_LINK_SUBWORKFLOW__64_KPI_DESIGN"),
        ("TODO_LINK_SUBWORKFLOW__64_KPI_DESIGN", "TODO_LINK_SUBWORKFLOW__65_CLIENT_VALIDATION_QUESTIONS"),
        ("TODO_LINK_SUBWORKFLOW__65_CLIENT_VALIDATION_QUESTIONS", "TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP"),
        ("TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP", "FINAL_GRETEL_TRACK_OUTPUT"),
    ]
    return {
        "name": "DEV_GRETEL_P0_LIVE_TEST",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure_gretel_p0_workflows(root=ROOT):
    global ROOT, WORKFLOW_DIR, DEV_WORKFLOW_DIR
    ROOT = Path(root)
    WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
    DEV_WORKFLOW_DIR = ROOT / "workflows" / "dev"
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    DEV_WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    workflow_builders = {
        "61_HYPOTHESIS_BUILDER.json": configure_61,
        "62_ROOT_CAUSE_DIAGNOSIS.json": configure_62,
        "63_ACTION_DESIGN.json": configure_63,
        "64_KPI_DESIGN.json": configure_64,
        "65_CLIENT_VALIDATION_QUESTIONS.json": configure_65,
        "66_90_DAY_ROADMAP.json": configure_66,
    }
    for filename, builder in workflow_builders.items():
        (WORKFLOW_DIR / filename).write_text(json.dumps(builder(), indent=2) + "\n", encoding="utf-8")
    (DEV_WORKFLOW_DIR / "DEV_GRETEL_P0_LIVE_TEST.json").write_text(
        json.dumps(configure_dev(), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    configure_gretel_p0_workflows()
    print("Configured Gretel P0 n8n workflows 61-66 and DEV_GRETEL_P0_LIVE_TEST.")
