/// <reference types="node" />

import axe from 'axe-core'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { countries } from '../data/countries'
import { FixtureDiagnosticRepository, type DiagnosticRepository } from '../repositories/diagnosticRepository'
import { DiagnosticTransportError, EvidenceRequiredError } from '../repositories/n8nDiagnosticRepository'
import type { DiagnosticInput, DiagnosticResult } from '../types/diagnostic'
import App from './App'

function renderAt(pathname = '/new-diagnostic', repository?: DiagnosticRepository) {
  window.history.replaceState({}, '', pathname)
  return render(<App repository={repository} />)
}

function fillDiagnostic({ organization = 'Example organization', website = 'https://example.test', country = 'US', startDate = '2020-01-01', endDate = '2020-01-01', challenge = 'Clarify the operations workflow and ownership.' } = {}) {
  fireEvent.change(screen.getByLabelText('Organization name'), { target: { value: organization } })
  fireEvent.change(screen.getByLabelText('Official website'), { target: { value: website } })
  fireEvent.change(screen.getByLabelText('Primary country of operation'), { target: { value: country } })
  fireEvent.change(screen.getByLabelText('Start date'), { target: { value: startDate } })
  fireEvent.change(screen.getByLabelText('End date'), { target: { value: endDate } })
  fireEvent.change(screen.getByLabelText('What do you want to understand?'), { target: { value: challenge } })
}

async function prepareDiagnostic(options = {}) {
  fillDiagnostic(options)
  fireEvent.click(screen.getByRole('button', { name: 'Prepare diagnostic' }))
  await waitFor(() => expect(window.location.pathname).toBe('/overview'))
  await screen.findByRole('button', { name: 'Prepare client conversation' })
}

async function reachConversation(options = {}) {
  await prepareDiagnostic(options)
  fireEvent.click(screen.getByRole('button', { name: 'Prepare client conversation' }))
  await screen.findByRole('heading', { level: 1, name: 'Prepare the conversation' })
}

async function reachBrief(options = {}) {
  await reachConversation(options)
  fireEvent.click(screen.getAllByRole('checkbox')[0])
  fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
  fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
  await screen.findByRole('heading', { level: 1, name: 'Conversation brief' })
}

describe('route protection and frozen shell', () => {
  beforeEach(() => window.history.replaceState({}, '', '/new-diagnostic'))

  it.each(['/overview', '/conversation', '/next-steps', '/brief'])('protects %s and explains the redirect', async (pathname) => {
    renderAt(pathname)
    expect(await screen.findByText('Complete the setup to prepare your diagnostic.')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/new-diagnostic')
  })

  it('renders future steps as disabled text before a result exists', () => {
    renderAt()
    expect(screen.getAllByText(/Overview|Conversation|Next steps|Conversation brief/).filter((node) => node.closest('[aria-disabled="true"]'))).toHaveLength(4)
    expect(screen.queryByRole('link', { name: /Overview/ })).not.toBeInTheDocument()
  })

  it('keeps five routes, one h1, one Demo marker and no legacy navigation', async () => {
    renderAt()
    expect(screen.getAllByText('Demo')).toHaveLength(1)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.queryByLabelText('Primary navigation')).not.toBeInTheDocument()
    await prepareDiagnostic()
    expect(screen.getByRole('link', { name: /Overview/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Conversation brief/ })).not.toBeInTheDocument()
  })
})

describe('setup validation, countries and documents', () => {
  beforeEach(() => window.history.replaceState({}, '', '/new-diagnostic'))

  it('uses the centralized country list and stores United States as US', async () => {
    const fixture = new FixtureDiagnosticRepository()
    const prepare = vi.fn((input: DiagnosticInput) => fixture.prepareDiagnostic(input))
    renderAt('/new-diagnostic', { prepareDiagnostic: prepare })
    const select = screen.getByRole('combobox', { name: 'Primary country of operation' })
    expect(within(select).getAllByRole('option')).toHaveLength(countries.length + 1)
    fillDiagnostic({ country: 'US' })
    fireEvent.click(screen.getByRole('button', { name: 'Prepare diagnostic' }))
    await waitFor(() => expect(prepare).toHaveBeenCalledOnce())
    expect(prepare.mock.calls[0][0].country).toBe('US')
  })

  it('documents the US to United States transformation in REPORT_MAPPING', () => {
    const mapping = readFileSync(resolve(process.cwd(), 'docs/REPORT_MAPPING.md'), 'utf8')
    expect(mapping).toContain('`country` = `US`')
    expect(mapping).toContain('`United States`')
    expect(mapping).toContain('The adapter preserves the ISO code; no country-name field is invented')
  })

  it('focuses the first invalid field and preserves associated errors', () => {
    renderAt()
    fireEvent.change(screen.getByLabelText('Start date'), { target: { value: '' } })
    fireEvent.change(screen.getByLabelText('End date'), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: 'Prepare diagnostic' }))
    expect(screen.getByLabelText('Organization name')).toHaveFocus()
    expect(screen.getByLabelText('Organization name')).toHaveAttribute('aria-describedby', expect.stringContaining('organization-name-error'))
  })

  it('keeps current website, country and date validation', () => {
    renderAt()
    fillDiagnostic({ website: 'invalid', startDate: '2020-03-02', endDate: '2020-03-01' })
    fireEvent.click(screen.getByRole('button', { name: 'Prepare diagnostic' }))
    expect(screen.getByText('Enter a complete web address.')).toBeInTheDocument()
    expect(screen.getByText('Start date must be on or before the end date.')).toBeInTheDocument()
  })

  it('accepts valid documents, shows metadata and removes one', () => {
    renderAt()
    const input = screen.getByLabelText('Supporting documents (optional)') as HTMLInputElement
    const inputClick = vi.spyOn(input, 'click')
    expect(input).toHaveAttribute('type', 'file')
    expect(input).toHaveClass('sr-only')
    expect(screen.getByText('No documents selected')).toBeInTheDocument()
    expect(screen.queryByText('Selected for this session. Documents will be analysed when the research workflow is connected.')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Add documents' }))
    expect(inputClick).toHaveBeenCalledOnce()
    const file = new File(['report'], 'report.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(screen.queryByText('No documents selected')).not.toBeInTheDocument()
    expect(screen.getByText('Selected for this session. Documents will be analysed when the research workflow is connected.')).toBeInTheDocument()
    expect(screen.getByText('report.pdf')).toBeInTheDocument()
    expect(screen.getByText(/PDF · 1 KB/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Remove report.pdf' }))
    expect(screen.queryByText('report.pdf')).not.toBeInTheDocument()
    expect(screen.getByText('No documents selected')).toBeInTheDocument()
  })

  it('rejects an invalid format and a document above 10 MiB', () => {
    renderAt()
    const input = screen.getByLabelText('Supporting documents (optional)')
    fireEvent.change(input, { target: { files: [new File(['x'], 'image.png', { type: 'image/png' })] } })
    expect(screen.getByText('Choose PDF, DOCX or TXT documents only.')).toBeInTheDocument()
    fireEvent.change(input, { target: { files: [new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'large.pdf', { type: 'application/pdf' })] } })
    expect(screen.getByText('Each document must be 10 MiB or smaller.')).toBeInTheDocument()
  })

  it('limits the selection to five documents', () => {
    renderAt()
    const files = Array.from({ length: 6 }, (_, index) => new File(['x'], `file-${index}.txt`, { type: 'text/plain' }))
    fireEvent.change(screen.getByLabelText('Supporting documents (optional)'), { target: { files } })
    expect(screen.getByText('Choose no more than five documents.')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /Remove file-/ })).toHaveLength(5)
  })

  it('resets country and documents when New diagnostic starts', async () => {
    renderAt()
    fireEvent.change(screen.getByLabelText('Supporting documents (optional)'), { target: { files: [new File(['x'], 'notes.txt', { type: 'text/plain' })] } })
    await prepareDiagnostic({ country: 'US' })
    fireEvent.click(screen.getByRole('link', { name: /New diagnostic/ }))
    expect(screen.getByLabelText('Primary country of operation')).toHaveValue('')
    expect(screen.queryByText('notes.txt')).not.toBeInTheDocument()
  })
})

describe('workshop agenda, brief and calendar', () => {
  beforeEach(() => window.history.replaceState({}, '', '/new-diagnostic'))

  it('requires a question before continuing', async () => {
    renderAt()
    await reachConversation()
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    expect(screen.getByText('Choose at least one question for the workshop agenda.')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/conversation')
  })

  it('adds, selects and removes only a custom question', async () => {
    renderAt()
    await reachConversation()
    fireEvent.click(screen.getByRole('button', { name: 'Add another question' }))
    fireEvent.change(screen.getByLabelText('Question for the client'), { target: { value: 'What should we review first?' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add question' }))
    expect(screen.getByRole('checkbox', { name: 'What should we review first?' })).toBeChecked()
    expect(screen.getByText('1 questions added to the workshop agenda')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    expect(screen.queryByText('What should we review first?')).not.toBeInTheDocument()
  })

  it('includes consultant notes in the brief only after explicit consent', async () => {
    renderAt()
    const documentFile = new File(['x'], 'context.txt', { type: 'text/plain' })
    fireEvent.change(screen.getByLabelText('Supporting documents (optional)'), { target: { files: [documentFile] } })
    await reachConversation({ country: 'US' })
    fireEvent.click(screen.getAllByRole('checkbox')[0])
    expect(screen.getByRole('checkbox', { name: /Include these notes in the client brief/ })).not.toBeChecked()
    fireEvent.change(screen.getByLabelText('Consultant notes (optional)'), { target: { value: 'Confirm the decision owner.' } })
    fireEvent.click(screen.getByRole('checkbox', { name: /Include these notes in the client brief/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
    expect(screen.getByText('United States')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Executive summary' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'What the available material suggests' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Workshop agenda' })).toBeInTheDocument()
    const notesSection = screen.getByRole('heading', { name: 'Consultant notes' }).closest('section')
    expect(within(notesSection as HTMLElement).getByText('Confirm the decision owner.')).toBeInTheDocument()
    expect(notesSection).not.toHaveClass('print-hidden')
    expect(screen.getByText(/context.txt.*Not analysed in this local demo/)).toBeInTheDocument()
    expect(screen.getByText('No reviewed public sources are included in this local demo result.')).toBeInTheDocument()
    expect(screen.getByText('Sources and limitations').closest('details')).not.toHaveAttribute('open')
  })

  it('omits private and empty consultant notes from the brief', async () => {
    renderAt()
    await reachConversation()
    fireEvent.click(screen.getAllByRole('checkbox')[0])
    fireEvent.change(screen.getByLabelText('Consultant notes (optional)'), { target: { value: 'Private sensitivity.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
    expect(screen.queryByRole('heading', { name: 'Consultant notes' })).not.toBeInTheDocument()
  })

  it('does not create a note section when inclusion is checked but the note is empty', async () => {
    renderAt()
    await reachConversation()
    fireEvent.click(screen.getAllByRole('checkbox')[0])
    fireEvent.click(screen.getByRole('checkbox', { name: /Include these notes in the client brief/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
    expect(screen.queryByRole('heading', { name: 'Consultant notes' })).not.toBeInTheDocument()
  })

  it('finalizes, schedules, reopens and preserves session information', async () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    renderAt()
    await reachConversation()
    fireEvent.click(screen.getAllByRole('checkbox')[0])
    fireEvent.change(screen.getByLabelText('Consultant notes (optional)'), { target: { value: 'Keep this context.' } })
    fireEvent.click(screen.getByRole('checkbox', { name: /Include these notes in the client brief/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
    expect(screen.getAllByText('Draft for review')).toHaveLength(2)
    expect(screen.getByText('Draft · Changes are kept for this session only')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Finalize brief' })).toBeInTheDocument()
    expect(screen.queryByText('Save draft')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Schedule client workshop' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Finalize brief' }))
    expect(screen.getByText('Ready for conversation')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reopen as draft' })).toBeInTheDocument()
    expect(screen.queryByLabelText('Workshop date')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Schedule client workshop' }))
    expect(screen.getByLabelText('Workshop date')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Workshop date'), { target: { value: '2026-09-01' } })
    fireEvent.change(screen.getByLabelText('Start time'), { target: { value: '10:30' } })
    fireEvent.change(screen.getByLabelText('Attendee emails (optional)'), { target: { value: 'client@example.test' } })
    fireEvent.click(screen.getByRole('button', { name: 'Open in Google Calendar' }))
    expect(open).toHaveBeenCalledWith(expect.stringMatching(/^https:\/\/calendar\.google\.com\/calendar\/render\?/), '_blank', 'noopener,noreferrer')
    expect(new URL(open.mock.calls[0][0] as string).searchParams.get('text')).toBe('Intellectus diagnostic workshop — Example organization')
    fireEvent.click(screen.getByRole('button', { name: 'Reopen as draft' }))
    expect(screen.getByText('Draft · Changes are kept for this session only')).toBeInTheDocument()
    expect(screen.queryByLabelText('Workshop date')).not.toBeInTheDocument()
    expect(screen.getByText('When a stakeholder reports an issue, what happens next?')).toBeInTheDocument()
    expect(screen.getByText('Keep this context.')).toBeInTheDocument()
    open.mockRestore()
  })

  it('excludes private notes from Calendar and includes consented notes', async () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    renderAt()
    await reachConversation()
    fireEvent.click(screen.getAllByRole('checkbox')[0])
    fireEvent.change(screen.getByLabelText('Consultant notes (optional)'), { target: { value: 'Handle this privately.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
    fireEvent.click(screen.getByRole('button', { name: 'Finalize brief' }))
    fireEvent.click(screen.getByRole('button', { name: 'Schedule client workshop' }))
    fireEvent.change(screen.getByLabelText('Workshop date'), { target: { value: '2026-09-01' } })
    fireEvent.change(screen.getByLabelText('Start time'), { target: { value: '10:30' } })
    fireEvent.click(screen.getByRole('button', { name: 'Open in Google Calendar' }))
    expect(new URL(open.mock.calls[0][0] as string).searchParams.get('details')).not.toContain('Handle this privately.')
    open.mockClear()
    fireEvent.click(screen.getByRole('link', { name: 'Edit workshop agenda' }))
    fireEvent.click(screen.getByRole('checkbox', { name: /Include these notes in the client brief/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
    fireEvent.click(screen.getByRole('button', { name: 'Schedule client workshop' }))
    fireEvent.change(screen.getByLabelText('Workshop date'), { target: { value: '2026-09-01' } })
    fireEvent.change(screen.getByLabelText('Start time'), { target: { value: '10:30' } })
    fireEvent.click(screen.getByRole('button', { name: 'Open in Google Calendar' }))
    expect(new URL(open.mock.calls[0][0] as string).searchParams.get('details')).toContain('Consultant notes: Handle this privately.')
    open.mockRestore()
  })

  it('resets consultant note text and inclusion for a new diagnostic', async () => {
    renderAt()
    await reachConversation()
    fireEvent.change(screen.getByLabelText('Consultant notes (optional)'), { target: { value: 'Temporary note.' } })
    fireEvent.click(screen.getByRole('checkbox', { name: /Include these notes in the client brief/ }))
    fireEvent.click(screen.getByRole('link', { name: /New diagnostic/ }))
    await prepareDiagnostic()
    fireEvent.click(screen.getByRole('button', { name: 'Prepare client conversation' }))
    expect(screen.getByLabelText('Consultant notes (optional)')).toHaveValue('')
    expect(screen.getByRole('checkbox', { name: /Include these notes in the client brief/ })).not.toBeChecked()
  })

  it('prints through the browser without server export', async () => {
    const print = vi.spyOn(window, 'print').mockImplementation(() => undefined)
    renderAt()
    await reachBrief()
    fireEvent.click(screen.getByRole('button', { name: 'Print or save as PDF' }))
    expect(print).toHaveBeenCalledOnce()
    fireEvent.click(screen.getByRole('button', { name: 'Finalize brief' }))
    fireEvent.click(screen.getByRole('button', { name: 'Print or save as PDF' }))
    expect(print).toHaveBeenCalledTimes(2)
    print.mockRestore()
  })
})

describe('automated accessibility', () => {
  it('announces the real pending state without invented progress', async () => {
    const repository: DiagnosticRepository = {
      deliveryMode: 'live',
      prepareDiagnostic: vi.fn(() => new Promise<DiagnosticResult>(() => undefined)),
    }
    const { container } = renderAt('/new-diagnostic', repository)
    fillDiagnostic()
    fireEvent.click(screen.getByRole('button', { name: 'Prepare diagnostic' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Preparing diagnostic…')
    expect(screen.getByRole('button', { name: 'Prepare diagnostic' })).toBeDisabled()
    expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })).violations).toEqual([])
  })

  it('has no axe violations across all five steps', async () => {
    const { container } = renderAt()
    expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })).violations).toEqual([])
    await prepareDiagnostic()
    expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })).violations).toEqual([])
    fireEvent.click(screen.getByRole('button', { name: 'Prepare client conversation' }))
    expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })).violations).toEqual([])
    fireEvent.click(screen.getAllByRole('checkbox')[0])
    fireEvent.click(screen.getByRole('button', { name: 'Save questions and continue' }))
    expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })).violations).toEqual([])
    fireEvent.click(screen.getByRole('button', { name: 'Add to conversation brief' }))
    expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })).violations).toEqual([])
  })

  it.each([
    [new EvidenceRequiredError(), 'Evidence is required before this analysis can run.'],
    [new DiagnosticTransportError(), 'We couldn’t prepare the diagnostic. Try again or continue with the local demo.'],
  ])('keeps the new failure state accessible and free of internal jargon', async (error, message) => {
    const repository: DiagnosticRepository = {
      deliveryMode: 'live',
      prepareDiagnostic: vi.fn(async () => { throw error }),
    }
    const { container } = renderAt('/new-diagnostic', repository)
    fillDiagnostic()
    fireEvent.click(screen.getByRole('button', { name: 'Prepare diagnostic' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(screen.getByRole('button', { name: 'Prepare diagnostic' })).toBeEnabled()
    expect(container.textContent).not.toMatch(/\bn8n\b|workflow 53|schemas?|run_id|stack trace/i)
    expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })).violations).toEqual([])
  })
})
