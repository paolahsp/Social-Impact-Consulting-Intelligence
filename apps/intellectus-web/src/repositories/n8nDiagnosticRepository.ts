import { z } from 'zod'
import {
  DiagnosticTransportRequestSchema,
  DiagnosticTransportResponseSchema,
  type CompletedDiagnosticTransportResponse,
} from '../schemas/diagnosticTransport'
import { DiagnosticInputSchema, DiagnosticResultSchema } from '../schemas/diagnosticRun'
import type { DiagnosticInput, DiagnosticResult } from '../types/diagnostic'
import type { DiagnosticRepository } from './diagnosticRepository'

const preparingError = 'We couldn’t prepare the diagnostic. Try again or continue with the local demo.'
const evidenceError = 'Evidence is required before this analysis can run.'
const maxResponseBytes = 1024 * 1024

export class EvidenceRequiredError extends Error {
  constructor() {
    super(evidenceError)
    this.name = 'EvidenceRequiredError'
  }
}

export class DiagnosticTransportError extends Error {
  constructor() {
    super(preparingError)
    this.name = 'DiagnosticTransportError'
  }
}

function sourceIdsForFinding(
  finding: CompletedDiagnosticTransportResponse['data']['findings'][number],
  response: CompletedDiagnosticTransportResponse,
) {
  const evidenceIds = new Set(finding.evidence_ids)
  return [...new Set(response.data.evidence
    .filter((evidence) => evidenceIds.has(evidence.evidence_id))
    .flatMap((evidence) => evidence.source_ids))]
}

export function mapTransportResponse(
  response: CompletedDiagnosticTransportResponse,
  requestedInput: DiagnosticInput,
): DiagnosticResult {
  if (response.demo) throw new DiagnosticTransportError()
  if (JSON.stringify(response.data.intake) !== JSON.stringify(requestedInput)) {
    throw new DiagnosticTransportError()
  }

  const sourceTitles = new Map(response.data.sources.map((source) => [source.source_id, source.title]))
  const summaryPoints = response.data.findings.slice(0, 3).map((finding) => finding.finding)
  const uncertainFindings = response.data.findings.filter((finding) => finding.requires_validation)
  const missingInformation = uncertainFindings.length > 0
    ? uncertainFindings.map((finding) => finding.finding)
    : ['Internal processes are not established by public evidence alone.']
  const questions = [...new Map(uncertainFindings
    .filter((finding) => finding.validation_question)
    .map((finding) => [finding.validation_question, finding])).values()]
    .map((finding, index) => ({
      key: `question-${index + 1}`,
      text: finding.validation_question!,
      reason: `This question validates: ${finding.finding}`,
    }))

  return DiagnosticResultSchema.parse({
    run_status: 'completed',
    diagnostic: {
      id: response.run_id,
      name: requestedInput.organization_name,
      isDemo: false,
      sources: response.data.sources.map((source) => ({
        id: source.source_id,
        title: source.title,
        sourceType: 'PUBLIC',
        isDemo: false,
        clientEvidenceEligible: true,
        url: source.url,
      })),
      items: response.data.findings.map((finding) => ({
        id: finding.finding_id,
        epistemicStatus: finding.finding_type === 'observed'
          ? 'PUBLIC_EVIDENCE'
          : finding.finding_type === 'inferred'
            ? 'INFERENCE'
            : finding.finding_type === 'hypothesis'
              ? 'HYPOTHESIS'
              : 'UNKNOWN',
        reviewStatus: 'NEEDS_REVIEW',
        title: finding.finding,
        summary: finding.finding,
        sourceIds: sourceIdsForFinding(finding, response),
        relatedItemIds: [],
      })),
    },
    final_package: {
      run_context: {
        input: requestedInput,
        prepared_at: response.completed_at,
      },
      organization_snapshot: {
        summary_points: summaryPoints,
        lenses: response.data.findings.slice(0, 3).map((finding) => {
          const sourceIds = sourceIdsForFinding(finding, response)
          return {
            title: finding.finding_type === 'observed' ? 'Observed public signal' : 'Finding for review',
            suggests: finding.finding,
            confirm: finding.validation_question ?? 'Review the cited public evidence before client use.',
            detail: sourceIds.map((sourceId) => sourceTitles.get(sourceId)).filter(Boolean).join('; ') || 'No source title is available for this finding.',
          }
        }),
      },
      public_evidence_map: response.data.sources,
      evidence_ledger: response.data.evidence,
      findings: response.data.findings.map((finding) => finding.finding),
      hypotheses: response.data.findings
        .filter((finding) => finding.finding_type === 'hypothesis')
        .map((finding) => finding.finding),
      diagnoses: [],
      recommendations: [{
        key: 'human-review',
        title: 'Diagnostic prepared for review.',
        description: 'Review the Operations/CX findings and validation questions before deciding on any next step.',
        rationale: 'The result is evidence-linked but does not include the wider transformation track.',
      }],
      kpis: [],
      client_validation_questions: questions,
      roadmap_90_day: [],
      missing_information: missingInformation,
      confidence_limitations: [
        'This result contains Operations/CX findings only.',
        'Recommendations, measures and a validation roadmap require the shared transformation track and human review.',
      ],
    },
  })
}

interface N8nDiagnosticRepositoryOptions {
  timeoutMs?: number
  fetchImpl?: typeof fetch
}

export class N8nDiagnosticRepository implements DiagnosticRepository {
  readonly deliveryMode = 'live' as const
  private readonly webhookUrl: string
  private readonly timeoutMs: number
  private readonly fetchImpl: typeof fetch

  constructor(webhookUrl: string, options: N8nDiagnosticRepositoryOptions = {}) {
    this.webhookUrl = z.url().refine((value) => ['http:', 'https:'].includes(new URL(value).protocol)).parse(webhookUrl)
    this.timeoutMs = options.timeoutMs ?? 15_000
    this.fetchImpl = options.fetchImpl ?? globalThis.fetch
  }

  async prepareDiagnostic(input: DiagnosticInput): Promise<DiagnosticResult> {
    const validatedInput = DiagnosticInputSchema.parse(input)
    const correlationId = `CORR-${crypto.randomUUID()}`
    const request = DiagnosticTransportRequestSchema.parse({
      contract_version: '1.0',
      mode: 'live',
      correlation_id: correlationId,
      intake: validatedInput,
    })
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), this.timeoutMs)

    try {
      const rawResponse = await this.fetchImpl(this.webhookUrl, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-Correlation-ID': correlationId,
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      })
      const responseText = await rawResponse.text()
      if (new TextEncoder().encode(responseText).length > maxResponseBytes) throw new DiagnosticTransportError()
      let responseJson: unknown
      try {
        responseJson = JSON.parse(responseText)
      } catch {
        throw new DiagnosticTransportError()
      }
      const response = DiagnosticTransportResponseSchema.parse(responseJson)
      if (rawResponse.status === 422 && response.status === 'needs_evidence') throw new EvidenceRequiredError()
      if (!rawResponse.ok || response.status !== 'completed' || rawResponse.status !== 200) throw new DiagnosticTransportError()
      return mapTransportResponse(response, validatedInput)
    } catch (error: unknown) {
      if (error instanceof EvidenceRequiredError || error instanceof DiagnosticTransportError) throw error
      throw new DiagnosticTransportError()
    } finally {
      window.clearTimeout(timeout)
    }
  }
}

export const diagnosticMessages = {
  preparing: 'Preparing diagnostic…',
  evidenceRequired: evidenceError,
  prepared: 'Diagnostic prepared for review.',
  failed: preparingError,
} as const
