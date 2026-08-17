import argparse
import json
import sys
from pathlib import Path


ALLOWED_STATES = {
    "new_source_found",
    "unknown_preserved",
    "no_new_evidence",
    "retry_exhausted",
    "research_failure",
    "invalid_input",
}
BAD_ABSENCE_PHRASES = [
    "does not have",
    "does not measure",
    "failed to",
    "no evidence exists",
    "no impact",
]


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def validate(payload):
    errors = []
    state = payload.get("controlled_state")
    request = payload.get("missing_evidence_request")
    new_sources = payload.get("new_sources")
    new_evidence = payload.get("new_evidence")
    retry_count = payload.get("retry_count")
    max_retries = payload.get("max_retries")
    unknown = payload.get("unknown_marker")

    require(state in ALLOWED_STATES, f"invalid controlled_state: {state!r}", errors)
    require(isinstance(payload.get("run_context"), dict), "run_context must be an object", errors)
    require(isinstance(request, dict), "missing_evidence_request must be an object", errors)
    require(isinstance(new_sources, list), "new_sources must be an array", errors)
    require(isinstance(new_evidence, list), "new_evidence must be an array", errors)
    require(isinstance(retry_count, int) and retry_count >= 0, "retry_count must be a non-negative integer", errors)
    require(isinstance(max_retries, int) and max_retries >= 0, "max_retries must be a non-negative integer", errors)
    require(isinstance(payload.get("research_attempted"), bool), "research_attempted must be boolean", errors)
    require(isinstance(payload.get("rerun_required"), bool), "rerun_required must be boolean", errors)
    require(isinstance(payload.get("requires_client_validation"), bool), "requires_client_validation must be boolean", errors)

    if isinstance(request, dict):
        for key in ["gap_id", "domain", "question", "retry_count", "max_retries", "reason_for_retry"]:
            require(key in request, f"missing_evidence_request.{key} is required", errors)

    if state == "retry_exhausted":
        require(payload.get("research_attempted") is False, "retry_exhausted must not attempt research", errors)
        require(bool(unknown), "retry_exhausted must preserve an unknown marker", errors)
        require(payload.get("requires_client_validation") is True, "retry_exhausted requires client validation", errors)
        if isinstance(request, dict):
            require(retry_count == request.get("retry_count"), "retry_exhausted must not increment retry_count", errors)

    if state == "unknown_preserved":
        require(payload.get("research_attempted") is False, "unknown_preserved must not run broad research", errors)
        require(payload.get("can_public_research_answer") is False, "unknown_preserved must mark can_public_research_answer false", errors)
        require(payload.get("requires_client_validation") is True, "unknown_preserved requires client validation", errors)
        require(bool(unknown), "unknown_preserved must include unknown_marker", errors)
        require(not new_sources, "unknown_preserved must not invent new sources", errors)
        require(not new_evidence, "unknown_preserved must not invent new evidence", errors)

    if state == "new_source_found":
        require(payload.get("research_attempted") is True, "new_source_found requires a research attempt", errors)
        require(payload.get("can_public_research_answer") is True, "new_source_found requires public-answerable decision", errors)
        require(bool(payload.get("targeted_query")), "new_source_found requires targeted_query", errors)
        require(bool(new_sources), "new_source_found requires new_sources", errors)
        require(payload.get("rerun_required") is True, "new_source_found must require rerun", errors)
        require(payload.get("rerun_domain") == request.get("domain"), "rerun_domain must match gap domain", errors)
        require(new_evidence == [], "new_source_found must preserve source/evidence distinction and not fabricate evidence", errors)

    if state == "no_new_evidence":
        require(payload.get("research_attempted") is True, "no_new_evidence requires a research attempt", errors)
        require(bool(unknown), "no_new_evidence must preserve unresolved unknown", errors)
        require(payload.get("requires_client_validation") is True, "no_new_evidence requires client validation", errors)
        require(new_evidence == [], "no_new_evidence must not fabricate evidence", errors)

    if state == "research_failure":
        require(payload.get("research_attempted") is True, "research_failure requires a research attempt", errors)
        require(bool(payload.get("errors")), "research_failure must expose errors", errors)
        require(new_evidence == [], "research_failure must not fabricate evidence", errors)

    if isinstance(new_sources, list):
        seen_urls = set()
        for index, source in enumerate(new_sources):
            prefix = f"new_sources[{index}]"
            require(isinstance(source, dict), f"{prefix} must be an object", errors)
            if not isinstance(source, dict):
                continue
            require(str(source.get("source_id", "")).startswith("SRC-GAP-"), f"{prefix}.source_id must be SRC-GAP-*", errors)
            require(isinstance(source.get("url"), str) and source["url"].startswith(("http://", "https://")), f"{prefix}.url must be HTTP(S)", errors)
            require(source.get("url") not in seen_urls, f"{prefix}.url duplicate within new_sources", errors)
            seen_urls.add(source.get("url"))
            validation = source.get("source_validation")
            require(isinstance(validation, dict), f"{prefix}.source_validation is required", errors)
            if isinstance(validation, dict):
                require(validation.get("is_new_to_run") is True, f"{prefix} must be new to current run", errors)
                require(validation.get("organization_relevant") is True, f"{prefix} must be organization relevant", errors)
                require(validation.get("gap_relevant") is True, f"{prefix} must be gap relevant", errors)
                require("source" in validation.get("source_vs_evidence_note", "").lower(), f"{prefix} must document source/evidence boundary", errors)

    if isinstance(unknown, dict):
        description = unknown.get("description", "")
        require("remains unresolved from the public sources reviewed" in description, "unknown_marker must preserve public-source uncertainty", errors)

    serialized = json.dumps(payload).lower()
    for phrase in BAD_ABSENCE_PHRASES:
        require(phrase not in serialized, f"payload contains prohibited absence-as-failure phrase: {phrase}", errors)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Paola workflow 54 evidence gap output")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Paola 54 output validation FAILED: {path}: {exc}")
            failed = True
            continue
        errors = validate(payload)
        if errors:
            print(f"Paola 54 output validation FAILED: {path}")
            for error in errors:
                print(f"- {error}")
            failed = True
            continue
        print(f"Paola 54 output validation PASSED: {path}")
        print(f"- controlled_state: {payload['controlled_state']}")
        print(f"- research_attempted: {payload['research_attempted']}")
        print(f"- new_sources: {len(payload.get('new_sources', []))}")
        print(f"- retry_count: {payload['retry_count']}/{payload['max_retries']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
