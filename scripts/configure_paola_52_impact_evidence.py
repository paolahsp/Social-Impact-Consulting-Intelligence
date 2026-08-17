import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=640, height=340, color=4):
    return {
        "parameters": {"content": content, "height": height, "width": width, "color": color},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
    }


def code_node(name, js_code, x, y):
    return {
        "parameters": {"jsCode": js_code.strip() + "\n"},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, y],
    }


def if_node(name, field, expected, x, y):
    return {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": slug(f"{name}_{expected}"),
                        "leftValue": f"={{{{ $json.{field} }}}}",
                        "rightValue": expected,
                        "operator": {"type": "string", "operation": "equals"},
                    }
                ],
                "combinator": "and",
            },
            "options": {},
        },
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "position": [x, y],
    }


def execute_subworkflow_node(name, x, y):
    return {
        "parameters": {
            "source": "database",
            "workflowId": {
                "__rl": True,
                "value": "",
                "mode": "list",
                "cachedResultName": "52_IMPACT_EVIDENCE_AGENT",
            },
            "workflowInputs": {
                "mappingMode": "passThrough",
                "value": {},
                "matchingColumns": [],
                "schema": [],
                "attemptToConvertTypes": False,
                "convertFieldsToString": True,
            },
            "options": {"waitForSubWorkflow": True},
        },
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1.3,
        "position": [x, y],
        "notes": "AFTER IMPORT: select the stored n8n workflow 52_IMPACT_EVIDENCE_AGENT. Never invent an ID.",
    }


def connections(edges):
    result = {}
    for edge in edges:
        source, target = edge[:2]
        source_output = edge[2] if len(edge) > 2 else 0
        target_input = edge[3] if len(edge) > 3 else 0
        result.setdefault(source, {"main": []})
        while len(result[source]["main"]) <= source_output:
            result[source]["main"].append([])
        result[source]["main"][source_output].append(
            {"node": target, "type": "main", "index": target_input}
        )
    return result


JS_INPUT_CONTRACT = r"""
return items.map(item => {
  const payload = item.json || {};
  const nested = payload.paola_track_output || payload;
  const runContext = nested.run_context || payload.run_context || {};
  const sources = Array.isArray(nested.sources) ? nested.sources : [];
  const evidence = Array.isArray(nested.evidence) ? nested.evidence : [];
  const documents = Array.isArray(nested.documents) ? nested.documents : [];
  const ragContext = nested.rag_context || payload.rag_context || { contexts: [] };
  const errors = [];
  if (!runContext.run_id) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'run_context.run_id is required' });
  if (!Array.isArray(sources)) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'sources must be an array' });
  if (!Array.isArray(evidence)) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'evidence must be an array' });
  return {
    json: {
      run_context: runContext,
      sources,
      evidence,
      documents,
      rag_context: ragContext,
      controlled_state: errors.length ? 'request_failure' : 'ready',
      errors,
      impact_taxonomy: ['activity', 'output', 'outcome', 'impact', 'indicator', 'unknown', 'impact_claim', 'impact_evidence']
    }
  };
});
"""


JS_FILTER_IMPACT_EVIDENCE = r"""
const impactTerms = ['impact', 'outcome', 'beneficiar', 'recipient', 'household', 'participant', 'people reached', 'transfer', 'poverty', 'mission', 'program', 'programme', 'kpi', 'indicator', 'research', 'evaluation', 'follow-up', 'follow up'];
function hasImpactSignal(value) {
  const text = String(value || '').toLowerCase();
  return impactTerms.some(term => text.includes(term));
}
function splitSentences(value) {
  return String(value || '').replace(/\s+/g, ' ').split(/(?<=[.!?])\s+/).map(s => s.trim()).filter(Boolean);
}
function nextId(index) {
  return `EV-IMP-${String(index + 1).padStart(3, '0')}`;
}
return items.map(item => {
  if (item.json.controlled_state === 'request_failure') return item;
  const sourceIds = new Set((item.json.sources || []).map(source => source.source_id));
  const impactEvidence = [];
  for (const ev of item.json.evidence || []) {
    const text = `${ev.domain || ''} ${ev.claim || ''}`;
    const refs = (ev.source_ids || []).filter(id => sourceIds.has(id));
    if (refs.length && hasImpactSignal(text)) {
      impactEvidence.push({ ...ev, source_ids: refs, impact_signal_source: 'evidence_ledger' });
    }
  }
  for (const doc of item.json.documents || []) {
    const sourceId = doc.source_id;
    if (!sourceIds.has(sourceId)) continue;
    const sections = Array.isArray(doc.sections) ? doc.sections : [];
    for (const section of sections) {
      const sectionType = String(section.section_type || '').toLowerCase();
      if (sectionType !== 'impact') continue;
      if (!hasImpactSignal(`${section.section_type || ''} ${section.text || ''}`)) continue;
      const selected = splitSentences(section.text)
        .filter(hasImpactSignal)
        .filter(sentence => !/financial statements|net assets|receivable|inventory|fair value|cash flows|auditors/i.test(sentence));
      for (const sentence of selected.slice(0, 4)) {
        if (impactEvidence.length >= 12) break;
        impactEvidence.push({
          evidence_id: nextId(impactEvidence.length),
          run_id: item.json.run_context.run_id,
          claim: sentence.slice(0, 360),
          source_ids: [sourceId],
          domain: 'impact_evidence',
          evidence_type: 'fact',
          confidence: doc.is_official ? 0.72 : 0.58,
          status: 'supported',
          contradiction_ids: [],
          requires_validation: false,
          impact_signal_source: 'document_section',
          document_id: doc.document_id || null,
          document_type: doc.document_type || null,
          section_type: section.section_type || null
        });
      }
    }
  }
  const controlledState = impactEvidence.length ? 'impact_evidence_available' : 'insufficient_evidence';
  return { json: { ...item.json, impact_evidence: impactEvidence, controlled_state: controlledState } };
});
"""


JS_CLASSIFY_IMPACT_LEVEL = r"""
function levelFor(claim) {
  const text = String(claim || '').toLowerCase();
  const hasNumber = /\b\d+([,.]\d+)?%?\b/.test(text);
  if (/(mission|aim|goal|vision).{0,80}(reduce poverty|improve|impact|change lives|alleviate suffering)/.test(text)) return 'impact_claim';
  if (/(long[- ]term|sustain|five years|years later|poverty reduction measured|counterfactual|attribut)/.test(text) && /(impact|outcome|effect)/.test(text)) return 'impact';
  if (/(improved|increased|decreased|reduced|changed|outcome|test scores|health|income|wellbeing|well-being)/.test(text) && (hasNumber || /survey|study|evaluation|research/.test(text))) return 'outcome';
  if (/(kpi|indicator|metric|measure|measurement|rate|percent|percentage|baseline|target)/.test(text)) return 'indicator';
  if (/(recipient|household|participant|people reached|operates in|countries|transfer sizes|attended|served|reached)/.test(text)) return 'output';
  if (/(provides|offers|identifies|informs|helps|register|sends|follows up|deliver|conducts|runs|program|programme|service)/.test(text)) return 'activity';
  return 'unknown';
}
return items.map(item => {
  if (item.json.controlled_state !== 'impact_evidence_available') return item;
  const classified = (item.json.impact_evidence || []).map(ev => ({
    ...ev,
    impact_classification: {
      level: levelFor(ev.claim),
      signal_nature: levelFor(ev.claim) === 'impact_claim' ? 'claim' : 'evidence_signal',
      taxonomy_version: 'impact-taxonomy-v1'
    }
  }));
  return { json: { ...item.json, impact_evidence: classified } };
});
"""


JS_ASSESS_CHARACTERISTICS = r"""
function sourceFor(ev, sources) {
  return sources.find(source => (ev.source_ids || []).includes(source.source_id)) || {};
}
function present(pattern, text) {
  return pattern.test(String(text || '').toLowerCase());
}
return items.map(item => {
  if (item.json.controlled_state !== 'impact_evidence_available') return item;
  const evidenceCharacteristics = (item.json.impact_evidence || []).map(ev => {
    const source = sourceFor(ev, item.json.sources || []);
    const claim = String(ev.claim || '');
    const measurementPresence = /\b\d+([,.]\d+)?%?\b/.test(claim);
    return {
      evidence_id: ev.evidence_id,
      impact_level: ev.impact_classification.level,
      source_authority: source.authority_level || 'unknown',
      specificity: measurementPresence || claim.length > 120 ? 'medium' : 'low',
      measurement_presence: measurementPresence,
      timeframe_visibility: present(/\b(20\d{2}|19\d{2}|year|month|quarter|five years|long[- ]term)\b/, claim),
      methodology_visibility: present(/\b(method|survey|study|evaluation|research|random|sample|baseline|follow[- ]up)\b/, claim),
      denominator_sample_visibility: present(/\b(sample|n=|participants|households|recipients)\b/, claim) && measurementPresence,
      baseline_visibility: present(/\bbaseline\b/, claim),
      target_visibility: present(/\btarget\b/, claim),
      attribution_limitations: ev.impact_classification.level === 'impact' || ev.impact_classification.level === 'outcome'
        ? 'Attribution cannot be assessed beyond what the cited public evidence states.'
        : null
    };
  });
  return { json: { ...item.json, evidence_characteristics: evidenceCharacteristics } };
});
"""


JS_DETECT_UNKNOWNS = r"""
return items.map(item => {
  const ids = (item.json.impact_evidence || []).map(ev => ev.evidence_id);
  if (item.json.controlled_state !== 'impact_evidence_available') {
    return {
      json: {
        ...item.json,
        unknowns: [{
          unknown_id: 'UNK-IMP-001',
          domain: 'impact_evidence',
          description: 'Impact-related public evidence was not identified in the structured inputs reviewed.',
          evidence_ids: ids
        }]
      }
    };
  }
  const levels = new Set((item.json.impact_evidence || []).map(ev => ev.impact_classification.level));
  const characteristics = item.json.evidence_characteristics || [];
  const unknowns = [];
  if (!levels.has('outcome')) unknowns.push('Outcome evidence was not identified in the public sources reviewed.');
  if (!levels.has('impact')) unknowns.push('Long-term impact evidence was not identified in the public sources reviewed.');
  if (!characteristics.some(c => c.methodology_visibility)) unknowns.push('Methodology visibility could not be determined from the public evidence reviewed.');
  if (!characteristics.some(c => c.baseline_visibility)) unknowns.push('Baseline visibility could not be determined from the public evidence reviewed.');
  if (!characteristics.some(c => c.denominator_sample_visibility)) unknowns.push('Denominator or sample visibility could not be determined from the public evidence reviewed.');
  if (!characteristics.some(c => c.target_visibility)) unknowns.push('Target visibility could not be determined from the public evidence reviewed.');
  return {
    json: {
      ...item.json,
      unknowns: unknowns.map((description, index) => ({
        unknown_id: `UNK-IMP-${String(index + 1).padStart(3, '0')}`,
        domain: 'impact_evidence',
        description,
        evidence_ids: ids
      }))
    }
  };
});
"""


JS_BUILD_FINDINGS = r"""
function avg(values) {
  if (!values.length) return 0.35;
  return Math.round((values.reduce((sum, value) => sum + value, 0) / values.length) * 100) / 100;
}
function evidenceIdsFor(evidence, levels) {
  return evidence.filter(ev => levels.includes(ev.impact_classification?.level)).map(ev => ev.evidence_id);
}
return items.map(item => {
  const evidence = item.json.impact_evidence || [];
  if (item.json.controlled_state === 'request_failure') return item;
  if (!evidence.length) {
    return {
      json: {
        ...item.json,
        controlled_state: 'insufficient_evidence',
        findings: [{
          finding_id: 'F-IMP-001',
          domain: 'impact_evidence',
          finding: 'Structured inputs did not contain enough impact-related public evidence to support meaningful impact findings.',
          evidence_ids: [],
          finding_type: 'unknown',
          confidence: 0.35,
          requires_validation: true,
          validation_question: 'Which public sources should be reviewed to understand activities, outputs, outcomes, and impact claims?'
        }]
      }
    };
  }
  const findings = [];
  const activityIds = evidenceIdsFor(evidence, ['activity']);
  const outputIds = evidenceIdsFor(evidence, ['output', 'indicator']);
  const claimIds = evidenceIdsFor(evidence, ['impact_claim']);
  const outcomeIds = evidenceIdsFor(evidence, ['outcome']);
  const impactIds = evidenceIdsFor(evidence, ['impact']);
  if (activityIds.length) findings.push({
    finding_id: `F-IMP-${String(findings.length + 1).padStart(3, '0')}`,
    domain: 'impact_evidence',
    finding: 'Program activities or service delivery steps are publicly described in the reviewed sources.',
    evidence_ids: activityIds,
    finding_type: 'observed',
    confidence: avg(evidence.filter(ev => activityIds.includes(ev.evidence_id)).map(ev => ev.confidence || 0.5)),
    requires_validation: false,
    validation_question: null
  });
  if (outputIds.length) findings.push({
    finding_id: `F-IMP-${String(findings.length + 1).padStart(3, '0')}`,
    domain: 'impact_evidence',
    finding: 'Public reporting reviewed contains output or reach signals.',
    evidence_ids: outputIds,
    finding_type: 'observed',
    confidence: avg(evidence.filter(ev => outputIds.includes(ev.evidence_id)).map(ev => ev.confidence || 0.5)),
    requires_validation: false,
    validation_question: null
  });
  if (claimIds.length) findings.push({
    finding_id: `F-IMP-${String(findings.length + 1).padStart(3, '0')}`,
    domain: 'impact_evidence',
    finding: 'An impact-oriented claim or mission statement is publicly stated, but it is not treated as proof that long-term impact occurred.',
    evidence_ids: claimIds,
    finding_type: 'observed',
    confidence: avg(evidence.filter(ev => claimIds.includes(ev.evidence_id)).map(ev => ev.confidence || 0.5)),
    requires_validation: true,
    validation_question: 'What outcome or longitudinal evidence supports this public impact claim?'
  });
  if (outcomeIds.length) findings.push({
    finding_id: `F-IMP-${String(findings.length + 1).padStart(3, '0')}`,
    domain: 'impact_evidence',
    finding: 'Outcome evidence is publicly reported in the reviewed sources.',
    evidence_ids: outcomeIds,
    finding_type: 'observed',
    confidence: avg(evidence.filter(ev => outcomeIds.includes(ev.evidence_id)).map(ev => ev.confidence || 0.5)),
    requires_validation: false,
    validation_question: null
  });
  if (impactIds.length) findings.push({
    finding_id: `F-IMP-${String(findings.length + 1).padStart(3, '0')}`,
    domain: 'impact_evidence',
    finding: 'Long-term impact evidence is publicly reported in the reviewed sources.',
    evidence_ids: impactIds,
    finding_type: 'observed',
    confidence: avg(evidence.filter(ev => impactIds.includes(ev.evidence_id)).map(ev => ev.confidence || 0.5)),
    requires_validation: true,
    validation_question: 'How should attribution limitations be interpreted for the long-term impact evidence?'
  });
  const outcomeImpactCount = outcomeIds.length + impactIds.length;
  if (activityIds.length + outputIds.length > outcomeImpactCount && outcomeImpactCount === 0) findings.push({
    finding_id: `F-IMP-${String(findings.length + 1).padStart(3, '0')}`,
    domain: 'impact_evidence',
    finding: 'Public reporting reviewed emphasizes activities, outputs, or claims more clearly than measured outcomes or long-term impact evidence.',
    evidence_ids: evidence.map(ev => ev.evidence_id),
    finding_type: 'inferred',
    confidence: 0.56,
    requires_validation: true,
    validation_question: 'Are measured outcomes or long-term follow-up results available outside the public sources reviewed?'
  });
  if (item.json.unknowns?.length) findings.push({
    finding_id: `F-IMP-${String(findings.length + 1).padStart(3, '0')}`,
    domain: 'impact_evidence',
    finding: 'Some impact evidence characteristics remain unknown from the public sources reviewed.',
    evidence_ids: evidence.map(ev => ev.evidence_id),
    finding_type: 'unknown',
    confidence: 0.5,
    requires_validation: true,
    validation_question: 'Which measurement details, if any, can the organization validate directly?'
  });
  return { json: { ...item.json, controlled_state: 'success', findings } };
});
"""


JS_TRACEABILITY_CHECK = r"""
return items.map(item => {
  if (item.json.controlled_state === 'request_failure') return item;
  const evidenceIds = new Set((item.json.impact_evidence || []).map(ev => ev.evidence_id));
  const sourceIds = new Set((item.json.sources || []).map(source => source.source_id));
  const errors = [...(item.json.errors || [])];
  for (const ev of item.json.impact_evidence || []) {
    if (!(ev.source_ids || []).some(id => sourceIds.has(id))) {
      errors.push({ stage: 'TRACEABILITY_CHECK', error_type: 'untraceable_evidence', message: `${ev.evidence_id} does not reference a known source` });
    }
  }
  const findings = (item.json.findings || []).map(finding => ({
    ...finding,
    evidence_ids: (finding.evidence_ids || []).filter(id => evidenceIds.has(id))
  }));
  for (const finding of findings) {
    if (finding.finding_type !== 'unknown' && !finding.evidence_ids.length) {
      errors.push({ stage: 'TRACEABILITY_CHECK', error_type: 'untraceable_finding', message: `${finding.finding_id} has no valid evidence references` });
    }
  }
  const controlledState = errors.length ? 'request_failure' : item.json.controlled_state;
  return { json: { ...item.json, findings, errors, controlled_state: controlledState } };
});
"""


JS_OUTPUT = r"""
return items.map(item => ({ json: {
  run_context: item.json.run_context || null,
  controlled_state: item.json.controlled_state,
  impact_taxonomy: item.json.impact_taxonomy || [],
  sources: item.json.sources || [],
  evidence: item.json.evidence || [],
  impact_evidence: item.json.impact_evidence || [],
  evidence_characteristics: item.json.evidence_characteristics || [],
  findings: item.json.findings || [],
  unknowns: item.json.unknowns || [],
  contradictions: item.json.contradictions || [],
  rag_metadata: {
    retrieval_run_id: item.json.rag_context?.retrieval_run_id || null,
    domains: item.json.rag_context?.domain ? [item.json.rag_context.domain] : [],
    retrieved_context_ids: (item.json.rag_context?.contexts || []).map(ctx => ctx.context_id)
  },
  guardrails: [
    'Activity, output, outcome, impact, indicator, and unknown are not interchangeable.',
    'Absence of public evidence is not treated as evidence of organizational absence.',
    'RAG context cannot add organization-specific facts.'
  ],
  errors: item.json.errors || []
} }));
"""


JS_DEV_GIVEDIRECTLY = r"""
return [{ json: {
  run_context: {
    run_id: 'RUN-N8N-52-GIVEDIRECTLY',
    organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States', mission_area: null },
    current_challenge: null,
    uploaded_document_refs: [],
    status: 'created',
    started_at: new Date().toISOString(),
    errors: []
  },
  sources: [{
    source_id: 'SRC-DOC-001',
    title: 'GiveDirectly FY2023 audited financial statements',
    url: 'https://www.givedirectly.org/wp-content/uploads/2024/11/FY2023-GiveDirectly-Audit-Final-FS-Public-Disclosure.pdf',
    source_type: 'public_document_audited_financial_statement',
    publisher: 'GiveDirectly',
    publication_date: null,
    retrieved_at: new Date().toISOString(),
    authority_level: 'official',
    freshness: 'unknown',
    is_official: true
  }],
  documents: [{
    document_id: 'DOC-001',
    source_id: 'SRC-DOC-001',
    document_type: 'audited_financial_statement',
    is_official: true,
    sections: [{
      section_type: 'impact',
      text: 'GiveDirectly mission is to reduce poverty by providing financial assistance directly to those in need. GiveDirectly offers a service that enables others to send cash transfers directly to people in need. GiveDirectly operates in the United States, Kenya, Uganda, Rwanda, Liberia, Malawi, Mozambique, the Democratic Republic of the Congo, Nigeria, Yemen, Bangladesh, Morocco, and the United Kingdom. GiveDirectly identifies households, informs them that they are eligible for a transfer, helps them register for a digital payments system, sends funds, and follows up with recipients post-transfer.'
    }]
  }],
  evidence: [],
  rag_context: {
    retrieval_run_id: 'RAG-52-FRAMEWORK-001',
    domain: 'impact_evidence',
    contexts: [{
      context_id: 'FRAMEWORK-IMPACT-001',
      domain: 'impact_evidence',
      title: 'Impact evidence taxonomy',
      content: 'Activities, outputs, outcomes, and impact are distinct. Public claims are not proof of long-term impact.'
    }]
  }
} }];
"""


JS_DEV_INSUFFICIENT = r"""
return [{ json: {
  run_context: {
    run_id: 'RUN-N8N-52-INSUFFICIENT',
    organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States', mission_area: null },
    current_challenge: null,
    uploaded_document_refs: [],
    status: 'created',
    started_at: new Date().toISOString(),
    errors: []
  },
  sources: [{
    source_id: 'SRC-001',
    title: 'Financials page search result',
    url: 'https://www.givedirectly.org/financials',
    source_type: 'registry',
    publisher: 'GiveDirectly',
    publication_date: null,
    retrieved_at: new Date().toISOString(),
    authority_level: 'official',
    freshness: 'unknown',
    is_official: true
  }],
  evidence: [{
    evidence_id: 'EV-001',
    run_id: 'RUN-N8N-52-INSUFFICIENT',
    claim: 'Public source contains revenue-resilience search signals: financial.',
    source_ids: ['SRC-001'],
    domain: 'revenue_resilience',
    evidence_type: 'fact',
    confidence: 0.68,
    status: 'supported',
    contradiction_ids: [],
    requires_validation: false
  }],
  documents: [],
  rag_context: { retrieval_run_id: 'RAG-52-FRAMEWORK-001', domain: 'impact_evidence', contexts: [] }
} }];
"""


def build_workflow():
    nodes = [
        sticky(
            "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
            "PURPOSE\nAnalyze public evidence about activities, outputs, outcomes, impact claims, indicators, evidence strength, and unknowns.\n\nOWNER\nPAOLA TRACK A\n\nINPUT CONTRACT\nrun_context + sources + evidence + optional structured documents + optional RAG context\n\nOUTPUT CONTRACT\nfinding.schema.json[] plus traceable impact_evidence and unknowns\n\nSTATUS\nRepository-ready deterministic implementation. No broad web search. No credentials. Inactive by default.",
            -620,
            -520,
            700,
            420,
            4,
        ),
        sticky(
            "NOTE__IMPACT_BOUNDARIES",
            "ACTIVITY != OUTPUT != OUTCOME != IMPACT\nA public claim is not automatically proof. Missing public evidence remains unknown, not a negative conclusion. RAG may provide conceptual framing only; it must not add organization facts.",
            -620,
            -40,
            700,
            280,
            6,
        ),
        {
            "parameters": {},
            "id": "start__sub_workflow_trigger",
            "name": "START__SUB_WORKFLOW_TRIGGER",
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1,
            "position": [0, 0],
        },
        code_node("INPUT_CONTRACT", JS_INPUT_CONTRACT, 260, 0),
        if_node("DECISION__INPUT_FAILURE", "controlled_state", "request_failure", 540, 0),
        code_node("OUTPUT_REQUEST_FAILURE", JS_OUTPUT, 820, -220),
        code_node("FILTER_IMPACT_EVIDENCE", JS_FILTER_IMPACT_EVIDENCE, 820, 120),
        if_node("DECISION__INSUFFICIENT_EVIDENCE", "controlled_state", "insufficient_evidence", 1100, 120),
        code_node("DETECT_UNKNOWNS__INSUFFICIENT", JS_DETECT_UNKNOWNS, 1380, -80),
        code_node("BUILD_FINDINGS__INSUFFICIENT", JS_BUILD_FINDINGS, 1660, -80),
        code_node("TRACEABILITY_CHECK__INSUFFICIENT", JS_TRACEABILITY_CHECK, 1940, -80),
        code_node("OUTPUT_INSUFFICIENT_EVIDENCE", JS_OUTPUT, 2220, -80),
        code_node("CLASSIFY_IMPACT_LEVEL", JS_CLASSIFY_IMPACT_LEVEL, 1380, 260),
        code_node("ASSESS_EVIDENCE_CHARACTERISTICS", JS_ASSESS_CHARACTERISTICS, 1660, 260),
        code_node("DETECT_UNKNOWNS", JS_DETECT_UNKNOWNS, 1940, 260),
        code_node("BUILD_FINDINGS", JS_BUILD_FINDINGS, 2220, 260),
        code_node("TRACEABILITY_CHECK", JS_TRACEABILITY_CHECK, 2500, 260),
        if_node("DECISION__TRACEABILITY_FAILURE", "controlled_state", "request_failure", 2780, 260),
        code_node("OUTPUT_TRACEABILITY_FAILURE", JS_OUTPUT, 3060, 80),
        code_node("OUTPUT_CONTRACT__IMPACT_FINDINGS", JS_OUTPUT, 3060, 420),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT"),
        ("INPUT_CONTRACT", "DECISION__INPUT_FAILURE"),
        ("DECISION__INPUT_FAILURE", "OUTPUT_REQUEST_FAILURE", 0),
        ("DECISION__INPUT_FAILURE", "FILTER_IMPACT_EVIDENCE", 1),
        ("FILTER_IMPACT_EVIDENCE", "DECISION__INSUFFICIENT_EVIDENCE"),
        ("DECISION__INSUFFICIENT_EVIDENCE", "DETECT_UNKNOWNS__INSUFFICIENT", 0),
        ("DETECT_UNKNOWNS__INSUFFICIENT", "BUILD_FINDINGS__INSUFFICIENT"),
        ("BUILD_FINDINGS__INSUFFICIENT", "TRACEABILITY_CHECK__INSUFFICIENT"),
        ("TRACEABILITY_CHECK__INSUFFICIENT", "OUTPUT_INSUFFICIENT_EVIDENCE"),
        ("DECISION__INSUFFICIENT_EVIDENCE", "CLASSIFY_IMPACT_LEVEL", 1),
        ("CLASSIFY_IMPACT_LEVEL", "ASSESS_EVIDENCE_CHARACTERISTICS"),
        ("ASSESS_EVIDENCE_CHARACTERISTICS", "DETECT_UNKNOWNS"),
        ("DETECT_UNKNOWNS", "BUILD_FINDINGS"),
        ("BUILD_FINDINGS", "TRACEABILITY_CHECK"),
        ("TRACEABILITY_CHECK", "DECISION__TRACEABILITY_FAILURE"),
        ("DECISION__TRACEABILITY_FAILURE", "OUTPUT_TRACEABILITY_FAILURE", 0),
        ("DECISION__TRACEABILITY_FAILURE", "OUTPUT_CONTRACT__IMPACT_FINDINGS", 1),
    ]
    return {
        "name": "52_IMPACT_EVIDENCE_AGENT",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def build_dev_workflow():
    branches = [
        ("GIVEDIRECTLY", JS_DEV_GIVEDIRECTLY, -120, "FINAL_GIVEDIRECTLY_IMPACT_EVIDENCE"),
        ("INSUFFICIENT", JS_DEV_INSUFFICIENT, 220, "FINAL_INSUFFICIENT_EVIDENCE"),
    ]
    nodes = [
        sticky(
            "00_README__DEV_WORKFLOW",
            "DEV_PAOLA_52_IMPACT_EVIDENCE_TEST\nRuns two visible branches against stored workflow 52:\n1) GiveDirectly structured document evidence path\n2) insufficient-evidence path\n\nAfter import, link every Execute Sub-workflow node to the real stored workflow 52 using the n8n database selector.",
            -520,
            -460,
            680,
            360,
            4,
        ),
        {
            "parameters": {},
            "id": "start__manual_test_trigger",
            "name": "START__MANUAL_TEST_TRIGGER",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [0, 80],
        },
    ]
    edges = []
    for label, js_code, y, final_name in branches:
        input_name = f"DEV_INPUT__{label}"
        execute_name = f"EXECUTE_SUBWORKFLOW__52_{label}"
        nodes.extend(
            [
                code_node(input_name, js_code, 300, y),
                execute_subworkflow_node(execute_name, 640, y),
                code_node(final_name, "return items;", 980, y),
            ]
        )
        edges.extend(
            [
                ("START__MANUAL_TEST_TRIGGER", input_name),
                (input_name, execute_name),
                (execute_name, final_name),
            ]
        )
    return {
        "name": "DEV_PAOLA_52_IMPACT_EVIDENCE_TEST",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure_paola_52_workflows(root=ROOT):
    root = Path(root)
    workflow_path = root / "workflows" / "skeletons" / "52_IMPACT_EVIDENCE_AGENT.json"
    dev_path = root / "workflows" / "dev" / "DEV_PAOLA_52_IMPACT_EVIDENCE_TEST.json"
    dev_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(json.dumps(build_workflow(), indent=2) + "\n", encoding="utf-8")
    dev_path.write_text(json.dumps(build_dev_workflow(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    configure_paola_52_workflows()
    print("Configured Paola 52 impact evidence n8n exports.")
