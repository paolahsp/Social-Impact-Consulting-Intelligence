import { FixtureDiagnosticRepository } from './diagnosticRepository'
import { N8nDiagnosticRepository } from './n8nDiagnosticRepository'

export function createConfiguredDiagnosticRepository(webhookUrl = import.meta.env.VITE_DIAGNOSTIC_WEBHOOK_URL) {
  if (import.meta.env.MODE === 'test' && webhookUrl === import.meta.env.VITE_DIAGNOSTIC_WEBHOOK_URL) {
    return new FixtureDiagnosticRepository()
  }
  const normalizedUrl = webhookUrl?.trim()
  if (!normalizedUrl) return new FixtureDiagnosticRepository()
  try {
    return new N8nDiagnosticRepository(normalizedUrl)
  } catch {
    return new FixtureDiagnosticRepository()
  }
}
