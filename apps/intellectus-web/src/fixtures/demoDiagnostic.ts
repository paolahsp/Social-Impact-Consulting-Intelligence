import { DiagnosticSchema } from '../schemas/diagnostic'
import { scenarioContent, type DiagnosticScenario } from './scenarioContent'

export function createDemoDiagnostic(organizationName: string, scenario: DiagnosticScenario = 'neutral') {
  const content = scenarioContent[scenario]
  return DiagnosticSchema.parse({
    id: 'DIAG-001',
    name: organizationName,
    isDemo: true,
    sources: [
      {
        id: 'SRC-001',
        title: 'Demo source — not client evidence',
        sourceType: 'PUBLIC',
        isDemo: true,
        clientEvidenceEligible: false,
        note: 'Local methodological fixture. It must never be exported as client evidence.',
      },
    ],
    items: [
      {
        id: 'UNK-001',
        epistemicStatus: 'UNKNOWN',
        reviewStatus: 'NEEDS_REVIEW',
        title: content.missing[0],
        summary: `The local sample cannot establish: ${content.missing[0]}`,
        sourceIds: [],
        relatedItemIds: [],
      },
      {
        id: 'HYP-001',
        epistemicStatus: 'HYPOTHESIS',
        reviewStatus: 'NEEDS_REVIEW',
        title: content.hypotheses[0],
        summary: content.hypotheses[0],
        sourceIds: [],
        relatedItemIds: ['UNK-001'],
      },
      {
        id: 'HYP-002',
        epistemicStatus: 'HYPOTHESIS',
        reviewStatus: 'NEEDS_REVIEW',
        title: content.hypotheses[1],
        summary: content.hypotheses[1],
        sourceIds: [],
        relatedItemIds: ['UNK-001'],
      },
      {
        id: 'HYP-003',
        epistemicStatus: 'HYPOTHESIS',
        reviewStatus: 'NEEDS_REVIEW',
        title: content.hypotheses[2],
        summary: content.hypotheses[2],
        sourceIds: [],
        relatedItemIds: ['UNK-001'],
      },
      {
        id: 'REC-001',
        epistemicStatus: 'RECOMMENDATION',
        reviewStatus: 'NEEDS_REVIEW',
        title: content.recommendation.title,
        summary: content.recommendation.description,
        sourceIds: [],
        relatedItemIds: ['UNK-001', 'HYP-001', 'HYP-002', 'HYP-003'],
      },
    ],
  })
}

export const demoDiagnostic = createDemoDiagnostic('Sample organization')
