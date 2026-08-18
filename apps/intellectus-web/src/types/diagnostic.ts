import type { z } from 'zod'
import type {
  AnalyticalItemSchema,
  DiagnosticSchema,
  EpistemicStatusSchema,
  EvidenceSourceSchema,
  ReviewStatusSchema,
} from '../schemas/diagnostic'
import type {
  DiagnosticInputSchema,
  DiagnosticResultSchema,
  DiagnosticRunStatusSchema,
  FinalPackageSchema,
} from '../schemas/diagnosticRun'

export type EpistemicStatus = z.infer<typeof EpistemicStatusSchema>
export type ReviewStatus = z.infer<typeof ReviewStatusSchema>
export type EvidenceSource = z.infer<typeof EvidenceSourceSchema>
export type AnalyticalItem = z.infer<typeof AnalyticalItemSchema>
export type Diagnostic = z.infer<typeof DiagnosticSchema>
export type DiagnosticRunStatus = z.infer<typeof DiagnosticRunStatusSchema>
export type DiagnosticInput = z.infer<typeof DiagnosticInputSchema>
export type FinalPackage = z.infer<typeof FinalPackageSchema>
export type DiagnosticResult = z.infer<typeof DiagnosticResultSchema>
