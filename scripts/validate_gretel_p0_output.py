#!/usr/bin/env python3
"""
Gretel P0 Output Validator

Validates Gretel transformation output against contract schemas.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


class GretelOutputValidator:
    """Validates Gretel output against contracts."""

    def __init__(self, contracts_dir: Path, output_file: Path):
        self.contracts_dir = contracts_dir
        self.output_file = output_file
        self.contracts = self._load_contracts()
        self.output = self._load_output()
        self.errors = []
        self.warnings = []

    def _load_contracts(self) -> Dict[str, Dict[str, Any]]:
        """Load contract schemas."""
        contracts = {}
        schema_files = [
            "hypothesis.schema.json",
            "diagnosis.schema.json",
            "recommendation.schema.json",
            "kpi.schema.json",
            "validation_question.schema.json",
            "roadmap_action.schema.json",
        ]

        for schema_file in schema_files:
            schema_path = self.contracts_dir / schema_file
            if schema_path.exists():
                with open(schema_path, "r") as f:
                    contracts[schema_file.replace(".schema.json", "")] = json.load(f)

        return contracts

    def _load_output(self) -> Dict[str, Any]:
        """Load output file."""
        with open(self.output_file, "r") as f:
            return json.load(f)

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validations."""
        self.errors = []
        self.warnings = []

        self._validate_hypotheses()
        self._validate_diagnoses()
        self._validate_recommendations()
        self._validate_kpis()
        self._validate_validation_questions()
        self._validate_roadmap_actions()
        self._validate_contract_discipline()
        self._validate_traceability()

        return len(self.errors) == 0, {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def _validate_hypotheses(self):
        """Validate hypothesis array."""
        hypotheses = self.output.get("hypotheses", [])
        schema = self.contracts.get("hypothesis", {})

        for i, hyp in enumerate(hypotheses):
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in hyp:
                    self.errors.append(
                        f"Hypothesis[{i}]: missing required field '{field}'"
                    )

            # Check ID pattern
            if "hypothesis_id" in hyp:
                if not hyp["hypothesis_id"].startswith("HYP-"):
                    self.errors.append(
                        f"Hypothesis[{i}]: ID must start with 'HYP-', got {hyp['hypothesis_id']}"
                    )

            # Check requires_validation is true
            if hyp.get("requires_validation") is not True:
                self.errors.append(
                    f"Hypothesis[{i}]: requires_validation must be true, got {hyp.get('requires_validation')}"
                )

            # Check confidence is 0-1
            conf = hyp.get("confidence", 0)
            if not (0 <= conf <= 1):
                self.errors.append(
                    f"Hypothesis[{i}]: confidence must be 0-1, got {conf}"
                )

            # Check validation_gap is not empty
            if not hyp.get("validation_gap"):
                self.warnings.append(
                    f"Hypothesis[{i}]: validation_gap should describe what validation is needed"
                )

    def _validate_diagnoses(self):
        """Validate diagnosis array."""
        diagnoses = self.output.get("diagnoses", [])
        schema = self.contracts.get("diagnosis", {})

        for i, diag in enumerate(diagnoses):
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in diag:
                    self.errors.append(
                        f"Diagnosis[{i}]: missing required field '{field}'"
                    )

            # Check ID pattern
            if "diagnosis_id" in diag:
                if not diag["diagnosis_id"].startswith("DX-"):
                    self.errors.append(
                        f"Diagnosis[{i}]: ID must start with 'DX-', got {diag['diagnosis_id']}"
                    )

            # Check diagnosis_type
            valid_types = [
                "observed_problem",
                "likely_cause",
                "validated_cause",
                "unknown",
            ]
            if diag.get("diagnosis_type") not in valid_types:
                self.errors.append(
                    f"Diagnosis[{i}]: invalid diagnosis_type {diag.get('diagnosis_type')}"
                )

            # Rule: public evidence → likely_cause, not validated_cause
            if (
                diag.get("diagnosis_type") == "validated_cause"
                and diag.get("confidence", 0) < 0.95
            ):
                self.warnings.append(
                    f"Diagnosis[{i}]: validated_cause should have very high confidence (0.95+), got {diag.get('confidence')}"
                )

            # Check confidence is 0-1
            conf = diag.get("confidence", 0)
            if not (0 <= conf <= 1):
                self.errors.append(
                    f"Diagnosis[{i}]: confidence must be 0-1, got {conf}"
                )

            # Check traceability
            if not diag.get("finding_ids") and not diag.get("hypothesis_ids"):
                self.errors.append(
                    f"Diagnosis[{i}]: must trace to at least one finding or hypothesis"
                )

            if not diag.get("evidence_ids"):
                self.warnings.append(
                    f"Diagnosis[{i}]: should trace to evidence_ids"
                )

    def _validate_recommendations(self):
        """Validate recommendation array."""
        recommendations = self.output.get("recommendations", [])
        schema = self.contracts.get("recommendation", {})

        for i, rec in enumerate(recommendations):
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in rec:
                    self.errors.append(
                        f"Recommendation[{i}]: missing required field '{field}'"
                    )

            # Check ID pattern
            if "recommendation_id" in rec:
                if not rec["recommendation_id"].startswith("REC-"):
                    self.errors.append(
                        f"Recommendation[{i}]: ID must start with 'REC-', got {rec['recommendation_id']}"
                    )

            # Check priority
            valid_priorities = ["low", "medium", "high"]
            if rec.get("priority") not in valid_priorities:
                self.errors.append(
                    f"Recommendation[{i}]: invalid priority {rec.get('priority')}"
                )

            # Check KPI structure
            kpi = rec.get("kpi", {})
            kpi_required = ["name", "baseline", "baseline_status", "target", "timeframe", "measurement_method"]
            for field in kpi_required:
                if field not in kpi:
                    self.errors.append(
                        f"Recommendation[{i}].kpi: missing required field '{field}'"
                    )

            # Check baseline_status
            valid_baseline_status = ["known", "estimated", "unknown", "not_applicable"]
            if kpi.get("baseline_status") not in valid_baseline_status:
                self.errors.append(
                    f"Recommendation[{i}].kpi: invalid baseline_status {kpi.get('baseline_status')}"
                )

            # Rule: never invent baseline
            if kpi.get("baseline_status") == "unknown" and kpi.get("baseline") is not None:
                self.warnings.append(
                    f"Recommendation[{i}].kpi: baseline should be null when baseline_status is 'unknown'"
                )

            # Check confidence is 0-1
            conf = rec.get("confidence", 0)
            if not (0 <= conf <= 1):
                self.errors.append(
                    f"Recommendation[{i}]: confidence must be 0-1, got {conf}"
                )

            # Check traceability
            if not rec.get("finding_ids"):
                self.errors.append(
                    f"Recommendation[{i}]: must have at least one finding_id"
                )

    def _validate_kpis(self):
        """Validate KPI array."""
        kpis = self.output.get("kpis", [])
        schema = self.contracts.get("kpi", {})

        for i, kpi in enumerate(kpis):
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in kpi:
                    self.errors.append(
                        f"KPI[{i}]: missing required field '{field}'"
                    )

            # Check baseline_status
            valid_baseline_status = ["known", "estimated", "unknown", "not_applicable"]
            if kpi.get("baseline_status") not in valid_baseline_status:
                self.errors.append(
                    f"KPI[{i}]: invalid baseline_status {kpi.get('baseline_status')}"
                )

            # Rule: never invent baseline
            if kpi.get("baseline_status") == "unknown" and kpi.get("baseline") is not None:
                self.warnings.append(
                    f"KPI[{i}]: baseline should be null when baseline_status is 'unknown'"
                )

            # Check name is not empty
            if not kpi.get("name"):
                self.errors.append(
                    f"KPI[{i}]: name cannot be empty"
                )

    def _validate_validation_questions(self):
        """Validate validation question array."""
        questions = self.output.get("validation_questions", [])
        schema = self.contracts.get("validation_question", {})

        for i, q in enumerate(questions):
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in q:
                    self.errors.append(
                        f"ValidationQuestion[{i}]: missing required field '{field}'"
                    )

            # Check ID pattern
            if "question_id" in q:
                if not q["question_id"].startswith("Q-"):
                    self.errors.append(
                        f"ValidationQuestion[{i}]: ID must start with 'Q-', got {q['question_id']}"
                    )

            # Check priority
            valid_priorities = ["low", "medium", "high"]
            if q.get("priority") not in valid_priorities:
                self.errors.append(
                    f"ValidationQuestion[{i}]: invalid priority {q.get('priority')}"
                )

            # Check traceability
            if not q.get("finding_ids") and not q.get("hypothesis_ids"):
                self.warnings.append(
                    f"ValidationQuestion[{i}]: should trace to at least one finding or hypothesis"
                )

            # Check question is not empty
            if not q.get("question"):
                self.errors.append(
                    f"ValidationQuestion[{i}]: question cannot be empty"
                )

    def _validate_roadmap_actions(self):
        """Validate roadmap action array."""
        actions = self.output.get("roadmap_actions", [])
        schema = self.contracts.get("roadmap_action", {})

        for i, action in enumerate(actions):
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in action:
                    self.errors.append(
                        f"RoadmapAction[{i}]: missing required field '{field}'"
                    )

            # Check ID pattern
            if "roadmap_action_id" in action:
                if not action["roadmap_action_id"].startswith("RA-"):
                    self.errors.append(
                        f"RoadmapAction[{i}]: ID must start with 'RA-', got {action['roadmap_action_id']}"
                    )

            # Check time_bucket
            valid_buckets = ["30_days", "60_days", "90_days"]
            if action.get("time_bucket") not in valid_buckets:
                self.errors.append(
                    f"RoadmapAction[{i}]: invalid time_bucket {action.get('time_bucket')}"
                )

            # Check action_type
            valid_types = ["implementation", "validation", "discovery"]
            if action.get("action_type") not in valid_types:
                self.errors.append(
                    f"RoadmapAction[{i}]: invalid action_type {action.get('action_type')}"
                )

            # Check action is not empty
            if not action.get("action"):
                self.errors.append(
                    f"RoadmapAction[{i}]: action cannot be empty"
                )

    def _validate_contract_discipline(self):
        """Validate contract discipline rules."""
        # Rule: hypothesis ≠ fact
        for i, hyp in enumerate(self.output.get("hypotheses", [])):
            if hyp.get("confidence", 0) >= 0.99:
                self.warnings.append(
                    f"Hypothesis[{i}]: confidence very high ({hyp['confidence']}) - ensure this is not a confirmed fact"
                )

        # Rule: public evidence → likely_cause, not validated_cause
        high_confidence_diagnoses = [
            d
            for d in self.output.get("diagnoses", [])
            if d.get("diagnosis_type") == "validated_cause"
        ]
        if high_confidence_diagnoses:
            self.warnings.append(
                f"Found {len(high_confidence_diagnoses)} validated_cause diagnoses - ensure these have direct evidence support"
            )

        # Rule: never invent baseline
        for i, kpi in enumerate(self.output.get("kpis", [])):
            if (
                kpi.get("baseline_status") == "known"
                and kpi.get("baseline") is None
            ):
                self.warnings.append(
                    f"KPI[{i}]: baseline_status is 'known' but baseline is null"
                )

    def _validate_traceability(self):
        """Validate traceability chains."""
        # Each recommendation should trace to findings
        for i, rec in enumerate(self.output.get("recommendations", [])):
            finding_ids = rec.get("finding_ids", [])
            diagnosis_ids = rec.get("diagnosis_ids", [])

            if not finding_ids and not diagnosis_ids:
                self.errors.append(
                    f"Recommendation[{i}]: does not trace to findings or diagnoses"
                )

        # Each diagnosis should trace to findings/hypotheses
        for i, diag in enumerate(self.output.get("diagnoses", [])):
            if not diag.get("finding_ids") and not diag.get("hypothesis_ids"):
                self.errors.append(
                    f"Diagnosis[{i}]: does not trace to findings or hypotheses"
                )


def main():
    """Run validation."""
    contracts_dir = Path(__file__).parent.parent / "contracts"
    output_file = Path(__file__).parent.parent / "runs" / "gretel_p0_fixture_run.json"

    if not output_file.exists():
        print(f"✗ Output file not found: {output_file}")
        return 1

    validator = GretelOutputValidator(contracts_dir, output_file)
    valid, results = validator.validate()

    print("=" * 80)
    print("GRETEL P0 OUTPUT VALIDATION")
    print("=" * 80)
    print()

    if valid:
        print("✓ All validations passed!")
    else:
        print("✗ Validation failed with errors:")
        print()

    if results.get("errors"):
        print("ERRORS:")
        for error in results["errors"]:
            print(f"  ✗ {error}")
        print()

    if results.get("warnings"):
        print("WARNINGS:")
        for warning in results["warnings"]:
            print(f"  ⚠ {warning}")
        print()

    print("=" * 80)
    print(f"Total errors: {len(results.get('errors', []))}")
    print(f"Total warnings: {len(results.get('warnings', []))}")
    print("=" * 80)

    return 0 if valid else 1


if __name__ == "__main__":
    exit(main())
