import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "fixtures" / "organization_input.json"
DEFAULT_CORPUS = ROOT / "knowledge" / "revenue_resilience_corpus.json"


REVENUE_TERMS = {
    "annual",
    "report",
    "financial",
    "finance",
    "revenue",
    "funding",
    "grant",
    "grants",
    "donor",
    "donors",
    "donation",
    "donations",
    "fundraising",
    "income",
    "partnership",
    "partners",
    "990",
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def domain_from_url(url):
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def strip_tags(value):
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def ddg_result_url(raw_href):
    raw_href = html.unescape(raw_href)
    parsed = urllib.parse.urlparse(raw_href)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return query["uddg"][0]
    return raw_href


def build_search_query(run_context, query_hint):
    org = run_context["organization"]
    hint = query_hint or "annual report revenue funding grants donations"
    return f'{org["name"]} {org.get("country", "")} {hint}'.strip()


def search_duckduckgo(query, max_results=5, timeout=15):
    url = "https://lite.duckduckgo.com/lite/?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Project3PaolaP0/1.0; public research configuration test",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")

    results = []
    link_pattern = re.compile(r"<a[^>]+href=\"([^\"]+)\"[^>]*class='result-link'[^>]*>(.*?)</a>", flags=re.S)
    matches = list(link_pattern.finditer(body))
    for offset, link_match in enumerate(matches):
        next_start = matches[offset + 1].start() if offset + 1 < len(matches) else len(body)
        block = body[link_match.end():next_start]
        snippet_match = re.search(r"class='result-snippet'[^>]*>(.*?)</td>", block, flags=re.S)
        snippet_html = snippet_match.group(1) if snippet_match else ""
        result = {
            "title": strip_tags(link_match.group(2)),
            "url": ddg_result_url(link_match.group(1)),
            "snippet": strip_tags(snippet_html),
        }
        if result["url"].startswith("//"):
            result["url"] = "https:" + result["url"]
        if result["title"] and result["url"].startswith("http"):
            results.append(result)
        if len(results) >= max_results:
            break
    return {"provider": "duckduckgo_html", "query": query, "search_url": url, "raw_result_count": len(results), "results": results}


def search_bing(query, max_results=5, timeout=15):
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Project3PaolaP0/1.0; public research configuration test",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")

    results = []
    blocks = re.findall(r"<li class=\"b_algo\".*?</li>", body, flags=re.S)
    for block in blocks:
        link_match = re.search(r"<h2.*?<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>", block, flags=re.S)
        if not link_match:
            continue
        snippet_match = re.search(r"<p[^>]*>(.*?)</p>", block, flags=re.S)
        result = {
            "title": strip_tags(link_match.group(2)),
            "url": html.unescape(link_match.group(1)),
            "snippet": strip_tags(snippet_match.group(1)) if snippet_match else "",
        }
        if result["title"] and result["url"].startswith("http"):
            results.append(result)
        if len(results) >= max_results:
            break
    return {"provider": "bing_html", "query": query, "search_url": url, "raw_result_count": len(results), "results": results}


def search_web(query, max_results=5, timeout=15):
    errors = []
    for search_func in [search_duckduckgo, search_bing]:
        try:
            payload = search_func(query, max_results=max_results, timeout=timeout)
            if payload["results"]:
                payload["fallback_errors"] = errors
                return payload
            errors.append({"provider": payload["provider"], "error_type": "EmptyResults", "message": "Provider returned zero parseable results."})
        except Exception as exc:
            errors.append({"provider": search_func.__name__.replace("search_", "") + "_html", "error_type": type(exc).__name__, "message": str(exc)})
    return {"provider": "no_provider_success", "query": query, "search_url": None, "raw_result_count": 0, "results": [], "fallback_errors": errors}


def infer_source_type(result):
    text = f'{result.get("title", "")} {result.get("url", "")} {result.get("snippet", "")}'.lower()
    if "annual" in text and "report" in text:
        return "public_report"
    if "990" in text or "charity" in text or "registry" in text:
        return "registry"
    if "news" in text or "press" in text:
        return "media"
    return "web_search_result"


def normalize_sources(search_payload, run_context):
    official_domain = domain_from_url(run_context["organization"].get("website", ""))
    org_name = run_context["organization"]["name"].lower()
    retrieved_at = utc_now()
    sources = []
    relevant_results = []
    for result in search_payload.get("results", []):
        haystack = f'{result.get("title", "")} {result.get("url", "")} {result.get("snippet", "")}'.lower()
        result_domain = domain_from_url(result.get("url", ""))
        org_tokens = [token for token in re.findall(r"[a-z0-9]+", org_name) if len(token) > 2]
        has_org = any(token in haystack for token in org_tokens) or (official_domain and result_domain.endswith(official_domain))
        has_revenue_signal = any(term in haystack for term in REVENUE_TERMS)
        if has_org or has_revenue_signal:
            relevant_results.append(result)

    for index, result in enumerate(relevant_results, start=1):
        result_domain = domain_from_url(result["url"])
        is_official = bool(official_domain and result_domain.endswith(official_domain))
        if not is_official and org_name in result.get("title", "").lower() and official_domain in result_domain:
            is_official = True
        sources.append(
            {
                "source_id": f"SRC-{index:03d}",
                "title": result.get("title") or "",
                "url": result["url"],
                "source_type": infer_source_type(result),
                "publisher": run_context["organization"]["name"] if is_official else result_domain or None,
                "publication_date": None,
                "retrieved_at": retrieved_at,
                "authority_level": "official" if is_official else "unknown",
                "freshness": "unknown",
                "is_official": is_official,
                "search_snippet": result.get("snippet", ""),
                "search_provider": search_payload.get("provider"),
            }
        )
    return sources


def classify_revenue_evidence(source):
    text = f'{source.get("title", "")} {source.get("url", "")} {source.get("search_snippet", "")}'.lower()
    terms = sorted(term for term in REVENUE_TERMS if term in text)
    if not terms:
        return None
    claim = f'Public source "{source["title"]}" contains revenue-resilience search signals: {", ".join(terms[:5])}.'
    confidence = 0.68 if source.get("is_official") else 0.52
    if source.get("source_type") == "public_report":
        confidence += 0.08
    return {
        "claim": claim,
        "domain": "revenue_resilience",
        "evidence_type": "fact",
        "confidence": min(round(confidence, 2), 0.86),
        "status": "supported",
        "requires_validation": False,
    }


def extract_evidence(run_context, sources):
    evidence = []
    for source in sources:
        extracted = classify_revenue_evidence(source)
        if not extracted:
            continue
        evidence.append(
            {
                "evidence_id": f"EV-{len(evidence) + 1:03d}",
                "run_id": run_context["run_id"],
                "claim": extracted["claim"],
                "source_ids": [source["source_id"]],
                "domain": extracted["domain"],
                "evidence_type": extracted["evidence_type"],
                "confidence": extracted["confidence"],
                "status": extracted["status"],
                "contradiction_ids": [],
                "requires_validation": extracted["requires_validation"],
            }
        )
    if not evidence:
        evidence.append(
            {
                "evidence_id": "EV-001",
                "run_id": run_context["run_id"],
                "claim": "No revenue-resilience evidence was extracted from the available public search results.",
                "source_ids": [source["source_id"] for source in sources[:1]],
                "domain": "revenue_resilience",
                "evidence_type": "unknown",
                "confidence": 0.4,
                "status": "unknown",
                "contradiction_ids": [],
                "requires_validation": True,
            }
        )
    return evidence


def tokenize(text):
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def retrieve_rag_context(evidence, corpus):
    query = " ".join(item["claim"] for item in evidence if item.get("domain") == "revenue_resilience")
    query_tokens = tokenize(query + " funding concentration revenue diversification recurring financial resilience limitations")
    scored = []
    for doc in corpus:
        doc_text = f'{doc["title"]} {doc["content"]} {doc["evaluation_use"]}'
        score = len(query_tokens & tokenize(doc_text))
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    contexts = []
    for score, doc in scored[:3]:
        item = dict(doc)
        item["retrieval_score"] = score
        contexts.append(item)
    return {
        "retrieval_run_id": "RAG-P0-001",
        "domain": "revenue_resilience",
        "query": query[:1000],
        "contexts": contexts,
    }


def build_revenue_findings(evidence, rag_context):
    revenue_evidence = [item for item in evidence if item.get("domain") == "revenue_resilience"]
    supported = [item for item in revenue_evidence if item.get("evidence_type") == "fact" and item.get("status") in {"supported", "partially_supported"}]
    if supported:
        evidence_ids = [item["evidence_id"] for item in supported]
        avg_confidence = sum(item["confidence"] for item in supported) / len(supported)
        finding = {
            "finding_id": "F-001",
            "domain": "revenue_resilience",
            "finding": "Public search results surfaced revenue-resilience signals that should be reviewed before drawing conclusions about funding mix or concentration.",
            "evidence_ids": evidence_ids,
            "finding_type": "observed",
            "confidence": round(min(avg_confidence, 0.72), 2),
            "requires_validation": True,
            "validation_question": "Which revenue sources are material, recurring, or concentrated in the current financial year?",
        }
    else:
        evidence_ids = [item["evidence_id"] for item in revenue_evidence]
        finding = {
            "finding_id": "F-001",
            "domain": "revenue_resilience",
            "finding": "Public search did not provide enough evidence to assess revenue resilience.",
            "evidence_ids": evidence_ids,
            "finding_type": "unknown",
            "confidence": 0.35,
            "requires_validation": True,
            "validation_question": "What are the organization's main revenue sources and how concentrated are they?",
        }
    finding["rag_context_ids"] = [item["context_id"] for item in rag_context.get("contexts", [])]
    finding["limitations"] = [
        "No revenue numbers are inferred from search metadata.",
        "Missing financial evidence remains unknown rather than negative.",
    ]
    return [finding]


def run_vertical_slice(args):
    run_context = load_json(args.input)
    if args.org_name:
        run_context["organization"]["name"] = args.org_name
    if args.website:
        run_context["organization"]["website"] = args.website
    if args.country:
        run_context["organization"]["country"] = args.country
    if args.run_id:
        run_context["run_id"] = args.run_id

    query = build_search_query(run_context, args.query)
    errors = []
    if args.simulate_failure == "empty_search":
        search_payload = {"provider": "simulated_empty_search", "query": query, "search_url": None, "raw_result_count": 0, "results": []}
        controlled_state = "empty_search"
    else:
        controlled_state = "ok"
        try:
            search_payload = search_web(query, args.max_results, args.timeout)
            if not search_payload["results"]:
                controlled_state = "empty_search"
        except Exception as exc:
            search_payload = {"provider": "no_provider_success", "query": query, "search_url": None, "raw_result_count": 0, "results": []}
            errors.append({"stage": "21_WEB_SEARCH", "error_type": type(exc).__name__, "message": str(exc)})
            controlled_state = "provider_failure"

    sources = normalize_sources(search_payload, run_context)
    evidence = extract_evidence(run_context, sources)
    corpus = load_json(args.corpus)
    rag_context = retrieve_rag_context(evidence, corpus)
    findings = build_revenue_findings(evidence, rag_context)
    unknowns = []
    if not sources:
        unknowns.append({"unknown_id": "UNK-001", "domain": "revenue_resilience", "description": "No public search results were returned.", "evidence_ids": [item["evidence_id"] for item in evidence]})
    if findings[0]["requires_validation"]:
        unknowns.append({"unknown_id": f"UNK-{len(unknowns) + 1:03d}", "domain": "revenue_resilience", "description": "Revenue concentration and recurrence cannot be determined from the P0 public search slice alone.", "evidence_ids": findings[0]["evidence_ids"]})

    output = {
        "input": run_context,
        "execution_path": [
            "21_WEB_SEARCH",
            "30_EVIDENCE_PIPELINE",
            "40_RAG_RETRIEVAL_PIPELINE",
            "51_REVENUE_RESILIENCE_AGENT",
        ],
        "controlled_state": controlled_state,
        "search": search_payload,
        "sources": sources,
        "evidence": evidence,
        "rag_context": rag_context,
        "findings": findings,
        "paola_track_output": {
            "run_context": run_context,
            "sources": sources,
            "evidence": evidence,
            "findings": findings,
            "unknowns": unknowns,
            "contradictions": [],
            "rag_metadata": {
                "retrieval_run_id": rag_context["retrieval_run_id"],
                "domains": ["revenue_resilience"],
                "retrieved_context_ids": [item["context_id"] for item in rag_context.get("contexts", [])],
            },
        },
        "errors": errors,
    }
    return output


def main():
    parser = argparse.ArgumentParser(description="Run Paola P0 vertical slice without storing secrets.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    parser.add_argument("--org-name")
    parser.add_argument("--website")
    parser.add_argument("--country")
    parser.add_argument("--run-id", default="RUN-PAOLA-P0-001")
    parser.add_argument("--query")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--simulate-failure", choices=["empty_search"])
    parser.add_argument("--output")
    args = parser.parse_args()

    output = run_vertical_slice(args)
    payload = json.dumps(output, indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if output["controlled_state"] in {"ok", "empty_search", "provider_failure"} else 1


if __name__ == "__main__":
    sys.exit(main())
