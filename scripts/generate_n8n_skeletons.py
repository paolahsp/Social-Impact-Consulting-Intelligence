import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "workflows" / "skeletons"
CONTRACT_DIR = ROOT / "contracts"


def slug_id(name):
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")[:80]


def sticky(name, content, x, y, width=440, height=260):
    return {
        "parameters": {
            "content": content,
            "height": height,
            "width": width,
            "color": 4,
        },
        "id": slug_id(name),
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
    }


def code_node(name, description, x, y, terminal=False):
    marker = "TERMINAL_OUTPUT_NODE" if terminal else "SKELETON_PLACEHOLDER"
    js = (
        f"// {marker}: {name}\n"
        f"// {description}\n"
        "// TODO: Replace this placeholder with configured production logic.\n"
        "// Contract discipline: preserve FACT / INFERENCE / HYPOTHESIS / UNKNOWN boundaries.\n"
        "return items;\n"
    )
    return {
        "parameters": {"jsCode": js},
        "id": slug_id(name),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, y],
    }


def trigger_node(kind, name, x, y):
    node_type = {
        "manual": "n8n-nodes-base.manualTrigger",
        "subworkflow": "n8n-nodes-base.executeWorkflowTrigger",
        "error": "n8n-nodes-base.errorTrigger",
    }[kind]
    return {
        "parameters": {},
        "id": slug_id(name),
        "name": name,
        "type": node_type,
        "typeVersion": 1,
        "position": [x, y],
    }


def if_node(name, condition_label, x, y):
    return {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                },
                "conditions": [
                    {
                        "id": slug_id(name + condition_label),
                        "leftValue": "={{ $json.placeholder_decision }}",
                        "rightValue": "yes",
                        "operator": {"type": "string", "operation": "equals"},
                    }
                ],
                "combinator": "and",
            },
            "options": {},
        },
        "id": slug_id(name),
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "position": [x, y],
    }


def build_connections(edges):
    connections = {}
    for edge in edges:
        if len(edge) == 2:
            src, dst = edge
            out_index = 0
        else:
            src, dst, out_index = edge
        connections.setdefault(src, {"main": []})
        while len(connections[src]["main"]) <= out_index:
            connections[src]["main"].append([])
        connections[src]["main"][out_index].append(
            {"node": dst, "type": "main", "index": 0}
        )
    return connections


def top_note(title, owner, input_contract, output_contract, purpose):
    return (
        f"PURPOSE\n{purpose}\n\n"
        f"OWNER\n{owner}\n\n"
        f"INPUT CONTRACT\n{input_contract}\n\n"
        f"OUTPUT CONTRACT\n{output_contract}\n\n"
        "STATUS\nSkeleton only. Inactive by default. No credentials. Configure TODO nodes after import."
    )


def workflow(name, owner, purpose, input_contract, output_contract, steps, edges=None, trigger="subworkflow", extra_nodes=None, notes=None):
    nodes = [
        sticky(
            "00_README__PURPOSE_OWNER_CONTRACTS_STATUS",
            top_note(name, owner, input_contract, output_contract, purpose),
            -420,
            -320,
            520,
            340,
        )
    ]
    if notes:
        for i, note in enumerate(notes):
            nodes.append(sticky(f"NOTE__{i + 1}", note, -420, 60 + i * 220, 520, 200))

    start_name = "START__MANUAL_TRIGGER" if trigger == "manual" else "START__SUB_WORKFLOW_TRIGGER"
    if trigger == "error":
        start_name = "START__ERROR_TRIGGER"
    nodes.append(trigger_node(trigger, start_name, 0, 0))

    x = 260
    for name_, desc in steps:
        terminal = name_.startswith("OUTPUT") or name_.startswith("RETURN") or name_.startswith("FINAL")
        nodes.append(code_node(name_, desc, x, 0, terminal=terminal))
        x += 300
    if extra_nodes:
        nodes.extend(extra_nodes)

    if edges is None:
        names = [start_name] + [s[0] for s in steps]
        edges = list(zip(names, names[1:]))

    return {
        "name": name,
        "nodes": nodes,
        "connections": build_connections(edges),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


OWNERS = {
    "paola": "PAOLA TRACK A",
    "gretel": "GRETEL TRACK B",
    "shared": "SHARED",
}


WORKFLOWS = [
    (
        "00_MAIN_ORCHESTRATOR",
        workflow(
            "00_MAIN_ORCHESTRATOR",
            OWNERS["shared"],
            "Coordinate the complete public-data-first diagnostic run.",
            "run_context.schema.json plus initial user/web app payload",
            "final_package.schema.json",
            [
                ("INPUT_CONTRACT__RUN_REQUEST", "Validate minimum intake fields and preserve optional context."),
                ("TODO_LINK_SUBWORKFLOW__10_INTAKE_AND_ORG_RESOLVER", "LINK SUB-WORKFLOW AFTER IMPORT: 10_INTAKE_AND_ORG_RESOLVER."),
                ("TODO_LINK_SUBWORKFLOW__20_CONTEXT_RESEARCH", "LINK SUB-WORKFLOW AFTER IMPORT: 20_CONTEXT_RESEARCH_ORCHESTRATOR."),
                ("TODO_LINK_SUBWORKFLOW__30_EVIDENCE_PIPELINE", "LINK SUB-WORKFLOW AFTER IMPORT: 30_EVIDENCE_PIPELINE."),
                ("TODO_LINK_SUBWORKFLOW__40_RAG_RETRIEVAL", "LINK SUB-WORKFLOW AFTER IMPORT: 40_RAG_RETRIEVAL_PIPELINE."),
                ("TODO_LINK_SUBWORKFLOW__50_ANALYSIS", "LINK SUB-WORKFLOW AFTER IMPORT: 50_ANALYSIS_ORCHESTRATOR."),
                ("TODO_LINK_SUBWORKFLOW__60_TRANSFORMATION", "LINK SUB-WORKFLOW AFTER IMPORT: 60_TRANSFORMATION_ORCHESTRATOR."),
                ("TODO_LINK_SUBWORKFLOW__70_REPORT_QA_DELIVERY", "LINK SUB-WORKFLOW AFTER IMPORT: 70_REPORT_QA_DELIVERY."),
                ("OUTPUT_CONTRACT__FINAL_PACKAGE", "Return canonical final package JSON and run status."),
            ],
            trigger="manual",
            notes=[
                "LINK SUB-WORKFLOW AFTER IMPORT\nDo not invent workflow IDs. Replace TODO_LINK_SUBWORKFLOW nodes with Execute Workflow nodes only after each imported workflow has a real n8n workflow ID.",
            ],
        ),
    ),
    (
        "10_INTAKE_AND_ORG_RESOLVER",
        workflow(
            "10_INTAKE_AND_ORG_RESOLVER",
            OWNERS["shared"],
            "Receive and normalize initial organization information.",
            "organization_name, website, country; optional mission_area, current_challenge, uploaded_document_refs",
            "run_context.schema.json",
            [
                ("INPUT_CONTRACT__ORG_REQUEST", "Check payload shape for public-data-first diagnostic intake."),
                ("VALIDATE_REQUIRED_FIELDS", "Require organization_name, website, and country."),
                ("NORMALIZE_URL_COUNTRY_NAME", "Normalize website URL, country label, and organization name."),
                ("TODO_AGENT_OR_SERVICE__ORGANIZATION_RESOLVER", "Placeholder for later entity resolution and disambiguation."),
                ("CREATE_RUN_ID", "Create deterministic run context structure; final ID strategy TBD."),
                ("INITIAL_RUN_STATE", "Initialize status, timestamps, and empty errors array."),
                ("OUTPUT_CONTRACT__RUN_CONTEXT", "Return run context for downstream orchestration."),
            ],
        ),
    ),
    (
        "20_CONTEXT_RESEARCH_ORCHESTRATOR",
        workflow(
            "20_CONTEXT_RESEARCH_ORCHESTRATOR",
            OWNERS["paola"],
            "Create and coordinate a public research plan.",
            "run_context.schema.json",
            "context_pack: run_context plus normalized source candidates",
            [
                ("TODO_AGENT__RESEARCH_PLANNER", "AGENT_INTERFACE__RESEARCH_PLANNER. Produce research tasks by channel."),
                ("RESEARCH_TASKS", "Normalize task list for public web, official site, documents, news, and registries."),
                ("FAN_OUT__RESEARCH_CHANNELS", "Fan out tasks to channel skeletons."),
                ("TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH", "LINK SUB-WORKFLOW AFTER IMPORT: 21_WEB_SEARCH."),
                ("TODO_LINK_SUBWORKFLOW__22_WEBSITE_EXTRACTION", "LINK SUB-WORKFLOW AFTER IMPORT: 22_WEBSITE_EXTRACTION."),
                ("TODO_LINK_SUBWORKFLOW__23_DOCUMENT_PUBLIC_DATA", "LINK SUB-WORKFLOW AFTER IMPORT: 23_DOCUMENT_PUBLIC_DATA_RESEARCH."),
                ("TODO_LINK_SUBWORKFLOW__24_NEWS_EXTERNAL_CONTEXT", "LINK SUB-WORKFLOW AFTER IMPORT: 24_NEWS_EXTERNAL_CONTEXT."),
                ("PUBLIC_DATA_REGISTRIES_PLACEHOLDER", "Placeholder for public registries and charity records."),
                ("MERGE__RESEARCH_RESULTS", "Merge returned source candidates without fabricating missing data."),
                ("CONTEXT_PACK", "Assemble normalized context pack for evidence extraction."),
                ("OUTPUT_CONTRACT__CONTEXT_PACK", "Return context pack with source candidates and task metadata."),
            ],
            edges=[
                ("START__SUB_WORKFLOW_TRIGGER", "TODO_AGENT__RESEARCH_PLANNER"),
                ("TODO_AGENT__RESEARCH_PLANNER", "RESEARCH_TASKS"),
                ("RESEARCH_TASKS", "FAN_OUT__RESEARCH_CHANNELS"),
                ("FAN_OUT__RESEARCH_CHANNELS", "TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH"),
                ("FAN_OUT__RESEARCH_CHANNELS", "TODO_LINK_SUBWORKFLOW__22_WEBSITE_EXTRACTION"),
                ("FAN_OUT__RESEARCH_CHANNELS", "TODO_LINK_SUBWORKFLOW__23_DOCUMENT_PUBLIC_DATA"),
                ("FAN_OUT__RESEARCH_CHANNELS", "TODO_LINK_SUBWORKFLOW__24_NEWS_EXTERNAL_CONTEXT"),
                ("FAN_OUT__RESEARCH_CHANNELS", "PUBLIC_DATA_REGISTRIES_PLACEHOLDER"),
                ("TODO_LINK_SUBWORKFLOW__21_WEB_SEARCH", "MERGE__RESEARCH_RESULTS"),
                ("TODO_LINK_SUBWORKFLOW__22_WEBSITE_EXTRACTION", "MERGE__RESEARCH_RESULTS"),
                ("TODO_LINK_SUBWORKFLOW__23_DOCUMENT_PUBLIC_DATA", "MERGE__RESEARCH_RESULTS"),
                ("TODO_LINK_SUBWORKFLOW__24_NEWS_EXTERNAL_CONTEXT", "MERGE__RESEARCH_RESULTS"),
                ("PUBLIC_DATA_REGISTRIES_PLACEHOLDER", "MERGE__RESEARCH_RESULTS"),
                ("MERGE__RESEARCH_RESULTS", "CONTEXT_PACK"),
                ("CONTEXT_PACK", "OUTPUT_CONTRACT__CONTEXT_PACK"),
            ],
            notes=[
                "LINK SUB-WORKFLOW AFTER IMPORT\nReplace channel TODO_LINK nodes with Execute Workflow nodes after 21, 22, 23, and 24 have real n8n IDs.",
            ],
        ),
    ),
    (
        "21_WEB_SEARCH",
        workflow(
            "21_WEB_SEARCH",
            OWNERS["paola"],
            "Generic public-web discovery.",
            "research_task with organization and query intent",
            "source.schema.json[]",
            [
                ("INPUT_CONTRACT__RESEARCH_TASK", "Accept a single web discovery task."),
                ("BUILD_SEARCH_QUERY", "Build provider-neutral search query."),
                ("TODO_API__WEB_SEARCH", "Placeholder for Tavily, Serper, or equivalent. No credentials configured."),
                ("VALIDATE_RESPONSE", "Validate response shape and organization relevance."),
                ("NORMALIZE_RESULTS", "Normalize result metadata into source contract fields."),
                ("RETURN_SOURCES", "Return source candidates."),
            ],
        ),
    ),
    (
        "22_WEBSITE_EXTRACTION",
        workflow(
            "22_WEBSITE_EXTRACTION",
            OWNERS["paola"],
            "Extract useful information from official organization pages.",
            "official_url plus run_context",
            "source.schema.json[] plus extracted useful_content",
            [
                ("INPUT_CONTRACT__OFFICIAL_URL", "Accept official URL and extraction scope."),
                ("TODO_API__WEBSITE_EXTRACTION", "Placeholder for Firecrawl, Jina, or direct extraction."),
                ("PAGE_RESULT_VALIDATION", "Validate page fetch/extraction status and URL match."),
                ("USEFUL_CONTENT", "Keep useful text, headings, and page signals."),
                ("SOURCE_METADATA", "Attach source metadata and retrieval timestamp."),
                ("RETURN_SOURCES", "Return official website source records."),
            ],
        ),
    ),
    (
        "23_DOCUMENT_PUBLIC_DATA_RESEARCH",
        workflow(
            "23_DOCUMENT_PUBLIC_DATA_RESEARCH",
            OWNERS["paola"],
            "Handle public reports, PDFs, registries, and structured public data.",
            "document/public_data research_task",
            "source.schema.json[] plus document metadata",
            [
                ("INPUT_CONTRACT__DOCUMENT_PUBLIC_DATA_TASK", "Accept report, registry, or public data task."),
                ("LOCATE_SOURCE", "Locate likely public source without assuming access."),
                ("TODO_API__FETCH_PUBLIC_DOCUMENT_OR_DATA", "Placeholder for fetch/download provider."),
                ("DECISION__FILE_TYPE_BRANCH", "Branch by PDF, HTML, or structured data."),
                ("EXTRACT_PLACEHOLDER__PDF", "Placeholder for PDF extraction."),
                ("EXTRACT_PLACEHOLDER__HTML", "Placeholder for HTML extraction."),
                ("EXTRACT_PLACEHOLDER__STRUCTURED_DATA", "Placeholder for CSV/JSON/registry extraction."),
                ("NORMALIZE_DOCUMENT_SOURCE", "Normalize extracted metadata and source records."),
                ("RETURN_SOURCES_DOCUMENTS", "Return source/document records."),
            ],
            edges=[
                ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__DOCUMENT_PUBLIC_DATA_TASK"),
                ("INPUT_CONTRACT__DOCUMENT_PUBLIC_DATA_TASK", "LOCATE_SOURCE"),
                ("LOCATE_SOURCE", "TODO_API__FETCH_PUBLIC_DOCUMENT_OR_DATA"),
                ("TODO_API__FETCH_PUBLIC_DOCUMENT_OR_DATA", "DECISION__FILE_TYPE_BRANCH"),
                ("DECISION__FILE_TYPE_BRANCH", "EXTRACT_PLACEHOLDER__PDF"),
                ("DECISION__FILE_TYPE_BRANCH", "EXTRACT_PLACEHOLDER__HTML"),
                ("DECISION__FILE_TYPE_BRANCH", "EXTRACT_PLACEHOLDER__STRUCTURED_DATA"),
                ("EXTRACT_PLACEHOLDER__PDF", "NORMALIZE_DOCUMENT_SOURCE"),
                ("EXTRACT_PLACEHOLDER__HTML", "NORMALIZE_DOCUMENT_SOURCE"),
                ("EXTRACT_PLACEHOLDER__STRUCTURED_DATA", "NORMALIZE_DOCUMENT_SOURCE"),
                ("NORMALIZE_DOCUMENT_SOURCE", "RETURN_SOURCES_DOCUMENTS"),
            ],
        ),
    ),
    (
        "24_NEWS_EXTERNAL_CONTEXT",
        workflow(
            "24_NEWS_EXTERNAL_CONTEXT",
            OWNERS["paola"],
            "Research relevant recent public context.",
            "news research_task plus run_context",
            "source.schema.json[]",
            [
                ("INPUT_CONTRACT__NEWS_TASK", "Accept news/external context task."),
                ("NEWS_QUERY", "Build organization-aware news query."),
                ("TODO_API__NEWS", "Placeholder for future news/search provider."),
                ("FILTER_ORGANIZATION_MATCH", "Filter false positives and unrelated organizations."),
                ("NORMALIZE_NEWS_SOURCE", "Normalize articles and external context as source records."),
                ("RETURN_SOURCES", "Return news/external source records."),
            ],
        ),
    ),
    (
        "30_EVIDENCE_PIPELINE",
        workflow(
            "30_EVIDENCE_PIPELINE",
            OWNERS["paola"],
            "Convert collected context into traceable evidence.",
            "context_pack with source.schema.json[]",
            "evidence.schema.json[] plus evidence ledger metadata",
            [
                ("INPUT_CONTRACT__CONTEXT_PACK", "Accept source set and run context."),
                ("SOURCE_DEDUPLICATION", "Identify duplicate URLs/documents/citations."),
                ("SOURCE_QUALITY", "Assess authority, freshness, official status, and relevance."),
                ("TODO_AGENT__EVIDENCE_EXTRACTION", "AGENT_INTERFACE__EVIDENCE_EXTRACTION."),
                ("EVIDENCE_TYPE_CLASSIFICATION", "Classify extracted claims by domain and type."),
                ("FACT_INFERENCE_HYPOTHESIS_UNKNOWN_GATE", "Prevent unsupported hypotheses from becoming facts."),
                ("TODO_STORAGE__EVIDENCE_LEDGER", "Placeholder for durable evidence ledger storage."),
                ("CONTRADICTION_CHECK", "Detect conflicting evidence and preserve source IDs."),
                ("MISSING_EVIDENCE_DETECTION", "Flag unknowns and validation questions."),
                ("OUTPUT_CONTRACT__EVIDENCE_LEDGER", "Return evidence ledger and gap signals."),
            ],
        ),
    ),
    (
        "40_RAG_RETRIEVAL_PIPELINE",
        workflow(
            "40_RAG_RETRIEVAL_PIPELINE",
            OWNERS["paola"],
            "Retrieve relevant evaluation criteria from the project's knowledge base.",
            "evidence ledger and analysis domain request",
            "rag_context grouped by conceptual domain",
            [
                ("INPUT_CONTRACT__EVIDENCE_DOMAIN", "Accept evidence summary and requested domain."),
                ("DETERMINE_RETRIEVAL_QUERY", "Build retrieval query from evidence and domain."),
                ("TODO_DB__VECTOR_STORE", "Placeholder for vector database configuration. No fake DB."),
                ("RETRIEVE_FRAMEWORK_CONTEXT", "Return relevant framework context for configured domains."),
                ("VALIDATE_RETRIEVAL", "Validate relevance, freshness, and domain coverage."),
                ("OUTPUT_CONTRACT__RAG_CONTEXT", "Return RAG context for analysis."),
            ],
            notes=[
                "EXPECTED DOMAINS\nRevenue Resilience\nImpact & Evidence\nOperations & Stakeholder Experience\nResponsible AI\nTransformation Prioritization",
            ],
        ),
    ),
    (
        "50_ANALYSIS_ORCHESTRATOR",
        workflow(
            "50_ANALYSIS_ORCHESTRATOR",
            OWNERS["shared"],
            "Dispatch evidence and RAG context to specialist analysis workflows.",
            "evidence.schema.json[] plus rag_context",
            "finding.schema.json[] with hypothesis builder output",
            [
                ("INPUT_CONTRACT__EVIDENCE_AND_RAG", "Accept evidence ledger and domain RAG context."),
                ("FAN_OUT__SPECIALIST_ANALYSIS", "Dispatch to revenue, impact, and operations/CX specialists."),
                ("TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE", "LINK SUB-WORKFLOW AFTER IMPORT: 51_REVENUE_RESILIENCE_AGENT."),
                ("TODO_LINK_SUBWORKFLOW__52_IMPACT_EVIDENCE", "LINK SUB-WORKFLOW AFTER IMPORT: 52_IMPACT_EVIDENCE_AGENT."),
                ("TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "LINK SUB-WORKFLOW AFTER IMPORT: 53_OPERATIONS_CX_AGENT."),
                ("MERGE_FINDINGS", "Merge specialist outputs."),
                ("HYPOTHESIS_BUILDER", "Normalize cross-domain hypotheses and validation needs."),
                ("OUTPUT_CONTRACT__FINDINGS", "Return structured findings."),
            ],
            edges=[
                ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__EVIDENCE_AND_RAG"),
                ("INPUT_CONTRACT__EVIDENCE_AND_RAG", "FAN_OUT__SPECIALIST_ANALYSIS"),
                ("FAN_OUT__SPECIALIST_ANALYSIS", "TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE"),
                ("FAN_OUT__SPECIALIST_ANALYSIS", "TODO_LINK_SUBWORKFLOW__52_IMPACT_EVIDENCE"),
                ("FAN_OUT__SPECIALIST_ANALYSIS", "TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX"),
                ("TODO_LINK_SUBWORKFLOW__51_REVENUE_RESILIENCE", "MERGE_FINDINGS"),
                ("TODO_LINK_SUBWORKFLOW__52_IMPACT_EVIDENCE", "MERGE_FINDINGS"),
                ("TODO_LINK_SUBWORKFLOW__53_OPERATIONS_CX", "MERGE_FINDINGS"),
                ("MERGE_FINDINGS", "HYPOTHESIS_BUILDER"),
                ("HYPOTHESIS_BUILDER", "OUTPUT_CONTRACT__FINDINGS"),
            ],
            notes=[
                "LINK SUB-WORKFLOW AFTER IMPORT\nReplace specialist TODO_LINK nodes only after 51, 52, and 53 exist in n8n.",
            ],
        ),
    ),
    (
        "51_REVENUE_RESILIENCE_AGENT",
        workflow(
            "51_REVENUE_RESILIENCE_AGENT",
            OWNERS["paola"],
            "Assess public signals related to economic and revenue resilience.",
            "revenue evidence plus revenue RAG context",
            "finding.schema.json[] for revenue resilience",
            [
                ("INPUT_CONTRACT__REVENUE_EVIDENCE", "Accept relevant evidence and RAG snippets."),
                ("TODO_AGENT__REVENUE", "AGENT_INTERFACE__REVENUE_ANALYSIS."),
                ("EVIDENCE_CHECK", "Trace each finding back to evidence IDs."),
                ("STRUCTURED_FINDINGS", "Structure findings without penalizing unavailable financial data."),
                ("UNKNOWNS", "Preserve missing financial information as unknowns or validation questions."),
                ("OUTPUT_CONTRACT__REVENUE_FINDINGS", "Return revenue findings."),
            ],
        ),
    ),
    (
        "52_IMPACT_EVIDENCE_AGENT",
        workflow(
            "52_IMPACT_EVIDENCE_AGENT",
            OWNERS["paola"],
            "Assess mission clarity, Theory of Change, impact claims, KPIs, and evidence maturity.",
            "impact evidence plus impact RAG context",
            "finding.schema.json[] for impact and evidence",
            [
                ("INPUT_CONTRACT__IMPACT_EVIDENCE", "Accept relevant evidence and impact RAG."),
                ("TODO_AGENT__IMPACT", "AGENT_INTERFACE__IMPACT_ANALYSIS."),
                ("CLASSIFY_FINDINGS", "Classify mission, activity, output, outcome, KPI, and evidence signals."),
                ("EVIDENCE_CHECK", "Trace findings to evidence IDs and confidence."),
                ("UNKNOWNS", "Preserve missing impact data as unknowns."),
                ("OUTPUT_CONTRACT__IMPACT_FINDINGS", "Return impact findings."),
            ],
        ),
    ),
    (
        "53_OPERATIONS_CX_AGENT",
        workflow(
            "53_OPERATIONS_CX_AGENT",
            OWNERS["gretel"],
            "Assess publicly observable operations and stakeholder experience signals.",
            "public operations/CX evidence plus operations RAG context",
            "finding.schema.json[] for operations/CX with validation questions",
            [
                ("INPUT_CONTRACT__PUBLIC_OPERATIONS_EVIDENCE", "Accept public evidence and operations/CX RAG."),
                ("TODO_AGENT__OPERATIONS_CX", "AGENT_INTERFACE__OPERATIONS_CX_ANALYSIS."),
                ("OBSERVABLE_FINDING", "Record only publicly observable signals as facts."),
                ("HYPOTHESIS_BUILDER", "Create hypotheses where internal process is not publicly evidenced."),
                ("VALIDATION_QUESTION", "Generate client validation questions for operational unknowns."),
                ("OUTPUT_CONTRACT__OPERATIONS_CX_FINDINGS", "Return operations/CX findings."),
            ],
        ),
    ),
    (
        "54_EVIDENCE_GAP_RESEARCH",
        workflow(
            "54_EVIDENCE_GAP_RESEARCH",
            OWNERS["paola"],
            "Perform targeted research only when an important evidence gap exists.",
            "missing_evidence_request with retry_count, max_retries, reason_for_retry",
            "new evidence or UNKNOWN marker",
            [
                ("INPUT_CONTRACT__MISSING_EVIDENCE_REQUEST", "Accept missing evidence request and retry metadata."),
                ("DECISION__CAN_PUBLIC_RESEARCH_ANSWER", "Decide whether public research can answer the gap."),
                ("MARK_UNKNOWN", "When public research cannot answer, mark UNKNOWN for client validation."),
                ("BUILD_TARGETED_QUERY", "Build a focused query for answerable public gaps."),
                ("TODO_API__TARGETED_RESEARCH", "Placeholder for targeted public research provider."),
                ("VALIDATE_NEW_SOURCE", "Validate relevance and source quality."),
                ("NEW_EVIDENCE", "Normalize new evidence for re-evaluation."),
                ("RETURN_TO_EVALUATION", "Return evidence or UNKNOWN marker to caller."),
            ],
            edges=[
                ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__MISSING_EVIDENCE_REQUEST"),
                ("INPUT_CONTRACT__MISSING_EVIDENCE_REQUEST", "DECISION__CAN_PUBLIC_RESEARCH_ANSWER"),
                ("DECISION__CAN_PUBLIC_RESEARCH_ANSWER", "BUILD_TARGETED_QUERY"),
                ("DECISION__CAN_PUBLIC_RESEARCH_ANSWER", "MARK_UNKNOWN"),
                ("BUILD_TARGETED_QUERY", "TODO_API__TARGETED_RESEARCH"),
                ("TODO_API__TARGETED_RESEARCH", "VALIDATE_NEW_SOURCE"),
                ("VALIDATE_NEW_SOURCE", "NEW_EVIDENCE"),
                ("NEW_EVIDENCE", "RETURN_TO_EVALUATION"),
                ("MARK_UNKNOWN", "RETURN_TO_EVALUATION"),
            ],
            extra_nodes=[
                sticky(
                    "NOTE__RETRY_LIMITS",
                    "RETRY CONTROL\nRequired fields: retry_count, max_retries, reason_for_retry.\nNo infinite loops. Parent workflow must stop retrying when retry_count >= max_retries.",
                    460,
                    -260,
                    420,
                    190,
                )
            ],
        ),
    ),
    (
        "60_TRANSFORMATION_ORCHESTRATOR",
        workflow(
            "60_TRANSFORMATION_ORCHESTRATOR",
            OWNERS["gretel"],
            "Coordinate transformation child workflows from hypotheses through roadmap.",
            "finding.schema.json[] plus evidence ledger",
            "recommendation.schema.json[] plus roadmap and validation questions",
            [
                ("INPUT_CONTRACT__MERGED_FINDINGS", "Accept merged specialist findings."),
                ("TODO_LINK_SUBWORKFLOW__61_HYPOTHESIS_BUILDER", "LINK SUB-WORKFLOW AFTER IMPORT: 61_HYPOTHESIS_BUILDER."),
                ("TODO_LINK_SUBWORKFLOW__62_ROOT_CAUSE_DIAGNOSIS", "LINK SUB-WORKFLOW AFTER IMPORT: 62_ROOT_CAUSE_DIAGNOSIS."),
                ("PRIORITIZATION", "Prioritize by evidence strength, client relevance, and feasibility."),
                ("TODO_LINK_SUBWORKFLOW__63_ACTION_DESIGN", "LINK SUB-WORKFLOW AFTER IMPORT: 63_ACTION_DESIGN."),
                ("TODO_LINK_SUBWORKFLOW__64_KPI_DESIGN", "LINK SUB-WORKFLOW AFTER IMPORT: 64_KPI_DESIGN."),
                ("TODO_LINK_SUBWORKFLOW__65_CLIENT_VALIDATION_QUESTIONS", "LINK SUB-WORKFLOW AFTER IMPORT: 65_CLIENT_VALIDATION_QUESTIONS."),
                ("TODO_LINK_SUBWORKFLOW__66_90_DAY_ROADMAP", "LINK SUB-WORKFLOW AFTER IMPORT: 66_90_DAY_ROADMAP."),
                ("OUTPUT_CONTRACT__TRANSFORMATION_PACKAGE", "Return diagnosis-action-KPI-validation chain."),
            ],
            notes=[
                "TARGET FLOW\nMerged specialist findings -> 61 Hypothesis Builder -> 62 Root Cause / Diagnosis -> Prioritization -> 63 Action Design -> 64 KPI Design -> 65 Client Validation Questions -> 66 90-Day Roadmap -> Transformation Output Contract",
                "LINK SUB-WORKFLOW AFTER IMPORT\nReplace transformation TODO_LINK nodes after 61, 62, 63, 64, 65, and 66 have real n8n workflow IDs.",
            ],
        ),
    ),
    (
        "61_HYPOTHESIS_BUILDER",
        workflow(
            "61_HYPOTHESIS_BUILDER",
            OWNERS["gretel"],
            "Build explicit hypotheses from public evidence while preserving fact/inference/hypothesis/unknown boundaries.",
            "finding.schema.json[] plus evidence.schema.json[]",
            "hypothesis.schema.json[] plus updated finding references",
            [
                ("INPUT_CONTRACT__FINDINGS_AND_EVIDENCE", "Accept merged findings and traceable evidence ledger."),
                ("CLASSIFY_FACT_INFERENCE_HYPOTHESIS_UNKNOWN", "Preserve public-data-first distinction for every claim."),
                ("TODO_AGENT__HYPOTHESIS_BUILDER", "AGENT_INTERFACE__HYPOTHESIS_BUILDER."),
                ("STRUCTURE_HYPOTHESIS_RECORD", "Require evidence_ids, hypothesis, confidence, requires_validation=true, and validation_gap."),
                ("VALIDATE_NO_HYPOTHESIS_AS_FACT", "Prevent a public-evidence hypothesis from becoming a confirmed diagnosis."),
                ("OUTPUT_CONTRACT__HYPOTHESES", "Return structured hypotheses."),
            ],
            notes=[
                "PRODUCT LOGIC\nObserved fact: volunteer applications are collected through a website form.\nHypothesis: volunteer follow-up may rely on manual handoffs.\nThis must not become a confirmed diagnosis without validation.",
            ],
        ),
    ),
    (
        "62_ROOT_CAUSE_DIAGNOSIS",
        workflow(
            "62_ROOT_CAUSE_DIAGNOSIS",
            OWNERS["gretel"],
            "Distinguish observed problems, likely causes, validated causes, and unknowns.",
            "finding.schema.json[] plus hypothesis.schema.json[]",
            "diagnosis records with diagnosis_type",
            [
                ("INPUT_CONTRACT__FINDINGS_HYPOTHESES", "Accept findings and hypotheses."),
                ("CLASSIFY_DIAGNOSIS_TYPE", "Use observed_problem, likely_cause, validated_cause, or unknown."),
                ("TODO_AGENT__ROOT_CAUSE", "AGENT_INTERFACE__ROOT_CAUSE_DIAGNOSIS."),
                ("EVIDENCE_SUPPORT_CHECK", "Public evidence normally produces likely_cause, not validated_cause."),
                ("VALIDATION_BOUNDARY_CHECK", "Require clear evidence before validated_cause."),
                ("OUTPUT_CONTRACT__DIAGNOSIS", "Return structured diagnosis records."),
            ],
        ),
    ),
    (
        "63_ACTION_DESIGN",
        workflow(
            "63_ACTION_DESIGN",
            OWNERS["gretel"],
            "Generate concrete actions only where evidence and diagnosis justify action.",
            "diagnosis records plus prioritized findings/hypotheses",
            "action recommendations suitable for recommendation.schema.json",
            [
                ("INPUT_CONTRACT__DIAGNOSIS_PRIORITY", "Accept diagnosis and prioritization context."),
                ("ACTION_JUSTIFICATION_GATE", "Block implementation actions for weak or unvalidated hypotheses."),
                ("TODO_AGENT__ACTION_DESIGN", "AGENT_INTERFACE__ACTION_DESIGN."),
                ("STRUCTURE_ACTIONS", "Tie each action to diagnosis, finding_ids, and evidence/hypothesis support."),
                ("HUMAN_REVIEW_FLAG", "Mark sensitive or low-confidence actions for human review."),
                ("OUTPUT_CONTRACT__ACTIONS", "Return justified action records."),
            ],
        ),
    ),
    (
        "64_KPI_DESIGN",
        workflow(
            "64_KPI_DESIGN",
            OWNERS["gretel"],
            "Define KPIs without inventing unsupported baselines.",
            "action records plus findings/evidence",
            "kpi.schema.json[]",
            [
                ("INPUT_CONTRACT__ACTIONS_FINDINGS", "Accept actions with their evidence and finding links."),
                ("BASELINE_STATUS_CHECK", "Classify baseline as known, estimated, unknown, or not_applicable."),
                ("TODO_AGENT__KPI", "AGENT_INTERFACE__KPI_DESIGN."),
                ("DEFINE_KPI_FIELDS", "Define name, baseline, baseline_status, target, timeframe, and measurement_method."),
                ("NO_INVENTED_BASELINE_GATE", "Never invent a baseline where evidence does not support it."),
                ("OUTPUT_CONTRACT__KPIS", "Return KPI records."),
            ],
        ),
    ),
    (
        "65_CLIENT_VALIDATION_QUESTIONS",
        workflow(
            "65_CLIENT_VALIDATION_QUESTIONS",
            OWNERS["gretel"],
            "Turn evidence gaps and hypotheses into useful first-conversation consultant questions.",
            "finding.schema.json[] plus hypothesis.schema.json[] plus diagnosis records",
            "validation_question.schema.json[]",
            [
                ("INPUT_CONTRACT__GAPS_HYPOTHESES", "Accept evidence gaps, findings, hypotheses, and diagnosis records."),
                ("QUESTION_SCOPE_SELECTION", "Select questions tied to a finding or hypothesis."),
                ("TODO_AGENT__CLIENT_QUESTIONS", "AGENT_INTERFACE__CLIENT_VALIDATION_QUESTIONS."),
                ("NEUTRALITY_AND_SPECIFICITY_CHECK", "Ensure questions are specific, neutral, non-leading, and consultant-useful."),
                ("TRACEABILITY_CHECK", "Require finding_ids or hypothesis_ids on every question."),
                ("OUTPUT_CONTRACT__VALIDATION_QUESTIONS", "Return validation question records."),
            ],
            notes=[
                "CORE MVP WORKFLOW\nExample validation question: What happens internally after someone submits the volunteer form?",
            ],
        ),
    ),
    (
        "66_90_DAY_ROADMAP",
        workflow(
            "66_90_DAY_ROADMAP",
            OWNERS["gretel"],
            "Organize supported actions into 30, 60, and 90 day roadmap steps.",
            "actions, KPIs, validation questions, hypotheses, and diagnosis records",
            "roadmap_action.schema.json[]",
            [
                ("INPUT_CONTRACT__TRANSFORMATION_COMPONENTS", "Accept actions, KPIs, questions, hypotheses, and diagnoses."),
                ("UNVALIDATED_HYPOTHESIS_GATE", "Do not treat unvalidated hypotheses as confirmed implementation tasks."),
                ("DISCOVERY_ACTION_BUILDER", "Create discovery tasks such as Validate X during client workshop when appropriate."),
                ("TODO_AGENT__90_DAY_ROADMAP", "AGENT_INTERFACE__90_DAY_ROADMAP."),
                ("ORGANIZE_30_60_90_DAYS", "Group roadmap actions into 30 days, 60 days, and 90 days."),
                ("OUTPUT_CONTRACT__ROADMAP", "Return roadmap action records."),
            ],
            notes=[
                "ROADMAP RULE\nValidated or sufficiently supported actions may become implementation steps. Unvalidated hypotheses should become validation/discovery actions instead.",
            ],
        ),
    ),
    (
        "70_REPORT_QA_DELIVERY",
        workflow(
            "70_REPORT_QA_DELIVERY",
            OWNERS["gretel"],
            "Assemble and validate the Pre-Engagement Diagnostic Pack.",
            "run_context, evidence, findings, recommendations, KPIs, questions, roadmap",
            "final_package.schema.json",
            [
                ("INPUT_CONTRACT__REPORT_COMPONENTS", "Accept all report components."),
                ("REPORT_ASSEMBLY", "Assemble canonical JSON diagnostic pack."),
                ("EVIDENCE_QA", "Check evidence linkage and confidence/limitations."),
                ("CHECK_MATERIAL_CLAIMS", "Ensure material claims cite evidence IDs."),
                ("CHECK_UNKNOWNS", "Ensure unknowns remain visible."),
                ("CHECK_RECOMMENDATION_TRACEABILITY", "Ensure recommendations trace to findings/evidence."),
                ("DECISION__PASS_QA", "Branch based on QA result."),
                ("CORRECTION_PLACEHOLDER", "Placeholder for correction loop; no final reasoning implementation yet."),
                ("TODO_STORAGE__FINAL_RUN", "Placeholder for saving canonical output."),
                ("EXPORT_PLACEHOLDER", "Future exports: JSON, Markdown, HTML, PDF. JSON is canonical."),
                ("RETURN_FINAL_PACKAGE", "Return final pre-engagement diagnostic pack."),
            ],
            edges=[
                ("START__SUB_WORKFLOW_TRIGGER", "INPUT_CONTRACT__REPORT_COMPONENTS"),
                ("INPUT_CONTRACT__REPORT_COMPONENTS", "REPORT_ASSEMBLY"),
                ("REPORT_ASSEMBLY", "EVIDENCE_QA"),
                ("EVIDENCE_QA", "CHECK_MATERIAL_CLAIMS"),
                ("CHECK_MATERIAL_CLAIMS", "CHECK_UNKNOWNS"),
                ("CHECK_UNKNOWNS", "CHECK_RECOMMENDATION_TRACEABILITY"),
                ("CHECK_RECOMMENDATION_TRACEABILITY", "DECISION__PASS_QA"),
                ("DECISION__PASS_QA", "TODO_STORAGE__FINAL_RUN"),
                ("DECISION__PASS_QA", "CORRECTION_PLACEHOLDER"),
                ("CORRECTION_PLACEHOLDER", "REPORT_ASSEMBLY"),
                ("TODO_STORAGE__FINAL_RUN", "EXPORT_PLACEHOLDER"),
                ("EXPORT_PLACEHOLDER", "RETURN_FINAL_PACKAGE"),
            ],
        ),
    ),
    (
        "99_GLOBAL_ERROR_HANDLER",
        workflow(
            "99_GLOBAL_ERROR_HANDLER",
            OWNERS["shared"],
            "Centralized error observability for workflow failures.",
            "n8n error trigger event",
            "normalized error log/notification placeholder",
            [
                ("NORMALIZE_ERROR", "Normalize n8n error payload."),
                ("CAPTURE_ERROR_CONTEXT", "Capture run_id, workflow_name, node_name, timestamp, error_type, message, partial_state_available."),
                ("CLASSIFY_RECOVERABLE_FATAL", "Classify as recoverable or fatal."),
                ("TODO_STORAGE__ERROR_LOG", "Placeholder for durable logging."),
                ("TODO_NOTIFICATION__ERROR_ALERT", "Placeholder for future notification channel. No credentials configured."),
                ("OUTPUT_CONTRACT__ERROR_EVENT", "Return normalized error event."),
            ],
            trigger="error",
        ),
    ),
]


SCHEMAS = {
    "run_context.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/run_context.schema.json",
        "title": "Run Context",
        "type": "object",
        "required": ["run_id", "organization", "status", "started_at", "errors"],
        "additionalProperties": True,
        "properties": {
            "run_id": {"type": "string", "pattern": "^RUN-"},
            "organization": {
                "type": "object",
                "required": ["name", "website", "country"],
                "additionalProperties": True,
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "website": {"type": "string", "format": "uri"},
                    "country": {"type": "string", "minLength": 1},
                    "mission_area": {"type": ["string", "null"]},
                },
            },
            "current_challenge": {"type": ["string", "null"]},
            "uploaded_document_refs": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
            "status": {
                "type": "string",
                "enum": ["created", "researching", "analyzing", "qa", "completed", "failed"],
            },
            "started_at": {"type": "string", "format": "date-time"},
            "errors": {"type": "array", "items": {"type": "object"}},
        },
        "examples": [
            {
                "run_id": "RUN-...",
                "organization": {
                    "name": "",
                    "website": "",
                    "country": "",
                    "mission_area": None,
                },
                "current_challenge": None,
                "status": "created",
                "started_at": "",
                "errors": [],
            }
        ],
    },
    "source.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/source.schema.json",
        "title": "Source",
        "type": "object",
        "required": [
            "source_id",
            "title",
            "url",
            "source_type",
            "retrieved_at",
            "is_official",
        ],
        "additionalProperties": True,
        "properties": {
            "source_id": {"type": "string", "pattern": "^SRC-"},
            "title": {"type": "string"},
            "url": {"type": "string", "format": "uri"},
            "source_type": {"type": "string"},
            "publisher": {"type": ["string", "null"]},
            "publication_date": {"type": ["string", "null"], "format": "date"},
            "retrieved_at": {"type": "string", "format": "date-time"},
            "authority_level": {
                "type": ["string", "null"],
                "enum": ["official", "registry", "independent", "media", "unknown", None],
            },
            "freshness": {
                "type": ["string", "null"],
                "enum": ["current", "recent", "stale", "unknown", None],
            },
            "is_official": {"type": "boolean"},
        },
    },
    "evidence.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/evidence.schema.json",
        "title": "Evidence",
        "type": "object",
        "required": [
            "evidence_id",
            "run_id",
            "claim",
            "source_ids",
            "domain",
            "evidence_type",
            "confidence",
            "status",
            "contradiction_ids",
            "requires_validation",
        ],
        "additionalProperties": True,
        "properties": {
            "evidence_id": {"type": "string", "pattern": "^EV-"},
            "run_id": {"type": "string"},
            "claim": {"type": "string"},
            "source_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^SRC-"},
            },
            "domain": {"type": "string"},
            "evidence_type": {
                "type": "string",
                "enum": ["fact", "inference", "hypothesis", "unknown"],
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "status": {
                "type": "string",
                "enum": [
                    "supported",
                    "partially_supported",
                    "contradicted",
                    "insufficient_evidence",
                    "unknown",
                ],
            },
            "contradiction_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^EV-"},
            },
            "requires_validation": {"type": "boolean"},
        },
    },
    "finding.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/finding.schema.json",
        "title": "Finding",
        "type": "object",
        "required": [
            "finding_id",
            "domain",
            "finding",
            "evidence_ids",
            "finding_type",
            "confidence",
            "requires_validation",
            "validation_question",
        ],
        "additionalProperties": True,
        "properties": {
            "finding_id": {"type": "string", "pattern": "^F-"},
            "domain": {"type": "string"},
            "finding": {"type": "string"},
            "evidence_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^EV-"},
            },
            "finding_type": {
                "type": "string",
                "enum": ["observed", "inferred", "hypothesis", "unknown"],
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "requires_validation": {"type": "boolean"},
            "validation_question": {"type": ["string", "null"]},
        },
    },
    "hypothesis.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/hypothesis.schema.json",
        "title": "Hypothesis",
        "type": "object",
        "required": [
            "hypothesis_id",
            "run_id",
            "domain",
            "evidence_ids",
            "finding_ids",
            "hypothesis",
            "confidence",
            "requires_validation",
            "validation_gap",
        ],
        "additionalProperties": True,
        "properties": {
            "hypothesis_id": {"type": "string", "pattern": "^HYP-"},
            "run_id": {"type": "string"},
            "domain": {"type": "string"},
            "evidence_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^EV-"},
            },
            "finding_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^F-"},
            },
            "hypothesis": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "requires_validation": {"const": True},
            "validation_gap": {"type": "string"},
        },
    },
    "diagnosis.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/diagnosis.schema.json",
        "title": "Diagnosis",
        "type": "object",
        "required": [
            "diagnosis_id",
            "domain",
            "diagnosis_type",
            "statement",
            "finding_ids",
            "hypothesis_ids",
            "evidence_ids",
            "confidence",
            "requires_validation",
        ],
        "additionalProperties": True,
        "properties": {
            "diagnosis_id": {"type": "string", "pattern": "^DX-"},
            "domain": {"type": "string"},
            "diagnosis_type": {
                "type": "string",
                "enum": ["observed_problem", "likely_cause", "validated_cause", "unknown"],
            },
            "statement": {"type": "string"},
            "finding_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^F-"},
            },
            "hypothesis_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^HYP-"},
            },
            "evidence_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^EV-"},
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "requires_validation": {"type": "boolean"},
        },
    },
    "validation_question.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/validation_question.schema.json",
        "title": "Validation Question",
        "type": "object",
        "required": [
            "question_id",
            "finding_ids",
            "hypothesis_ids",
            "question",
            "purpose",
            "domain",
            "priority",
        ],
        "additionalProperties": True,
        "properties": {
            "question_id": {"type": "string", "pattern": "^Q-"},
            "finding_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^F-"},
            },
            "hypothesis_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^HYP-"},
            },
            "question": {"type": "string"},
            "purpose": {"type": "string"},
            "domain": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        },
    },
    "kpi.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/kpi.schema.json",
        "title": "KPI",
        "type": "object",
        "required": [
            "name",
            "baseline",
            "baseline_status",
            "target",
            "timeframe",
            "measurement_method",
        ],
        "additionalProperties": True,
        "properties": {
            "name": {"type": "string"},
            "baseline": {"type": ["string", "number", "null"]},
            "baseline_status": {
                "type": "string",
                "enum": ["known", "estimated", "unknown", "not_applicable"],
            },
            "target": {"type": ["string", "number", "null"]},
            "timeframe": {"type": ["string", "null"]},
            "measurement_method": {"type": "string"},
        },
    },
    "roadmap_action.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/roadmap_action.schema.json",
        "title": "Roadmap Action",
        "type": "object",
        "required": [
            "roadmap_action_id",
            "time_bucket",
            "action",
            "action_type",
            "recommendation_ids",
            "hypothesis_ids",
            "validation_question_ids",
        ],
        "additionalProperties": True,
        "properties": {
            "roadmap_action_id": {"type": "string", "pattern": "^RA-"},
            "time_bucket": {"type": "string", "enum": ["30_days", "60_days", "90_days"]},
            "action": {"type": "string"},
            "action_type": {"type": "string", "enum": ["implementation", "validation", "discovery"]},
            "recommendation_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^REC-"},
            },
            "hypothesis_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^HYP-"},
            },
            "validation_question_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^Q-"},
            },
        },
    },
    "recommendation.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/recommendation.schema.json",
        "title": "Recommendation",
        "type": "object",
        "required": [
            "recommendation_id",
            "finding_ids",
            "diagnosis",
            "action",
            "priority",
            "kpi",
            "confidence",
            "requires_human_review",
        ],
        "additionalProperties": True,
        "properties": {
            "recommendation_id": {"type": "string", "pattern": "^REC-"},
            "finding_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^F-"},
            },
            "diagnosis_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^DX-"},
                "default": [],
            },
            "diagnosis": {"type": "string"},
            "action": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            "kpi": {
                "type": "object",
                "required": [
                    "name",
                    "baseline",
                    "baseline_status",
                    "target",
                    "timeframe",
                    "measurement_method",
                ],
                "additionalProperties": True,
                "properties": {
                    "name": {"type": "string"},
                    "baseline": {"type": ["string", "number", "null"]},
                    "baseline_status": {
                        "type": "string",
                        "enum": ["known", "estimated", "unknown", "not_applicable"],
                    },
                    "target": {"type": ["string", "number", "null"]},
                    "timeframe": {"type": ["string", "null"]},
                    "measurement_method": {"type": "string"},
                },
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "requires_human_review": {"type": "boolean", "default": True},
        },
    },
    "final_package.schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/contracts/final_package.schema.json",
        "title": "Pre-Engagement Diagnostic Pack",
        "type": "object",
        "required": [
            "run_context",
            "organization_snapshot",
            "public_evidence_map",
            "evidence_ledger",
            "findings",
            "hypotheses",
            "diagnoses",
            "recommendations",
            "kpis",
            "client_validation_questions",
            "roadmap_90_day",
            "missing_information",
            "confidence_limitations",
        ],
        "additionalProperties": True,
        "properties": {
            "run_context": {"$ref": "run_context.schema.json"},
            "organization_snapshot": {"type": "object"},
            "public_evidence_map": {"type": "array", "items": {"$ref": "source.schema.json"}},
            "revenue_resilience": {"type": "object"},
            "impact_and_evidence": {"type": "object"},
            "operations_stakeholder_experience": {"type": "object"},
            "findings": {"type": "array", "items": {"$ref": "finding.schema.json"}},
            "hypotheses": {"type": "array", "items": {"$ref": "hypothesis.schema.json"}},
            "diagnoses": {"type": "array", "items": {"$ref": "diagnosis.schema.json"}},
            "priority_hypotheses": {"type": "array", "items": {"$ref": "finding.schema.json"}},
            "recommendations": {"type": "array", "items": {"$ref": "recommendation.schema.json"}},
            "actions": {"type": "array", "items": {"type": "object"}},
            "kpis": {"type": "array", "items": {"$ref": "kpi.schema.json"}},
            "client_validation_questions": {
                "type": "array",
                "items": {"$ref": "validation_question.schema.json"},
            },
            "evidence_ledger": {"type": "array", "items": {"$ref": "evidence.schema.json"}},
            "missing_information": {"type": "array", "items": {"type": "string"}},
            "confidence_limitations": {"type": "array", "items": {"type": "string"}},
            "roadmap_90_day": {
                "type": ["array", "null"],
                "items": {"$ref": "roadmap_action.schema.json"},
            },
        },
    },
}


WORKFLOW_MAP_ROWS = [
    ("00_MAIN_ORCHESTRATOR", "SHARED", "Coordinates full run", "Initial run request", "Final package", "10,20,30,40,50,60,70", "Sub-workflow links"),
    ("10_INTAKE_AND_ORG_RESOLVER", "SHARED", "Normalizes intake and run context", "Organization request", "Run context", "None", "Organization resolver"),
    ("20_CONTEXT_RESEARCH_ORCHESTRATOR", "PAOLA TRACK A", "Plans and coordinates public research", "Run context", "Context pack", "21,22,23,24", "Research planner plus channel links"),
    ("21_WEB_SEARCH", "PAOLA TRACK A", "Public web discovery", "Research task", "Sources", "None", "Web search API"),
    ("22_WEBSITE_EXTRACTION", "PAOLA TRACK A", "Official site extraction", "Official URL", "Sources/content", "None", "Extraction API/provider"),
    ("23_DOCUMENT_PUBLIC_DATA_RESEARCH", "PAOLA TRACK A", "Public reports and registry data", "Document/public data task", "Sources/documents", "None", "Fetch/extraction tools"),
    ("24_NEWS_EXTERNAL_CONTEXT", "PAOLA TRACK A", "Recent external context", "News task", "Sources", "None", "News/search API"),
    ("30_EVIDENCE_PIPELINE", "PAOLA TRACK A", "Turns context into traceable evidence", "Context pack", "Evidence ledger", "54 optional later", "Evidence extraction agent/storage"),
    ("40_RAG_RETRIEVAL_PIPELINE", "PAOLA TRACK A", "Retrieves framework context", "Evidence/domain", "RAG context", "Knowledge base", "Vector store"),
    ("50_ANALYSIS_ORCHESTRATOR", "SHARED", "Dispatches specialist analysis", "Evidence + RAG", "Findings", "51,52,53", "Sub-workflow links"),
    ("51_REVENUE_RESILIENCE_AGENT", "PAOLA TRACK A", "Revenue resilience analysis", "Revenue evidence/RAG", "Revenue findings", "40", "Revenue agent"),
    ("52_IMPACT_EVIDENCE_AGENT", "PAOLA TRACK A", "Impact and evidence analysis", "Impact evidence/RAG", "Impact findings", "40", "Impact agent"),
    ("53_OPERATIONS_CX_AGENT", "GRETEL TRACK B", "Operations and CX analysis", "Operations evidence/RAG", "Operations findings", "40", "Operations/CX agent"),
    ("54_EVIDENCE_GAP_RESEARCH", "PAOLA TRACK A", "Targeted evidence gap research", "Missing evidence request", "New evidence/unknown", "Research providers", "Targeted research API"),
    ("60_TRANSFORMATION_ORCHESTRATOR", "GRETEL TRACK B", "Coordinates transformation child workflows", "Findings/evidence", "Recommendations/roadmap/questions", "61,62,63,64,65,66", "Sub-workflow links"),
    ("61_HYPOTHESIS_BUILDER", "GRETEL TRACK B", "Builds explicit hypotheses without upgrading them to facts", "Findings/evidence", "Hypotheses", "50,30", "Hypothesis builder agent"),
    ("62_ROOT_CAUSE_DIAGNOSIS", "GRETEL TRACK B", "Distinguishes observed problems, likely causes, validated causes, and unknowns", "Findings/hypotheses", "Diagnoses", "61", "Root cause agent"),
    ("63_ACTION_DESIGN", "GRETEL TRACK B", "Designs justified actions only where supported", "Diagnoses/priorities", "Actions", "62", "Action design agent"),
    ("64_KPI_DESIGN", "GRETEL TRACK B", "Defines KPIs without inventing baselines", "Actions/findings", "KPIs", "63", "KPI agent"),
    ("65_CLIENT_VALIDATION_QUESTIONS", "GRETEL TRACK B", "Turns gaps and hypotheses into consultant questions", "Gaps/hypotheses/diagnoses", "Validation questions", "61,62", "Client questions agent"),
    ("66_90_DAY_ROADMAP", "GRETEL TRACK B", "Organizes supported work into 30/60/90 day roadmap", "Actions/KPIs/questions", "Roadmap actions", "63,64,65", "Roadmap agent"),
    ("70_REPORT_QA_DELIVERY", "GRETEL TRACK B", "Assembles and QAs diagnostic pack", "Report components", "Final package", "All upstream", "Storage/export"),
    ("99_GLOBAL_ERROR_HANDLER", "SHARED", "Normalizes errors", "n8n error event", "Error event/log", "All workflows may attach", "Logging/notification"),
]


def write_docs():
    workflow_map = [
        "# Workflow Map",
        "",
        "All workflows are skeletons, inactive by default, and intentionally use TODO placeholders for APIs, agents, storage, RAG, and sub-workflow links.",
        "",
        "| Workflow | Owner | Purpose | Input | Output | Dependencies | Future configuration |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in WORKFLOW_MAP_ROWS:
        workflow_map.append("| " + " | ".join(row) + " |")
    workflow_map.append("")
    workflow_map.append("Core principle: every stage must preserve the distinction between fact, inference, hypothesis, and unknown.")
    (ROOT / "workflows" / "WORKFLOW_MAP.md").write_text("\n".join(workflow_map) + "\n", encoding="utf-8")

    import_order = """# Import Order

Recommended sequence:

1. 99_GLOBAL_ERROR_HANDLER
2. 21_WEB_SEARCH
3. 22_WEBSITE_EXTRACTION
4. 23_DOCUMENT_PUBLIC_DATA_RESEARCH
5. 24_NEWS_EXTERNAL_CONTEXT
6. 51_REVENUE_RESILIENCE_AGENT
7. 52_IMPACT_EVIDENCE_AGENT
8. 53_OPERATIONS_CX_AGENT
9. 54_EVIDENCE_GAP_RESEARCH
10. 40_RAG_RETRIEVAL_PIPELINE
11. 30_EVIDENCE_PIPELINE
12. 61_HYPOTHESIS_BUILDER
13. 62_ROOT_CAUSE_DIAGNOSIS
14. 63_ACTION_DESIGN
15. 64_KPI_DESIGN
16. 65_CLIENT_VALIDATION_QUESTIONS
17. 66_90_DAY_ROADMAP
18. 60_TRANSFORMATION_ORCHESTRATOR
19. 50_ANALYSIS_ORCHESTRATOR
20. 20_CONTEXT_RESEARCH_ORCHESTRATOR
21. 10_INTAKE_AND_ORG_RESOLVER
22. 70_REPORT_QA_DELIVERY
23. 00_MAIN_ORCHESTRATOR

Why this order:

- Import leaf workflows first so parent placeholders can later be replaced with real Execute Workflow nodes.
- Import shared error handling before normal workflows so it can be attached during configuration.
- Import transformation child workflows before 60_TRANSFORMATION_ORCHESTRATOR.
- Import orchestrators after their children.
- Import the main orchestrator last because it links the whole architecture.

No workflow IDs are hardcoded in these skeletons. Link sub-workflows manually after import.
"""
    (ROOT / "workflows" / "IMPORT_ORDER.md").write_text(import_order, encoding="utf-8")

    checks = [
        "# Configuration Checklist",
        "",
        "Use this checklist per workflow during n8n setup.",
        "",
    ]
    for stem, _wf in WORKFLOWS:
        checks.extend(
            [
                f"## {stem}",
                "",
                "- [ ] Imported",
                "- [ ] Trigger works",
                "- [ ] Input contract validated",
                "- [ ] API configured",
                "- [ ] Agent configured",
                "- [ ] Output matches contract",
                "- [ ] Error path tested",
                "- [ ] Connected to parent workflow",
                "- [ ] Integration test passed",
                "",
            ]
        )
    (ROOT / "workflows" / "CONFIGURATION_CHECKLIST.md").write_text("\n".join(checks), encoding="utf-8")

    contracts_readme = """# Contracts

These JSON Schemas define the shared data contracts for the n8n skeleton architecture.

- `run_context.schema.json`: canonical run and organization state.
- `source.schema.json`: public source metadata.
- `evidence.schema.json`: traceable claim record with fact/inference/hypothesis/unknown typing.
- `finding.schema.json`: structured specialist analysis finding.
- `hypothesis.schema.json`: public-data-first hypothesis with evidence IDs, confidence, validation requirement, and validation gap.
- `diagnosis.schema.json`: observed problem, likely cause, validated cause, or unknown.
- `validation_question.schema.json`: consultant-facing validation questions tied to findings or hypotheses.
- `kpi.schema.json`: KPI definition with baseline status and measurement method.
- `roadmap_action.schema.json`: 30/60/90 day action, validation, or discovery step.
- `recommendation.schema.json`: diagnosis, action, KPI, priority, and review flag.
- `final_package.schema.json`: canonical Pre-Engagement Diagnostic Pack.

Contract rules:

- A hypothesis must never silently become a fact.
- Missing public evidence should be represented as `unknown` or `insufficient_evidence`.
- Public evidence should normally create `likely_cause`, not `validated_cause`.
- Baselines must not be invented; use `baseline_status: "unknown"` when needed.
- Recommendations must trace back to finding IDs and, through findings, to evidence IDs.
- Validation questions must be specific, neutral, non-leading, and tied to a finding or hypothesis.
- JSON is the canonical final output format; Markdown, HTML, and PDF are future exports.
"""
    (CONTRACT_DIR / "README.md").write_text(contracts_readme, encoding="utf-8")


def main():
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "workflows").mkdir(parents=True, exist_ok=True)

    expected_workflow_files = {f"{stem}.json" for stem, _data in WORKFLOWS}
    for path in WORKFLOW_DIR.glob("*.json"):
        if path.name not in expected_workflow_files:
            path.unlink()

    expected_contract_files = set(SCHEMAS)
    for path in CONTRACT_DIR.glob("*.schema.json"):
        if path.name not in expected_contract_files:
            path.unlink()

    for stem, data in WORKFLOWS:
        path = WORKFLOW_DIR / f"{stem}.json"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    for filename, schema in SCHEMAS.items():
        (CONTRACT_DIR / filename).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

    write_docs()
    try:
        from configure_paola_p0_n8n_exports import configure_paola_p0_workflows

        configure_paola_p0_workflows(ROOT)
    except ImportError:
        pass
    try:
        from configure_paola_22_website_extraction import configure_paola_22_workflows

        configure_paola_22_workflows(ROOT)
    except ImportError:
        pass
    try:
        from configure_paola_23_document_research import configure_paola_23_workflows

        configure_paola_23_workflows(ROOT)
    except ImportError:
        pass
    try:
        from configure_paola_52_impact_evidence import configure_paola_52_workflows

        configure_paola_52_workflows(ROOT)
    except ImportError:
        pass
    print(f"Generated {len(WORKFLOWS)} workflows and {len(SCHEMAS)} schemas.")


if __name__ == "__main__":
    main()
