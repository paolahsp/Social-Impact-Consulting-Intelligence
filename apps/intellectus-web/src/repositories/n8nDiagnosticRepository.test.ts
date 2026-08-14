/// <reference types="node" />

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it, vi } from 'vitest'
import { DiagnosticTransportResponseSchema } from '../schemas/diagnosticTransport'
import { createConfiguredDiagnosticRepository } from './createDiagnosticRepository'
import { FixtureDiagnosticRepository } from './diagnosticRepository'
import {
  DiagnosticTransportError,
  EvidenceRequiredError,
  N8nDiagnosticRepository,
  mapTransportResponse,
} from './n8nDiagnosticRepository'

const input = {
  organization_name: 'GiveDirectly',
  website: 'https://www.givedirectly.org',
  country: 'US',
  current_challenge: 'Preparing for a pre-engagement diagnostic workshop',
  research_window: { start_date: '2026-05-12', end_date: '2026-08-09' },
  uploaded_document_refs: [],
}

function response(status: number, body: unknown) {
  return {
    status,
    ok: status >= 200 && status < 300,
    text: async () => JSON.stringify(body),
  } as Response
}

describe('N8nDiagnosticRepository', () => {
  it('sends a schema-valid live request without treating intake or browser files as evidence', async () => {
    const fetchImpl = vi.fn(async (_url: string | URL | Request, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body))
      expect(body).toMatchObject({ contract_version: '1.0', mode: 'live', intake: input })
      expect(body).not.toHaveProperty('evidence_handoff')
      expect(body.intake.uploaded_document_refs).toEqual([])
      expect(init?.signal).toBeInstanceOf(AbortSignal)
      return response(422, {
        contract_version: '1.0', status: 'needs_evidence', correlation_id: body.correlation_id,
        run_id: 'RUN-OFFLINE-001', demo: false,
        message: 'Evidence is required before this analysis can run.',
        error: { code: 'evidence_required' },
      })
    }) as typeof fetch
    const repository = new N8nDiagnosticRepository('https://workflow.example.test/webhook', { fetchImpl })
    await expect(repository.prepareDiagnostic(input)).rejects.toBeInstanceOf(EvidenceRequiredError)
    expect(fetchImpl).toHaveBeenCalledOnce()
  })

  it('maps malformed, upstream and network responses to one public error without internal detail', async () => {
    const malformed = new N8nDiagnosticRepository('https://workflow.example.test/webhook', {
      fetchImpl: vi.fn(async () => response(200, { stack: 'internal' })) as typeof fetch,
    })
    await expect(malformed.prepareDiagnostic(input)).rejects.toEqual(new DiagnosticTransportError())

    const network = new N8nDiagnosticRepository('https://workflow.example.test/webhook', {
      fetchImpl: vi.fn(async () => { throw new Error('getaddrinfo secret-host') }) as typeof fetch,
    })
    await expect(network.prepareDiagnostic(input)).rejects.toMatchObject({
      message: 'We couldn’t prepare the diagnostic. Try again or continue with the local demo.',
    })
  })

  it('aborts a request after the configured timeout', async () => {
    const fetchImpl = vi.fn((_url: string | URL | Request, init?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
    })) as typeof fetch
    const repository = new N8nDiagnosticRepository('https://workflow.example.test/webhook', { fetchImpl, timeoutMs: 1 })
    await expect(repository.prepareDiagnostic(input)).rejects.toBeInstanceOf(DiagnosticTransportError)
  })

  it('validates the repository demo response and refuses to present it as live', () => {
    const fixture = JSON.parse(readFileSync(resolve(process.cwd(), '../../fixtures/intellectus_71_success_response.json'), 'utf8'))
    const parsed = DiagnosticTransportResponseSchema.parse(fixture)
    expect(parsed.status).toBe('completed')
    if (parsed.status !== 'completed') throw new Error('Expected completed fixture')
    expect(parsed.demo).toBe(true)
    expect(() => mapTransportResponse(parsed, parsed.data.intake)).toThrow(DiagnosticTransportError)
  })

  it('uses the explicit local demo only when the webhook variable is absent or invalid', () => {
    expect(createConfiguredDiagnosticRepository('')).toBeInstanceOf(FixtureDiagnosticRepository)
    expect(createConfiguredDiagnosticRepository('not-a-url')).toBeInstanceOf(FixtureDiagnosticRepository)
    expect(createConfiguredDiagnosticRepository('https://workflow.example.test/webhook')).toBeInstanceOf(N8nDiagnosticRepository)
  })
})
