import { z } from 'zod'

const StableIdSchema = z
  .string()
  .regex(/^[A-Z]+(?:-[A-Z0-9]+)+$/, 'Use a stable prefixed ID such as ITEM-001')

export const EpistemicStatusSchema = z.enum([
  'PUBLIC_EVIDENCE',
  'INFERENCE',
  'HYPOTHESIS',
  'UNKNOWN',
  'RECOMMENDATION',
])

export const ReviewStatusSchema = z.enum([
  'NOT_REVIEWED',
  'NEEDS_REVIEW',
  'APPROVED',
  'REJECTED',
])

export const EvidenceSourceSchema = z
  .object({
    id: StableIdSchema,
    title: z.string().min(1),
    sourceType: z.enum(['PUBLIC', 'INTERNAL']),
    isDemo: z.boolean(),
    clientEvidenceEligible: z.boolean(),
    url: z.url().optional(),
    note: z.string().min(1).optional(),
  })
  .superRefine((source, context) => {
    if (source.isDemo && source.clientEvidenceEligible) {
      context.addIssue({
        code: 'custom',
        path: ['clientEvidenceEligible'],
        message: 'Demo sources cannot be exported as client evidence',
      })
    }
  })

export const AnalyticalItemSchema = z.object({
  id: StableIdSchema,
  epistemicStatus: EpistemicStatusSchema,
  reviewStatus: ReviewStatusSchema,
  title: z.string().min(1),
  summary: z.string().min(1),
  sourceIds: z.array(StableIdSchema),
  relatedItemIds: z.array(StableIdSchema),
})

export const DiagnosticSchema = z
  .object({
    id: StableIdSchema,
    name: z.string().min(1),
    isDemo: z.boolean(),
    sources: z.array(EvidenceSourceSchema),
    items: z.array(AnalyticalItemSchema),
  })
  .superRefine((diagnostic, context) => {
    const sourceIds = new Set(diagnostic.sources.map(({ id }) => id))
    const itemIds = new Set(diagnostic.items.map(({ id }) => id))

    if (sourceIds.size !== diagnostic.sources.length) {
      context.addIssue({
        code: 'custom',
        path: ['sources'],
        message: 'Source IDs must be unique',
      })
    }

    if (itemIds.size !== diagnostic.items.length) {
      context.addIssue({
        code: 'custom',
        path: ['items'],
        message: 'Analytical item IDs must be unique',
      })
    }

    diagnostic.items.forEach((item, itemIndex) => {
      if (item.epistemicStatus === 'PUBLIC_EVIDENCE' && item.sourceIds.length === 0) {
        context.addIssue({
          code: 'custom',
          path: ['items', itemIndex, 'sourceIds'],
          message: 'Public evidence must reference at least one source',
        })
      }

      if (
        item.epistemicStatus === 'PUBLIC_EVIDENCE' &&
        item.sourceIds.some((sourceId) => {
          const source = diagnostic.sources.find(({ id }) => id === sourceId)
          return source?.isDemo || !source?.clientEvidenceEligible
        })
      ) {
        context.addIssue({
          code: 'custom',
          path: ['items', itemIndex, 'sourceIds'],
          message: 'Public evidence must reference client-eligible, non-demo sources',
        })
      }

      item.sourceIds.forEach((sourceId, sourceIndex) => {
        if (!sourceIds.has(sourceId)) {
          context.addIssue({
            code: 'custom',
            path: ['items', itemIndex, 'sourceIds', sourceIndex],
            message: `Unknown source reference: ${sourceId}`,
          })
        }
      })

      item.relatedItemIds.forEach((relatedItemId, relatedIndex) => {
        if (!itemIds.has(relatedItemId)) {
          context.addIssue({
            code: 'custom',
            path: ['items', itemIndex, 'relatedItemIds', relatedIndex],
            message: `Unknown analytical item reference: ${relatedItemId}`,
          })
        }

        if (relatedItemId === item.id) {
          context.addIssue({
            code: 'custom',
            path: ['items', itemIndex, 'relatedItemIds', relatedIndex],
            message: 'An analytical item cannot reference itself',
          })
        }
      })
    })
  })
