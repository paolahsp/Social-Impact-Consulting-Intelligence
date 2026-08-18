import type { IntakeData } from './diagnosticContext'

function formatLocalDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function createInitialIntake(today = new Date()): IntakeData {
  const localToday = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const startDate = new Date(localToday)
  startDate.setDate(startDate.getDate() - 89)

  return {
    organization_name: '',
    website: '',
    country: '',
    current_challenge: '',
    research_window: {
      start_date: formatLocalDate(startDate),
      end_date: formatLocalDate(localToday),
    },
    uploaded_document_refs: [],
  }
}
