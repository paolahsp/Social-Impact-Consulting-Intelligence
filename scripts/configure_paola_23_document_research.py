import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def slug(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=620, height=340, color=4):
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
                "cachedResultName": "23_DOCUMENT_PUBLIC_DATA_RESEARCH",
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
        "notes": "AFTER IMPORT: select the stored n8n workflow 23_DOCUMENT_PUBLIC_DATA_RESEARCH. Never invent an ID.",
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


JS_INPUT_VALIDATION = r"""
function normalizeWebsite(value) {
  const raw = String(value || '').trim();
  if (!raw) return null;
  try {
    const parsed = new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`);
    if (!parsed.hostname.includes('.')) return null;
    return `${parsed.protocol}//${parsed.hostname.toLowerCase()}`;
  } catch { return null; }
}

return items.map(item => {
  const payload = item.json || {};
  const suppliedContext = payload.run_context || {};
  const suppliedOrganization = suppliedContext.organization || payload.organization || {};
  const organization = {
    ...suppliedOrganization,
    name: payload.organization_name || suppliedOrganization.name || null,
    website: normalizeWebsite(payload.website || suppliedOrganization.website),
    country: payload.country || suppliedOrganization.country || null,
    mission_area: payload.mission_area || suppliedOrganization.mission_area || null
  };
  const runContext = {
    ...suppliedContext,
    run_id: suppliedContext.run_id || payload.run_id || `RUN-23-${Date.now()}`,
    organization,
    current_challenge: suppliedContext.current_challenge || payload.current_challenge || null,
    uploaded_document_refs: suppliedContext.uploaded_document_refs || payload.uploaded_document_refs || [],
    status: suppliedContext.status || 'created',
    started_at: suppliedContext.started_at || payload.started_at || new Date().toISOString(),
    errors: suppliedContext.errors || []
  };
  const errors = [...(payload.errors || [])];
  if (!organization.name || !organization.website || !organization.country) {
    errors.push({
      stage: 'INPUT_VALIDATION',
      error_type: 'invalid_input',
      message: 'organization name, website, and country are required'
    });
  }
  const rawCandidates = Array.isArray(payload.document_candidates)
    ? payload.document_candidates.slice(0, 8)
    : [];
  return {
    json: {
      run_context: runContext,
      organization,
      document_candidates: rawCandidates,
      controlled_state: errors.length ? 'request_failure' : 'ready',
      errors,
      extraction_provider: 'jina_reader'
    }
  };
});
"""


JS_DOCUMENT_CANDIDATES = r"""
const output = [];
for (const item of items) {
  const base = item.json;
  if (base.controlled_state === 'request_failure') {
    output.push({ json: { ...base, candidate_index: 0, candidate: null, candidate_state: 'input_failure', fetch_state: 'rejected' } });
    continue;
  }
  if (!base.document_candidates.length) {
    output.push({ json: { ...base, candidate_index: 0, candidate: null, candidate_state: 'no_documents_found', fetch_state: 'rejected' } });
    continue;
  }
  for (let index = 0; index < base.document_candidates.length; index++) {
    const supplied = base.document_candidates[index] || {};
    const url = String(supplied.url || '').trim();
    let validUrl = null;
    try {
      const parsed = new URL(url);
      if (['http:', 'https:'].includes(parsed.protocol)) validUrl = parsed.toString();
    } catch {}
    output.push({
      json: {
        ...base,
        candidate_index: index,
        candidate: {
          url: validUrl || url || null,
          title: supplied.title ? String(supplied.title).trim() : null,
          discovered_by: ['web_search', 'website_extraction', 'public_data'].includes(supplied.discovered_by)
            ? supplied.discovered_by
            : 'public_data'
        },
        candidate_state: validUrl ? 'candidate' : 'invalid_url',
        fetch_state: validUrl ? 'pending' : 'rejected'
      }
    });
  }
}
return output;
"""


JS_RELEVANCE_FILTER = r"""
const documentSignals = ['annual', 'report', 'impact', 'financial', 'finance', 'audit', 'audited', 'accounts', 'transparency', 'results', 'strategy', 'publication', 'statement', 'form 990', '990'];
const supportedExtensions = ['pdf', 'txt', 'html', 'htm', 'csv', 'json', 'doc', 'docx'];
const unsupportedExtensions = ['zip', 'rar', 'exe', 'jpg', 'jpeg', 'png', 'gif', 'mp3', 'mp4'];

return items.map(item => {
  if (item.json.fetch_state === 'rejected') return item;
  const candidate = item.json.candidate || {};
  const text = `${candidate.title || ''} ${candidate.url || ''}`.toLowerCase();
  const extensionMatch = String(candidate.url || '').match(/\.([a-z0-9]{2,5})(?:[?#]|$)/i);
  const extension = extensionMatch ? extensionMatch[1].toLowerCase() : null;
  const hasSignal = documentSignals.some(signal => text.includes(signal));
  const supportedExtension = Boolean(extension && supportedExtensions.includes(extension));
  const unsupportedExtension = Boolean(extension && unsupportedExtensions.includes(extension));
  const relevant = !unsupportedExtension && (supportedExtension || hasSignal);
  return {
    json: {
      ...item.json,
      candidate_state: relevant ? 'relevant_document' : 'unsupported_document',
      fetch_state: relevant ? 'pending' : 'rejected',
      relevance_reason: relevant
        ? (supportedExtension ? `supported_${extension}_candidate` : 'document_title_or_url_signal')
        : (unsupportedExtension ? `unsupported_${extension}` : 'no_document_signal'),
      file_type_hint: extension || (hasSignal ? 'html' : null)
    }
  };
});
"""


JS_ORGANIZATION_MATCH = r"""
function host(value) {
  try { return new URL(value).hostname.replace(/^www\./, '').toLowerCase(); }
  catch { return ''; }
}
function tokens(value) {
  return String(value || '').toLowerCase().match(/[a-z0-9]+/g) || [];
}

return items.map(item => {
  if (item.json.fetch_state === 'rejected') return item;
  const org = item.json.organization;
  const officialDomain = host(org.website);
  const candidateDomain = host(item.json.candidate.url);
  const officialMatch = Boolean(officialDomain && candidateDomain && (candidateDomain === officialDomain || candidateDomain.endsWith(`.${officialDomain}`)));
  const orgTokens = tokens(org.name).filter(token => token.length >= 3);
  const candidateText = `${item.json.candidate.title || ''} ${item.json.candidate.url || ''}`.toLowerCase();
  const nameMatch = orgTokens.some(token => candidateText.includes(token));
  const plausibleMatch = officialMatch || nameMatch;
  return {
    json: {
      ...item.json,
      organization_match: {
        matched: plausibleMatch,
        official_domain_match: officialMatch,
        organization_name_match: nameMatch,
        method: officialMatch ? 'official_domain' : (nameMatch ? 'organization_name' : 'no_match')
      },
      is_official: officialMatch,
      authority_level: officialMatch ? 'official' : 'unknown',
      candidate_state: plausibleMatch ? 'organization_matched' : 'organization_mismatch',
      fetch_state: plausibleMatch ? 'ready' : 'rejected',
      extraction_url: plausibleMatch ? `https://r.jina.ai/${item.json.candidate.url}` : null
    }
  };
});
"""


JS_RESPONSE_CHECK = r"""
function responseText(value) {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return '';
  try { return JSON.stringify(value); } catch { return String(value); }
}

return items.map((item, index) => {
  const bases = $items('DECISION__FETCHABLE', 0);
  const base = bases[index]?.json || item.json;
  const text = responseText(item.json.document_text || item.json.data || item.json.body || item.json.response || '');
  const errorMessage = item.json.error?.message || item.json.message || '';
  const statusCode = Number(item.json.statusCode || item.json.status || 0);
  const titleMatch = text.match(/^Title:\s*(.+)$/mi);
  const sourceMatch = text.match(/^URL Source:\s*(.+)$/mi);
  const publishedMatch = text.match(/^Published Time:\s*(.+)$/mi);
  const looksLikeProviderError = /Target URL returned error|Domain .* could not be resolved|Failed to fetch|Access Denied|\b404 Not Found\b|\b502 Bad Gateway\b|cannot find the page|page not found/i.test(text);
  const failed = Boolean(item.json.error || errorMessage || statusCode >= 400 || looksLikeProviderError || text.trim().length < 200);
  if (failed) {
    return {
      json: {
        ...base,
        fetch_state: 'request_failure',
        document_text: '',
        fetch_error: errorMessage || (statusCode ? `HTTP ${statusCode}` : 'Jina Reader returned no usable document content')
      }
    };
  }
  return {
    json: {
      ...base,
      fetch_state: 'success',
      document_text: text,
      reader_title: titleMatch ? titleMatch[1].trim() : null,
      reader_source_url: sourceMatch ? sourceMatch[1].trim() : base.candidate.url,
      reader_published_time: publishedMatch ? publishedMatch[1].trim() : null
    }
  };
});
"""


JS_DOCUMENT_CLASSIFICATION = r"""
return items.map(item => {
  if (item.json.fetch_state !== 'success') return item;
  const text = `${item.json.candidate.title || ''} ${item.json.candidate.url || ''} ${item.json.reader_title || ''} ${item.json.document_text.slice(0, 5000)}`.toLowerCase();
  let documentType = 'other_public_document';
  if (/audited|independent auditor|auditors['’]? report/.test(text) && /financial|statement|accounts/.test(text)) documentType = 'audited_financial_statement';
  else if (/impact\s+(and\s+progress\s+)?report|impact report/.test(text)) documentType = 'impact_report';
  else if (/annual\s+(activity\s+)?report|annual report/.test(text)) documentType = 'annual_report';
  else if (/financial\s+(report|statement)|statement of financial|financial statements|form 990/.test(text)) documentType = 'financial_report';
  else if (/program(me)?\s+report|activity report|project report/.test(text)) documentType = 'program_report';
  else if (/strategy|strategic framework|strategic plan/.test(text)) documentType = 'strategy_document';
  else if (/registry|charity commission|companies house|public filing/.test(text)) documentType = 'public_registry_document';
  return { json: { ...item.json, document_type: documentType } };
});
"""


JS_CONTENT_EXTRACTION = r"""
function clean(value) {
  return String(value || '')
    .replace(/^Title:.*$/gmi, '')
    .replace(/^URL Source:.*$/gmi, '')
    .replace(/^Published Time:.*$/gmi, '')
    .replace(/^Markdown Content:\s*$/gmi, '')
    .replace(/\r/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
const sectionRules = [
  ['financial', ['revenue', 'income', 'expenditure', 'expenses', 'funding', 'grant', 'donation', 'financial position', 'cash flow', 'net assets']],
  ['impact', ['impact', 'outcome', 'results', 'beneficiaries', 'recipients', 'people reached']],
  ['programs', ['program', 'programme', 'activities', 'services', 'operations']],
  ['governance', ['governance', 'board', 'trustees', 'management', 'accountability', 'audit committee']],
  ['partners', ['partner', 'partnership', 'donor', 'funder']],
  ['strategy', ['strategy', 'strategic', 'priorities', 'objectives', 'goals']]
];

return items.map(item => {
  if (item.json.fetch_state !== 'success') return item;
  const content = clean(item.json.document_text).slice(0, 80000);
  const blocks = content.split(/\n\s*\n|(?=^#{1,4}\s)/m)
    .map(block => block.replace(/\s+/g, ' ').trim())
    .filter(block => block.length >= 80);
  const sections = [];
  const seen = new Set();
  for (const [sectionType, terms] of sectionRules) {
    let count = 0;
    for (const block of blocks) {
      const lower = block.toLowerCase();
      if (!terms.some(term => lower.includes(term))) continue;
      const text = block.slice(0, 1200);
      const key = text.toLowerCase().slice(0, 240);
      if (seen.has(key)) continue;
      seen.add(key);
      sections.push({ section_type: sectionType, text });
      count += 1;
      if (count >= 2 || sections.length >= 8) break;
    }
    if (sections.length >= 8) break;
  }
  if (!sections.length) {
    for (const block of blocks.slice(0, 2)) sections.push({ section_type: 'overview', text: block.slice(0, 1200) });
  }
  return {
    json: {
      ...item.json,
      extracted_content: content,
      content_length: content.length,
      sections
    }
  };
});
"""


JS_METADATA_NORMALIZATION = r"""
function publicationDate(value) {
  if (!value) return null;
  const match = String(value).match(/\b(20\d{2})-(\d{2})-(\d{2})\b/);
  return match ? match[0] : null;
}
function fileType(value, hint) {
  const match = String(value || '').match(/\.([a-z0-9]{2,5})(?:[?#]|$)/i);
  return match ? match[1].toLowerCase() : (hint || 'html');
}
function fallbackTitle(url) {
  try {
    const last = new URL(url).pathname.split('/').filter(Boolean).pop() || 'Public document';
    return decodeURIComponent(last).replace(/[-_]+/g, ' ').replace(/\.[a-z0-9]{2,5}$/i, '').trim() || 'Public document';
  } catch { return 'Public document'; }
}

return items.map(item => {
  if (item.json.fetch_state !== 'success' || !item.json.sections?.length) {
    return {
      json: {
        run_context: item.json.run_context,
        result_type: 'error',
        candidate_index: item.json.candidate_index,
        candidate: item.json.candidate,
        error: {
          stage: item.json.fetch_state === 'success' ? 'CONTENT_EXTRACTION' : 'DOCUMENT_FETCH',
          error_type: item.json.fetch_state === 'success' ? 'extraction_failure' : 'request_failure',
          url: item.json.candidate?.url || null,
          message: item.json.fetch_error || 'The document did not yield useful extractable content'
        }
      }
    };
  }
  const sequence = String(item.json.candidate_index + 1).padStart(3, '0');
  const title = item.json.reader_title || item.json.candidate.title || fallbackTitle(item.json.candidate.url);
  const retrievedAt = new Date().toISOString();
  const sourceId = `SRC-DOC-${sequence}`;
  const documentId = `DOC-${sequence}`;
  const metadata = {
    title,
    url: item.json.candidate.url,
    document_type: item.json.document_type || 'other_public_document',
    publisher: item.json.is_official ? item.json.organization.name : null,
    publication_date: publicationDate(item.json.reader_published_time),
    retrieved_at: retrievedAt,
    authority_level: item.json.authority_level || 'unknown',
    is_official: Boolean(item.json.is_official),
    file_type: fileType(item.json.candidate.url, item.json.file_type_hint),
    discovered_by: item.json.candidate.discovered_by,
    organization_match: item.json.organization_match
  };
  return {
    json: {
      run_context: item.json.run_context,
      result_type: 'document',
      candidate_index: item.json.candidate_index,
      source: {
        source_id: sourceId,
        title: metadata.title,
        url: metadata.url,
        source_type: `public_document_${metadata.document_type}`,
        publisher: metadata.publisher,
        publication_date: metadata.publication_date,
        retrieved_at: metadata.retrieved_at,
        authority_level: metadata.authority_level,
        freshness: 'unknown',
        is_official: metadata.is_official,
        document_id: documentId,
        document_type: metadata.document_type,
        file_type: metadata.file_type,
        discovered_by: metadata.discovered_by,
        extraction_provider: 'jina_reader',
        useful_sections: item.json.sections
      },
      document: {
        document_id: documentId,
        source_id: sourceId,
        ...metadata,
        sections: item.json.sections,
        content_excerpt: item.json.extracted_content.slice(0, 3000),
        extracted_character_count: item.json.content_length
      }
    }
  };
});
"""


JS_REJECTED_CANDIDATE = r"""
return items.map(item => {
  if (item.json.candidate_state === 'no_documents_found') {
    return { json: { run_context: item.json.run_context, result_type: 'control', control_state: 'no_documents_found', candidate_index: null, candidate: null } };
  }
  const errorType = item.json.candidate_state === 'input_failure'
    ? 'invalid_input'
    : item.json.candidate_state === 'organization_mismatch'
      ? 'organization_mismatch'
      : item.json.candidate_state === 'invalid_url'
        ? 'invalid_url'
        : 'unsupported_document';
  return {
    json: {
      run_context: item.json.run_context,
      result_type: 'error',
      candidate_index: item.json.candidate_index,
      candidate: item.json.candidate,
      error: {
        stage: errorType === 'invalid_input' ? 'INPUT_VALIDATION' : errorType === 'organization_mismatch' ? 'ORGANIZATION_MATCH_CHECK' : 'DOCUMENT_RELEVANCE_FILTER',
        error_type: errorType,
        url: item.json.candidate?.url || null,
        message: errorType === 'organization_mismatch'
          ? 'Document candidate could not be matched to the target organization'
          : errorType === 'unsupported_document'
            ? 'Candidate is not a supported or recognizable public document'
            : errorType === 'invalid_url'
              ? 'Document candidate URL is not a valid HTTP(S) URL'
              : 'Organization input is incomplete'
      }
    }
  };
});
"""


JS_AGGREGATE = r"""
const rows = items.map(item => item.json);
const runContext = rows.find(row => row.run_context)?.run_context || null;
const documents = rows.filter(row => row.result_type === 'document').map(row => row.document).sort((a, b) => a.document_id.localeCompare(b.document_id));
const sources = rows.filter(row => row.result_type === 'document').map(row => row.source).sort((a, b) => a.source_id.localeCompare(b.source_id));
const errors = rows.filter(row => row.result_type === 'error').map(row => row.error);
const candidatesAttempted = rows.filter(row => row.candidate?.url).length;
let controlledState = 'success';
if (documents.length && errors.length) controlledState = 'partial_success';
else if (documents.length) controlledState = 'success';
else if (rows.some(row => row.control_state === 'no_documents_found')) controlledState = 'no_documents_found';
else if (errors.length && errors.every(error => error.error_type === 'unsupported_document')) controlledState = 'unsupported_document';
else controlledState = 'request_failure';

return [{
  json: {
    run_context: runContext,
    controlled_state: controlledState,
    extraction_provider: 'jina_reader',
    provider: {
      name: 'Jina Reader',
      credential_required: false,
      integration: 'n8n HTTP Request',
      endpoint_pattern: 'https://r.jina.ai/{public_document_url}'
    },
    candidates_attempted: candidatesAttempted,
    documents,
    sources,
    useful_sections_count: documents.reduce((total, document) => total + document.sections.length, 0),
    errors
  }
}];
"""


JS_OUTPUT = r"""
return items.map(item => ({ json: {
  run_context: item.json.run_context,
  controlled_state: item.json.controlled_state,
  extraction_provider: item.json.extraction_provider,
  provider: item.json.provider,
  candidates_attempted: item.json.candidates_attempted,
  documents: item.json.documents || [],
  sources: item.json.sources || [],
  useful_sections_count: item.json.useful_sections_count || 0,
  errors: item.json.errors || []
} }));
"""


JS_DEV_GIVEDIRECTLY = r"""
return [{ json: {
  run_id: 'RUN-N8N-23-GIVEDIRECTLY',
  organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States' },
  document_candidates: [{
    url: 'https://www.givedirectly.org/wp-content/uploads/2024/11/FY2023-GiveDirectly-Audit-Final-FS-Public-Disclosure.pdf',
    title: 'GiveDirectly FY2023 audited financial statements',
    discovered_by: 'website_extraction'
  }]
} }];
"""


JS_DEV_MSF = r"""
return [{ json: {
  run_id: 'RUN-N8N-23-MSF',
  organization: { name: 'Médecins Sans Frontières', website: 'https://www.msf.org', country: 'Switzerland' },
  document_candidates: [{
    url: 'https://www.msf.org/sites/default/files/2024-07/MSF_Financial_Report_2023_FINAL_APPROVED_030724.pdf',
    title: 'MSF International Financial Report 2023',
    discovered_by: 'web_search'
  }]
} }];
"""


JS_DEV_PARTIAL = r"""
return [{ json: {
  run_id: 'RUN-N8N-23-PARTIAL',
  organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States' },
  document_candidates: [
    {
      url: 'https://www.givedirectly.org/wp-content/uploads/2024/11/FY2023-GiveDirectly-Audit-Final-FS-Public-Disclosure.pdf',
      title: 'GiveDirectly FY2023 audited financial statements',
      discovered_by: 'website_extraction'
    },
    {
      url: 'https://www.givedirectly.org/wp-content/uploads/2099/12/missing-document.pdf',
      title: 'Missing GiveDirectly report test',
      discovered_by: 'public_data'
    }
  ]
} }];
"""


JS_DEV_UNSUPPORTED = r"""
return [{ json: {
  run_id: 'RUN-N8N-23-UNSUPPORTED',
  organization: { name: 'GiveDirectly', website: 'https://www.givedirectly.org', country: 'United States' },
  document_candidates: [{
    url: 'https://www.givedirectly.org/about',
    title: 'About GiveDirectly',
    discovered_by: 'website_extraction'
  }]
} }];
"""


def build_workflow():
    nodes = [
        sticky(
            "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
            "PURPOSE\nTurn public organizational documents into traceable, bounded sources.\n\nOWNER\nPAOLA TRACK A\n\nINPUT CONTRACT\nrun_context + organization + document_candidates[]\n\nOUTPUT CONTRACT\nsource.schema.json[] + documents[] + controlled_state + errors[]\n\nSTATUS\nRepository-ready Jina Reader implementation. Inactive by default. No credentials. Public document statements only; no consulting conclusions.",
            -620,
            -520,
            680,
            420,
            4,
        ),
        sticky(
            "NOTE__FACT_BOUNDARIES",
            "WHAT THE DOCUMENT STATES ≠ WHAT THE CONSULTING SYSTEM CONCLUDES\nExtracted sections remain source text. Missing data remains unknown. This workflow never upgrades public document text into an efficiency, performance, or strategy judgment.",
            -620,
            -40,
            680,
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
        code_node("INPUT_VALIDATION", JS_INPUT_VALIDATION, 260, 0),
        code_node("DOCUMENT_CANDIDATES", JS_DOCUMENT_CANDIDATES, 540, 0),
        code_node("DOCUMENT_RELEVANCE_FILTER", JS_RELEVANCE_FILTER, 820, 0),
        code_node("ORGANIZATION_MATCH_CHECK", JS_ORGANIZATION_MATCH, 1100, 0),
        if_node("DECISION__FETCHABLE", "fetch_state", "ready", 1380, 0),
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
                    "timeout": 90000,
                    "response": {"response": {"responseFormat": "text", "outputPropertyName": "document_text"}},
                },
            },
            "id": "document_fetch__jina_reader",
            "name": "DOCUMENT_FETCH__JINA_READER",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1660, -160],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxTries": 2,
            "waitBetweenTries": 1000,
        },
        code_node("FILE_TYPE_AND_RESPONSE_CHECK", JS_RESPONSE_CHECK, 1940, -160),
        code_node("DOCUMENT_TYPE_CLASSIFICATION", JS_DOCUMENT_CLASSIFICATION, 2220, -160),
        code_node("USEFUL_SECTION_EXTRACTION", JS_CONTENT_EXTRACTION, 2500, -160),
        code_node("METADATA_NORMALIZATION", JS_METADATA_NORMALIZATION, 2780, -160),
        code_node("NORMALIZE_REJECTED_CANDIDATE", JS_REJECTED_CANDIDATE, 1940, 240),
        {
            "parameters": {"mode": "append", "numberInputs": 2},
            "id": "merge__candidate_results",
            "name": "MERGE__CANDIDATE_RESULTS",
            "type": "n8n-nodes-base.merge",
            "typeVersion": 3.2,
            "position": [3080, 40],
        },
        code_node("AGGREGATE_DOCUMENT_RESULTS", JS_AGGREGATE, 3360, 40),
        if_node("DECISION__NO_DOCUMENTS_FOUND", "controlled_state", "no_documents_found", 3640, 40),
        code_node("OUTPUT_NO_DOCUMENTS_FOUND", JS_OUTPUT, 3920, -320),
        if_node("DECISION__UNSUPPORTED_DOCUMENT", "controlled_state", "unsupported_document", 3920, 40),
        code_node("OUTPUT_UNSUPPORTED_DOCUMENT", JS_OUTPUT, 4200, -220),
        if_node("DECISION__REQUEST_FAILURE", "controlled_state", "request_failure", 4200, 100),
        code_node("OUTPUT_REQUEST_FAILURE", JS_OUTPUT, 4480, -100),
        if_node("DECISION__PARTIAL_SUCCESS", "controlled_state", "partial_success", 4480, 180),
        code_node("OUTPUT_PARTIAL_SUCCESS", JS_OUTPUT, 4760, 80),
        code_node("OUTPUT_SUCCESS", JS_OUTPUT, 4760, 300),
    ]
    edges = [
        ("START__SUB_WORKFLOW_TRIGGER", "INPUT_VALIDATION"),
        ("INPUT_VALIDATION", "DOCUMENT_CANDIDATES"),
        ("DOCUMENT_CANDIDATES", "DOCUMENT_RELEVANCE_FILTER"),
        ("DOCUMENT_RELEVANCE_FILTER", "ORGANIZATION_MATCH_CHECK"),
        ("ORGANIZATION_MATCH_CHECK", "DECISION__FETCHABLE"),
        ("DECISION__FETCHABLE", "DOCUMENT_FETCH__JINA_READER", 0),
        ("DECISION__FETCHABLE", "NORMALIZE_REJECTED_CANDIDATE", 1),
        ("DOCUMENT_FETCH__JINA_READER", "FILE_TYPE_AND_RESPONSE_CHECK"),
        ("FILE_TYPE_AND_RESPONSE_CHECK", "DOCUMENT_TYPE_CLASSIFICATION"),
        ("DOCUMENT_TYPE_CLASSIFICATION", "USEFUL_SECTION_EXTRACTION"),
        ("USEFUL_SECTION_EXTRACTION", "METADATA_NORMALIZATION"),
        ("METADATA_NORMALIZATION", "MERGE__CANDIDATE_RESULTS", 0, 0),
        ("NORMALIZE_REJECTED_CANDIDATE", "MERGE__CANDIDATE_RESULTS", 0, 1),
        ("MERGE__CANDIDATE_RESULTS", "AGGREGATE_DOCUMENT_RESULTS"),
        ("AGGREGATE_DOCUMENT_RESULTS", "DECISION__NO_DOCUMENTS_FOUND"),
        ("DECISION__NO_DOCUMENTS_FOUND", "OUTPUT_NO_DOCUMENTS_FOUND", 0),
        ("DECISION__NO_DOCUMENTS_FOUND", "DECISION__UNSUPPORTED_DOCUMENT", 1),
        ("DECISION__UNSUPPORTED_DOCUMENT", "OUTPUT_UNSUPPORTED_DOCUMENT", 0),
        ("DECISION__UNSUPPORTED_DOCUMENT", "DECISION__REQUEST_FAILURE", 1),
        ("DECISION__REQUEST_FAILURE", "OUTPUT_REQUEST_FAILURE", 0),
        ("DECISION__REQUEST_FAILURE", "DECISION__PARTIAL_SUCCESS", 1),
        ("DECISION__PARTIAL_SUCCESS", "OUTPUT_PARTIAL_SUCCESS", 0),
        ("DECISION__PARTIAL_SUCCESS", "OUTPUT_SUCCESS", 1),
    ]
    return {
        "name": "23_DOCUMENT_PUBLIC_DATA_RESEARCH",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def build_dev_workflow():
    branches = [
        ("GIVEDIRECTLY", JS_DEV_GIVEDIRECTLY, -360, "FINAL_GIVEDIRECTLY_SUCCESS"),
        ("MSF", JS_DEV_MSF, -80, "FINAL_MSF_SUCCESS"),
        ("PARTIAL_SUCCESS", JS_DEV_PARTIAL, 200, "FINAL_PARTIAL_SUCCESS"),
        ("UNSUPPORTED", JS_DEV_UNSUPPORTED, 480, "FINAL_UNSUPPORTED_DOCUMENT"),
    ]
    nodes = [
        sticky(
            "00_README__DEV_WORKFLOW",
            "DEV_PAOLA_23_DOCUMENT_RESEARCH_TEST\nRuns four visible branches against the stored 23 sub-workflow:\n1) GiveDirectly audited financial statement\n2) MSF financial report\n3) valid + missing GiveDirectly documents (partial success)\n4) unsupported non-document URL\n\nAfter import, link every Execute Sub-workflow node to the real stored workflow 23.",
            -520,
            -620,
            680,
            420,
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
        execute_name = f"EXECUTE_SUBWORKFLOW__23_{label}"
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
        "name": "DEV_PAOLA_23_DOCUMENT_RESEARCH_TEST",
        "nodes": nodes,
        "connections": connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


def configure_paola_23_workflows(root=ROOT):
    root = Path(root)
    workflow_path = root / "workflows" / "skeletons" / "23_DOCUMENT_PUBLIC_DATA_RESEARCH.json"
    dev_path = root / "workflows" / "dev" / "DEV_PAOLA_23_DOCUMENT_RESEARCH_TEST.json"
    dev_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(json.dumps(build_workflow(), indent=2) + "\n", encoding="utf-8")
    dev_path.write_text(json.dumps(build_dev_workflow(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    configure_paola_23_workflows()
    print("Configured Paola 23 document research n8n exports.")
