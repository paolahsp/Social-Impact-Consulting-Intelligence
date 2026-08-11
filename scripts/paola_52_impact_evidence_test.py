import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPACT_TERMS = [
    "impact",
    "outcome",
    "beneficiar",
    "recipient",
    "household",
    "participant",
    "people reached",
    "transfer",
    "poverty",
    "mission",
    "program",
    "programme",
    "kpi",
    "indicator",
    "research",
    "evaluation",
    "follow-up",
    "follow up",
]
TAXONOMY = [
    "activity",
    "output",
    "outcome",
    "impact",
    "indicator",
    "unknown",
    "impact_claim",
    "impact_evidence",
]


def has_impact_signal(value):
    text = str(value or "").lower()
    return any(term in text for term in IMPACT_TERMS)


def split_sentences(value):
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]


def level_for(claim):
    text = str(claim or "").lower()
    has_number = re.search(r"\b\d+([,.]\d+)?%?\b", text) is not None
    if re.search(r"(mission|aim|goal|vision).{0,80}(reduce poverty|improve|impact|change lives|alleviate suffering)", text):
        return "impact_claim"
    if re.search(r"(long[- ]term|sustain|five years|years later|poverty reduction measured|counterfactual|attribut)", text) and re.search(r"(impact|outcome|effect)", text):
        return "impact"
    if re.search(r"(improved|increased|decreased|reduced|changed|outcome|test scores|health|income|wellbeing|well-being)", text) and (has_number or re.search(r"survey|study|evaluation|research", text)):
        return "outcome"
    if re.search(r"(kpi|indicator|metric|measure|measurement|rate|percent|percentage|baseline|target)", text):
        return "indicator"
    if re.search(r"(recipient|household|participant|people reached|operates in|countries|transfer sizes|attended|served|reached)", text):
        return "output"
    if re.search(r"(provides|offers|identifies|informs|helps|register|sends|follows up|deliver|conducts|runs|program|programme|service)", text):
        return "activity"
    return "unknown"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_input(payload):
    nested = payload.get("paola_track_output") or payload
    return {
        "run_context": nested.get("run_context") or payload.get("run_context") or {},
        "sources": nested.get("sources") or [],
        "evidence": nested.get("evidence") or [],
        "documents": nested.get("documents") or [],
        "rag_context": nested.get("rag_context") or payload.get("rag_context") or {"contexts": []},
        "errors": [],
        "impact_taxonomy": TAXONOMY,
    }


def filter_impact_evidence(state):
    source_ids = {source.get("source_id") for source in state["sources"]}
    impact_evidence = []
    for evidence in state["evidence"]:
        refs = [source_id for source_id in evidence.get("source_ids", []) if source_id in source_ids]
        if refs and has_impact_signal(f"{evidence.get('domain', '')} {evidence.get('claim', '')}"):
            copied = dict(evidence)
            copied["source_ids"] = refs
            copied["impact_signal_source"] = "evidence_ledger"
            impact_evidence.append(copied)
    for document in state["documents"]:
        source_id = document.get("source_id")
        if source_id not in source_ids:
            continue
        for section in document.get("sections", []):
            if str(section.get("section_type", "")).lower() != "impact":
                continue
            if not has_impact_signal(f"{section.get('section_type', '')} {section.get('text', '')}"):
                continue
            selected = [sentence for sentence in split_sentences(section.get("text")) if has_impact_signal(sentence)]
            selected = [
                sentence
                for sentence in selected
                if not re.search(r"financial statements|net assets|receivable|inventory|fair value|cash flows|auditors", sentence, re.IGNORECASE)
            ]
            for sentence in selected[:4]:
                if len(impact_evidence) >= 12:
                    break
                impact_evidence.append(
                    {
                        "evidence_id": f"EV-IMP-{len(impact_evidence) + 1:03d}",
                        "run_id": state["run_context"]["run_id"],
                        "claim": sentence[:360],
                        "source_ids": [source_id],
                        "domain": "impact_evidence",
                        "evidence_type": "fact",
                        "confidence": 0.72 if document.get("is_official") else 0.58,
                        "status": "supported",
                        "contradiction_ids": [],
                        "requires_validation": False,
                        "impact_signal_source": "document_section",
                        "document_id": document.get("document_id"),
                        "document_type": document.get("document_type"),
                        "section_type": section.get("section_type"),
                    }
                )
    state["impact_evidence"] = impact_evidence
    state["controlled_state"] = "impact_evidence_available" if impact_evidence else "insufficient_evidence"


def classify(state):
    for evidence in state.get("impact_evidence", []):
        level = level_for(evidence["claim"])
        evidence["impact_classification"] = {
            "level": level,
            "signal_nature": "claim" if level == "impact_claim" else "evidence_signal",
            "taxonomy_version": "impact-taxonomy-v1",
        }


def assess(state):
    sources = {source.get("source_id"): source for source in state["sources"]}
    characteristics = []
    for evidence in state.get("impact_evidence", []):
        source = sources.get((evidence.get("source_ids") or [None])[0], {})
        claim = evidence.get("claim", "")
        measurement = re.search(r"\b\d+([,.]\d+)?%?\b", claim) is not None
        lower = claim.lower()
        characteristics.append(
            {
                "evidence_id": evidence["evidence_id"],
                "impact_level": evidence["impact_classification"]["level"],
                "source_authority": source.get("authority_level") or "unknown",
                "specificity": "medium" if measurement or len(claim) > 120 else "low",
                "measurement_presence": measurement,
                "timeframe_visibility": re.search(r"\b(20\d{2}|19\d{2}|year|month|quarter|five years|long[- ]term)\b", lower) is not None,
                "methodology_visibility": re.search(r"\b(method|survey|study|evaluation|research|random|sample|baseline|follow[- ]up)\b", lower) is not None,
                "denominator_sample_visibility": re.search(r"\b(sample|n=|participants|households|recipients)\b", lower) is not None and measurement,
                "baseline_visibility": "baseline" in lower,
                "target_visibility": "target" in lower,
                "attribution_limitations": "Attribution cannot be assessed beyond what the cited public evidence states."
                if evidence["impact_classification"]["level"] in {"impact", "outcome"}
                else None,
            }
        )
    state["evidence_characteristics"] = characteristics


def detect_unknowns(state):
    ids = [evidence["evidence_id"] for evidence in state.get("impact_evidence", [])]
    if not ids:
        state["unknowns"] = [
            {
                "unknown_id": "UNK-IMP-001",
                "domain": "impact_evidence",
                "description": "Impact-related public evidence was not identified in the structured inputs reviewed.",
                "evidence_ids": [],
            }
        ]
        return
    levels = {evidence["impact_classification"]["level"] for evidence in state["impact_evidence"]}
    checks = state.get("evidence_characteristics", [])
    descriptions = []
    if "outcome" not in levels:
        descriptions.append("Outcome evidence was not identified in the public sources reviewed.")
    if "impact" not in levels:
        descriptions.append("Long-term impact evidence was not identified in the public sources reviewed.")
    if not any(item["methodology_visibility"] for item in checks):
        descriptions.append("Methodology visibility could not be determined from the public evidence reviewed.")
    if not any(item["baseline_visibility"] for item in checks):
        descriptions.append("Baseline visibility could not be determined from the public evidence reviewed.")
    if not any(item["denominator_sample_visibility"] for item in checks):
        descriptions.append("Denominator or sample visibility could not be determined from the public evidence reviewed.")
    if not any(item["target_visibility"] for item in checks):
        descriptions.append("Target visibility could not be determined from the public evidence reviewed.")
    state["unknowns"] = [
        {
            "unknown_id": f"UNK-IMP-{index + 1:03d}",
            "domain": "impact_evidence",
            "description": description,
            "evidence_ids": ids,
        }
        for index, description in enumerate(descriptions)
    ]


def average(values):
    return round(sum(values) / len(values), 2) if values else 0.35


def evidence_ids_for(evidence, levels):
    return [item["evidence_id"] for item in evidence if item.get("impact_classification", {}).get("level") in levels]


def build_findings(state):
    evidence = state.get("impact_evidence", [])
    if not evidence:
        state["controlled_state"] = "insufficient_evidence"
        state["findings"] = [
            {
                "finding_id": "F-IMP-001",
                "domain": "impact_evidence",
                "finding": "Structured inputs did not contain enough impact-related public evidence to support meaningful impact findings.",
                "evidence_ids": [],
                "finding_type": "unknown",
                "confidence": 0.35,
                "requires_validation": True,
                "validation_question": "Which public sources should be reviewed to understand activities, outputs, outcomes, and impact claims?",
            }
        ]
        return
    findings = []
    activity_ids = evidence_ids_for(evidence, {"activity"})
    output_ids = evidence_ids_for(evidence, {"output", "indicator"})
    claim_ids = evidence_ids_for(evidence, {"impact_claim"})
    outcome_ids = evidence_ids_for(evidence, {"outcome"})
    impact_ids = evidence_ids_for(evidence, {"impact"})

    def add(finding, evidence_ids, finding_type="observed", confidence=None, requires_validation=False, validation_question=None):
        findings.append(
            {
                "finding_id": f"F-IMP-{len(findings) + 1:03d}",
                "domain": "impact_evidence",
                "finding": finding,
                "evidence_ids": evidence_ids,
                "finding_type": finding_type,
                "confidence": confidence if confidence is not None else average([item.get("confidence", 0.5) for item in evidence if item["evidence_id"] in evidence_ids]),
                "requires_validation": requires_validation,
                "validation_question": validation_question,
            }
        )

    if activity_ids:
        add("Program activities or service delivery steps are publicly described in the reviewed sources.", activity_ids)
    if output_ids:
        add("Public reporting reviewed contains output or reach signals.", output_ids)
    if claim_ids:
        add(
            "An impact-oriented claim or mission statement is publicly stated, but it is not treated as proof that long-term impact occurred.",
            claim_ids,
            requires_validation=True,
            validation_question="What outcome or longitudinal evidence supports this public impact claim?",
        )
    if outcome_ids:
        add("Outcome evidence is publicly reported in the reviewed sources.", outcome_ids)
    if impact_ids:
        add(
            "Long-term impact evidence is publicly reported in the reviewed sources.",
            impact_ids,
            requires_validation=True,
            validation_question="How should attribution limitations be interpreted for the long-term impact evidence?",
        )
    if len(activity_ids) + len(output_ids) > len(outcome_ids) + len(impact_ids) and not (outcome_ids or impact_ids):
        add(
            "Public reporting reviewed emphasizes activities, outputs, or claims more clearly than measured outcomes or long-term impact evidence.",
            [item["evidence_id"] for item in evidence],
            finding_type="inferred",
            confidence=0.56,
            requires_validation=True,
            validation_question="Are measured outcomes or long-term follow-up results available outside the public sources reviewed?",
        )
    if state.get("unknowns"):
        add(
            "Some impact evidence characteristics remain unknown from the public sources reviewed.",
            [item["evidence_id"] for item in evidence],
            finding_type="unknown",
            confidence=0.5,
            requires_validation=True,
            validation_question="Which measurement details, if any, can the organization validate directly?",
        )
    state["controlled_state"] = "success"
    state["findings"] = findings


def traceability_check(state):
    if state.get("controlled_state") == "request_failure":
        return
    source_ids = {source.get("source_id") for source in state["sources"]}
    evidence_ids = {evidence.get("evidence_id") for evidence in state.get("impact_evidence", [])}
    errors = state.setdefault("errors", [])
    for evidence in state.get("impact_evidence", []):
        if not any(source_id in source_ids for source_id in evidence.get("source_ids", [])):
            errors.append({"stage": "TRACEABILITY_CHECK", "error_type": "untraceable_evidence", "message": f"{evidence.get('evidence_id')} does not reference a known source"})
    for finding in state.get("findings", []):
        finding["evidence_ids"] = [evidence_id for evidence_id in finding.get("evidence_ids", []) if evidence_id in evidence_ids]
        if finding["finding_type"] != "unknown" and not finding["evidence_ids"]:
            errors.append({"stage": "TRACEABILITY_CHECK", "error_type": "untraceable_finding", "message": f"{finding.get('finding_id')} has no valid evidence references"})
    if errors:
        state["controlled_state"] = "request_failure"


def analyze(payload):
    state = normalize_input(payload)
    if not state["run_context"].get("run_id"):
        state["controlled_state"] = "request_failure"
        state["errors"].append({"stage": "INPUT_CONTRACT", "error_type": "invalid_input", "message": "run_context.run_id is required"})
    else:
        filter_impact_evidence(state)
        if state["controlled_state"] == "impact_evidence_available":
            classify(state)
            assess(state)
        detect_unknowns(state)
        build_findings(state)
        traceability_check(state)
    return {
        "repository_execution_evidence": {
            "verified_at": "2026-08-11T00:00:00Z",
            "runner": "scripts/paola_52_impact_evidence_test.py",
            "note": "Repository-local deterministic mirror of the n8n Code-node logic."
        },
        "run_context": state.get("run_context"),
        "controlled_state": state.get("controlled_state"),
        "impact_taxonomy": TAXONOMY,
        "sources": state.get("sources", []),
        "evidence": state.get("evidence", []),
        "impact_evidence": state.get("impact_evidence", []),
        "evidence_characteristics": state.get("evidence_characteristics", []),
        "findings": state.get("findings", []),
        "unknowns": state.get("unknowns", []),
        "contradictions": [],
        "rag_metadata": {
            "retrieval_run_id": state.get("rag_context", {}).get("retrieval_run_id"),
            "domains": [state.get("rag_context", {}).get("domain")] if state.get("rag_context", {}).get("domain") else [],
            "retrieved_context_ids": [ctx.get("context_id") for ctx in state.get("rag_context", {}).get("contexts", [])],
        },
        "guardrails": [
            "Activity, output, outcome, impact, indicator, and unknown are not interchangeable.",
            "Absence of public evidence is not treated as evidence of organizational absence.",
            "RAG context cannot add organization-specific facts.",
        ],
        "errors": state.get("errors", []),
    }


def insufficient_payload():
    p0 = load_json(ROOT / "runs" / "paola_p0_givedirectly.json")
    return p0.get("paola_track_output", p0)


def main():
    parser = argparse.ArgumentParser(description="Run local Paola 52 impact evidence fixtures")
    parser.add_argument("--write-runs", action="store_true")
    args = parser.parse_args()

    outputs = {
        "paola_52_givedirectly.json": analyze(load_json(ROOT / "runs" / "paola_23_givedirectly.json")),
        "paola_52_insufficient_evidence.json": analyze(insufficient_payload()),
    }
    if args.write_runs:
        for filename, payload in outputs.items():
            (ROOT / "runs" / filename).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for filename, payload in outputs.items():
        print(f"{filename}: {payload['controlled_state']}, findings={len(payload['findings'])}, impact_evidence={len(payload['impact_evidence'])}, unknowns={len(payload['unknowns'])}")


if __name__ == "__main__":
    main()
