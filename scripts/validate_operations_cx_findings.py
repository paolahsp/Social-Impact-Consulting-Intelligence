#!/usr/bin/env python3
"""
Validator for Operations/CX Agent findings.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


class OperationsCXValidator:
    """Validate operations/CX findings against schema."""

    def __init__(self, contracts_dir: Path, output_file: Path):
        self.contracts_dir = contracts_dir
        self.output_file = output_file
        self.schema = self._load_schema()
        self.output = self._load_output()
        self.errors = []
        self.warnings = []

    def _load_schema(self) -> Dict[str, Any]:
        """Load finding schema."""
        schema_path = self.contracts_dir / "finding.schema.json"
        with open(schema_path, "r") as f:
            return json.load(f)

    def _load_output(self) -> Dict[str, Any]:
        """Load output file."""
        with open(self.output_file, "r") as f:
            return json.load(f)

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validations."""
        self.errors = []
        self.warnings = []

        findings = self.output.get("findings", [])

        for i, finding in enumerate(findings):
            self._validate_finding(finding, i)

        self._validate_contract_discipline()

        return len(self.errors) == 0, {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def _validate_finding(self, finding: Dict[str, Any], index: int):
        """Validate a single finding."""
        # Check required fields
        required = self.schema.get("required", [])
        for field in required:
            if field not in finding:
                self.errors.append(
                    f"Finding[{index}]: missing required field '{field}'"
                )

        # Check ID pattern
        if "finding_id" in finding:
            if not finding["finding_id"].startswith("F-"):
                self.errors.append(
                    f"Finding[{index}]: ID must start with 'F-', got {finding['finding_id']}"
                )

        # Check domain is operations_cx
        if finding.get("domain") != "operations_cx":
            self.errors.append(
                f"Finding[{index}]: domain must be 'operations_cx', got {finding.get('domain')}"
            )

        # Check finding_type
        valid_types = ["observed", "inferred", "hypothesis", "unknown"]
        if finding.get("finding_type") not in valid_types:
            self.errors.append(
                f"Finding[{index}]: invalid finding_type {finding.get('finding_type')}"
            )

        # Check confidence is 0-1
        conf = finding.get("confidence", 0)
        if not (0 <= conf <= 1):
            self.errors.append(
                f"Finding[{index}]: confidence must be 0-1, got {conf}"
            )

        # Check requires_validation is boolean
        if not isinstance(finding.get("requires_validation"), bool):
            self.errors.append(
                f"Finding[{index}]: requires_validation must be boolean, got {type(finding.get('requires_validation'))}"
            )

        # Check evidence_ids
        if not finding.get("evidence_ids"):
            self.warnings.append(f"Finding[{index}]: should have at least one evidence_id")

        # Check finding text is not empty
        if not finding.get("finding"):
            self.errors.append(f"Finding[{index}]: finding text cannot be empty")

        # Rule: observed findings should not require validation
        if finding.get("finding_type") == "observed" and finding.get(
            "requires_validation"
        ):
            self.warnings.append(
                f"Finding[{index}]: observed findings typically should not require validation"
            )

        # Rule: unknown/hypothesis findings should require validation
        if finding.get("finding_type") in [
            "unknown",
            "hypothesis",
        ] and not finding.get("requires_validation"):
            self.errors.append(
                f"Finding[{index}]: {finding.get('finding_type')} findings must require validation"
            )

        # Check validation_question
        if finding.get("requires_validation") and not finding.get(
            "validation_question"
        ):
            self.errors.append(
                f"Finding[{index}]: requires_validation=true but validation_question is missing"
            )

    def _validate_contract_discipline(self):
        """Validate contract discipline rules."""
        findings = self.output.get("findings", [])

        # Count by type
        observed_count = sum(1 for f in findings if f.get("finding_type") == "observed")
        inferred_count = sum(
            1 for f in findings if f.get("finding_type") == "inferred"
        )
        unknown_count = sum(1 for f in findings if f.get("finding_type") == "unknown")
        hypothesis_count = sum(
            1 for f in findings if f.get("finding_type") == "hypothesis"
        )

        print()
        print("Contract discipline check:")
        print(
            f"  Observed: {observed_count} (directly evidenced from public sources)"
        )
        print(
            f"  Inferred: {inferred_count} (patterns from multiple signals)"
        )
        print(
            f"  Unknown: {unknown_count} (not publicly visible, unconfirmed)"
        )
        print(f"  Hypothesis: {hypothesis_count} (educated guesses about internal processes)")

        if unknown_count == 0 and hypothesis_count == 0:
            self.warnings.append(
                "No unknown or hypothesis findings detected. Check if internal processes were identified."
            )

        # Check for technology recommendations
        for i, finding in enumerate(findings):
            finding_text = finding.get("finding", "").lower()
            tech_keywords = [
                "CRM",
                "salesforce",
                "recommend",
                "implement",
                "should install",
                "should use",
                "needs",
            ]
            if any(kw.lower() in finding_text for kw in tech_keywords):
                self.warnings.append(
                    f"Finding[{i}]: appears to contain technology recommendation. This workflow should only diagnose, not recommend."
                )


def main():
    """Run validation."""
    contracts_dir = Path(__file__).parent.parent / "contracts"
    output_file = (
        Path(__file__).parent.parent / "runs" / "operations_cx_agent_output.json"
    )

    if not output_file.exists():
        print(f"✗ Output file not found: {output_file}")
        return 1

    validator = OperationsCXValidator(contracts_dir, output_file)
    valid, results = validator.validate()

    print("=" * 80)
    print("OPERATIONS/CX AGENT FINDINGS VALIDATION")
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
