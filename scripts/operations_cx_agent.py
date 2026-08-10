#!/usr/bin/env python3
"""
53 — OPERATIONS_CX_AGENT

Assess publicly observable operations and stakeholder experience signals.

Distinguishes:
- Observable signals (from public evidence)
- Inferred patterns (from multiple signals)
- Internal process unknowns (not publicly visible)
- Hypotheses about internal workflows

Output: findings in finding.schema.json format (domain=operations_cx)
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class OperationsCXAgent:
    """Analyze public evidence for operations/CX insights."""

    def __init__(self, evidence: List[Dict[str, Any]], sources: List[Dict[str, Any]]):
        self.evidence = evidence
        self.sources = sources
        self.findings = []
        self.finding_counter = 0

    def _generate_finding_id(self) -> str:
        """Generate sequential finding ID."""
        self.finding_counter += 1
        return f"F-{str(self.finding_counter).zfill(3)}"

    def _get_source_by_id(self, source_id: str) -> Dict[str, Any]:
        """Retrieve source by ID."""
        for src in self.sources:
            if src.get("source_id") == source_id:
                return src
        return {}

    def analyze(self) -> List[Dict[str, Any]]:
        """Run complete analysis."""
        # Step 1: Extract evidence relevant to operations/CX
        operations_evidence = self._filter_operations_evidence()

        # Step 2: Identify observable signals
        self._identify_observable_signals(operations_evidence)

        # Step 3: Identify inferred patterns
        self._identify_inferred_patterns(operations_evidence)

        # Step 4: Identify unknowns and hypotheses
        self._identify_unknowns_and_hypotheses(operations_evidence)

        return self.findings

    def _filter_operations_evidence(self) -> List[Dict[str, Any]]:
        """Filter evidence relevant to operations_cx domain."""
        ops_evidence = [
            ev
            for ev in self.evidence
            if ev.get("domain") == "operations_cx" or self._is_operations_related(ev)
        ]
        return ops_evidence

    def _is_operations_related(self, evidence: Dict[str, Any]) -> bool:
        """Check if evidence is related to operations/CX."""
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
            "CRM",
            "database",
            "tracking",
            "onboarding",
            "stakeholder",
            "experience",
            "customer",
        ]

        claim = evidence.get("claim", "").lower()
        return any(keyword.lower() in claim for keyword in ops_keywords)

    def _identify_observable_signals(self, ops_evidence: List[Dict[str, Any]]):
        """
        Identify observable signals from evidence.

        Observable = publicly visible, directly evidenced
        """
        for evidence in ops_evidence:
            if evidence.get("evidence_type") == "fact":
                claim = evidence.get("claim", "")
                confidence = evidence.get("confidence", 0.7)
                evidence_ids = [evidence.get("evidence_id", "")]

                # Observable signals for volunteer/donor journeys
                observable_findings = self._derive_observable_findings(
                    claim, confidence, evidence_ids, evidence
                )
                self.findings.extend(observable_findings)

    def _derive_observable_findings(
        self,
        claim: str,
        confidence: float,
        evidence_ids: List[str],
        evidence: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Derive observable findings from evidence claims."""
        findings = []
        claim_lower = claim.lower()

        # Pattern 1: Digital entry points
        if any(
            keyword in claim_lower
            for keyword in ["application", "form", "website", "online"]
        ):
            if "volunteer" in claim_lower:
                finding = {
                    "finding_id": self._generate_finding_id(),
                    "domain": "operations_cx",
                    "finding": "The organization provides a digital entry point for prospective volunteers through its website.",
                    "evidence_ids": evidence_ids,
                    "finding_type": "observed",
                    "confidence": min(confidence, 0.9),
                    "requires_validation": False,
                    "validation_question": None,
                }
                findings.append(finding)

            elif "donor" in claim_lower or "donation" in claim_lower or "fund" in claim_lower:
                finding = {
                    "finding_id": self._generate_finding_id(),
                    "domain": "operations_cx",
                    "finding": "The organization provides a digital channel for donors to contribute.",
                    "evidence_ids": evidence_ids,
                    "finding_type": "observed",
                    "confidence": min(confidence, 0.9),
                    "requires_validation": False,
                    "validation_question": None,
                }
                findings.append(finding)

        # Pattern 2: Multiple revenue/stakeholder sources
        if any(
            keyword in claim_lower for keyword in ["funding", "revenue", "donor", "grant", "support"]
        ):
            if "more than one" in claim_lower or "multiple" in claim_lower:
                finding = {
                    "finding_id": self._generate_finding_id(),
                    "domain": "operations_cx",
                    "finding": "The organization publicly describes support from multiple funding or stakeholder sources.",
                    "evidence_ids": evidence_ids,
                    "finding_type": "observed",
                    "confidence": min(confidence, 0.85),
                    "requires_validation": False,
                    "validation_question": None,
                }
                findings.append(finding)

        # Pattern 3: Communication channels
        if any(
            keyword in claim_lower for keyword in ["email", "phone", "contact", "communication", "website"]
        ):
            finding = {
                "finding_id": self._generate_finding_id(),
                "domain": "operations_cx",
                "finding": f"Observable communication mechanism: {claim}",
                "evidence_ids": evidence_ids,
                "finding_type": "observed",
                "confidence": min(confidence, 0.85),
                "requires_validation": False,
                "validation_question": None,
            }
            findings.append(finding)

        return findings

    def _identify_inferred_patterns(self, ops_evidence: List[Dict[str, Any]]):
        """
        Identify inferred patterns from multiple evidence items.

        Inferred = pattern across multiple signals, but not directly stated
        """
        # Look for journey patterns
        volunteer_signals = [
            ev
            for ev in ops_evidence
            if "volunteer" in ev.get("claim", "").lower()
        ]
        donor_signals = [
            ev
            for ev in ops_evidence
            if any(
                kw in ev.get("claim", "").lower()
                for kw in ["donor", "funding", "revenue", "donation"]
            )
        ]

        # Inferred from multiple volunteer signals
        if len(volunteer_signals) >= 2:
            evidence_ids = [ev.get("evidence_id", "") for ev in volunteer_signals]
            finding = {
                "finding_id": self._generate_finding_id(),
                "domain": "operations_cx",
                "finding": "The organization has established processes for volunteer recruitment and engagement, evidenced by public volunteer channels.",
                "evidence_ids": evidence_ids,
                "finding_type": "inferred",
                "confidence": 0.65,
                "requires_validation": True,
                "validation_question": "Can you describe the complete volunteer journey from initial interest to active participation?",
            }
            self.findings.append(finding)

        # Inferred from multiple donor signals
        if len(donor_signals) >= 2:
            evidence_ids = [ev.get("evidence_id", "") for ev in donor_signals]
            finding = {
                "finding_id": self._generate_finding_id(),
                "domain": "operations_cx",
                "finding": "The organization maintains donor engagement mechanisms across multiple channels or funding relationships.",
                "evidence_ids": evidence_ids,
                "finding_type": "inferred",
                "confidence": 0.62,
                "requires_validation": True,
                "validation_question": "How does the organization currently nurture relationships with donors across the funding cycle?",
            }
            self.findings.append(finding)

    def _identify_unknowns_and_hypotheses(
        self, ops_evidence: List[Dict[str, Any]]
    ):
        """
        Identify unknowns and hypotheses where internal processes are not publicly visible.

        Unknown = absence of public evidence doesn't mean process doesn't exist
        Hypothesis = educated guess about internal workflow
        """
        # Check for observable signals that imply hidden internal processes

        # Pattern 1: Application form exists → internal processing is unknown
        volunteer_forms = [
            ev
            for ev in ops_evidence
            if "volunteer" in ev.get("claim", "").lower()
            and any(
                kw in ev.get("claim", "").lower()
                for kw in ["application", "form", "apply", "submit"]
            )
        ]

        if volunteer_forms:
            evidence_ids = [ev.get("evidence_id", "") for ev in volunteer_forms]
            finding = {
                "finding_id": self._generate_finding_id(),
                "domain": "operations_cx",
                "finding": "The internal volunteer intake and qualification process after application submission is not publicly described.",
                "evidence_ids": evidence_ids,
                "finding_type": "unknown",
                "confidence": 0.7,
                "requires_validation": True,
                "validation_question": "After a volunteer submits an application, what is the internal process for review, qualification, and onboarding?",
            }
            self.findings.append(finding)

        # Pattern 2: Donation channel exists → follow-up process is unknown
        donation_channels = [
            ev
            for ev in ops_evidence
            if any(
                kw in ev.get("claim", "").lower()
                for kw in ["donor", "donation", "funding", "contribute", "donate"]
            )
        ]

        if donation_channels:
            evidence_ids = [
                ev.get("evidence_id", "")
                for ev in donation_channels[:3]
            ]  # limit to 3
            finding = {
                "finding_id": self._generate_finding_id(),
                "domain": "operations_cx",
                "finding": "The internal process for acknowledging donations and maintaining donor engagement is not publicly visible.",
                "evidence_ids": evidence_ids,
                "finding_type": "unknown",
                "confidence": 0.65,
                "requires_validation": True,
                "validation_question": "How does the organization acknowledge and engage with donors after they make a contribution?",
            }
            self.findings.append(finding)

        # Pattern 3: Digital fragmentation hypothesis
        if len(ops_evidence) >= 3:
            # If multiple communication channels but no visible integration
            communication_channels = [
                ev
                for ev in ops_evidence
                if any(
                    kw in ev.get("claim", "").lower()
                    for kw in ["email", "phone", "form", "website", "social", "contact"]
                )
            ]

            if len(communication_channels) >= 2:
                evidence_ids = [
                    ev.get("evidence_id", "")
                    for ev in communication_channels[:3]
                ]
                finding = {
                    "finding_id": self._generate_finding_id(),
                    "domain": "operations_cx",
                    "finding": "The organization may manage stakeholder information across multiple disconnected systems or channels, based on the variety of visible contact points.",
                    "evidence_ids": evidence_ids,
                    "finding_type": "hypothesis",
                    "confidence": 0.45,
                    "requires_validation": True,
                    "validation_question": "How does the organization currently track and manage information about volunteers and donors across different touchpoints?",
                }
                self.findings.append(finding)

        # Pattern 4: Generic unknown for processes that are never visible
        generic_unknowns = [
            ("workflow automation", "Are volunteer and donor workflows currently automated or managed manually?"),
            ("data integration", "How is stakeholder data integrated across different systems?"),
            ("follow-up tracking", "How does the organization track follow-up communications with stakeholders?"),
        ]

        for unknown_area, validation_q in generic_unknowns:
            # Only add if relevant evidence exists
            if len(ops_evidence) >= 2:
                finding = {
                    "finding_id": self._generate_finding_id(),
                    "domain": "operations_cx",
                    "finding": f"The organization's internal approach to {unknown_area} cannot be determined from public information.",
                    "evidence_ids": [ops_evidence[0].get("evidence_id", "")],
                    "finding_type": "unknown",
                    "confidence": 0.5,
                    "requires_validation": True,
                    "validation_question": validation_q,
                }
                self.findings.append(finding)


def main():
    """Test Operations/CX Agent on fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "paola_track_output.json"

    with open(fixture_path, "r") as f:
        paola_output = json.load(f)

    evidence = paola_output.get("evidence", [])
    sources = paola_output.get("sources", [])

    agent = OperationsCXAgent(evidence, sources)
    findings = agent.analyze()

    # Save findings
    output = {
        "domain": "operations_cx",
        "findings": findings,
        "total": len(findings),
    }

    output_path = (
        Path(__file__).parent.parent / "runs" / "operations_cx_agent_output.json"
    )
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✓ Operations/CX analysis complete")
    print(f"✓ Output saved to {output_path}")
    print()
    print(f"Total findings: {len(findings)}")
    print()

    # Breakdown by type
    by_type = {}
    for f in findings:
        ftype = f.get("finding_type", "unknown")
        by_type[ftype] = by_type.get(ftype, 0) + 1

    print("By finding type:")
    for ftype, count in sorted(by_type.items()):
        print(f"  {ftype}: {count}")

    print()
    print("Sample findings:")
    for f in findings[:3]:
        print(f"  - [{f['finding_type']}] {f['finding'][:70]}...")


if __name__ == "__main__":
    main()
