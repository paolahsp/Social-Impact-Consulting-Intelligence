import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "workflows" / "skeletons"


NOTE = (
    "PHASE 2B P0 N8N EXECUTION\n"
    "Repository-ready n8n implementation for Paola P0 only.\n"
    "n8n owns the visible execution path and state passing.\n"
    "21 uses an HTTP Request node against DuckDuckGo Lite HTML with no credentials.\n"
    "Code nodes are limited to compact deterministic parsing, mapping, retrieval scoring, and validation.\n"
    "No Python runner is called by n8n. No secrets are stored."
)


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=520, height=260, color=5):
    return {
        "parameters": {"content": content, "height": height, "width": width, "color": color},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
    }


def trigger(name="START__SUB_WORKFLOW_TRIGGER", x=0, y=0):
    return {
        "parameters": {},
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.executeWorkflowTrigger",
        "typeVersion": 1,
        "position": [x, y],
    }


def manual_trigger(name="START__MANUAL_TEST_TRIGGER", x=0, y=0):
    return {
        "parameters": {},
        "id": slug(name),
        "name": name,
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


def http_node(name, x, y):
    return {
        "parameters": {
            "method": "GET",
            "url": "={{ $json.search.search_url }}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "User-Agent", "value": "Mozilla/5.0 Project3PaolaP0/1.0"},
                    {"name": "Accept", "value": "text/html,application/xhtml+xml"},
                ]
            },
            "options": {
                "timeout": 15000,
                "response": {"response": {"responseFormat": "text", "outputPropertyName": "html"}},
            },
        },
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [x, y],
        "continueOnFail": True,
    }


def if_node(name, left, right, x, y):
    return {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": slug(name + right),
                        "leftValue": left,
                        "rightValue": right,
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


def execute_workflow_node(name, target_workflow_name, x, y):
    return {
        "parameters": {
            "workflowId": "",
            "options": {},
        },
        "id": slug(name),
        "name": name,
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1,
        "position": [x, y],
        "notes": f"AFTER IMPORT: set workflowId to {target_workflow_name}. Do not invent IDs in repo JSON.",
    }


def connections(edges):
    out = {}
    for edge in edges:
        if len(edge) == 2:
            src, dst = edge
            index = 0
        else:
            src, dst, index = edge
        out.setdefault(src, {"main": []})
        while len(out[src]["main"]) <= index:
            out[src]["main"].append([])
        out[src]["main"][index].append({"node": dst, "type": "main", "index": 0})
    return out


def workflow(name, purpose, owner, input_contract, output_contract, nodes, edges):
    return {
        "name": name,
        "nodes": [
            sticky(
                "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
                f"PURPOSE\n{purpose}\n\nOWNER\n{owner}\n\nINPUT CONTRACT\n{input_contract}\n\nOUTPUT CONTRACT\n{output_contract}\n\nSTATUS\nPhase 2B repository-ready. Inactive by default. No credentials.",
                -420,
                -320,
                520,
                340,
                4,
            ),
            sticky("NOTE__PHASE2B_P0_N8N_EXECUTION", NOTE, -420, 60, 520, 300, 5),
            *nodes,
        ],
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


JS_21_INPUT = """
return items.map(item => {
  const payload = item.json || {};
  const runContext = payload.run_context || {
    run_id: payload.run_id || 'RUN-N8N-P0-TEST',
    organization: {
      name: payload.organization_name || payload.organization?.name,
      website: payload.website || payload.organization?.website,
      country: payload.country || payload.organization?.country,
      mission_area: payload.mission_area || payload.organization?.mission_area || null
    },
    current_challenge: payload.current_challenge || null,
    uploaded_document_refs: payload.uploaded_document_refs || [],
    status: 'created',
    started_at: payload.started_at || new Date().toISOString(),
    errors: []
  };
  if (!runContext.organization?.name || !runContext.organization?.website || !runContext.organization?.country) {
    return { json: { ...payload, run_context: runContext, controlled_state: 'invalid_input', errors: [{ stage: '21_WEB_SEARCH', message: 'organization_name, website, and country are required' }] } };
  }
  return { json: { ...payload, run_context: runContext, errors: payload.errors || [] } };
});
"""

JS_21_QUERY = """
return items.map(item => {
  const org = item.json.run_context.organization;
  const hint = item.json.query || 'annual report revenue funding grants donations financial statements';
  const query = `${org.name} ${org.country || ''} ${hint}`.trim();
  return { json: { ...item.json, search: { provider: 'duckduckgo_lite_html', query, search_url: `https://lite.duckduckgo.com/lite/?q=${encodeURIComponent(query)}` } } };
});
"""

JS_21_PARSE = """
function stripTags(value) {
  return String(value || '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/\\s+/g, ' ').trim();
}
function decodeDdgUrl(raw) {
  const value = String(raw || '').replace(/&amp;/g, '&');
  const match = value.match(/[?&]uddg=([^&]+)/);
  return match ? decodeURIComponent(match[1]) : value;
}
return items.map(item => {
  const baseItems = $items('BUILD_SEARCH_QUERY');
  const base = baseItems[$itemIndex]?.json || item.json;
  if (item.json.error || item.json.message?.includes('ECONN') || item.json.statusCode >= 400) {
    return { json: { ...base, controlled_state: 'request_failure', search: { ...(base.search || {}), raw_result_count: 0, results: [] }, errors: [...(base.errors || []), { stage: '21_WEB_SEARCH', error_type: 'request_failure', message: item.json.error?.message || item.json.message || 'HTTP request failed' }] } };
  }
  const html = String(item.json.html || item.json.data || item.json.body || item.json.response || item.json || '');
  const linkPattern = /<a[^>]+href="([^"]+)"[^>]*class='result-link'[^>]*>(.*?)<\\/a>/gs;
  const matches = [...html.matchAll(linkPattern)];
  const results = [];
  for (let i = 0; i < matches.length && results.length < 5; i++) {
    const start = matches[i].index + matches[i][0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index : html.length;
    const block = html.slice(start, end);
    const snippetMatch = block.match(/class='result-snippet'[^>]*>(.*?)<\\/td>/s);
    const url = decodeDdgUrl(matches[i][1]);
    if (url.startsWith('http')) {
      results.push({ title: stripTags(matches[i][2]), url, snippet: stripTags(snippetMatch ? snippetMatch[1] : '') });
    }
  }
  const controlled_state = results.length ? 'search_success' : 'empty_search';
  return { json: { ...base, controlled_state, search: { ...base.search, raw_result_count: results.length, results } } };
});
"""

JS_21_NORMALIZE = """
function domainFromUrl(url) { try { return new URL(url).hostname.replace(/^www\\./, '').toLowerCase(); } catch { return ''; } }
function sourceType(result) {
  const text = `${result.title} ${result.url} ${result.snippet}`.toLowerCase();
  if (text.includes('990') || text.includes('registry')) return 'registry';
  if (text.includes('annual') && text.includes('report')) return 'public_report';
  if (text.includes('news') || text.includes('press')) return 'media';
  return 'web_search_result';
}
const revenueTerms = ['annual','report','financial','finance','revenue','funding','grant','grants','donor','donors','donation','donations','fundraising','income','partnership','partners','990'];
return items.map(item => {
  const org = item.json.run_context.organization;
  const officialDomain = domainFromUrl(org.website || '');
  const orgTokens = String(org.name || '').toLowerCase().match(/[a-z0-9]+/g) || [];
  const relevant = (item.json.search.results || []).filter(result => {
    const haystack = `${result.title} ${result.url} ${result.snippet}`.toLowerCase();
    const host = domainFromUrl(result.url);
    return orgTokens.some(token => token.length > 2 && haystack.includes(token)) || (officialDomain && host.endsWith(officialDomain)) || revenueTerms.some(term => haystack.includes(term));
  });
  const retrieved_at = new Date().toISOString();
  const sources = relevant.map((result, index) => {
    const host = domainFromUrl(result.url);
    const is_official = Boolean(officialDomain && host.endsWith(officialDomain));
    return {
      source_id: `SRC-${String(index + 1).padStart(3, '0')}`,
      title: result.title || '',
      url: result.url,
      source_type: sourceType(result),
      publisher: is_official ? org.name : (host || null),
      publication_date: null,
      retrieved_at,
      authority_level: is_official ? 'official' : 'unknown',
      freshness: 'unknown',
      is_official,
      search_snippet: result.snippet || '',
      search_provider: item.json.search.provider
    };
  });
  return { json: { ...item.json, controlled_state: sources.length ? 'ok' : 'empty_search', sources } };
});
"""

JS_RETURN_SOURCES = """
return items.map(item => ({ json: { run_context: item.json.run_context, sources: item.json.sources || [], search: item.json.search, controlled_state: item.json.controlled_state, errors: item.json.errors || [] } }));
"""

JS_EMPTY_SEARCH = """
return items.map(item => ({ json: { run_context: item.json.run_context, sources: [], search: item.json.search, controlled_state: 'empty_search', errors: item.json.errors || [] } }));
"""

JS_REQUEST_FAILURE = """
return items.map(item => ({ json: { run_context: item.json.run_context, sources: [], search: item.json.search, controlled_state: 'request_failure', errors: item.json.errors || [{ stage: '21_WEB_SEARCH', message: 'HTTP request failed' }] } }));
"""

JS_PASS = "return items;"

JS_30_SOURCE_INPUT = """
return items.map(item => ({ json: { ...item.json, sources: item.json.sources || [], evidence: item.json.evidence || [], errors: item.json.errors || [] } }));
"""

JS_30_DEDUPE = """
return items.map(item => {
  const seen = new Set();
  const sources = [];
  for (const source of item.json.sources || []) {
    const key = String(source.url || '').toLowerCase();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    sources.push(source);
  }
  return { json: { ...item.json, sources } };
});
"""

JS_30_QUALITY = """
return items.map(item => {
  const sources = (item.json.sources || []).map(source => ({
    ...source,
    source_quality: {
      has_title: Boolean(source.title),
      has_url: Boolean(source.url),
      official_signal: Boolean(source.is_official),
      authority_level: source.authority_level || 'unknown'
    }
  }));
  return { json: { ...item.json, sources } };
});
"""

JS_30_EXTRACT = """
const revenueTerms = ['annual','report','financial','finance','revenue','funding','grant','grants','donor','donors','donation','donations','fundraising','income','partnership','partners','990'];
return items.map(item => {
  const runContext = item.json.run_context;
  const evidence = [];
  for (const source of item.json.sources || []) {
    const text = `${source.title} ${source.url} ${source.search_snippet || ''}`.toLowerCase();
    const terms = revenueTerms.filter(term => text.includes(term));
    if (!terms.length) continue;
    evidence.push({
      evidence_id: `EV-${String(evidence.length + 1).padStart(3, '0')}`,
      run_id: runContext.run_id,
      claim: `Public source "${source.title}" contains revenue-resilience search signals: ${terms.slice(0, 5).join(', ')}.`,
      source_ids: [source.source_id],
      domain: 'revenue_resilience',
      evidence_type: 'fact',
      confidence: source.is_official ? 0.68 : 0.52,
      status: 'supported',
      contradiction_ids: [],
      requires_validation: false
    });
  }
  if (!evidence.length) {
    evidence.push({ evidence_id: 'EV-001', run_id: runContext.run_id, claim: 'No revenue-resilience evidence was extracted from the available public search results.', source_ids: (item.json.sources || []).slice(0, 1).map(source => source.source_id), domain: 'revenue_resilience', evidence_type: 'unknown', confidence: 0.4, status: 'unknown', contradiction_ids: [], requires_validation: true });
  }
  return { json: { ...item.json, evidence } };
});
"""

JS_30_VALIDATE = """
return items.map(item => {
  const sourceIds = new Set((item.json.sources || []).map(source => source.source_id));
  const evidence = (item.json.evidence || []).map(ev => {
    const supportedRefs = (ev.source_ids || []).filter(id => sourceIds.has(id));
    if (ev.evidence_type === 'fact' && !supportedRefs.length) {
      return { ...ev, evidence_type: 'unknown', status: 'unknown', requires_validation: true, confidence: Math.min(ev.confidence || 0.4, 0.4) };
    }
    return ev;
  });
  return { json: { ...item.json, evidence } };
});
"""

JS_30_OUTPUT = """
return items.map(item => ({ json: { ...item.json, evidence_ledger: item.json.evidence, contradictions: [], unknowns: (item.json.evidence || []).filter(ev => ev.evidence_type === 'unknown').map((ev, index) => ({ unknown_id: `UNK-${String(index + 1).padStart(3, '0')}`, domain: ev.domain, description: ev.claim, evidence_ids: [ev.evidence_id] })) } }));
"""

JS_40_EVIDENCE_INPUT = """
return items.map(item => ({ json: { ...item.json, organization_evidence: (item.json.evidence || []).filter(ev => ev.domain === 'revenue_resilience') } }));
"""

JS_40_QUERY = """
return items.map(item => {
  const query = (item.json.organization_evidence || []).map(ev => ev.claim).join(' ');
  return { json: { ...item.json, retrieval_query: `${query} funding concentration revenue diversification recurring financial resilience limitations`.trim() } };
});
"""

JS_40_CORPUS = """
const framework_corpus = [
  { context_id: 'FRAMEWORK-REV-001', domain: 'revenue_resilience', title: 'Funding Concentration', content: 'Revenue resilience assessment should check whether an organization depends heavily on one grant, donor, contract, or funder. Public evidence may reveal named funding sources, but concentration percentages are often unknown without internal financial data.', evaluation_use: 'Use this when evidence mentions grants, funders, annual reports, or revenue sources. Do not infer concentration unless amounts or proportions are available.' },
  { context_id: 'FRAMEWORK-REV-002', domain: 'revenue_resilience', title: 'Revenue Diversification', content: 'Diversification considers whether public signals show multiple revenue types such as individual donations, grants, corporate partnerships, government contracts, memberships, or earned income. Public signals can support an observed finding that multiple revenue channels are described, but cannot prove resilience by themselves.', evaluation_use: 'Use this when evidence mentions donations, grants, partnerships, fundraising, revenue, or financial reports.' },
  { context_id: 'FRAMEWORK-REV-003', domain: 'revenue_resilience', title: 'Recurring Revenue', content: 'Recurring revenue signals include monthly giving, memberships, multi-year grants, subscriptions, retained service contracts, or repeat government funding. If these signals are not public, the correct result is an unknown or validation question, not a negative finding.', evaluation_use: 'Use this when public evidence mentions recurring donors, monthly giving, memberships, or multi-year funding.' },
  { context_id: 'FRAMEWORK-REV-004', domain: 'revenue_resilience', title: 'Financial Resilience Limitations', content: 'Public-data-first diagnostics must separate facts from hypotheses. Missing financial evidence should remain unknown. Do not invent revenue numbers, donor concentration, cash runway, operating reserves, or growth rates.', evaluation_use: 'Use this as a guardrail for all revenue resilience findings.' }
];
return items.map(item => ({ json: { ...item.json, framework_corpus } }));
"""

JS_40_SCORE = """
function tokens(text) { return new Set(String(text || '').toLowerCase().match(/[a-z0-9]+/g) || []); }
return items.map(item => {
  const q = tokens(item.json.retrieval_query);
  const contexts = (item.json.framework_corpus || []).map(doc => {
    const d = tokens(`${doc.title} ${doc.content} ${doc.evaluation_use}`);
    const score = [...q].filter(token => d.has(token)).length;
    return { ...doc, retrieval_score: score };
  }).filter(doc => doc.retrieval_score > 0).sort((a, b) => b.retrieval_score - a.retrieval_score).slice(0, 3);
  return { json: { ...item.json, rag_context: { retrieval_run_id: 'RAG-P0-N8N-001', domain: 'revenue_resilience', query: item.json.retrieval_query, contexts } } };
});
"""

JS_40_VALIDATE = """
return items.map(item => ({ json: { ...item.json, rag_context: { ...item.json.rag_context, organization_evidence_count: (item.json.organization_evidence || []).length, framework_context_count: (item.json.rag_context?.contexts || []).length } } }));
"""

JS_51_INPUT = """
return items.map(item => ({ json: { ...item.json, revenue_evidence: (item.json.evidence || []).filter(ev => ev.domain === 'revenue_resilience'), rag_context: item.json.rag_context || { contexts: [] } } }));
"""

JS_51_EVALUATE = """
return items.map(item => {
  const supported = (item.json.revenue_evidence || []).filter(ev => ev.evidence_type === 'fact' && ['supported', 'partially_supported'].includes(ev.status));
  const finding = supported.length
    ? { finding_id: 'F-001', domain: 'revenue_resilience', finding: 'Public search results surfaced revenue-resilience signals that should be reviewed before drawing conclusions about funding mix or concentration.', evidence_ids: supported.map(ev => ev.evidence_id), finding_type: 'observed', confidence: Math.round(Math.min(0.72, supported.reduce((sum, ev) => sum + ev.confidence, 0) / supported.length) * 100) / 100, requires_validation: true, validation_question: 'Which revenue sources are material, recurring, or concentrated in the current financial year?' }
    : { finding_id: 'F-001', domain: 'revenue_resilience', finding: 'Public search did not provide enough evidence to assess revenue resilience.', evidence_ids: (item.json.revenue_evidence || []).map(ev => ev.evidence_id), finding_type: 'unknown', confidence: 0.35, requires_validation: true, validation_question: "What are the organization's main revenue sources and how concentrated are they?" };
  finding.rag_context_ids = (item.json.rag_context?.contexts || []).map(ctx => ctx.context_id);
  finding.limitations = ['No revenue numbers are inferred from search metadata.', 'Missing financial evidence remains unknown rather than negative.'];
  return { json: { ...item.json, findings: [finding] } };
});
"""

JS_51_CHECK = """
return items.map(item => {
  const evidenceIds = new Set((item.json.evidence || []).map(ev => ev.evidence_id));
  const findings = (item.json.findings || []).map(finding => ({ ...finding, evidence_ids: (finding.evidence_ids || []).filter(id => evidenceIds.has(id)) }));
  return { json: { ...item.json, findings } };
});
"""

JS_51_UNKNOWNS = """
return items.map(item => {
  const hasUnknown = (item.json.revenue_evidence || []).some(ev => ev.evidence_type === 'unknown') || (item.json.findings || []).some(f => f.finding_type === 'unknown' || f.requires_validation);
  const unknowns = hasUnknown ? [{ unknown_id: 'UNK-REV-001', domain: 'revenue_resilience', description: 'Revenue concentration and recurrence cannot be determined from the P0 public search slice alone.', evidence_ids: (item.json.findings?.[0]?.evidence_ids || []) }] : [];
  return { json: { ...item.json, unknowns } };
});
"""

JS_51_OUTPUT = """
return items.map(item => ({ json: { run_context: item.json.run_context, sources: item.json.sources || [], evidence: item.json.evidence || [], findings: item.json.findings || [], unknowns: item.json.unknowns || [], contradictions: item.json.contradictions || [], rag_metadata: { retrieval_run_id: item.json.rag_context?.retrieval_run_id || null, domains: ['revenue_resilience'], retrieved_context_ids: (item.json.rag_context?.contexts || []).map(ctx => ctx.context_id) }, rag_context: item.json.rag_context, controlled_state: item.json.controlled_state, errors: item.json.errors || [] } }));
"""

JS_DEV_INPUT = """
return [{
  json: {
    organization_name: 'GiveDirectly',
    website: 'https://www.givedirectly.org',
    country: 'United States',
    query: 'annual report revenue funding grants donations financial statements'
  }
}];
"""

JS_DEV_EMPTY = """
return [{
  json: {
    run_context: {
      run_id: 'RUN-N8N-P0-EMPTY',
      organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States', mission_area: null },
      current_challenge: null,
      uploaded_document_refs: [],
      status: 'created',
      started_at: new Date().toISOString(),
      errors: []
    },
    sources: [],
    search: { provider: 'simulated_empty_search', query: 'SIMULATED_EMPTY_SEARCH', search_url: null, raw_result_count: 0, results: [] },
    controlled_state: 'empty_search',
    errors: []
  }
}];
"""


def configure_21():
    wf = workflow(
        "21_WEB_SEARCH",
        "Generic public-web discovery using visible n8n HTTP request and branch states.",
        "PAOLA TRACK A",
        "organization/run context plus query",
        "source.schema.json[] plus controlled_state",
        [
            trigger(),
            code_node("INPUT_CONTRACT__RESEARCH_TASK", JS_21_INPUT, 260, 0),
            code_node("BUILD_SEARCH_QUERY", JS_21_QUERY, 560, 0),
            http_node("HTTP_REQUEST__DUCKDUCKGO_LITE", 860, 0),
            code_node("PARSE_HTML_RESULTS", JS_21_PARSE, 1160, 0),
            if_node("DECISION__REQUEST_FAILURE", "={{ $json.controlled_state }}", "request_failure", 1460, 0),
            code_node("OUTPUT_REQUEST_FAILURE", JS_REQUEST_FAILURE, 1760, -220),
            if_node("DECISION__EMPTY_SEARCH", "={{ $json.controlled_state }}", "empty_search", 1760, 80),
            code_node("OUTPUT_EMPTY_SEARCH", JS_EMPTY_SEARCH, 2060, -80),
            code_node("NORMALIZE_RESULTS", JS_21_NORMALIZE, 2060, 180),
            code_node("OUTPUT_SUCCESS__SOURCES", JS_RETURN_SOURCES, 2360, 180),
        ],
        [
            ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__RESEARCH_TASK"),
            ("INPUT_CONTRACT__RESEARCH_TASK", "BUILD_SEARCH_QUERY"),
            ("BUILD_SEARCH_QUERY", "HTTP_REQUEST__DUCKDUCKGO_LITE"),
            ("HTTP_REQUEST__DUCKDUCKGO_LITE", "PARSE_HTML_RESULTS"),
            ("PARSE_HTML_RESULTS", "DECISION__REQUEST_FAILURE"),
            ("DECISION__REQUEST_FAILURE", "OUTPUT_REQUEST_FAILURE", 0),
            ("DECISION__REQUEST_FAILURE", "DECISION__EMPTY_SEARCH", 1),
            ("DECISION__EMPTY_SEARCH", "OUTPUT_EMPTY_SEARCH", 0),
            ("DECISION__EMPTY_SEARCH", "NORMALIZE_RESULTS", 1),
            ("NORMALIZE_RESULTS", "OUTPUT_SUCCESS__SOURCES"),
        ],
    )
    (WORKFLOW_DIR / "21_WEB_SEARCH.json").write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")


def configure_30():
    wf = workflow(
        "30_EVIDENCE_PIPELINE",
        "Convert normalized sources into traceable evidence for the P0 revenue slice.",
        "PAOLA TRACK A",
        "source.schema.json[] plus run_context",
        "evidence.schema.json[] plus evidence ledger metadata",
        [
            trigger(),
            code_node("SOURCE_INPUT", JS_30_SOURCE_INPUT, 260, 0),
            code_node("SOURCE_DEDUPLICATION", JS_30_DEDUPE, 560, 0),
            code_node("SOURCE_QUALITY", JS_30_QUALITY, 860, 0),
            code_node("EVIDENCE_EXTRACTION_MAPPING", JS_30_EXTRACT, 1160, 0),
            code_node("EVIDENCE_CLASSIFICATION", JS_PASS, 1460, 0),
            code_node("EVIDENCE_VALIDATION", JS_30_VALIDATE, 1760, 0),
            code_node("OUTPUT_CONTRACT__EVIDENCE_LEDGER", JS_30_OUTPUT, 2060, 0),
        ],
        [
            ("START__SUB_WORKFLOW_TRIGGER", "SOURCE_INPUT"),
            ("SOURCE_INPUT", "SOURCE_DEDUPLICATION"),
            ("SOURCE_DEDUPLICATION", "SOURCE_QUALITY"),
            ("SOURCE_QUALITY", "EVIDENCE_EXTRACTION_MAPPING"),
            ("EVIDENCE_EXTRACTION_MAPPING", "EVIDENCE_CLASSIFICATION"),
            ("EVIDENCE_CLASSIFICATION", "EVIDENCE_VALIDATION"),
            ("EVIDENCE_VALIDATION", "OUTPUT_CONTRACT__EVIDENCE_LEDGER"),
        ],
    )
    (WORKFLOW_DIR / "30_EVIDENCE_PIPELINE.json").write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")


def configure_40():
    wf = workflow(
        "40_RAG_RETRIEVAL_PIPELINE",
        "Retrieve Revenue Resilience framework context from a transparent local P0 corpus.",
        "PAOLA TRACK A",
        "organization evidence plus domain/query",
        "rag_context with framework contexts",
        [
            sticky("NOTE__P0_LOCAL_CORPUS", "P0 RETRIEVAL IMPLEMENTATION\nThis is local JSON corpus retrieval, not Pinecone or a production vector store.\nOrganization evidence and framework knowledge remain separate.", -420, 400, 520, 220, 6),
            trigger(),
            code_node("ORGANIZATION_EVIDENCE_INPUT", JS_40_EVIDENCE_INPUT, 260, 0),
            code_node("BUILD_RETRIEVAL_QUERY", JS_40_QUERY, 560, 0),
            code_node("LOAD_LOCAL_FRAMEWORK_CORPUS", JS_40_CORPUS, 860, 0),
            code_node("SCORE_AND_SELECT_CONTEXTS", JS_40_SCORE, 1160, 0),
            code_node("VALIDATE_RETRIEVAL", JS_40_VALIDATE, 1460, 0),
            code_node("OUTPUT_CONTRACT__RAG_CONTEXT", JS_PASS, 1760, 0),
        ],
        [
            ("START__SUB_WORKFLOW_TRIGGER", "ORGANIZATION_EVIDENCE_INPUT"),
            ("ORGANIZATION_EVIDENCE_INPUT", "BUILD_RETRIEVAL_QUERY"),
            ("BUILD_RETRIEVAL_QUERY", "LOAD_LOCAL_FRAMEWORK_CORPUS"),
            ("LOAD_LOCAL_FRAMEWORK_CORPUS", "SCORE_AND_SELECT_CONTEXTS"),
            ("SCORE_AND_SELECT_CONTEXTS", "VALIDATE_RETRIEVAL"),
            ("VALIDATE_RETRIEVAL", "OUTPUT_CONTRACT__RAG_CONTEXT"),
        ],
    )
    (WORKFLOW_DIR / "40_RAG_RETRIEVAL_PIPELINE.json").write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")


def configure_51():
    wf = workflow(
        "51_REVENUE_RESILIENCE_AGENT",
        "Produce a structured Revenue Resilience finding from evidence and retrieved context.",
        "PAOLA TRACK A",
        "revenue evidence plus revenue RAG context",
        "finding.schema.json[] for revenue resilience",
        [
            trigger(),
            code_node("INPUT_CONTRACT__REVENUE_EVIDENCE_AND_RAG", JS_51_INPUT, 260, 0),
            code_node("REVENUE_EVALUATION", JS_51_EVALUATE, 560, 0),
            code_node("EVIDENCE_TRACE_CHECK", JS_51_CHECK, 860, 0),
            code_node("UNKNOWN_LIMITATIONS", JS_51_UNKNOWNS, 1160, 0),
            code_node("OUTPUT_CONTRACT__PAOLA_TRACK_OUTPUT", JS_51_OUTPUT, 1460, 0),
        ],
        [
            ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__REVENUE_EVIDENCE_AND_RAG"),
            ("INPUT_CONTRACT__REVENUE_EVIDENCE_AND_RAG", "REVENUE_EVALUATION"),
            ("REVENUE_EVALUATION", "EVIDENCE_TRACE_CHECK"),
            ("EVIDENCE_TRACE_CHECK", "UNKNOWN_LIMITATIONS"),
            ("UNKNOWN_LIMITATIONS", "OUTPUT_CONTRACT__PAOLA_TRACK_OUTPUT"),
        ],
    )
    (WORKFLOW_DIR / "51_REVENUE_RESILIENCE_AGENT.json").write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")


def configure_dev_workflow():
    dev_dir = ROOT / "workflows" / "dev"
    dev_dir.mkdir(parents=True, exist_ok=True)
    nodes = [
        sticky("00_README__DEV_WORKFLOW", "DEV_PAOLA_P0_LIVE_TEST\nImport after workflows 21, 30, 40, and 51.\nThis workflow provides GiveDirectly test input and visibly chains the four P0 workflows.\nWorkflow IDs must be linked manually after import.", -420, -300, 520, 300, 4),
        manual_trigger(),
        code_node("DEV_INPUT__GIVEDIRECTLY", JS_DEV_INPUT, 260, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH", "21_WEB_SEARCH", 560, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__30_EVIDENCE_PIPELINE", "30_EVIDENCE_PIPELINE", 860, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__40_RAG_RETRIEVAL", "40_RAG_RETRIEVAL_PIPELINE", 1160, 0),
        execute_workflow_node("TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE", "51_REVENUE_RESILIENCE_AGENT", 1460, 0),
        code_node("FINAL_PAOLA_TRACK_OUTPUT", JS_PASS, 1760, 0),
        code_node("DEV_INPUT__SIMULATED_EMPTY_SEARCH_FOR_30", JS_DEV_EMPTY, 260, 300),
    ]
    wf = {
        "name": "DEV_PAOLA_P0_LIVE_TEST",
        "nodes": nodes,
        "connections": connections(
            [
                ("START__MANUAL_TEST_TRIGGER", "DEV_INPUT__GIVEDIRECTLY"),
                ("DEV_INPUT__GIVEDIRECTLY", "TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH"),
                ("TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH", "TODO_LINK_SUBWORKFLOW__30_EVIDENCE_PIPELINE"),
                ("TODO_LINK_SUBWORKFLOW__30_EVIDENCE_PIPELINE", "TODO_LINK_SUBWORKFLOW__40_RAG_RETRIEVAL"),
                ("TODO_LINK_SUBWORKFLOW__40_RAG_RETRIEVAL", "TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE"),
                ("TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE", "FINAL_PAOLA_TRACK_OUTPUT"),
            ]
        ),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }
    (dev_dir / "DEV_PAOLA_P0_LIVE_TEST.json").write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")


def configure_paola_p0_workflows(root=ROOT):
    global WORKFLOW_DIR
    WORKFLOW_DIR = Path(root) / "workflows" / "skeletons"
    configure_21()
    configure_30()
    configure_40()
    configure_51()
    configure_dev_workflow()


if __name__ == "__main__":
    configure_paola_p0_workflows()
    print("Configured Paola P0 n8n-native workflow exports.")
