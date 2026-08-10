import json
import sys
from pathlib import Path
from urllib.parse import urlparse


EXPECTED_CONTEXT_KEYS = {
    "mission_signals",
    "program_signals",
    "impact_signals",
    "fundraising_signals",
    "stakeholder_entry_points",
    "report_links",
}


def host(value):
    return (urlparse(value or "").hostname or "").removeprefix("www.").lower()


def validate(payload):
    errors = []
    state = payload.get("controlled_state")
    if state not in {"success", "no_relevant_content", "request_failure"}:
        errors.append(f"unsupported controlled_state: {state!r}")

    sources = payload.get("sources")
    output_errors = payload.get("errors")
    context = payload.get("website_context")
    if not isinstance(sources, list):
        errors.append("sources must be a list")
        sources = []
    if not isinstance(output_errors, list):
        errors.append("errors must be a list")
        output_errors = []
    if not isinstance(context, dict):
        errors.append("website_context must be an object")
        context = {}
    missing_context = EXPECTED_CONTEXT_KEYS - set(context)
    if missing_context:
        errors.append(f"website_context missing keys: {sorted(missing_context)}")

    run_context = payload.get("run_context") or {}
    organization = run_context.get("organization") or {}
    official_host = host(organization.get("website"))

    if state == "success" and not sources:
        errors.append("success requires at least one source")
    if state == "request_failure":
        if sources:
            errors.append("request_failure must not return sources")
        if not output_errors:
            errors.append("request_failure requires at least one error")

    source_ids = set()
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id.startswith("SRC-"):
            errors.append(f"{prefix}.source_id must start with SRC-")
        elif source_id in source_ids:
            errors.append(f"duplicate source_id: {source_id}")
        source_ids.add(source_id)
        if not source.get("title"):
            errors.append(f"{prefix}.title is required")
        source_host = host(source.get("url"))
        if not source_host:
            errors.append(f"{prefix}.url must be an absolute URL")
        if source.get("is_official") is not True:
            errors.append(f"{prefix}.is_official must be true")
        if official_host and source_host != official_host and not source_host.endswith(f".{official_host}"):
            errors.append(f"{prefix}.url is outside the official organization domain")
        if not source.get("useful_content"):
            errors.append(f"{prefix}.useful_content is required")

    serialized_context = json.dumps(context, ensure_ascii=False).lower()
    forbidden_conclusions = [
        "is inefficient",
        "is ineffective",
        "needs consulting",
        "must improve",
        "poor performance",
    ]
    for phrase in forbidden_conclusions:
        if phrase in serialized_context:
            errors.append(f"unsupported consulting conclusion found: {phrase!r}")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_paola_22_output.py <run.json>")
        return 2
    path = Path(sys.argv[1])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Paola 22 output validation FAILED: {exc}")
        return 1
    errors = validate(payload)
    if errors:
        print(f"Paola 22 output validation FAILED: {path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Paola 22 output validation PASSED: {path}")
    print(f"- controlled_state: {payload['controlled_state']}")
    print(f"- pages_attempted: {payload.get('pages_attempted', 0)}")
    print(f"- sources: {len(payload.get('sources', []))}")
    print(f"- errors: {len(payload.get('errors', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
