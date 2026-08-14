import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AppShell } from '../components/layout/AppShell'
import {
  BriefPage,
  ConversationPage,
  NewDiagnosticPage,
  NextStepsPage,
  OverviewPage,
} from '../pages/ProductPages'
import {
  FixtureDiagnosticRepository,
  type DiagnosticRepository,
} from '../repositories/diagnosticRepository'
import { DiagnosticProvider } from './DiagnosticProvider'
import { useDiagnostic } from './diagnosticContext'

const fixtureRepository = new FixtureDiagnosticRepository()

function ProtectedStep({ children, brief = false }: { children: ReactNode; brief?: boolean }) {
  const { briefExists, result } = useDiagnostic()
  const location = useLocation()
  if (!result || (brief && !briefExists)) {
    return <Navigate replace state={{ setupRequired: true, from: location.pathname }} to="/new-diagnostic" />
  }
  return children
}

export default function App({
  repository = fixtureRepository,
}: {
  repository?: DiagnosticRepository
}) {
  return (
    <BrowserRouter>
      <DiagnosticProvider repository={repository}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Navigate replace to="/new-diagnostic" />} />
            <Route element={<NewDiagnosticPage />} path="/new-diagnostic" />
            <Route element={<ProtectedStep><OverviewPage /></ProtectedStep>} path="/overview" />
            <Route element={<ProtectedStep><ConversationPage /></ProtectedStep>} path="/conversation" />
            <Route element={<ProtectedStep><NextStepsPage /></ProtectedStep>} path="/next-steps" />
            <Route element={<ProtectedStep brief><BriefPage /></ProtectedStep>} path="/brief" />
            <Route path="*" element={<Navigate replace to="/new-diagnostic" />} />
          </Route>
        </Routes>
      </DiagnosticProvider>
    </BrowserRouter>
  )
}
