import { z } from 'zod'
import { isoCountryCodes } from '../data/countries'
import { DiagnosticSchema } from './diagnostic'

const DateOnlySchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/)

export const DiagnosticRunStatusSchema = z.enum([
  'created',
  'researching',
  'analyzing',
  'qa',
  'completed',
  'failed',
])

export const DiagnosticInputSchema = z.object({
  organization_name: z.string().trim().min(1),
  website: z.url().refine((value) => {
    const protocol = new URL(value).protocol
    return protocol === 'http:' || protocol === 'https:'
  }),
  country: z.string().refine(
    (code) => (isoCountryCodes as readonly string[]).includes(code),
    'Use an ISO 3166-1 alpha-2 country code',
  ),
  current_challenge: z.string().trim().min(1).max(600),
  research_window: z.object({
    start_date: DateOnlySchema,
    end_date: DateOnlySchema,
  }),
  uploaded_document_refs: z.array(z.string()),
})

const LensSchema = z.object({
  title: z.string().min(1),
  suggests: z.string().min(1),
  confirm: z.string().min(1),
  detail: z.string().min(1),
})

const QuestionSchema = z.object({
  key: z.string().min(1),
  text: z.string().min(1),
  reason: z.string().min(1),
})

const RecommendationSchema = z.object({
  key: z.string().min(1),
  title: z.string().min(1),
  description: z.string().min(1),
  rationale: z.string().min(1),
})

const KpiSchema = z.object({
  key: z.string().min(1),
  title: z.string().min(1),
  baseline: z.string().min(1),
})

const RoadmapPhaseSchema = z.object({
  title: z.string().min(1),
  period: z.string().min(1),
  objective: z.string().min(1),
  activities: z.array(z.string().min(1)).max(3),
})

export const FinalPackageSchema = z.object({
  run_context: z.object({
    input: DiagnosticInputSchema,
    prepared_at: z.string().min(1),
  }),
  organization_snapshot: z.object({
    summary_points: z.array(z.string().min(1)).max(3),
    lenses: z.array(LensSchema),
  }),
  public_evidence_map: z.array(z.record(z.string(), z.unknown())),
  evidence_ledger: z.array(z.record(z.string(), z.unknown())),
  findings: z.array(z.string()),
  hypotheses: z.array(z.string()),
  diagnoses: z.array(z.string()),
  recommendations: z.array(RecommendationSchema),
  kpis: z.array(KpiSchema),
  client_validation_questions: z.array(QuestionSchema),
  roadmap_90_day: z.array(RoadmapPhaseSchema),
  missing_information: z.array(z.string()),
  confidence_limitations: z.array(z.string()),
})

export const DiagnosticResultSchema = z.object({
  run_status: DiagnosticRunStatusSchema,
  diagnostic: DiagnosticSchema,
  final_package: FinalPackageSchema,
})
