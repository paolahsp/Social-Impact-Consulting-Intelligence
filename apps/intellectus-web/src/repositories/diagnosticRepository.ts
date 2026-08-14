import { createDemoDiagnostic } from '../fixtures/demoDiagnostic'
import { orderedLenses, scenarioContent, type DiagnosticScenario } from '../fixtures/scenarioContent'
import {
  DiagnosticInputSchema,
  DiagnosticResultSchema,
} from '../schemas/diagnosticRun'
import type {
  DiagnosticInput,
  DiagnosticResult,
  DiagnosticRunStatus,
} from '../types/diagnostic'

export const runStatusLabels: Record<DiagnosticRunStatus, string> = {
  created: 'Preparing your diagnostic',
  researching: 'Reviewing public sources',
  analyzing: 'Organizing the evidence',
  qa: 'Preparing your brief',
  completed: 'Ready for review',
  failed: 'We couldn’t complete the diagnostic',
}

export interface DiagnosticRepository {
  prepareDiagnostic(input: DiagnosticInput): Promise<DiagnosticResult>
}

const scenarioKeywords: Record<Exclude<DiagnosticScenario, 'neutral'>, Set<string>> = {
  funding: new Set(['funding', 'fund', 'fundraising', 'revenue', 'income', 'donor', 'grant', 'financial', 'sustainability']),
  impact: new Set(['impact', 'outcome', 'evidence', 'evaluation', 'measurement', 'learning', 'effectiveness']),
  operations: new Set(['operation', 'process', 'workflow', 'service', 'issue', 'resolution', 'handoff', 'ownership', 'stakeholder', 'recipient', 'experience']),
}

function normalizedWords(value: string) {
  return value.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, ' ').trim().split(/\s+/).filter(Boolean)
}

export function classifyChallenge(value: string): DiagnosticScenario {
  const scores = { funding: 0, impact: 0, operations: 0 }
  for (const word of normalizedWords(value)) {
    const variants = word.endsWith('s') ? [word, word.slice(0, -1)] : [word]
    for (const scenario of Object.keys(scores) as Array<keyof typeof scores>) {
      if (variants.some((variant) => scenarioKeywords[scenario].has(variant))) scores[scenario] += 1
    }
  }
  const highest = Math.max(...Object.values(scores))
  if (highest === 0) return 'neutral'
  const matches = (Object.keys(scores) as Array<keyof typeof scores>).filter((scenario) => scores[scenario] === highest)
  return matches.length === 1 ? matches[0] : 'neutral'
}

export class FixtureDiagnosticRepository implements DiagnosticRepository {
  async prepareDiagnostic(input: DiagnosticInput): Promise<DiagnosticResult> {
    const validatedInput = DiagnosticInputSchema.parse(input)
    const scenario = classifyChallenge(validatedInput.current_challenge)
    const content = scenarioContent[scenario]
    const diagnostic = createDemoDiagnostic(validatedInput.organization_name, scenario)

    return DiagnosticResultSchema.parse({
      run_status: 'completed',
      diagnostic,
      final_package: {
        run_context: {
          input: validatedInput,
          prepared_at: new Date().toISOString(),
        },
        organization_snapshot: {
          summary_points: content.summary,
          lenses: orderedLenses(scenario),
        },
        public_evidence_map: [],
        evidence_ledger: [],
        findings: content.findings,
        hypotheses: content.hypotheses,
        diagnoses: [],
        recommendations: [content.recommendation],
        kpis: content.kpis,
        client_validation_questions: content.questions,
        roadmap_90_day: content.roadmap,
        missing_information: content.missing,
        confidence_limitations: [
          'The local demo does not contain reviewed public sources for this organization.',
          'Internal processes and KPI baselines require client validation.',
        ],
      },
    })
  }
}
