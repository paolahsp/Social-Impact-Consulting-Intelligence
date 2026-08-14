import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { runStatusLabels, type DiagnosticRepository } from '../repositories/diagnosticRepository'
import type { DiagnosticResult, DiagnosticRunStatus } from '../types/diagnostic'
import { DiagnosticContext, type DiagnosticContextValue } from './diagnosticContext'
import { createInitialIntake } from './initialIntake'

export function DiagnosticProvider({ children, repository }: { children: ReactNode; repository: DiagnosticRepository }) {
  const [result, setResult] = useState<DiagnosticResult | null>(null)
  const [runStatus, setRunStatus] = useState<DiagnosticRunStatus>('created')
  const [runError, setRunError] = useState('')
  const [intake, setIntake] = useState(createInitialIntake)
  const [reviewed, setReviewed] = useState(false)
  const [nextStepAdded, setNextStepAdded] = useState(false)
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([])
  const [consultantNotes, setConsultantNotes] = useState('')
  const [includeConsultantNotes, setIncludeConsultantNotes] = useState(false)
  const [briefExists, setBriefExists] = useState(false)
  const [customQuestions, setCustomQuestions] = useState<Array<{ id: string; text: string }>>([])
  const [supportingDocuments, setSupportingDocuments] = useState<File[]>([])

  const resetDiagnostic = useCallback(() => {
    setResult(null)
    setRunStatus('created')
    setRunError('')
    setIntake(createInitialIntake())
    setReviewed(false)
    setNextStepAdded(false)
    setSelectedQuestionIds([])
    setConsultantNotes('')
    setIncludeConsultantNotes(false)
    setBriefExists(false)
    setCustomQuestions([])
    setSupportingDocuments([])
  }, [])

  const value = useMemo<DiagnosticContextValue>(() => ({
    result,
    runStatus,
    runStatusMessage: runStatusLabels[runStatus],
    runError,
    intake,
    reviewed,
    nextStepAdded,
    selectedQuestionIds,
    consultantNotes,
    includeConsultantNotes,
    briefExists,
    customQuestions,
    supportingDocuments,
    saveIntake: setIntake,
    resetDiagnostic,
    prepareDiagnostic: async (nextIntake, documents) => {
      setIntake(nextIntake)
      setResult(null)
      setRunStatus('created')
      setRunError('')
      setReviewed(false)
      setNextStepAdded(false)
      setSelectedQuestionIds([])
      setConsultantNotes('')
      setIncludeConsultantNotes(false)
      setBriefExists(false)
      setCustomQuestions([])
      setSupportingDocuments(documents)

      try {
        const nextResult = await repository.prepareDiagnostic(nextIntake)
        setResult(nextResult)
        setRunStatus(nextResult.run_status)
        return nextResult.run_status === 'completed'
      } catch (error: unknown) {
        setRunStatus('failed')
        setRunError(error instanceof Error ? error.message : runStatusLabels.failed)
        return false
      }
    },
    finalizeBrief: () => setReviewed(true),
    reopenBrief: () => setReviewed(false),
    addNextStepToBrief: () => {
      setNextStepAdded(true)
      setBriefExists(true)
    },
    toggleQuestion: (id) => setSelectedQuestionIds((ids) => ids.includes(id) ? ids.filter((itemId) => itemId !== id) : [...ids, id]),
    saveConsultantNotes: setConsultantNotes,
    setIncludeConsultantNotes,
    addCustomQuestion: (question) => {
      const id = `custom-${crypto.randomUUID()}`
      setCustomQuestions((current) => [...current, { id, text: question }])
      setSelectedQuestionIds((current) => [...current, id])
    },
    removeCustomQuestion: (id) => {
      setCustomQuestions((current) => current.filter((question) => question.id !== id))
      setSelectedQuestionIds((current) => current.filter((questionId) => questionId !== id))
    },
  }), [briefExists, consultantNotes, customQuestions, includeConsultantNotes, intake, nextStepAdded, repository, resetDiagnostic, result, reviewed, runError, runStatus, selectedQuestionIds, supportingDocuments])

  return <DiagnosticContext.Provider value={value}>{children}</DiagnosticContext.Provider>
}
