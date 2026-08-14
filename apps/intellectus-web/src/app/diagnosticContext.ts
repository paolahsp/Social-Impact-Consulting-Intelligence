import { createContext, useContext } from 'react'
import type { DiagnosticInput, DiagnosticResult, DiagnosticRunStatus } from '../types/diagnostic'

export type IntakeData = DiagnosticInput

export interface DiagnosticContextValue {
  result: DiagnosticResult | null
  runStatus: DiagnosticRunStatus
  runStatusMessage: string
  runError: string
  intake: IntakeData
  reviewed: boolean
  nextStepAdded: boolean
  selectedQuestionIds: string[]
  consultantNotes: string
  includeConsultantNotes: boolean
  briefExists: boolean
  customQuestions: Array<{ id: string; text: string }>
  supportingDocuments: File[]
  saveIntake: (intake: IntakeData) => void
  resetDiagnostic: () => void
  prepareDiagnostic: (intake: IntakeData, documents: File[]) => Promise<boolean>
  finalizeBrief: () => void
  reopenBrief: () => void
  addNextStepToBrief: () => void
  toggleQuestion: (id: string) => void
  saveConsultantNotes: (note: string) => void
  setIncludeConsultantNotes: (include: boolean) => void
  addCustomQuestion: (question: string) => void
  removeCustomQuestion: (id: string) => void
}

export const DiagnosticContext = createContext<DiagnosticContextValue | null>(null)

export function useDiagnostic() {
  const context = useContext(DiagnosticContext)
  if (!context) throw new Error('useDiagnostic must be used within DiagnosticProvider')
  return context
}
