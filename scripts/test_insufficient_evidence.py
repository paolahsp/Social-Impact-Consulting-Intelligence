#!/usr/bin/env python3
"""
Test the transformation pipeline with insufficient evidence.
"""

import json
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from gretel_p0_transformation import GretelTransformationPipeline


def test_insufficient_evidence():
    """Run transformation on insufficient evidence fixture."""
    fixture_path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "paola_track_insufficient_evidence.json"
    )

    with open(fixture_path, "r") as f:
        paola_output = json.load(f)

    pipeline = GretelTransformationPipeline(paola_output)
    gretel_output = pipeline.run()

    # Save output
    output_path = (
        Path(__file__).parent.parent / "runs" / "gretel_p0_insufficient_evidence_test.json"
    )

    with open(output_path, "w") as f:
        json.dump(gretel_output, f, indent=2)

    print(f"✓ Insufficient evidence test complete")
    print(f"✓ Output saved to {output_path}")
    print()
    print(f"Hypotheses: {len(gretel_output['hypotheses'])}")
    print(f"Diagnoses: {len(gretel_output['diagnoses'])}")
    print(f"Recommendations: {len(gretel_output['recommendations'])}")
    print(f"KPIs: {len(gretel_output['kpis'])}")
    print(f"Validation Questions: {len(gretel_output['validation_questions'])}")
    print(f"Roadmap Actions: {len(gretel_output['roadmap_actions'])}")
    
    # Print details
    print()
    print("=" * 80)
    print("INSUFFICIENT EVIDENCE TEST - KEY OUTPUTS")
    print("=" * 80)
    
    if gretel_output.get("diagnoses"):
        dx = gretel_output["diagnoses"][0]
        print()
        print("Diagnosis type:", dx.get("diagnosis_type"))
        print("Confidence:", dx.get("confidence"))
        print("Requires validation:", dx.get("requires_validation"))
        print("Statement:", dx.get("statement"))
    
    if gretel_output.get("recommendations"):
        rec = gretel_output["recommendations"][0]
        print()
        print("Recommendation action:", rec.get("action"))
        print("Priority:", rec.get("priority"))
        print("KPI baseline status:", rec.get("kpi", {}).get("baseline_status"))
        print("Requires human review:", rec.get("requires_human_review"))
    
    if gretel_output.get("roadmap_actions"):
        ra = gretel_output["roadmap_actions"][0]
        print()
        print("First roadmap action type:", ra.get("action_type"))
        print("Time bucket:", ra.get("time_bucket"))
        print("Action:", ra.get("action"))


if __name__ == "__main__":
    test_insufficient_evidence()
