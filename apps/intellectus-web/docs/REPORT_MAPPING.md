# Conversation brief data mapping

The local demo validates the UI-to-adapter boundary. Shared workflow field
paths that were not available in this workspace are marked **To verify against
shared repository**.

| Concept | Web intake | Paola research output | Gretel transformation output | `final_package` | Brief section | Local fallback | Display rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Organization | `organization_name` | Context only | Context only | `run_context.input.organization_name` | Metadata | Current form value | Always show |
| Website | `website` | Research input | Context only | `run_context.input.website` | Not repeated | Current form value | Keep available to adapter |
| Country code | `country` = `US` | Research context | Context | `run_context.input.country` | Metadata lookup input | `US` | Preserve ISO alpha-2 |
| Country name | Derived centrally = `United States` | **To verify against shared repository** | **To verify against shared repository** | No separate field currently | `United States` | Central `getCountryName` lookup | Real adapter derives and sends both when required |
| Research window | `research_window` | **To verify against shared repository** | Context | `run_context.input.research_window` | Metadata | Current dates | Limits recent external context; does not exclude relevant official reports; current workflows are not claimed to consume it |
| Document references | `uploaded_document_refs` | Research input | Context | `run_context.input.uploaded_document_refs` | Sources and limitations when real | Empty array | Browser Files remain separate and are not sources |
| Sources | — | Sources | Context | `public_evidence_map`, `evidence_ledger` | Sources and limitations | None reviewed | Show only reviewed sources |
| Evidence | — | Evidence | Context | `public_evidence_map`, `evidence_ledger` | Available material | Prudently worded demo findings | Never label demo copy approved evidence |
| Findings | — | Findings | Input to transformation | `findings` | Available material | Scenario findings | Show when present |
| Unknowns | — | Unknowns | Input to transformation | `missing_information` | What remains unclear | Scenario gaps | Plain language only |
| Contradictions | — | Contradictions | Input to transformation | **To verify against shared repository** | Sources and limitations | None | Show only when present and reviewed |
| Hypotheses | — | Context | Hypotheses | `hypotheses` | Supporting detail | Scenario possibilities | Closed initially outside final brief |
| Workshop questions | Conversation choices | Context | Questions | `client_validation_questions` | Workshop agenda | Five scenario questions | Show selected questions only |
| Recommendations | — | Context | Recommendations | `recommendations` | Suggested next step | One scenario action | Requires consultant addition to brief |
| KPIs | — | Context | KPIs | `kpis` | How progress could be measured | Two scenario measures | State that baseline is not established |
| Validation plan | — | Context | Validation actions | `roadmap_90_day` | Validation plan | Validate–Design–Pilot | Compact sequence |
| Consultant notes | Session state plus explicit inclusion choice | Must not overwrite | Must not overwrite | Outside workflow result | Consultant notes | Empty and private | Without inclusion: `Internal preparation only`; when consciously included: `Consultant-reviewed / client-usable`; show only when included and non-empty |
| Review status | Session state | Must not overwrite | Must not overwrite | Outside workflow result | Metadata and Final review | Draft | Human decision: Draft or Ready |
| Limitations | — | Source limitations | Confidence framing | `confidence_limitations` | Sources and limitations | Local-demo limitations | Closed on screen; visible in print |

Paola supplies sources, evidence, findings, unknowns and contradictions. Gretel
supplies hypotheses, questions, recommendations, KPIs and validation actions.
The resulting `final_package` supplies the brief. New workflow results must not
overwrite consultant notes or the human Draft/Ready decision.

Consultant notes remain human-controlled session state. The workflow must never
overwrite their text or inclusion choice. Private notes are excluded from the
brief, print output and Calendar description.
