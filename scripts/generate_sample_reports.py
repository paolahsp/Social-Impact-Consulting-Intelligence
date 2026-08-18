"""Generate the two Project 3 sample reports from retained JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"


def load_json(relative_path: str) -> dict:
    with (ROOT / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def fmt_confidence(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.0%}"
    return "Not provided"


def write_report(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def generate_fictional_report() -> None:
    response = load_json("fixtures/intellectus_71_success_response.json")
    package = load_json("fixtures/final_package_example.json")
    data = response["data"]
    intake = data["intake"]

    lines = [
        "# Fictional River Learning Collective",
        "",
        "## Pre-Engagement Diagnostic — Operations & Stakeholder Experience",
        "",
        "> **Demonstration status:** Controlled fictional sample. This report is",
        "> generated from the retained Intellectus response and final-package",
        "> fixtures. It is not a claim about a real organization.",
        "",
        f"- **Run ID:** `{response['run_id']}`",
        f"- **Correlation ID:** `{response['correlation_id']}`",
        f"- **Status:** `{response['status']}`",
        f"- **Country:** {intake['country']}",
        f"- **Objective:** {intake['current_challenge']}",
        "",
        "## What the evidence supports",
        "",
    ]

    for finding in data["findings"]:
        if finding["finding_type"] == "observed":
            evidence = ", ".join(finding["evidence_ids"])
            lines.extend(
                [
                    f"- **{finding['finding_id']}:** {finding['finding']}",
                    f"  - Evidence: `{evidence}`",
                    f"  - Confidence: {fmt_confidence(finding['confidence'])}",
                ]
            )

    lines.extend(["", "## Unknowns and hypotheses", ""])
    for finding in data["findings"]:
        if finding["finding_type"] in {"unknown", "hypothesis"}:
            lines.extend(
                [
                    f"- **{finding['finding_type'].title()} — {finding['finding_id']}:** "
                    f"{finding['finding']}",
                    f"  - Confidence: {fmt_confidence(finding['confidence'])}",
                    f"  - Requires validation: {'Yes' if finding['requires_validation'] else 'No'}",
                ]
            )
            if finding.get("validation_question"):
                lines.append(f"  - Validation question: {finding['validation_question']}")

    recommendation = package["recommendations"][0]
    kpi = recommendation["kpi"]
    lines.extend(
        [
            "",
            "## Recommended next step",
            "",
            f"- **Diagnosis to validate:** {recommendation['diagnosis']}",
            f"- **Action:** {recommendation['action']}",
            f"- **Priority:** {recommendation['priority'].title()}",
            f"- **Human review required:** {'Yes' if recommendation['requires_human_review'] else 'No'}",
            "",
            "## Measurement",
            "",
            f"- **KPI:** {kpi['name']}",
            f"- **Baseline:** {kpi['baseline_status']}",
            f"- **Target:** {'Not set until validation' if kpi['target'] is None else kpi['target']}",
            f"- **Method:** {kpi['measurement_method']}",
            "",
            "## Evidence sources",
            "",
        ]
    )
    for source in data["sources"]:
        lines.append(
            f"- `{source['source_id']}` — {source['title']} "
            f"({source['source_type']}, {source['authority_level']})"
        )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The organization, website, and source records are fictional.",
            "- Public evidence does not establish the internal volunteer follow-up process.",
            "- The hypothesis must not be presented as a fact.",
            "- A consultant must approve any client-facing use.",
            "",
            "## Artifact provenance",
            "",
            "Generated deterministically from:",
            "",
            "- `fixtures/intellectus_71_success_response.json`",
            "- `fixtures/final_package_example.json`",
            "- `scripts/generate_sample_reports.py`",
        ]
    )

    write_report(SAMPLES / "01_fictional_river_learning_collective.md", lines)


def generate_revenue_report() -> None:
    run = load_json("runs/paola_p0_givedirectly.json")
    context = run["input"]
    org = context["organization"]
    finding = run["findings"][0]
    unknowns = run["paola_track_output"]["unknowns"]

    lines = [
        "# GiveDirectly",
        "",
        "## Revenue Resilience — Public-Search P0 Report",
        "",
        "> **Scope:** Retained Project 3 P0 run based on public search metadata.",
        "> It surfaces evidence for consultant review; it is not a complete",
        "> financial assessment or client diagnosis.",
        "",
        f"- **Run ID:** `{context['run_id']}`",
        f"- **Controlled state:** `{run['controlled_state']}`",
        f"- **Organization:** {org['name']}",
        f"- **Website:** {org['website']}",
        f"- **Research provider:** `{run['search']['provider']}`",
        f"- **Execution path:** {' -> '.join(run['execution_path'])}",
        "",
        "## Finding",
        "",
        f"{finding['finding']}",
        "",
        f"- **Finding type:** {finding['finding_type']}",
        f"- **Confidence:** {fmt_confidence(finding['confidence'])}",
        f"- **Requires validation:** {'Yes' if finding['requires_validation'] else 'No'}",
        f"- **Validation question:** {finding['validation_question']}",
        "",
        "## Public sources surfaced",
        "",
    ]

    for source in run["sources"]:
        official = "official" if source["is_official"] else "third-party"
        lines.append(
            f"- `{source['source_id']}` — [{source['title']}]({source['url']}) "
            f"({official}; authority: {source['authority_level']})"
        )

    lines.extend(["", "## Evidence ledger", ""])
    for item in run["evidence"]:
        source_ids = ", ".join(item["source_ids"])
        lines.extend(
            [
                f"- **{item['evidence_id']}:** {item['claim']}",
                f"  - Sources: `{source_ids}`",
                f"  - Confidence: {fmt_confidence(item['confidence'])}",
                f"  - Status: {item['status']}",
            ]
        )

    lines.extend(["", "## Unknowns", ""])
    for unknown in unknowns:
        lines.append(f"- **{unknown['unknown_id']}:** {unknown['description']}")

    lines.extend(["", "## Retrieved framework context", ""])
    for item in run["rag_context"]["contexts"]:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                item["content"],
                "",
                f"**Evaluation use:** {item['evaluation_use']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Consultant review decision",
            "",
            "Do not infer revenue concentration, reserves, runway, or resilience",
            "from these search results. Review the underlying financial statements",
            "and ask which sources are material, recurring, or concentrated in the",
            "current financial year.",
            "",
            "## Limitations",
            "",
        ]
    )
    for limitation in finding["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "- Search metadata can identify relevant sources but does not replace",
            "  source-document review.",
            "- The retained run does not establish financial health or client outcomes.",
            "",
            "## Artifact provenance",
            "",
            "Generated deterministically from:",
            "",
            "- `runs/paola_p0_givedirectly.json`",
            "- `scripts/generate_sample_reports.py`",
        ]
    )

    write_report(SAMPLES / "02_givedirectly_revenue_resilience.md", lines)


def main() -> None:
    SAMPLES.mkdir(exist_ok=True)
    generate_fictional_report()
    generate_revenue_report()
    print("Generated 2 sample reports in samples/")


if __name__ == "__main__":
    main()

