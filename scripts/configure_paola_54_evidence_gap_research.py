import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=640, height=320, color=4):
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


def execute_subworkflow_node(name, target_name, x, y):
    return {
        "parameters": {
            "source": "database",
            "workflowId": {
                "__rl": True,
                "value": "",
                "mode": "list",
                "cachedResultName": target_name,
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
        "notes": f"AFTER IMPORT: select the stored n8n workflow {target_name}. Never invent an ID.",
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
function toInt(value, fallback) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : fallback;
}
function normalizeRequest(value) {
  const request = value || {};
  const retryCount = toInt(request.retry_count, 0);
  const maxRetries = toInt(request.max_retries, 1);
  return {
    gap_id: request.gap_id || null,
    domain: request.domain || null,
    question: request.question || request.description || null,
    description: request.description || request.question || null,
    gap_type: request.gap_type || 'unspecified',
    current_evidence_ids: Array.isArray(request.current_evidence_ids) ? request.current_evidence_ids : [],
    retry_count: retryCount,
    max_retries: maxRetries,
    reason_for_retry: request.reason_for_retry || null
  };
}
return items.map(item => {
  const payload = item.json || {};
  const nested = payload.paola_track_output || payload;
  const runContext = nested.run_context || payload.run_context || {};
  const sources = Array.isArray(nested.sources) ? nested.sources : [];
  const evidence = Array.isArray(nested.evidence) ? nested.evidence : [];
  const request = normalizeRequest(payload.missing_evidence_request || nested.missing_evidence_request);
  const errors = [];
  if (!runContext.run_id) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'run_context.run_id is required' });
  if (!runContext.organization?.name || !runContext.organization?.website || !runContext.organization?.country) {
    errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'run_context.organization name, website, and country are required' });
  }
  if (!request.gap_id) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'missing_evidence_request.gap_id is required' });
  if (!request.domain) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'missing_evidence_request.domain is required' });
  if (!request.question) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'missing_evidence_request.question or description is required' });
  if (request.max_retries < 0 || request.retry_count < 0) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'retry_count and max_retries must be non-negative integers' });
  if (!request.reason_for_retry) errors.push({ stage: 'INPUT_CONTRACT', error_type: 'invalid_input', message: 'reason_for_retry is required' });
  const controlledState = errors.length ? 'invalid_input' : (request.retry_count >= request.max_retries ? 'retry_exhausted' : 'ready');
  return {
    json: {
      run_context: runContext,
      sources,
      evidence,
      missing_evidence_request: request,
      controlled_state: controlledState,
      retry_count: request.retry_count,
      max_retries: request.max_retries,
      reason_for_retry: request.reason_for_retry,
      research_attempted: false,
      new_sources: [],
      new_evidence: [],
      requires_client_validation: false,
      rerun_required: false,
      rerun_domain: null,
      errors
    }
  };
});
"""


JS_MARK_UNKNOWN = r"""
return items.map(item => {
  const request = item.json.missing_evidence_request || {};
  return {
    json: {
      ...item.json,
      controlled_state: item.json.controlled_state || 'unknown_preserved',
      unknown_marker: {
        unknown_id: request.gap_id || 'GAP-UNKNOWN',
        domain: request.domain || null,
        description: 'The evidence gap remains unresolved from the public sources reviewed.',
        reason: item.json.reason_for_preserving_unknown || 'Public research cannot reasonably answer this gap.',
        evidence_ids: request.current_evidence_ids || []
      },
      requires_client_validation: true,
      rerun_required: false,
      rerun_domain: null,
      new_sources: item.json.new_sources || [],
      new_evidence: []
    }
  };
});
"""


JS_PUBLIC_ANSWERABILITY = r"""
const publicSignals = [
  'annual report', 'audited', 'financial statements', 'financial report', 'form 990', '990',
  'funding', 'funder', 'grant', 'donor', 'revenue', 'public report', 'impact report',
  'methodology', 'evaluation', 'outcome', 'indicator', 'kpi', 'partnership', 'strategy',
  'program reach', 'people reached', 'published', 'publicly reported'
];
const privateSignals = [
  'internal', 'handoff', 'handoffs', 'crm', 'staff workload', 'response time',
  'unpublished', 'beneficiary-level private', 'private data', 'team sentiment',
  'process friction', 'after a stakeholder submits', 'after someone submits',
  'workflow ownership', 'internal workflow', 'configuration'
];
return items.map(item => {
  if (item.json.controlled_state !== 'ready') return item;
  const request = item.json.missing_evidence_request;
  const text = `${request.domain || ''} ${request.gap_type || ''} ${request.question || ''} ${request.description || ''}`.toLowerCase();
  const privateMatch = privateSignals.find(signal => text.includes(signal));
  const publicMatch = publicSignals.find(signal => text.includes(signal));
  const answerable = Boolean(publicMatch && !privateMatch);
  return {
    json: {
      ...item.json,
      can_public_research_answer: answerable,
      answerability_state: answerable ? 'public_answerable' : 'unknown_preserved',
      answerability_reason: answerable
        ? `Gap contains public research signal: ${publicMatch}`
        : (privateMatch ? `Gap appears private/internal: ${privateMatch}` : 'No reliable public research path identified'),
      reason_for_preserving_unknown: answerable ? null : 'Public research cannot reasonably answer this specific evidence gap.'
    }
  };
});
"""


JS_BUILD_TARGETED_QUERY = r"""
function compact(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}
function uniqueWords(parts) {
  const out = [];
  const seen = new Set();
  for (const part of parts) {
    for (const token of compact(part).split(' ')) {
      const clean = token.replace(/[^\w.-]/g, '');
      const key = clean.toLowerCase();
      if (!clean || seen.has(key)) continue;
      seen.add(key);
      out.push(clean);
    }
  }
  return out.join(' ');
}
return items.map(item => {
  const org = item.json.run_context.organization || {};
  const request = item.json.missing_evidence_request;
  const text = `${request.gap_type || ''} ${request.question || ''} ${request.description || ''}`.toLowerCase();
  let hints = 'public report source';
  if (/fund|grant|donor|revenue|financial|990|audited|audit/.test(text)) hints = 'audited financial statements funding concentration annual report form 990';
  else if (/impact|outcome|methodolog|evaluation|longitudinal|indicator|kpi/.test(text)) hints = 'impact report outcome evaluation methodology longitudinal study indicators';
  else if (/partner|partnership/.test(text)) hints = 'public partnership announcement annual report';
  else if (/strategy|strategic/.test(text)) hints = 'strategy document strategic plan annual report';
  else if (/program|reach|people served|people reached/.test(text)) hints = 'program reach annual report public results';
  const targetedQuery = uniqueWords([org.name, org.country, request.question, request.gap_type, hints]);
  return {
    json: {
      ...item.json,
      targeted_query: targetedQuery,
      query_strategy: {
        organization_identity: org.name,
        gap_subject: request.question,
        source_hint: hints
      }
    }
  };
});
"""


JS_PREPARE_21 = r"""
return items.map(item => ({
  json: {
    ...item.json,
    retry_count_before_attempt: item.json.retry_count,
    retry_count: item.json.retry_count + 1,
    missing_evidence_request: {
      ...item.json.missing_evidence_request,
      retry_count: item.json.retry_count + 1
    },
    research_attempted: true,
    query: item.json.targeted_query
  }
}));
"""


JS_VALIDATE_SEARCH = r"""
function normalizeUrl(value) {
  try {
    const url = new URL(String(value || '').trim());
    url.hash = '';
    url.search = '';
    return url.toString().replace(/\/$/, '').toLowerCase();
  } catch {
    return '';
  }
}
function host(value) {
  const match = String(value || '').match(/^https?:\/\/([^\/?#]+)/i);
  return match ? match[1].replace(/^www\./, '').toLowerCase() : '';
}
function tokens(value) {
  return String(value || '').toLowerCase().match(/[a-z0-9]+/g) || [];
}
function gapTerms(request) {
  const text = `${request.domain || ''} ${request.gap_type || ''} ${request.question || ''} ${request.description || ''}`.toLowerCase();
  const terms = ['annual','report','financial','funding','grant','donor','revenue','990','audit','audited','impact','outcome','evaluation','methodology','indicator','strategy','partnership','program','reach'];
  return terms.filter(term => text.includes(term));
}
return items.map((item, index) => {
  const baseItems = $items('PREPARE_21_SEARCH_REQUEST', 0);
  const base = baseItems[index]?.json || item.json;
  const returnedState = item.json.controlled_state || 'unknown';
  const returnedErrors = item.json.errors || [];
  const existingUrls = new Set((base.sources || []).map(source => normalizeUrl(source.url)).filter(Boolean));
  const officialDomain = host(base.run_context?.organization?.website);
  const orgTokens = tokens(base.run_context?.organization?.name).filter(token => token.length > 2);
  const terms = gapTerms(base.missing_evidence_request);
  const newSources = [];
  const rejected_sources = [];
  if (returnedState === 'request_failure') {
    return {
      json: {
        ...base,
        controlled_state: 'research_failure',
        search_controlled_state: returnedState,
        errors: [...(base.errors || []), ...returnedErrors, { stage: 'TARGETED_RESEARCH', error_type: 'research_failure', message: 'Workflow 21 returned request_failure' }]
      }
    };
  }
  for (const source of item.json.sources || []) {
    const normalized = normalizeUrl(source.url);
    const sourceText = `${source.title || ''} ${source.url || ''} ${source.search_snippet || ''}`.toLowerCase();
    const sourceHost = host(source.url);
    const validUrl = Boolean(normalized);
    const duplicate = validUrl && existingUrls.has(normalized);
    const orgRelevant = Boolean((officialDomain && sourceHost.endsWith(officialDomain)) || orgTokens.some(token => sourceText.includes(token)));
    const gapRelevant = terms.length ? terms.some(term => sourceText.includes(term)) : false;
    if (!validUrl || duplicate || !orgRelevant || !gapRelevant) {
      rejected_sources.push({
        title: source.title || null,
        url: source.url || null,
        reason: !validUrl ? 'invalid_url' : duplicate ? 'duplicate_existing_source' : !orgRelevant ? 'organization_mismatch' : 'gap_mismatch'
      });
      continue;
    }
    newSources.push({
      ...source,
      source_id: `SRC-GAP-${String(newSources.length + 1).padStart(3, '0')}`,
      original_source_id: source.source_id || null,
      discovered_by: '54_EVIDENCE_GAP_RESEARCH',
      targeted_gap_id: base.missing_evidence_request.gap_id,
      targeted_query: base.targeted_query,
      source_validation: {
        is_new_to_run: true,
        organization_relevant: orgRelevant,
        gap_relevant: gapRelevant,
        source_vs_evidence_note: 'New source found; downstream extraction/evidence processing is required before treating the gap as resolved.'
      }
    });
    if (newSources.length >= 5) break;
  }
  const controlledState = newSources.length ? 'new_source_found' : 'no_new_evidence';
  return {
    json: {
      ...base,
      controlled_state: controlledState,
      search_controlled_state: returnedState,
      new_sources: newSources,
      new_evidence: [],
      rejected_sources,
      unknown_marker: newSources.length ? null : {
        unknown_id: base.missing_evidence_request.gap_id,
        domain: base.missing_evidence_request.domain,
        description: 'The evidence gap remains unresolved from the public sources reviewed.',
        evidence_ids: base.missing_evidence_request.current_evidence_ids || []
      },
      requires_client_validation: !newSources.length,
      rerun_required: Boolean(newSources.length),
      rerun_domain: newSources.length ? base.missing_evidence_request.domain : null
    }
  };
});
"""


JS_OUTPUT = r"""
return items.map(item => ({ json: {
  run_context: item.json.run_context || null,
  missing_evidence_request: item.json.missing_evidence_request || null,
  controlled_state: item.json.controlled_state,
  can_public_research_answer: Boolean(item.json.can_public_research_answer),
  answerability_reason: item.json.answerability_reason || null,
  targeted_query: item.json.targeted_query || null,
  query_strategy: item.json.query_strategy || null,
  search_controlled_state: item.json.search_controlled_state || null,
  new_sources: item.json.new_sources || [],
  new_evidence: item.json.new_evidence || [],
  rejected_sources: item.json.rejected_sources || [],
  unknown_marker: item.json.unknown_marker || null,
  retry_count: item.json.retry_count,
  max_retries: item.json.max_retries,
  reason_for_retry: item.json.reason_for_retry || null,
  research_attempted: Boolean(item.json.research_attempted),
  rerun_required: Boolean(item.json.rerun_required),
  rerun_domain: item.json.rerun_domain || null,
  requires_client_validation: Boolean(item.json.requires_client_validation),
  source_evidence_boundary: 'A new source is not treated as gap-resolving evidence until downstream extraction/evidence processing validates attributable facts.',
  errors: item.json.errors || []
} }));
"""


JS_DEV_ANSWERABLE = r"""
return [{ json: {
  run_context: {
    run_id: 'RUN-N8N-54-GIVEDIRECTLY-ANSWERABLE',
    organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States', mission_area: null },
    current_challenge: 'Resolve a public financial evidence gap',
    uploaded_document_refs: [],
    status: 'created',
    started_at: new Date().toISOString(),
    errors: []
  },
  sources: [{
    source_id: 'SRC-WEB-001',
    title: 'GiveDirectly home page',
    url: 'https://www.givedirectly.org/',
    source_type: 'official_website_home',
    publisher: 'GiveDirectly',
    publication_date: null,
    retrieved_at: new Date().toISOString(),
    authority_level: 'official',
    freshness: 'unknown',
    is_official: true
  }],
  evidence: [],
  missing_evidence_request: {
    gap_id: 'GAP-REV-001',
    domain: 'revenue_resilience',
    question: 'Can funding concentration be determined from additional public financial information?',
    gap_type: 'public_financial_information',
    current_evidence_ids: [],
    retry_count: 0,
    max_retries: 1,
    reason_for_retry: 'Existing evidence does not show funding concentration.'
  }
} }];
"""


JS_DEV_INTERNAL = r"""
return [{ json: {
  run_context: {
    run_id: 'RUN-N8N-54-INTERNAL-GAP',
    organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States', mission_area: null },
    current_challenge: 'Preserve an internal process unknown',
    uploaded_document_refs: [],
    status: 'created',
    started_at: new Date().toISOString(),
    errors: []
  },
  sources: [],
  evidence: [],
  missing_evidence_request: {
    gap_id: 'GAP-OPS-001',
    domain: 'operations_cx',
    question: 'What happens internally after a stakeholder submits an application form?',
    gap_type: 'internal_handoff',
    current_evidence_ids: [],
    retry_count: 0,
    max_retries: 1,
    reason_for_retry: 'Public sources do not describe the internal follow-up process.'
  }
} }];
"""


JS_DEV_RETRY = r"""
return [{ json: {
  run_context: {
    run_id: 'RUN-N8N-54-RETRY-EXHAUSTED',
    organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States', mission_area: null },
    current_challenge: 'Stop after retry limit',
    uploaded_document_refs: [],
    status: 'created',
    started_at: new Date().toISOString(),
    errors: []
  },
  sources: [],
  evidence: [],
  missing_evidence_request: {
    gap_id: 'GAP-REV-RETRY',
    domain: 'revenue_resilience',
    question: 'Can funding concentration be determined from additional public financial information?',
    gap_type: 'public_financial_information',
    current_evidence_ids: [],
    retry_count: 1,
    max_retries: 1,
    reason_for_retry: 'Existing evidence does not show funding concentration.'
  }
} }];
"""


def build_workflow():
    nodes = [
        sticky(
            "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
            "PURPOSE\nResolve a specific UNKNOWN only when additional public research can reasonably help.\n\nOWNER\nPAOLA TRACK A\n\nINPUT CONTRACT\nrun_context + sources + evidence + missing_evidence_request with retry_count, max_retries, reason_for_retry\n\nOUTPUT CONTRACT\nworkflow-local targeted result: new_sources OR preserved unknown. No competing shared schema.\n\nSTATUS\nRepository-ready controller. Reuses workflow 21 through Execute Sub-workflow. Inactive by default.",
            -660,
            -560,
            760,
            430,
            4,
        ),
        sticky(
            "NOTE__EVIDENCE_GAP_BOUNDARIES",
            "UNKNOWN -> can public research answer? -> targeted research or client validation.\n\nA new URL is not automatically evidence. If research finds nothing, preserve UNKNOWN. Absence of public evidence is not evidence of absence.",
            -660,
            -80,
            760,
            300,
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
        code_node("INPUT_CONTRACT__MISSING_EVIDENCE_REQUEST", JS_INPUT_CONTRACT, 280, 0),
        if_node("DECISION__INVALID_INPUT", "controlled_state", "invalid_input", 560, 0),
        code_node("OUTPUT_INVALID_INPUT", JS_OUTPUT, 840, -360),
        if_node("DECISION__RETRY_EXHAUSTED", "controlled_state", "retry_exhausted", 840, 40),
        code_node("MARK_UNKNOWN__RETRY_EXHAUSTED", JS_MARK_UNKNOWN, 1120, -180),
        code_node("OUTPUT_RETRY_EXHAUSTED", JS_OUTPUT, 1400, -180),
        code_node("CAN_PUBLIC_RESEARCH_ANSWER", JS_PUBLIC_ANSWERABILITY, 1120, 220),
        if_node("DECISION__PUBLIC_ANSWERABLE", "answerability_state", "public_answerable", 1400, 220),
        code_node("MARK_UNKNOWN__NOT_PUBLICLY_ANSWERABLE", JS_MARK_UNKNOWN, 1680, 20),
        code_node("OUTPUT_UNKNOWN_PRESERVED", JS_OUTPUT, 1960, 20),
        code_node("BUILD_TARGETED_QUERY", JS_BUILD_TARGETED_QUERY, 1680, 380),
        code_node("PREPARE_21_SEARCH_REQUEST", JS_PREPARE_21, 1960, 380),
        execute_subworkflow_node("EXECUTE_SUBWORKFLOW__21_WEB_SEARCH", "21_WEB_SEARCH", 2240, 380),
        code_node("VALIDATE_NEW_SOURCE", JS_VALIDATE_SEARCH, 2520, 380),
        if_node("DECISION__RESEARCH_FAILURE", "controlled_state", "research_failure", 2800, 380),
        code_node("OUTPUT_RESEARCH_FAILURE", JS_OUTPUT, 3080, 180),
        if_node("DECISION__NEW_SOURCE_FOUND", "controlled_state", "new_source_found", 3080, 520),
        code_node("OUTPUT_NEW_SOURCE_FOUND", JS_OUTPUT, 3360, 400),
        code_node("OUTPUT_NO_NEW_EVIDENCE", JS_OUTPUT, 3360, 620),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__MISSING_EVIDENCE_REQUEST"),
        ("INPUT_CONTRACT__MISSING_EVIDENCE_REQUEST", "DECISION__INVALID_INPUT"),
        ("DECISION__INVALID_INPUT", "OUTPUT_INVALID_INPUT", 0),
        ("DECISION__INVALID_INPUT", "DECISION__RETRY_EXHAUSTED", 1),
        ("DECISION__RETRY_EXHAUSTED", "MARK_UNKNOWN__RETRY_EXHAUSTED", 0),
        ("MARK_UNKNOWN__RETRY_EXHAUSTED", "OUTPUT_RETRY_EXHAUSTED"),
        ("DECISION__RETRY_EXHAUSTED", "CAN_PUBLIC_RESEARCH_ANSWER", 1),
        ("CAN_PUBLIC_RESEARCH_ANSWER", "DECISION__PUBLIC_ANSWERABLE"),
        ("DECISION__PUBLIC_ANSWERABLE", "BUILD_TARGETED_QUERY", 0),
        ("DECISION__PUBLIC_ANSWERABLE", "MARK_UNKNOWN__NOT_PUBLICLY_ANSWERABLE", 1),
        ("MARK_UNKNOWN__NOT_PUBLICLY_ANSWERABLE", "OUTPUT_UNKNOWN_PRESERVED"),
        ("BUILD_TARGETED_QUERY", "PREPARE_21_SEARCH_REQUEST"),
        ("PREPARE_21_SEARCH_REQUEST", "EXECUTE_SUBWORKFLOW__21_WEB_SEARCH"),
        ("EXECUTE_SUBWORKFLOW__21_WEB_SEARCH", "VALIDATE_NEW_SOURCE"),
        ("VALIDATE_NEW_SOURCE", "DECISION__RESEARCH_FAILURE"),
        ("DECISION__RESEARCH_FAILURE", "OUTPUT_RESEARCH_FAILURE", 0),
        ("DECISION__RESEARCH_FAILURE", "DECISION__NEW_SOURCE_FOUND", 1),
        ("DECISION__NEW_SOURCE_FOUND", "OUTPUT_NEW_SOURCE_FOUND", 0),
        ("DECISION__NEW_SOURCE_FOUND", "OUTPUT_NO_NEW_EVIDENCE", 1),
    ]
    return {
        "name": "54_EVIDENCE_GAP_RESEARCH",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def build_dev_workflow():
    branches = [
        ("ANSWERABLE_GIVEDIRECTLY", JS_DEV_ANSWERABLE, -180, "FINAL_ANSWERABLE_GAP"),
        ("NON_PUBLIC_INTERNAL", JS_DEV_INTERNAL, 200, "FINAL_NON_PUBLIC_GAP"),
        ("RETRY_EXHAUSTED", JS_DEV_RETRY, 580, "FINAL_RETRY_EXHAUSTED"),
    ]
    nodes = [
        sticky(
            "00_README__DEV_WORKFLOW",
            "DEV_PAOLA_54_EVIDENCE_GAP_TEST\nRuns three visible branches against stored workflow 54:\nA) GiveDirectly public-answerable financial gap\nB) internal/non-public gap\nC) retry exhausted\n\nAfter import, link each Execute Sub-workflow node to the real stored workflow 54. Workflow 54 itself links to stored workflow 21.",
            -560,
            -560,
            720,
            420,
            4,
        ),
        {
            "parameters": {},
            "id": "start__manual_test_trigger",
            "name": "START__MANUAL_TEST_TRIGGER",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [0, 120],
        },
    ]
    edges = []
    for label, js_code, y, final_name in branches:
        input_name = f"DEV_INPUT__{label}"
        execute_name = f"EXECUTE_SUBWORKFLOW__54_{label}"
        nodes.extend(
            [
                code_node(input_name, js_code, 300, y),
                execute_subworkflow_node(execute_name, "54_EVIDENCE_GAP_RESEARCH", 640, y),
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
        "name": "DEV_PAOLA_54_EVIDENCE_GAP_TEST",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure_paola_54_workflows(root=ROOT):
    root = Path(root)
    workflow_path = root / "workflows" / "skeletons" / "54_EVIDENCE_GAP_RESEARCH.json"
    dev_path = root / "workflows" / "dev" / "DEV_PAOLA_54_EVIDENCE_GAP_TEST.json"
    dev_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(json.dumps(build_workflow(), indent=2) + "\n", encoding="utf-8")
    dev_path.write_text(json.dumps(build_dev_workflow(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    configure_paola_54_workflows()
    print("Configured Paola 54 evidence gap research n8n exports.")
