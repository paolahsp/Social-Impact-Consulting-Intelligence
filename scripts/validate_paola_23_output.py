import argparse
import json
import re
import sys
from pathlib import Path


ALLOWED_STATES = {
    "success",
    "partial_success",
    "no_documents_found",
    "unsupported_document",
    "request_failure",
}
ALLOWED_DOCUMENT_TYPES = {
    "annual_report",
    "impact_report",
    "financial_report",
    "audited_financial_statement",
    "program_report",
    "strategy_document",
    "public_registry_document",
    "other_public_document",
}
ALLOWED_AUTHORITY = {"official", "registry", "independent", "media", "unknown", None}
SOURCE_ID = re.compile(r"^SRC-DOC-\d{3}$")
DOCUMENT_ID = re.compile(r"^DOC-\d{3}$")


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def validate(payload):
    errors = []
    state = payload.get("controlled_state")
    documents = payload.get("documents")
    sources = payload.get("sources")
    run_context = payload.get("run_context")
    reported_errors = payload.get("errors")

    require(state in ALLOWED_STATES, f"invalid controlled_state: {state!r}", errors)
    require(isinstance(run_context, dict), "run_context must be an object", errors)
    require(isinstance(documents, list), "documents must be an array", errors)
    require(isinstance(sources, list), "sources must be an array", errors)
    require(isinstance(reported_errors, list), "errors must be an array", errors)
    require(payload.get("extraction_provider") == "jina_reader", "extraction_provider must be jina_reader", errors)
    require(isinstance(payload.get("candidates_attempted"), int), "candidates_attempted must be an integer", errors)

    if not isinstance(documents, list) or not isinstance(sources, list):
        return errors

    source_ids = []
    document_ids = []
    source_by_id = {}
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        require(isinstance(source, dict), f"{prefix} must be an object", errors)
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        source_ids.append(source_id)
        source_by_id[source_id] = source
        require(isinstance(source_id, str) and SOURCE_ID.match(source_id), f"{prefix}.source_id is invalid", errors)
        require(isinstance(source.get("title"), str) and source["title"].strip(), f"{prefix}.title is required", errors)
        require(isinstance(source.get("url"), str) and source["url"].startswith(("http://", "https://")), f"{prefix}.url is invalid", errors)
        require(source.get("document_type") in ALLOWED_DOCUMENT_TYPES, f"{prefix}.document_type is invalid", errors)
        require(source.get("authority_level") in ALLOWED_AUTHORITY, f"{prefix}.authority_level is invalid", errors)
        require(isinstance(source.get("is_official"), bool), f"{prefix}.is_official must be boolean", errors)
        require(source.get("discovered_by") in {"web_search", "website_extraction", "public_data"}, f"{prefix}.discovered_by is invalid", errors)
        require(isinstance(source.get("useful_sections"), list), f"{prefix}.useful_sections must be an array", errors)

    for index, document in enumerate(documents):
        prefix = f"documents[{index}]"
        require(isinstance(document, dict), f"{prefix} must be an object", errors)
        if not isinstance(document, dict):
            continue
        document_id = document.get("document_id")
        document_ids.append(document_id)
        source_id = document.get("source_id")
        require(isinstance(document_id, str) and DOCUMENT_ID.match(document_id), f"{prefix}.document_id is invalid", errors)
        require(source_id in source_by_id, f"{prefix}.source_id is not traceable to sources", errors)
        require(document.get("document_type") in ALLOWED_DOCUMENT_TYPES, f"{prefix}.document_type is invalid", errors)
        require(isinstance(document.get("is_official"), bool), f"{prefix}.is_official must be boolean", errors)
        require(isinstance(document.get("file_type"), str) and document["file_type"], f"{prefix}.file_type is required", errors)
        sections = document.get("sections")
        require(isinstance(sections, list) and 1 <= len(sections) <= 8, f"{prefix}.sections must contain 1-8 sections", errors)
        if isinstance(sections, list):
            for section_index, section in enumerate(sections):
                section_prefix = f"{prefix}.sections[{section_index}]"
                require(isinstance(section, dict), f"{section_prefix} must be an object", errors)
                if isinstance(section, dict):
                    require(isinstance(section.get("section_type"), str) and section["section_type"], f"{section_prefix}.section_type is required", errors)
                    require(isinstance(section.get("text"), str) and 1 <= len(section["text"]) <= 1200, f"{section_prefix}.text must contain 1-1200 characters", errors)
        require("consulting_conclusion" not in document, f"{prefix} must not contain consulting conclusions", errors)
        require("diagnosis" not in document, f"{prefix} must not contain diagnoses", errors)

    require(len(source_ids) == len(set(source_ids)), "source IDs must be unique", errors)
    require(len(document_ids) == len(set(document_ids)), "document IDs must be unique", errors)
    require(len(documents) == len(sources), "each document must have exactly one source", errors)

    if state == "success":
        require(bool(documents), "success requires at least one document", errors)
        require(not reported_errors, "success must not contain errors", errors)
    elif state == "partial_success":
        require(bool(documents), "partial_success requires successful documents", errors)
        require(bool(reported_errors), "partial_success requires explicit errors", errors)
    elif state in {"no_documents_found", "unsupported_document", "request_failure"}:
        require(not documents, f"{state} must not contain fabricated documents", errors)
    if state == "unsupported_document" and isinstance(reported_errors, list):
        require(bool(reported_errors) and all(error.get("error_type") == "unsupported_document" for error in reported_errors), "unsupported_document requires only unsupported_document errors", errors)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Paola workflow 23 output evidence")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Paola 23 output validation FAILED: {path}: {exc}")
            failed = True
            continue
        errors = validate(payload)
        if errors:
            print(f"Paola 23 output validation FAILED: {path}")
            for error in errors:
                print(f"- {error}")
            failed = True
            continue
        print(f"Paola 23 output validation PASSED: {path}")
        print(f"- controlled_state: {payload['controlled_state']}")
        print(f"- candidates_attempted: {payload['candidates_attempted']}")
        print(f"- documents: {len(payload['documents'])}")
        print(f"- sources: {len(payload['sources'])}")
        print(f"- errors: {len(payload['errors'])}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
