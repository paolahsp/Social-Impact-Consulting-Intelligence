import { describe, expect, it } from 'vitest'
import { DiagnosticInputSchema, DiagnosticResultSchema } from '../schemas/diagnosticRun'
import { FixtureDiagnosticRepository, classifyChallenge, runStatusLabels } from './diagnosticRepository'

const input = {
  organization_name: 'Example organization', website: 'https://example.test', country: 'US',
  current_challenge: 'Prepare a focused first conversation.',
  research_window: { start_date: '2026-01-01', end_date: '2026-03-01' }, uploaded_document_refs: [],
}

describe('local diagnostic scenarios', () => {
  it.each([
    ['Improve fundings sustainability', 'funding'],
    ['Review impact measurement and learning', 'impact'],
    ['Clarify the operations workflow and ownership', 'operations'],
    ['Explore our priorities for next year', 'neutral'],
    ['Funding and impact', 'neutral'],
  ])('classifies %s as %s', (challenge, expected) => expect(classifyChallenge(challenge)).toBe(expected))

  it.each([
    ['funding', 'Funding resilience', 'Committed funding coverage'],
    ['impact measurement', 'Impact and evidence', 'Priority outcome evidence coverage'],
    ['operations process', 'Operations and stakeholder experience', 'Issue-resolution cycle time'],
    ['a broad challenge', 'Funding resilience', 'Decision scope agreed'],
  ])('keeps questions, recommendations and KPIs coherent for %s', async (challenge, firstLens, firstKpi) => {
    const result = await new FixtureDiagnosticRepository().prepareDiagnostic({ ...input, current_challenge: challenge })
    expect(result.final_package.organization_snapshot.lenses[0].title).toBe(firstLens)
    expect(result.final_package.client_validation_questions).toHaveLength(5)
    expect(result.final_package.recommendations[0].title).toBeTruthy()
    expect(result.final_package.kpis[0].title).toBe(firstKpi)
    expect(result.diagnostic.items.find((item) => item.epistemicStatus === 'RECOMMENDATION')?.title).toBe(result.final_package.recommendations[0].title)
  })
})

describe('FixtureDiagnosticRepository contract', () => {
  it('returns a schema-validated package with the ISO country code and no organization contamination', async () => {
    const result = await new FixtureDiagnosticRepository().prepareDiagnostic(input)
    expect(DiagnosticResultSchema.parse(result)).toEqual(result)
    expect(result.final_package.run_context.input.country).toBe('US')
    expect(result.diagnostic.name).toBe('Example organization')
    expect(JSON.stringify(result)).not.toContain('GiveDirectly')
  })

  it('rejects an invalid ISO country code with Zod', () => {
    expect(() => DiagnosticInputSchema.parse({ ...input, country: 'USA' })).toThrow()
  })

  it('defines plain-language copy for every frozen run state', () => {
    expect(runStatusLabels).toEqual({ created: 'Preparing your diagnostic', researching: 'Reviewing public sources', analyzing: 'Organizing the evidence', qa: 'Preparing your brief', completed: 'Ready for review', failed: 'We couldn’t complete the diagnostic' })
  })
})
