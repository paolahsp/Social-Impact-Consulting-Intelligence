import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse


ROOT = Path(__file__).resolve().parents[1]

PUBLIC_SIGNALS = [
    "annual report",
    "audited",
    "financial statements",
    "financial report",
    "form 990",
    "990",
    "funding",
    "funder",
    "grant",
    "donor",
    "revenue",
    "public report",
    "impact report",
    "methodology",
    "evaluation",
    "outcome",
    "indicator",
    "kpi",
    "partnership",
    "strategy",
    "program reach",
    "people reached",
    "published",
    "publicly reported",
]
PRIVATE_SIGNALS = [
    "internal",
    "handoff",
    "handoffs",
    "crm",
    "staff workload",
    "response time",
    "unpublished",
    "beneficiary-level private",
    "private data",
    "team sentiment",
    "process friction",
    "after a stakeholder submits",
    "after someone submits",
    "workflow ownership",
    "internal workflow",
    "configuration",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_url(value):
    try:
        parsed = urlparse(str(value or "").strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", "", "")).lower()
    except ValueError:
        return ""


def host(value):
    try:
        return urlparse(value).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def tokens(value):
    return re.findall(r"[a-z0-9]+", str(value or "").lower())


def to_int(value, fallback):
    return value if isinstance(value, int) and value >= 0 else fallback


def normalize_request(payload):
    request = payload.get("missing_evidence_request") or {}
    retry_count = to_int(request.get("retry_count"), 0)
    max_retries = to_int(request.get("max_retries"), 1)
    return {
        "gap_id": request.get("gap_id"),
        "domain": request.get("domain"),
        "question": request.get("question") or request.get("description"),
        "description": request.get("description") or request.get("question"),
        "gap_type": request.get("gap_type") or "unspecified",
        "current_evidence_ids": request.get("current_evidence_ids") if isinstance(request.get("current_evidence_ids"), list) else [],
        "retry_count": retry_count,
        "max_retries": max_retries,
        "reason_for_retry": request.get("reason_for_retry"),
    }


def input_contract(payload):
    nested = payload.get("paola_track_output") or payload
    run_context = nested.get("run_context") or payload.get("run_context") or {}
    sources = nested.get("sources") if isinstance(nested.get("sources"), list) else []
    evidence = nested.get("evidence") if isinstance(nested.get("evidence"), list) else []
    request = normalize_request(payload if "missing_evidence_request" in payload else nested)
    errors = []
    org = run_context.get("organization") or {}
    if not run_context.get("run_id"):
        errors.append({"stage": "INPUT_CONTRACT", "error_type": "invalid_input", "message": "run_context.run_id is required"})
    if not org.get("name") or not org.get("website") or not org.get("country"):
        errors.append({"stage": "INPUT_CONTRACT", "error_type": "invalid_input", "message": "run_context.organization name, website, and country are required"})
    if not request.get("gap_id"):
        errors.append({"stage": "INPUT_CONTRACT", "error_type": "invalid_input", "message": "missing_evidence_request.gap_id is required"})
    if not request.get("domain"):
        errors.append({"stage": "INPUT_CONTRACT", "error_type": "invalid_input", "message": "missing_evidence_request.domain is required"})
    if not request.get("question"):
        errors.append({"stage": "INPUT_CONTRACT", "error_type": "invalid_input", "message": "missing_evidence_request.question or description is required"})
    if not request.get("reason_for_retry"):
        errors.append({"stage": "INPUT_CONTRACT", "error_type": "invalid_input", "message": "reason_for_retry is required"})
    controlled_state = "invalid_input" if errors else ("retry_exhausted" if request["retry_count"] >= request["max_retries"] else "ready")
    return {
        "run_context": run_context,
        "sources": sources,
        "evidence": evidence,
        "missing_evidence_request": request,
        "controlled_state": controlled_state,
        "retry_count": request["retry_count"],
        "max_retries": request["max_retries"],
        "reason_for_retry": request["reason_for_retry"],
        "research_attempted": False,
        "new_sources": [],
        "new_evidence": [],
        "requires_client_validation": False,
        "rerun_required": False,
        "rerun_domain": None,
        "errors": errors,
    }


def mark_unknown(state, reason=None):
    request = state["missing_evidence_request"]
    state["unknown_marker"] = {
        "unknown_id": request.get("gap_id") or "GAP-UNKNOWN",
        "domain": request.get("domain"),
        "description": "The evidence gap remains unresolved from the public sources reviewed.",
        "reason": reason or state.get("reason_for_preserving_unknown") or "Public research cannot reasonably answer this gap.",
        "evidence_ids": request.get("current_evidence_ids") or [],
    }
    state["requires_client_validation"] = True
    state["rerun_required"] = False
    state["rerun_domain"] = None
    state["new_sources"] = state.get("new_sources", [])
    state["new_evidence"] = []


def assess_answerability(state):
    request = state["missing_evidence_request"]
    text = f"{request.get('domain', '')} {request.get('gap_type', '')} {request.get('question', '')} {request.get('description', '')}".lower()
    private_match = next((signal for signal in PRIVATE_SIGNALS if signal in text), None)
    public_match = next((signal for signal in PUBLIC_SIGNALS if signal in text), None)
    answerable = bool(public_match and not private_match)
    state["can_public_research_answer"] = answerable
    state["answerability_state"] = "public_answerable" if answerable else "unknown_preserved"
    state["answerability_reason"] = f"Gap contains public research signal: {public_match}" if answerable else (
        f"Gap appears private/internal: {private_match}" if private_match else "No reliable public research path identified"
    )
    state["reason_for_preserving_unknown"] = None if answerable else "Public research cannot reasonably answer this specific evidence gap."


def unique_words(parts):
    out = []
    seen = set()
    for part in parts:
        for token in re.sub(r"\s+", " ", str(part or "").strip()).split(" "):
            clean = re.sub(r"[^\w.-]", "", token)
            key = clean.lower()
            if clean and key not in seen:
                seen.add(key)
                out.append(clean)
    return " ".join(out)


def build_targeted_query(state):
    org = state["run_context"]["organization"]
    request = state["missing_evidence_request"]
    text = f"{request.get('gap_type', '')} {request.get('question', '')} {request.get('description', '')}".lower()
    hints = "public report source"
    if re.search(r"fund|grant|donor|revenue|financial|990|audited|audit", text):
        hints = "audited financial statements funding concentration annual report form 990"
    elif re.search(r"impact|outcome|methodolog|evaluation|longitudinal|indicator|kpi", text):
        hints = "impact report outcome evaluation methodology longitudinal study indicators"
    elif "partner" in text:
        hints = "public partnership announcement annual report"
    elif "strategy" in text:
        hints = "strategy document strategic plan annual report"
    elif re.search(r"program|reach|people served|people reached", text):
        hints = "program reach annual report public results"
    state["targeted_query"] = unique_words([org.get("name"), org.get("country"), request.get("question"), request.get("gap_type"), hints])
    state["query_strategy"] = {
        "organization_identity": org.get("name"),
        "gap_subject": request.get("question"),
        "source_hint": hints,
    }


def gap_terms(request):
    text = f"{request.get('domain', '')} {request.get('gap_type', '')} {request.get('question', '')} {request.get('description', '')}".lower()
    terms = ["annual", "report", "financial", "funding", "grant", "donor", "revenue", "990", "audit", "audited", "impact", "outcome", "evaluation", "methodology", "indicator", "strategy", "partnership", "program", "reach"]
    return [term for term in terms if term in text]


def validate_search(state, search_output):
    state["retry_count_before_attempt"] = state["retry_count"]
    state["retry_count"] += 1
    state["missing_evidence_request"]["retry_count"] = state["retry_count"]
    state["research_attempted"] = True
    returned_state = search_output.get("controlled_state") or "unknown"
    state["search_controlled_state"] = returned_state
    if returned_state == "request_failure":
        state["controlled_state"] = "research_failure"
        state.setdefault("errors", []).extend(search_output.get("errors", []))
        state["errors"].append({"stage": "TARGETED_RESEARCH", "error_type": "research_failure", "message": "Workflow 21 returned request_failure"})
        return
    existing_urls = {normalize_url(source.get("url")) for source in state.get("sources", [])}
    official_domain = host(state["run_context"]["organization"].get("website", ""))
    org_tokens = [token for token in tokens(state["run_context"]["organization"].get("name")) if len(token) > 2]
    terms = gap_terms(state["missing_evidence_request"])
    new_sources = []
    rejected = []
    for source in search_output.get("sources", []):
        normalized = normalize_url(source.get("url"))
        source_text = f"{source.get('title', '')} {source.get('url', '')} {source.get('search_snippet', '')}".lower()
        source_host = host(source.get("url", ""))
        valid_url = bool(normalized)
        duplicate = valid_url and normalized in existing_urls
        org_relevant = bool((official_domain and source_host.endswith(official_domain)) or any(token in source_text for token in org_tokens))
        gap_relevant = any(term in source_text for term in terms) if terms else False
        if not valid_url or duplicate or not org_relevant or not gap_relevant:
            rejected.append({
                "title": source.get("title"),
                "url": source.get("url"),
                "reason": "invalid_url" if not valid_url else "duplicate_existing_source" if duplicate else "organization_mismatch" if not org_relevant else "gap_mismatch",
            })
            continue
        copied = dict(source)
        copied["source_id"] = f"SRC-GAP-{len(new_sources) + 1:03d}"
        copied["original_source_id"] = source.get("source_id")
        copied["discovered_by"] = "54_EVIDENCE_GAP_RESEARCH"
        copied["targeted_gap_id"] = state["missing_evidence_request"]["gap_id"]
        copied["targeted_query"] = state["targeted_query"]
        copied["source_validation"] = {
            "is_new_to_run": True,
            "organization_relevant": org_relevant,
            "gap_relevant": gap_relevant,
            "source_vs_evidence_note": "New source found; downstream extraction/evidence processing is required before treating the gap as resolved.",
        }
        new_sources.append(copied)
        if len(new_sources) >= 5:
            break
    state["new_sources"] = new_sources
    state["new_evidence"] = []
    state["rejected_sources"] = rejected
    if new_sources:
        state["controlled_state"] = "new_source_found"
        state["requires_client_validation"] = False
        state["rerun_required"] = True
        state["rerun_domain"] = state["missing_evidence_request"]["domain"]
    else:
        state["controlled_state"] = "no_new_evidence"
        mark_unknown(state, "Targeted public research did not identify a new relevant source.")


def output(state):
    return {
        "repository_execution_evidence": {
            "verified_at": "2026-08-13T00:00:00Z",
            "runner": "scripts/paola_54_evidence_gap_test.py",
            "note": "Repository-local deterministic mirror of workflow 54 controller logic; live n8n verification must be recorded separately.",
        },
        "run_context": state.get("run_context"),
        "missing_evidence_request": state.get("missing_evidence_request"),
        "controlled_state": state.get("controlled_state"),
        "can_public_research_answer": bool(state.get("can_public_research_answer")),
        "answerability_reason": state.get("answerability_reason"),
        "targeted_query": state.get("targeted_query"),
        "query_strategy": state.get("query_strategy"),
        "search_controlled_state": state.get("search_controlled_state"),
        "new_sources": state.get("new_sources", []),
        "new_evidence": state.get("new_evidence", []),
        "rejected_sources": state.get("rejected_sources", []),
        "unknown_marker": state.get("unknown_marker"),
        "retry_count": state.get("retry_count"),
        "max_retries": state.get("max_retries"),
        "reason_for_retry": state.get("reason_for_retry"),
        "research_attempted": bool(state.get("research_attempted")),
        "rerun_required": bool(state.get("rerun_required")),
        "rerun_domain": state.get("rerun_domain"),
        "requires_client_validation": bool(state.get("requires_client_validation")),
        "source_evidence_boundary": "A new source is not treated as gap-resolving evidence until downstream extraction/evidence processing validates attributable facts.",
        "errors": state.get("errors", []),
    }


def analyze(payload, search_output=None):
    state = input_contract(payload)
    if state["controlled_state"] == "invalid_input":
        return output(state)
    if state["controlled_state"] == "retry_exhausted":
        mark_unknown(state, "retry_count is greater than or equal to max_retries; no additional research attempted.")
        return output(state)
    assess_answerability(state)
    if not state["can_public_research_answer"]:
        state["controlled_state"] = "unknown_preserved"
        mark_unknown(state, state["reason_for_preserving_unknown"])
        return output(state)
    build_targeted_query(state)
    validate_search(state, search_output or {"controlled_state": "empty_search", "sources": [], "errors": []})
    return output(state)


def base_run_context(run_id):
    return {
        "run_id": run_id,
        "organization": {"name": "GiveDirectly", "website": "https://www.givedirectly.org", "country": "United States", "mission_area": None},
        "current_challenge": "Resolve evidence gap",
        "uploaded_document_refs": [],
        "status": "created",
        "started_at": "2026-08-13T00:00:00Z",
        "errors": [],
    }


def answerable_payload():
    return {
        "run_context": base_run_context("RUN-LOCAL-54-GIVEDIRECTLY-ANSWERABLE"),
        "sources": [{
            "source_id": "SRC-WEB-001",
            "title": "GiveDirectly home page",
            "url": "https://www.givedirectly.org/",
            "source_type": "official_website_home",
            "publisher": "GiveDirectly",
            "publication_date": None,
            "retrieved_at": "2026-08-13T00:00:00Z",
            "authority_level": "official",
            "freshness": "unknown",
            "is_official": True,
        }],
        "evidence": [],
        "missing_evidence_request": {
            "gap_id": "GAP-REV-001",
            "domain": "revenue_resilience",
            "question": "Can funding concentration be determined from additional public financial information?",
            "gap_type": "public_financial_information",
            "current_evidence_ids": [],
            "retry_count": 0,
            "max_retries": 1,
            "reason_for_retry": "Existing evidence does not show funding concentration.",
        },
    }


def internal_payload():
    return {
        "run_context": base_run_context("RUN-LOCAL-54-INTERNAL-GAP"),
        "sources": [],
        "evidence": [],
        "missing_evidence_request": {
            "gap_id": "GAP-OPS-001",
            "domain": "operations_cx",
            "question": "What happens internally after a stakeholder submits an application form?",
            "gap_type": "internal_handoff",
            "current_evidence_ids": [],
            "retry_count": 0,
            "max_retries": 1,
            "reason_for_retry": "Public sources do not describe the internal follow-up process.",
        },
    }


def retry_payload():
    payload = answerable_payload()
    payload["run_context"]["run_id"] = "RUN-LOCAL-54-RETRY-EXHAUSTED"
    payload["missing_evidence_request"]["gap_id"] = "GAP-REV-RETRY"
    payload["missing_evidence_request"]["retry_count"] = 1
    payload["missing_evidence_request"]["max_retries"] = 1
    return payload


def empty_search_payload():
    payload = answerable_payload()
    payload["run_context"]["run_id"] = "RUN-LOCAL-54-EMPTY-SEARCH"
    payload["missing_evidence_request"]["gap_id"] = "GAP-REV-EMPTY"
    return payload


def p0_search_output():
    data = load_json(ROOT / "runs" / "paola_p0_givedirectly.json")
    return {
        "controlled_state": data.get("controlled_state"),
        "sources": data.get("sources", []),
        "search": data.get("search"),
        "errors": data.get("errors", []),
    }


def main():
    parser = argparse.ArgumentParser(description="Run local Paola 54 evidence gap fixtures")
    parser.add_argument("--write-runs", action="store_true")
    args = parser.parse_args()
    outputs = {
        "paola_54_givedirectly_answerable_gap.json": analyze(answerable_payload(), p0_search_output()),
        "paola_54_internal_gap.json": analyze(internal_payload()),
        "paola_54_retry_exhausted.json": analyze(retry_payload()),
        "paola_54_empty_search.json": analyze(empty_search_payload(), {"controlled_state": "empty_search", "sources": [], "errors": []}),
    }
    if args.write_runs:
        for filename, payload in outputs.items():
            (ROOT / "runs" / filename).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for filename, payload in outputs.items():
        print(
            f"{filename}: {payload['controlled_state']}, research_attempted={payload['research_attempted']}, "
            f"new_sources={len(payload['new_sources'])}, retry={payload['retry_count']}/{payload['max_retries']}"
        )


if __name__ == "__main__":
    main()
