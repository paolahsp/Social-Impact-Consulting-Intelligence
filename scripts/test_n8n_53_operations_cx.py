#!/usr/bin/env python3
"""
Test harness for n8n workflow 53_OPERATIONS_CX_AGENT.

Simulates n8n execution flow by passing data through the workflow nodes.
"""

import json
from pathlib import Path


def simulate_input_node(input_data):
    """Simulate: INPUT_CONTRACT__PUBLIC_OPERATIONS_EVIDENCE"""
    if not isinstance(input_data.get("evidence"), list):
        raise ValueError("Input must contain evidence array")
    return input_data


def simulate_filter_node(data):
    """Simulate: FILTER_OPERATIONS_DOMAIN"""
    evidence = data.get("evidence", [])
    sources = data.get("sources", [])

    ops_keywords = [
        "volunteer",
        "donor",
        "application",
        "form",
        "process",
        "workflow",
        "journey",
        "follow-up",
        "followup",
        "contact",
        "email",
        "phone",
        "communication",
        "automation",
        "crm",
        "database",
        "tracking",
        "onboarding",
        "stakeholder",
        "experience",
        "customer",
    ]

    ops_evidence = [
        ev
        for ev in evidence
        if ev.get("domain") == "operations_cx"
        or any(kw in ev.get("claim", "").lower() for kw in ops_keywords)
    ]

    return {
        "evidence": ops_evidence,
        "sources": sources,
        "run_context": data.get("run_context"),
        "all_evidence": evidence,
    }


def simulate_classify_node(data):
    """Simulate: CLASSIFY_EVIDENCE"""
    evidence = data.get("evidence", [])
    classified = {}

    for ev in evidence:
        ev_type = ev.get("evidence_type", "unknown")
        if ev_type not in classified:
            classified[ev_type] = []
        classified[ev_type].append(ev)

    return {
        "observable": classified.get("fact", []),
        "inferred_signals": classified.get("inferred", []),
        "unknowns": classified.get("unknown", []),
        "sources": data.get("sources"),
        "run_context": data.get("run_context"),
        "all_evidence": data.get("all_evidence"),
    }


def simulate_build_findings_node(data):
    """Simulate: BUILD_FINDINGS"""
    findings = []
    finding_counter = 0

    def make_id():
        nonlocal finding_counter
        finding_counter += 1
        return f"F-{str(finding_counter).zfill(3)}"

    observable = data.get("observable", [])

    # Observable findings
    for ev in observable:
        claim = ev.get("claim", "")
        confidence = ev.get("confidence", 0.7)

        if "application" in claim.lower() or "form" in claim.lower():
            if "volunteer" in claim.lower():
                findings.append(
                    {
                        "finding_id": make_id(),
                        "domain": "operations_cx",
                        "finding": "The organization provides a digital entry point for prospective volunteers through its website.",
                        "evidence_ids": [ev.get("evidence_id", "")],
                        "finding_type": "observed",
                        "confidence": min(confidence, 0.9),
                        "requires_validation": False,
                        "validation_question": None,
                    }
                )

        if any(
            kw in claim.lower() for kw in ["email", "phone", "contact", "communication", "website"]
        ):
            findings.append(
                {
                    "finding_id": make_id(),
                    "domain": "operations_cx",
                    "finding": f"Observable communication mechanism: {claim}",
                    "evidence_ids": [ev.get("evidence_id", "")],
                    "finding_type": "observed",
                    "confidence": min(confidence, 0.85),
                    "requires_validation": False,
                    "validation_question": None,
                }
            )

    # Inferred findings
    if len(observable) >= 2:
        volunteer_evidence = [e for e in observable if "volunteer" in e.get("claim", "").lower()]
        if len(volunteer_evidence) >= 2:
            findings.append(
                {
                    "finding_id": make_id(),
                    "domain": "operations_cx",
                    "finding": "The organization has established processes for volunteer recruitment and engagement, evidenced by public volunteer channels.",
                    "evidence_ids": [e.get("evidence_id", "") for e in volunteer_evidence[:2]],
                    "finding_type": "inferred",
                    "confidence": 0.65,
                    "requires_validation": True,
                    "validation_question": "Can you describe the complete volunteer journey from initial interest to active participation?",
                }
            )

    # Unknown findings
    for ev in observable:
        claim = ev.get("claim", "").lower()
        if "application" in claim or "form" in claim:
            if "volunteer" in claim:
                findings.append(
                    {
                        "finding_id": make_id(),
                        "domain": "operations_cx",
                        "finding": "The internal volunteer intake and qualification process after application submission is not publicly described.",
                        "evidence_ids": [ev.get("evidence_id", "")],
                        "finding_type": "unknown",
                        "confidence": 0.7,
                        "requires_validation": True,
                        "validation_question": "After a volunteer submits an application, what is the internal process for review, qualification, and onboarding?",
                    }
                )

    # Generic unknowns
    if len(observable) >= 2:
        generic_unknowns = [
            {
                "finding": "The organization's internal approach to workflow automation cannot be determined from public information.",
                "question": "Are volunteer and donor workflows currently automated or managed manually?",
            },
            {
                "finding": "The organization's internal approach to data integration cannot be determined from public information.",
                "question": "How is stakeholder data integrated across different systems?",
            },
            {
                "finding": "The organization's internal approach to follow-up tracking cannot be determined from public information.",
                "question": "How does the organization track follow-up communications with stakeholders?",
            },
        ]

        for u in generic_unknowns:
            findings.append(
                {
                    "finding_id": make_id(),
                    "domain": "operations_cx",
                    "finding": u["finding"],
                    "evidence_ids": [observable[0].get("evidence_id", "")],
                    "finding_type": "unknown",
                    "confidence": 0.5,
                    "requires_validation": True,
                    "validation_question": u["question"],
                }
            )

    return {"findings": findings, "finding_count": len(findings)}


def simulate_validate_node(data):
    """Simulate: VALIDATE_FINDINGS"""
    findings = data.get("findings", [])
    errors = []

    for i, f in enumerate(findings):
        if not f.get("finding_id") or not f["finding_id"].startswith("F-"):
            errors.append(f"Finding[{i}]: invalid ID")
        if f.get("domain") != "operations_cx":
            errors.append(f"Finding[{i}]: domain must be operations_cx")
        if f.get("finding_type") not in ["observed", "inferred", "unknown", "hypothesis"]:
            errors.append(f"Finding[{i}]: invalid finding_type")
        if not (0 <= f.get("confidence", 0) <= 1):
            errors.append(f"Finding[{i}]: confidence must be 0-1")
        if not isinstance(f.get("requires_validation"), bool):
            errors.append(f"Finding[{i}]: requires_validation must be boolean")
        if f.get("requires_validation") and not f.get("validation_question"):
            errors.append(f"Finding[{i}]: requires_validation=true but no validation_question")

    if errors:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")

    return data


def simulate_output_node(data):
    """Simulate: OUTPUT_CONTRACT__OPERATIONS_CX_FINDINGS"""
    return {"findings": data.get("findings", [])}


def simulate_workflow_execution(input_data):
    """Simulate complete n8n workflow execution."""
    print("N8N WORKFLOW 53_OPERATIONS_CX_AGENT — EXECUTION SIMULATION")
    print("=" * 80)

    # Node 1: Input
    print("\n1. INPUT_CONTRACT__PUBLIC_OPERATIONS_EVIDENCE")
    try:
        step1 = simulate_input_node(input_data)
        print("   ✓ Input validated")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

    # Node 2: Filter
    print("\n2. FILTER_OPERATIONS_DOMAIN")
    try:
        step2 = simulate_filter_node(step1)
        print(f"   ✓ Filtered evidence: {len(step2['evidence'])} items")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

    # Node 3: Classify
    print("\n3. CLASSIFY_EVIDENCE")
    try:
        step3 = simulate_classify_node(step2)
        print(
            f"   ✓ Observable: {len(step3['observable'])}, Inferred: {len(step3['inferred_signals'])}, Unknown: {len(step3['unknowns'])}"
        )
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

    # Node 4: Build Findings
    print("\n4. BUILD_FINDINGS")
    try:
        step4 = simulate_build_findings_node(step3)
        print(f"   ✓ Generated {step4['finding_count']} findings")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

    # Node 5: Validate
    print("\n5. VALIDATE_FINDINGS")
    try:
        step5 = simulate_validate_node(step4)
        print("   ✓ All findings valid")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

    # Node 6: Output
    print("\n6. OUTPUT_CONTRACT__OPERATIONS_CX_FINDINGS")
    try:
        step6 = simulate_output_node(step5)
        print(f"   ✓ Output ready: {len(step6['findings'])} findings")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

    print("\n" + "=" * 80)
    print("✓ WORKFLOW EXECUTION SUCCESSFUL")
    print("=" * 80)

    return step6


def main():
    """Run workflow simulation test."""
    # Load fixture
    fixture_path = Path(__file__).parent.parent / "fixtures" / "paola_track_output.json"

    with open(fixture_path, "r") as f:
        paola_output = json.load(f)

    # Run workflow
    result = simulate_workflow_execution(paola_output)

    if result:
        # Save test output
        output_path = (
            Path(__file__).parent.parent
            / "runs"
            / "n8n_53_operations_cx_test_output.json"
        )
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\n✓ Test output saved to {output_path}")
        print()

        # Print summary
        findings = result.get("findings", [])
        by_type = {}
        for f in findings:
            ftype = f.get("finding_type", "unknown")
            by_type[ftype] = by_type.get(ftype, 0) + 1

        print("FINDINGS SUMMARY:")
        for ftype in ["observed", "inferred", "unknown", "hypothesis"]:
            if ftype in by_type:
                print(f"  {ftype}: {by_type[ftype]}")

        return 0
    else:
        print("\n✗ WORKFLOW EXECUTION FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
