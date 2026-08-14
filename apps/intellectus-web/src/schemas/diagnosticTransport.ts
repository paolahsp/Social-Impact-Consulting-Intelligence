import { z } from 'zod'
import { DiagnosticInputSchema } from './diagnosticRun'

export const DiagnosticContractVersionSchema = z.literal('1.0')
const HttpUrlSchema = z.url().refine((value) => ['http:', 'https:'].includes(new URL(value).protocol))

const SourceSchema = z.object({
  source_id: z.string().regex(/^SRC-/),
  title: z.string().min(1),
  url: HttpUrlSchema,
  source_type: z.string().min(1),
  publisher: z.string().nullable().optional(),
  publication_date: z.string().nullable().optional(),
  retrieved_at: z.string().min(1),
  authority_level: z.string().nullable().optional(),
  freshness: z.string().nullable().optional(),
  is_official: z.boolean(),
}).loose()

const EvidenceSchema = z.object({
  evidence_id: z.string().regex(/^EV-/),
  run_id: z.string().min(1),
  claim: z.string().min(1),
  source_ids: z.array(z.string().regex(/^SRC-/)),
  domain: z.string().min(1),
  evidence_type: z.enum(['fact', 'inference', 'hypothesis', 'unknown']),
  confidence: z.number().min(0).max(1),
  status: z.enum(['supported', 'partially_supported', 'contradicted', 'insufficient_evidence', 'unknown']),
  contradiction_ids: z.array(z.string().regex(/^EV-/)),
  requires_validation: z.boolean(),
}).loose()

export const OperationsFindingSchema = z.object({
  finding_id: z.string().regex(/^F-OPS-/),
  domain: z.literal('operations_cx'),
  finding: z.string().min(1),
  evidence_ids: z.array(z.string().regex(/^EV-/)).min(1),
  finding_type: z.enum(['observed', 'inferred', 'hypothesis', 'unknown']),
  confidence: z.number().min(0).max(1),
  requires_validation: z.boolean(),
  validation_question: z.string().min(1).nullable(),
}).loose()

const UpstreamFindingSchema = OperationsFindingSchema.extend({
  finding_id: z.string().regex(/^F-/),
  domain: z.string().min(1),
}).loose()

export const EvidenceHandoffSchema = z.object({
  run_context: z.object({
    run_id: z.string().regex(/^RUN-/),
    organization: z.object({
      name: z.string().min(1),
      website: HttpUrlSchema,
      country: z.string().min(1),
    }).loose(),
    status: z.enum(['created', 'researching', 'analyzing', 'qa', 'completed', 'failed']),
    started_at: z.string().min(1),
    errors: z.array(z.record(z.string(), z.unknown())),
  }).loose(),
  sources: z.array(SourceSchema),
  evidence: z.array(EvidenceSchema),
  findings: z.array(UpstreamFindingSchema),
  unknowns: z.array(z.record(z.string(), z.unknown())),
  contradictions: z.array(z.record(z.string(), z.unknown())),
  rag_metadata: z.record(z.string(), z.unknown()),
}).superRefine((handoff, context) => {
  const sourceIds = new Set(handoff.sources.map((source) => source.source_id))
  const evidenceIds = new Set(handoff.evidence.map((evidence) => evidence.evidence_id))
  const findingIds = new Set(handoff.findings.map((finding) => finding.finding_id))
  if (sourceIds.size !== handoff.sources.length) context.addIssue({ code: 'custom', path: ['sources'], message: 'Source IDs must be unique' })
  if (evidenceIds.size !== handoff.evidence.length) context.addIssue({ code: 'custom', path: ['evidence'], message: 'Evidence IDs must be unique' })
  if (findingIds.size !== handoff.findings.length) context.addIssue({ code: 'custom', path: ['findings'], message: 'Finding IDs must be unique' })
  handoff.evidence.forEach((evidence, evidenceIndex) => {
    evidence.source_ids.forEach((sourceId, sourceIndex) => {
      if (!sourceIds.has(sourceId)) context.addIssue({ code: 'custom', path: ['evidence', evidenceIndex, 'source_ids', sourceIndex], message: 'Unknown source reference' })
    })
    evidence.contradiction_ids.forEach((evidenceId, contradictionIndex) => {
      if (!evidenceIds.has(evidenceId)) context.addIssue({ code: 'custom', path: ['evidence', evidenceIndex, 'contradiction_ids', contradictionIndex], message: 'Unknown contradiction reference' })
    })
  })
  handoff.findings.forEach((finding, findingIndex) => finding.evidence_ids.forEach((evidenceId, evidenceIndex) => {
    if (!evidenceIds.has(evidenceId)) context.addIssue({ code: 'custom', path: ['findings', findingIndex, 'evidence_ids', evidenceIndex], message: 'Unknown evidence reference' })
  }))
})

export const DiagnosticTransportRequestSchema = z.object({
  contract_version: DiagnosticContractVersionSchema,
  mode: z.enum(['live', 'demo']),
  correlation_id: z.string().min(1).optional(),
  run_id: z.string().min(1).optional(),
  intake: DiagnosticInputSchema,
  evidence_handoff: EvidenceHandoffSchema.optional(),
}).superRefine((request, context) => {
  if (request.mode === 'demo' && request.evidence_handoff) {
    context.addIssue({ code: 'custom', path: ['evidence_handoff'], message: 'Demo mode cannot accept a supplied evidence handoff' })
  }
  if (request.mode === 'demo' && request.intake.uploaded_document_refs.length > 0) {
    context.addIssue({ code: 'custom', path: ['intake', 'uploaded_document_refs'], message: 'Demo mode cannot use document references' })
  }
})

const ResponseBaseSchema = z.object({
  contract_version: DiagnosticContractVersionSchema,
  correlation_id: z.string().min(1),
  run_id: z.string().min(1),
  demo: z.boolean(),
  message: z.string().min(1),
})

const CompletedResponseSchema = ResponseBaseSchema.extend({
  status: z.literal('completed'),
  completed_at: z.string().min(1),
  data: z.object({
    intake: DiagnosticInputSchema,
    sources: z.array(SourceSchema),
    evidence: z.array(EvidenceSchema),
    findings: z.array(OperationsFindingSchema).min(1),
    unknowns: z.array(z.record(z.string(), z.unknown())),
    contradictions: z.array(z.record(z.string(), z.unknown())),
    rag_metadata: z.record(z.string(), z.unknown()),
  }),
}).superRefine((response, context) => {
  const sourceIds = new Set(response.data.sources.map((source) => source.source_id))
  const evidenceIds = new Set(response.data.evidence.map((evidence) => evidence.evidence_id))
  const findingIds = new Set(response.data.findings.map((finding) => finding.finding_id))
  if (sourceIds.size !== response.data.sources.length) context.addIssue({ code: 'custom', path: ['data', 'sources'], message: 'Source IDs must be unique' })
  if (evidenceIds.size !== response.data.evidence.length) context.addIssue({ code: 'custom', path: ['data', 'evidence'], message: 'Evidence IDs must be unique' })
  if (findingIds.size !== response.data.findings.length) context.addIssue({ code: 'custom', path: ['data', 'findings'], message: 'Finding IDs must be unique' })
  response.data.evidence.forEach((evidence, evidenceIndex) => evidence.source_ids.forEach((sourceId, sourceIndex) => {
    if (!sourceIds.has(sourceId)) context.addIssue({ code: 'custom', path: ['data', 'evidence', evidenceIndex, 'source_ids', sourceIndex], message: 'Unknown source reference' })
  }))
  response.data.findings.forEach((finding, findingIndex) => {
    finding.evidence_ids.forEach((evidenceId, evidenceIndex) => {
      if (!evidenceIds.has(evidenceId)) context.addIssue({ code: 'custom', path: ['data', 'findings', findingIndex, 'evidence_ids', evidenceIndex], message: 'Unknown evidence reference' })
    })
    if (finding.finding_type === 'observed' && (finding.requires_validation || finding.validation_question !== null)) {
      context.addIssue({ code: 'custom', path: ['data', 'findings', findingIndex], message: 'Observed findings must remain directly observable' })
    }
    if (finding.finding_type !== 'observed' && (!finding.requires_validation || !finding.validation_question)) {
      context.addIssue({ code: 'custom', path: ['data', 'findings', findingIndex], message: 'Non-observed findings require validation' })
    }
  })
})

const NeedsEvidenceResponseSchema = ResponseBaseSchema.extend({
  status: z.literal('needs_evidence'),
  demo: z.literal(false),
  error: z.object({ code: z.literal('evidence_required') }),
})

const ErrorResponseSchema = ResponseBaseSchema.extend({
  status: z.literal('error'),
  error: z.object({
    code: z.enum(['invalid_request', 'upstream_failure', 'invalid_upstream_response']),
  }),
})

export const DiagnosticTransportResponseSchema = z.discriminatedUnion('status', [
  CompletedResponseSchema,
  NeedsEvidenceResponseSchema,
  ErrorResponseSchema,
])

export type DiagnosticTransportRequest = z.infer<typeof DiagnosticTransportRequestSchema>
export type DiagnosticTransportResponse = z.infer<typeof DiagnosticTransportResponseSchema>
export type CompletedDiagnosticTransportResponse = z.infer<typeof CompletedResponseSchema>
