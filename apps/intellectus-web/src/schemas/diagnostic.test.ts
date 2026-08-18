import { describe, expect, it } from 'vitest'
import { demoDiagnostic } from '../fixtures/demoDiagnostic'
import { DiagnosticSchema } from './diagnostic'

describe('DiagnosticSchema', () => {
  it('accepts the valid demo fixture', () => {
    expect(DiagnosticSchema.parse(demoDiagnostic)).toEqual(demoDiagnostic)
  })

  it('rejects an invalid fixture', () => {
    expect(() =>
      DiagnosticSchema.parse({ ...demoDiagnostic, name: '' }),
    ).toThrow()
  })

  it('rejects a missing relational reference', () => {
    const invalidDiagnostic = {
      ...demoDiagnostic,
      items: demoDiagnostic.items.map((item, index) =>
        index === 0 ? { ...item, relatedItemIds: ['MISSING-999'] } : item,
      ),
    }

    expect(() => DiagnosticSchema.parse(invalidDiagnostic)).toThrow(
      'Unknown analytical item reference: MISSING-999',
    )
  })

  it('does not allow demo material to be classified as public evidence', () => {
    const invalidDiagnostic = {
      ...demoDiagnostic,
      items: demoDiagnostic.items.map((item, index) =>
        index === 0
          ? { ...item, epistemicStatus: 'PUBLIC_EVIDENCE', sourceIds: ['SRC-001'] }
          : item,
      ),
    }

    expect(() => DiagnosticSchema.parse(invalidDiagnostic)).toThrow(
      'Public evidence must reference client-eligible, non-demo sources',
    )
  })

  it('keeps every fixture relationship resolvable', () => {
    const itemIds = new Set(demoDiagnostic.items.map(({ id }) => id))
    expect(
      demoDiagnostic.items.every(({ relatedItemIds }) =>
        relatedItemIds.every((id) => itemIds.has(id)),
      ),
    ).toBe(true)
  })
})
