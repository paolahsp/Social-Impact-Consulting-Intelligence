import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "skeletons" / "22_WEBSITE_EXTRACTION.json"
DEV_WORKFLOW_PATH = ROOT / "workflows" / "dev" / "DEV_PAOLA_22_WEBSITE_EXTRACTION_TEST.json"


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=540, height=320, color=4):
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


def if_node(name, expected, x, y):
    return {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": slug(f"{name}_{expected}"),
                        "leftValue": "={{ $json.controlled_state }}",
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
        "notes": f"AFTER IMPORT: select the stored n8n workflow {target_name}. Never use Local File or invent an ID.",
    }


def connections(edges):
    result = {}
    for source, target, *output_index in edges:
        index = output_index[0] if output_index else 0
        result.setdefault(source, {"main": []})
        while len(result[source]["main"]) <= index:
            result[source]["main"].append([])
        result[source]["main"][index].append({"node": target, "type": "main", "index": 0})
    return result


JS_INPUT_VALIDATION = r"""
function normalizeWebsite(value) {
  const raw = String(value || '').trim();
  if (!raw) return null;
  const candidate = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  const match = candidate.match(/^(https?):\/\/([^\/?#]+)(?:[\/?#]|$)/i);
  if (!match || !match[2] || !match[2].includes('.')) return null;
  return `${match[1].toLowerCase()}://${match[2].toLowerCase()}`;
}

return items.map(item => {
  const payload = item.json || {};
  const organization = payload.run_context?.organization || payload.organization || {};
  const organizationName = payload.organization_name || organization.name;
  const country = payload.country || organization.country;
  const website = normalizeWebsite(payload.official_url || payload.website || organization.website);
  const runContext = payload.run_context || {
    run_id: payload.run_id || `RUN-22-${Date.now()}`,
    organization: {
      name: organizationName,
      website,
      country,
      mission_area: payload.mission_area || organization.mission_area || null
    },
    current_challenge: payload.current_challenge || null,
    uploaded_document_refs: payload.uploaded_document_refs || [],
    status: 'created',
    started_at: payload.started_at || new Date().toISOString(),
    errors: []
  };
  runContext.organization = {
    ...(runContext.organization || {}),
    name: organizationName,
    website,
    country,
    mission_area: payload.mission_area || organization.mission_area || runContext.organization?.mission_area || null
  };
  const errors = [...(payload.errors || [])];
  if (!organizationName || !country || !website) {
    errors.push({
      stage: 'INPUT_VALIDATION',
      error_type: 'invalid_input',
      message: 'organization_name, website/official_url, and country are required and website must be an HTTP(S) URL'
    });
  }
  return {
    json: {
      ...payload,
      run_context: runContext,
      official_url: website,
      controlled_state: errors.length ? 'request_failure' : 'ready',
      errors
    }
  };
});
"""


JS_OFFICIAL_URL = r"""
return items.map(item => {
  if (item.json.controlled_state === 'request_failure') return item;
  const officialDomain = String(item.json.official_url).replace(/^https?:\/\//i, '').split('/')[0].replace(/^www\./, '').toLowerCase();
  return {
    json: {
      ...item.json,
      official_domain: officialDomain,
      extraction_provider: 'jina_reader',
      provider_endpoint_pattern: 'https://r.jina.ai/http://{host}{path}'
    }
  };
});
"""


JS_PAGE_DISCOVERY = r"""
const output = [];
const pathCandidates = [
  { path: '/', page_type: 'home' },
  { path: '/about', page_type: 'about' },
  { path: '/our-work', page_type: 'programs' },
  { path: '/impact', page_type: 'impact' },
  { path: '/financials', page_type: 'financials' },
  { path: '/annual-reports', page_type: 'reports' },
  { path: '/donate', page_type: 'fundraising' },
  { path: '/contact', page_type: 'contact' }
];

for (const item of items) {
  if (item.json.controlled_state === 'request_failure') {
    output.push({ json: { ...item.json, page_index: 0, page_type: 'invalid_input', page_url: null, extraction_url: null } });
    continue;
  }
  const root = String(item.json.official_url).replace(/\/+$/, '');
  const host = root.replace(/^https?:\/\//i, '').split('/')[0];
  for (let index = 0; index < pathCandidates.length; index++) {
    const candidate = pathCandidates[index];
    const pageUrl = candidate.path === '/' ? `${root}/` : `${root}${candidate.path}`;
    const extractionUrl = `https://r.jina.ai/http://${host}${candidate.path}`;
    output.push({
      json: {
        ...item.json,
        page_index: index,
        page_type: candidate.page_type,
        page_url: pageUrl,
        extraction_url: extractionUrl,
        relevance_reason: `official_${candidate.page_type}_candidate`
      }
    });
  }
}
return output;
"""


JS_RELEVANCE_FILTER = r"""
const allowedTypes = new Set(['home', 'about', 'programs', 'impact', 'financials', 'reports', 'fundraising', 'contact']);
return items.filter(item => item.json.controlled_state === 'request_failure' || (item.json.page_url && allowedTypes.has(item.json.page_type)));
"""


JS_RESPONSE_VALIDATION = r"""
function responseText(value) {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return '';
  try { return JSON.stringify(value); } catch { return String(value); }
}

return items.map((item, index) => {
  const bases = $items('RELEVANCE_FILTER');
  const base = bases[index]?.json || item.json;
  if (base.controlled_state === 'request_failure' && !base.extraction_url) {
    return { json: { ...base, fetch_state: 'request_failure' } };
  }
  const text = responseText(item.json.reader_text || item.json.data || item.json.body || item.json.response || '');
  const errorMessage = item.json.error?.message || item.json.message || '';
  const statusCode = Number(item.json.statusCode || item.json.status || 0);
  const titleMatch = text.match(/^Title:\s*(.+)$/mi);
  const title = titleMatch ? titleMatch[1].trim() : '';
  const looksLikeProviderError = /Target URL returned error|Domain .* could not be resolved|Failed to fetch|Access Denied|\b404 Not Found\b|\b502 Bad Gateway\b|cannot find the page/i.test(text) || /page not found/i.test(title);
  const failed = Boolean(item.json.error || errorMessage || statusCode >= 400 || looksLikeProviderError || text.trim().length < 80);
  if (failed) {
    return {
      json: {
        ...base,
        fetch_state: 'request_failure',
        reader_text: '',
        fetch_error: errorMessage || (statusCode ? `HTTP ${statusCode}` : 'Jina Reader returned no usable page content')
      }
    };
  }
  const sourceMatch = text.match(/^URL Source:\s*(.+)$/mi);
  return {
    json: {
      ...base,
      fetch_state: 'success',
      reader_text: text,
      reader_title: title,
      reader_source_url: sourceMatch ? sourceMatch[1].trim() : base.page_url
    }
  };
});
"""


JS_ORGANIZATION_MATCH = r"""
function host(value) {
  const match = String(value || '').match(/^https?:\/\/([^\/?#]+)/i);
  return match ? match[1].replace(/^www\./, '').toLowerCase() : '';
}

return items.map(item => {
  if (item.json.fetch_state !== 'success') return item;
  const expectedDomain = item.json.official_domain;
  const actualDomain = host(item.json.reader_source_url || item.json.page_url);
  const officialDomainMatch = Boolean(expectedDomain && actualDomain && (actualDomain === expectedDomain || actualDomain.endsWith(`.${expectedDomain}`)));
  const nameTokens = String(item.json.run_context?.organization?.name || '').toLowerCase().match(/[a-z0-9]+/g) || [];
  const content = `${item.json.reader_title || ''} ${item.json.reader_text || ''}`.toLowerCase();
  const nameMatch = nameTokens.filter(token => token.length > 3).some(token => content.includes(token));
  return {
    json: {
      ...item.json,
      organization_match: officialDomainMatch || nameMatch,
      is_official: officialDomainMatch
    }
  };
});
"""


JS_USEFUL_CONTENT = r"""
function clean(value) {
  return String(value || '')
    .replace(/^Title:.*$/gmi, '')
    .replace(/^URL Source:.*$/gmi, '')
    .replace(/^Published Time:.*$/gmi, '')
    .replace(/^Markdown Content:\s*$/gmi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

return items.map(item => {
  if (item.json.fetch_state !== 'success' || !item.json.organization_match) {
    return { json: { ...item.json, useful_content: '' } };
  }
  const content = clean(item.json.reader_text).slice(0, 16000);
  const title = item.json.reader_title || content.match(/^#\s+(.+)$/m)?.[1]?.trim() || `${item.json.run_context.organization.name} — ${item.json.page_type}`;
  return {
    json: {
      ...item.json,
      source_title: title,
      useful_content: content,
      content_length: content.length
    }
  };
});
"""


JS_SOURCE_NORMALIZATION = r"""
return items.map(item => {
  if (item.json.fetch_state !== 'success' || !item.json.organization_match || !item.json.useful_content) {
    return {
      json: {
        run_context: item.json.run_context,
        page_index: item.json.page_index,
        page_type: item.json.page_type,
        page_url: item.json.page_url,
        result_type: 'error',
        error: {
          stage: item.json.fetch_state === 'success' ? 'ORGANIZATION_MATCH_CHECK' : 'EXTRACTION_REQUEST__JINA_READER',
          error_type: item.json.fetch_state === 'success' ? 'organization_mismatch' : 'request_failure',
          page_url: item.json.page_url,
          message: item.json.fetch_error || 'The page did not yield usable organization-matched content'
        }
      }
    };
  }
  const normalizedPageType = /jobs?|openings?|careers?/i.test(item.json.source_title || '')
    ? 'careers'
    : item.json.page_type;
  return {
    json: {
      run_context: item.json.run_context,
      result_type: 'source',
      source: {
        source_id: `SRC-WEB-${String(item.json.page_index + 1).padStart(3, '0')}`,
        title: item.json.source_title,
        url: item.json.page_url,
        source_type: `official_website_${normalizedPageType}`,
        publisher: item.json.run_context.organization.name,
        publication_date: null,
        retrieved_at: new Date().toISOString(),
        authority_level: 'official',
        freshness: 'unknown',
        is_official: true,
        extraction_provider: 'jina_reader',
        page_type: normalizedPageType,
        useful_content: item.json.useful_content
      }
    }
  };
});
"""


JS_AGGREGATE = r"""
function sentences(text) {
  return String(text || '').replace(/\s+/g, ' ').split(/(?<=[.!?])\s+/).map(value => value.trim()).filter(value => value.length >= 40 && value.length <= 360);
}
function selectSignals(allSentences, terms, limit = 5) {
  const selected = [];
  const seen = new Set();
  for (const sentence of allSentences) {
    const lower = sentence.toLowerCase();
    if (!terms.some(term => lower.includes(term))) continue;
    const key = lower.slice(0, 180);
    if (seen.has(key)) continue;
    seen.add(key);
    selected.push(sentence);
    if (selected.length >= limit) break;
  }
  return selected;
}

const rows = items.map(item => item.json);
const sourceRows = rows.filter(row => row.result_type === 'source');
const sources = sourceRows.map(row => row.source);
const errors = rows.filter(row => row.result_type === 'error').map(row => row.error);
const runContext = rows[0]?.run_context || null;
const allSentences = sourceRows.flatMap(row => sentences(row.source.useful_content));
const stakeholderEntryPoints = sources
  .filter(source => ['fundraising', 'contact', 'programs'].includes(source.page_type))
  .map(source => ({ page_type: source.page_type, title: source.title, url: source.url }));
const reportLinks = sources
  .filter(source => ['financials', 'reports'].includes(source.page_type) || /report|financial|research/i.test(`${source.title} ${source.url}`))
  .map(source => ({ title: source.title, url: source.url, page_type: source.page_type }));
const websiteContext = {
  mission_signals: selectSignals(allSentences, ['mission', 'purpose', 'we exist', 'our goal', 'our vision', 'people in poverty', 'living in poverty', 'help someone']),
  program_signals: selectSignals(allSentences, ['program', 'how it works', 'what we do', 'service', 'cash transfer', 'initiative']),
  impact_signals: selectSignals(allSentences, ['impact', 'evidence', 'research', 'results', 'outcomes']),
  fundraising_signals: selectSignals(allSentences, ['donate', 'donor', 'fundraising', 'contribution', 'give now', 'support our']),
  stakeholder_entry_points: stakeholderEntryPoints,
  report_links: reportLinks
};
let controlledState = 'success';
if (!sources.length && errors.length) controlledState = 'request_failure';
else if (!sources.length) controlledState = 'no_relevant_content';
return [{
  json: {
    run_context: runContext,
    controlled_state: controlledState,
    extraction_provider: 'jina_reader',
    pages_attempted: rows.length,
    sources,
    website_context: websiteContext,
    errors
  }
}];
"""


JS_OUTPUT = r"""
return items.map(item => ({
  json: {
    run_context: item.json.run_context,
    controlled_state: item.json.controlled_state,
    extraction_provider: item.json.extraction_provider,
    pages_attempted: item.json.pages_attempted,
    sources: item.json.sources || [],
    website_context: item.json.website_context || {
      mission_signals: [],
      program_signals: [],
      impact_signals: [],
      fundraising_signals: [],
      stakeholder_entry_points: [],
      report_links: []
    },
    errors: item.json.errors || []
  }
}));
"""


JS_DEV_GIVEDIRECTLY = r"""
return [{ json: {
  run_id: 'RUN-N8N-22-GIVEDIRECTLY',
  organization_name: 'GiveDirectly',
  website: 'https://www.givedirectly.org',
  country: 'United States'
} }];
"""


JS_DEV_INVALID = r"""
return [{ json: {
  run_id: 'RUN-N8N-22-INVALID',
  organization_name: 'Invalid Website Test',
  website: 'https://this-domain-must-not-exist.invalid',
  country: 'Test'
} }];
"""


def build_workflow():
    nodes = [
        sticky(
            "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
            "PURPOSE\nExtract useful public evidence from official organization pages.\n\nOWNER\nPAOLA TRACK A\n\nINPUT CONTRACT\nofficial_url or website plus run_context/organization fields\n\nOUTPUT CONTRACT\nsource.schema.json[] plus controlled_state and website_context\n\nSTATUS\nRepository-ready Jina Reader development implementation. Inactive by default. No credentials. Public evidence only; no consulting conclusions.",
            -520,
            -420,
            600,
            400,
            4,
        ),
        sticky(
            "NOTE__FACT_BOUNDARIES",
            "FACT ≠ INFERENCE ≠ HYPOTHESIS ≠ UNKNOWN\nThis workflow collects and normalizes public page evidence. Missing content remains unknown. It must never infer organizational inefficiency, performance, or need from missing website information.",
            -520,
            20,
            600,
            260,
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
        code_node("INPUT_VALIDATION", JS_INPUT_VALIDATION, 280, 0),
        code_node("OFFICIAL_URL", JS_OFFICIAL_URL, 560, 0),
        code_node("PAGE_DISCOVERY", JS_PAGE_DISCOVERY, 840, 0),
        code_node("RELEVANCE_FILTER", JS_RELEVANCE_FILTER, 1120, 0),
        {
            "parameters": {
                "method": "GET",
                "url": "={{ $json.extraction_url }}",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "Accept", "value": "text/plain"},
                        {"name": "User-Agent", "value": "Mozilla/5.0 SocialImpactConsultingIntelligence/1.0"},
                    ]
                },
                "options": {
                    "timeout": 30000,
                    "response": {"response": {"responseFormat": "text", "outputPropertyName": "reader_text"}},
                },
            },
            "id": "extraction_request__jina_reader",
            "name": "EXTRACTION_REQUEST__JINA_READER",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1400, 0],
            "continueOnFail": True,
        },
        code_node("RESPONSE_VALIDATION", JS_RESPONSE_VALIDATION, 1680, 0),
        code_node("ORGANIZATION_MATCH_CHECK", JS_ORGANIZATION_MATCH, 1960, 0),
        code_node("USEFUL_CONTENT", JS_USEFUL_CONTENT, 2240, 0),
        code_node("SOURCE_NORMALIZATION", JS_SOURCE_NORMALIZATION, 2520, 0),
        code_node("AGGREGATE_WEBSITE_CONTEXT", JS_AGGREGATE, 2800, 0),
        if_node("DECISION__REQUEST_FAILURE", "request_failure", 3080, 0),
        code_node("OUTPUT_REQUEST_FAILURE", JS_OUTPUT, 3360, -240),
        if_node("DECISION__NO_RELEVANT_CONTENT", "no_relevant_content", 3360, 80),
        code_node("OUTPUT_NO_RELEVANT_CONTENT", JS_OUTPUT, 3640, -40),
        code_node("OUTPUT_SUCCESS", JS_OUTPUT, 3640, 180),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_VALIDATION"),
        ("INPUT_VALIDATION", "OFFICIAL_URL"),
        ("OFFICIAL_URL", "PAGE_DISCOVERY"),
        ("PAGE_DISCOVERY", "RELEVANCE_FILTER"),
        ("RELEVANCE_FILTER", "EXTRACTION_REQUEST__JINA_READER"),
        ("EXTRACTION_REQUEST__JINA_READER", "RESPONSE_VALIDATION"),
        ("RESPONSE_VALIDATION", "ORGANIZATION_MATCH_CHECK"),
        ("ORGANIZATION_MATCH_CHECK", "USEFUL_CONTENT"),
        ("USEFUL_CONTENT", "SOURCE_NORMALIZATION"),
        ("SOURCE_NORMALIZATION", "AGGREGATE_WEBSITE_CONTEXT"),
        ("AGGREGATE_WEBSITE_CONTEXT", "DECISION__REQUEST_FAILURE"),
        ("DECISION__REQUEST_FAILURE", "OUTPUT_REQUEST_FAILURE", 0),
        ("DECISION__REQUEST_FAILURE", "DECISION__NO_RELEVANT_CONTENT", 1),
        ("DECISION__NO_RELEVANT_CONTENT", "OUTPUT_NO_RELEVANT_CONTENT", 0),
        ("DECISION__NO_RELEVANT_CONTENT", "OUTPUT_SUCCESS", 1),
    ]
    return {
        "name": "22_WEBSITE_EXTRACTION",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def build_dev_workflow():
    nodes = [
        sticky(
            "00_README__DEV_WORKFLOW",
            "DEV_PAOLA_22_WEBSITE_EXTRACTION_TEST\nRuns two visible branches against the stored 22_WEBSITE_EXTRACTION sub-workflow:\n1) GiveDirectly happy path\n2) reserved invalid domain failure path\n\nAfter import, both Execute Sub-workflow nodes must be linked to the real stored workflow ID.",
            -480,
            -360,
            580,
            320,
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
        code_node("DEV_INPUT__GIVEDIRECTLY", JS_DEV_GIVEDIRECTLY, 300, -80),
        execute_subworkflow_node("EXECUTE_SUBWORKFLOW__22_GIVEDIRECTLY", "22_WEBSITE_EXTRACTION", 620, -80),
        code_node("FINAL_HAPPY_PATH_RESULT", "return items;", 940, -80),
        code_node("DEV_INPUT__INVALID_WEBSITE", JS_DEV_INVALID, 300, 260),
        execute_subworkflow_node("EXECUTE_SUBWORKFLOW__22_INVALID_WEBSITE", "22_WEBSITE_EXTRACTION", 620, 260),
        code_node("FINAL_FAILURE_PATH_RESULT", "return items;", 940, 260),
    ]
    edges = [
        ("START__MANUAL_TEST_TRIGGER", "DEV_INPUT__GIVEDIRECTLY"),
        ("DEV_INPUT__GIVEDIRECTLY", "EXECUTE_SUBWORKFLOW__22_GIVEDIRECTLY"),
        ("EXECUTE_SUBWORKFLOW__22_GIVEDIRECTLY", "FINAL_HAPPY_PATH_RESULT"),
        ("START__MANUAL_TEST_TRIGGER", "DEV_INPUT__INVALID_WEBSITE"),
        ("DEV_INPUT__INVALID_WEBSITE", "EXECUTE_SUBWORKFLOW__22_INVALID_WEBSITE"),
        ("EXECUTE_SUBWORKFLOW__22_INVALID_WEBSITE", "FINAL_FAILURE_PATH_RESULT"),
    ]
    return {
        "name": "DEV_PAOLA_22_WEBSITE_EXTRACTION_TEST",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure_paola_22_workflows(root=ROOT):
    root = Path(root)
    workflow_path = root / "workflows" / "skeletons" / "22_WEBSITE_EXTRACTION.json"
    dev_workflow_path = root / "workflows" / "dev" / "DEV_PAOLA_22_WEBSITE_EXTRACTION_TEST.json"
    dev_workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(json.dumps(build_workflow(), indent=2) + "\n", encoding="utf-8")
    dev_workflow_path.write_text(json.dumps(build_dev_workflow(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    configure_paola_22_workflows()
    print("Configured Paola 22 website extraction n8n exports.")
