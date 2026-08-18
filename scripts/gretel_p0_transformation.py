#!/usr/bin/env python3
"""
Gretel P0 Vertical Slice — Transformation Pipeline

Chains workflows 61-66:
61 - HYPOTHESIS_BUILDER
62 - ROOT_CAUSE_DIAGNOSIS
63 - ACTION_DESIGN
64 - KPI_DESIGN
65 - CLIENT_VALIDATION_QUESTIONS
66 - 90_DAY_ROADMAP

Input: Paola track output (evidence, findings, unknowns)
Output: Complete transformation chain with hypotheses, diagnoses, actions, KPIs, questions, roadmap

Contract discipline: preserve FACT ≠ INFERENCE ≠ HYPOTHESIS ≠ UNKNOWN boundaries
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime


class GretelTransformationPipeline:
    """Complete transformation from evidence to roadmap."""

    def __init__(self, paola_output: Dict[str, Any]):
        self.paola_output = paola_output
        self.run_context = paola_output.get("run_context", {})
        self.sources = paola_output.get("sources", [])
        self.evidence = paola_output.get("evidence", [])
        self.findings = paola_output.get("findings", [])
        self.unknowns = paola_output.get("unknowns", [])
        self.contradictions = paola_output.get("contradictions", [])
        self.rag_metadata = paola_output.get("rag_metadata", {})

        # Track generated IDs
        self.hypothesis_counter = 0
        self.diagnosis_counter = 0
        self.recommendation_counter = 0
        self.question_counter = 0
        self.roadmap_counter = 0

    def _generate_id(self, prefix: str) -> str:
        """Generate a sequential ID."""
        if prefix == "HYP":
            self.hypothesis_counter += 1
            return f"{prefix}-{str(self.hypothesis_counter).zfill(3)}"
        elif prefix == "DX":
            self.diagnosis_counter += 1
            return f"{prefix}-{str(self.diagnosis_counter).zfill(3)}"
        elif prefix == "REC":
            self.recommendation_counter += 1
            return f"{prefix}-{str(self.recommendation_counter).zfill(3)}"
        elif prefix == "Q":
            self.question_counter += 1
            return f"{prefix}-{str(self.question_counter).zfill(3)}"
        elif prefix == "RA":
            self.roadmap_counter += 1
            return f"{prefix}-{str(self.roadmap_counter).zfill(3)}"
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def _get_evidence_by_id(self, evidence_id: str) -> Dict[str, Any]:
        """Retrieve evidence by ID."""
        for ev in self.evidence:
            if ev.get("evidence_id") == evidence_id:
                return ev
        return {}

    def _get_finding_by_id(self, finding_id: str) -> Dict[str, Any]:
        """Retrieve finding by ID."""
        for f in self.findings:
            if f.get("finding_id") == finding_id:
                return f
        return {}

    def _get_unknown_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Retrieve unknowns for a domain."""
        return [u for u in self.unknowns if u.get("domain") == domain]

    def workflow_61_hypothesis_builder(self) -> List[Dict[str, Any]]:
        """
        61 — HYPOTHESIS_BUILDER

        For findings where internal reality is not directly observable,
        create structured hypotheses.

        Input: findings, evidence, unknowns
        Output: hypotheses[]
        """
        hypotheses = []

        for finding in self.findings:
            finding_id = finding.get("finding_id", "")
            domain = finding.get("domain", "")
            finding_text = finding.get("finding", "")
            evidence_ids = finding.get("evidence_ids", [])
            finding_type = finding.get("finding_type", "")
            confidence = finding.get("confidence", 0.5)

            # Rule: For "observed" findings with high confidence,
            # derive hypotheses about internal processes not directly visible
            if finding_type == "observed" and confidence >= 0.75:
                # Get associated evidence
                ev_list = [self._get_evidence_by_id(ev_id) for ev_id in evidence_ids]
                evidence_domains = [ev.get("domain") for ev in ev_list if ev]

                # Check for unknowns in this domain
                domain_unknowns = self._get_unknown_by_domain(domain)

                if domain_unknowns:
                    # Hypothesis: internal process is not publicly visible
                    hypothesis_text = self._derive_hypothesis(
                        finding_text, domain, domain_unknowns
                    )
                    validation_gap = domain_unknowns[0].get("description", "")

                    hypothesis = {
                        "hypothesis_id": self._generate_id("HYP"),
                        "run_id": self.run_context.get("run_id", ""),
                        "domain": domain,
                        "evidence_ids": evidence_ids,
                        "finding_ids": [finding_id],
                        "hypothesis": hypothesis_text,
                        "confidence": max(
                            0.3, confidence * 0.6
                        ),  # Lower confidence for hypothesis
                        "requires_validation": True,
                        "validation_gap": validation_gap,
                    }
                    hypotheses.append(hypothesis)

            # Rule: For "inferred" findings with moderate confidence,
            # create hypotheses about causation or internal state
            elif finding_type == "inferred" and confidence >= 0.5:
                hypothesis_text = self._derive_hypothesis_from_inference(
                    finding_text, domain
                )
                validation_gap = f"Additional evidence needed to validate: {finding_text}"

                hypothesis = {
                    "hypothesis_id": self._generate_id("HYP"),
                    "run_id": self.run_context.get("run_id", ""),
                    "domain": domain,
                    "evidence_ids": evidence_ids,
                    "finding_ids": [finding_id],
                    "hypothesis": hypothesis_text,
                    "confidence": confidence * 0.7,  # Lower than finding confidence
                    "requires_validation": True,
                    "validation_gap": validation_gap,
                }
                hypotheses.append(hypothesis)

        return hypotheses

    def _derive_hypothesis(
        self, finding: str, domain: str, unknowns: List[Dict[str, Any]]
    ) -> str:
        """Derive a reasonable hypothesis from a finding and unknowns."""
        # This would be an LLM call in production; for testing, use templates
        templates = {
            "operations_cx": "The {domain} process may involve steps that are not publicly visible. This internal workflow should be validated during the client conversation.",
            "revenue_resilience": "Revenue patterns may depend on factors that are not publicly reported. The organization's actual funding distribution should be confirmed.",
            "impact_evidence": "Impact measurement may involve internal processes not described in public sources.",
        }

        template = templates.get(domain, "Internal processes may differ from public descriptions.")
        return template.format(domain=domain)

    def _derive_hypothesis_from_inference(self, finding: str, domain: str) -> str:
        """Derive a hypothesis from an inferred finding."""
        return f"Based on the evidence, it appears that {finding.lower()} This should be validated with the client."

    def workflow_62_root_cause_diagnosis(
        self, hypotheses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        62 — ROOT_CAUSE_DIAGNOSIS

        Distinguish: observed_problem, likely_cause, validated_cause, unknown

        Public evidence → likely_cause (not validated_cause)

        Input: findings, hypotheses
        Output: diagnoses[]
        """
        diagnoses = []

        # For each hypothesis, create a diagnosis
        for hypothesis in hypotheses:
            hypothesis_id = hypothesis.get("hypothesis_id", "")
            domain = hypothesis.get("domain", "")
            evidence_ids = hypothesis.get("evidence_ids", [])
            finding_ids = hypothesis.get("finding_ids", [])
            hypothesis_confidence = hypothesis.get("confidence", 0.5)

            # Classify diagnosis type
            # Rule: public evidence → likely_cause, not validated_cause
            if hypothesis_confidence >= 0.7:
                diagnosis_type = "likely_cause"
            elif hypothesis_confidence >= 0.5:
                diagnosis_type = "likely_cause"
            else:
                diagnosis_type = "unknown"

            # For observed findings, may indicate observed_problem
            finding = self._get_finding_by_id(finding_ids[0] if finding_ids else "")
            if finding.get("finding_type") == "observed":
                if hypothesis_confidence >= 0.75:
                    diagnosis_type = "observed_problem"

            diagnosis = {
                "diagnosis_id": self._generate_id("DX"),
                "domain": domain,
                "diagnosis_type": diagnosis_type,
                "statement": self._derive_diagnosis_statement(
                    hypothesis, diagnosis_type
                ),
                "finding_ids": finding_ids,
                "hypothesis_ids": [hypothesis_id],
                "evidence_ids": evidence_ids,
                "confidence": hypothesis_confidence,
                "requires_validation": hypothesis.get("requires_validation", True),
            }
            diagnoses.append(diagnosis)

        return diagnoses

    def _derive_diagnosis_statement(
        self, hypothesis: Dict[str, Any], diagnosis_type: str
    ) -> str:
        """Derive a diagnosis statement from hypothesis."""
        hypothesis_text = hypothesis.get("hypothesis", "")
        domain = hypothesis.get("domain", "")

        statements = {
            "observed_problem": f"An observed issue: {hypothesis_text}",
            "likely_cause": f"A likely contributing factor: {hypothesis_text}",
            "validated_cause": f"A confirmed cause (validated): {hypothesis_text}",
            "unknown": f"The actual cause cannot be determined from public evidence. {hypothesis_text}",
        }

        return statements.get(
            diagnosis_type, f"Diagnosis (type unknown): {hypothesis_text}"
        )

    def workflow_63_action_design(
        self, diagnoses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        63 — ACTION_DESIGN

        Actions must be:
        - concrete
        - proportionate
        - realistic
        - traceable to diagnosis
        - mission-aligned

        If hypothesis unvalidated: action = Validate with client

        Input: diagnoses, findings, hypotheses
        Output: recommendations[]
        """
        recommendations = []

        for diagnosis in diagnoses:
            diagnosis_id = diagnosis.get("diagnosis_id", "")
            diagnosis_type = diagnosis.get("diagnosis_type", "")
            domain = diagnosis.get("domain", "")
            confidence = diagnosis.get("confidence", 0.5)
            requires_validation = diagnosis.get("requires_validation", True)
            finding_ids = diagnosis.get("finding_ids", [])
            hypothesis_ids = diagnosis.get("hypothesis_ids", [])

            # Rule: If unvalidated, first action = validation
            if requires_validation or confidence < 0.7:
                action_text = self._derive_validation_action(diagnosis)
                priority = "high"
                rec_human_review = True
            else:
                action_text = self._derive_implementation_action(diagnosis, domain)
                priority = "medium"
                rec_human_review = False

            # Create KPI stub (will be expanded in workflow 64)
            kpi = {
                "name": self._derive_kpi_name(diagnosis, domain),
                "baseline": None,
                "baseline_status": "unknown" if requires_validation else "estimated",
                "target": None,
                "timeframe": "After validation" if requires_validation else "30-90 days",
                "measurement_method": self._derive_measurement_method(diagnosis, domain),
            }

            recommendation = {
                "recommendation_id": self._generate_id("REC"),
                "finding_ids": finding_ids,
                "diagnosis_ids": [diagnosis_id],
                "diagnosis": diagnosis.get("statement", ""),
                "action": action_text,
                "priority": priority,
                "kpi": kpi,
                "confidence": confidence,
                "requires_human_review": rec_human_review,
            }
            recommendations.append(recommendation)

        return recommendations

    def _derive_validation_action(self, diagnosis: Dict[str, Any]) -> str:
        """Derive validation action."""
        domain = diagnosis.get("domain", "")
        diagnosis_type = diagnosis.get("diagnosis_type", "")

        templates = {
            "operations_cx": "Validate the current operations and customer experience process during the client workshop. Understand the actual workflow before recommending changes.",
            "revenue_resilience": "Discuss funding sources and concentration during the client workshop. Confirm the organization's actual revenue dependencies.",
            "impact_evidence": "Discuss impact measurement practices during the client workshop.",
        }

        return templates.get(domain, "Validate this finding with the client organization.")

    def _derive_implementation_action(self, diagnosis: Dict[str, Any], domain: str) -> str:
        """Derive implementation action."""
        templates = {
            "operations_cx": "Document and optimize the operations process based on validated insights.",
            "revenue_resilience": "Develop a revenue diversification strategy based on confirmed funding dependencies.",
            "impact_evidence": "Implement or enhance impact measurement systems.",
        }

        return templates.get(domain, "Implement improvements based on validated findings.")

    def _derive_kpi_name(self, diagnosis: Dict[str, Any], domain: str) -> str:
        """Derive KPI name."""
        names = {
            "operations_cx": "Operations efficiency / Customer experience quality",
            "revenue_resilience": "Funding source diversity / Revenue stability",
            "impact_evidence": "Impact measurement maturity",
        }
        return names.get(domain, "Performance metric")

    def _derive_measurement_method(
        self, diagnosis: Dict[str, Any], domain: str
    ) -> str:
        """Derive measurement method."""
        methods = {
            "operations_cx": "Review process documentation, staff interviews, and workflow metrics.",
            "revenue_resilience": "Analyze financial statements and funding reports.",
            "impact_evidence": "Review impact measurement frameworks and reporting practices.",
        }
        return methods.get(domain, "Develop measurement framework with client.")

    def workflow_64_kpi_design(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        64 — KPI_DESIGN

        Never invent baseline.
        If unknown: baseline=null, baseline_status="unknown"

        Input: recommendations
        Output: kpis[]
        """
        kpis = []

        for recommendation in recommendations:
            kpi_data = recommendation.get("kpi", {})
            requires_human_review = recommendation.get("requires_human_review", False)

            # Refine KPI definition
            kpi = {
                "name": kpi_data.get("name", ""),
                "baseline": None,  # Never invent; use null
                "baseline_status": kpi_data.get("baseline_status", "unknown"),
                "target": None,  # Never invent; use null
                "timeframe": kpi_data.get("timeframe", "To be determined"),
                "measurement_method": kpi_data.get("measurement_method", ""),
            }

            kpis.append(kpi)

        return kpis

    def workflow_65_client_validation_questions(
        self, hypotheses: List[Dict[str, Any]], diagnoses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        65 — CLIENT_VALIDATION_QUESTIONS (CORE PRODUCT FEATURE)

        Convert hypotheses and evidence gaps into useful consultant questions.

        Must be: neutral, specific, non-leading

        Input: hypotheses, diagnoses, findings, unknowns
        Output: validation_questions[]
        """
        questions = []

        # For each hypothesis, create validation question
        for hypothesis in hypotheses:
            hypothesis_id = hypothesis.get("hypothesis_id", "")
            finding_ids = hypothesis.get("finding_ids", [])
            domain = hypothesis.get("domain", "")
            validation_gap = hypothesis.get("validation_gap", "")

            question_text = self._derive_neutral_question(hypothesis, domain)

            question = {
                "question_id": self._generate_id("Q"),
                "finding_ids": finding_ids,
                "hypothesis_ids": [hypothesis_id],
                "question": question_text,
                "purpose": f"Validate: {validation_gap}",
                "domain": domain,
                "priority": "high",
            }
            questions.append(question)

        # For each unknown, create discovery question
        for unknown in self.unknowns:
            unknown_id = unknown.get("unknown_id", "")
            domain = unknown.get("domain", "")
            description = unknown.get("description", "")
            evidence_ids = unknown.get("evidence_ids", [])

            question_text = self._derive_discovery_question(domain, description)

            question = {
                "question_id": self._generate_id("Q"),
                "finding_ids": [],
                "hypothesis_ids": [],
                "question": question_text,
                "purpose": f"Discover: {description}",
                "domain": domain,
                "priority": "medium",
            }
            questions.append(question)

        return questions

    def _derive_neutral_question(
        self, hypothesis: Dict[str, Any], domain: str
    ) -> str:
        """Derive a neutral, specific, non-leading question."""
        templates = {
            "operations_cx": "Can you describe the actual workflow after a {event} happens? What specific steps are involved?",
            "revenue_resilience": "What are your actual revenue sources, and approximately what percentage comes from each?",
            "impact_evidence": "How do you currently measure and report on your impact?",
        }

        template = templates.get(domain, "Can you describe how this process actually works?")
        return template.format(event="application is submitted")

    def _derive_discovery_question(self, domain: str, description: str) -> str:
        """Derive a discovery question from unknown description."""
        return f"Regarding '{description}' — can you walk us through how this actually works?"

    def workflow_66_90_day_roadmap(
        self,
        diagnoses: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        questions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        66 — 90_DAY_ROADMAP

        Organize into 30/60/90 day buckets.
        Unvalidated → validation/discovery
        Validated → implementation

        Input: diagnoses, recommendations, validation_questions
        Output: roadmap_actions[]
        """
        roadmap_actions = []

        # 30-day actions: validation and discovery
        for recommendation in recommendations:
            if recommendation.get("requires_human_review", False):
                action_type = "validation"
                time_bucket = "30_days"
                action_text = f"Validate during client workshop: {recommendation.get('action', '')}"
            else:
                action_type = "discovery"
                time_bucket = "30_days"
                action_text = recommendation.get("action", "")

            roadmap_action = {
                "roadmap_action_id": self._generate_id("RA"),
                "time_bucket": time_bucket,
                "action": action_text,
                "action_type": action_type,
                "recommendation_ids": [recommendation.get("recommendation_id", "")],
                "hypothesis_ids": [],
                "validation_question_ids": [],
            }
            roadmap_actions.append(roadmap_action)

        # Link validation questions to roadmap actions
        for i, question in enumerate(questions):
            if i < len(roadmap_actions):
                roadmap_actions[i]["validation_question_ids"].append(
                    question.get("question_id", "")
                )

        # 60/90-day actions: design and implementation (once validated)
        if any(not rec.get("requires_human_review") for rec in recommendations):
            design_action = {
                "roadmap_action_id": self._generate_id("RA"),
                "time_bucket": "60_days",
                "action": "Design implementation plan based on validated findings.",
                "action_type": "design",
                "recommendation_ids": [],
                "hypothesis_ids": [],
                "validation_question_ids": [],
            }
            roadmap_actions.append(design_action)

            implementation_action = {
                "roadmap_action_id": self._generate_id("RA"),
                "time_bucket": "90_days",
                "action": "Begin implementation and track KPI baselines.",
                "action_type": "implementation",
                "recommendation_ids": [],
                "hypothesis_ids": [],
                "validation_question_ids": [],
            }
            roadmap_actions.append(implementation_action)

        return roadmap_actions

    def run(self) -> Dict[str, Any]:
        """Execute the complete transformation pipeline."""
        # 61 → Hypotheses
        hypotheses = self.workflow_61_hypothesis_builder()

        # 62 → Diagnoses
        diagnoses = self.workflow_62_root_cause_diagnosis(hypotheses)

        # 63 → Recommendations
        recommendations = self.workflow_63_action_design(diagnoses)

        # 64 → KPIs
        kpis = self.workflow_64_kpi_design(recommendations)

        # 65 → Validation Questions
        questions = self.workflow_65_client_validation_questions(hypotheses, diagnoses)

        # 66 → 90-Day Roadmap
        roadmap_actions = self.workflow_66_90_day_roadmap(
            diagnoses, recommendations, questions
        )

        return {
            "run_context": self.run_context,
            "hypotheses": hypotheses,
            "diagnoses": diagnoses,
            "recommendations": recommendations,
            "kpis": kpis,
            "validation_questions": questions,
            "roadmap_actions": roadmap_actions,
        }


def main():
    """Load fixture and run transformation pipeline."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "paola_track_output.json"

    with open(fixture_path, "r") as f:
        paola_output = json.load(f)

    pipeline = GretelTransformationPipeline(paola_output)
    gretel_output = pipeline.run()

    # Save output
    output_path = (
        Path(__file__).parent.parent / "runs" / "gretel_p0_fixture_run.json"
    )
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(gretel_output, f, indent=2)

    print(f"✓ Transformation complete")
    print(f"✓ Output saved to {output_path}")
    print()
    print(f"Hypotheses: {len(gretel_output['hypotheses'])}")
    print(f"Diagnoses: {len(gretel_output['diagnoses'])}")
    print(f"Recommendations: {len(gretel_output['recommendations'])}")
    print(f"KPIs: {len(gretel_output['kpis'])}")
    print(f"Validation Questions: {len(gretel_output['validation_questions'])}")
    print(f"Roadmap Actions: {len(gretel_output['roadmap_actions'])}")


if __name__ == "__main__":
    main()
