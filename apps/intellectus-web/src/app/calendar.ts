export const GOOGLE_CALENDAR_CREATE_URL = 'https://calendar.google.com/calendar/render'

interface CalendarDetails {
  organization: string
  date: string
  startTime: string
  durationMinutes: number
  attendeeEmails: string
  objective: string
  agenda: string[]
  consultantNotes: string
  nextStep: string
  contextPeriod: string
}

function calendarDate(value: Date) {
  return value.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

export function createGoogleCalendarUrl(details: CalendarDetails) {
  const start = new Date(`${details.date}T${details.startTime}:00`)
  const end = new Date(start.getTime() + details.durationMinutes * 60_000)
  const description = [
    `Objective: ${details.objective}`,
    `Workshop agenda:\n${details.agenda.map((question) => `• ${question}`).join('\n')}`,
    details.consultantNotes ? `Consultant notes: ${details.consultantNotes}` : '',
    `Suggested next step: ${details.nextStep}`,
    `Recent context period: ${details.contextPeriod}`,
  ].filter(Boolean).join('\n\n')
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: `Intellectus diagnostic workshop — ${details.organization}`,
    dates: `${calendarDate(start)}/${calendarDate(end)}`,
    details: description,
  })
  const attendees = details.attendeeEmails.split(/[;,\s]+/).map((email) => email.trim()).filter(Boolean)
  attendees.forEach((email) => params.append('add', email))
  return `${GOOGLE_CALENDAR_CREATE_URL}?${params.toString()}`
}
