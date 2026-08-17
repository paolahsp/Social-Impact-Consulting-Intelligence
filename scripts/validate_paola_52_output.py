import argparse
import json
import re
import sys
from pathlib import Path


ALLOWED_STATES = {"success", "insufficient_evidence", "request_failure"}
ALLOWED_LEVELS = {
    "activity",
    "output",
    "outcome",
    "impact",
    "indicator",
    "unknown",
    "impact_claim",
    "impact_evidence",
}
ALLOWED_FINDING_TYPES = {"observed", "inferred", "hypothesis", "unknown"}
BAD_ABSENCE_PHRASES = [
    "does not measure",
    "has weak impact measurement",
    "does not have long-term outcomes",
    "failed to measure",
    "no impact",
]


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def validate(payload):
    errors = []
    state = payload.get("controlled_state")
    evidence = payload.get("impact_evidence")
    characteristics = payload.get("evidence_characteristics")
    findings = payload.get("findings")
    unknowns = payload.get("unknowns")
    sources = payload.get("sources")

    require(state in ALLOWED_STATES, f"invalid controlled_state: {state!r}", errors)
    require(isinstance(payload.get("run_context"), dict), "run_context must be an object", errors)
    require(isinstance(sources, list), "sources must be an array", errors)
    require(isinstance(evidence, list), "impact_evidence must be an array", errors)
    require(isinstance(characteristics, list), "evidence_characteristics must be an array", errors)
    require(isinstance(findings, list), "findings must be an array", errors)
    require(isinstance(unknowns, list), "unknowns must be an array", errors)
    if not all(isinstance(level, str) and level in ALLOWED_LEVELS for level in payload.get("impact_taxonomy", [])):
        errors.append("impact_taxonomy contains an unbounded level")

    source_ids = {source.get("source_id") for source in sources or [] if isinstance(source, dict)}
    evidence_ids = set()
    characteristics_by_id = {}

    for index, item in enumerate(evidence or []):
        prefix = f"impact_evidence[{index}]"
        require(isinstance(item, dict), f"{prefix} must be an object", errors)
        if not isinstance(item, dict):
            continue
        evidence_id = item.get("evidence_id")
        evidence_ids.add(evidence_id)
        level = item.get("impact_classification", {}).get("level")
        require(isinstance(evidence_id, str) and evidence_id.startswith("EV-"), f"{prefix}.evidence_id is invalid", errors)
        require(level in ALLOWED_LEVELS, f"{prefix}.impact_classification.level is invalid: {level!r}", errors)
        refs = item.get("source_ids")
        require(isinstance(refs, list) and refs and any(ref in source_ids for ref in refs), f"{prefix}.source_ids must reference known sources", errors)
        require(item.get("evidence_type") in {"fact", "inference", "hypothesis", "unknown"}, f"{prefix}.evidence_type is invalid", errors)
        require(item.get("status") in {"supported", "partially_supported", "contradicted", "insufficient_evidence", "unknown"}, f"{prefix}.status is invalid", errors)
        if level == "impact_claim":
            require(item.get("impact_classification", {}).get("signal_nature") == "claim", f"{prefix} impact_claim must be marked as claim", errors)

    for index, item in enumerate(characteristics or []):
        prefix = f"evidence_characteristics[{index}]"
        require(isinstance(item, dict), f"{prefix} must be an object", errors)
        if not isinstance(item, dict):
            continue
        evidence_id = item.get("evidence_id")
        characteristics_by_id[evidence_id] = item
        require(evidence_id in evidence_ids, f"{prefix}.evidence_id is not traceable", errors)
        level = item.get("impact_level")
        require(level in ALLOWED_LEVELS, f"{prefix}.impact_level is invalid", errors)
        for key in [
            "measurement_presence",
            "timeframe_visibility",
            "methodology_visibility",
            "denominator_sample_visibility",
            "baseline_visibility",
            "target_visibility",
        ]:
            require(isinstance(item.get(key), bool), f"{prefix}.{key} must be boolean", errors)
        if level == "impact":
            require(item.get("measurement_presence") or item.get("methodology_visibility"), f"{prefix} escalates to impact without measurement or methodology signal", errors)
        if item.get("baseline_visibility"):
            linked = next((ev for ev in evidence or [] if ev.get("evidence_id") == evidence_id), {})
            require(re.search(r"\bbaseline\b", linked.get("claim", ""), re.IGNORECASE), f"{prefix} invents baseline visibility", errors)

    for index, finding in enumerate(findings or []):
        prefix = f"findings[{index}]"
        require(isinstance(finding, dict), f"{prefix} must be an object", errors)
        if not isinstance(finding, dict):
            continue
        require(isinstance(finding.get("finding_id"), str) and finding["finding_id"].startswith("F-"), f"{prefix}.finding_id is invalid", errors)
        require(finding.get("domain") == "impact_evidence", f"{prefix}.domain must be impact_evidence", errors)
        require(finding.get("finding_type") in ALLOWED_FINDING_TYPES, f"{prefix}.finding_type is invalid", errors)
        refs = finding.get("evidence_ids")
        require(isinstance(refs, list), f"{prefix}.evidence_ids must be an array", errors)
        if state == "success":
            require(bool(refs), f"{prefix}.evidence_ids must not be empty in success state", errors)
        require(all(ref in evidence_ids for ref in refs), f"{prefix}.evidence_ids contains unknown references", errors)
        require(isinstance(finding.get("requires_validation"), bool), f"{prefix}.requires_validation must be boolean", errors)
        require("validation_question" in finding, f"{prefix}.validation_question is required", errors)
        lower = str(finding.get("finding", "")).lower()
        for phrase in BAD_ABSENCE_PHRASES:
            require(phrase not in lower, f"{prefix} contains prohibited absence-as-failure phrase: {phrase}", errors)

    for index, unknown in enumerate(unknowns or []):
        prefix = f"unknowns[{index}]"
        require(isinstance(unknown, dict), f"{prefix} must be an object", errors)
        if isinstance(unknown, dict):
            require(unknown.get("domain") == "impact_evidence", f"{prefix}.domain must be impact_evidence", errors)
            require(isinstance(unknown.get("description"), str) and unknown["description"], f"{prefix}.description is required", errors)
            require("not identified in the public sources reviewed" in unknown["description"] or "could not be determined" in unknown["description"] or "not identified in the structured inputs reviewed" in unknown["description"], f"{prefix}.description must preserve public-evidence uncertainty", errors)
            require(isinstance(unknown.get("evidence_ids"), list), f"{prefix}.evidence_ids must be an array", errors)

    if state == "success":
        require(bool(evidence), "success requires impact_evidence", errors)
        require(bool(findings), "success requires findings", errors)
        require(bool(unknowns), "success should preserve explicit unknowns", errors)
    if state == "insufficient_evidence":
        require(not evidence, "insufficient_evidence must not fabricate impact_evidence", errors)
        require(bool(unknowns), "insufficient_evidence must preserve unknowns", errors)
        require(all(finding.get("finding_type") == "unknown" for finding in findings or []), "insufficient_evidence findings must be unknown", errors)

    serialized = json.dumps(payload).lower()
    for phrase in BAD_ABSENCE_PHRASES:
        require(phrase not in serialized, f"payload contains prohibited phrase: {phrase}", errors)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Paola workflow 52 impact evidence output")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Paola 52 output validation FAILED: {path}: {exc}")
            failed = True
            continue
        errors = validate(payload)
        if errors:
            print(f"Paola 52 output validation FAILED: {path}")
            for error in errors:
                print(f"- {error}")
            failed = True
            continue
        print(f"Paola 52 output validation PASSED: {path}")
        print(f"- controlled_state: {payload['controlled_state']}")
        print(f"- impact_evidence: {len(payload.get('impact_evidence', []))}")
        print(f"- findings: {len(payload.get('findings', []))}")
        print(f"- unknowns: {len(payload.get('unknowns', []))}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
