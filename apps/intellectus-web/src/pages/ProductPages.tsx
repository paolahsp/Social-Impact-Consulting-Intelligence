import { useRef, useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react'
import { FileText } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { createGoogleCalendarUrl } from '../app/calendar'
import { useDiagnostic } from '../app/diagnosticContext'
import { countries, getCountryName } from '../data/countries'

const fieldClass = 'mt-2 min-h-11 w-full min-w-0 rounded-control border border-border bg-surface px-3.5 py-3 text-ink placeholder:text-muted/70 focus:border-accent'
const maxDocumentSize = 10 * 1024 * 1024
const allowedDocumentTypes = new Set(['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'])
const allowedDocumentExtensions = new Set(['pdf', 'docx', 'txt'])

interface FormErrors {
  organization_name?: string
  website?: string
  country?: string
  current_challenge?: string
  research_window?: string
}

function PageFrame({ children, document = false }: { children: ReactNode; document?: boolean }) {
  return <div className={`mx-auto w-full px-page py-9 sm:py-12 ${document ? 'max-w-document' : 'max-w-reading'}`}>{children}</div>
}

function PageIntro({ eyebrow, title, children }: { eyebrow?: string; title: string; children: ReactNode }) {
  return <header className="max-w-[44rem]">{eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">{eyebrow}</p>}<h1 className="page-title mt-3 font-serif font-semibold leading-[1.08] text-ink">{title}</h1><p className="mt-4 text-lg leading-8 text-muted">{children}</p></header>
}

function FieldError({ id, children }: { id: string; children?: string }) {
  return children ? <p className="mt-2 text-sm font-medium text-danger" id={id}>{children}</p> : null
}

function StepActions({ back, children }: { back?: string; children: ReactNode }) {
  return <nav aria-label="Step actions" className="mt-10 flex flex-col-reverse gap-3 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">{back ? <Link className="inline-flex min-h-11 items-center justify-center rounded-control px-4 font-semibold text-accent hover:bg-blush" to={back}>Back</Link> : <span />}{children}</nav>
}

function dateOrdinal(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  return match ? Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])) / 86_400_000 : null
}

function selectedDayCount(startDate: string, endDate: string) {
  const start = dateOrdinal(startDate)
  const end = dateOrdinal(endDate)
  return start === null || end === null ? 0 : Math.max(0, end - start + 1)
}

function formatLocalDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function formatDateOnly(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return value
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])))
}

function documentExtension(file: File) {
  return file.name.split('.').pop()?.toLowerCase() ?? ''
}

function documentType(file: File) {
  const extension = documentExtension(file)
  return extension ? extension.toUpperCase() : 'Document'
}

function readableSize(size: number) {
  return size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} KB` : `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function isAllowedDocument(file: File) {
  return file.type ? allowedDocumentTypes.has(file.type) : allowedDocumentExtensions.has(documentExtension(file))
}

export function NewDiagnosticPage() {
  const { intake, prepareDiagnostic, runStatus, runStatusMessage, supportingDocuments } = useDiagnostic()
  const [form, setForm] = useState(intake)
  const [documents, setDocuments] = useState<File[]>(supportingDocuments)
  const [documentError, setDocumentError] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [preparing, setPreparing] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const fileInput = useRef<HTMLInputElement>(null)
  const today = formatLocalDate(new Date())
  const duration = selectedDayCount(form.research_window.start_date, form.research_window.end_date)
  const setupRequired = Boolean((location.state as { setupRequired?: boolean } | null)?.setupRequired)

  const update = (field: 'organization_name' | 'website' | 'country' | 'current_challenge', value: string) => {
    setForm((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const updateDate = (field: 'start_date' | 'end_date', value: string) => {
    setForm((current) => ({ ...current, research_window: { ...current.research_window, [field]: value } }))
    setErrors((current) => ({ ...current, research_window: undefined }))
  }

  const selectDocuments = (event: ChangeEvent<HTMLInputElement>) => {
    const incoming = Array.from(event.target.files ?? [])
    const next = [...documents]
    let nextError = ''
    for (const file of incoming) {
      if (!isAllowedDocument(file)) nextError = 'Choose PDF, DOCX or TXT documents only.'
      else if (file.size > maxDocumentSize) nextError = 'Each document must be 10 MiB or smaller.'
      else if (next.some((current) => current.name === file.name && current.size === file.size)) nextError = 'That document is already selected.'
      else if (next.length >= 5) nextError = 'Choose no more than five documents.'
      else next.push(file)
    }
    setDocuments(next)
    setDocumentError(nextError)
    if (fileInput.current) fileInput.current.value = ''
  }

  const focusFirstInvalid = (nextErrors: FormErrors) => {
    const id = nextErrors.organization_name ? 'organization-name' : nextErrors.website ? 'official-website' : nextErrors.country ? 'primary-country' : nextErrors.research_window ? 'start-date' : 'conversation-focus'
    const field = document.getElementById(id)
    field?.focus()
    field?.scrollIntoView?.({ block: 'center', behavior: 'smooth' })
  }

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextErrors: FormErrors = {}
    const { start_date: startDate, end_date: endDate } = form.research_window
    if (!form.organization_name.trim()) nextErrors.organization_name = 'Enter the organization name before continuing.'
    if (!form.website.trim()) nextErrors.website = 'Enter the official website before continuing.'
    else {
      try {
        const website = new URL(form.website)
        if (!['http:', 'https:'].includes(website.protocol)) throw new Error()
      } catch { nextErrors.website = 'Enter a complete web address.' }
    }
    if (!form.country) nextErrors.country = 'Select the primary country of operation.'
    if (!startDate || !endDate) nextErrors.research_window = 'Select both a start date and an end date.'
    else {
      const start = dateOrdinal(startDate)
      const end = dateOrdinal(endDate)
      const todayOrdinal = dateOrdinal(today)
      if (end !== null && todayOrdinal !== null && end > todayOrdinal) nextErrors.research_window = 'End date cannot be later than today.'
      else if (start !== null && end !== null && start > end) nextErrors.research_window = 'Start date must be on or before the end date.'
      else if (selectedDayCount(startDate, endDate) > 90) nextErrors.research_window = 'Select a recent context period of 90 days or fewer.'
    }
    if (!form.current_challenge.trim()) nextErrors.current_challenge = 'Describe what you want to understand before continuing.'
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) {
      focusFirstInvalid(nextErrors)
      return
    }
    setPreparing(true)
    const prepared = await prepareDiagnostic({ ...form, organization_name: form.organization_name.trim(), website: form.website.trim(), current_challenge: form.current_challenge.trim(), uploaded_document_refs: [] }, documents)
    if (prepared) navigate('/overview')
    else setPreparing(false)
  }

  const dateDescription = `research-window-help research-window-duration${errors.research_window ? ' research-window-error' : ''}`
  return <PageFrame>
    <PageIntro eyebrow="Pre-engagement diagnostic" title="Prepare your next client conversation">Define the organization, recent context and decision you need to prepare for the first conversation.</PageIntro>
    {setupRequired && <p className="mt-6 rounded-panel border border-border bg-blush px-4 py-3" role="status">Complete the setup to prepare your diagnostic.</p>}
    <form className="mt-9 space-y-7" noValidate onSubmit={submit}>
      <div><label className="font-semibold" htmlFor="organization-name">Organization name</label><p className="mt-1 text-sm leading-6 text-muted" id="organization-name-help">Enter the organization you are preparing to meet.</p><input aria-describedby={`organization-name-help${errors.organization_name ? ' organization-name-error' : ''}`} aria-invalid={Boolean(errors.organization_name)} className={fieldClass} id="organization-name" onChange={(event) => update('organization_name', event.target.value)} required value={form.organization_name} /><FieldError id="organization-name-error">{errors.organization_name}</FieldError></div>
      <div><label className="font-semibold" htmlFor="official-website">Official website</label><p className="mt-1 text-sm leading-6 text-muted" id="official-website-help">Used to identify relevant public information.</p><input aria-describedby={`official-website-help${errors.website ? ' official-website-error' : ''}`} aria-invalid={Boolean(errors.website)} className={fieldClass} id="official-website" inputMode="url" onChange={(event) => update('website', event.target.value)} required type="url" value={form.website} /><FieldError id="official-website-error">{errors.website}</FieldError></div>
      <div><label className="font-semibold" htmlFor="supporting-documents">Supporting documents (optional)</label><p className="mt-1 text-sm leading-6 text-muted" id="supporting-documents-help">Add reports, evaluations or background documents that may help prepare the diagnostic.</p><input accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" aria-describedby={`supporting-documents-help supporting-documents-format${documents.length > 0 ? ' supporting-documents-session' : ''}${documentError ? ' supporting-documents-error' : ''}`} className="sr-only" id="supporting-documents" multiple onChange={selectDocuments} ref={fileInput} tabIndex={-1} type="file" /><div className="mt-3 flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:gap-4"><button aria-controls="supporting-documents" className="inline-flex min-h-11 items-center justify-center rounded-control border border-border bg-surface px-4 font-semibold text-ink hover:bg-blush" onClick={() => fileInput.current?.click()} type="button">Add documents</button><p className="text-sm text-muted" id="supporting-documents-format">PDF, DOCX or TXT · Up to 5 files · 10 MB each</p></div>{documents.length === 0 ? <p className="mt-3 text-sm text-muted">No documents selected</p> : <><p className="mt-3 text-sm text-muted" id="supporting-documents-session">Selected for this session. Documents will be analysed when the research workflow is connected.</p><ul aria-label="Selected supporting documents" className="mt-3 divide-y divide-border border-y border-border">{documents.map((file) => <li className="flex flex-wrap items-center justify-between gap-3 py-3" key={`${file.name}-${file.size}`}><span className="flex min-w-0 items-center gap-3"><FileText aria-hidden="true" className="h-5 w-5 shrink-0 text-muted" strokeWidth={1.75} /><span className="min-w-0"><strong className="block break-words">{file.name}</strong><span className="text-sm text-muted">{documentType(file)} · {readableSize(file.size)}</span></span></span><button aria-label={`Remove ${file.name}`} className="min-h-11 px-2 font-semibold text-accent hover:underline" onClick={() => setDocuments((current) => current.filter((item) => item !== file))} type="button">Remove</button></li>)}</ul></>}<FieldError id="supporting-documents-error">{documentError}</FieldError></div>
      <div><label className="font-semibold" htmlFor="primary-country">Primary country of operation</label><p className="mt-1 text-sm leading-6 text-muted" id="primary-country-help">Choose the main country for this diagnostic context.</p><select aria-describedby={`primary-country-help${errors.country ? ' primary-country-error' : ''}`} aria-invalid={Boolean(errors.country)} className={fieldClass} id="primary-country" onChange={(event) => update('country', event.target.value)} required value={form.country}><option value="">Select a country</option>{countries.map((country) => <option key={country.code} value={country.code}>{country.name}</option>)}</select><FieldError id="primary-country-error">{errors.country}</FieldError></div>
      <fieldset><legend className="font-semibold">Recent context period</legend><p className="mt-1 text-sm leading-6 text-muted" id="research-window-help">This period limits recent external context. Relevant official reports may be older.</p><div className="mt-3 grid gap-5 sm:grid-cols-2"><div><label className="text-sm font-semibold" htmlFor="start-date">Start date</label><input aria-describedby={dateDescription} aria-invalid={Boolean(errors.research_window)} className={fieldClass} id="start-date" max={today} onChange={(event) => updateDate('start_date', event.target.value)} required type="date" value={form.research_window.start_date} /></div><div><label className="text-sm font-semibold" htmlFor="end-date">End date</label><input aria-describedby={dateDescription} aria-invalid={Boolean(errors.research_window)} className={fieldClass} id="end-date" max={today} onChange={(event) => updateDate('end_date', event.target.value)} required type="date" value={form.research_window.end_date} /></div></div><p aria-live="polite" className="mt-2 text-sm text-muted" id="research-window-duration">{duration} {duration === 1 ? 'day' : 'days'} selected · Maximum 90 days</p><FieldError id="research-window-error">{errors.research_window}</FieldError></fieldset>
      <div><label className="font-semibold" htmlFor="conversation-focus">What do you want to understand?</label><p className="mt-1 text-sm leading-6 text-muted" id="conversation-focus-help">Describe the decision or challenge you need to discuss.</p><textarea aria-describedby={`conversation-focus-help conversation-focus-count${errors.current_challenge ? ' conversation-focus-error' : ''}`} aria-invalid={Boolean(errors.current_challenge)} className={`${fieldClass} min-h-32 resize-y`} id="conversation-focus" maxLength={600} onChange={(event) => update('current_challenge', event.target.value)} required value={form.current_challenge} /><div className="mt-2 flex flex-wrap justify-between gap-2"><FieldError id="conversation-focus-error">{errors.current_challenge}</FieldError><p aria-live="polite" className="ml-auto text-sm text-muted" id="conversation-focus-count">{form.current_challenge.length} / 600</p></div></div>
      <button className="primary-action" disabled={preparing} type="submit">Prepare diagnostic</button>{preparing && <p aria-live="polite" className="text-sm font-medium text-muted" role="status">{runStatusMessage}</p>}{!preparing && runStatus === 'failed' && <p className="text-sm font-medium text-danger" role="alert">{runStatusMessage}</p>}
    </form>
  </PageFrame>
}

export function OverviewPage() {
  const navigate = useNavigate()
  const { result } = useDiagnostic()
  const packageResult = result!.final_package
  return <PageFrame><PageIntro title="Diagnostic overview">A concise orientation to what the available material suggests and what the first conversation should confirm.</PageIntro><section className="mt-9 border-y border-border py-7" aria-labelledby="overview-summary"><h2 className="font-serif text-2xl font-semibold" id="overview-summary">Executive summary</h2><ul className="mt-4 list-disc space-y-2 pl-5 leading-7 text-ink">{packageResult.organization_snapshot.summary_points.map((point) => <li key={point}>{point}</li>)}</ul></section><section className="mt-9" aria-labelledby="lenses-title"><h2 className="font-serif text-2xl font-semibold" id="lenses-title">Three lenses for the conversation</h2><div className="mt-5 space-y-4">{packageResult.organization_snapshot.lenses.map((lens) => <article className="rounded-panel border border-border bg-surface px-5 py-6 sm:px-6" key={lens.title}><h3 className="font-serif text-xl font-semibold">{lens.title}</h3><dl className="mt-4 grid gap-4 sm:grid-cols-2"><div><dt className="text-sm font-semibold text-muted">What the available material suggests</dt><dd className="mt-1 leading-7">{lens.suggests}</dd></div><div><dt className="text-sm font-semibold text-muted">What still needs to be confirmed</dt><dd className="mt-1 leading-7">{lens.confirm}</dd></div></dl><details className="mt-4"><summary className="flex min-h-11 cursor-pointer items-center text-sm font-semibold text-accent">See supporting detail</summary><p className="pb-2 text-sm leading-6 text-muted">{lens.detail}</p></details></article>)}</div></section><StepActions back="/new-diagnostic"><button className="primary-action" onClick={() => navigate('/conversation')} type="button">Prepare client conversation</button></StepActions></PageFrame>
}

export function ConversationPage() {
  const navigate = useNavigate()
  const { consultantNotes, customQuestions, includeConsultantNotes, result, selectedQuestionIds, toggleQuestion, saveConsultantNotes, setIncludeConsultantNotes, addCustomQuestion, removeCustomQuestion } = useDiagnostic()
  const [addingQuestion, setAddingQuestion] = useState(false)
  const [customQuestion, setCustomQuestion] = useState('')
  const [agendaError, setAgendaError] = useState('')
  const packageResult = result!.final_package
  const addQuestion = () => {
    const question = customQuestion.trim()
    if (!question) return
    addCustomQuestion(question)
    setCustomQuestion('')
    setAddingQuestion(false)
    setAgendaError('')
  }
  const continueToNextSteps = () => {
    if (selectedQuestionIds.length === 0) {
      setAgendaError('Choose at least one question for the workshop agenda.')
      document.getElementById('workshop-agenda')?.focus()
      return
    }
    navigate('/next-steps')
  }
  return <PageFrame><PageIntro title="Prepare the conversation">Choose what the client conversation should clarify and record context for the workshop.</PageIntro><section className="mt-9 bg-blush px-5 py-5 sm:px-6" aria-labelledby="priority-title"><h2 className="font-serif text-2xl font-semibold" id="priority-title">Priority to clarify</h2><p className="mt-3 leading-7">{packageResult.missing_information[0]}</p></section><details className="mt-5 border-y border-border py-1"><summary className="flex min-h-12 cursor-pointer items-center font-semibold text-accent">Possible explanations</summary><ul className="space-y-2 pb-4 pt-2 text-sm leading-6 text-muted">{packageResult.hypotheses.map((item) => <li key={item}>{item}</li>)}</ul></details><section className="mt-9 rounded-panel border border-border bg-surface px-5 py-6 sm:px-7" id="workshop-agenda" tabIndex={-1} aria-labelledby="workshop-agenda-title"><h2 className="font-serif text-2xl font-semibold" id="workshop-agenda-title">Build your workshop agenda</h2><p className="mt-2 leading-7 text-muted">Choose the questions you want to discuss with the client.</p><p aria-live="polite" className="mt-3 text-sm font-semibold">{selectedQuestionIds.length} questions added to the workshop agenda</p>{agendaError && <p className="mt-2 text-sm font-semibold text-danger" role="alert">{agendaError}</p>}<ul className="mt-4 border-t border-border">{packageResult.client_validation_questions.map((question) => <li className="border-b border-border py-4" key={question.key}><label className="flex min-h-11 cursor-pointer items-start gap-3 font-medium leading-7"><input checked={selectedQuestionIds.includes(question.key)} className="mt-1.5 h-5 w-5 shrink-0 accent-accent" onChange={() => { toggleQuestion(question.key); setAgendaError('') }} type="checkbox" /><span>{question.text}</span></label><details className="ml-8 mt-1"><summary className="flex min-h-11 cursor-pointer items-center text-sm font-semibold text-accent">Why ask this?</summary><p className="pb-2 text-sm leading-6 text-muted">{question.reason}</p></details></li>)}{customQuestions.map((question) => <li className="flex flex-wrap items-start justify-between gap-3 border-b border-border py-4" key={question.id}><label className="flex min-h-11 flex-1 cursor-pointer items-start gap-3 font-medium leading-7"><input checked={selectedQuestionIds.includes(question.id)} className="mt-1.5 h-5 w-5 shrink-0 accent-accent" onChange={() => toggleQuestion(question.id)} type="checkbox" /><span>{question.text}</span></label><button className="min-h-11 px-2 font-semibold text-accent hover:underline" onClick={() => removeCustomQuestion(question.id)} type="button">Remove</button></li>)}</ul>{addingQuestion ? <div className="mt-5"><label className="font-semibold" htmlFor="custom-question">Question for the client</label><textarea aria-describedby="custom-question-count" className={`${fieldClass} min-h-24 resize-y`} id="custom-question" maxLength={300} onChange={(event) => setCustomQuestion(event.target.value)} value={customQuestion} /><p aria-live="polite" className="mt-2 text-right text-sm text-muted" id="custom-question-count">{customQuestion.length} / 300</p><div className="mt-3 flex flex-wrap gap-3"><button className="min-h-11 rounded-control bg-ink px-4 font-semibold text-surface" onClick={addQuestion} type="button">Add question</button><button className="min-h-11 px-3 font-semibold text-accent" onClick={() => { setAddingQuestion(false); setCustomQuestion('') }} type="button">Cancel</button></div></div> : <button className="mt-4 min-h-11 font-semibold text-accent hover:underline" onClick={() => setAddingQuestion(true)} type="button">Add another question</button>}<div className="mt-7 border-t border-border pt-6"><label className="font-semibold" htmlFor="consultant-notes">Consultant notes (optional)</label><p className="mt-1 text-sm leading-6 text-muted" id="consultant-notes-help">Add context, sensitivities or reminders for the client conversation.</p><textarea aria-describedby="consultant-notes-help consultant-notes-count" className={`${fieldClass} min-h-28 resize-y`} id="consultant-notes" maxLength={1000} onChange={(event) => saveConsultantNotes(event.target.value)} value={consultantNotes} /><p aria-live="polite" className="mt-2 text-right text-sm text-muted" id="consultant-notes-count">{consultantNotes.length} / 1000</p><label className="mt-4 flex min-h-11 cursor-pointer items-start gap-3"><input checked={includeConsultantNotes} className="mt-1 h-5 w-5 shrink-0 accent-accent" onChange={(event) => setIncludeConsultantNotes(event.target.checked)} type="checkbox" /><span><span className="block font-semibold">Include these notes in the client brief</span><span className="mt-1 block text-sm leading-6 text-muted">Leave this unchecked when the notes are for your private preparation only.</span></span></label></div></section><StepActions back="/overview"><button className="primary-action" onClick={continueToNextSteps} type="button">Save questions and continue</button></StepActions></PageFrame>
}

export function NextStepsPage() {
  const navigate = useNavigate()
  const { addNextStepToBrief, result } = useDiagnostic()
  const packageResult = result!.final_package
  const recommendation = packageResult.recommendations[0]
  const addToBrief = () => { addNextStepToBrief(); navigate('/brief') }
  return <PageFrame><PageIntro title="Recommended next steps">Turn what needs confirmation into one manageable action and a simple validation sequence.</PageIntro><div className="mt-9 rounded-panel border border-border bg-surface px-5 py-7 sm:px-7"><section aria-labelledby="recommendation-title"><h2 className="font-serif text-2xl font-semibold" id="recommendation-title">{recommendation.title}</h2><p className="mt-3 max-w-[44rem] leading-7 text-muted">{recommendation.description}</p><aside className="mt-5 border-l-2 border-accent bg-blush px-5 py-4"><h3 className="font-semibold">Why start here?</h3><p className="mt-2 leading-7">{recommendation.rationale}</p></aside></section><section className="mt-9" aria-labelledby="measures-title"><h2 className="font-serif text-2xl font-semibold" id="measures-title">How progress could be measured</h2><dl className="mt-4 divide-y divide-border border-y border-border">{packageResult.kpis.map((kpi) => <div className="flex flex-col gap-1 py-4 sm:flex-row sm:items-baseline sm:justify-between sm:gap-5" key={kpi.key}><dt className="font-semibold">{kpi.title}</dt><dd className="text-sm text-muted">{kpi.baseline}</dd></div>)}</dl></section><section className="mt-9" aria-labelledby="validation-sequence-title"><h2 className="font-serif text-2xl font-semibold" id="validation-sequence-title">Validation sequence</h2><ol className="mt-5 grid gap-0 border-y border-border lg:grid-cols-3 lg:divide-x lg:divide-border">{packageResult.roadmap_90_day.map((phase, index) => <li className="border-b border-border py-5 last:border-b-0 lg:border-b-0 lg:px-5 lg:first:pl-0 lg:last:pr-0" key={phase.title}><p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">{index + 1} · {phase.period}</p><h3 className="mt-2 font-serif text-xl font-semibold">{phase.title}</h3><p className="mt-2 text-sm leading-6 text-muted">{phase.objective}</p><ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6 text-ink">{phase.activities.map((activity) => <li key={activity}>{activity}</li>)}</ul></li>)}</ol><details className="mt-4 border-b border-border pb-1"><summary className="flex min-h-12 cursor-pointer items-center font-semibold text-accent">View validation plan</summary><p className="pb-4 text-sm leading-6 text-muted">Sequence and timing should be adapted after the client confirms the current situation, available information and practical constraints.</p></details></section></div><StepActions back="/conversation"><button className="primary-action" onClick={addToBrief} type="button">Add to conversation brief</button></StepActions></PageFrame>
}

export function BriefPage() {
  const { consultantNotes, customQuestions, finalizeBrief, includeConsultantNotes, intake, nextStepAdded, reopenBrief, result, reviewed, selectedQuestionIds, supportingDocuments } = useDiagnostic()
  const [showWorkshop, setShowWorkshop] = useState(false)
  const [workshopDate, setWorkshopDate] = useState('')
  const [startTime, setStartTime] = useState('')
  const [duration, setDuration] = useState('60')
  const [attendees, setAttendees] = useState('')
  const [calendarError, setCalendarError] = useState('')
  const packageResult = result!.final_package
  const resultQuestions = packageResult.client_validation_questions.filter((question) => selectedQuestionIds.includes(question.key)).map((question) => question.text)
  const ownQuestions = customQuestions.filter((question) => selectedQuestionIds.includes(question.id)).map((question) => question.text)
  const agenda = [...resultQuestions, ...ownQuestions]
  const recommendation = packageResult.recommendations[0]
  const contextPeriod = `${formatDateOnly(intake.research_window.start_date)} – ${formatDateOnly(intake.research_window.end_date)}`
  const preparedAt = new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(packageResult.run_context.prepared_at))

  const openCalendar = (event: FormEvent) => {
    event.preventDefault()
    if (!workshopDate || !startTime) {
      setCalendarError('Choose a workshop date and start time.')
      return
    }
    const url = createGoogleCalendarUrl({ organization: intake.organization_name, date: workshopDate, startTime, durationMinutes: Number(duration), attendeeEmails: attendees, objective: intake.current_challenge, agenda, consultantNotes: includeConsultantNotes ? consultantNotes : '', nextStep: recommendation.title, contextPeriod })
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return <PageFrame document>
    <article className="print-document min-w-0 border border-border bg-surface px-5 py-8 sm:px-9 sm:py-10 lg:px-14 lg:py-12">
      <header className="border-b border-border pb-8">
        <p className="print-brand">Intellectus · Social Impact Intelligence</p>
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">{intake.organization_name}</p><h1 className="page-title mt-3 font-serif font-semibold leading-[1.08] text-ink">Conversation brief</h1><p className="mt-4 max-w-[42rem] text-lg leading-8 text-muted">A focused, consultant-reviewed starting point for the next client conversation.</p></div>
          <p aria-live="polite" className={`rounded-control px-3 py-2 text-sm font-semibold ${reviewed ? 'bg-sage-soft text-sage' : 'bg-blush text-ink'}`}>{reviewed ? 'Ready' : 'Draft for review'}</p>
        </div>
        <dl className="mt-6 grid gap-x-6 gap-y-3 border-t border-border pt-5 text-sm sm:grid-cols-2"><div><dt className="font-semibold text-muted">Organization</dt><dd className="mt-1">{intake.organization_name}</dd></div><div><dt className="font-semibold text-muted">Primary country of operation</dt><dd className="mt-1">{getCountryName(intake.country)}</dd></div><div><dt className="font-semibold text-muted">Recent context period</dt><dd className="mt-1">{contextPeriod}</dd></div><div><dt className="font-semibold text-muted">Prepared at</dt><dd className="mt-1">{preparedAt}</dd></div><div><dt className="font-semibold text-muted">Status</dt><dd className="mt-1">{reviewed ? 'Ready' : 'Draft for review'}</dd></div></dl>
      </header>
      <div className="divide-y divide-border">
        <section className="py-8"><h2 className="brief-heading">Executive summary</h2><ul className="mt-4 list-disc space-y-2 pl-5 leading-7">{packageResult.organization_snapshot.summary_points.map((point) => <li key={point}>{point}</li>)}</ul></section>
        <section className="py-8"><h2 className="brief-heading">Starting context</h2><p className="mt-4 leading-7">{intake.current_challenge}</p>{supportingDocuments.length > 0 && <div className="mt-5"><h3 className="font-semibold">Supporting documents selected</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6">{supportingDocuments.map((file) => <li key={`${file.name}-${file.size}`}>{file.name} · {documentType(file)} · {readableSize(file.size)} — Not analysed in this local demo</li>)}</ul></div>}</section>
        <section className="py-8"><h2 className="brief-heading">What the available material suggests</h2><ul className="mt-4 list-disc space-y-2 pl-5 leading-7">{packageResult.findings.map((item) => <li key={item}>{item}</li>)}</ul></section>
        <section className="py-8"><h2 className="brief-heading">What remains unclear</h2><ul className="mt-4 list-disc space-y-2 pl-5 leading-7">{packageResult.missing_information.map((item) => <li key={item}>{item}</li>)}</ul></section>
        <section className="py-8"><h2 className="brief-heading">Workshop agenda</h2><ol className="mt-4 list-decimal space-y-2 pl-5 leading-7">{agenda.map((question) => <li key={question}>{question}</li>)}</ol></section>
        {includeConsultantNotes && consultantNotes.trim() && <section className="py-8"><h2 className="brief-heading">Consultant notes</h2><p className="mt-4 whitespace-pre-wrap leading-7">{consultantNotes}</p></section>}
        <section className="py-8"><h2 className="brief-heading">Suggested next step</h2>{nextStepAdded && <><p className="mt-4 font-semibold">{recommendation.title}</p><p className="mt-2 leading-7 text-muted">{recommendation.description}</p></>}</section>
        <section className="py-8"><h2 className="brief-heading">How progress could be measured</h2><ul className="mt-4 space-y-2 leading-7">{packageResult.kpis.map((kpi) => <li key={kpi.key}><strong>{kpi.title}</strong> — {kpi.baseline}</li>)}</ul></section>
        <section className="py-8"><h2 className="brief-heading">Validation plan</h2><ol className="mt-4 divide-y divide-border border-y border-border">{packageResult.roadmap_90_day.map((phase) => <li className="grid gap-1 py-4 sm:grid-cols-[7rem_1fr]" key={phase.title}><p className="font-semibold">{phase.title}</p><div><p className="text-sm text-muted">{phase.period}</p><p className="mt-1 leading-7">{phase.objective}</p></div></li>)}</ol></section>
      </div>
      <details className="print-expand border-y border-border py-2"><summary className="flex min-h-12 cursor-pointer items-center font-semibold text-accent">Sources and limitations</summary><div className="space-y-4 pb-5 pt-4 text-sm leading-7 text-muted"><p>No reviewed public sources are included in this local demo result.</p><ul className="list-disc space-y-2 pl-5">{packageResult.confidence_limitations.map((item) => <li key={item}>{item}</li>)}</ul></div></details>
      <section className="print-hidden py-8" aria-labelledby="final-review-title">
        <h2 className="brief-heading" id="final-review-title">Review and finalize</h2>
        <p className="mt-3 max-w-[42rem] leading-7 text-muted">Review the brief before using it in your client conversation.</p>
        <p aria-live="polite" className={`mt-5 rounded-panel px-4 py-3 font-semibold ${reviewed ? 'bg-sage-soft text-sage' : 'bg-blush text-ink'}`}>{reviewed ? 'Ready for conversation' : 'Draft · Changes are kept for this session only'}</p>
        {!reviewed && <p className="mt-3 text-sm leading-6 text-muted">This draft is not saved after you close or refresh the application.</p>}
        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          {reviewed ? <button aria-expanded={showWorkshop} className="primary-action" onClick={() => setShowWorkshop((shown) => !shown)} type="button">Schedule client workshop</button> : <button className="primary-action" onClick={finalizeBrief} type="button">Finalize brief</button>}
          <button className="min-h-12 w-full rounded-control border border-border bg-surface px-5 font-semibold text-ink hover:bg-blush sm:w-auto" onClick={() => window.print()} type="button">Print or save as PDF</button>
          {reviewed && <button className="min-h-12 w-full rounded-control border border-border bg-surface px-5 font-semibold text-ink hover:bg-blush sm:w-auto" onClick={() => { reopenBrief(); setShowWorkshop(false) }} type="button">Reopen as draft</button>}
        </div>
        <div className="mt-4 flex flex-col items-start gap-1 text-sm font-semibold sm:flex-row sm:gap-5"><Link className="inline-flex min-h-11 items-center text-accent hover:underline" to="/new-diagnostic">Edit starting information</Link><Link className="inline-flex min-h-11 items-center text-accent hover:underline" to="/conversation">Edit workshop agenda</Link></div>
        {reviewed && showWorkshop && <form className="mt-7 space-y-5 rounded-panel border border-border bg-surface p-5" onSubmit={openCalendar}><div className="grid gap-5 sm:grid-cols-2"><div><label className="font-semibold" htmlFor="workshop-date">Workshop date</label><input className={fieldClass} id="workshop-date" onChange={(event) => setWorkshopDate(event.target.value)} required type="date" value={workshopDate} /></div><div><label className="font-semibold" htmlFor="workshop-time">Start time</label><input className={fieldClass} id="workshop-time" onChange={(event) => setStartTime(event.target.value)} required type="time" value={startTime} /></div><div><label className="font-semibold" htmlFor="workshop-duration">Duration</label><select className={fieldClass} id="workshop-duration" onChange={(event) => setDuration(event.target.value)} value={duration}>{[30, 45, 60, 90].map((minutes) => <option key={minutes} value={minutes}>{minutes} minutes</option>)}</select></div><div><label className="font-semibold" htmlFor="workshop-attendees">Attendee emails (optional)</label><input className={fieldClass} id="workshop-attendees" onChange={(event) => setAttendees(event.target.value)} type="text" value={attendees} /></div></div>{calendarError && <p className="text-sm font-semibold text-danger" role="alert">{calendarError}</p>}<p className="text-sm leading-6 text-muted">Review the event details in Google Calendar before sending invitations.</p><button className="primary-action" type="submit">Open in Google Calendar</button></form>}
      </section>
      <p className="print-footer">Prepared with Intellectus · Social Impact Intelligence</p>
    </article>
  </PageFrame>
}
